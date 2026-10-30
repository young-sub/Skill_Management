import { expect, it } from "vitest";
import { fixtureFetch } from "./accountFixture";

const request = (path: string, method = "GET", body?: unknown) => fixtureFetch(`http://localhost/api${path}`, {
  method,
  headers: { origin: "http://localhost", "content-type": "application/json" },
  ...(body === undefined ? {} : { body: JSON.stringify(body) }),
});
const data = async (response: Response) => (await response.json() as any).data;
const tiers = (quantities: number[]) => quantities.map((quantity, index) => ({ quantity, unitCode: "ea", priceKrw: 1000 + index }));
const values = (offers: any[]) => offers.map(({ quantity, unitCode, priceKrw }) => ({ quantity, unitCode, priceKrw }));
async function product() {
  const response = await request("/products", "POST", {
    categoryId: "category-supplements", nameKo: `tiers-${crypto.randomUUID()}`,
    descriptionKo: "fourth price tier", offers: tiers([1, 10]),
  });
  expect(response.status).toBe(201);
  return data(response);
}

it("direct edits keep every submitted tier in order, including the exact ten-tier boundary", async () => {
  let current = await product();
  for (const quantities of [[10, 1, 30, 20], [8, 1, 3, 5, 2, 4, 6, 7, 10, 9]]) {
    const offers = tiers(quantities);
    const response = await request(`/products/${current.id}`, "PATCH", { expectedVersion: current.version, offers });
    expect(response.status).toBe(200);
    current = await data(response);
    expect(values(current.offers)).toEqual(offers);
    expect(values((await data(await request(`/products/${current.id}`))).offers)).toEqual(offers);
  }
  const retained = current.offers;
  const response = await request(`/products/${current.id}`, "PATCH", {
    expectedVersion: current.version, descriptionKo: "description-only edit",
  });
  expect(response.status).toBe(200);
  expect((await data(response)).offers).toEqual(retained);
});

it("spreadsheet updates also keep all five tiers in submitted order after a fresh read", async () => {
  const current = await product();
  const category = (await data(await request("/categories"))).find((row: any) => row.id === current.categoryId);
  const row = {
    rowNumber: 2, productId: current.id, currentVersion: current.version,
    categoryPathKo: category.pathKo, nameKo: current.nameKo, descriptionKo: current.descriptionKo,
    singleQuantity: 10, priceKrw: 1000, unitLabel: "개",
    bundles: [{ quantity: 1, priceKrw: 1001 }, { quantity: 30, priceKrw: 1002 },
      { quantity: 20, priceKrw: 1003 }, { quantity: 40, priceKrw: 1004 }],
  };
  const preview = await request("/product-import/preview", "POST", { rows: [row] });
  expect(preview.status).toBe(200);
  expect((await data(preview)).rows[0].status).toBe("update");
  const applied = await request("/product-import/apply", "POST", { rows: [row] });
  expect(applied.status).toBe(200);
  expect(await data(applied)).toMatchObject({ updatedRows: 1, invalidRows: 0 });
  const saved = await data(await request(`/products/${current.id}`));
  expect(values(saved.offers)).toEqual(tiers([10, 1, 30, 20, 40]));
});

it("one/three-tier edits still work and invalid or stale edits change no data or version", async () => {
  let current = await product();
  for (const quantities of [[2], [3, 1, 2]]) {
    const response = await request(`/products/${current.id}`, "PATCH", { expectedVersion: current.version, offers: tiers(quantities) });
    expect(response.status).toBe(200);
    current = await data(response);
    expect(values(current.offers)).toEqual(tiers(quantities));
  }
  for (const offers of [tiers([1, 1]), tiers(Array.from({ length: 11 }, (_, index) => index + 1))]) {
    const response = await request(`/products/${current.id}`, "PATCH", { expectedVersion: current.version, offers });
    expect(response.status).toBe(400);
    expect((await response.json() as any).error.code).toBe("validation_failed");
    expect(await data(await request(`/products/${current.id}`))).toEqual(current);
  }
  const stale = await request(`/products/${current.id}`, "PATCH", { expectedVersion: current.version - 1, offers: tiers([4, 5, 6, 7]) });
  expect(stale.status).toBe(409);
  expect((await stale.json() as any).error.code).toBe("product_conflict");
  expect(await data(await request(`/products/${current.id}`))).toEqual(current);
});
