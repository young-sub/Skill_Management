import { expect, it } from "vitest";
import { fixtureFetch } from "./accountFixture";

const request = (path: string, init?: RequestInit) => fixtureFetch(`http://localhost${path}`, {
  ...init,
  headers: init?.body ? { "content-type": "application/json", origin: "http://localhost", ...init.headers } : init?.headers,
});
const post = (path: string, body: unknown) => request(path, { method: "POST", body: JSON.stringify(body) });

it("keeps the description limit consistent for product edits and new products", async () => {
  const suffix = crypto.randomUUID();
  const originalDescription = "x".repeat(500);
  const tooLong = "x".repeat(501);
  const created = await post("/api/products", {
    categoryId: "category-supplements", nameKo: `eval-edit-${suffix}`, descriptionKo: originalDescription,
    offers: [{ quantity: 1, unitCode: "ea", priceKrw: 1000 }],
  });
  expect(created.status).toBe(201);
  const product = (await created.json() as any).data;

  const siblingCreate = await post("/api/products", {
    categoryId: "category-supplements", nameKo: `eval-create-${suffix}`, descriptionKo: tooLong,
    offers: [{ quantity: 1, unitCode: "ea", priceKrw: 1000 }],
  });
  expect(siblingCreate.status).toBe(400);

  const updated = await request(`/api/products/${product.id}`, {
    method: "PATCH", body: JSON.stringify({ expectedVersion: product.version, descriptionKo: tooLong }),
  });
  expect(updated.status).toBe(400);
  const fetched = (await (await request(`/api/products/${product.id}`)).json() as any).data;
  expect(fetched.descriptionKo).toBe(originalDescription);
});
