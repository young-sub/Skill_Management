// Project-specific acceptance: real Labeler UI/Worker/local D1, no API fixtures.
import assert from 'node:assert/strict';
import { createHash, randomUUID } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import { pathToFileURL } from 'node:url';

const base = new URL(process.env.UI_BASE_URL);
assert.equal(base.protocol, 'http:');
assert.ok(['127.0.0.1', 'localhost'].includes(base.hostname), 'Local acceptance only');
const root = await fs.realpath(process.env.LABELER_ROOT);
const database = await fs.realpath(process.env.LABELER_DATABASE);
assert.ok(database.startsWith(path.join(root, '.work') + path.sep), 'Use an isolated project database');
const output = path.resolve(process.env.UI_EVIDENCE_DIR);
await fs.mkdir(output, { recursive: true });
const reportPath = path.join(output, 'storage.json');
await fs.writeFile(reportPath, '{}', { flag: 'wx' });
const report = { status: 'RUNNING', target: { root, database, url: base.origin },
  source: {}, observations: [], errors: [], scope: 'local-product', cleanup: {},
  payload_fault: process.env.LABELER_PAYLOAD_FAULT === '1' };
await fs.writeFile(reportPath, JSON.stringify(report));
const started = Date.now();
const check = (id, actual, expected) => {
  const passed = JSON.stringify(actual) === JSON.stringify(expected);
  report.observations.push({ id, actual, expected, passed });
  assert.ok(passed, id);
};
for (const name of ['src/client/ProductForm.tsx', 'src/client/api.ts', 'src/worker/index.ts',
  'src/worker/products.ts', 'src/shared/product.ts', 'dist/pharmacy_labeler/index.js']) {
  report.source[name] = createHash('sha256').update(await fs.readFile(path.join(root, name))).digest('hex');
}
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE).href);
let browser;
const db = new DatabaseSync(database, { readOnly: true });
const prefix = 'verification-' + randomUUID();
const rows = () => db.prepare('SELECT id, name_ko, owner_id FROM products WHERE name_ko LIKE ? ORDER BY id').all(prefix + '%');
try {
  browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  page.setDefaultTimeout(30000);
  page.setDefaultNavigationTimeout(60000);
  await page.goto(base.href, { waitUntil: 'domcontentloaded' });
  const login = await page.evaluate(async () => {
    const response = await fetch('/api/auth/local-session', { method: 'POST',
      headers: { 'content-type': 'application/json' }, body: JSON.stringify({ role: 'developer' }) });
    return { status: response.status, body: await response.json() };
  });
  check('local_session', login.status, 200);
  const account = login.body.data.id;
  const categoryResponse = await context.request.post(new URL('/api/categories', base).href,
    { headers: { origin: base.origin }, data: { nameKo: prefix + '-category', sortOrder: 0 } });
  check('isolated_category', categoryResponse.status(), 201);
  const category = (await categoryResponse.json()).data.id;
  if (process.env.LABELER_PAYLOAD_FAULT === '1') {
    await page.route('**/api/products', async route => {
      if (route.request().method() !== 'POST') return route.continue();
      const body = route.request().postDataJSON();
      body.offers[0].priceKrw = -1;
      await route.continue({ postData: JSON.stringify(body) });
    });
  }
  await page.goto(base.href, { waitUntil: 'domcontentloaded' });
  await page.getByRole('button', { name: '직접 추가', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: '상품 직접 추가', exact: true });
  await dialog.getByLabel('대분류', { exact: true }).selectOption(category);
  await dialog.getByLabel('한국어 상품명').fill(prefix);
  await dialog.getByLabel('한국어 설명', { exact: true }).fill('Isolated full-stack verification');
  await dialog.getByLabel('단품 가격', { exact: true }).fill('3500');
  const [response] = await Promise.all([
    page.waitForResponse(r => new URL(r.url()).pathname === '/api/products' && r.request().method() === 'POST'),
    dialog.getByRole('button', { name: '상품 추가', exact: true }).click(),
  ]);
  report.request = response.request().postDataJSON();
  check('ui_save_status', response.status(), 201);
  const saved = (await response.json()).data;
  report.product_id = saved.id;
  check('ui_payload', [report.request.nameKo, report.request.offers[0].priceKrw], [prefix, 3500]);
  check('api_domain_result', [saved.nameKo, saved.offers[0].priceKrw], [prefix, 3500]);
  check('independent_storage', rows().map(r => [r.id, r.name_ko, r.owner_id]), [[saved.id, prefix, account]]);
  check('stored_price', db.prepare('SELECT price_krw FROM product_offers WHERE product_id = ?').get(saved.id)?.price_krw, 3500);
  const request = async (client, resource, data, extraHeaders = {}) => client.post(new URL(resource, base).href,
    { headers: { origin: base.origin, ...extraHeaders }, data });
  const zero = await request(context.request, '/api/products', { ...report.request, nameKo: prefix + '-zero',
    offers: [{ ...report.request.offers[0], priceKrw: 0 }] });
  check('zero_price_allowed', zero.status(), 201);
  const zeroId = (await zero.json()).data.id;
  check('zero_price_persisted', db.prepare('SELECT price_krw FROM product_offers WHERE product_id = ?').get(zeroId)?.price_krw, 0);
  const snapshot = rows();
  const rejected = await request(context.request, '/api/products', { ...report.request, nameKo: prefix + '-invalid',
    offers: [{ ...report.request.offers[0], priceKrw: -1 }] });
  check('direct_domain_rejection', rejected.status(), 400);
  await rejected.body();
  check('rejection_preserves_storage', rows(), snapshot);
  const mismatch = await request(context.request, '/api/products', { ...report.request, nameKo: prefix + '-mismatch' },
    { 'x-account-id': '00000000-0000-4000-8000-000000001001' });
  check('account_mismatch_denied', mismatch.status(), 409);
  await mismatch.body();
  const anonymous = await browser.newContext();
  const denied = await request(anonymous.request, '/api/products', { ...report.request, nameKo: prefix + '-anonymous' });
  check('anonymous_write_denied', denied.status(), 403);
  await denied.body();
  check('bypasses_preserve_storage', rows(), snapshot);
  const other = await browser.newContext();
  const otherLogin = await request(other.request, '/api/auth/local-session', { role: 'customer' });
  check('other_account_session', otherLogin.status(), 200);
  await otherLogin.body();
  const privateRead = await other.request.get(new URL('/api/products/' + saved.id, base).href);
  check('other_account_read_denied', privateRead.status(), 404);
  await privateRead.body();
  const fresh = await context.request.get(new URL('/api/products/' + saved.id, base).href);
  check('fresh_api_read', [(await fresh.json()).data.id, fresh.status()], [saved.id, 200]);
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.getByText(prefix, { exact: true }).first().waitFor();
  check('reload_shows_saved_product', await page.getByText(prefix, { exact: true }).first().isVisible(), true);
  await page.screenshot({ path: path.join(output, 'saved-desktop.png'), fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: path.join(output, 'saved-mobile.png'), fullPage: true });
  for (const [name, hash] of Object.entries(report.source)) {
    check('unchanged:' + name, createHash('sha256').update(await fs.readFile(path.join(root, name))).digest('hex'), hash);
  }
  report.status = 'PASS';
} catch (error) {
  report.status = 'FAIL';
  report.errors.push(error.stack ?? String(error));
  process.exitCode = 1;
} finally {
  db.close();
  if (browser) await browser.close();
  report.cleanup.browser_closed = true;
  report.elapsed_ms = Date.now() - started;
  await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ status: report.status, report: reportPath, checks: report.observations.length }));
}
