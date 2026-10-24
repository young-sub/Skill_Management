# Labeler v2 validation — a-* scenarios

All four scenarios were validated in separate fresh clones checked out at Labeler commit 984e4f646e08b75a8dfc4b9c62913670960c1659. Each clone used the required junction to the evaluation-only dependency copy. The whitespace complaint used its declared planted fault; the other three began at the pristine pinned tree. No source checkout was edited, and no dependency install or commit was performed.

The configured regression commands use explicit files, maxWorkers=2, and the required Wrangler log setting. Hidden tests were run separately on each mutated reference tree to prove the probe kills. The evaluator runs probe commands before copying hidden files, so a regression exit of 0 for a probe does not replace the separate hidden-kill evidence below.

## Commands

| ID | Hidden command | Explicit regression command |
| --- | --- | --- |
| a-offer-quantity-all-paths | set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/zz-eval-a-offer-quantity-all-paths.test.ts | set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/product.test.ts tests/productImportPerformance.test.ts tests/backup.test.ts tests/productCatalog.test.ts src/client/ProductForm.test.tsx |
| a-product-source-stale-all-paths | set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/zz-eval-a-source-stale.test.ts | set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/product.test.ts tests/productImportPerformance.test.ts tests/backup.test.ts |
| a-product-name-whitespace-complaint | set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/zz-eval-a-name-whitespace.test.ts | set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/product.test.ts tests/productImportPerformance.test.ts src/client/ProductForm.test.tsx |
| a-import-offer-sequence | set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/zz-eval-a-import-offer-sequence.test.ts | set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/product.test.ts tests/productImportPerformance.test.ts src/client/ProductForm.test.tsx |

## a-offer-quantity-all-paths

Reference patch: reference/a-offer-quantity-all-paths.patch.

| Stage | Result |
| --- | --- |
| (a) Pinned starting tree | Hidden exit 1, 2/5 passed, 5.15 s. Restore preview allowed an invalid quantity, 11-option list, and empty offer list: zz-eval-a-offer-quantity-all-paths.test.ts:118, :135, :149 expected canApply false but got true. Regression exit 0, 90/90 passed, 17.14 s. Logs: evidence/a-offer-quantity-all-paths/a-pristine-start-hidden.log and a-pristine-start-regression.log. |
| (b) Reference | Hidden exit 0, 5/5 passed, 5.62 s. Regression exit 0, 90/90 passed, 17.02 s. Logs: b-final-reference-hidden.log and b-final-reference-regression.log. |
| (c1) Raise the shared quantity maximum from 999 to 1000 | Exact replacement occurs once. Hidden exit 1, 3/5 passed, 5.41 s: line 41 got HTTP 500 instead of 400 for quantity 1000, and line 118 allowed invalid restore. Regression exit 0, 90/90 passed, 16.85 s. Logs: c-probe1-hidden-kill-final.log and c-probe1-regression-final.log. |
| (c2) Skip restore offer validation | Exact replacement occurs once. Hidden exit 1, 2/5 passed, 5.24 s: lines 118, 135, and 149 allowed invalid restores. Regression exit 0, 90/90 passed, 16.41 s. Logs: c-probe2-hidden-kill-final.log and c-probe2-regression-final.log. |
| (c3) Allow mixed units within one product | Exact replacement occurs once. Hidden exit 1, 4/5 passed, 5.58 s: line 49 accepted a mixed-unit edit with HTTP 200 instead of 400. Regression exit 1, 89/90 passed, 16.51 s: existing unit-consistency assertion failed at product.test.ts:352. Logs: c-probe3-hidden-kill-final.log and c-probe3-regression-final.log. |
| (d) First-obvious partial | Validate only each restored offer quantity. Regression exit 0, 90/90 passed, 16.30 s. Hidden exit 1, 3/5 passed, 5.27 s: the 11-option and zero-option restore cases passed preview when they should have been rejected, at lines 135 and 149. Partial patch: evidence/a-offer-quantity-all-paths/d-quantity-only.patch; logs: d-final-partial-regression.log and d-final-partial-hidden.log. |

## a-product-source-stale-all-paths

Reference patch: reference/a-product-source-stale-all-paths.patch.

| Stage | Result |
| --- | --- |
| (a) Pinned starting tree | Hidden exit 1, 3/5 passed, 7.57 s. Restore changed the name and description but left product status as 번역 완료 instead of 원문 변경 at zz-eval-a-source-stale.test.ts:70 and :82. Regression exit 0, 62/62 passed, 13.32 s. Logs: evidence/a-product-source-stale-all-paths/a-start-hidden.log and a-start-regression.log. |
| (b) Reference | Hidden exit 0, 5/5 passed, 5.57 s. Regression exit 0, 62/62 passed, 12.96 s. Logs: b-reference-hidden.log and b-reference-regression.log. |
| (c1) Keep the prior source hash on direct edit | Exact replacement occurs once. Hidden exit 1, 3/5 passed, 5.53 s: direct edit and workbook update remained complete at lines 43 and 56. Regression exit 0, 62/62 passed, 12.11 s. Logs: c-probe1-hidden.log and c-probe1-regression.log. |
| (c2) Keep the prior source hash on restore | Exact replacement occurs once. Hidden exit 1, 3/5 passed, 5.26 s: restore name and description remained complete at lines 70 and 82. Regression exit 0, 62/62 passed, 10.32 s. Logs: c-probe2-final-hidden.log and c-probe2-final-regression.log. |
| (d) First-obvious partial | Recompute the restore hash only when the product name changes. Regression exit 0, 62/62 passed, 11.25 s. Hidden exit 1, 4/5 passed, 5.35 s: description-only restore stayed complete at line 82. Partial patch: evidence/a-product-source-stale-all-paths/d-name-only-partial.patch; logs: d-name-only-partial-regression.log and d-name-only-partial-hidden.log. |

## a-product-name-whitespace-complaint

Fault: shared name normalization removed all internal whitespace. Reference patch: reference/a-product-name-whitespace-complaint.patch.

| Stage | Result |
| --- | --- |
| (a) Pinned starting tree with fault | Hidden exit 1, 1/4 passed, 4.83 s: registration, direct edit, and workbook update lost word separators at zz-eval-a-name-whitespace.test.ts:30, :39, and :49. Regression exit 1, 22/24 passed, 10.11 s: existing normalization assertions failed at product.test.ts:34 and :179. Logs: evidence/a-product-name-whitespace-complaint/a-start-hidden.log and a-start-regression.log. |
| (b) Reference | Hidden exit 0, 4/4 passed, 4.65 s. Regression exit 0, 24/24 passed, 9.48 s. Logs: b-reference-hidden.log and b-reference-regression.log. |
| (c1) Remove all internal whitespace | Exact replacement occurs once. Hidden exit 1, 1/4 passed, 4.56 s: lines 30, 39, and 49 lost separators. Regression exit 1, 22/24 passed, 9.92 s: product.test.ts:34 and :179 failed. Logs: c-probe1-hidden.log and c-probe1-regression.log. |
| (c2) Collapse ordinary spaces but leave tabs and line breaks | Exact replacement occurs once. Hidden exit 1, 2/4 passed, 4.72 s: lines 39 and 49 retained tabs and line breaks. Regression exit 1, 23/24 passed, 9.35 s: product.test.ts:34 failed. Logs: c-probe2-hidden.log and c-probe2-regression.log. |
| (d) First-obvious partial | Collapse ordinary spaces and line breaks but leave tabs. Regression exit 0, 24/24 passed, 10.03 s. Hidden exit 1, 2/4 passed, 4.78 s: direct edit and import retained tabs at lines 39 and 49. Partial patch: evidence/a-product-name-whitespace-complaint/d-partial.patch; logs: d-partial-regression.log and d-partial-hidden.log. |

## a-import-offer-sequence

Reference patch: reference/a-import-offer-sequence.patch.

| Stage | Result |
| --- | --- |
| (a) Pinned starting tree | Hidden exit 1, 1/2 passed, 4.86 s: workbook update expected two updated rows and one invalid row but got one updated and two invalid at zz-eval-a-import-offer-sequence.test.ts:70. Regression exit 0, 24/24 passed, 10.05 s. Logs: evidence/a-import-offer-sequence/a-start-hidden.log and a-start-regression.log. |
| (b) Reference | Hidden exit 0, 2/2 passed, 4.69 s. Regression exit 0, 24/24 passed, 9.05 s. Logs: b-reference-hidden.log and b-reference-regression.log. |
| (c1) Delete offer lists from every workbook update | Exact replacement occurs once. Hidden exit 1, 1/2 passed, 4.65 s: the filled three-tier replacement kept the previous two tiers at line 76. Regression exit 1, 20/21 passed, 18.42 s: the existing legacy-workbook contract failed at product.test.ts:563. Logs: c-probe1-hidden.log and c-probe1-regression.log. |
| (c2) Require an offer list on every direct edit | Exact replacement occurs once. Hidden exit 1, 0/2 passed, 4.36 s: an edit omitting options returned 400 instead of 200 at lines 34 and 68. Regression exit 1, 18/21 passed, 18.70 s: existing product flows failed at product.test.ts:136, :165, and :486. Logs: c-probe2-hidden.log and c-probe2-regression.log. |
| (d) First-obvious partial | Preserve blank workbook options only for a product that already has one option. Regression exit 0, 21/21 passed, 18.79 s. Hidden exit 1, 1/2 passed, 4.68 s: the three-option blank section was treated as invalid at line 70. Partial patch: evidence/a-import-offer-sequence/d-partial.patch; logs: d-partial-regression.log and d-partial-hidden.log. |

An early sequence probe attempt stopped before assertions because the shared evaluation dependency copy lacked packages. That attempt is retained in evidence/a-import-offer-sequence but excluded from the results. After the dependency copy was repaired without installing or overwriting packages, the final c and d runs above completed with behavioral assertions.
