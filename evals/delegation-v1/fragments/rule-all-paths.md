## rule-all-paths

The prompt asks for a 300-character product-description limit without naming the save flows. The hidden suite covers create, edit, duplicate of a legacy over-limit row, bulk import, shared-catalog add, and both update and overwrite restore plans/applies. The reference implementation centralizes the limit, validates duplicate inputs, rejects invalid imports/catalog additions/restores, and reflects the limit in the two product entry forms.

Clone: `C:\Users\YS\AppData\Local\Temp\claude\eval-authoring\rule-all-paths-baseline-20261024`, detached at `984e4f646e08b75a8dfc4b9c62913670960c1659`, with `node_modules` junctioned to the source. `reference/rule-all-paths.patch` was generated from `git diff` and applied successfully to this clean clone. No source checkout was modified and no commit was made.

Commands below ran with `WRANGLER_LOG_PATH=.work\eval-wrangler.log`; the JSON commands use the same setting for the runner.

| Check | Exit | Runtime | Result |
| --- | ---: | ---: | --- |
| Starting tree, updated hidden file: `npx vitest run --configLoader runner --cache=false tests/zz-eval-rule-all-paths.test.ts` | 1 | 8.59 s | 6/6 intended failures. Create: expected status 400, received 201 (`zz-eval-rule-all-paths.test.ts:21`); legacy duplicate: expected 400, received 201 (`:40`); new import: expected `invalid`, received `create` (`:54`); existing-product import: expected `invalid`, received `update` (`:71`); catalog add promise resolved (`:89`); restore expected `canApply: false`, received `true` (`:102`). Update/overwrite applies are then blocked by the failed preview expectation. |
| Reference tree, same hidden command | 0 | 8.56 s | 6/6 passed, including import update and update/overwrite restore rejection without changing the stored product. |
| Regression: `npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/product.test.ts tests/productImportPerformance.test.ts tests/backup.test.ts tests/productCatalog.test.ts src/client/ProductForm.test.tsx src/client/ProductCatalogFinder.test.tsx` | 0 | 28.64 s Vitest duration | 6 files, 89 tests passed. |
| Probe 1 hidden check: change the create schema's `.max(MAX_PRODUCT_DESCRIPTION_LENGTH)` to `.max(500)` | 1 | 8.56 s | Exact find is 76 UTF-8 bytes and occurs once. Three hidden tests fail; primary assertion is create expected 400, received 201 (`:21`). |
| Probe 1 probe command with hidden file moved out: `npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/product.test.ts tests/productImportPerformance.test.ts tests/backup.test.ts tests/productCatalog.test.ts src/client/ProductForm.test.tsx src/client/ProductCatalogFinder.test.tsx` | 0 | 33.32 s | 6 files, 89 tests passed. |
| Probe 2 hidden check: change the restore guard condition to `if (false)` | 1 | 8.28 s | Exact find is 128 UTF-8 bytes and occurs once. Restore hidden test fails: expected `canApply: false`, received `true` (`:102`). |
| Probe 2 probe command with hidden file moved out: same six-file command above | 0 | 32.67 s | 6 files, 89 tests passed. |

The first hidden-free `--changed` attempt, with two workers and default timeouts, exceeded the target at 381.54 seconds and exited 1 under concurrent host load: 640 tests passed, 3 failed, 3 skipped, plus one worker-start error. Failures were the existing `atelier.test.ts` 5-second timeout, two `translationCredits.test.ts` fixture errors after timeouts, and an Undici `bad port` worker-start error for `CommonDesignWorkspace.test.ts`. The probe commands therefore use the same six explicit product, import, backup, catalog, and form test files as regression; each completed below 35 seconds with 89 tests passing and no hidden test installed.

Raw output: `evidence/rule-all-paths/a-start-hidden-updated.txt`, `b-reference-hidden.txt`, `b-regression.txt`, `c-probe1-hidden.txt`, `c-probe1-command-hidden-free.txt`, `c-probe2-hidden.txt`, `c-probe2-command-hidden-free.txt`, and `c-probe-command-hidden-free.txt`.

The extra `evidence/rule-all-paths/a-start-hidden.txt` is an earlier four-test baseline captured before the import-update and overwrite-restore assertions were added; the six-test final baseline is `a-start-hidden-updated.txt`.
