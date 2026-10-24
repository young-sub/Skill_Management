import { expect, it } from 'vitest';
import { createTestAccount } from './accountFixture';

it('saves a private trimmed work memo, reads it afresh, clears it and isolates accounts', async () => {
  const a = await createTestAccount('customer'), b = await createTestAccount('customer');
  const reply = await a.request('/auth/profile', 'PATCH', { workMemo: '  다음 달 포장 변경  ' });
  expect(reply.status, 'work memo must be accepted for a free customer').toBe(200);
  expect((await reply.json() as any).data.workMemo).toBe('다음 달 포장 변경');
  const fresh = await a.request('/me');
  expect((await fresh.json() as any).data.workMemo).toBe('다음 달 포장 변경');
  const other = await b.request('/me');
  expect((await other.json() as any).data.workMemo ?? null).toBeNull();
  const cleared = await a.request('/auth/profile', 'PATCH', { workMemo: '   ' });
  expect(cleared.status).toBe(200);
  expect((await (await a.request('/me')).json() as any).data.workMemo).toBeNull();
});

it('rejects overlong memos without overwriting the previously saved organization or memo', async () => {
  const a = await createTestAccount('customer');
  expect((await a.request('/auth/profile', 'PATCH', { organization: '기존 약국', workMemo: '이전 메모' })).status).toBe(200);
  expect((await a.request('/auth/profile', 'PATCH', { organization: '덮어쓰기 금지', workMemo: '가'.repeat(201) })).status,
    '201 characters must reject the entire profile edit').toBe(400);
  expect((await (await a.request('/me')).json() as any).data).toMatchObject({ organization: '기존 약국', workMemo: '이전 메모' });
  expect((await a.request('/auth/profile', 'PATCH', { workMemo: '가'.repeat(200) })).status).toBe(200);
  expect((await a.request('/auth/profile', 'PATCH', { contact: '010' })).status).toBe(200);
  expect((await (await a.request('/me')).json() as any).data.workMemo).toBe('가'.repeat(200));
});
