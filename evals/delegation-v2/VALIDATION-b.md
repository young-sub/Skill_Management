# Labeler fragment validation (owner: `b-*`)

All four scenarios were exercised in separate authoring clones checked out at Labeler ref `984e4f646e08b75a8dfc4b9c62913670960c1659`. Faults were applied only for the two scenarios that declare one. Exit codes below are the Vitest command exit codes. Durations are Vitest-reported durations from the retained logs under `evidence/<scenario-id>/`.

## Commands

Each command uses the scenario's `node_modules` junction and the required Wrangler log setting. The following are the exact hidden (`H`) and regression (`R`) commands from `scenarios-labeler-b.json`.

| ID suffix | H: hidden command | R: explicit regression command |
|---|---|---|
| sequence | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/zz-eval-b-sequence.test.ts` | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/product.test.ts tests/categorySigns.test.ts tests/categoryBackup.test.ts` |
| entitlement | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/zz-eval-b-entitlement.test.ts` | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/designs.test.ts tests/template.test.ts` |
| contract | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/zz-eval-b-contract.test.ts` | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/product.test.ts tests/catalogSearch.test.ts src/client/ProductCatalogFinder.test.tsx` |
| cross-path | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/zz-eval-b-cross-path.test.ts` | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/product.test.ts tests/productImportPerformance.test.ts src/client/ProductForm.test.tsx` |

## Results

### `b-sequence-category-branch-copy`

Reference patch: `reference/b-sequence-category-branch-copy.patch`.

| Stage | Result and evidence |
|---|---|
| (a) Pinned starting clone | H exit **1**, 1 test failed, **4.34 s**. `tests/zz-eval-b-sequence.test.ts:54` expected branch duplication to return 201 but received 404; the public action was absent. Log: `evidence/b-sequence-category-branch-copy/start-hidden.log`. |
| (b) Final reference | H exit **0**, 1 passed, **4.75 s**; R exit **0**, 30 passed, **9.94 s**; TypeScript compiler exit **0**, no diagnostics, **5.73 s**. Logs: `typefix-reference-hidden-final.log`, `typefix-reference-regression-final.log`, `compiler-final.log`. |
| (c) Probe 1: raise the copied-branch depth guard from 3 to 4 | Updated find text includes the depth calculation and guard; exact replacement occurred once. The regression run on the equivalent depth mutation before the typing correction exited **0**, 30 passed, **11.05 s**. On the final typed reference, H exits **1**, **4.56 s**, `tests/zz-eval-b-sequence.test.ts:100` expected HTTP 400 but got 201 for a fourth-level copy. Log: `probe-branch-copy-allows-a-fourth-level-final-hidden.log`; earlier probe logs are retained. |
| (c) Probe 2: duplicate only the selected category and omit its descendants | Exact replacement occurred once. R exit **0**, 30 passed, **9.45 s**; H exit **1**, **4.48 s**, `tests/zz-eval-b-sequence.test.ts:56` expected 3 copied rows but got 1. Logs: `probe-branch-copy-drops-descendants-{regression,hidden}.log`. |
| (d) First-obvious partial | Implement branch copying but omit the new operation's depth guard (Probe 1). R passes as above; H fails at line 100 as above. This demonstrates that adding the new path without carrying forward the first request's rule is discriminated. |

**Follow-up typing audit.** The pre-correction compiler run exited **2** with the anticipated `TS2352` cast diagnostics at `src/worker/categories.ts:197` and `:208`, plus `TS2339` for `depth` at line 211. During follow-up, the approved evaluation dependency copy temporarily lacked `@cloudflare/workers-types` and `@vitest/utils`; the blocked-attempt logs `compiler-after.log` and `typefix-reference-hidden.log` are retained. After the dependency copy was restored without installs, the final compiler, hidden test, and regression command all passed as recorded above. The changed depth probe was applied once, failed hidden at line 100 as expected, and the reference tree was restored; its patch matches `git diff --binary`.

### `b-entitlement-design-save-api`

The starting clone has the scenario's planted removal of the paid-save guard. Reference patch: `reference/b-entitlement-design-save-api.patch`.

| Stage | Result and evidence |
|---|---|
| (a) Pinned starting clone with fault | H exit **1**, 1 test failed, **4.62 s**. `tests/zz-eval-b-entitlement.test.ts:17` expected HTTP 403 for an unpaid direct API save but got 201. Log: `evidence/b-entitlement-design-save-api/start-hidden.log`. |
| (b) Reference | H exit **0**, 1 passed, **6.78 s**; R exit **0**, 11 passed, **6.67 s**. Logs: `reference-hidden.log`, `reference-regression.log`. |
| (c) Probe 1: allow revoked periods by dropping the `revoked_at IS NULL` condition | Exact replacement occurred once. R exit **0**, 11 passed, **8.61 s**; H exit **1**, **5.42 s**, `tests/zz-eval-b-entitlement.test.ts:44` expected HTTP 403 but got 201 for a revoked customer. Logs: `probe-revoked-period-still-grants-access-{regression,hidden}.log`. |
| (c) Probe 2: remove the operator exemption | Exact replacement occurred once. H exit **1**, **5.94 s**, `tests/zz-eval-b-entitlement.test.ts:50` expected staff save HTTP 201 but got 403. R also exits **1** because existing template lifecycle setup fails at `tests/template.test.ts:105`; this is a regression-killing probe in addition to the hidden failure. Logs: `probe-operators-lose-the-exemption-{regression,hidden}.log`. |
| (c) Probe 3: remove the save paid-check | Exact replacement occurred once. H exit **1**, **6.95 s**, line 17 expected 403 but got 201. R exits **1**; existing `tests/designs.test.ts:77` also observes the forbidden save returning 201. Logs: `probe-design-save-skips-paid-check-{regression,hidden}.log`. |
| (d) First-obvious partial | Check paid/active periods but forget suspended periods. R exit **0**, 11 passed, **6.20 s**; H exit **1**, **4.52 s**, line 44 expected HTTP 403 but got 201 for a suspended customer. Logs: `d-partial-allows-suspended-{regression,hidden}.log`. |

### `b-contract-catalog-default-page`

Reference patch: `reference/b-contract-catalog-default-page.patch`.

| Stage | Result and evidence |
|---|---|
| (a) Pinned starting clone | H exit **1**, 1 test failed, **5.26 s**. `tests/zz-eval-b-contract.test.ts:25` observed the catalog's old default of 20 instead of the requested 40 (`pageCount` was correspondingly short). Log: `evidence/b-contract-catalog-default-page/start-hidden.log`. |
| (b) Reference | H exit **0**, 1 passed, **5.44 s**; R exit **0**, 31 passed, **20.34 s**. Logs: `reference-hidden.log`, `reference-regression.log`. |
| (c) Probe 1: leave the catalog default at 20 | Exact replacement occurred once. R exit **0**, 31 passed, **21.74 s**; H exit **1**, **5.64 s**, line 25 still observes 20 rather than 40. Logs: `probe-default-remains-twenty-{regression,hidden}.log`. |
| (c) Probe 2: cap explicit page size at 49 | Exact replacement occurred once. R exit **0**, 31 passed, **22.14 s**; H exit **1**, **4.88 s**, line 47 rejects the valid explicit size 50 instead of returning that page size. Logs: `probe-explicit-fifty-limit-is-capped-at-forty-nine-{regression,hidden}.log`. |
| (d) First-obvious partial | Set the default to 40 only for unfiltered browsing, leaving search and kind-filtered catalog requests at 20. R exit **0**, 31 passed, **23.44 s**; H exit **1**, **5.14 s**, line 38 expects 40 search results per page but gets 20. Logs: `d-partial-browse-only-{regression,hidden}.log`. |

This scenario also covers the cross-module regression failure mode. A plausible broad fix changes the shared product pagination default from 100 to 40. Running the explicit existing `tests/product.test.ts` command then exits **1**: `tests/product.test.ts:79` expects the separate account-products API to retain `pageCount: 100`, but sees 40; 17 tests pass and 1 fails in **5.80 s**. Evidence: `evidence/b-contract-catalog-default-page/natural-shared-default-regression.log`. The reference changes only the catalog schema default and preserves the account-products contract.

### `b-cross-path-custom-unit-limit`

The starting clone has the scenario's planted shared-schema maximum of 40. Reference patch: `reference/b-cross-path-custom-unit-limit.patch`.

| Stage | Result and evidence |
|---|---|
| (a) Pinned starting clone with fault | H exit **1**, 1 test failed, **4.87 s**. `tests/zz-eval-b-cross-path.test.ts:23` expected a 21-character unit to return HTTP 400 but it was accepted with 201. Log: `evidence/b-cross-path-custom-unit-limit/start-hidden.log`. |
| (b) Reference | H exit **0**, 1 passed, **4.83 s**; R exit **0**, 21 passed, **20.38 s**. Logs: `reference-hidden.log`, `reference-regression.log`. |
| (c) Probe 1: allow a 21-character unit | Exact replacement occurred once. R exit **0**, 21 passed, **21.95 s**; H exit **1**, **5.72 s**, line 23 expected HTTP 400 but got 201. Logs: `probe-twenty-one-character-unit-is-accepted-{regression,hidden}.log`. |
| (c) Probe 2: collapse internal whitespace while importing | Exact replacement occurred once. R exit **0**, 21 passed, **19.06 s**; H exit **1**, **4.56 s**, line 58 expected the padded 21-character import row to be `invalid` but it was accepted as a create row. Logs: `probe-import-collapses-inner-spaces-before-counting-{regression,hidden}.log`. |
| (c) Probe 3: reject the valid 20-character boundary | Exact replacement occurred once. R reports **21 passed**, **29.25 s**; H exit **1**, **4.77 s**, line 17 expected the 20-character value to be accepted with HTTP 201. Logs: `probe-twenty-character-unit-is-rejected-{regression,hidden}.log`. |
| (d) First-obvious partial | Apply the 20-character validation to create/edit but keep the import path's internal-whitespace collapsing. R exit **0**, 21 passed, **19.06 s**; H exit **1**, **4.56 s**, line 58 observes the import bypass. This is Probe 2 and uses the same evidence. |
