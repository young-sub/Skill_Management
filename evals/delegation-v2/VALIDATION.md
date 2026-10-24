# Delegation v2 validation

Authoring controls only: no candidate-agent session, dependency installation, or commit was performed. Eleven new scenarios plus the unchanged v1 anchor were exercised in isolated local clones.

Labeler pin: 984e4f646e08b75a8dfc4b9c62913670960c1659. Yeondoo Link pin: d17f0c2322056a4d804c911b83d6cc1b1738a083. Original source HEAD/status/tracked-diff snapshots are retained in evidence/source-before.json and source-after.json. Skill_Management started on wp-20261024-lean-delegation at ef4bc9e95b80df6e588212774b179f0f9d50e594 with an unrelated dirty uthoring/skills/agent-workflow/SKILL.md; concurrent changes were outside this assignment. All repository writes for this task stayed under this suite.

## Control summary

(a) = intended starting hidden assertion failure; (b) = reference hidden/regression exits; (c) = exact reference mutations killed by hidden checks; (d) = incomplete implementation regression/hidden exits. Exit 1 in (a), (c), and the second half of (d) is the required result, not an invalid scenario.

| ID | Project | (a) | (b) H/R | (c) killed | (d) R/H |
| --- | --- | --- | --- | --- | --- |
| a-offer-quantity-all-paths | labeler | 1 | 0 / 0 | 3/3 | 0 / 1 |
| a-product-source-stale-all-paths | labeler | 1 | 0 / 0 | 2/2 | 0 / 1 |
| a-product-name-whitespace-complaint | labeler | 1 | 0 / 0 | 2/2 | 0 / 1 |
| a-import-offer-sequence | labeler | 1 | 0 / 0 | 2/2 | 0 / 1 |
| a-update-offer-list-complaint | labeler | 1 | 0 / 0 | 2/2 | 0 / 1 |
| b-sequence-category-branch-copy | labeler | 1 | 0 / 0 | 2/2 | 0 / 1 |
| b-entitlement-design-save-api | labeler | 1 | 0 / 0 | 3/3 | 0 / 1 |
| b-contract-catalog-default-page | labeler | 1 | 0 / 0 | 2/2 | 0 / 1 |
| b-cross-path-custom-unit-limit | labeler | 1 | 0 / 0 | 3/3 | 0 / 1 |
| cart-item-to-compare | yeondoo-link | 1 | 0 / 0 | 3/3 | 0 / 1 |
| medicine-catalog-classification-bypass | yeondoo-link | 1 | 0 / 0 | 2/2 | 0 / 1 |
| rule-all-paths | labeler | 1 | 0 / 0 | 2/2 | 0 / 1 |

All 12 have the required a-d authoring controls. Actual candidate success, strong-agent discrimination, duration and cost remain unmeasured. The incomplete implementations below establish a deliberate regression-passing gap; they are not samples of candidate-agent behavior.

## Host, evidence and interpretation

- Clones use git clone --local with --no-hardlinks fallback and explicit detached pins. Command-local Git ownership exceptions were used for the known source roots and their .git directories; no global configuration changed.
- Every dependency junction targets its matching evaluation copy. No npm install/ci/update was run. During authoring the Labeler dependency copy unexpectedly lost packages. Matching .package-lock.json SHA-256 hashes and remaining package versions were checked; missing files were copied from the read-only original with robocopy /XC /XN /XO /XJ, preserving every existing destination file. Robocopy exit 1 means successful file copies: 16,868 files (190.79 MiB), zero failures. See evidence/dependency-incident.json, dependency-restore.json, and dependency-restore.log. The writer/cause is unknown; host process inspection was denied. Environment failures from the outage do not count as behavioral kills.
- Labeler commands use the requested Wrangler log destination, runner config loader, cache disabled and explicit existing regression files. Individual hidden assertions execute well below five seconds; suite timings include startup. Yeondoo uses explicit native Node test files and needs no Vite host workaround or Skill_Management dependency.
- Timings in the b-* and a-* fragments are native Vitest durations where stated; root and Yeondoo tables use command wall time. Do not compare them as candidate performance measurements. Raw outputs remain alongside the reports.
- The branch-copy reference had TypeScript-only errors despite passing transpiled tests. These were repaired and its final compiler, hidden and regression checks passed. The earlier type errors and dependency-related interruptions remain documented.
- Byte-oriented fault/probe contexts use Windows checkout line endings where multiline. An initial integration audit caught an LF-only root fault context before it matched a fresh CRLF checkout; that transport issue was corrected without changing canonical source logic. Multiline Yeondoo contexts were aligned with the same checkout convention. The fresh-reference audit checks actual unique byte matches.
- Hidden checks execute product/API/domain behavior and fresh reads where appropriate; the Yeondoo FE oracle exercises its existing transition interface. The reference includes a cart-row UI control and passes TypeScript, but browser interaction is unverified.
- Configured probes execute before hidden installation. A passing configured probe regression is explicitly distinguished from a hidden mutation kill. Exact-text probes may be inapplicable to a differently structured correct candidate implementation.
- No product Feature Map edit was made: impact is delegated-work evaluation assets, and the user authorized repository writes only under evals/delegation-v2/.

## Detailed executed controls

## Labeler v2 validation — a-* scenarios

All four scenarios were validated in separate fresh clones checked out at Labeler commit 984e4f646e08b75a8dfc4b9c62913670960c1659. Each clone used the required junction to the evaluation-only dependency copy. The whitespace complaint used its declared planted fault; the other three began at the pristine pinned tree. No source checkout was edited, and no dependency install or commit was performed.

The configured regression commands use explicit files, maxWorkers=2, and the required Wrangler log setting. Hidden tests were run separately on each mutated reference tree to prove the probe kills. The evaluator runs probe commands before copying hidden files, so a regression exit of 0 for a probe does not replace the separate hidden-kill evidence below.

### Commands

| ID | Hidden command | Explicit regression command |
| --- | --- | --- |
| a-offer-quantity-all-paths | set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/zz-eval-a-offer-quantity-all-paths.test.ts | set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/product.test.ts tests/productImportPerformance.test.ts tests/backup.test.ts tests/productCatalog.test.ts src/client/ProductForm.test.tsx |
| a-product-source-stale-all-paths | set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/zz-eval-a-source-stale.test.ts | set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/product.test.ts tests/productImportPerformance.test.ts tests/backup.test.ts |
| a-product-name-whitespace-complaint | set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/zz-eval-a-name-whitespace.test.ts | set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/product.test.ts tests/productImportPerformance.test.ts src/client/ProductForm.test.tsx |
| a-import-offer-sequence | set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/zz-eval-a-import-offer-sequence.test.ts | set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/product.test.ts tests/productImportPerformance.test.ts src/client/ProductForm.test.tsx |

### a-offer-quantity-all-paths

Reference patch: reference/a-offer-quantity-all-paths.patch.

| Stage | Result |
| --- | --- |
| (a) Pinned starting tree | Hidden exit 1, 2/5 passed, 5.15 s. Restore preview allowed an invalid quantity, 11-option list, and empty offer list: zz-eval-a-offer-quantity-all-paths.test.ts:118, :135, :149 expected canApply false but got true. Regression exit 0, 90/90 passed, 17.14 s. Logs: evidence/a-offer-quantity-all-paths/a-pristine-start-hidden.log and a-pristine-start-regression.log. |
| (b) Reference | Hidden exit 0, 5/5 passed, 5.62 s. Regression exit 0, 90/90 passed, 17.02 s. Logs: b-final-reference-hidden.log and b-final-reference-regression.log. |
| (c1) Raise the shared quantity maximum from 999 to 1000 | Exact replacement occurs once. Hidden exit 1, 3/5 passed, 5.41 s: line 41 got HTTP 500 instead of 400 for quantity 1000, and line 118 allowed invalid restore. Regression exit 0, 90/90 passed, 16.85 s. Logs: c-probe1-hidden-kill-final.log and c-probe1-regression-final.log. |
| (c2) Skip restore offer validation | Exact replacement occurs once. Hidden exit 1, 2/5 passed, 5.24 s: lines 118, 135, and 149 allowed invalid restores. Regression exit 0, 90/90 passed, 16.41 s. Logs: c-probe2-hidden-kill-final.log and c-probe2-regression-final.log. |
| (c3) Allow mixed units within one product | Exact replacement occurs once. Hidden exit 1, 4/5 passed, 5.58 s: line 49 accepted a mixed-unit edit with HTTP 200 instead of 400. Regression exit 1, 89/90 passed, 16.51 s: existing unit-consistency assertion failed at product.test.ts:352. Logs: c-probe3-hidden-kill-final.log and c-probe3-regression-final.log. |
| (d) First-obvious partial | Validate only each restored offer quantity. Regression exit 0, 90/90 passed, 16.30 s. Hidden exit 1, 3/5 passed, 5.27 s: the 11-option and zero-option restore cases passed preview when they should have been rejected, at lines 135 and 149. Partial patch: evidence/a-offer-quantity-all-paths/d-quantity-only.patch; logs: d-final-partial-regression.log and d-final-partial-hidden.log. |

### a-product-source-stale-all-paths

Reference patch: reference/a-product-source-stale-all-paths.patch.

| Stage | Result |
| --- | --- |
| (a) Pinned starting tree | Hidden exit 1, 3/5 passed, 7.57 s. Restore changed the name and description but left product status as 번역 완료 instead of 원문 변경 at zz-eval-a-source-stale.test.ts:70 and :82. Regression exit 0, 62/62 passed, 13.32 s. Logs: evidence/a-product-source-stale-all-paths/a-start-hidden.log and a-start-regression.log. |
| (b) Reference | Hidden exit 0, 5/5 passed, 5.57 s. Regression exit 0, 62/62 passed, 12.96 s. Logs: b-reference-hidden.log and b-reference-regression.log. |
| (c1) Keep the prior source hash on direct edit | Exact replacement occurs once. Hidden exit 1, 3/5 passed, 5.53 s: direct edit and workbook update remained complete at lines 43 and 56. Regression exit 0, 62/62 passed, 12.11 s. Logs: c-probe1-hidden.log and c-probe1-regression.log. |
| (c2) Keep the prior source hash on restore | Exact replacement occurs once. Hidden exit 1, 3/5 passed, 5.26 s: restore name and description remained complete at lines 70 and 82. Regression exit 0, 62/62 passed, 10.32 s. Logs: c-probe2-final-hidden.log and c-probe2-final-regression.log. |
| (d) First-obvious partial | Recompute the restore hash only when the product name changes. Regression exit 0, 62/62 passed, 11.25 s. Hidden exit 1, 4/5 passed, 5.35 s: description-only restore stayed complete at line 82. Partial patch: evidence/a-product-source-stale-all-paths/d-name-only-partial.patch; logs: d-name-only-partial-regression.log and d-name-only-partial-hidden.log. |

### a-product-name-whitespace-complaint

Fault: shared name normalization removed all internal whitespace. Reference patch: reference/a-product-name-whitespace-complaint.patch.

| Stage | Result |
| --- | --- |
| (a) Pinned starting tree with fault | Hidden exit 1, 1/4 passed, 4.83 s: registration, direct edit, and workbook update lost word separators at zz-eval-a-name-whitespace.test.ts:30, :39, and :49. Regression exit 1, 22/24 passed, 10.11 s: existing normalization assertions failed at product.test.ts:34 and :179. Logs: evidence/a-product-name-whitespace-complaint/a-start-hidden.log and a-start-regression.log. |
| (b) Reference | Hidden exit 0, 4/4 passed, 4.65 s. Regression exit 0, 24/24 passed, 9.48 s. Logs: b-reference-hidden.log and b-reference-regression.log. |
| (c1) Remove all internal whitespace | Exact replacement occurs once. Hidden exit 1, 1/4 passed, 4.56 s: lines 30, 39, and 49 lost separators. Regression exit 1, 22/24 passed, 9.92 s: product.test.ts:34 and :179 failed. Logs: c-probe1-hidden.log and c-probe1-regression.log. |
| (c2) Collapse ordinary spaces but leave tabs and line breaks | Exact replacement occurs once. Hidden exit 1, 2/4 passed, 4.72 s: lines 39 and 49 retained tabs and line breaks. Regression exit 1, 23/24 passed, 9.35 s: product.test.ts:34 failed. Logs: c-probe2-hidden.log and c-probe2-regression.log. |
| (d) First-obvious partial | Collapse ordinary spaces and line breaks but leave tabs. Regression exit 0, 24/24 passed, 10.03 s. Hidden exit 1, 2/4 passed, 4.78 s: direct edit and import retained tabs at lines 39 and 49. Partial patch: evidence/a-product-name-whitespace-complaint/d-partial.patch; logs: d-partial-regression.log and d-partial-hidden.log. |

### a-import-offer-sequence

Reference patch: reference/a-import-offer-sequence.patch.

| Stage | Result |
| --- | --- |
| (a) Pinned starting tree | Hidden exit 1, 1/2 passed, 4.86 s: workbook update expected two updated rows and one invalid row but got one updated and two invalid at zz-eval-a-import-offer-sequence.test.ts:70. Regression exit 0, 24/24 passed, 10.05 s. Logs: evidence/a-import-offer-sequence/a-start-hidden.log and a-start-regression.log. |
| (b) Reference | Hidden exit 0, 2/2 passed, 4.69 s. Regression exit 0, 24/24 passed, 9.05 s. Logs: b-reference-hidden.log and b-reference-regression.log. |
| (c1) Delete offer lists from every workbook update | Exact replacement occurs once. Hidden exit 1, 1/2 passed, 4.65 s: the filled three-tier replacement kept the previous two tiers at line 76. Regression exit 1, 20/21 passed, 18.42 s: the existing legacy-workbook contract failed at product.test.ts:563. Logs: c-probe1-hidden.log and c-probe1-regression.log. |
| (c2) Require an offer list on every direct edit | Exact replacement occurs once. Hidden exit 1, 0/2 passed, 4.36 s: an edit omitting options returned 400 instead of 200 at lines 34 and 68. Regression exit 1, 18/21 passed, 18.70 s: existing product flows failed at product.test.ts:136, :165, and :486. Logs: c-probe2-hidden.log and c-probe2-regression.log. |
| (d) First-obvious partial | Preserve blank workbook options only for a product that already has one option. Regression exit 0, 21/21 passed, 18.79 s. Hidden exit 1, 1/2 passed, 4.68 s: the three-option blank section was treated as invalid at line 70. Partial patch: evidence/a-import-offer-sequence/d-partial.patch; logs: d-partial-regression.log and d-partial-hidden.log. |

An early sequence probe attempt stopped before assertions because the shared evaluation dependency copy lacked packages. That attempt is retained in evidence/a-import-offer-sequence but excluded from the results. After the dependency copy was repaired without installing or overwriting packages, the final c and d runs above completed with behavioral assertions.

## Offer-list complaint validation

### `a-update-offer-list-complaint`

Feature: delegated-work evaluation assets. Fresh clone `root-offer-complaint` at Labeler `984e4f646e08b75a8dfc4b9c62913670960c1659`, with the required evaluation dependency junction.

The synthetic fault independently caps standalone updates and cached batch updates at three offer rows. The reference removes both caps; its resulting product source is byte-identical to the pinned original. No commit or dependency installation was performed.

Hidden command H: `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/zz-eval-offer-list-complaint.test.ts`

Explicit regression command R: `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/product.test.ts tests/productImportPerformance.test.ts src/client/ProductForm.test.tsx`

| Stage | Command | Exit codes by attempt | Seconds by attempt |
| --- | --- | --- | --- |
| a-start-hidden | H | 1, 1 | 12.141, 11.453 |
| a-start-regression | R | 1, 1 | 26.219, 27.875 |
| b-reference-regression | R | 0 | 23.781 |
| b-reference-hidden | H | 0 | 9.062 |
| c-probe1-hidden | H | 1, 1 | 9.032, 9.359 |
| c-probe2-hidden | H | 1, 1 | 10.406, 9.532 |
| d-partial-regression | R | 0 | 25.39 |
| d-partial-hidden | H | 1, 1 | 9.063, 8.875 |

Nonzero commands were repeated once, matching the judging retry rule. Both failures were assertion failures, rather than runtime/setup failures. The starting regression also fails: the reported standalone four-tier case is already covered; the sibling cached batch case is not.

Failing assertion evidence (the complete outputs and all attempts are in `evidence/a-update-offer-list-complaint/final/results.json`):

- a-start-hidden: `evidence/a-update-offer-list-complaint/final/a-start-hidden-retry.log:17` — AssertionError: expected [ { quantity: 10, …(2) }, …(2) ] to deeply equal [ { quantity: 10, …(2) }, …(3) ]
- a-start-hidden: `evidence/a-update-offer-list-complaint/final/a-start-hidden-retry.log:46` — AssertionError: expected [ { quantity: 10, …(2) }, …(2) ] to deeply equal [ { quantity: 10, …(2) }, …(4) ]
- a-start-regression: `evidence/a-update-offer-list-complaint/final/a-start-regression-retry.log:16` — AssertionError: expected [ { …(5) }, { …(5) }, { …(5) } ] to match object [ { quantity: 10, …(2) }, …(3) ]
- c-probe1-hidden: `evidence/a-update-offer-list-complaint/final/c-probe1-hidden-retry.log:16` — AssertionError: expected [ { quantity: 10, …(2) }, …(2) ] to deeply equal [ { quantity: 10, …(2) }, …(3) ]
- c-probe2-hidden: `evidence/a-update-offer-list-complaint/final/c-probe2-hidden-retry.log:16` — AssertionError: expected [ { quantity: 10, …(2) }, …(2) ] to deeply equal [ { quantity: 10, …(2) }, …(4) ]
- d-partial-hidden: `evidence/a-update-offer-list-complaint/final/d-partial-hidden-retry.log:16` — AssertionError: expected [ { quantity: 10, …(2) }, …(2) ] to deeply equal [ { quantity: 10, …(2) }, …(4) ]

Both probes match exactly once on the reference tree. Probe 1 restores only the standalone cap and kills the direct-edit hidden case; probe 2 restores only the cached-batch cap and kills the spreadsheet hidden case.

The first-obvious partial removes the reported standalone cap while leaving the independent cached batch cap. Its exact fault-relative diff is `evidence/a-update-offer-list-complaint/final/partial.patch`. Direct hidden cases pass, the five-tier spreadsheet fresh read returns only three tiers, and the same full explicit regression command passes. This is the required discriminating control.

Earlier shared-clamp prototype logs under `evidence/a-update-offer-list-complaint/` are superseded; only the `final/` records describe the shipped fault and probes.

## Labeler fragment validation (owner: `b-*`)

All four scenarios were exercised in separate authoring clones checked out at Labeler ref `984e4f646e08b75a8dfc4b9c62913670960c1659`. Faults were applied only for the two scenarios that declare one. Exit codes below are the Vitest command exit codes. Durations are Vitest-reported durations from the retained logs under `evidence/<scenario-id>/`.

### Commands

Each command uses the scenario's `node_modules` junction and the required Wrangler log setting. The following are the exact hidden (`H`) and regression (`R`) commands from `scenarios-labeler-b.json`.

| ID suffix | H: hidden command | R: explicit regression command |
|---|---|---|
| sequence | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/zz-eval-b-sequence.test.ts` | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/product.test.ts tests/categorySigns.test.ts tests/categoryBackup.test.ts` |
| entitlement | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/zz-eval-b-entitlement.test.ts` | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/designs.test.ts tests/template.test.ts` |
| contract | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/zz-eval-b-contract.test.ts` | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/product.test.ts tests/catalogSearch.test.ts src/client/ProductCatalogFinder.test.tsx` |
| cross-path | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/zz-eval-b-cross-path.test.ts` | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/product.test.ts tests/productImportPerformance.test.ts src/client/ProductForm.test.tsx` |

### Results

#### `b-sequence-category-branch-copy`

Reference patch: `reference/b-sequence-category-branch-copy.patch`.

| Stage | Result and evidence |
|---|---|
| (a) Pinned starting clone | H exit **1**, 1 test failed, **4.34 s**. `tests/zz-eval-b-sequence.test.ts:54` expected branch duplication to return 201 but received 404; the public action was absent. Log: `evidence/b-sequence-category-branch-copy/start-hidden.log`. |
| (b) Final reference | H exit **0**, 1 passed, **4.75 s**; R exit **0**, 30 passed, **9.94 s**; TypeScript compiler exit **0**, no diagnostics, **5.73 s**. Logs: `typefix-reference-hidden-final.log`, `typefix-reference-regression-final.log`, `compiler-final.log`. |
| (c) Probe 1: raise the copied-branch depth guard from 3 to 4 | Updated find text includes the depth calculation and guard; exact replacement occurred once. The regression run on the equivalent depth mutation before the typing correction exited **0**, 30 passed, **11.05 s**. On the final typed reference, H exits **1**, **4.56 s**, `tests/zz-eval-b-sequence.test.ts:100` expected HTTP 400 but got 201 for a fourth-level copy. Log: `probe-branch-copy-allows-a-fourth-level-final-hidden.log`; earlier probe logs are retained. |
| (c) Probe 2: duplicate only the selected category and omit its descendants | Exact replacement occurred once. R exit **0**, 30 passed, **9.45 s**; H exit **1**, **4.48 s**, `tests/zz-eval-b-sequence.test.ts:56` expected 3 copied rows but got 1. Logs: `probe-branch-copy-drops-descendants-{regression,hidden}.log`. |
| (d) First-obvious partial | Implement branch copying but omit the new operation's depth guard (Probe 1). R passes as above; H fails at line 100 as above. This demonstrates that adding the new path without carrying forward the first request's rule is discriminated. |

**Follow-up typing audit.** The pre-correction compiler run exited **2** with the anticipated `TS2352` cast diagnostics at `src/worker/categories.ts:197` and `:208`, plus `TS2339` for `depth` at line 211. During follow-up, the approved evaluation dependency copy temporarily lacked `@cloudflare/workers-types` and `@vitest/utils`; the blocked-attempt logs `compiler-after.log` and `typefix-reference-hidden.log` are retained. After the dependency copy was restored without installs, the final compiler, hidden test, and regression command all passed as recorded above. The changed depth probe was applied once, failed hidden at line 100 as expected, and the reference tree was restored; its patch matches `git diff --binary`.

#### `b-entitlement-design-save-api`

The starting clone has the scenario's planted removal of the paid-save guard. Reference patch: `reference/b-entitlement-design-save-api.patch`.

| Stage | Result and evidence |
|---|---|
| (a) Pinned starting clone with fault | H exit **1**, 1 test failed, **4.62 s**. `tests/zz-eval-b-entitlement.test.ts:17` expected HTTP 403 for an unpaid direct API save but got 201. Log: `evidence/b-entitlement-design-save-api/start-hidden.log`. |
| (b) Reference | H exit **0**, 1 passed, **6.78 s**; R exit **0**, 11 passed, **6.67 s**. Logs: `reference-hidden.log`, `reference-regression.log`. |
| (c) Probe 1: allow revoked periods by dropping the `revoked_at IS NULL` condition | Exact replacement occurred once. R exit **0**, 11 passed, **8.61 s**; H exit **1**, **5.42 s**, `tests/zz-eval-b-entitlement.test.ts:44` expected HTTP 403 but got 201 for a revoked customer. Logs: `probe-revoked-period-still-grants-access-{regression,hidden}.log`. |
| (c) Probe 2: remove the operator exemption | Exact replacement occurred once. H exit **1**, **5.94 s**, `tests/zz-eval-b-entitlement.test.ts:50` expected staff save HTTP 201 but got 403. R also exits **1** because existing template lifecycle setup fails at `tests/template.test.ts:105`; this is a regression-killing probe in addition to the hidden failure. Logs: `probe-operators-lose-the-exemption-{regression,hidden}.log`. |
| (c) Probe 3: remove the save paid-check | Exact replacement occurred once. H exit **1**, **6.95 s**, line 17 expected 403 but got 201. R exits **1**; existing `tests/designs.test.ts:77` also observes the forbidden save returning 201. Logs: `probe-design-save-skips-paid-check-{regression,hidden}.log`. |
| (d) First-obvious partial | Check paid/active periods but forget suspended periods. R exit **0**, 11 passed, **6.20 s**; H exit **1**, **4.52 s**, line 44 expected HTTP 403 but got 201 for a suspended customer. Logs: `d-partial-allows-suspended-{regression,hidden}.log`. |

#### `b-contract-catalog-default-page`

Reference patch: `reference/b-contract-catalog-default-page.patch`.

| Stage | Result and evidence |
|---|---|
| (a) Pinned starting clone | H exit **1**, 1 test failed, **5.26 s**. `tests/zz-eval-b-contract.test.ts:25` observed the catalog's old default of 20 instead of the requested 40 (`pageCount` was correspondingly short). Log: `evidence/b-contract-catalog-default-page/start-hidden.log`. |
| (b) Reference | H exit **0**, 1 passed, **5.44 s**; R exit **0**, 31 passed, **20.34 s**. Logs: `reference-hidden.log`, `reference-regression.log`. |
| (c) Probe 1: leave the catalog default at 20 | Exact replacement occurred once. R exit **0**, 31 passed, **21.74 s**; H exit **1**, **5.64 s**, line 25 still observes 20 rather than 40. Logs: `probe-default-remains-twenty-{regression,hidden}.log`. |
| (c) Probe 2: cap explicit page size at 49 | Exact replacement occurred once. R exit **0**, 31 passed, **22.14 s**; H exit **1**, **4.88 s**, line 47 rejects the valid explicit size 50 instead of returning that page size. Logs: `probe-explicit-fifty-limit-is-capped-at-forty-nine-{regression,hidden}.log`. |
| (d) First-obvious partial | Set the default to 40 only for unfiltered browsing, leaving search and kind-filtered catalog requests at 20. R exit **0**, 31 passed, **23.44 s**; H exit **1**, **5.14 s**, line 38 expects 40 search results per page but gets 20. Logs: `d-partial-browse-only-{regression,hidden}.log`. |

This scenario also covers the cross-module regression failure mode. A plausible broad fix changes the shared product pagination default from 100 to 40. Running the explicit existing `tests/product.test.ts` command then exits **1**: `tests/product.test.ts:79` expects the separate account-products API to retain `pageCount: 100`, but sees 40; 17 tests pass and 1 fails in **5.80 s**. Evidence: `evidence/b-contract-catalog-default-page/natural-shared-default-regression.log`. The reference changes only the catalog schema default and preserves the account-products contract.

#### `b-cross-path-custom-unit-limit`

The starting clone has the scenario's planted shared-schema maximum of 40. Reference patch: `reference/b-cross-path-custom-unit-limit.patch`.

| Stage | Result and evidence |
|---|---|
| (a) Pinned starting clone with fault | H exit **1**, 1 test failed, **4.87 s**. `tests/zz-eval-b-cross-path.test.ts:23` expected a 21-character unit to return HTTP 400 but it was accepted with 201. Log: `evidence/b-cross-path-custom-unit-limit/start-hidden.log`. |
| (b) Reference | H exit **0**, 1 passed, **4.83 s**; R exit **0**, 21 passed, **20.38 s**. Logs: `reference-hidden.log`, `reference-regression.log`. |
| (c) Probe 1: allow a 21-character unit | Exact replacement occurred once. R exit **0**, 21 passed, **21.95 s**; H exit **1**, **5.72 s**, line 23 expected HTTP 400 but got 201. Logs: `probe-twenty-one-character-unit-is-accepted-{regression,hidden}.log`. |
| (c) Probe 2: collapse internal whitespace while importing | Exact replacement occurred once. R exit **0**, 21 passed, **19.06 s**; H exit **1**, **4.56 s**, line 58 expected the padded 21-character import row to be `invalid` but it was accepted as a create row. Logs: `probe-import-collapses-inner-spaces-before-counting-{regression,hidden}.log`. |
| (c) Probe 3: reject the valid 20-character boundary | Exact replacement occurred once. R reports **21 passed**, **29.25 s**; H exit **1**, **4.77 s**, line 17 expected the 20-character value to be accepted with HTTP 201. Logs: `probe-twenty-character-unit-is-rejected-{regression,hidden}.log`. |
| (d) First-obvious partial | Apply the 20-character validation to create/edit but keep the import path's internal-whitespace collapsing. R exit **0**, 21 passed, **19.06 s**; H exit **1**, **4.56 s**, line 58 observes the import bypass. This is Probe 2 and uses the same evidence. |

## Yeondoo Link and anchor validation

All Yeondoo runs used a fresh local clone pinned to `d17f0c2322056a4d804c911b83d6cc1b1738a083`; the anchor used a separate fresh Labeler clone pinned to `984e4f646e08b75a8dfc4b9c62913670960c1659`. Each clone's `node_modules` was a junction to its matching `eval-deps` copy. No package installation or commit was used. Raw command output, exit codes, and runtimes are under the corresponding `evidence/` folders.

The Yeondoo regression command is explicit and independent of Skill_Management:

```text
node --experimental-strip-types --test scripts/session.test.mjs scripts/cart.test.mjs
```

### `cart-item-to-compare`

The starting-tree hidden command was `node --experimental-strip-types --test scripts/zz-eval-cart-item-to-compare.test.mjs`. It exited 1 in 0.279 s: all four subtests failed because the action was unsupported; the first candidate-order assertion is at hidden test line 58, with no-op assertions at lines 103, 123, and 138.

Applying `reference/cart-item-to-compare.patch` made the hidden command pass 4/4 in 0.244 s and the Yeondoo regression command pass 12/12 in 0.236 s. The client change also passed `node node_modules/typescript/bin/tsc --noEmit --pretty false` in 0.543 s.

Each mutation below matched its `find` text exactly once in the reference tree. The configured regression command passed for each mutation; the hidden command failed on the named assertion:

| Probe | Hidden result | Regression result | Failure |
| --- | --- | --- | --- |
| `duplicate-add-toggles-existing-comparison-item` | exit 1, 0.221 s | exit 0, 0.220 s | Existing item must remain unchanged, hidden line 103. |
| `sixth-item-is-accepted` | exit 1, 0.257 s | exit 0, 0.268 s | Sixth-item rejection, hidden line 123. |
| `new-item-keeps-stale-review` | exit 1, 0.229 s | exit 0, 0.255 s | Successful addition must clear only the new item's old review data, hidden line 63. |

For the partial implementation, I routed `compare-cart-item` through the existing `candidate` toggle after checking that the cart contains the product. This passes the regression command in 0.239 s but fails the hidden suite in 0.209 s because repeating an already-compared item toggles it out (hidden line 103). The partial patch is retained as `evidence/y-cart-item-to-compare/d-partial.patch`.

The hidden oracle exercises the session transition, not browser reachability. The reference adds a localized action to each cart row, and the TypeScript check passes, but there is no browser-interaction result for this scenario.

### `medicine-catalog-classification-bypass`

The planted fault changed `tylenol500.kind` from `medicine` to `cosmetic`; its exact replacement matched once. With that fault applied, the hidden command `node --experimental-strip-types --test scripts/zz-eval-medicine-classification.test.mjs` exited 1 in 0.220 s. The overview assertion failed at hidden line 25 and the purchase-request assertion failed at line 31, as intended.

The nonempty `reference/medicine-catalog-classification-bypass.patch` reverses the fault to the canonical medicine classification. Applying it made the hidden command pass 5/5 in 0.245 s and the Yeondoo regression command pass 12/12 in 0.225 s.

Each exact probe matched once on the reference tree:

| Probe | Hidden result | Regression result | Failure |
| --- | --- | --- | --- |
| `hides-approved-and-cosmetic-overviews` | exit 1, 0.212 s | exit 0, 0.244 s | Forcing overview lookup to false hides confirmed-medicine and ordinary-cosmetic overviews; hidden lines 38 and 46 fail because those overviews should be visible. |
| `medicine-purchase-bypasses-pharmacist-gate` | exit 1, 0.235 s | exit 1, 0.237 s | Purchase remains incorrectly allowed for Tylenol and another medicine; hidden lines 31 and 55. |

The plausible partial implementation special-cases Tylenol in the purchase-review rule but leaves its catalog classification and overview rule untouched. It passes regression in 0.256 s and fails hidden in 0.200 s on the overview assertion at line 25. Its patch is retained as `evidence/y-medicine-catalog-classification-bypass/d-partial.patch`.

### `rule-all-paths` anchor

The scenario object, hidden test, reference patch, probes, and regression command are unchanged from v1. The copied hidden test and reference patch have the same SHA-256 hashes as their v1 sources.

Starting-tree hidden command:

```text
set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false tests/zz-eval-rule-all-paths.test.ts
```

It exited 1 in 9.790 s with all 6 tests failing. The assertions cover create/update (hidden line 21), legacy copy (line 40), bulk import/update (lines 54 and 70), shared catalog add (line 89), and restore (line 102).

Applying the unchanged `reference/rule-all-paths.patch` made the hidden command pass 6/6 in 10.382 s. The unchanged explicit regression command exited 0 in 43.248 s:

```text
set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/product.test.ts tests/productImportPerformance.test.ts tests/backup.test.ts tests/productCatalog.test.ts src/client/ProductForm.test.tsx src/client/ProductCatalogFinder.test.tsx
```

Both unchanged probes matched exactly once. Their hidden command failed as required; their configured regression command passed:

| Probe | Hidden result | Regression result | Failure |
| --- | --- | --- | --- |
| `allows-overlong-create-description` | exit 1, 10.675 s | exit 0, 45.122 s | Create/update, legacy-copy, and shared-catalog assertions fail; hidden lines 21, 40, and 89. |
| `skips-restore-description-guard` | exit 1, 12.769 s | exit 0, 43.811 s | Restore rejects no overlong value; hidden line 102. |

The partial implementation limits only the create schema to 300 characters and leaves update, copy, import, and restore paths unchanged. It passes the regression command in 39.016 s and fails the hidden command in 10.050 s: update, legacy-copy, and restore assertions fail at lines 21, 40, and 102. The partial patch is retained as `evidence/rule-all-paths/d-partial.patch`.

The superseded cart-transfer prototype logs remain under `evidence/y-cart-transfer/` with an audit note; they are excluded from all active scenario results. The comparison-flow hidden oracle is reducer-only, as described above.

## Final integration and cleanup

- Actual runner schema validation and the OFF/plugin 24-cell dry run exited 0, with zero sessions launched. Commands and output: evidence/dry-run-command.json, dry-run.json.
- Independent pinned-clone patch checks and all 28 unique reference probe byte matches passed for all 12 scenarios; anchor object and hidden/reference bytes equal v1. See evidence/asset-audit.json. Additional worker compiler checks passed for offer restore, source staleness and the import sequence.
- Integration corrected byte-context transport only: the root multiline fault and Yeondoo multiline contexts use CRLF, and the paid-guard fault removes the complete line to match its staged reference base. The branch descendant probe now uses the corrected mapped-row type; its final rerun exited 1 at hidden line 56 (expected 3 categories, got 1), 9.328 seconds wall time. See evidence/b-sequence-category-branch-copy/final-descendant-probe-hidden.json and .log. These corrections did not change the canonical reference or mutation behavior.
- The original two source checkouts retained identical HEAD, Git status and tracked diff hashes after all work. Source snapshots are in evidence/source-before.json and source-after.json.
- Cleanup inventory found 32 disposable clone roots, 130,756 ordinary files and 17,899,913,750 bytes. All 9 remaining junctions were removed with cmd /c rmdir before recursively deleting only C:/Users/YS/AppData/Local/Temp/claude/eval-authoring-v2/. That directory is absent. Both evaluation dependency copies retained their entry counts and lockfile hashes. Exact targets/exclusions/results: evidence/cleanup-preview.json, cleanup-result.json, dependency-cleanup-before.json, dependency-cleanup-after.json.
- No scenario remains invalid under a-d. Browser interaction and actual candidate-agent discrimination remain unmeasured.
