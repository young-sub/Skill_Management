import { fixtureFetch } from "./accountFixture";
import { describe, expect, it } from "vitest";

const request = (path: string, method = "GET", body?: unknown) => fixtureFetch(`http://localhost${path}`, {
  method,
  headers: body === undefined ? undefined : { "content-type": "application/json", origin: "http://localhost" },
  ...(body === undefined ? {} : { body: JSON.stringify(body) }),
});
const data = async (response: Response) => (await response.json() as any).data;
async function createProduct(name: string, offers: Array<{ quantity: number; priceKrw: number }> = [
  { quantity: 1, priceKrw: 1200 }, { quantity: 3, priceKrw: 3000 }, { quantity: 5, priceKrw: 4500 },
]) {
  const response = await request("/api/products", "POST", {
    categoryId: "category-supplements", nameKo: name, descriptionKo: "원래 설명",
    offers: offers.map((offer) => ({ ...offer, unitCode: "box" })),
  });
  expect(response.status).toBe(201);
  return data(response);
}
function blankOfferRow(product: any, rowNumber: number, descriptionKo: string) {
  return {
    rowNumber, productId: product.id, currentVersion: product.version, categoryPathKo: ["영양제"],
    nameKo: product.nameKo, descriptionKo, singleQuantity: "", priceKrw: "", unitLabel: "", unitCustomKo: "", bundles: [],
  };
}

describe("product update offer preservation in direct edits and workbook imports", () => {
  it("keeps omitted offers on a direct edit and rejects stale edits atomically", async () => {
    const created = await createProduct(`직접 옵션 ${crypto.randomUUID()}`);
    const before = await data(await request(`/api/products/${created.id}`));
    const saved = await request(`/api/products/${created.id}`, "PATCH", {
      expectedVersion: before.version, descriptionKo: "직접 수정한 설명",
    });
    expect(saved.status).toBe(200);
    const after = await data(await request(`/api/products/${created.id}`));
    expect(after).toMatchObject({ version: before.version + 1, descriptionKo: "직접 수정한 설명", offers: before.offers });

    const stale = await request(`/api/products/${created.id}`, "PATCH", {
      expectedVersion: before.version, nameKo: "오래된 화면의 이름",
    });
    expect(stale.status).toBe(409);
    expect((await stale.json() as any).error.code).toBe("product_conflict");
    const unchanged = await data(await request(`/api/products/${created.id}`));
    expect(unchanged).toMatchObject({ version: after.version, nameKo: after.nameKo, descriptionKo: after.descriptionKo, offers: after.offers });
  });

  it("preserves a blank workbook offer section, replaces filled tiers in order, and isolates invalid rows", async () => {
    const keep = await createProduct(`보존 옵션 ${crypto.randomUUID()}`);
    const replace = await createProduct(`교체 옵션 ${crypto.randomUUID()}`, [{ quantity: 1, priceKrw: 2000 }, { quantity: 4, priceKrw: 7000 }]);
    const invalid = await createProduct(`오류 옵션 ${crypto.randomUUID()}`, [{ quantity: 1, priceKrw: 2600 }, { quantity: 6, priceKrw: 13000 }]);
    const keepBefore = await data(await request(`/api/products/${keep.id}`));
    const invalidBefore = await data(await request(`/api/products/${invalid.id}`));

    const rows = [
      blankOfferRow(keep, 2, "가격은 그대로인 설명"),
      {
        rowNumber: 3, productId: replace.id, currentVersion: replace.version, categoryPathKo: ["영양제"],
        nameKo: replace.nameKo, descriptionKo: "새 가격 구성을 적용", singleQuantity: 1, priceKrw: 2500,
        unitLabel: "박스", bundles: [{ quantity: 5, priceKrw: 11000 }, { quantity: 10, priceKrw: 20000 }],
      },
      {
        rowNumber: 4, productId: invalid.id, currentVersion: invalid.version, categoryPathKo: ["영양제"],
        nameKo: invalid.nameKo, descriptionKo: "저장되면 안 되는 설명", singleQuantity: 1, priceKrw: 3000,
        unitLabel: "박스", bundles: [{ quantity: 4, priceKrw: "" }],
      },
    ];
    const appliedResponse = await request("/api/product-import/apply", "POST", { rows });
    expect(appliedResponse.status).toBe(200);
    const applied = await data(appliedResponse);
    expect(applied).toMatchObject({ totalRows: 3, updatedRows: 2, invalidRows: 1 });
    expect(applied.rows.map((row: any) => row.status)).toEqual(["update", "update", "invalid"]);

    const kept = await data(await request(`/api/products/${keep.id}`));
    expect(kept).toMatchObject({ version: keepBefore.version + 1, descriptionKo: "가격은 그대로인 설명", offers: keepBefore.offers });
    const replaced = await data(await request(`/api/products/${replace.id}`));
    expect(replaced.offers.map(({ quantity, priceKrw }: any) => ({ quantity, priceKrw }))).toEqual([
      { quantity: 1, priceKrw: 2500 }, { quantity: 5, priceKrw: 11000 }, { quantity: 10, priceKrw: 20000 },
    ]);
    const untouched = await data(await request(`/api/products/${invalid.id}`));
    expect(untouched).toMatchObject({ version: invalidBefore.version, descriptionKo: invalidBefore.descriptionKo, offers: invalidBefore.offers });
  });
});