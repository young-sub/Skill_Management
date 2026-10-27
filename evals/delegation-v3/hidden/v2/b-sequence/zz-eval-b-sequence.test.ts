import { env } from "cloudflare:workers";
import { expect, it } from "vitest";
import { createTestAccount } from "./accountFixture";

const data = async (response: Response) => (await response.json() as any).data;
const addCategory = async (account: Awaited<ReturnType<typeof createTestAccount>>, nameKo: string, parentId: string | null = null, iconKey = "tag") => {
  const response = await account.request("/categories", "POST", { nameKo, sortOrder: 10, ...(parentId ? { parentId } : {}), iconKey });
  expect(response.status, await response.clone().text()).toBe(201);
  return data(response);
};

it("duplicates only category structure, preserves subtree order, and rejects a fourth level atomically", async () => {
  const account = await createTestAccount("developer");
  const suffix = crypto.randomUUID();
  const sourceRoot = await addCategory(account, `원본-${suffix}`);
  const sourceBranch = await addCategory(account, `중간-${suffix}`, sourceRoot.id, "pill");
  const sourceLeaf = await addCategory(account, `가 하위-${suffix}`, sourceBranch.id, "heart-pulse");
  const secondLeaf = await addCategory(account, `나 하위-${suffix}`, sourceBranch.id, "tag");
  await account.request(`/categories/${secondLeaf.id}`, "PATCH", { isActive: false });

  const targetRoot = await addCategory(account, `대상-${suffix}`);
  const targetSibling = await addCategory(account, `기존 자식-${suffix}`, targetRoot.id);
  const tooDeepParent = await addCategory(account, `깊은 대상-${suffix}`, targetRoot.id);

  const product = await account.request("/products", "POST", {
    categoryId: sourceLeaf.id,
    nameKo: `연결 상품-${suffix}`,
    descriptionKo: "원본에만 남아야 하는 상품",
    offers: [{ quantity: 1, unitCode: "ea", priceKrw: 1000 }],
  });
  expect(product.status).toBe(201);
  const db = (env as Env).DB;
  const phraseId = crypto.randomUUID();
  const now = new Date().toISOString();
  await db.prepare(`INSERT INTO category_signs
    (id,owner_id,name,normalized_name,sort_order,version,is_active,created_at,updated_at,category_id)
    VALUES (?,?,?,?,0,1,1,?,?,?)`)
    .bind(phraseId, account.id, `안내-${suffix}`, `안내-${suffix}`, now, now, sourceLeaf.id).run();
  const setId = crypto.randomUUID(), jobId = crypto.randomUUID();
  await db.prepare(`INSERT INTO print_sets (id,name,items_json,created_by,created_at,updated_by,updated_at,owner_id,design_type)
    VALUES (?, ?, '[]', ?, ?, ?, ?, ?, 'category')`)
    .bind(setId, `출력 목록-${suffix}`, account.id, now, account.id, now, account.id).run();
  await db.prepare(`INSERT INTO print_jobs (id,item_count,page_count,snapshot_json,created_by,created_at,owner_id,design_type)
    VALUES (?,1,1,'{}',?,?,?,'category')`)
    .bind(jobId, account.id, now, account.id).run();

  const originalBefore = await data(await account.request("/categories"));
  const setsBefore = await db.prepare("SELECT count(*) AS n FROM print_sets WHERE owner_id=?").bind(account.id).first<number>("n");
  const jobsBefore = await db.prepare("SELECT count(*) AS n FROM print_jobs WHERE owner_id=?").bind(account.id).first<number>("n");
  const copyResponse = await account.request(`/categories/${sourceBranch.id}/duplicate`, "POST", {
    parentId: targetRoot.id,
    nameKo: `중간 복사-${suffix}`,
  });
  expect(copyResponse.status, await copyResponse.clone().text()).toBe(201);
  const copied = await data(copyResponse) as any[];
  expect(copied).toHaveLength(3);
  const copiedRoot = copied[0], copiedLeaf = copied[1], copiedInactiveLeaf = copied[2];
  expect(copiedRoot).toMatchObject({
    nameKo: `중간 복사-${suffix}`, parentId: targetRoot.id, depth: 2, iconKey: "pill", isActive: true,
  });
  expect(copiedLeaf).toMatchObject({
    nameKo: sourceLeaf.nameKo, parentId: copiedRoot.id, depth: 3, iconKey: "heart-pulse", isActive: true,
    activeProductCount: 0, activePhraseCount: 0,
  });
  expect(copiedInactiveLeaf).toMatchObject({
    nameKo: secondLeaf.nameKo, parentId: copiedRoot.id, depth: 3, iconKey: "tag", isActive: false,
    activeProductCount: 0, activePhraseCount: 0,
  });
  expect(new Set(copied.map((item: any) => item.id)).size).toBe(3);
  expect(copied.every((item: any) => ![sourceBranch.id, sourceLeaf.id, secondLeaf.id].includes(item.id))).toBe(true);
  expect(copiedRoot.sortOrder).toBeGreaterThan(targetSibling.sortOrder);
  expect((await data(await account.request("/categories"))).filter((item: any) => [sourceBranch.id, sourceLeaf.id, secondLeaf.id].includes(item.id)))
    .toEqual(originalBefore.filter((item: any) => [sourceBranch.id, sourceLeaf.id, secondLeaf.id].includes(item.id)));
  expect(await db.prepare("SELECT id FROM products WHERE category_id=? AND deleted_at IS NULL").bind(sourceLeaf.id).first()).not.toBeNull();
  expect(await db.prepare("SELECT id FROM products WHERE category_id=? AND deleted_at IS NULL").bind(copiedLeaf.id).first()).toBeNull();
  expect(await db.prepare("SELECT id FROM category_signs WHERE category_id=?").bind(sourceLeaf.id).first()).toMatchObject({ id: phraseId });
  expect(await db.prepare("SELECT id FROM category_signs WHERE category_id=?").bind(copiedLeaf.id).first()).toBeNull();
  expect(await db.prepare("SELECT count(*) AS n FROM print_sets WHERE owner_id=?").bind(account.id).first<number>("n")).toBe(setsBefore);
  expect(await db.prepare("SELECT count(*) AS n FROM print_jobs WHERE owner_id=?").bind(account.id).first<number>("n")).toBe(jobsBefore);

  const topCopy = await account.request(`/categories/${sourceRoot.id}/duplicate`, "POST", {
    parentId: null,
    nameKo: `최상위 복사-${suffix}`,
  });
  expect(topCopy.status, await topCopy.clone().text()).toBe(201);
  const topItems = await data(topCopy) as any[];
  expect(topItems).toHaveLength(4);
  expect(topItems[0]).toMatchObject({ nameKo: `최상위 복사-${suffix}`, parentId: null, depth: 1 });
  expect(topItems[1]).toMatchObject({ nameKo: sourceBranch.nameKo, parentId: topItems[0].id, depth: 2 });
  expect(topItems[2]).toMatchObject({ nameKo: sourceLeaf.nameKo, parentId: topItems[1].id, depth: 3 });
  expect(topItems[3]).toMatchObject({ nameKo: secondLeaf.nameKo, parentId: topItems[1].id, depth: 3 });
  expect(await db.prepare("SELECT id FROM products WHERE category_id IN (?,?)").bind(topItems[2].id, topItems[3].id).first()).toBeNull();

  const siblingsBefore = (await data(await account.request("/categories"))).filter((item: any) => item.parentId === tooDeepParent.id);
  const categoriesBefore = await data(await account.request("/categories"));
  const rejected = await account.request(`/categories/${sourceBranch.id}/duplicate`, "POST", {
    parentId: tooDeepParent.id,
    nameKo: `너무 깊은 복사-${suffix}`,
  });
  expect(rejected.status).toBe(400);
  expect((await rejected.json() as any).error.code).toBe("category_hierarchy_invalid");
  expect(await data(await account.request("/categories"))).toEqual(categoriesBefore);
  expect((await data(await account.request("/categories"))).filter((item: any) => item.parentId === tooDeepParent.id)).toEqual(siblingsBefore);
  expect(await db.prepare("SELECT count(*) AS n FROM products WHERE category_id IN (?,?)").bind(copiedLeaf.id, sourceLeaf.id).first<number>("n")).toBe(1);

  const beforeFourthLevel = await data(await account.request("/categories"));
  const fourthCreate = await account.request("/categories", "POST", {
    nameKo: `4단계-${suffix}`, sortOrder: 10, parentId: sourceLeaf.id,
  });
  expect(fourthCreate.status).toBe(400);
  expect((await fourthCreate.json() as any).error.code).toBe("category_hierarchy_invalid");
  expect(await data(await account.request("/categories"))).toEqual(beforeFourthLevel);
  const fourthMove = await account.request(`/categories/${sourceBranch.id}/move`, "PATCH", {
    parentId: tooDeepParent.id, beforeId: null,
  });
  expect(fourthMove.status).toBe(400);
  expect((await fourthMove.json() as any).error.code).toBe("category_hierarchy_invalid");
  expect(await data(await account.request("/categories"))).toEqual(beforeFourthLevel);
});
