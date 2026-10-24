import { env } from 'cloudflare:workers';
import { expect, it } from 'vitest';
import { createTestAccount } from './accountFixture';

const submit = (a: Awaited<ReturnType<typeof createTestAccount>>, requestId = crypto.randomUUID(), message = '상품 인쇄 문의') => a.request('/account-requests', 'POST', { requestId, kind: 'support', message });
const rows = async (a: Awaited<ReturnType<typeof createTestAccount>>) => (await (await a.request('/account-requests')).json() as any).data;

it('caps unresolved support at three, includes hidden and in-progress requests, and permits an idempotent retry', async () => {
  const a = await createTestAccount('customer'), b = await createTestAccount('customer');
  const requestId = crypto.randomUUID();
  const first = await (await submit(a, requestId)).json() as any;
  await submit(a); await submit(a);
  const fourth = await submit(a);
  expect(fourth.status, 'fourth unresolved support request must be rejected').toBe(409);
  expect((await fourth.json() as any).error.code).toBe('support_request_limit');
  expect((await submit(a, requestId)).status, 'retry must return its original saved request at the cap').toBe(201);
  expect(await rows(a)).toHaveLength(3);
  await (env as Env).DB.prepare("UPDATE account_requests SET status = 'in_progress', hidden_at = ? WHERE id = ?").bind(Date.now(), first.data.id).run();
  expect((await submit(a)).status, 'hiding or processing a request does not free a slot').toBe(409);
  expect((await submit(b)).status, 'limits are per account').toBe(201);
  await (env as Env).DB.prepare("UPDATE account_requests SET status = 'closed' WHERE id = ?").bind(first.data.id).run();
  expect((await submit(a)).status, 'closing a request frees a slot').toBe(201);
});

it('re-submits an owned completed support message as a fresh request, but preserves the earlier cap', async () => {
  const a = await createTestAccount('customer'), other = await createTestAccount('customer');
  const original = (await (await submit(a, crypto.randomUUID(), '예전 문의 내용')).json() as any).data;
  await (env as Env).DB.prepare("UPDATE account_requests SET status = 'closed', response = '처리 완료' WHERE id = ?").bind(original.id).run();
  const requestId = crypto.randomUUID();
  const re = await a.request(`/account-requests/${original.id}/resubmit`, 'POST', { requestId });
  expect(re.status, 'completed support can be resubmitted').toBe(201);
  const saved = (await re.json() as any).data;
  expect(saved).toMatchObject({ kind: 'support', message: '예전 문의 내용', status: 'open', response: null });
  expect(saved.id).not.toBe(original.id);
  expect(saved.revision).toBe(1);
  const retry = await a.request(`/account-requests/${original.id}/resubmit`, 'POST', { requestId });
  expect(retry.status).toBe(201);
  expect((await retry.json() as any).data.id).toBe(saved.id);
  expect((await other.request(`/account-requests/${original.id}/resubmit`, 'POST', { requestId: crypto.randomUUID() })).status, 'another member cannot copy a private inquiry').toBe(404);
  expect((await a.request(`/account-requests/${saved.id}/resubmit`, 'POST', { requestId: crypto.randomUUID() })).status, 'open support cannot be resubmitted').toBe(409);
  await submit(a); await submit(a);
  const rejected = await a.request(`/account-requests/${original.id}/resubmit`, 'POST', { requestId: crypto.randomUUID() });
  expect(rejected.status, 'resubmit must preserve the first request unresolved-support cap').toBe(409);
  expect((await rejected.json() as any).error.code).toBe('support_request_limit');
  expect((await rows(a)).filter((r: any) => r.status !== 'closed')).toHaveLength(3);
  const unchanged = (await rows(a)).find((r: any) => r.id === original.id);
  expect(unchanged).toMatchObject({ status: 'closed', response: '처리 완료', revision: 1 });
});

it('keeps the support cap atomic across simultaneous submissions', async () => {
  const a = await createTestAccount('customer');
  const results = await Promise.all(Array.from({ length: 4 }, () => submit(a)));
  expect(results.map(r => r.status).sort()).toEqual([201, 201, 201, 409]);
  expect(await rows(a)).toHaveLength(3);
});

it('keeps refunds separate from the support cap and does not resubmit refund history', async () => {
  const a = await createTestAccount('customer');
  await submit(a); await submit(a); await submit(a);
  const orderId = crypto.randomUUID();
  await (env as Env).DB.prepare(`INSERT INTO commerce_orders
    (id, account_id, request_id, kind, amount_krw, credits, policy_json, store_id, channel_key, status, created_at)
    VALUES (?, ?, ?, 'period', 10000, 50000, '{}', 'synthetic', 'synthetic', 'PAID', ?)`)
    .bind(orderId, a.id, crypto.randomUUID(), Date.now()).run();
  const refund = await a.request('/account-requests', 'POST', { requestId: crypto.randomUUID(), kind: 'refund', orderId, message: '환불 문의' });
  expect(refund.status, 'refund requests do not consume unresolved support slots').toBe(201);
  const saved = (await refund.json() as any).data;
  await (env as Env).DB.prepare("UPDATE account_requests SET status = 'closed' WHERE id = ?").bind(saved.id).run();
  expect((await a.request(`/account-requests/${saved.id}/resubmit`, 'POST', { requestId: crypto.randomUUID() })).status, 'only general support can be resubmitted').toBe(409);
});
