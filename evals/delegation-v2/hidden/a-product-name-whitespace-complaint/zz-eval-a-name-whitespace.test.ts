import { fixtureFetch } from "./accountFixture";
import { describe, expect, it } from "vitest";

const request = (path: string, method = "GET", body?: unknown) => fixtureFetch(`http://localhost${path}`, {
  method,
  headers: body === undefined ? undefined : { "content-type": "application/json", origin: "http://localhost" },
  ...(body === undefined ? {} : { body: JSON.stringify(body) }),
});
const data = async (response: Response) => (await response.json() as any).data;
async function createProduct(name: string) {
  const response = await request("/api/products", "POST", {
    categoryId: "category-supplements", nameKo: name, descriptionKo: "공백 확인 상품",
    offers: [{ quantity: 1, unitCode: "box", priceKrw: 1000 }],
  });
  expect(response.status).toBe(201);
  return data(response);
}
const importRow = (product: any, nameKo: string, rowNumber = 2) => ({
  rowNumber, productId: product.id, currentVersion: product.version, categoryPathKo: ["영양제"],
  nameKo, descriptionKo: "공백 확인 상품", singleQuantity: 1, priceKrw: 1000, unitLabel: "박스", bundles: [],
});

describe("product names preserve one readable space between words", () => {
  it("cleans outside whitespace and compresses repeated spaces on registration", async () => {
    const response = await request("/api/products", "POST", {
      categoryId: "category-supplements", nameKo: "  비타민   C  500  ", descriptionKo: "등록 공백",
      offers: [{ quantity: 1, unitCode: "box", priceKrw: 1000 }],
    });
    expect(response.status).toBe(201);
    expect((await data(response)).nameKo).toBe("비타민 C 500");
  });

  it("keeps word boundaries after a direct product edit", async () => {
    const product = await createProduct(`직접공백${crypto.randomUUID()}`);
    const response = await request(`/api/products/${product.id}`, "PATCH", {
      expectedVersion: product.version, nameKo: "  비타민\tC\n 1000  ",
    });
    expect(response.status).toBe(200);
    expect((await data(await request(`/api/products/${product.id}`))).nameKo).toBe("비타민 C 1000");
  });

  it("keeps the same word boundaries in spreadsheet updates", async () => {
    const product = await createProduct(`일괄공백${crypto.randomUUID()}`);
    const response = await request("/api/product-import/apply", "POST", {
      rows: [importRow(product, "  허브\t혼합\n 상자  ")],
    });
    expect(response.status).toBe(200);
    expect(await data(response)).toMatchObject({ updatedRows: 1, invalidRows: 0 });
    expect((await data(await request(`/api/products/${product.id}`))).nameKo).toBe("허브 혼합 상자");
  });

  it("rejects a name that becomes empty and leaves direct and imported products unchanged", async () => {
    const product = await createProduct(`빈이름${crypto.randomUUID()}`);
    const direct = await request(`/api/products/${product.id}`, "PATCH", {
      expectedVersion: product.version, nameKo: "  \t\n  ",
    });
    expect(direct.status).toBe(400);
    expect((await direct.json() as any).error.code).toBe("validation_failed");
    expect((await data(await request(`/api/products/${product.id}`))).nameKo).toBe(product.nameKo);

    const applied = await request("/api/product-import/apply", "POST", {
      rows: [importRow(product, " \t\n ", 2), importRow(product, "정상 상품 이름", 3)],
    });
    expect(applied.status).toBe(200);
    expect(await data(applied)).toMatchObject({ invalidRows: 1, updatedRows: 0 });
    expect((await data(await request(`/api/products/${product.id}`))).nameKo).toBe(product.nameKo);
  });
});