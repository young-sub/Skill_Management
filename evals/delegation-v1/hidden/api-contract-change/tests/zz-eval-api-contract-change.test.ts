import { env } from "cloudflare:workers";
import { expect, it } from "vitest";
import { createTestAccount } from "./accountFixture";

it("limits translation history without changing its array contract or default", async () => {
  const account = await createTestAccount("developer");
  const now = Date.now();
  const ids = Array.from({ length: 105 }, (_, index) => `${account.id}-eval-job-${index}`);
  const rows = ids.map((id, index) => (env as Env).DB.prepare(`INSERT INTO translation_jobs
    (id, account_id, payload_json, total_credits, status, created_at, expires_at)
    VALUES (?, ?, '{}', 0, 'completed', ?, ?)`)
    .bind(id, account.id, now + index, now + 60_000));
  for (let start = 0; start < rows.length; start += 50) await (env as Env).DB.batch(rows.slice(start, start + 50));

  const read = async (query = "") => {
    const response = await account.request(`/translations/jobs${query}`);
    expect(response.status).toBe(200);
    return (await response.json() as { data: unknown }).data;
  };
  const recent = ids.slice().reverse();
  const limited = await read("?limit=3");
  expect(Array.isArray(limited)).toBe(true);
  expect((limited as Array<{ id: string }>).map(job => job.id)).toEqual(recent.slice(0, 3));

  const defaultPage = await read();
  expect(Array.isArray(defaultPage)).toBe(true);
  expect(defaultPage).toHaveLength(100);
  expect((defaultPage as Array<{ id: string }>)[0].id).toBe(recent[0]);

  for (const query of ["?limit=0", "?limit=2.5", "?limit=abc"]) {
    const fallback = await read(query);
    expect(Array.isArray(fallback)).toBe(true);
    expect(fallback).toHaveLength(100);
  }
  const capped = await read("?limit=150");
  expect(Array.isArray(capped)).toBe(true);
  expect(capped).toHaveLength(100);
});
