import { env } from "cloudflare:workers";
import { expect, it } from "vitest";
import { createTestAccount } from "./accountFixture";

it("defaults catalog browse and search to forty while preserving bounds, cursor order, and API response shape", async () => {
  const account = await createTestAccount("developer");
  const db = (env as Env).DB;
  const prefix = `v2-catalog-${crypto.randomUUID()}`;
  const stamp = "2026-10-20T12:00:00.000Z";
  for (let start = 0; start < 110; start += 15) {
    await db.batch(Array.from({ length: Math.min(15, 110 - start) }, (_, offset) => {
      const index = start + offset;
      const id = `${prefix}-${String(index).padStart(2, "0")}`;
      return db.prepare(`INSERT INTO catalog_products
        (id,kind,source_kind,official_id,name_ko,name_ko_normalized,manufacturer_ko,manufacturer_ko_normalized,responsible_seller_ko,status,collected_at,created_at,updated_at)
        VALUES (?, ?, 'eval', ?, ?, ?, 'maker', 'maker', '', 'published', ?, ?, ?)`)
        .bind(id, index % 2 ? "supplement" : "otc", id, `상품 ${prefix} ${String(index).padStart(2, "0")}`, `상품 ${prefix} ${String(index).padStart(2, "0")}`, stamp, stamp, stamp);
    }));
  }

  const browseResponse = await account.request("/product-catalog");
  expect(browseResponse.status).toBe(200);
  const browse = await (browseResponse.json() as Promise<any>).then(body => body.data);
  expect(Object.keys(browse).sort()).toEqual(["items", "nextCursor", "pageCount", "total"].sort());
  expect(browse).toMatchObject({ total: 110, pageCount: 40, nextCursor: expect.any(String) });
  expect(browse.items).toHaveLength(40);
  expect(browse.items.map((item: any) => item.id)).toEqual(
    [...browse.items.map((item: any) => item.id)].sort((left: string, right: string) => right.localeCompare(left)),
  );
  const next = await (await account.request(`/product-catalog?cursor=${encodeURIComponent(browse.nextCursor)}`)).json() as any;
  expect(next.data).toMatchObject({ total: 110, pageCount: 40, nextCursor: expect.any(String) });
  const last = await (await account.request(`/product-catalog?cursor=${encodeURIComponent(next.data.nextCursor)}`)).json() as any;
  expect(last.data).toMatchObject({ total: 110, pageCount: 30, nextCursor: null });
  const allItems = [...browse.items, ...next.data.items, ...last.data.items];
  expect(new Set(allItems.map((item: any) => item.id)).size).toBe(110);

  const searched = await (await account.request(`/product-catalog?search=${encodeURIComponent(prefix)}`)).json() as any;
  expect(searched.data).toMatchObject({ total: 110, pageCount: 40 });
  const kindOnly = await (await account.request("/product-catalog?kind=supplement")).json() as any;
  expect(kindOnly.data).toMatchObject({ total: 55, pageCount: 40, nextCursor: expect.any(String) });
  const typed = await (await account.request(`/product-catalog?kind=supplement&search=${encodeURIComponent(prefix)}`)).json() as any;
  expect(typed.data).toMatchObject({ total: 55, pageCount: 40, nextCursor: expect.any(String) });

  const one = await (await account.request(`/product-catalog?search=${encodeURIComponent(prefix)}&limit=1`)).json() as any;
  expect(one.data).toMatchObject({ total: 110, pageCount: 1, nextCursor: expect.any(String) });
  const fifty = await (await account.request(`/product-catalog?search=${encodeURIComponent(prefix)}&limit=50`)).json() as any;
  expect(fifty.data).toMatchObject({ total: 110, pageCount: 50, nextCursor: expect.any(String) });
  for (const limit of ["0", "51", "1.5"]) {
    const invalid = await account.request(`/product-catalog?limit=${limit}`);
    expect(invalid.status, limit).toBe(400);
    expect((await invalid.json() as any).error.code, limit).toBe("validation_failed");
  }

  const categoryResponse = await account.request("/categories", "POST", { nameKo: `내 상품 분류 ${crypto.randomUUID()}`, sortOrder: 10 });
  expect(categoryResponse.status).toBe(201);
  const category = await (categoryResponse.json() as Promise<any>).then(body => body.data);
  for (let start = 0; start < 105; start += 35) {
    await db.batch(Array.from({ length: Math.min(35, 105 - start) }, (_, offset) => {
      const index = start + offset;
      const id = crypto.randomUUID();
      const name = `계정 상품 ${prefix} ${String(index).padStart(3, "0")}`;
      return db.prepare(`INSERT INTO products
        (owner_id,id,category_id,name_ko,name_ko_normalized,description_ko,translation_source_hash,created_by,created_at,updated_by,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)`)
        .bind(account.id, id, category.id, name, name.toLocaleLowerCase("ko"), "설명", `hash-${id}`, "eval", stamp, "eval", stamp);
    }));
  }
  const accountProducts = await (await account.request("/products")).json() as any;
  expect(accountProducts.data).toMatchObject({ total: 105, pageCount: 100, nextCursor: expect.any(String) });
  expect(accountProducts.data.items).toHaveLength(100);
});
