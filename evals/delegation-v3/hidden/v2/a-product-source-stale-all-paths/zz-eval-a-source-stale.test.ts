import { fixtureFetch } from "./accountFixture";
import { env } from "cloudflare:workers";
import { describe, expect, it } from "vitest";

const request = (path: string, method = "GET", body?: unknown) => fixtureFetch(`http://localhost${path}`, {
  method,
  headers: body === undefined ? undefined : { "content-type": "application/json", origin: "http://localhost" },
  ...(body === undefined ? {} : { body: JSON.stringify(body) }),
});
const data = async (response: Response) => (await response.json() as any).data;
async function createProduct(name: string, description = "설명") {
  const response = await request("/api/products", "POST", {
    categoryId: "category-supplements", nameKo: name, descriptionKo: description,
    offers: [{ quantity: 1, unitCode: "box", priceKrw: 1000 }],
  });
  expect(response.status).toBe(201);
  return data(response);
}
async function approveAllLocales(product: any) {
  const now = new Date().toISOString();
  const locales = ["en", "zh-CN", "ja"] as const;
  await (env as Env).DB.batch(locales.map((locale) => (env as Env).DB.prepare(`INSERT INTO product_localizations
    (product_id, locale, name, description, source_hash, translation_hash, origin, provider, model, approved_by, approved_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, 'manual', NULL, NULL, 'reviewer@example.com', ?, ?)`)
    .bind(product.id, locale, `Approved ${locale} name`, `Approved ${locale} description`, product.sourceHash, `approved-${locale}-${product.id}`, now, now)));
}
async function expectStale(productId: string, expectedName?: string, expectedDescription?: string) {
  const product = await data(await request(`/api/products/${productId}`));
  if (expectedName !== undefined) expect(product.nameKo).toBe(expectedName);
  if (expectedDescription !== undefined) expect(product.descriptionKo).toBe(expectedDescription);
  expect(product.translationStatus).toBe("원문 변경");
  const detail = await data(await request(`/api/translations/fields/product/${productId}`));
  expect(detail.fields.name.locales.en).toMatchObject({ text: `Approved en name`, stale: true });
  expect(detail.fields.description.locales.en).toMatchObject({ text: `Approved en description`, stale: true });
}

describe("approved product translations stay visible and become stale across saves", () => {
  it("marks preserved approvals stale after a direct product edit", async () => {
    const product = await createProduct(`직접 수정 ${crypto.randomUUID()}`);
    await approveAllLocales(product);
    const response = await request(`/api/products/${product.id}`, "PATCH", { expectedVersion: product.version, nameKo: "직접 수정 새 이름" });
    expect(response.status).toBe(200);
    await expectStale(product.id, "직접 수정 새 이름", "설명");
  });

  it("marks preserved approvals stale after a spreadsheet product update", async () => {
    const product = await createProduct(`일괄 수정 ${crypto.randomUUID()}`);
    await approveAllLocales(product);
    const rows = [{
      rowNumber: 2, productId: product.id, currentVersion: product.version, categoryPathKo: ["영양제"],
      nameKo: product.nameKo, descriptionKo: "일괄 수정 설명", singleQuantity: 1, priceKrw: 1000, unitLabel: "박스", bundles: [],
    }];
    const applied = await request("/api/product-import/apply", "POST", { rows });
    expect(applied.status).toBe(200);
    expect(await data(applied)).toMatchObject({ updatedRows: 1, invalidRows: 0 });
    await expectStale(product.id, product.nameKo, "일괄 수정 설명");
  });

  it("marks preserved approvals stale when restore changes the product name", async () => {
    const product = await createProduct(`복원 이름 ${crypto.randomUUID()}`);
    await approveAllLocales(product);
    const backup = await (await request("/api/admin/backup")).json() as any;
    const saved = backup.data.products.find((row: any) => row.id === product.id);
    saved.name_ko = "복원 후 새 상품명";
    saved.name_ko_normalized = saved.name_ko.toLocaleLowerCase("ko");
    const preview = await data(await request("/api/admin/restore/preview", "POST", { mode: "update", backup }));
    expect(preview.canApply).toBe(true);
    const applied = await request("/api/admin/restore/apply", "POST", { mode: "update", backup });
    expect(applied.status).toBe(200);
    await expectStale(product.id, "복원 후 새 상품명", "설명");
  });

  it("marks preserved approvals stale when restore changes the product description", async () => {
    const product = await createProduct(`복원 설명 ${crypto.randomUUID()}`);
    await approveAllLocales(product);
    const backup = await (await request("/api/admin/backup")).json() as any;
    backup.data.products.find((row: any) => row.id === product.id).description_ko = "복원 후 새 설명";
    const preview = await data(await request("/api/admin/restore/preview", "POST", { mode: "update", backup }));
    expect(preview.canApply).toBe(true);
    const applied = await request("/api/admin/restore/apply", "POST", { mode: "update", backup });
    expect(applied.status).toBe(200);
    await expectStale(product.id, product.nameKo, "복원 후 새 설명");
  });

  it("keeps approvals complete when only an offer price changes", async () => {
    const product = await createProduct(`가격 수정 ${crypto.randomUUID()}`);
    await approveAllLocales(product);
    const response = await request(`/api/products/${product.id}`, "PATCH", {
      expectedVersion: product.version, offers: [{ quantity: 1, unitCode: "box", priceKrw: 1200 }],
    });
    expect(response.status).toBe(200);
    const current = await data(await request(`/api/products/${product.id}`));
    expect(current.translationStatus).toBe("번역 완료");
    const detail = await data(await request(`/api/translations/fields/product/${product.id}`));
    expect(detail.fields.name.locales.en).toMatchObject({ text: "Approved en name", stale: false });
    expect(detail.fields.description.locales.en).toMatchObject({ text: "Approved en description", stale: false });
  });
});