import ExcelJS from "exceljs";
import { expect, it } from "vitest";
import { parseProductWorkbook } from "../src/client/productWorkbook";
import { LEGACY_PRODUCT_XLSX_HEADERS, PRODUCT_XLSX_ROW_KIND_HEADER } from "../src/shared/product";
import { fixtureFetch } from "./accountFixture";

const request = (path: string, method = "GET", body?: unknown) => fixtureFetch(`http://localhost${path}`, {
  method,
  headers: body === undefined ? undefined : { "content-type": "application/json", origin: "http://localhost" },
  ...(body === undefined ? {} : { body: JSON.stringify(body) }),
});
const data = async (response: Response) => (await response.json() as any).data;

it("keeps every current offer when a legacy-layout spreadsheet row leaves all offer cells blank", async () => {
  const created = await request("/api/products", "POST", {
    categoryId: "category-supplements", nameKo: `구형 양식 ${crypto.randomUUID()}`, descriptionKo: "원래 설명",
    offers: [{ quantity: 1, priceKrw: 1200 }, { quantity: 3, priceKrw: 3000 }, { quantity: 5, priceKrw: 4500 }]
      .map((offer) => ({ ...offer, unitCode: "box" })),
  });
  expect(created.status).toBe(201);
  const before = await data(await request(`/api/products/${(await data(created)).id}`));

  // A workbook in the older column layout: offer cells are 단품가격_원, 단위, 직접입력단위, 묶음수량, 묶음가격_원.
  const workbook = new ExcelJS.Workbook();
  const sheet = workbook.addWorksheet("상품등록");
  sheet.addRow([...LEGACY_PRODUCT_XLSX_HEADERS, PRODUCT_XLSX_ROW_KIND_HEADER]);
  sheet.addRow([before.id, before.version, "영양제", before.nameKo, "구형 양식으로 고친 설명", "", "", "", "", "", ""]);
  const rows = await parseProductWorkbook(await workbook.xlsx.writeBuffer());

  const applied = await request("/api/product-import/apply", "POST", { rows });
  expect(applied.status).toBe(200);
  expect((await data(applied)).rows[0].status).toBe("update");
  const after = await data(await request(`/api/products/${before.id}`));
  expect(after).toMatchObject({ descriptionKo: "구형 양식으로 고친 설명", version: before.version + 1, offers: before.offers });
});
