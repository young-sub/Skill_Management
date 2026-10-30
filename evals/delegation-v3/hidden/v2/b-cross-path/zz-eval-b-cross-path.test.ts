import { expect, it } from "vitest";
import { createTestAccount } from "./accountFixture";

it("keeps custom sales-unit names within twenty trimmed characters on create, edit, and import", async () => {
  const account = await createTestAccount("developer");
  const categoryResponse = await account.request("/categories", "POST", { nameKo: `단위 경계 분류 ${crypto.randomUUID()}`, sortOrder: 10 });
  expect(categoryResponse.status, await categoryResponse.clone().text()).toBe(201);
  const category = await (categoryResponse.json() as Promise<any>).then(body => body.data);
  const custom = (unitCustomKo: string) => ({ quantity: 1, unitCode: "custom", unitCustomKo, priceKrw: 1200 });
  const create = async (unitCustomKo: string, name: string) => account.request("/products", "POST", {
    categoryId: category.id, nameKo: name, descriptionKo: "상품 설명",
    offers: [custom(unitCustomKo)],
  });

  const exactlyTwenty = "가".repeat(20);
  const created = await create(exactlyTwenty, `단위 경계 ${crypto.randomUUID()}`);
  expect(created.status, await created.clone().text()).toBe(201);
  const product = await (created.json() as Promise<any>).then(body => body.data);
  expect(product.offers[0].unitCustomKo).toBe(exactlyTwenty);

  const twentyOne = "가".repeat(21);
  const rejectedCreate = await create(twentyOne, `단위 초과 ${crypto.randomUUID()}`);
  expect(rejectedCreate.status).toBe(400);
  expect((await rejectedCreate.json() as any).error.code).toBe("validation_failed");
  const rejectedUpdate = await account.request(`/products/${product.id}`, "PATCH", {
    expectedVersion: product.version, offers: [custom(twentyOne)],
  });
  expect(rejectedUpdate.status).toBe(400);
  expect((await rejectedUpdate.json() as any).error.code).toBe("validation_failed");
  const unchanged = await (await account.request(`/products/${product.id}`)).json() as any;
  expect(unchanged.data).toMatchObject({ version: product.version, offers: [expect.objectContaining({ unitCustomKo: exactlyTwenty })] });

  const importName = `가져오기 경계 ${crypto.randomUUID()}`;
  const importedTwenty = {
    rows: [{ rowNumber: 2, categoryNameKo: category.nameKo, nameKo: importName, descriptionKo: "설명", priceKrw: 1200, unitLabel: "직접 입력", unitCustomKo: exactlyTwenty }],
  };
  const preview = await (await account.request("/product-import/preview", "POST", importedTwenty)).json() as any;
  expect(preview.data.rows[0]).toMatchObject({ status: "create" });
  const applied = await (await account.request("/product-import/apply", "POST", importedTwenty)).json() as any;
  expect(applied.data).toMatchObject({ createdRows: 1, updatedRows: 0 });
  const tooLongImportName = `가져오기 초과 ${crypto.randomUUID()}`;
  const importedTwentyOne = {
    rows: [{ rowNumber: 2, categoryNameKo: category.nameKo, nameKo: tooLongImportName, descriptionKo: "설명", priceKrw: 1200, unitLabel: "직접 입력", unitCustomKo: twentyOne }],
  };
  const invalidPreview = await (await account.request("/product-import/preview", "POST", importedTwentyOne)).json() as any;
  expect(invalidPreview.data.rows[0]).toMatchObject({ status: "invalid" });
  const invalidApply = await (await account.request("/product-import/apply", "POST", importedTwentyOne)).json() as any;
  expect(invalidApply.data).toMatchObject({ createdRows: 0, updatedRows: 0, invalidRows: 1 });
  const absent = await (await account.request(`/products?search=${encodeURIComponent(tooLongImportName)}`)).json() as any;
  expect(absent.data).toMatchObject({ total: 0, items: [] });

  const paddedUnit = `${"가".repeat(10)}${" ".repeat(20)}나`;
  const paddedName = `내부 공백 초과 ${crypto.randomUUID()}`;
  const paddedImport = {
    rows: [{ rowNumber: 2, categoryNameKo: category.nameKo, nameKo: paddedName, descriptionKo: "설명", priceKrw: 1200, unitLabel: "직접 입력", unitCustomKo: paddedUnit }],
  };
  const paddedPreview = await (await account.request("/product-import/preview", "POST", paddedImport)).json() as any;
  expect(paddedPreview.data.rows[0]).toMatchObject({ status: "invalid" });
  const paddedApply = await (await account.request("/product-import/apply", "POST", paddedImport)).json() as any;
  expect(paddedApply.data).toMatchObject({ createdRows: 0, updatedRows: 0, invalidRows: 1 });
  const paddedAbsent = await (await account.request(`/products?search=${encodeURIComponent(paddedName)}`)).json() as any;
  expect(paddedAbsent.data).toMatchObject({ total: 0, items: [] });
});
