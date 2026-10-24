import { owner, ownerValue, type AccountDatabase } from "./accountData";
import { assertScopedAccountActive } from './accountLifecycle';
import { paidAccess } from "./entitlements";
import { backupPackageSchema, MAX_BACKUP_BYTES, restoreApplyInputSchema, restoreInputSchema, type BackupPackage } from "../shared/backup";
import { inspectImage } from "./assets";
import { templateConfigSchema } from "../shared/template";
import { printQueueSchema } from "../shared/printing";
import { categoryDesignSchema, categoryQueueSchema, categorySnapshotSchema } from "../shared/categorySign";
import { fieldSourceHash } from "../shared/fieldTranslation";
import { commonPrintInputSchema, commonSnapshotSchema } from "../shared/commonPrinting";
import { remapCommonSet, remapCommonSnapshot } from "./commonPrintBackup";
import { favoriteKey, type DesignFavorite } from "../shared/designFavorite";
import { offersSchema } from "../shared/product";

export type BackupEnv = { DB: AccountDatabase; MEDIA?: R2Bucket; APP_VERSION?: string; bypassPaid?: boolean };

const tables = [
  "categories", "category_signs", "products", "product_offers", "product_localizations", "translation_drafts",
  "translation_reviews", "templates", "assets", "print_sets", "print_jobs", "field_translations",
  "product_catalog_links", "product_catalog_translation_sources", "design_favorites",
] as const;
const rootTables = new Set<string>(["categories", "category_signs", "products", "templates", "assets", "print_sets", "print_jobs", "field_translations"]);
const backupSelect = (db: AccountDatabase, table: (typeof tables)[number]) => `SELECT * FROM ${table} WHERE ${rootTables.has(table) || table === "design_favorites" ? owner(db) : `product_id IN (SELECT id FROM products WHERE ${owner(db)})`}`;
const stripOwner = (row: Record<string, unknown>) => Object.fromEntries(Object.entries(row).filter(([key]) => key !== "owner_id" && key !== "account_id"));
async function backupRows(db: AccountDatabase, table: (typeof tables)[number]) {
  return { results: (await db.prepare(backupSelect(db, table)).all<Record<string, unknown>>()).results.map(stripOwner) };
}

async function catalogRestoreRows<T extends {id:string}>(db:AccountDatabase,table:"catalog_descriptions"|"catalog_packages"|"product_catalog_links",ids:(string|null)[],columns:string) {
  const unique=[...new Set(ids.filter((id):id is string=>Boolean(id)))],rows=new Map<string,T>();
  for(let start=0;start<unique.length;start+=100) {
    const result=await db.prepare(`SELECT id,${columns} FROM ${table} WHERE id IN (SELECT value FROM json_each(?))`)
      .bind(JSON.stringify(unique.slice(start,start+100))).all<T>();
    for(const row of result.results)rows.set(row.id,row);
  }
  return rows;
}


const base64 = (bytes: Uint8Array) => {
  let binary = "";
  for (let offset = 0; offset < bytes.length; offset += 0x8000) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + 0x8000));
  }
  return btoa(binary);
};
const unbase64 = (value: string) => Uint8Array.from(atob(value), (character) => character.charCodeAt(0));

const sha256 = async (bytes: Uint8Array) => [...new Uint8Array(await crypto.subtle.digest("SHA-256", bytes.slice().buffer))]
  .map((value) => value.toString(16).padStart(2, "0")).join("");

const serializedByteLength = (value: unknown) => new TextEncoder().encode(JSON.stringify(value)).byteLength;
const assertBackupSize = (value: unknown): BackupPackage => {
  const backup = backupPackageSchema.parse(value);
  if (serializedByteLength(backup) > MAX_BACKUP_BYTES) throw new Error("backup_too_large");
  return backup;
};
const estimatedBackupSize = (manifest: unknown, data: Record<string, unknown[]>) => {
  let estimate = serializedByteLength({ manifest, data, assets: [] });
  for (const metadata of data.assets ?? []) {
    const byteSize = Number((metadata as Record<string, unknown>).byte_size);
    if (!Number.isSafeInteger(byteSize) || byteSize < 0) return MAX_BACKUP_BYTES + 1;
    estimate += serializedByteLength({ metadata, sha256: "0".repeat(64), contentBase64: "" }) + 4 * Math.ceil(byteSize / 3) + 1;
    if (estimate > MAX_BACKUP_BYTES) return estimate;
  }
  return estimate;
};

const ASSET_IO_CONCURRENCY = 4;
async function mapAssetBatches<T, R>(items: readonly T[], work: (item: T) => Promise<R>) {
  const results: R[] = [];
  for (let offset = 0; offset < items.length; offset += ASSET_IO_CONCURRENCY) {
    // Drain in-flight I/O and report the first error in input order.
    const batch = await Promise.allSettled(items.slice(offset, offset + ASSET_IO_CONCURRENCY).map(work));
    for (const result of batch) {
      if (result.status === "rejected") throw result.reason;
      results.push(result.value);
    }
  }
  return results;
}

export async function createBackup(env: BackupEnv): Promise<BackupPackage> {
  const data = Object.fromEntries(await Promise.all(tables.map(async (table) => [
    table, (await backupRows(env.DB, table)).results,
  ]))) as Record<(typeof tables)[number], Record<string, unknown>[]>;
  const manifest = {
    format: "yeondu-label-backup" as const,
    formatVersion: 3 as const,
    accountId: env.DB.accountId,
    exportedAt: new Date().toISOString(),
    appVersion: env.APP_VERSION ?? "unknown",
    counts: Object.fromEntries(tables.map((table) => [table, data[table].length])),
  };
  if (estimatedBackupSize(manifest, data) > MAX_BACKUP_BYTES) throw new Error("backup_too_large");
  const assets = await mapAssetBatches(data.assets, async (metadata) => {
    if (!env.MEDIA) throw new Error("asset_storage_unavailable");
    const object = await env.MEDIA.get(String(metadata.r2_key));
    if (!object) throw new Error("asset_storage_unavailable");
    const bytes = new Uint8Array(await object.arrayBuffer());
    return { metadata, sha256: await sha256(bytes), contentBase64: base64(bytes) };
  });
  return assertBackupSize({ manifest, data, assets });
}


type RestoreConflict = { domain: string; code: string; key: string; message: string };

const duplicateConflicts = (domain: string, rows: Record<string, unknown>[], keyOf: (row: Record<string, unknown>) => string, code = "duplicate_backup_id") => {
  const seen = new Set<string>(); const conflicts: RestoreConflict[] = [];
  for (const row of rows) {
    const key = keyOf(row);
    if (seen.has(key)) conflicts.push({ domain, code, key, message: "백업 파일 안에 같은 키가 반복됩니다." });
    seen.add(key);
  }
  return conflicts;
};

const duplicateLogicalConflicts = (domain: string, rows: Record<string, unknown>[], keyOf: (row: Record<string, unknown>) => string) => {
  const seen = new Map<string, string>(); const conflicts: RestoreConflict[] = [];
  for (const row of rows) {
    const key = keyOf(row); const rowId = String(row.id);
    if (seen.has(key) && seen.get(key) !== rowId) conflicts.push({ domain, code: "duplicate_backup_key", key, message: "백업 파일 안에 같은 키가 반복됩니다." });
    seen.set(key, rowId);
  }
  return conflicts;
};

const stable = (value: unknown): unknown => Array.isArray(value) ? value.map(stable)
  : value && typeof value === "object" ? Object.fromEntries(Object.entries(value).sort(([left], [right]) => left.localeCompare(right)).map(([key, item]) => [key, stable(item)]))
  : value;
const same = (a: unknown, b: unknown) => JSON.stringify(stable(a)) === JSON.stringify(stable(b));
const without = (row: Record<string, unknown>, keys: string[]) => Object.fromEntries(Object.entries(row).filter(([key]) => !keys.includes(key)));
type OrderedMappings = { targets: string[]; bySource: Map<string, number[]> };
export const createOrderedMappings = (): OrderedMappings => ({ targets: [], bySource: new Map() });
export const addOrderedMapping = (mappings: OrderedMappings, sourceId: string, targetId: string) => {
  const order = mappings.targets.length;
  mappings.targets.push(targetId);
  const orders = mappings.bySource.get(sourceId);
  if (orders) orders.push(order); else mappings.bySource.set(sourceId, [order]);
};
export const resolveMappedId = (mappings: OrderedMappings, value: string) => {
  let current = value;
  let lastOrder = -1;
  while (true) {
    const orders = mappings.bySource.get(current);
    let low = 0;
    let high = orders?.length ?? 0;
    while (low < high) {
      const middle = (low + high) >>> 1;
      if (orders![middle] <= lastOrder) low = middle + 1; else high = middle;
    }
    const nextOrder = orders?.[low];
    if (nextOrder === undefined) return current;
    current = mappings.targets[nextOrder];
    lastOrder = nextOrder;
  }
};

export async function copyBackupForAccount(source: BackupPackage, accountId: string) {
  const backup = structuredClone(source);
  backup.data.field_translations ??= [];
  backup.data.category_signs ??= [];
  backup.data.product_catalog_links ??= [];
  backup.data.product_catalog_translation_sources ??= [];
  const ids = new Map<string, string>();
  const remap = async (kind: string, value: string) => {
    const key = `${kind}:${value}`;
    if (!ids.has(key)) {
      const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`${accountId}:${source.manifest.accountId ?? source.manifest.exportedAt}:${key}`)));
      digest[6] = (digest[6] & 15) | 80; digest[8] = (digest[8] & 63) | 128;
      const hex = [...digest.subarray(0, 16)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
      ids.set(key, `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`);
    }
    return ids.get(key)!;
  };
  for (const row of backup.data.categories) { row.id = await remap("categories", row.id); if (row.parent_id) row.parent_id = await remap("categories", row.parent_id); if (row.default_template_key) row.default_template_key = await remap("template_key", row.default_template_key); }
  for (const row of backup.data.design_favorites ?? []) if (row.source === "saved") row.family = await remap("template_key", row.family);
  for (const row of backup.data.category_signs) {
    row.id = await remap("category_signs", row.id);
    if (row.asset_id) row.asset_id = await remap("assets", row.asset_id);
    if (row.category_id) row.category_id = await remap("categories", row.category_id);
  }
  for (const row of backup.data.products) { row.id = await remap("products", row.id); row.category_id = await remap("categories", row.category_id); if (row.template_key_override) row.template_key_override = await remap("template_key", row.template_key_override); }
  for (const row of backup.data.product_offers) { row.id = await remap("product_offers", row.id); row.product_id = await remap("products", row.product_id); }
  for (const row of backup.data.field_translations) {
    row.id=await remap("field_translations",row.id);
    row.target_id=await remap(row.target_kind==="product"?"products":"category_signs",row.target_id);
  }
  for (const table of [backup.data.product_localizations, backup.data.translation_drafts, backup.data.translation_reviews]) for (const row of table) row.product_id = await remap("products", row.product_id);
  for (const row of backup.data.product_catalog_links) { row.id=await remap("product_catalog_links",row.id); row.product_id=await remap("products",row.product_id); row.request_id=null; }
  for (const row of backup.data.product_catalog_translation_sources) {
    row.product_id=await remap("products",row.product_id);
    try { const provenance=JSON.parse(row.provenance_json); provenance.productId=row.product_id; row.provenance_json=JSON.stringify(provenance); }
    catch { throw new Error("invalid_catalog_provenance"); }
  }
  for (const row of backup.data.assets) row.id = await remap("assets", row.id);
  for (const item of backup.assets) item.metadata.id = await remap("assets", item.metadata.id);
  for (const row of backup.data.templates) {
    row.id = await remap("templates", row.id); row.template_key = await remap("template_key", row.template_key);
    try {
      const config = JSON.parse(row.config_json) as { schemaVersion?: number; blocks?: Array<{ type?: string; assetId?: string }>; canvas?: { backgroundAssetId?: string | null } };
      if (row.design_type === "category") {
        const categoryConfig = config as { image?: { assetId?: string | null } | null };
        if (categoryConfig.image?.assetId) categoryConfig.image.assetId = await remap("assets", categoryConfig.image.assetId);
        row.config_json = JSON.stringify(config);
      } else if ((config.schemaVersion === 2 || config.schemaVersion === 3)) {
        for (const block of config.blocks ?? []) if (block.type === "image" && block.assetId) block.assetId = await remap("assets", block.assetId);
        if (config.canvas?.backgroundAssetId) config.canvas.backgroundAssetId = await remap("assets", config.canvas.backgroundAssetId);
        row.config_json = JSON.stringify(config);
      }
    } catch { /* Existing config validation reports malformed backup content. */ }
  }
  for (const row of backup.data.print_sets) {
    row.id = await remap("print_sets", row.id);
    try {
      if(row.print_schema_version===3){row.items_json=await remapCommonSet(row.items_json,remap);continue;}
      const items = JSON.parse(row.items_json) as Array<{ productId?: string; signId?: string }>;
      for (const item of items) {
        if (item.productId) item.productId = await remap("products", item.productId);
        if (item.signId) item.signId = await remap("category_signs", item.signId);
      }
      row.items_json = JSON.stringify(items);
    } catch { /* Existing reference validation reports malformed backup content. */ }
  }
  const snapshotReferenceKind = (path: string[], key: string) => {
    const ancestors = path.filter((part) => !/^\d+$/.test(part));
    const has = (name: string) => ancestors.includes(name);
    if (key === "productId") return "products";
    if (key === "categoryId") return "categories";
    if (key === "signId") return "category_signs";
    if (key === "templateKey" || key === "templateKeyOverride") return "template_key";
    if ((key === "assetId" || key === "backgroundAssetId") && has("config")) return "assets";
    if (key !== "id") return undefined;
    const parent = ancestors.at(-1);
    if (has("pages") && has("items")) return "print_tag";
    if (has("tags") && !has("product")) return "print_tag";
    if (has("categoryPath")) return "categories";
    if (has("offers")) return "product_offers";
    if (parent === "template") return "templates";
    if (parent === "product") return "products";
    return undefined;
  };
  const remapSnapshot = async (value: unknown, path: string[] = []): Promise<unknown> => {
    if (Array.isArray(value)) return Promise.all(value.map((item, index) => remapSnapshot(item, [...path, String(index)])));
    if (!value || typeof value !== "object") return value;
    const entries = await Promise.all(Object.entries(value).map(async ([key, item]) => {
      const kind = snapshotReferenceKind(path, key);
      const next = kind && typeof item === "string" ? await remap(kind, item) : await remapSnapshot(item, [...path, key]);
      return [key, next] as const;
    }));
    return Object.fromEntries(entries);
  };
  for (const row of backup.data.print_jobs) {
    row.id = await remap("print_jobs", row.id);
    try {
      if(row.print_schema_version===3){row.snapshot_json=await remapCommonSnapshot(row.snapshot_json,remap);continue;}
      row.snapshot_json = JSON.stringify(await remapSnapshot(JSON.parse(row.snapshot_json)));
    } catch { /* Saved print history remains available if its snapshot is malformed. */ }
  }
  backup.manifest.accountId = accountId;
  return backup;
}

async function restorePlan(env: BackupEnv, raw: unknown) {
  const input = restoreInputSchema.parse(raw);
  const { mode } = input;
  const foreign = input.backup.manifest.accountId !== env.DB.accountId;
  if (foreign && !input.copyForeign) throw new Error("backup_owner_mismatch");
  const backup = foreign ? await copyBackupForAccount(input.backup, env.DB.accountId) : input.backup;
  const currentFavorites = (await env.DB.prepare(`SELECT source,family FROM design_favorites WHERE ${owner(env.DB)}`).all<DesignFavorite>()).results;
  const incomingFavorites = backup.data.design_favorites ?? [];
  const currentFavoriteKeys = new Set(currentFavorites.map(favoriteKey)), incomingFavoriteKeys = new Set(incomingFavorites.map(favoriteKey));
  const newFavorites = incomingFavorites.filter(row => !currentFavoriteKeys.has(favoriteKey(row)));
  const removedFavorites = mode === "overwrite" && backup.data.design_favorites !== undefined ? currentFavorites.filter(row => !incomingFavoriteKeys.has(favoriteKey(row))) : [];
  const commonReferenceMaps:Record<string,Map<string,string>>={products:new Map(),category_signs:new Map(),templates:new Map()};
  for (const table of tables) {
    if (!rootTables.has(table) && table !== "product_offers") continue;
    const ids = (backup.data[table] ?? []).map((row) => (row as { id: string }).id);
    const condition = rootTables.has(table) ? `NOT (${owner(env.DB)}) OR owner_id IS NULL`
      : `product_id NOT IN (SELECT id FROM products WHERE ${owner(env.DB)})`;
    const collision = await env.DB.prepare(`SELECT 1 FROM ${table} WHERE id IN (SELECT value FROM json_each(?)) AND (${condition}) LIMIT 1`).bind(JSON.stringify(ids)).first();
    if (collision) throw new Error("backup_owner_mismatch");
  }
  if (new TextEncoder().encode(JSON.stringify(backup)).byteLength > MAX_BACKUP_BYTES) throw new Error("backup_too_large");
  const logicalText = (value: unknown) => String(value).normalize("NFKC").trim().replace(/\s+/g, " ").toLocaleLowerCase("ko");
  const backupCategoriesById = new Map(backup.data.categories.map((row) => [row.id, row]));
  const backupPaths = new Map<string, string[]>();
  const backupPath = (row: (typeof backup.data.categories)[number], seen = new Set<string>()): string[] => {
    const cached = backupPaths.get(row.id);
    if (cached) return cached;
    if (seen.has(row.id)) return [];
    seen.add(row.id);
    const parent = row.parent_id ? backupCategoriesById.get(row.parent_id) : undefined;
    if (row.parent_id && !parent) return [];
    const path = parent ? [...backupPath(parent, seen), logicalText(row.name_ko)] : [logicalText(row.name_ko)];
    if (!path.length || path.length > 3) return [];
    backupPaths.set(row.id, path);
    return path;
  };
  const originalBackupPaths = new Map(backup.data.categories.map((row) => [row, backupPath(row)]));
  const conflicts = [
    ...duplicateConflicts("design_favorites", incomingFavorites, row => favoriteKey(row as DesignFavorite)),
    ...duplicateConflicts("categories", backup.data.categories, (row) => String(row.id)),
    ...duplicateConflicts("category_signs", backup.data.category_signs, (row) => String(row.id)),
    ...duplicateConflicts("products", backup.data.products, (row) => String(row.id)),
    ...duplicateConflicts("product_offers", backup.data.product_offers, (row) => String(row.id)),
    ...duplicateConflicts("assets", backup.data.assets, (row) => String(row.id)),
    ...duplicateConflicts("templates", backup.data.templates, (row) => String(row.id)),
    ...duplicateConflicts("print_sets", backup.data.print_sets, (row) => String(row.id)),
    ...duplicateConflicts("print_jobs", backup.data.print_jobs, (row) => String(row.id)),
    ...duplicateConflicts("product_localizations", backup.data.product_localizations, (row) => `${row.product_id}\0${row.locale}`),
    ...duplicateConflicts("translation_drafts", backup.data.translation_drafts, (row) => `${row.product_id}\0${row.locale}`),
    ...duplicateConflicts("translation_reviews", backup.data.translation_reviews, (row) => `${row.product_id}\0${row.locale}\0${row.translation_hash}`),
    ...duplicateConflicts("product_catalog_links",backup.data.product_catalog_links,row=>`${row.catalog_product_id}\0${row.package_id ?? ""}`),
    ...duplicateConflicts("product_catalog_translation_sources",backup.data.product_catalog_translation_sources,row=>`${row.product_id}\0${row.locale}`),
    ...duplicateConflicts("asset_contents", backup.assets, (row) => String((row.metadata as Record<string, unknown>).id)),
    ...duplicateLogicalConflicts("categories", backup.data.categories, (row) => originalBackupPaths.get(row as (typeof backup.data.categories)[number])!.join("\0")),
    ...duplicateLogicalConflicts("category_signs", backup.data.category_signs, (row) => String(row.normalized_name)),
    ...duplicateLogicalConflicts("products", backup.data.products, (row) => `${row.category_id}\0${logicalText(row.name_ko_normalized)}`),
    ...duplicateLogicalConflicts("templates", backup.data.templates, (row) => `${row.template_key}\0${row.version}`),
  ];
  for (const category of backup.data.categories) if (!backupPath(category).length) conflicts.push({
    domain: "categories", code: "invalid_category_hierarchy", key: category.id,
    message: "분류 부모 관계는 백업 안에서 순환 없이 최대 3단계여야 합니다.",
  });
  const backupBytes = new Map<string, Uint8Array>();
  for (const asset of backup.assets) {
    try {
      const bytes = unbase64(asset.contentBase64);
      if (await sha256(bytes) !== asset.sha256) conflicts.push({
        domain: "assets", code: "asset_checksum_mismatch", key: asset.metadata.id,
        message: "이미지 검사값이 백업 내용과 다릅니다.",
      });
      else backupBytes.set(asset.metadata.id, bytes);
    } catch {
      conflicts.push({ domain: "assets", code: "invalid_asset_content", key: asset.metadata.id, message: "이미지 원본을 읽을 수 없습니다." });
    }
  }
  const [currentCategories, currentProducts, currentOffers, currentLocalizations, currentDrafts, currentReviews,
    currentAssets, currentTemplates, currentPrintSets, currentPrintJobs, currentCategorySigns, currentFieldTranslations] = await Promise.all([
    backupRows(env.DB, "categories"),
    backupRows(env.DB, "products"),
    backupRows(env.DB, "product_offers"),
    backupRows(env.DB, "product_localizations"),
    backupRows(env.DB, "translation_drafts"),
    backupRows(env.DB, "translation_reviews"),
    backupRows(env.DB, "assets"),
    backupRows(env.DB, "templates"),
    backupRows(env.DB, "print_sets"),
    backupRows(env.DB, "print_jobs"),
    backupRows(env.DB, "category_signs"),
    backupRows(env.DB, "field_translations"),
  ]);
  const categoriesById = new Map(currentCategories.results.map((row) => [String(row.id), row]));
  const currentCategoryById = new Map(currentCategories.results.map((row) => [String(row.id), row]));
  const currentPath = (row: Record<string, unknown>): string[] => {
    const parent = row.parent_id ? currentCategoryById.get(String(row.parent_id)) : undefined;
    return parent ? [...currentPath(parent), logicalText(row.name_ko)] : [logicalText(row.name_ko)];
  };
  const categoriesByPath = new Map(currentCategories.results.map((row) => [currentPath(row).join("\0"), row]));
  let mapped = 0;
  const categoryIdMap = createOrderedMappings();
  for (const category of [...backup.data.categories].sort((left, right) => originalBackupPaths.get(left)!.length - originalBackupPaths.get(right)!.length)) {
    const byId = categoriesById.get(category.id); const byPath = categoriesByPath.get(originalBackupPaths.get(category)!.join("\0"));
    if (byId && byPath && byId.id !== byPath.id) {
      conflicts.push({ domain: "categories", code: "ambiguous_identity", key: category.id, message: "분류 ID와 이름이 서로 다른 기존 분류를 가리킵니다." });
      continue;
    }
    const targetId = String(byId?.id ?? byPath?.id ?? category.id);
    if (targetId !== category.id) {
      const sourceId = category.id;
      category.id = targetId;
      addOrderedMapping(categoryIdMap, sourceId, targetId); mapped += 1;
    }
  }
  for (const category of backup.data.categories) {
    if (category.parent_id) category.parent_id = resolveMappedId(categoryIdMap, category.parent_id);
  }
  for (const product of backup.data.products) product.category_id = resolveMappedId(categoryIdMap, product.category_id);
  for (const phrase of backup.data.category_signs) if (phrase.category_id) phrase.category_id = resolveMappedId(categoryIdMap, phrase.category_id);
  const categoryIds = new Set(backup.data.categories.map((category) => category.id));
  for (const product of backup.data.products) if (!categoryIds.has(product.category_id)) conflicts.push({
    domain: "products", code: "missing_category", key: product.id,
    message: "상품이 참조하는 분류가 백업에 없습니다.",
  });
  const productIds = new Set(backup.data.products.map((product) => product.id));
  for (const phrase of backup.data.category_signs) if (phrase.category_id && !categoryIds.has(phrase.category_id)) conflicts.push({domain:"category_signs",code:"missing_category",key:phrase.id,message:"팜플렛 분류가 백업에 없습니다."});
  const categorySignsById = new Map(currentCategorySigns.results.map((row) => [String(row.id), row]));
  const categorySignsByName = new Map(currentCategorySigns.results.map((row) => [String(row.normalized_name), row]));
  const replaceSignReferences = (value: unknown, mappings: OrderedMappings): unknown => {
    if (Array.isArray(value)) return value.map((item) => replaceSignReferences(item, mappings));
    if (!value || typeof value !== "object") return value;
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [
      key, key === "signId" && typeof item === "string" ? resolveMappedId(mappings, item) : replaceSignReferences(item, mappings),
    ]));
  };
  type ParsedSignSet = { row: BackupPackage["data"]["print_sets"][number]; value: unknown; invalid: boolean };
  type ParsedSignJob = { row: BackupPackage["data"]["print_jobs"][number]; value: unknown; invalid: boolean };
  const signIdMap = createOrderedMappings();
  let parsedSignSets: ParsedSignSet[] | undefined;
  let parsedSignJobs: ParsedSignJob[] | undefined;
  const prepareSignReferences = () => {
    parsedSignSets ??= backup.data.print_sets.filter((row) => row.print_schema_version !== 3).map((row) => {
      try { return { row, value: JSON.parse(row.items_json), invalid: false }; }
      catch { return { row, value: null, invalid: true }; }
    });
    parsedSignJobs ??= backup.data.print_jobs.filter((row) => row.print_schema_version !== 3).map((row) => {
      try { return { row, value: JSON.parse(row.snapshot_json), invalid: false }; }
      catch { return { row, value: null, invalid: true }; }
    });
  };
  for (const sign of backup.data.category_signs) {
    const byId = categorySignsById.get(sign.id);
    const byName = categorySignsByName.get(sign.normalized_name);
    if (byId && byName && byId.id !== byName.id) {
      conflicts.push({ domain: "category_signs", code: "ambiguous_identity", key: sign.id, message: "category sign identity is ambiguous" });
      continue;
    }
    const targetId = String(byId?.id ?? byName?.id ?? sign.id);
    if (targetId !== sign.id) {
      const sourceId = sign.id;
      sign.id = targetId;
      addOrderedMapping(signIdMap, sourceId, targetId);
      commonReferenceMaps.category_signs.set(sourceId, targetId);
      prepareSignReferences();
      for (const parsed of parsedSignSets ?? []) if (parsed.invalid) conflicts.push({ domain: "print_sets", code: "invalid_reference_json", key: parsed.row.id, message: "invalid print-set reference JSON" });
      for (const parsed of parsedSignJobs ?? []) if (parsed.invalid) conflicts.push({ domain: "print_jobs", code: "invalid_reference_json", key: parsed.row.id, message: "invalid print-job reference JSON" });
      mapped += 1;
    }
  }
  for (const row of backup.data.field_translations) if (row.target_kind === "phrase") row.target_id = resolveMappedId(signIdMap, row.target_id);
  for (const parsed of parsedSignSets ?? []) if (!parsed.invalid) parsed.row.items_json = JSON.stringify(replaceSignReferences(parsed.value, signIdMap));
  for (const parsed of parsedSignJobs ?? []) if (!parsed.invalid) parsed.row.snapshot_json = JSON.stringify(replaceSignReferences(parsed.value, signIdMap));
  for (const printSet of backup.data.print_sets) {
    if(printSet.print_schema_version===3)continue;
    try {
      if (printSet.design_type === "category") {
        categoryQueueSchema.parse(JSON.parse(printSet.items_json));
      } else {
        const items = printQueueSchema.parse(JSON.parse(printSet.items_json));
        if (items.some((item) => !productIds.has(item.productId))) conflicts.push({
          domain: "print_sets", code: "missing_product", key: printSet.id, message: "print set references a missing product",
        });
      }
    } catch {
      conflicts.push({ domain: "print_sets", code: "invalid_reference_json", key: printSet.id, message: "invalid print-set reference JSON" });
    }
  }
  const productsById = new Map(currentProducts.results.map((row) => [String(row.id), row]));
  const productKey = (row: Record<string, unknown>) => `${row.category_id}\0${String(row.name_ko_normalized).normalize("NFKC").trim().toLocaleLowerCase("ko")}`;
  const productsByKey = new Map(currentProducts.results.filter((row) => row.deleted_at === null).map((row) => [productKey(row), row]));
  type ParsedProductSet = { row: BackupPackage["data"]["print_sets"][number]; value: unknown[]; invalid: boolean };
  const productIdMap = createOrderedMappings();
  let parsedProductSets: ParsedProductSet[] | undefined;
  const prepareProductReferences = () => {
    parsedProductSets ??= backup.data.print_sets.filter((row) => row.print_schema_version !== 3).map((row) => {
      try {
        const value = JSON.parse(row.items_json) as unknown;
        if (!Array.isArray(value) || value.some((item) => item === null)) throw new Error();
        return { row, value, invalid: false };
      } catch { return { row, value: [], invalid: true }; }
    });
  };
  for (const product of backup.data.products) {
    const byId = productsById.get(product.id); const byKey = product.deleted_at === null ? productsByKey.get(productKey(product)) : undefined;
    if (byId && byKey && byId.id !== byKey.id) {
      conflicts.push({ domain: "products", code: "ambiguous_identity", key: product.id, message: "상품 ID와 분류·상품명이 서로 다른 기존 상품을 가리킵니다." });
      continue;
    }
    const targetId = String(byId?.id ?? byKey?.id ?? product.id);
    if (targetId !== product.id) {
      const sourceId = product.id;
      product.id = targetId;
      productIds.delete(sourceId); productIds.add(targetId);
      addOrderedMapping(productIdMap, sourceId, targetId); mapped += 1;
      commonReferenceMaps.products.set(sourceId, targetId);
      prepareProductReferences();
      for (const parsed of parsedProductSets ?? []) if (parsed.invalid) conflicts.push({ domain: "print_sets", code: "invalid_reference_json", key: parsed.row.id, message: "저장한 인쇄 목록을 읽을 수 없습니다." });
    }
  }
  for (const offer of backup.data.product_offers) offer.product_id = resolveMappedId(productIdMap, offer.product_id);
  for (const row of backup.data.field_translations) if (row.target_kind === "product") row.target_id = resolveMappedId(productIdMap, row.target_id);
  for (const table of [backup.data.product_localizations, backup.data.translation_drafts, backup.data.translation_reviews,
    backup.data.product_catalog_links, backup.data.product_catalog_translation_sources]) {
    for (const row of table) row.product_id = resolveMappedId(productIdMap, row.product_id);
  }
  for (const parsed of parsedProductSets ?? []) if (!parsed.invalid) {
    for (const item of parsed.value) {
      if (item && typeof item === "object" && "productId" in item && typeof (item as { productId?: unknown }).productId === "string") {
        (item as { productId: string }).productId = resolveMappedId(productIdMap, (item as { productId: string }).productId);
      }
    }
    parsed.row.items_json = JSON.stringify(parsed.value);
  }
  for (const [domain, rows] of [
    ["product_offers", backup.data.product_offers],
    ["product_localizations", backup.data.product_localizations],
    ["translation_drafts", backup.data.translation_drafts],
    ["translation_reviews", backup.data.translation_reviews],
    ["product_catalog_links",backup.data.product_catalog_links],
    ["product_catalog_translation_sources",backup.data.product_catalog_translation_sources],
  ] as const) for (const row of rows) if (!productIds.has(row.product_id)) conflicts.push({
    domain, code: "missing_product", key: "id" in row ? String(row.id) : `${row.product_id}\0${"locale" in row ? row.locale : ""}`,
    message: "하위 정보가 참조하는 상품이 백업에 없습니다.",
  });
  for (const printSet of backup.data.print_sets) {
    if(printSet.print_schema_version===3)continue;
    if (printSet.design_type === "category") continue;
    try {
      const items = printQueueSchema.parse(JSON.parse(printSet.items_json));
      if (items.some((item) => !productIds.has(item.productId))) conflicts.push({
        domain: "print_sets", code: "missing_product", key: printSet.id, message: "인쇄 목록이 참조하는 상품이 백업에 없습니다.",
      });
    } catch {
      conflicts.push({ domain: "print_sets", code: "invalid_reference_json", key: printSet.id, message: "저장한 인쇄 목록을 읽을 수 없습니다." });
    }
  }
  const currentOffersById = new Map(currentOffers.results.map((row) => [String(row.id), row]));
  for (const offer of backup.data.product_offers) {
    const current = currentOffersById.get(offer.id);
    if (productIds.has(offer.product_id) && current && current.product_id !== offer.product_id) conflicts.push({
      domain: "product_offers", code: "ambiguous_identity", key: offer.id,
      message: "같은 가격 ID가 다른 상품에 이미 연결되어 있습니다.",
    });
  }
  const offersByProduct = (rows: Record<string, unknown>[]) => rows.reduce((groups, row) => {
    const key = String(row.product_id); const group = groups.get(key);
    if (group) group.push(row); else groups.set(key, [row]);
    return groups;
  }, new Map<string, Record<string, unknown>[]>());
  const currentOffersByProduct = offersByProduct(currentOffers.results);
  const backupOffersByProduct = offersByProduct(backup.data.product_offers);
  for (const [productId, offers] of backupOffersByProduct) {
    const parsedOffers = offersSchema.safeParse(offers.map((offer) => ({
      quantity: offer.quantity,
      unitCode: offer.unit_code,
      unitCustomKo: offer.unit_custom_ko ?? undefined,
      priceKrw: offer.price_krw,
    })));
    if (!parsedOffers.success) conflicts.push({
      domain: "product_offers", code: "invalid_offers", key: productId,
      message: "諛깆뾽 ?⑦뭹 媛寃⑹? ?좏슚?섏? ?딆븘 ?ㅼ떆?섏? ?딄퀬 ?ㅻ뒗 ?⑸땲??.",
    });
  }
  const changedCategories = backup.data.categories.filter((row) => {
    const current = categoriesById.get(row.id);
    return !current || !same(without(current, ["created_at", "updated_at"]), without(row, ["created_at", "updated_at"]));
  }).sort((left, right) => originalBackupPaths.get(left)!.length - originalBackupPaths.get(right)!.length);
  const changedProducts = backup.data.products.map((row) => {
    const current = productsById.get(row.id);
    const productChanged = !current || !same(
      without(current, ["version", "created_by", "created_at", "updated_by", "updated_at"]),
      without(row, ["version", "created_by", "created_at", "updated_by", "updated_at"]),
    );
    const offerChanged = !same(
      (currentOffersByProduct.get(row.id) ?? []).map((offer) => without(offer, ["created_at", "updated_at"])),
      (backupOffersByProduct.get(row.id) ?? []).map((offer) => without(offer, ["created_at", "updated_at"])),
    );
    if (!productChanged && !offerChanged) return null;
    return current ? { ...row, version: Number(current.version) + 1 } : row;
  }).filter((row): row is BackupPackage["data"]["products"][number] => row !== null);
  const composite = (row: Record<string, unknown>) => `${row.product_id}\0${row.locale}`;
  const reviewKey = (row: Record<string, unknown>) => `${composite(row)}\0${row.translation_hash}`;
  const changedRows = <T extends Record<string, unknown>>(rows: T[], current: Record<string, unknown>[], keyOf: (row: Record<string, unknown>) => string) => {
    const byKey = new Map(current.map((row) => [keyOf(row), row]));
    return rows.filter((row) => !same(row, byKey.get(keyOf(row))));
  };
  const currentLocalizationsByKey = new Map(currentLocalizations.results.map((row) => [composite(row), row]));
  let changedLocalizations = changedRows(backup.data.product_localizations, currentLocalizations.results, composite);
  const approvedLocalizationConflicts: RestoreConflict[] = [];
  changedLocalizations = changedLocalizations.filter((row) => {
    const current = currentLocalizationsByKey.get(composite(row));
    const approved = current && String(current.approved_at ?? "").trim().length > 0;
    if (!approved) return true;
    if (!same(without(current, ["updated_at"]), without(row, ["updated_at"]))) approvedLocalizationConflicts.push({
      domain: "product_localizations", code: "approved_translation_immutable", key: composite(row),
      message: "Approved translations are preserved and cannot be replaced by a backup.",
    });
    return false;
  });
  conflicts.push(...approvedLocalizationConflicts);
  const changedDrafts = changedRows(backup.data.translation_drafts, currentDrafts.results, composite);
  const currentLinks = await backupRows(env.DB,"product_catalog_links");
  const currentCatalogSources = await backupRows(env.DB,"product_catalog_translation_sources");
  const catalogLinkKey = (row: Record<string, unknown>) => JSON.stringify([row.catalog_product_id,row.package_id,row.product_id]);
  const currentLinksByKey = new Map<string, Record<string, unknown>>();
  for (const current of currentLinks.results) if (!currentLinksByKey.has(catalogLinkKey(current))) currentLinksByKey.set(catalogLinkKey(current), current);
  const changedCatalogLinks = changedRows(backup.data.product_catalog_links,currentLinks.results,row=>`${row.catalog_product_id}\0${row.package_id ?? ""}`);
  const [descriptions,packages,linkIds]=await Promise.all([
    catalogRestoreRows<{id:string;catalog_product_id:string;version:number}>(env.DB,"catalog_descriptions",changedCatalogLinks.map(row=>row.description_id),"catalog_product_id,version"),
    catalogRestoreRows<{id:string;catalog_product_id:string;version:number}>(env.DB,"catalog_packages",changedCatalogLinks.map(row=>row.package_id),"catalog_product_id,version"),
    catalogRestoreRows<{id:string;account_id:string}>(env.DB,"product_catalog_links",changedCatalogLinks.map(row=>row.id),"account_id"),
  ]);
  const collisionKey=(row:{catalog_product_id:string;package_id:string|null})=>JSON.stringify([row.catalog_product_id,row.package_id ?? ""]);
  const keys=[...new Map(changedCatalogLinks.map(row=>[collisionKey(row),{catalog_product_id:row.catalog_product_id,package_id:row.package_id ?? ""}])).values()];
  const collisions=new Map<string,{product_id:string}>();
  for(let start=0;start<keys.length;start+=100) {
    const rows=await env.DB.prepare(`SELECT l.catalog_product_id,l.package_id,l.product_id FROM json_each(?) requested CROSS JOIN product_catalog_links l
      WHERE l.account_id=? AND l.catalog_product_id=json_extract(requested.value,'$.catalog_product_id') AND COALESCE(l.package_id,'')=json_extract(requested.value,'$.package_id')`)
      .bind(JSON.stringify(keys.slice(start,start+100)),env.DB.accountId).all<{catalog_product_id:string;package_id:string|null;product_id:string}>();
    for(const row of rows.results)collisions.set(collisionKey(row),row);
  }
  for (const row of changedCatalogLinks) {
    const description=row.description_id ? descriptions.get(row.description_id) : null;
    const packaging=row.package_id ? packages.get(row.package_id) : null;
    if(description && (description.catalog_product_id!==row.catalog_product_id || description.version!==row.description_version)
      || packaging && (packaging.catalog_product_id!==row.catalog_product_id || packaging.version!==row.package_version)) {
      conflicts.push({domain:"product_catalog_links",code:"invalid_catalog_reference",key:row.id,message:"공용 상품의 설명 또는 포장 연결이 일치하지 않습니다."});
    }
    for(const field of [row.package_snapshot_json,row.override_json]) {
      try { const value=JSON.parse(field); if(!value || typeof value!=="object" || Array.isArray(value)) throw new Error(); }
      catch { conflicts.push({domain:"product_catalog_links",code:"invalid_catalog_snapshot",key:row.id,message:"상품 포장 정보를 읽을 수 없습니다."}); }
    }
    const collision=collisions.get(collisionKey(row));
    if(collision && collision.product_id!==row.product_id) conflicts.push({domain:"product_catalog_links",code:"catalog_link_conflict",key:row.id,message:"공용 상품이 다른 계정 상품에 연결되어 있습니다."});
    const idCollision=linkIds.get(row.id);
    if(idCollision && idCollision.account_id!==env.DB.accountId) throw new Error("backup_owner_mismatch");
    const sameLink=currentLinksByKey.get(catalogLinkKey(row));
    if(sameLink) row.id=String(sameLink.id);
  }
  const changedCatalogSources = changedRows(backup.data.product_catalog_translation_sources,currentCatalogSources.results,composite);
  for(const row of changedCatalogSources) {
    try {
      const provenance=JSON.parse(row.provenance_json);
      if(!provenance || provenance.productId!==row.product_id || provenance.sourceHash!==row.source_hash
        || provenance.translationHash!==row.translation_hash || provenance.id!==row.catalog_translation_id || provenance.locale!==row.locale) throw new Error();
    } catch { conflicts.push({domain:"product_catalog_translation_sources",code:"invalid_catalog_provenance",key:`${row.product_id}:${row.locale}`,message:"상품 번역의 출처 기록이 일치하지 않습니다."}); }
  }
  const reviewsByKey = new Map(currentReviews.results.map((row) => [reviewKey(row), row]));
  const newReviews = backup.data.translation_reviews.filter((row) => !reviewsByKey.has(reviewKey(row)));
  for (const review of backup.data.translation_reviews) {
    const current = reviewsByKey.get(reviewKey(review));
    if (current && !same(current, review)) conflicts.push({
      domain: "translation_reviews", code: "immutable_history_conflict", key: reviewKey(review),
      message: "같은 번역 검토 키의 기존 이력과 백업 내용이 다릅니다.",
    });
  }
  const assetsById = new Map(currentAssets.results.map((row) => [String(row.id), row]));
  const assetsByHash = new Map<string, Record<string, unknown>[]>();
  const assetHashById = new Map<string, string>();
  if (currentAssets.results.length && !env.MEDIA) throw new Error("asset_storage_unavailable");
  const currentHashes = await mapAssetBatches(currentAssets.results, async (current) => {
    const object = await env.MEDIA!.get(String(current.r2_key));
    if (!object) throw new Error("asset_storage_unavailable");
    return sha256(new Uint8Array(await object.arrayBuffer()));
  });
  for (const [index, hash] of currentHashes.entries()) {
    const current = currentAssets.results[index];
    const matches = assetsByHash.get(hash);
    if (matches) matches.push(current); else assetsByHash.set(hash, [current]);
    assetHashById.set(String(current.id), hash);
  }
  const backupAssetById = new Map(backup.assets.map((asset) => [asset.metadata.id, asset]));
  const assetIdMap = new Map<string, string>();
  const changedAssets: BackupPackage["data"]["assets"] = [];
  const newAssetUploads: { key: string; bytes: Uint8Array }[] = [];
  for (const metadata of backup.data.assets) {
    const content = backupAssetById.get(metadata.id);
    if (!content || !same(content.metadata, metadata)) {
      conflicts.push({ domain: "assets", code: "asset_metadata_mismatch", key: metadata.id, message: "이미지 정보와 원본 파일이 일치하지 않습니다." });
      continue;
    }
    const bytes = backupBytes.get(metadata.id);
    if (!bytes) continue;
    try { inspectImage(bytes, metadata.mime_type); } catch {
      conflicts.push({ domain: "assets", code: "invalid_asset_content", key: metadata.id, message: "지원하지 않는 이미지 원본입니다." });
      continue;
    }
    const byId = assetsById.get(metadata.id); const hashMatches = assetsByHash.get(content.sha256) ?? [];
    if (!byId && hashMatches.length > 1) {
      conflicts.push({ domain: "assets", code: "ambiguous_identity", key: metadata.id, message: "같은 원본을 가진 기존 이미지가 여러 개라 연결 대상을 정할 수 없습니다." });
      continue;
    }
    const current = byId ?? hashMatches[0];
    if (current && String(current.id) !== metadata.id) {
      const sourceId = metadata.id; metadata.id = String(current.id); content.metadata.id = metadata.id; mapped += 1;
      assetIdMap.set(sourceId, metadata.id);
    }
    if (current) {
      if (assetHashById.get(String(current.id)) !== content.sha256) {
        conflicts.push({ domain: "assets", code: "asset_content_conflict", key: metadata.id, message: "같은 이미지 ID의 기존 원본이 백업과 다릅니다." });
        continue;
      }
      const next = { ...metadata, r2_key: String(current.r2_key) };
      if (!same(current, next)) changedAssets.push(next);
    } else {
      const key = `accounts/${env.DB.accountId}/assets/restore-${crypto.randomUUID()}`;
      changedAssets.push({ ...metadata, r2_key: key }); newAssetUploads.push({ key, bytes });
    }
  }
  const backupAssetContentIds = new Set(backup.data.assets.map((row) => row.id));
  for (const asset of backup.assets) if (!backupAssetContentIds.has(asset.metadata.id)) conflicts.push({
    domain: "assets", code: "orphan_asset_content", key: asset.metadata.id, message: "연결할 이미지 정보가 없습니다.",
  });
  const assetIds = backupAssetContentIds;
  for (const phrase of backup.data.category_signs) {
    if (phrase.asset_id) phrase.asset_id = assetIdMap.get(phrase.asset_id) ?? phrase.asset_id;
    if (phrase.asset_id && !assetIds.has(phrase.asset_id)) conflicts.push({
      domain: "category_signs", code: "missing_asset", key: phrase.id, message: "팜플렛의 대표 이미지가 백업에 없습니다.",
    });
    if (!(phrase.title_ko ?? phrase.name).trim() && !phrase.body_ko.trim()) conflicts.push({
      domain: "category_signs", code: "empty_phrase", key: phrase.id, message: "제목이나 본문이 필요합니다.",
    });
  }
  const changedCategorySigns = backup.data.category_signs.filter((row) => {
    const current = categorySignsById.get(row.id);
    return !current || !same(without(current, ["version", "created_at", "updated_at"]), without(row, ["version", "created_at", "updated_at"]));
  }).map(row => {
    const current = categorySignsById.get(row.id);
    return current ? { ...row, version: Number(current.version) + 1, created_at: String(current.created_at) } : row;
  });
  const remapSnapshotAssets = (value: unknown, path: string[] = []): unknown => {
    if (Array.isArray(value)) return value.map((item, index) => remapSnapshotAssets(item, [...path, String(index)]));
    if (!value || typeof value !== "object") return value;
    const ancestors = path.filter((part) => !/^\d+$/.test(part));
    return Object.fromEntries(Object.entries(value).map(([key, item]) => {
      if ((key === "assetId" || key === "backgroundAssetId") && ancestors.includes("config") && typeof item === "string") {
        return [key, assetIdMap.get(item) ?? item];
      }
      return [key, remapSnapshotAssets(item, [...path, key])];
    }));
  };
  for (const job of backup.data.print_jobs) {
    if(job.print_schema_version===3)continue;
    try { job.snapshot_json = JSON.stringify(remapSnapshotAssets(JSON.parse(job.snapshot_json))); }
    catch { /* Saved print history remains available if its snapshot is malformed. */ }
  }
  for (const template of backup.data.templates) {
    if (template.design_type === "category") {
      try {
        const config = categoryDesignSchema.parse(JSON.parse(template.config_json));
        if (template.width_mm !== config.widthMm || template.height_mm !== config.heightMm) conflicts.push({
          domain: "templates", code: "invalid_template_config", key: template.id,
          message: "category template dimensions do not match its design config",
        });
        if (config.image?.assetId && assetIdMap.has(config.image.assetId)) config.image.assetId = assetIdMap.get(config.image.assetId)!;
        template.config_json = JSON.stringify(config);
        if (config.image?.assetId && !assetIds.has(config.image.assetId)) conflicts.push({
          domain: "templates", code: "missing_asset", key: template.id, message: "category design references a missing asset",
        });
      } catch {
        conflicts.push({ domain: "templates", code: "invalid_template_config", key: template.id, message: "invalid category design config" });
      }
      continue;
    }
    try {
      const config = templateConfigSchema.parse(JSON.parse(template.config_json));
      if ((config.schemaVersion === 2 || config.schemaVersion === 3)) {
        for (const block of config.blocks) if (block.type === "image" && assetIdMap.has(block.assetId)) block.assetId = assetIdMap.get(block.assetId)!;
        if (config.canvas.backgroundAssetId && assetIdMap.has(config.canvas.backgroundAssetId)) config.canvas.backgroundAssetId = assetIdMap.get(config.canvas.backgroundAssetId)!;
        template.config_json = JSON.stringify(config);
        const references = config.blocks.filter((block) => block.type === "image").map((block) => block.assetId);
        if (config.canvas.backgroundAssetId) references.push(config.canvas.backgroundAssetId);
        if (references.some((id) => !assetIds.has(id))) conflicts.push({
          domain: "templates", code: "missing_asset", key: template.id, message: "레이블이 참조하는 이미지가 백업에 없습니다.",
        });
      }
    } catch {
      conflicts.push({ domain: "templates", code: "invalid_template_config", key: template.id, message: "레이블 설정을 읽을 수 없습니다." });
    }
  }
  const templatesById = new Map(currentTemplates.results.map((row) => [String(row.id), row]));
  const templateKey = (row: Record<string, unknown>) => `${row.design_type ?? "label"}\0${row.template_key}\0${row.version}`;
  const templatesByKey = new Map(currentTemplates.results.map((row) => [templateKey(row), row]));
  const wrongTemplateKinds = new Set<string>();
  for (const template of backup.data.templates) {
    const byId = templatesById.get(template.id); const byKey = templatesByKey.get(templateKey(template));
    if (byId && String(byId.design_type ?? "label") !== template.design_type) {
      conflicts.push({ domain: "templates", code: "wrong_design_type", key: template.id, message: "template ID belongs to another design type" });
      wrongTemplateKinds.add(template.id);
      continue;
    }
    if (byId && byKey && byId.id !== byKey.id) {
      conflicts.push({ domain: "templates", code: "ambiguous_identity", key: template.id, message: "레이블 ID와 버전 키가 서로 다른 기존 레이블을 가리킵니다." });
      continue;
    }
    const targetId = String(byId?.id ?? byKey?.id ?? template.id);
    if (targetId !== template.id) { commonReferenceMaps.templates.set(template.id,targetId);template.id = targetId; mapped += 1; }
  }
  commonReferenceMaps.assets=assetIdMap;
  const remapCommon=async(kind:string,id:string)=>commonReferenceMaps[kind]?.get(id)??id;
  const commonTemplates=new Map(backup.data.templates.map(t=>[t.id,t]));
  const commonPhrases=new Set(backup.data.category_signs.map(p=>p.id));
  for(const set of backup.data.print_sets)if(set.print_schema_version===3){
    try{
      if(set.design_type!=="label")throw new Error("wrong_design_type");
      set.items_json=await remapCommonSet(set.items_json,remapCommon);
      const job=commonPrintInputSchema.parse(JSON.parse(set.items_json));
      for(const item of job.items){
        if(item.target.kind==="product"&&(!productIds.has(item.target.id)||(item.target.phraseId&&!commonPhrases.has(item.target.phraseId))))throw new Error("missing_product_or_phrase");
        if(item.target.kind==="phrase"&&!commonPhrases.has(item.target.id))throw new Error("missing_phrase");
        if(item.design.source==="saved"&&commonTemplates.get(item.design.id)?.version!==item.design.version)throw new Error("missing_design_version");
        const config=item.design.source==="inline"?item.design.config:undefined;
        const refs=[...Object.values(item.overrides).map(o=>o.assetId),config?.canvas.backgroundAssetId,...config?.blocks.flatMap(b=>b.type==="image"?[b.assetId]:[])??[]].filter((id):id is string=>Boolean(id));
        if(refs.some(id=>!assetIds.has(id)))throw new Error("missing_asset");
      }
    }catch{conflicts.push({domain:"print_sets",code:"invalid_reference_json",key:set.id,message:"공통 인쇄 목록의 내용·디자인·이미지 참조를 확인하세요."});}
  }
  for(const job of backup.data.print_jobs)if(job.print_schema_version===3){
    try{
      if(job.design_type!=="label")throw new Error("wrong_design_type");
      job.snapshot_json=await remapCommonSnapshot(job.snapshot_json,remapCommon);
      const snapshot=commonSnapshotSchema.parse(JSON.parse(job.snapshot_json));
      if(snapshot.tags.length!==job.item_count||snapshot.pages.length!==job.page_count||snapshot.resolved.some(item=>item.assetIds.some(id=>!assetIds.has(id))))throw new Error("invalid_snapshot_references");
    }catch{conflicts.push({domain:"print_jobs",code:"invalid_snapshot",key:job.id,message:"공통 인쇄 기록의 배치·글자 크기·이미지를 확인하세요."});}
  }
  const changedTemplates = backup.data.templates.filter((row) => {
    if (wrongTemplateKinds.has(row.id)) return false;
    const current = templatesById.get(row.id);
    const contentChanged = current && !same(without(current, ["updated_at", "deleted_at", "deleted_by", "is_active"]), without(row, ["updated_at", "deleted_at", "deleted_by", "is_active"]));
    if (current && row.design_type === "category" && contentChanged) conflicts.push({
      domain: "templates", code: "immutable_history_conflict", key: row.id, message: "category design versions are immutable once saved",
    });
    if (current && row.design_type !== "category" && String(current.status) !== "draft" && contentChanged) conflicts.push({
      domain: "templates", code: "immutable_history_conflict", key: row.id, message: "인쇄에 적용된 레이블 버전의 기존 내용과 백업이 다릅니다.",
    });
    return !current || (!contentChanged || (row.design_type !== "category" && String(current.status) === "draft")) && !same(current, row);
  });
  const printSetsById = new Map(currentPrintSets.results.map((row) => [String(row.id), row]));
  for (const printSet of backup.data.print_sets) {
    const current = printSetsById.get(printSet.id);
    if (current && (String(current.design_type ?? "label") !== printSet.design_type||Number(current.print_schema_version??1)!==printSet.print_schema_version)) conflicts.push({
      domain: "print_sets", code: "wrong_design_type", key: printSet.id, message: "print set ID belongs to another design type",
    });
  }
  const changedPrintSets = backup.data.print_sets.filter((row) => !same(printSetsById.get(row.id), row));
  for (const job of backup.data.print_jobs) if (job.print_schema_version!==3&&job.design_type === "category") {
    try {
      const snapshot = categorySnapshotSchema.parse(JSON.parse(job.snapshot_json));
      const references = [snapshot.config.image?.assetId, snapshot.template.config.image?.assetId]
        .filter((id): id is string => Boolean(id));
      if (references.some((id) => !assetIds.has(id))) throw new Error("missing_category_snapshot_asset");
    } catch {
      conflicts.push({ domain: "print_jobs", code: "invalid_snapshot", key: job.id, message: "invalid category print snapshot" });
    }
  }
  for (const job of backup.data.print_jobs) if (job.print_schema_version!==3&&job.design_type === "label") {
    try {
      const snapshot = JSON.parse(job.snapshot_json) as { designType?: string };
      if (snapshot.designType === "category"||snapshot.designType==="common") conflicts.push({
        domain: "print_jobs", code: "wrong_design_type", key: job.id, message: "label print job contains a category snapshot",
      });
    } catch { /* Existing label snapshot compatibility remains unchanged. */ }
  }
  const printJobsById = new Map(currentPrintJobs.results.map((row) => [String(row.id), row]));
  const newPrintJobs = backup.data.print_jobs.filter((row) => !printJobsById.has(row.id));
  for (const job of backup.data.print_jobs) {
    const current = printJobsById.get(job.id);
    if (current && !same(current, job)) conflicts.push({
      domain: "print_jobs", code: "immutable_history_conflict", key: job.id, message: "같은 인쇄 기록 ID의 기존 스냅샷과 백업이 다릅니다.",
    });
  }
  const fieldKey=(row:Record<string,unknown>)=>`${row.target_kind}\0${row.target_id}\0${row.field}\0${row.locale}`;
  const fieldsById=new Map(currentFieldTranslations.results.map(row=>[String(row.id),row]));
  const fieldsByKey=new Map(currentFieldTranslations.results.map(row=>[fieldKey(row),row]));
  const backupFieldCategorySignIds = new Set(backup.data.category_signs.map((row) => row.id));
  const incomingFieldIds = new Set(backup.data.field_translations.map((row) => row.id));
  conflicts.push(...duplicateConflicts("field_translations",backup.data.field_translations,row=>String(row.id)),
    ...duplicateLogicalConflicts("field_translations",backup.data.field_translations,fieldKey));
  for (const row of backup.data.field_translations) {
    const targetExists=row.target_kind==="product" ? productIds.has(row.target_id) : backupFieldCategorySignIds.has(row.target_id);
    if (!targetExists || await fieldSourceHash(row.target_kind,row.field,row.source_text)!==row.source_hash) conflicts.push({domain:"field_translations",code:"invalid_source",key:row.id,message:"번역 원문이나 연결 대상을 확인해 주세요."});
    const byId=fieldsById.get(row.id),byKey=fieldsByKey.get(fieldKey(row));
    if (byId && fieldKey(byId)!==fieldKey(row)) conflicts.push({domain:"field_translations",code:"ambiguous_identity",key:row.id,message:"번역 ID의 대상이 다릅니다."});
    if (!byId && byKey) { row.id=String(byKey.id); mapped++; }
  }
  const changedFieldTranslations=backup.data.field_translations.filter(row=> {
    const current=fieldsById.get(row.id);
    return !current || !same(without(current,["revision","updated_at"]),without(row,["revision","updated_at"]));
  }).map(row=>({...row,revision:crypto.randomUUID()}));
  const removedFieldTranslations=mode==="overwrite" ? currentFieldTranslations.results.filter(row=>!incomingFieldIds.has(String(row.id))) : [];
  const creates = changedFieldTranslations.filter(row=>!fieldsById.has(row.id)).length + changedCategories.filter((row) => !categoriesById.has(row.id)).length
    + changedCategorySigns.filter((row) => !categorySignsById.has(row.id)).length
    + changedProducts.filter((row) => !productsById.has(row.id)).length + newReviews.length
    + changedAssets.filter((row) => !assetsById.has(row.id)).length + changedTemplates.filter((row) => !templatesById.has(row.id)).length
    + changedPrintSets.filter((row) => !printSetsById.has(row.id)).length + newPrintJobs.length + newFavorites.length;
  const updates = changedFieldTranslations.length + changedCategories.length + changedCategorySigns.length + changedProducts.length + changedLocalizations.length + changedDrafts.length
    + changedAssets.length + changedTemplates.length + changedPrintSets.length + newReviews.length + newPrintJobs.length + changedCatalogLinks.length + changedCatalogSources.length + newFavorites.length - creates;
  const backupCategoryIds = new Set(backup.data.categories.map((row) => row.id));
  const backupCategorySignIds = new Set(backup.data.category_signs.map((row) => row.id));
  const backupProductIds = new Set(backup.data.products.map((row) => row.id));
  const backupAssetIds = new Set(backup.data.assets.map((row) => row.id));
  const backupTemplateIds = new Set(backup.data.templates.map((row) => row.id));
  const deactivateCategories = mode === "overwrite" ? currentCategories.results.filter((row) => !backupCategoryIds.has(String(row.id)) && row.is_active === 1) : [];
  const deactivateCategorySigns = mode === "overwrite" ? currentCategorySigns.results.filter((row) => !backupCategorySignIds.has(String(row.id)) && row.is_active === 1) : [];
  const deactivateProducts = mode === "overwrite" ? currentProducts.results.filter((row) => !backupProductIds.has(String(row.id)) && row.deleted_at === null) : [];
  const deactivateAssets = mode === "overwrite" ? currentAssets.results.filter((row) => !backupAssetIds.has(String(row.id)) && row.is_active === 1) : [];
  const deactivateTemplates = mode === "overwrite" ? currentTemplates.results.filter((row) => !backupTemplateIds.has(String(row.id)) && row.deleted_at === null) : [];
  if (!env.bypassPaid && !await paidAccess(env.DB)) {
    const restricted = mode !== "update" || changedFieldTranslations.length || changedLocalizations.length || changedDrafts.length || newReviews.length
      || changedCategorySigns.length || changedAssets.length || changedTemplates.length || changedPrintSets.length || newPrintJobs.length
      || changedProducts.some(row => row.deleted_at !== (productsById.get(row.id)?.deleted_at ?? null));
    if (restricted) throw new Error("paid_required");
    const newProducts = changedProducts.filter(row => !productsById.has(row.id)).length;
    if (newProducts && currentProducts.results.length + newProducts > 3) throw new Error("free_product_limit");
  }
  return {
    mode, backup, conflicts, newFavorites, removedFavorites, changedCategories, changedProducts, changedLocalizations, changedDrafts, newReviews, changedFieldTranslations, removedFieldTranslations,
    changedCatalogLinks,changedCatalogSources,
    changedCategorySigns, changedAssets, newAssetUploads, changedTemplates, changedPrintSets, newPrintJobs,
    deactivateCategories, deactivateCategorySigns, deactivateProducts, deactivateAssets, deactivateTemplates,
    summary: {
      create: creates, update: updates,
       unchanged: backup.data.field_translations.length - changedFieldTranslations.length + backup.data.categories.length + backup.data.category_signs.length + backup.data.products.length + backup.data.product_localizations.length
        + backup.data.translation_drafts.length + backup.data.translation_reviews.length
        + backup.data.assets.length + backup.data.templates.length + backup.data.print_sets.length + backup.data.print_jobs.length + backup.data.product_catalog_links.length + backup.data.product_catalog_translation_sources.length
         - changedCategories.length - changedCategorySigns.length - changedProducts.length - changedLocalizations.length - changedDrafts.length - newReviews.length
        - changedAssets.length - changedTemplates.length - changedPrintSets.length - newPrintJobs.length - changedCatalogLinks.length - changedCatalogSources.length + incomingFavorites.length - newFavorites.length,
       deactivate: removedFavorites.length + removedFieldTranslations.length + deactivateCategories.length + deactivateCategorySigns.length + deactivateProducts.length + deactivateAssets.length + deactivateTemplates.length, mapped,
    },
  };
}

export async function previewRestore(env: BackupEnv, raw: unknown) {
  const plan = await restorePlan(env, raw);
  return {
    mode: plan.mode, canApply: plan.conflicts.length === 0, blockingConflicts: plan.conflicts.length,
    conflicts: plan.conflicts, summary: plan.summary,
  };
}

type ResetPlan = {
  counts: Record<string, number>;
  retainedCounts: Record<string, number>;
  resetCounts: Record<string, number>;
  assets: Record<string, unknown>[];
  assetsToDelete: Record<string, unknown>[];
  preservedAssetIds: Set<string>;
};

const collectExactStringReferences = (value: unknown, candidates: Set<string>, found: Set<string>) => {
  if (typeof value === "string") {
    if (candidates.has(value)) found.add(value);
    return;
  }
  if (Array.isArray(value)) {
    for (const item of value) collectExactStringReferences(item, candidates, found);
    return;
  }
  if (value && typeof value === "object") {
    for (const item of Object.values(value)) collectExactStringReferences(item, candidates, found);
  }
};

async function loadResetPlan(env: BackupEnv): Promise<ResetPlan> {
  const loaded = await Promise.all(tables.map(async (table) => [table, (await backupRows(env.DB, table)).results] as const));
  const rows = Object.fromEntries(loaded) as Record<(typeof tables)[number], Record<string, unknown>[]>;
  const assets = rows.assets;
  if (assets.length && !env.MEDIA) throw new Error("asset_storage_unavailable");
  const counts = Object.fromEntries(tables.map((table) => [table, rows[table].length]));
  const retainedTemplates = rows.templates.filter((row) => String(row.status) !== "draft");
  const preservedAssetIds = new Set<string>();
  const assetIds = new Set(assets.map((row) => String(row.id)));
  let parseSafe = true;
  const scanJson = (raw: unknown) => {
    try { collectExactStringReferences(JSON.parse(String(raw)), assetIds, preservedAssetIds); }
    catch { parseSafe = false; }
  };
  for (const job of rows.print_jobs) scanJson(job.snapshot_json);
  for (const template of retainedTemplates) scanJson(template.config_json);
  if (!parseSafe) for (const id of assetIds) preservedAssetIds.add(id);
  const assetsToDelete = assets.filter((row) => !preservedAssetIds.has(String(row.id)));
  const retainedCounts = {
    categories: rows.categories.length,
    category_signs: rows.category_signs.length,
    products: rows.products.length,
    product_localizations: rows.product_localizations.length,
    templates: retainedTemplates.length,
    assets: assets.length - assetsToDelete.length,
    print_jobs: rows.print_jobs.length,
    design_favorites: rows.design_favorites.length,
  };
  const resetCounts = {
    field_translations: rows.field_translations.length,
    categories: rows.categories.length,
    category_signs: rows.category_signs.length,
    products: rows.products.length,
    product_offers: rows.product_offers.length,
    translation_drafts: rows.translation_drafts.length,
    translation_reviews: rows.translation_reviews.length,
    templates: rows.templates.length - retainedTemplates.length,
    assets: assetsToDelete.length,
    print_sets: rows.print_sets.length,
    print_jobs: 0,
  };
  return { counts, retainedCounts, resetCounts, assets, assetsToDelete, preservedAssetIds };
}

export async function previewReset(env: BackupEnv) {
  const plan = await loadResetPlan(env);
  return {
    counts: plan.counts,
    retainedCounts: plan.retainedCounts,
    resetCounts: plan.resetCounts,
    mediaCleanupRequired: plan.assetsToDelete.length,
  };
}

const withCleanupKeys = (resultJson: string, keys: string[]) => {
  if (!keys.length) return resultJson;
  try {
    const parsed = JSON.parse(resultJson);
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return JSON.stringify({ ...(parsed as Record<string, unknown>), mediaCleanupPendingKeys: keys });
    }
  } catch { /* Preserve the internal result as a string if it is not JSON. */ }
  return JSON.stringify({ resultJson, mediaCleanupPendingKeys: keys });
};
export async function resetContent(env: BackupEnv, expectedRevision?: number, completion?: { operationId: string; resultJson: string }) {
  const plan = await loadResetPlan(env);
  const nowIso = new Date().toISOString();
  const nowMs = Date.now();
  const statements: D1PreparedStatement[] = [];
  if (expectedRevision !== undefined) {
    statements.push(env.DB.prepare("INSERT INTO account_content_revisions (account_id, revision, updated_at) SELECT account_id, NULL, ? FROM account_content_revisions WHERE account_id = ? AND revision != ?").bind(nowMs, env.DB.accountId, expectedRevision));
    statements.push(env.DB.prepare("UPDATE account_content_revisions SET revision = revision + 1, updated_at = ? WHERE account_id = ? AND revision = ?").bind(nowMs, env.DB.accountId, expectedRevision));
  }
  statements.push(
    env.DB.prepare(`DELETE FROM translation_drafts WHERE product_id IN (SELECT id FROM products WHERE ${owner(env.DB)})`),
    env.DB.prepare(`DELETE FROM field_translations WHERE ${owner(env.DB)}`),
    env.DB.prepare(`DELETE FROM translation_reviews WHERE product_id IN (SELECT id FROM products WHERE ${owner(env.DB)})`),
    env.DB.prepare(`DELETE FROM product_offers WHERE product_id IN (SELECT id FROM products WHERE ${owner(env.DB)})`),
    env.DB.prepare(`DELETE FROM print_sets WHERE ${owner(env.DB)}`),
    env.DB.prepare(`DELETE FROM templates WHERE ${owner(env.DB)} AND status = 'draft'`),
    env.DB.prepare(`UPDATE templates SET is_active = 0, deleted_at = COALESCE(deleted_at, ?), updated_at = ? WHERE ${owner(env.DB)} AND status <> 'draft'`).bind(nowIso, nowIso),
    env.DB.prepare(`UPDATE products SET is_active = 0, deleted_at = COALESCE(deleted_at, ?), version = version + 1, updated_at = ? WHERE ${owner(env.DB)}`).bind(nowIso, nowIso),
    env.DB.prepare(`UPDATE categories SET is_active = 0, updated_at = ? WHERE ${owner(env.DB)}`).bind(nowIso),
    env.DB.prepare(`UPDATE category_signs SET is_active = 0, updated_at = ? WHERE ${owner(env.DB)}`).bind(nowIso),
    env.DB.prepare(`UPDATE assets SET is_active = 0, deactivated_at = COALESCE(deactivated_at, ?) WHERE ${owner(env.DB)}`).bind(nowIso),
    env.DB.prepare(`DELETE FROM assets WHERE ${owner(env.DB)} AND id NOT IN (SELECT value FROM json_each(?))`).bind(JSON.stringify([...plan.preservedAssetIds])),
  );
  if (completion) {
    statements.push(env.DB.prepare("UPDATE operator_content_operations SET status = ?, result_json = ?, lease_until = NULL, applied_at = ? WHERE id = ? AND status = ? AND lease_until >= CAST(strftime('%s', 'now') AS INTEGER) * 1000")
      .bind("completed", withCleanupKeys(completion.resultJson, plan.assetsToDelete.map((asset) => String(asset.r2_key))), nowMs, completion.operationId, "applying"));
    statements.push(env.DB.prepare("INSERT INTO account_content_revisions (account_id, revision, updated_at) SELECT account_id, NULL, ? FROM operator_content_operations WHERE id = ? AND status != ?")
      .bind(nowMs, completion.operationId, "completed"));
  }
  await env.DB.batch(statements);
  const cleanup = await cleanupRestoreUploads(env, plan.assetsToDelete.map((asset) => String(asset.r2_key)));
  return {
    counts: plan.counts,
    retainedCounts: plan.retainedCounts,
    resetCounts: plan.resetCounts,
    mediaCleanupPendingKeys: cleanup.remainingKeys,
    mediaCleanupFailed: cleanup.remainingKeys.length,
    mediaCleanupRemainingKeys: cleanup.remainingKeys,
  };
}

export class RestoreMediaCleanupError extends Error {
  constructor(public readonly remainingKeys: string[], public readonly cause?: unknown) {
    super("restore_media_cleanup_required");
    this.name = "RestoreMediaCleanupError";
  }
}

export async function cleanupRestoreUploads(env: BackupEnv, keys: readonly string[]) {
  const prefix = "accounts/" + env.DB.accountId + "/assets/";
  const uniqueKeys = [...new Set(keys)];
  const unsafeKeys = uniqueKeys.filter((key) => !key.startsWith(prefix));
  if (!env.MEDIA) return { remainingKeys: uniqueKeys };
  const candidateKeys = uniqueKeys.filter((key) => key.startsWith(prefix));
  if (!candidateKeys.length) return { remainingKeys: unsafeKeys };
  let referencedKeys: Set<string>;
  try {
    const rows = await env.DB.prepare(
      "SELECT r2_key FROM assets WHERE " + owner(env.DB) + " AND r2_key IN (SELECT value FROM json_each(?))",
    ).bind(JSON.stringify(candidateKeys)).all<{ r2_key: string }>();
    referencedKeys = new Set(rows.results.map((row) => String(row.r2_key)));
  } catch {
    return { remainingKeys: uniqueKeys };
  }
  const protectedKeys = candidateKeys.filter((key) => referencedKeys.has(key));
  const safeKeys = candidateKeys.filter((key) => !referencedKeys.has(key));
  const results = await mapAssetBatches(safeKeys, async (key) => {
    try { await env.MEDIA!.delete(key); return null; }
    catch { return key; }
  });
  return { remainingKeys: [...new Set([...unsafeKeys, ...protectedKeys, ...results.filter((key): key is string => Boolean(key))])] };
}
export type RestoreApplyOptions = { expectedRevision?: number; operationId?: string; completionJson?: string };

export async function applyRestore(env: BackupEnv, raw: unknown, actor: string, trusted: RestoreApplyOptions = {}) {
  await assertScopedAccountActive(env.DB);
  const input = restoreApplyInputSchema.parse(raw);
  if (input.mode === "overwrite" && !trusted.operationId) {
    const safetyAt = Date.parse(input.safetyBackupExportedAt ?? "");
    if (input.confirmation !== "덮어쓰기" || !Number.isFinite(safetyAt) || safetyAt < Date.now() - 10 * 60_000 || safetyAt > Date.now() + 60_000) {
      throw new Error("backup_confirmation_required");
    }
  }
  const plan = await restorePlan(env, { mode: input.mode, copyForeign: input.copyForeign, backup: input.backup });
  if (plan.conflicts.length) throw new Error("backup_conflict");
  const statements: D1PreparedStatement[] = [];
  if (plan.changedCategories.length) statements.push(env.DB.prepare(`INSERT INTO categories
    (owner_id, id, parent_id, name_ko, name_en, name_zh_cn, name_ja, default_template_key, icon_key, sort_order, is_active, created_at, updated_at)
    SELECT ${ownerValue(env.DB)}, json_extract(value, '$.id'), json_extract(value, '$.parent_id'), json_extract(value, '$.name_ko'), json_extract(value, '$.name_en'),
      json_extract(value, '$.name_zh_cn'), json_extract(value, '$.name_ja'), json_extract(value, '$.default_template_key'), json_extract(value, '$.icon_key'),
      json_extract(value, '$.sort_order'), json_extract(value, '$.is_active'), json_extract(value, '$.created_at'), ?
    FROM json_each(?) WHERE 1
    ON CONFLICT(id) DO UPDATE SET parent_id=excluded.parent_id, name_ko=excluded.name_ko, name_en=excluded.name_en, name_zh_cn=excluded.name_zh_cn,
      name_ja=excluded.name_ja, default_template_key=excluded.default_template_key, icon_key=excluded.icon_key, sort_order=excluded.sort_order,
      is_active=excluded.is_active, updated_at=excluded.updated_at`)
    .bind(new Date().toISOString(), JSON.stringify(plan.changedCategories)));
  if (plan.changedCategorySigns.length) statements.push(env.DB.prepare(`INSERT INTO category_signs
    (owner_id, id, name, normalized_name, sort_order, version, is_active, created_at, updated_at, title_ko, body_ko, asset_id, category_id, deleted_at)
    SELECT ${ownerValue(env.DB)}, json_extract(value, '$.id'), json_extract(value, '$.name'), json_extract(value, '$.normalized_name'),
      json_extract(value, '$.sort_order'), json_extract(value, '$.version'), json_extract(value, '$.is_active'),
      json_extract(value, '$.created_at'), json_extract(value, '$.updated_at'), json_extract(value, '$.title_ko'),
      COALESCE(json_extract(value, '$.body_ko'), ''), json_extract(value, '$.asset_id'), json_extract(value, '$.category_id'), json_extract(value, '$.deleted_at') FROM json_each(?) WHERE 1
    ON CONFLICT(id) DO UPDATE SET name=excluded.name, normalized_name=excluded.normalized_name, sort_order=excluded.sort_order,
      version=excluded.version, is_active=excluded.is_active, updated_at=excluded.updated_at,
      title_ko=excluded.title_ko, body_ko=excluded.body_ko, asset_id=excluded.asset_id, category_id=excluded.category_id, deleted_at=excluded.deleted_at`)
    .bind(JSON.stringify(plan.changedCategorySigns)));
  if (plan.changedProducts.length) {
    const now = new Date().toISOString();
    statements.push(env.DB.prepare(`INSERT INTO products
      (owner_id, id, category_id, name_ko, name_ko_normalized, description_ko, translation_source_hash, template_key_override,
       version, is_active, deleted_at, created_by, created_at, updated_by, updated_at, currency_code)
      SELECT ${ownerValue(env.DB)}, json_extract(value, '$.id'), json_extract(value, '$.category_id'), json_extract(value, '$.name_ko'),
        json_extract(value, '$.name_ko_normalized'), json_extract(value, '$.description_ko'), json_extract(value, '$.translation_source_hash'),
        json_extract(value, '$.template_key_override'), json_extract(value, '$.version'), json_extract(value, '$.is_active'),
        json_extract(value, '$.deleted_at'), json_extract(value, '$.created_by'), json_extract(value, '$.created_at'), ?, ?, COALESCE(json_extract(value, '$.currency_code'), 'KRW')
      FROM json_each(?) WHERE 1
      ON CONFLICT(id) DO UPDATE SET category_id=excluded.category_id, name_ko=excluded.name_ko,
        name_ko_normalized=excluded.name_ko_normalized, description_ko=excluded.description_ko,
        translation_source_hash=excluded.translation_source_hash, template_key_override=excluded.template_key_override,
        version=excluded.version, is_active=excluded.is_active, deleted_at=excluded.deleted_at, currency_code=excluded.currency_code,
        updated_by=excluded.updated_by, updated_at=excluded.updated_at`)
      .bind(actor, now, JSON.stringify(plan.changedProducts)));
    const productIds = plan.changedProducts.map((row) => row.id);
    const productIdSet = new Set(productIds);
    const offers = plan.backup.data.product_offers.filter((row) => productIdSet.has(row.product_id));
    statements.push(env.DB.prepare(`DELETE FROM product_offers WHERE product_id IN (SELECT value FROM json_each(?))`).bind(JSON.stringify(productIds)));
    if (offers.length) statements.push(env.DB.prepare(`INSERT INTO product_offers
      (id, product_id, sort_order, quantity, unit_code, unit_custom_ko, price_krw, created_at, updated_at, price_minor)
      SELECT json_extract(value, '$.id'), json_extract(value, '$.product_id'), json_extract(value, '$.sort_order'),
        json_extract(value, '$.quantity'), json_extract(value, '$.unit_code'), json_extract(value, '$.unit_custom_ko'),
        json_extract(value, '$.price_krw'), json_extract(value, '$.created_at'), json_extract(value, '$.updated_at'), COALESCE(json_extract(value, '$.price_minor'), ROUND(json_extract(value, '$.price_krw') * 100))
      FROM json_each(?)`).bind(JSON.stringify(offers)));
  }
  if(plan.changedCatalogLinks.length) statements.push(env.DB.prepare(`INSERT INTO product_catalog_links
    (id,account_id,product_id,catalog_product_id,description_id,description_version,package_id,package_version,package_snapshot_json,override_json,request_id,created_at,updated_at)
    SELECT json_extract(value,'$.id'),?,json_extract(value,'$.product_id'),json_extract(value,'$.catalog_product_id'),json_extract(value,'$.description_id'),json_extract(value,'$.description_version'),
      json_extract(value,'$.package_id'),json_extract(value,'$.package_version'),json_extract(value,'$.package_snapshot_json'),json_extract(value,'$.override_json'),json_extract(value,'$.request_id'),json_extract(value,'$.created_at'),json_extract(value,'$.updated_at')
    FROM json_each(?) WHERE 1 ON CONFLICT(id) DO UPDATE SET description_id=excluded.description_id,description_version=excluded.description_version,package_id=excluded.package_id,
      package_version=excluded.package_version,package_snapshot_json=excluded.package_snapshot_json,override_json=excluded.override_json,updated_at=excluded.updated_at`)
    .bind(env.DB.accountId,JSON.stringify(plan.changedCatalogLinks)));
  if(plan.changedCatalogSources.length) statements.push(env.DB.prepare(`INSERT INTO product_catalog_translation_sources
    (product_id,locale,source_hash,translation_hash,catalog_translation_id,provenance_json,reused_at)
    SELECT json_extract(value,'$.product_id'),json_extract(value,'$.locale'),json_extract(value,'$.source_hash'),json_extract(value,'$.translation_hash'),json_extract(value,'$.catalog_translation_id'),json_extract(value,'$.provenance_json'),json_extract(value,'$.reused_at')
    FROM json_each(?) WHERE 1 ON CONFLICT(product_id,locale) DO UPDATE SET source_hash=excluded.source_hash,translation_hash=excluded.translation_hash,catalog_translation_id=excluded.catalog_translation_id,provenance_json=excluded.provenance_json,reused_at=excluded.reused_at`)
    .bind(JSON.stringify(plan.changedCatalogSources)));
  if (plan.changedLocalizations.length) statements.push(env.DB.prepare(`INSERT INTO product_localizations
    (product_id, locale, name, description, source_hash, translation_hash, origin, provider, model, approved_by, approved_at, updated_at)
    SELECT json_extract(value, '$.product_id'), json_extract(value, '$.locale'), json_extract(value, '$.name'),
      json_extract(value, '$.description'), json_extract(value, '$.source_hash'), json_extract(value, '$.translation_hash'),
      json_extract(value, '$.origin'), json_extract(value, '$.provider'), json_extract(value, '$.model'),
      json_extract(value, '$.approved_by'), json_extract(value, '$.approved_at'), json_extract(value, '$.updated_at')
    FROM json_each(?) WHERE 1
    ON CONFLICT(product_id, locale) DO UPDATE SET name=excluded.name, description=excluded.description,
      source_hash=excluded.source_hash, translation_hash=excluded.translation_hash, origin=excluded.origin,
      provider=excluded.provider, model=excluded.model, approved_by=excluded.approved_by,
      approved_at=excluded.approved_at, updated_at=excluded.updated_at`).bind(JSON.stringify(plan.changedLocalizations)));
  if (plan.changedFieldTranslations.length) statements.push(env.DB.prepare(`INSERT INTO field_translations
    (id,owner_id,target_kind,target_id,field,locale,text,back_text,source_text,source_hash,origin,revision,updated_at,metadata_json)
    SELECT json_extract(value,'$.id'),${ownerValue(env.DB)},json_extract(value,'$.target_kind'),json_extract(value,'$.target_id'),
      json_extract(value,'$.field'),json_extract(value,'$.locale'),json_extract(value,'$.text'),json_extract(value,'$.back_text'),
      json_extract(value,'$.source_text'),json_extract(value,'$.source_hash'),json_extract(value,'$.origin'),json_extract(value,'$.revision'),json_extract(value,'$.updated_at'),json_extract(value,'$.metadata_json')
    FROM json_each(?) WHERE 1 ON CONFLICT(id) DO UPDATE SET text=excluded.text,back_text=excluded.back_text,source_text=excluded.source_text,
      source_hash=excluded.source_hash,origin=excluded.origin,revision=excluded.revision,updated_at=excluded.updated_at,metadata_json=excluded.metadata_json`).bind(JSON.stringify(plan.changedFieldTranslations)));
  if (plan.removedFieldTranslations.length) statements.push(env.DB.prepare(`DELETE FROM field_translations WHERE ${owner(env.DB)} AND id IN (SELECT value FROM json_each(?))`).bind(JSON.stringify(plan.removedFieldTranslations.map(row=>row.id))));
  if (plan.changedDrafts.length) statements.push(env.DB.prepare(`INSERT INTO translation_drafts
    (product_id, locale, name, description, source_hash, translation_hash, origin, provider, model,
     generation_warnings_json, updated_by, updated_at, back_name_ko, back_description_ko)
    SELECT json_extract(value, '$.product_id'), json_extract(value, '$.locale'), json_extract(value, '$.name'),
      json_extract(value, '$.description'), json_extract(value, '$.source_hash'), json_extract(value, '$.translation_hash'),
      json_extract(value, '$.origin'), json_extract(value, '$.provider'), json_extract(value, '$.model'),
      json_extract(value, '$.generation_warnings_json'), json_extract(value, '$.updated_by'), json_extract(value, '$.updated_at'),
      json_extract(value, '$.back_name_ko'), json_extract(value, '$.back_description_ko')
    FROM json_each(?) WHERE 1
    ON CONFLICT(product_id, locale) DO UPDATE SET name=excluded.name, description=excluded.description,
      source_hash=excluded.source_hash, translation_hash=excluded.translation_hash, origin=excluded.origin,
      provider=excluded.provider, model=excluded.model, generation_warnings_json=excluded.generation_warnings_json,
      updated_by=excluded.updated_by, updated_at=excluded.updated_at, back_name_ko=excluded.back_name_ko,
      back_description_ko=excluded.back_description_ko`).bind(JSON.stringify(plan.changedDrafts)));
  if (plan.newReviews.length) statements.push(env.DB.prepare(`INSERT INTO translation_reviews
    (product_id, locale, translation_hash, source_hash, back_name_ko, back_description_ko, naturalness,
     meaning_preservation, numbers_and_units, added_claims, overflow_risk, requires_confirmation, warnings_json,
     provider, model, review_notes, confirmed_by_reviewer, reviewed_by, reviewed_at)
    SELECT json_extract(value, '$.product_id'), json_extract(value, '$.locale'), json_extract(value, '$.translation_hash'),
      json_extract(value, '$.source_hash'), json_extract(value, '$.back_name_ko'), json_extract(value, '$.back_description_ko'),
      json_extract(value, '$.naturalness'), json_extract(value, '$.meaning_preservation'), json_extract(value, '$.numbers_and_units'),
      json_extract(value, '$.added_claims'), json_extract(value, '$.overflow_risk'), json_extract(value, '$.requires_confirmation'),
      json_extract(value, '$.warnings_json'), json_extract(value, '$.provider'), json_extract(value, '$.model'),
      json_extract(value, '$.review_notes'), json_extract(value, '$.confirmed_by_reviewer'), json_extract(value, '$.reviewed_by'),
      json_extract(value, '$.reviewed_at') FROM json_each(?)`).bind(JSON.stringify(plan.newReviews)));
  if (plan.changedAssets.length) statements.push(env.DB.prepare(`INSERT INTO assets
    (owner_id, id, display_name, asset_type, provenance, r2_key, original_filename, mime_type, byte_size, width_px, height_px,
     is_active, deactivated_at, created_by, created_at, crop_json)
    SELECT ${ownerValue(env.DB)}, json_extract(value, '$.id'), json_extract(value, '$.display_name'), json_extract(value, '$.asset_type'),
      json_extract(value, '$.provenance'), json_extract(value, '$.r2_key'), json_extract(value, '$.original_filename'),
      json_extract(value, '$.mime_type'), json_extract(value, '$.byte_size'), json_extract(value, '$.width_px'),
      json_extract(value, '$.height_px'), json_extract(value, '$.is_active'), json_extract(value, '$.deactivated_at'),
      json_extract(value, '$.created_by'), json_extract(value, '$.created_at'), json_extract(value, '$.crop_json') FROM json_each(?) WHERE 1
    ON CONFLICT(id) DO UPDATE SET display_name=excluded.display_name, asset_type=excluded.asset_type,
      provenance=excluded.provenance, original_filename=excluded.original_filename, is_active=excluded.is_active,
      deactivated_at=excluded.deactivated_at, crop_json=excluded.crop_json`).bind(JSON.stringify(plan.changedAssets)));
  for (const designType of ["label", "category"] as const) {
    const keys = plan.changedTemplates.filter((row) => row.is_active && row.design_type === designType).map((row) => row.template_key);
    if (keys.length) statements.push(env.DB.prepare(`UPDATE templates SET is_active = 0 WHERE ${owner(env.DB)} AND design_type = ? AND template_key IN (SELECT value FROM json_each(?))`).bind(designType, JSON.stringify(keys)));
  }
  if (plan.changedTemplates.length) statements.push(env.DB.prepare(`INSERT INTO templates
    (owner_id, id, template_key, design_type, version, name, width_mm, height_mm, config_json, status, is_active, created_by, created_at, updated_at, published_at, deleted_at, deleted_by)
    SELECT ${ownerValue(env.DB)}, json_extract(value, '$.id'), json_extract(value, '$.template_key'), COALESCE(json_extract(value, '$.design_type'), 'label'), json_extract(value, '$.version'),
      json_extract(value, '$.name'), json_extract(value, '$.width_mm'), json_extract(value, '$.height_mm'),
      json_extract(value, '$.config_json'), json_extract(value, '$.status'), json_extract(value, '$.is_active'),
      json_extract(value, '$.created_by'), json_extract(value, '$.created_at'), json_extract(value, '$.updated_at'),
      json_extract(value, '$.published_at'), json_extract(value, '$.deleted_at'), json_extract(value, '$.deleted_by') FROM json_each(?) WHERE 1
    ON CONFLICT(id) DO UPDATE SET design_type=excluded.design_type, name=excluded.name, width_mm=excluded.width_mm, height_mm=excluded.height_mm,
      config_json=excluded.config_json, is_active=excluded.is_active, updated_at=excluded.updated_at,
      deleted_at=excluded.deleted_at, deleted_by=excluded.deleted_by`).bind(JSON.stringify(plan.changedTemplates)));
  if (plan.changedPrintSets.length) statements.push(env.DB.prepare(`INSERT INTO print_sets
    (owner_id, id, design_type, name, items_json, created_by, created_at, updated_by, updated_at, print_schema_version)
    SELECT ${ownerValue(env.DB)}, json_extract(value, '$.id'), COALESCE(json_extract(value, '$.design_type'), 'label'), json_extract(value, '$.name'), json_extract(value, '$.items_json'),
      json_extract(value, '$.created_by'), json_extract(value, '$.created_at'), json_extract(value, '$.updated_by'),
      json_extract(value, '$.updated_at'), COALESCE(json_extract(value, '$.print_schema_version'),1) FROM json_each(?) WHERE 1
    ON CONFLICT(id) DO UPDATE SET design_type=excluded.design_type, name=excluded.name, items_json=excluded.items_json, print_schema_version=excluded.print_schema_version,
      updated_by=excluded.updated_by, updated_at=excluded.updated_at`).bind(JSON.stringify(plan.changedPrintSets)));
  if (plan.newPrintJobs.length) statements.push(env.DB.prepare(`INSERT INTO print_jobs
    (owner_id, id, design_type, item_count, page_count, snapshot_json, created_by, created_at, print_dialog_opened_at, print_schema_version)
    SELECT ${ownerValue(env.DB)}, json_extract(value, '$.id'), COALESCE(json_extract(value, '$.design_type'), 'label'), json_extract(value, '$.item_count'), json_extract(value, '$.page_count'),
      json_extract(value, '$.snapshot_json'), json_extract(value, '$.created_by'), json_extract(value, '$.created_at'),
      json_extract(value, '$.print_dialog_opened_at'), COALESCE(json_extract(value, '$.print_schema_version'),1) FROM json_each(?)`).bind(JSON.stringify(plan.newPrintJobs)));
  if (plan.newFavorites.length) statements.push(env.DB.prepare(`INSERT OR IGNORE INTO design_favorites(owner_id,source,family)
    SELECT ${ownerValue(env.DB)},json_extract(value,'$.source'),json_extract(value,'$.family') FROM json_each(?)`).bind(JSON.stringify(plan.newFavorites)));
  if (plan.removedFavorites.length) statements.push(env.DB.prepare(`DELETE FROM design_favorites WHERE ${owner(env.DB)}
    AND EXISTS (SELECT 1 FROM json_each(?) item WHERE json_extract(item.value,'$.source')=design_favorites.source
      AND json_extract(item.value,'$.family')=design_favorites.family)`).bind(JSON.stringify(plan.removedFavorites)));
  if (plan.mode === "overwrite") {
    const now = new Date().toISOString();
    if (plan.deactivateProducts.length) statements.push(env.DB.prepare(`UPDATE products SET deleted_at = ?, is_active = 0,
      version = version + 1, updated_by = ?, updated_at = ? WHERE ${owner(env.DB)} AND id IN (SELECT value FROM json_each(?)) AND deleted_at IS NULL`)
      .bind(now, actor, now, JSON.stringify(plan.deactivateProducts.map((row) => row.id))));
    if (plan.deactivateCategories.length) statements.push(env.DB.prepare(`UPDATE categories SET is_active = 0, updated_at = ? WHERE ${owner(env.DB)} AND id IN (SELECT value FROM json_each(?))`)
      .bind(now, JSON.stringify(plan.deactivateCategories.map((row) => row.id))));
    if (plan.deactivateCategorySigns.length) statements.push(env.DB.prepare(`UPDATE category_signs SET is_active = 0, updated_at = ? WHERE ${owner(env.DB)} AND id IN (SELECT value FROM json_each(?))`)
      .bind(now, JSON.stringify(plan.deactivateCategorySigns.map((row) => row.id))));
    if (plan.deactivateAssets.length) statements.push(env.DB.prepare(`UPDATE assets SET is_active = 0, deactivated_at = ? WHERE ${owner(env.DB)} AND id IN (SELECT value FROM json_each(?))`)
      .bind(now, JSON.stringify(plan.deactivateAssets.map((row) => row.id))));
    if (plan.deactivateTemplates.length) statements.push(env.DB.prepare(`UPDATE templates SET is_active = 0, deleted_at = ?, deleted_by = ?, updated_at = ? WHERE ${owner(env.DB)} AND id IN (SELECT value FROM json_each(?)) AND deleted_at IS NULL`)
      .bind(now, actor, now, JSON.stringify(plan.deactivateTemplates.map((row) => row.id))));
    const productIds = plan.backup.data.products.map((row) => row.id);
    statements.push(env.DB.prepare(`DELETE FROM translation_drafts WHERE product_id IN (SELECT value FROM json_each(?))
      AND NOT EXISTS (SELECT 1 FROM json_each(?) incoming WHERE json_extract(incoming.value, '$.product_id') = translation_drafts.product_id
        AND json_extract(incoming.value, '$.locale') = translation_drafts.locale)`)
      .bind(JSON.stringify(productIds), JSON.stringify(plan.backup.data.translation_drafts)));
  }
  if (trusted.expectedRevision !== undefined) {
    statements.unshift(env.DB.prepare("UPDATE account_content_revisions SET revision = revision + 1, updated_at = ? WHERE account_id = ? AND revision = ?").bind(Date.now(), env.DB.accountId, trusted.expectedRevision));
    statements.unshift(env.DB.prepare("INSERT INTO account_content_revisions (account_id, revision, updated_at) SELECT account_id, NULL, ? FROM account_content_revisions WHERE account_id = ? AND revision != ?").bind(Date.now(), env.DB.accountId, trusted.expectedRevision));
  }
  if (trusted.operationId && trusted.completionJson) {
    const completionNow = Date.now();
    statements.push(env.DB.prepare("UPDATE operator_content_operations SET status = ?, result_json = ?, lease_until = NULL, applied_at = ? WHERE id = ? AND status = ? AND lease_until >= CAST(strftime('%s', 'now') AS INTEGER) * 1000").bind("completed", trusted.completionJson, completionNow, trusted.operationId, "applying"));
    statements.push(env.DB.prepare("INSERT INTO account_content_revisions (account_id, revision, updated_at) SELECT account_id, NULL, ? FROM operator_content_operations WHERE id = ? AND status != ?").bind(completionNow, trusted.operationId, "completed"));
  }
  if (plan.newAssetUploads.length && !env.MEDIA) throw new Error("asset_storage_unavailable");
  const pendingUploadKeys = plan.newAssetUploads.map((asset) => asset.key);
  if (trusted.operationId && pendingUploadKeys.length) {
    const journal = await env.DB.prepare("UPDATE operator_content_operations SET result_json = ? WHERE id = ? AND status = ? AND lease_until >= CAST(strftime('%s', 'now') AS INTEGER) * 1000")
      .bind(withCleanupKeys(trusted.completionJson ?? "{}", pendingUploadKeys), trusted.operationId, "applying").run();
    if (journal.meta.changes !== 1) throw new Error("operator_operation_uncertain");
  }
  const attemptedUploadKeys: string[] = [];
  try {
    for (const asset of plan.newAssetUploads) {
      attemptedUploadKeys.push(asset.key);
      await env.MEDIA!.put(asset.key, asset.bytes);
    }
    if (statements.length) await env.DB.batch(statements);
  } catch (cause) {
    const cleanup = await cleanupRestoreUploads(env, attemptedUploadKeys);
    if (cleanup.remainingKeys.length) throw new RestoreMediaCleanupError(cleanup.remainingKeys, cause);
    throw cause;
  }  return { mode: plan.mode, summary: plan.summary };
}
