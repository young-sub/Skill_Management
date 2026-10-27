import { expect, it } from "vitest";
import { fixtureFetch } from "./accountFixture";

const request = (path: string, init?: RequestInit) => fixtureFetch(`http://localhost${path}`, {
  ...init,
  headers: init?.body ? { "content-type": "application/json", origin: "http://localhost", ...init.headers } : init?.headers,
});
const post = (path: string, body: unknown) => request(path, { method: "POST", body: JSON.stringify(body) });
const add = async (nameKo: string, parentId?: string) => {
  const response = await post("/api/categories", { nameKo, sortOrder: 10, ...(parentId ? { parentId } : {}) });
  expect(response.status).toBe(201);
  return (await response.json() as any).data;
};
const categories = async () => (await (await request("/api/categories?includeInactive=true")).json() as any).data as any[];
const move = async (id: string, parentId: string) => {
  const response = await request(`/api/categories/${id}/move`, { method: "PATCH", body: JSON.stringify({ parentId, beforeId: null }) });
  expect(response.status).toBe(200);
};

it("rejects an update restore whose parent links would leave the tree deeper than three levels", async () => {
  const key = crypto.randomUUID();
  const top = await add(`eval-v3-top-${key}`);
  const middle = await add(`eval-v3-middle-${key}`, top.id);
  const branch = await add(`eval-v3-branch-${key}`, middle.id);
  const backup = await (await request("/api/admin/backup")).json();
  const other = await add(`eval-v3-other-${key}`);
  await move(branch.id, other.id);
  const child = await add(`eval-v3-child-${key}`, branch.id);
  expect(child.depth).toBe(3);
  const before = await categories();

  const preview = await post("/api/admin/restore/preview", { mode: "update", backup });
  expect(preview.status).toBe(200);
  expect((await preview.json() as any).data.canApply).toBe(false);
  const applied = await post("/api/admin/restore/apply", { mode: "update", backup });
  expect(applied.status).toBe(409);
  expect((await applied.json() as any).error.code).toBe("backup_conflict");

  const after = await categories();
  expect(Math.max(...after.map((item) => item.depth))).toBeLessThanOrEqual(3);
  const parents = (rows: any[]) => Object.fromEntries(rows.map((row) => [row.id, row.parentId ?? null]));
  expect(parents(after)).toEqual(parents(before));
});

it("still applies an update restore that moves a category back within three levels", async () => {
  const key = crypto.randomUUID();
  const top = await add(`eval-v3-top-${key}`);
  const middle = await add(`eval-v3-middle-${key}`, top.id);
  const branch = await add(`eval-v3-branch-${key}`, middle.id);
  const backup = await (await request("/api/admin/backup")).json();
  const other = await add(`eval-v3-other-${key}`);
  await move(branch.id, other.id);

  const applied = await post("/api/admin/restore/apply", { mode: "update", backup });
  expect(applied.status).toBe(200);
  const restored = (await categories()).find((item) => item.id === branch.id);
  expect(restored.depth).toBe(3);
  expect(Math.max(...(await categories()).map((item) => item.depth))).toBeLessThanOrEqual(3);
});
