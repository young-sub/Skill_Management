import { env } from "cloudflare:workers";
import { expect, it } from "vitest";
import { createRecommendedLayouts } from "../src/shared/template";
import { toDesignConfig } from "../src/shared/design";
import { createTestAccount } from "./accountFixture";

const data = async (response: Response) => (await response.json() as any).data;
const newConfig = () => toDesignConfig(createRecommendedLayouts()[0].config, 90, 50);
const save = (account: Awaited<ReturnType<typeof createTestAccount>>, name: string, config = newConfig(), base?: { id: string; version: number }) =>
  account.request("/designs", "POST", { name, config, ...(base ? { baseId: base.id, expectedVersion: base.version } : {}) });

it("enforces paid access for direct design saves while retaining reads and staff exemptions", async () => {
  const db = (env as Env).DB;
  const free = await createTestAccount("customer");
  const before = await db.prepare("SELECT count(*) AS n FROM templates WHERE owner_id=? AND design_type='label'").bind(free.id).first<number>("n");
  const denied = await save(free, "무료 저장 시도");
  expect(denied.status).toBe(403);
  expect((await denied.json() as any).error.code).toBe("paid_required");
  expect(await db.prepare("SELECT count(*) AS n FROM templates WHERE owner_id=? AND design_type='label'").bind(free.id).first<number>("n")).toBe(before);

  const paid = await createTestAccount("customer");
  const periodId = crypto.randomUUID();
  await db.prepare("INSERT INTO account_periods (id,account_id,starts_at,ends_at,source) VALUES (?,?,?,?,?)")
    .bind(periodId, paid.id, Date.now() - 1000, Date.now() + 60_000, "eval-active").run();
  const first = await save(paid, "유료 저장");
  expect(first.status).toBe(201);
  const saved = await data(first);
  expect(saved).toMatchObject({ version: 1 });
  await db.prepare("UPDATE account_periods SET ends_at=? WHERE id=?").bind(Date.now() - 1, periodId).run();
  const changedConfig = newConfig();
  changedConfig.canvas.backgroundColor = "#ddffee";
  const deniedVersion = await save(paid, "만료 후 수정", changedConfig, { id: saved.id, version: 1 });
  expect(deniedVersion.status).toBe(403);
  expect((await deniedVersion.json() as any).error.code).toBe("paid_required");
  expect(await data(await paid.request("/designs"))).toMatchObject({ labels: [expect.objectContaining({ id: saved.id, version: 1 })] });
  expect(await db.prepare("SELECT count(*) AS n FROM templates WHERE owner_id=? AND template_key=?").bind(paid.id, saved.templateKey).first<number>("n")).toBe(1);

  for (const state of ["not_started", "revoked", "suspended"] as const) {
    const customer = await createTestAccount("customer");
    const id = crypto.randomUUID();
    await db.prepare("INSERT INTO account_periods (id,account_id,starts_at,ends_at,source,revoked_at,suspended_at) VALUES (?,?,?,?,?,?,?)")
      .bind(id, customer.id, state === "not_started" ? Date.now() + 60_000 : Date.now() - 1000, Date.now() + 120_000, "eval-inactive", state === "revoked" ? Date.now() : null, state === "suspended" ? Date.now() : null).run();
    const response = await save(customer, `권한 없는 ${state}`);
    expect(response.status, state).toBe(403);
    expect((await response.json() as any).error.code, state).toBe("paid_required");
  }

  for (const role of ["developer", "operator"] as const) {
    const staff = await createTestAccount(role);
    expect((await save(staff, `${role} 저장`)).status, role).toBe(201);
  }
});
