import { env } from "cloudflare:workers";
import { expect, it } from "vitest";
import { fixtureDatabase, fixtureFetch, createTestAccount } from "./accountFixture";
import { applyOperatorContent, previewOperatorContent } from "../src/worker/operatorContent";
import { addProductCatalog, applyProductCatalogImport } from "../src/worker/productCatalog";
import { accountDatabase } from "../src/worker/accountData";

const request = (path: string, init?: RequestInit) => fixtureFetch(`http://localhost${path}`, {
  ...init,
  headers: init?.body ? { "content-type": "application/json", origin: "http://localhost", ...init.headers } : init?.headers,
});
const post = (path: string, body: unknown) => request(path, { method: "POST", body: JSON.stringify(body) });
const productInput = (nameKo: string, offers: unknown[]) => ({
  categoryId: "category-supplements", nameKo, descriptionKo: "offer boundary",
  offers,
});
const orderedOffers = [
  { quantity: 50, unitCode: "ea", priceKrw: 5000 },
  { quantity: 2, unitCode: "ea", priceKrw: 2500 },
];

it("keeps direct create, edit, copy, and import on one exact offer rule", async () => {
  const suffix = crypto.randomUUID();
  const createdResponse = await post("/api/products", productInput(`offer-source-${suffix}`, orderedOffers));
  expect(createdResponse.status).toBe(201);
  const source = (await createdResponse.json() as any).data;
  expect(source.offers.map((offer: any) => offer.quantity)).toEqual([50, 2]);

  const copied = await post(`/api/products/${source.id}/duplicate`, {});
  expect(copied.status).toBe(201);
  expect(((await copied.json() as any).data).offers.map((offer: any) => offer.quantity)).toEqual([50, 2]);

  const rejected = await post("/api/products", productInput(`offer-invalid-${suffix}`, [
    { quantity: 999, unitCode: "ea", priceKrw: 5000 },
    { quantity: 999, unitCode: "ea", priceKrw: 2500 },
  ]));
  expect(rejected.status).toBe(400);
  const overLimit = await post("/api/products", productInput(`offer-over-limit-${suffix}`, [
    { quantity: 1000, unitCode: "ea", priceKrw: 5000 },
  ]));
  expect(overLimit.status).toBe(400);

  const invalidEdit = await request(`/api/products/${source.id}`, {
    method: "PATCH", body: JSON.stringify({ expectedVersion: source.version, offers: [
      { quantity: 999, unitCode: "ea", priceKrw: 5000 },
      { quantity: 2, unitCode: "box", priceKrw: 2500 },
    ] }),
  });
  expect(invalidEdit.status).toBe(400);
  const unchanged = (await (await request(`/api/products/${source.id}`)).json() as any).data;
  expect(unchanged).toMatchObject({ version: source.version, offers: source.offers });

  const atLimit = await post("/api/products", productInput(`offer-max-${suffix}`, Array.from({ length: 10 }, (_, index) => ({
    quantity: 999 - index, unitCode: "ea", priceKrw: index,
  }))));
  expect(atLimit.status).toBe(201);
  const tooMany = await post("/api/products", productInput(`offer-too-many-${suffix}`, Array.from({ length: 11 }, (_, index) => ({
    quantity: 999 - index, unitCode: "ea", priceKrw: index,
  }))));
  expect(tooMany.status).toBe(400);

  const category = ((await (await request("/api/categories")).json() as any).data)
    .find((item: any) => item.id === "category-supplements");
  const goodRow = {
    rowNumber: 2, categoryPathKo: category.pathKo, nameKo: `offer-import-good-${suffix}`,
    descriptionKo: "valid import row", singleQuantity: 50, priceKrw: 5000, unitLabel: "\uac1c",
    bundles: [{ quantity: 2, priceKrw: 2500 }],
  };
  const badRow = { ...goodRow, rowNumber: 3, nameKo: `offer-import-bad-${suffix}`, bundles: [{ quantity: 50, priceKrw: 2500 }] };
  const result = (await (await post("/api/product-import/apply", { rows: [goodRow, badRow] })).json() as any).data;
  expect(result).toMatchObject({ createdRows: 1, invalidRows: 1 });
  const imported = ((await (await request(`/api/products?search=${encodeURIComponent(goodRow.nameKo)}`)).json() as any).data.items[0]);
  expect(imported.offers.map((offer: any) => offer.quantity)).toEqual([50, 2]);

  const suffix2 = crypto.randomUUID();
  await applyProductCatalogImport(fixtureDatabase(), {
    schemaVersion: 2, reviewStatus: "approved", artifactId: `offer-catalog-${suffix2}`,
    products: [{ id: `offer-catalog-${suffix2}`, kind: "otc", sourceKind: "e-drug", officialId: `O-${suffix2}`,
      nameKo: `offer catalog ${suffix2}`, manufacturerKo: "Eval", status: "published", collectedAt: "2026-10-20T00:00:00.000Z", contentHash: `product-${suffix2}` }],
    descriptions: [{ id: `offer-description-${suffix2}`, catalogProductId: `offer-catalog-${suffix2}`, version: 1,
      nameKo: `offer catalog ${suffix2}`, descriptionKo: "catalog description", sourceHash: `source-${suffix2}`,
      contentHash: `description-${suffix2}`, status: "approved", collectedAt: "2026-10-20T00:00:00.000Z" }],
    packages: [],
  }, "eval-operator");
  await expect(addProductCatalog(accountDatabase((env as Env).DB, fixtureDatabase().accountId), {
    items: [{ catalogProductId: `offer-catalog-${suffix2}`, descriptionVersion: 1, categoryId: "category-supplements",
      quantity: 1000, unitCode: "ea", priceKrw: 1000 }],
  }, "eval-operator")).rejects.toThrow();
});

it("blocks invalid offer tiers in customer and operator imports", async () => {
  const operator = await createTestAccount("operator");
  const customer = await createTestAccount("customer");
  const category = (await (await customer.request("/categories", "POST", { nameKo: `operator-${crypto.randomUUID()}`, sortOrder: 1 })).json() as any).data;
  const row = {
    rowNumber: 2, categoryPathKo: category.pathKo, nameKo: `operator-offer-${crypto.randomUUID()}`,
    descriptionKo: "operator import", singleQuantity: 1000, priceKrw: 1000, unitLabel: "\uac1c",
  };
  const operation = await previewOperatorContent({ DB: (env as Env).DB, MEDIA: (env as Env).MEDIA }, operator.id, customer.id, {
    kind: "product-import", rows: [row], reason: "offer validation",
  });
  expect(operation.status).toBe("conflict");
  expect(operation.summary).toMatchObject({ invalidRows: 1 });
  await expect(applyOperatorContent({ DB: (env as Env).DB, MEDIA: (env as Env).MEDIA }, operator.id, customer.id, operation.operationId))
    .rejects.toThrow();
});

it("rejects an invalid backup offer without changing the stored tiers", async () => {
  const created = await post("/api/products", productInput(`offer-restore-${crypto.randomUUID()}`, orderedOffers));
  expect(created.status).toBe(201);
  const product = (await created.json() as any).data;
  const backup = await (await request("/api/admin/backup")).json() as any;
  const rows = backup.data.product_offers.filter((offer: any) => offer.product_id === product.id);
  rows[0].quantity = 1000;

  const preview = await post("/api/admin/restore/preview", { mode: "update", backup });
  expect(preview.status).toBe(200);
  expect(((await preview.json() as any).data).canApply).toBe(false);
  const applied = await post("/api/admin/restore/apply", { mode: "update", backup });
  expect(applied.status).toBe(409);
  expect(((await applied.json() as any).error).code).toBe("backup_conflict");
  expect(((await (await request(`/api/products/${product.id}`)).json() as any).data).offers).toEqual(product.offers);
});

it("rejects an overlong offer list in a restored backup", async () => {
  const created = await post("/api/products", productInput(`offer-restore-count-${crypto.randomUUID()}`, orderedOffers));
  const product = (await created.json() as any).data;
  const backup = await (await request("/api/admin/backup")).json() as any;
  const offers = backup.data.product_offers.filter((offer: any) => offer.product_id === product.id);
  for (let index = 0; index < 9; index += 1) {
    backup.data.product_offers.push({ ...offers[0], id: crypto.randomUUID(), quantity: 100 + index, sort_order: offers.length + index });
  }
  const preview = await post("/api/admin/restore/preview", { mode: "update", backup });
  expect(preview.status).toBe(200);
  expect(((await preview.json() as any).data).canApply).toBe(false);
  const applied = await post("/api/admin/restore/apply", { mode: "update", backup });
  expect(applied.status).toBe(409);
  expect(((await applied.json() as any).error).code).toBe("backup_conflict");
  expect(((await (await request(`/api/products/${product.id}`)).json() as any).data).offers).toEqual(product.offers);
});

it("rejects a restored product with no offer tiers", async () => {
  const created = await post("/api/products", productInput(`offer-restore-empty-${crypto.randomUUID()}`, orderedOffers));
  const product = (await created.json() as any).data;
  const backup = await (await request("/api/admin/backup")).json() as any;
  backup.data.product_offers = backup.data.product_offers.filter((offer: any) => offer.product_id !== product.id);
  const preview = await post("/api/admin/restore/preview", { mode: "update", backup });
  expect(preview.status).toBe(200);
  expect(((await preview.json() as any).data).canApply).toBe(false);
  const applied = await post("/api/admin/restore/apply", { mode: "update", backup });
  expect(applied.status).toBe(409);
  expect(((await applied.json() as any).error).code).toBe("backup_conflict");
  expect(((await (await request(`/api/products/${product.id}`)).json() as any).data).offers).toEqual(product.offers);
});
