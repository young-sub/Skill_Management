import { env } from "cloudflare:workers";
import { expect, it } from "vitest";
import { accountDatabase } from "../src/worker/accountData";
import { addProductCatalog, applyProductCatalogImport } from "../src/worker/productCatalog";
import { fixtureDatabase, fixtureFetch } from "./accountFixture";

const request = (path: string, init?: RequestInit) => fixtureFetch(`http://localhost${path}`, {
  ...init,
  headers: init?.body ? { "content-type": "application/json", origin: "http://localhost", ...init.headers } : init?.headers,
});
const post = (path: string, body: unknown) => request(path, { method: "POST", body: JSON.stringify(body) });
const description = (length: number) => "x".repeat(length);
const input = (nameKo: string, descriptionKo: string) => ({
  categoryId: "category-supplements", nameKo, descriptionKo,
  offers: [{ quantity: 1, unitCode: "ea", priceKrw: 1000 }],
});

it("rejects product descriptions over 300 characters on create and update", async () => {
  const long = description(301);
  const createRejected = await post("/api/products", input(`eval-create-${crypto.randomUUID()}`, long));
  expect(createRejected.status).toBe(400);

  const sourceResponse = await post("/api/products", input(`eval-copy-${crypto.randomUUID()}`, description(300)));
  expect(sourceResponse.status).toBe(201);
  const source = (await sourceResponse.json() as any).data;
  const updated = await request(`/api/products/${source.id}`, {
    method: "PATCH", body: JSON.stringify({ expectedVersion: source.version, descriptionKo: long }),
  });
  expect(updated.status).toBe(400);
  expect(((await (await request(`/api/products/${source.id}`)).json() as any).data.descriptionKo).length).toBe(300);
});

it("does not copy a legacy product whose description is over the current limit", async () => {
  const long = description(301);
  const sourceResponse = await post("/api/products", input(`eval-copy-${crypto.randomUUID()}`, "short"));
  expect(sourceResponse.status).toBe(201);
  const source = (await sourceResponse.json() as any).data;
  await (env as Env).DB.prepare("UPDATE products SET description_ko = ? WHERE id = ?").bind(long, source.id).run();
  const copied = await post(`/api/products/${source.id}/duplicate`, {});
  expect(copied.status).toBe(400);
  expect(await (env as Env).DB.prepare("SELECT COUNT(*) AS count FROM products WHERE name_ko LIKE ?")
    .bind(`${source.nameKo}%`).first<number>("count")).toBe(1);
});

it("rejects overlong descriptions in the bulk product import", async () => {
  const long = description(301);
  const category = ((await (await request("/api/categories")).json() as any).data)
    .find((item: any) => item.id === "category-supplements");
  const importRow = {
    rowNumber: 2, categoryPathKo: category.pathKo, nameKo: `eval-import-${crypto.randomUUID()}`,
    descriptionKo: long, priceKrw: 1000, unitLabel: "\uac1c",
  };
  const preview = ((await (await post("/api/product-import/preview", { rows: [importRow] })).json() as any).data);
  expect(preview.rows[0].status).toBe("invalid");
  const applied = ((await (await post("/api/product-import/apply", { rows: [importRow] })).json() as any).data);
  expect(applied).toMatchObject({ createdRows: 0, invalidRows: 1 });
});

it("does not update an existing product from a bulk row with an overlong description", async () => {
  const category = ((await (await request("/api/categories")).json() as any).data)
    .find((item: any) => item.id === "category-supplements");
  const created = await post("/api/products", input(`eval-import-update-${crypto.randomUUID()}`, "short"));
  expect(created.status).toBe(201);
  const product = (await created.json() as any).data;
  const row = {
    rowNumber: 2, productId: product.id, currentVersion: product.version,
    categoryPathKo: category.pathKo, nameKo: product.nameKo, descriptionKo: description(301),
    priceKrw: 1000, unitLabel: "\uac1c",
  };
  const preview = ((await (await post("/api/product-import/preview", { rows: [row] })).json() as any).data);
  expect(preview.rows[0].status).toBe("invalid");
  const applied = ((await (await post("/api/product-import/apply", { rows: [row] })).json() as any).data);
  expect(applied).toMatchObject({ updatedRows: 0, invalidRows: 1 });
  expect(((await (await request(`/api/products/${product.id}`)).json() as any).data.descriptionKo)).toBe("short");
});

it("rejects an overlong description when adding a shared catalog product", async () => {
  const suffix = crypto.randomUUID();
  const catalogProductId = `eval-catalog-${suffix}`;
  await applyProductCatalogImport(fixtureDatabase(), {
    schemaVersion: 2, reviewStatus: "approved", artifactId: `eval-${suffix}`,
    products: [{ id: catalogProductId, kind: "otc", sourceKind: "e-drug", officialId: `OTC-${suffix}`, nameKo: `Eval product ${suffix}`, manufacturerKo: "Eval", status: "published", collectedAt: "2026-10-03T00:00:00.000Z", contentHash: `product-${suffix}` }],
    descriptions: [{ id: `${catalogProductId}-description-1`, catalogProductId, version: 1, nameKo: `Eval product ${suffix}`, descriptionKo: "short", sourceHash: `source-${suffix}`, contentHash: `description-${suffix}`, status: "approved", collectedAt: "2026-10-03T00:00:00.000Z" }],
    packages: [],
  }, "eval-operator");
  const db = fixtureDatabase();
  await expect(addProductCatalog(accountDatabase((env as Env).DB, db.accountId), {
    items: [{ catalogProductId, descriptionVersion: 1, categoryId: "category-supplements", quantity: 1, unitCode: "ea", priceKrw: 1000, override: { descriptionKo: description(301) } }],
  }, "eval-operator")).rejects.toThrow();
});

it("blocks update and overwrite restores containing an overlong product description", async () => {
  const long = description(301);
  const restoreSource = await post("/api/products", input(`eval-restore-${crypto.randomUUID()}`, "short"));
  expect(restoreSource.status).toBe(201);
  const restoreProduct = (await restoreSource.json() as any).data;
  const backup = await (await request("/api/admin/backup")).json() as any;
  backup.data.products.find((item: any) => item.id === restoreProduct.id).description_ko = long;
  const restore = await post("/api/admin/restore/preview", { mode: "update", backup });
  expect(restore.status).toBe(200);
  const result = (await restore.json() as any).data;
  expect(result.canApply).toBe(false);
  expect(result.conflicts).toContainEqual(expect.objectContaining({ domain: "products", key: restoreProduct.id }));
  const applied = await post("/api/admin/restore/apply", { mode: "update", backup });
  expect(applied.status).toBe(409);
  expect(((await applied.json() as any).error).code).toBe("backup_conflict");

  const overwrite = await post("/api/admin/restore/preview", { mode: "overwrite", backup });
  expect(overwrite.status).toBe(200);
  expect(((await overwrite.json() as any).data).canApply).toBe(false);
  const safetyBackup = (await (await request("/api/admin/backup")).json() as any);
  const overwriteApplied = await post("/api/admin/restore/apply", {
    mode: "overwrite", backup, confirmation: "덮어쓰기",
    safetyBackupExportedAt: safetyBackup.manifest.exportedAt,
  });
  expect(overwriteApplied.status).toBe(409);
  expect(((await overwriteApplied.json() as any).error).code).toBe("backup_conflict");
  expect(((await (await request(`/api/products/${restoreProduct.id}`)).json() as any).data.descriptionKo)).toBe("short");
});
