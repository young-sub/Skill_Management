import { env } from "cloudflare:workers";
import { expect, it } from "vitest";
import { fixtureFetch } from "./accountFixture";

const request = (path: string, init?: RequestInit) => fixtureFetch(`http://localhost${path}`, {
  ...init,
  headers: init?.body ? { "content-type": "application/json", origin: "http://localhost", ...init.headers } : init?.headers,
});
const post = (path: string, body: unknown) => request(path, { method: "POST", body: JSON.stringify(body) });
const input = (nameKo: string, descriptionKo: string) => ({
  categoryId: "category-supplements", nameKo, descriptionKo,
  offers: [{ quantity: 1, unitCode: "ea", priceKrw: 1000 }],
});
// 300 typed characters; "㎎" is one character that the app's text normalization expands to "mg".
const expanding = () => {
  const text = "1정 500㎎ ".repeat(40).slice(0, 299) + "끝";
  expect(text.length).toBe(300);
  return text;
};
const storedLength = async (name: string) => (await (env as Env).DB
  .prepare("SELECT MAX(LENGTH(description_ko)) AS length FROM products WHERE name_ko = ?").bind(name).first<number>("length")) ?? 0;

it("never stores a created product description longer than 300 characters after normalization", async () => {
  const name = `eval-v3-create-${crypto.randomUUID()}`;
  const response = await post("/api/products", input(name, expanding()));
  if (response.ok) expect(await storedLength(name)).toBeLessThanOrEqual(300);
  else expect(response.status).toBe(400);
  expect(await storedLength(name)).toBeLessThanOrEqual(300);
});

it("never stores an edited product description longer than 300 characters after normalization", async () => {
  const name = `eval-v3-edit-${crypto.randomUUID()}`;
  const created = await post("/api/products", input(name, "short"));
  expect(created.status).toBe(201);
  const source = (await created.json() as any).data;
  const response = await request(`/api/products/${source.id}`, {
    method: "PATCH", body: JSON.stringify({ expectedVersion: source.version, descriptionKo: expanding() }),
  });
  if (!response.ok) {
    expect(response.status).toBe(400);
    expect(((await (await request(`/api/products/${source.id}`)).json() as any).data.descriptionKo)).toBe("short");
  }
  expect(await storedLength(name)).toBeLessThanOrEqual(300);
});
