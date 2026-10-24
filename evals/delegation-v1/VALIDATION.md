# Validation: delegation v1

Authoring controls were executed on Windows in throwaway local clones under `C:/Users/YS/AppData/Local/Temp/claude/eval-authoring/`, at Labeler `984e4f646e08b75a8dfc4b9c62913670960c1659` and yeondoo-link `d17f0c2322056a4d804c911b83d6cc1b1738a083`. No commits or paid Claude sessions were run. Only this suite directory was authored in Skill_Management; the source checkout working trees were not modified. Existing concurrent Skill_Management changes and yeondoo-link documentation changes were preserved. Feature impact is evaluation assets only; no product Feature Map row is changed because product changes exist exclusively as reference patches in disposable clones.

## Host and interpretation

- The initial `git clone --local` hardlink attempt failed with permission denied under the sandbox account. Local clones succeeded with `--local --no-hardlinks`. Source Git ownership checks used process/command-local `safe.directory` values, never global settings. `evidence/environment.json` distinguishes current source HEADs from the actual pinned evaluation refs.
- Default Labeler Vitest startup failed at `node_modules/.vite-temp` through the required source junction. All final commands use `--configLoader runner --cache=false`; Wrangler logs are redirected to the clone's `.work/`. These command flags change host loading/cache behavior, not application behavior. Full `--changed <pin>` commands were actually executed without hidden files, and their measured times are reported below.
- Existing Labeler client tests use React `renderToStaticMarkup`; neither jsdom nor happy-dom is installed. Client hidden checks follow that existing rendered-DOM convention. No pixel, real-browser, provider, production or paid-agent acceptance is claimed.
- yeondoo-link's programmatic Vite test also attempts `node_modules/.vite-temp`. Its command-scoped preload rejects only directory creation at that clone-relative junction path with EACCES, activating Vite's built-in config-adjacent temporary-file fallback. Helpers are suite-owned assets reachable before hidden installation; application/tests and source dependencies remain unchanged. The full `node --experimental-strip-types --test scripts/*.test.mjs` is retained after the environment prefix.
- Faults were applied and staged, where needed, only in throwaway clones, without commits. The reference diff is relative to the faulted start. The existing runner later commits scenario faults before paid sessions; that behavior was read, not executed during authoring.
- Starting RED and mutation RED require assertion failures about the requested behavior; setup errors are not evidence of validity. Reference GREEN requires both the final hidden command and the declared existing-suite regression. Probe kill controls use hidden tests; separately labeled hidden-free runs execute the exact future probe command and establish current test-suite sensitivity and timing. Passing hidden-free controls are expected where the original suite lacks new feature coverage.
- Reference probes use exact byte replacements. A fresh-clone audit independently applied every fault and reference patch, checked every probe target occurs exactly once as UTF-8 bytes, reversed the patch/fault, and confirmed a clean tree. This protects against newline normalization and wrong diff bases. See `evidence/asset-audit.json`.
- Runner schema validation plus a 16-cell OFF/plugin matrix dry run passed (exit 0), with `python -B scripts/run_delegation_eval.py ... --dry-run` and process-local Git ownership entries. No paid sessions ran. The runner's unchanged hardlink clone path cannot execute under this sandbox account; use an account where that operation succeeds. No runner repair was authorized.
- Budgets are 1,800/2,700 seconds as requested. The existing runner applies the sequence budget separately to each prompt. Actual delegated-agent duration, cost, success rate, and model identity remain unmeasured; 10–25 minutes is a task sizing estimate.


## Final control summary

| Scenario | Starting hidden exit | Reference hidden / regression exits | Hidden probe kills |
| --- | ---: | --- | ---: |
| fullstack-feature | 1 | 0 / 0 | 2/2 |
| rule-all-paths | 1 | 0 / 0 | 2/2 |
| complaint-bypass | 1 | 0 / 0 | 2/2 |
| api-contract-change | 1 | 0 / 0 | 2/2 |
| ui-consistency | 1 | 0 / 0 | 2/2 |
| sequence-rule-preserve | 1 | 0 / 0 | 2/2 |
| fe-logic-feature | 1 | 0 / 0 | 3/3 |
| fe-bug | 1 | 0 / 0 | 2/2 |

All eight scenarios satisfy the requested authoring controls. Final configured command measurements are below five minutes; the retained 381-second broad experiment was rejected in favor of scoped commands. Hidden-test failure under each probe establishes mutation relevance; it is distinct from future candidate test detection.

## fullstack-feature

Feature: new private account work memo; no Skill_Management product feature changes. Clone: `C:\Users\YS\AppData\Local\Temp\claude\eval-authoring\fullstack-copy`. Pinned Labeler ref.

| Stage | Exit | Seconds | Command |
| --- | --- | --- | --- |
| starting-hidden | 1 | 9.937 | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false tests/zz-eval-fullstack-feature.test.ts src/client/zz-eval-fullstack-feature.test.tsx` |
| reference-hidden | 0 | 9.719 | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false tests/zz-eval-fullstack-feature.test.ts src/client/zz-eval-fullstack-feature.test.tsx` |
| reference-regression | 0 | 26.921 | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false tests/socialAuth.test.ts tests/accountIsolation.test.ts src/client/BillingManager.test.tsx src/client/Account.test.tsx` |
| probe-1-hidden | 1 | 10.079 | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false tests/zz-eval-fullstack-feature.test.ts src/client/zz-eval-fullstack-feature.test.tsx` |
| probe-1-without-hidden | 0 | 104.468 | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --changed 984e4f646e08b75a8dfc4b9c62913670960c1659` |
| probe-2-hidden | 1 | 10.922 | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false tests/zz-eval-fullstack-feature.test.ts src/client/zz-eval-fullstack-feature.test.tsx` |
| probe-2-without-hidden | 0 | 107.235 | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --changed 984e4f646e08b75a8dfc4b9c62913670960c1659` |

Starting failure: new workMemo PATCH rejected with 400 instead of 200; account HTML lacks memo. Reference covers React form/state/request, API strict schema, domain write/read mapping, additive D1 migration, fresh authenticated reads, clear, 200/201 boundary, atomic rejection, and account isolation.

Probe 1 drops the domain value; probe 2 suppresses persisted memo display. Each hidden check failed at its target. Hidden-free probe runs measure existing-suite sensitivity, not a requirement that the reference leave new visible tests. Hidden UI observation follows existing SSR convention and does not simulate a browser click; reference save wiring was inspected. Existing tests unchanged.

Raw command output: `evidence/fullstack-feature/*.log`; exact timings: `evidence/fullstack-feature/results.json`.

Final oracle revision removes a physical database column-name assertion to allow equivalent D1 designs; API field workMemo is explicit in the prompt. Fresh authenticated request reads remain. Final unchanged product reference and probes were replayed against this final oracle:

- `final-starting-hidden`: exit 1, 10.313 s; hidden command above.
- `final-reference-hidden`: exit 0, 10.5 s; hidden command above.
- `final-probe-1-hidden`: exit 1, 10.75 s; hidden command above.
- `final-probe-2-hidden`: exit 1, 10.734 s; hidden command above.

Final broad probe commands bound Vitest workers to four and use 20-second individual test/hook deadlines. This avoids incidental 5-second timeouts observed during concurrent authoring; no business assertion was removed. Earlier runs remain in raw logs. Final exact hidden-free probe commands:

- `bounded-probe-1-without-hidden`: exit 1, 233.484 s; `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --changed 984e4f646e08b75a8dfc4b9c62913670960c1659 --maxWorkers=4 --testTimeout=20000 --hookTimeout=20000`.
- `bounded-probe-2-without-hidden`: exit 0, 246.141 s; `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --changed 984e4f646e08b75a8dfc4b9c62913670960c1659 --maxWorkers=4 --testTimeout=20000 --hookTimeout=20000`.

**Final probe command selection:** broad `--changed <pin>` was attempted with the junctioned modules, first at default concurrency/deadlines and then at maxWorkers=4 with 20-second deadlines. Retained outputs show incidental timeouts and/or Miniflare worker startup errors (`bad port`, websocket upgrade), even with passing business assertions; those are environment failures, not detected mutations. Following the requested fallback, final probes list the relevant existing files plus plausible new owner-test filenames. This is narrower than dependency discovery and can miss differently named candidate tests; it avoids counting unrelated host errors as prevention. Final exact hidden-free controls:

- `final-scoped-probe-1-without-hidden`: exit 0, 32.093 s; `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false tests/socialAuth.test.ts tests/accountIsolation.test.ts src/client/BillingManager.test.tsx src/client/Account.test.tsx src/client/AccountManager.test.tsx tests/accountProfiles.test.ts --maxWorkers=4 --testTimeout=20000 --hookTimeout=20000`.
- `final-scoped-probe-2-without-hidden`: exit 0, 30.563 s; `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false tests/socialAuth.test.ts tests/accountIsolation.test.ts src/client/BillingManager.test.tsx src/client/Account.test.tsx src/client/AccountManager.test.tsx tests/accountProfiles.test.ts --maxWorkers=4 --testTimeout=20000 --hookTimeout=20000`.


Key observed assertion lines (raw logs retained):


- `evidence/fullstack-feature/final-probe-1-hidden.log`: AssertionError: expected null to be '다음 달 포장 변경' // Object.is equality; AssertionError: expected { …(14) } to match object { organization: '기존 약국', …(1) }

- `evidence/fullstack-feature/final-probe-2-hidden.log`: AssertionError: expected '<main class="workspace billing-page a…' to contain '&lt;b&gt;내 작업 메모&lt;/b&gt;'

- `evidence/fullstack-feature/final-starting-hidden.log`: AssertionError: work memo must be accepted for a free customer: expected 400 to be 200 // Object.is equality; AssertionError: expected 400 to be 200 // Object.is equality; AssertionError: my account must expose the work memo: expected '<main class="workspace billing-page a…' to contain '작업 메모'

- `evidence/fullstack-feature/probe-1-hidden.log`: AssertionError: expected null to be '다음 달 포장 변경' // Object.is equality; AssertionError: expected { …(14) } to match object { organization: '기존 약국', …(1) }

- `evidence/fullstack-feature/probe-2-hidden.log`: AssertionError: expected '<main class="workspace billing-page a…' to contain '&lt;b&gt;내 작업 메모&lt;/b&gt;'

- `evidence/fullstack-feature/starting-hidden.log`: AssertionError: work memo must be accepted for a free customer: expected 400 to be 200 // Object.is equality; AssertionError: expected 400 to be 200 // Object.is equality; AssertionError: my account must expose the work memo: expected '<main class="workspace billing-page a…' to contain '작업 메모'


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


Key observed assertion lines (raw logs retained):


- `evidence/rule-all-paths/a-start-hidden.txt`: AssertionError: expected 201 to be 400 // Object.is equality; AssertionError: expected 201 to be 400 // Object.is equality; AssertionError: expected 'create' to be 'invalid' // Object.is equality; AssertionError: expected { Object (mode, canApply, ...) } to match object { Object (canApply, conflicts) }


## complaint-bypass

The complaint is a product-description limit mismatch: new products reject descriptions above 500 characters, while editing an existing product accepts them. The planted defect changes only `updateProductSchema` in `src/shared/product.ts` from 500 to 800. The hidden API check exercises both PATCH and sibling POST, then confirms a rejected edit preserves the old description.

Clone: `C:\Users\YS\AppData\Local\Temp\claude\eval-authoring\complaint-bypass-20261024`, detached at `984e4f646e08b75a8dfc4b9c62913670960c1659`, with `node_modules` junctioned to the source. The fault's exact find occurs once. The fault was staged only to form a reference diff; no commit was created during authoring. `fault.commit_message` is provided for the runner's pre-session fault commit. The reference patch changes the limit back from 800 to 500 and applies cleanly to the faulted tree.

Commands ran with `WRANGLER_LOG_PATH=.work\eval-wrangler.log`.

| Check | Exit | Runtime | Result |
| --- | ---: | ---: | --- |
| Faulted starting tree hidden check: `npx vitest run --configLoader runner --cache=false tests/zz-eval-complaint-bypass.test.ts` | 1 | 12.32 s | The PATCH branch accepted the 501-character description: expected status 400, received 200 (`zz-eval-complaint-bypass.test.ts:30`). The sibling create assertion passed. |
| Reference hidden check, same command | 0 | 11.76 s | 1/1 passed; the edit was rejected and the stored description stayed unchanged. |
| Regression: `npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/product.test.ts src/client/ProductForm.test.tsx` | 0 | 28.18 s | 2 files, 20 tests passed. |
| Probe 1: change the create schema's `.max(500)` to `.max(800)`; hidden check | 1 | 13.41 s | Exact find is 49 UTF-8 bytes and occurs once. The sibling create assertion failed: expected 400, received 201 (`:25`). |
| Probe 1 command, with hidden file moved out: same two-file regression command | 0 | 27.91 s | 2 files, 20 tests passed. |
| Probe 2: change the update schema's `.max(500).optional()` to `.max(800).optional()`; hidden check | 1 | 12.92 s | Exact find is 60 UTF-8 bytes and occurs once. PATCH assertion failed: expected 400, received 200 (`:30`). |
| Probe 2 command, with hidden file moved out: same two-file regression command | 0 | 26.88 s | 2 files, 20 tests passed. |

The broad `--changed` command exceeded five minutes and encountered unrelated timeouts and an Undici `bad port` worker-start error on the junctioned host during the other Labeler scenario. This scenario therefore uses the exact existing product tests most likely to be touched rather than a broad changed-file run.

Raw output: `evidence/complaint-bypass/complaint-bypass-a-start-hidden.txt`, `complaint-bypass-b-reference-hidden.txt`, `complaint-bypass-b-regression.txt`, `complaint-bypass-c-probe1-hidden.txt`, `complaint-bypass-c-probe1-command-hidden-free.txt`, `complaint-bypass-c-probe2-hidden.txt`, and `complaint-bypass-c-probe2-command-hidden-free.txt`.


Key observed assertion lines (raw logs retained):



# `api-contract-change` validation

Validated in a disposable local clone at `984e4f646e08b75a8dfc4b9c62913670960c1659`; the source repository was not edited. The reference implementation is [api-contract-change.patch](reference/api-contract-change.patch). The hidden route test seeds 105 recent jobs and exercises a smaller `limit`, the default array/order, invalid values, and the 100-item cap.

- **Starting tree (a):** `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false tests/zz-eval-api-contract-change.test.ts` exited 1 in 7.765s. `tests/zz-eval-api-contract-change.test.ts:23` expected the three newest IDs but received the default 100, because the route ignored `limit`.
- **Reference (b):** the same hidden command exited 0 in 7.816s (1 test passed). Regression command `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false tests/credits.test.ts tests/translationCredits.test.ts tests/fieldTranslations.test.ts tests/catalogTranslationReuse.test.ts src/client/TranslationManager.test.tsx` exited 0 in 22.508s (5 files, 60 tests passed).
- **Probe `caps-requested-history-size` (c):** replacing `Math.min(requestedLimit, 100)` with `requestedLimit` occurred once. The hidden test exited 1 in 7.543s at line 37: expected 100 jobs, received 105. With hidden files moved out of `tests/`, `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --changed 984e4f646e08b75a8dfc4b9c62913670960c1659 --configLoader runner --cache=false --maxWorkers=4 --testTimeout=20000 --hookTimeout=20000` exited 0 in 97.588s (59 files, 465 passed, 3 skipped).
- **Probe `rejects-fractional-history-limit` (c):** replacing `Number.isInteger(requestedLimit) && requestedLimit > 0` with `requestedLimit > 0` occurred once. The hidden test exited 1 in 8.587s: `?limit=2.5` returned HTTP 500 instead of 200, failing the response-status assertion at line 17. With hidden files moved out of `tests/`, the same `--changed` command exited 0 in 249.843s (59 files, 465 passed, 3 skipped).

The hidden-free `--changed` commands use `--maxWorkers=4 --testTimeout=20000 --hookTimeout=20000`. Earlier broad runs with Vitest's default 5-second timeout had unrelated worker-startup/network errors and timed-out tests; the bounded command above completed under five minutes. The junctioned `node_modules` emitted a sourcemap-outside-clone warning, without affecting the passing result.

Raw command output, including the failed broad attempts, is retained under [`evidence/api-contract-change/`](../evidence/api-contract-change/).


Key observed assertion lines (raw logs retained):



# `ui-consistency` validation

Validated in a disposable local clone at `984e4f646e08b75a8dfc4b9c62913670960c1659`; the source repository was not edited. The reference implementation is [ui-consistency.patch](reference/ui-consistency.patch). The hidden test renders the product finder with its existing React SSR convention and checks that each selectable product name has a valid HTML label association to its enabled checkbox, while an already-added product stays disabled.

- **Starting tree (a):** `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false src/client/zz-eval-ui-consistency.test.tsx` exited 1 in 21.958s. The assertion at line 40 found no label containing the selectable product name.
- **Reference (b):** the same hidden command exited 0 in 20.996s (1 test passed). Existing client regression `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false src/client/ProductCatalogFinder.test.tsx` exited 0 in 19.004s (1 file, 12 tests passed).
- **Probe `keeps-product-name-associated` (c):** removing the label's checkbox association occurred once. The hidden test exited 1 in 19.651s at line 46 because neither an explicit `for` link nor a nested checkbox associated the visible product name.
- **Probe `keeps-added-catalog-item-disabled` (c):** removing the already-added condition from `disabled` occurred once. The hidden test exited 1 in 21.276s at line 53 because the added product checkbox no longer had `disabled`.

The hidden-free configured `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --changed 984e4f646e08b75a8dfc4b9c62913670960c1659 --configLoader runner --cache=false --maxWorkers=4 --testTimeout=20000 --hookTimeout=20000` command exited 0 for each probe: 35.078s after the association probe and 34.181s after the added-item probe (each 5 files, 34 tests passed). This repository has no jsdom or happy-dom dependency, so the hidden test follows the existing server-rendered client test approach and asserts DOM semantics; it does not run a browser interaction test.

Raw command output is retained under [`evidence/ui-consistency/`](../evidence/ui-consistency/).


Key observed assertion lines (raw logs retained):



## sequence-rule-preserve

Feature: support inquiry admission and completed-inquiry resubmission. Sequential product requests; final oracle checks both. No Skill_Management product change. Clone: `C:\Users\YS\AppData\Local\Temp\claude\eval-authoring\sequence`.

| Stage | Exit | Seconds | Command |
| --- | --- | --- | --- |
| starting-hidden | 1 | 9.578 | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false tests/zz-eval-sequence-rule-preserve.test.ts` |
| reference-hidden | 0 | 9.641 | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false tests/zz-eval-sequence-rule-preserve.test.ts` |
| reference-regression | 0 | 13.906 | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false tests/accountRequests.test.ts tests/accountRequestRefund.test.ts tests/accountIsolation.test.ts` |
| probe-1-hidden | 1 | 10.141 | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false tests/zz-eval-sequence-rule-preserve.test.ts` |
| probe-1-without-hidden | 1 | 114.406 | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --changed 984e4f646e08b75a8dfc4b9c62913670960c1659` |
| probe-2-hidden | 1 | 10.875 | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false tests/zz-eval-sequence-rule-preserve.test.ts` |
| probe-2-without-hidden | 1 | 123.641 | `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --changed 984e4f646e08b75a8dfc4b9c62913670960c1659` |

The first request caps unresolved support at three per account, includes hidden/in-progress rows, excludes closed rows, preserves idempotency and independent accounts, and covers simultaneous admission. The second request copies only owned visible completed support into a new unanswered row, keeps source history unchanged, preserves the original cap and retries, and rejects open/foreign sources. A single atomic INSERT SELECT enforces admission for both paths; refund admission is unchanged.

Probe 1 admits a fourth unresolved inquiry; probe 2 removes ownership from resubmission lookup. Both must fail final hidden assertions. Hidden-free probe outcomes measure baseline prevention separately. Raw logs and timing records are under `evidence/sequence-rule-preserve/`.

Final hidden suite additionally exercises refund creation at a full support cap and rejection of resubmitting completed refund history. Four final hidden tests; replay results:

- `final-starting-hidden`: exit 1, 11.89 s; hidden command above.
- `final-reference-hidden`: exit 0, 15.219 s; hidden command above.
- `final-probe-1-hidden`: exit 1, 11.687 s; hidden command above.
- `final-probe-2-hidden`: exit 1, 13.11 s; hidden command above.

Final broad probe commands bound Vitest workers to four and use 20-second individual test/hook deadlines. This avoids incidental 5-second timeouts observed during concurrent authoring; no business assertion was removed. Earlier runs remain in raw logs. Final exact hidden-free probe commands:

- `bounded-probe-1-without-hidden`: exit 0, 216.015 s; `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --changed 984e4f646e08b75a8dfc4b9c62913670960c1659 --maxWorkers=4 --testTimeout=20000 --hookTimeout=20000`.
- `bounded-probe-2-without-hidden`: exit 0, 234.266 s; `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --changed 984e4f646e08b75a8dfc4b9c62913670960c1659 --maxWorkers=4 --testTimeout=20000 --hookTimeout=20000`.


Key observed assertion lines (raw logs retained):


- `evidence/sequence-rule-preserve/final-probe-1-hidden.log`: AssertionError: fourth unresolved support request must be rejected: expected 201 to be 409 // Object.is equality; AssertionError: resubmit must preserve the first request unresolved-support cap: expected 201 to be 409 // Object.is equality; AssertionError: expected [ 201, 201, 201, 201 ] to deeply equal [ 201, 201, 201, 409 ]

- `evidence/sequence-rule-preserve/final-probe-2-hidden.log`: AssertionError: another member cannot copy a private inquiry: expected 201 to be 404 // Object.is equality

- `evidence/sequence-rule-preserve/final-starting-hidden.log`: AssertionError: fourth unresolved support request must be rejected: expected 201 to be 409 // Object.is equality; AssertionError: completed support can be resubmitted: expected 404 to be 201 // Object.is equality; AssertionError: expected [ 201, 201, 201, 201 ] to deeply equal [ 201, 201, 201, 409 ]; AssertionError: only general support can be resubmitted: expected 404 to be 409 // Object.is equality

- `evidence/sequence-rule-preserve/probe-1-hidden.log`: AssertionError: fourth unresolved support request must be rejected: expected 201 to be 409 // Object.is equality; AssertionError: resubmit must preserve the first request unresolved-support cap: expected 201 to be 409 // Object.is equality; AssertionError: expected [ 201, 201, 201, 201 ] to deeply equal [ 201, 201, 201, 409 ]

- `evidence/sequence-rule-preserve/probe-2-hidden.log`: AssertionError: another member cannot copy a private inquiry: expected 201 to be 404 // Object.is equality

- `evidence/sequence-rule-preserve/starting-hidden.log`: AssertionError: fourth unresolved support request must be rejected: expected 201 to be 409 // Object.is equality; AssertionError: completed support can be resubmitted: expected 404 to be 201 // Object.is equality; AssertionError: expected [ 201, 201, 201, 201 ] to deeply equal [ 201, 201, 201, 409 ]


# Yeondoo Link: `fe-logic-feature`

The buyer can move every selected quantity from purchase review into the cart in one action. Quantities merge with existing cart items; any item that is unclassified, known out of stock, needs pharmacist approval, or would exceed 99 causes the whole transfer to be rejected. The UI adds a localized cart action in the purchase screen and reports successful adds through the existing live status region.

Prompt: 구매 검토 화면에서 선택한 상품들을 장바구니에 한 번에 담는 `add-selected-to-cart` 동작을 추가해 주세요. 기존 장바구니 수량에 선택한 수량을 더하고, 상품별 수량은 99개를 넘지 않게 해 주세요. 재고가 없거나 분류가 정해지지 않은 상품은 담을 수 없고, 약사 확인이 필요한 의약품은 확인이 끝난 뒤에만 담을 수 있어야 합니다. 하나라도 담을 수 없는 상품이 있으면 일부만 추가하지 말고 장바구니를 그대로 두고 선택도 유지해 주세요.

Pinned source: `C:/Users/YS/Desktop/python/yeondoo-link`, `d17f0c2322056a4d804c911b83d6cc1b1738a083`. Validation clone: `C:/Users/YS/AppData/Local/Temp/claude/eval-authoring/delegation-20261024-yeondoo`. The hidden test imports the existing `transition` module and exercises its public action; it does not require an exported implementation helper.

| Stage | Command / outcome | Runtime | Evidence |
| --- | --- | ---: | --- |
| (a) pinned start | `node --experimental-strip-types --test scripts/zz-eval-fe-logic-feature.test.mjs` -> exit 1, 0/6 passed | 0.279 s | `a-start-hidden.log`: first acceptance assertion expected cart `{illiyoon_cream: 5}`, actual `{}` (line 36); the baseline has no bulk-cart action. |
| (b) reference hidden | Same hidden-only command -> exit 0, 6/6 passed | 0.246 s | `b-hidden-pass.log` |
| (b) reference regression | `set "NODE_OPTIONS=--require=C:/Users/YS/Desktop/python/Skill_Management/evals/delegation-v1/evidence/fe-logic-feature/vite-temp-safe-host.cjs" && node --experimental-strip-types --test scripts/*.test.mjs` -> exit 0, 62/62 passed (56 existing + 6 hidden) | 2.427 s | `b-regression-pass.log` |
| (b) production build | `npm run build` -> exit 0; TypeScript and Vite build pass | 8.533 s | `b-build.log` |
| (c) hidden-free baseline | The runner probe command -> exit 0, 56/56 existing test cases | 2.765 s | `c-no-hidden-baseline.log` |

The reference implementation is [reference/fe-logic-feature.patch](reference/fe-logic-feature.patch). Every probe matcher occurs once in the reference tree. Runner-style probe commands were run with hidden files absent; all passed on the reference tree. Applying each mutation separately and installing the hidden file only for the mutation-kill check produced:

| Probe mutation | Hidden-free runner command | Hidden acceptance kill |
| --- | --- | --- |
| Remove the explicit unclassified-product rejection | exit 0, 56/56, 2.485 s (`c-no-hidden-classification.log`) | exit 1, 5/6; 'an unclassified selection prevents every item' fails (`c-hidden-kill-classification.log`) |
| Remove the catalog out-of-stock rejection | exit 0, 56/56, 2.613 s (`c-no-hidden-catalog-stock.log`) | exit 1, 5/6; 'a catalog item marked out of stock' fails (`c-hidden-kill-catalog-stock.log`) |
| Bypass the medicine pharmacist gate | exit 0, 56/56, 2.535 s (`c-no-hidden-pharmacist-gate.log`) | exit 1, 5/6; 'a pharmacist-required product' fails (`c-hidden-kill-pharmacist-gate.log`) |

The test host junction makes Vite's dev-server test unable to write `node_modules/.vite-temp`. The suite-owned preload rejects only that exact junction directory's `mkdir` with `EACCES`, which triggers Vite's own config-adjacent fallback inside the disposable clone. The helper does not redirect arbitrary paths. The hidden logic suite does not render the button DOM; `npm run build` checks that the UI integration type-checks and bundles. No product source checkout was modified and no commit was made during authoring.


Key observed assertion lines (raw logs retained):


- `evidence/fe-logic-feature/a-start-hidden.log`: name: 'AssertionError'; name: 'AssertionError'; name: 'AssertionError'; name: 'AssertionError'

- `evidence/fe-logic-feature/c-hidden-kill-catalog-stock.log`: name: 'AssertionError'

- `evidence/fe-logic-feature/c-hidden-kill-classification.log`: name: 'AssertionError'

- `evidence/fe-logic-feature/c-hidden-kill-pharmacist-gate.log`: name: 'AssertionError'


# Yeondoo Link: `fe-bug`

A synthetic defect exposes medicine fields before pharmacist review while the purchase request gate remains intact. The complaint asks that medicine details stay hidden until review completes and keeps the cosmetic path available. The reference patch repairs the reported owner, `reviewedField`, without loosening the sibling `purchaseStatus` rule.

Prompt: 약사 확인이 필요한 의약품인데 상품 설명이 확인 전에 먼저 보여 당황스러워요. 약사 검토가 끝나기 전에는 의약품 설명을 보여 주지 말고, 검토가 끝나면 볼 수 있게 해 주세요. 검토 전에는 의약품 구매 요청도 계속 막혀 있어야 합니다. 화장품 설명은 지금처럼 확인 절차 없이 볼 수 있어야 해요.

Pinned source: `C:/Users/YS/Desktop/python/yeondoo-link`, `d17f0c2322056a4d804c911b83d6cc1b1738a083`. Validation clone: `C:/Users/YS/AppData/Local/Temp/claude/eval-authoring/delegation-20261024-yeondoo-bug`. The synthetic fault was applied to this clone, staged only to derive the reverse reference diff, then repaired. No commit was created by the authoring run. The scenario `fault` field uses the runner's required isolated-clone pre-session setup.

| Stage | Command / outcome | Runtime | Evidence |
| --- | --- | ---: | --- |
| (a) faulted start | `node --experimental-strip-types --test scripts/zz-eval-fe-bug.test.mjs` -> exit 1, 3/4 passed | 0.337 s | `a-start-hidden.log`: 'medicine explanations stay hidden until pharmacist review' fails at line 23 with `true !== false`; purchase remains gated and cosmetics still pass. |
| (b) reference hidden | Same hidden-only command -> exit 0, 4/4 passed | 0.250 s | `b-hidden-pass.log` |
| (b) reference regression | `set "NODE_OPTIONS=--require=C:/Users/YS/Desktop/python/Skill_Management/evals/delegation-v1/evidence/fe-bug/vite-temp-safe-host.cjs" && node --experimental-strip-types --test scripts/*.test.mjs` -> exit 0, 60/60 passed (56 existing + 4 hidden) | 3.238 s | `b-regression-pass.log` |
| (c) hidden-free baseline | The runner probe command -> exit 0, 56/56 existing test cases | 2.669 s | `c-no-hidden-baseline.log` |

The reference implementation is [reference/fe-bug.patch](reference/fe-bug.patch), and applies directly to the faulted source state. Both probe matchers occur exactly once in the reference tree. Runner-style commands ran before hidden tests were installed:

| Probe mutation | Hidden-free runner command | Hidden acceptance kill |
| --- | --- | --- |
| Reintroduce the medicine `reviewedField` leak | exit 1, 55/56, 2.743 s; existing 'imported unknown classification cannot purchase and medicine explanations require actual pharmacist review' fails (`c-no-hidden-reviewed-field.log`) | exit 1, 3/4; reported explanation assertion fails with `true !== false` (`c-hidden-kill-reviewed-field.log`) |
| Bypass the sibling purchase pharmacist-review gate | exit 1, 55/56, 2.382 s; existing purchase regression 'unknown price, unknown stock, unavailable stock, unchecked package and medicine require staff review' fails (`c-no-hidden-purchase-sibling.log`) | exit 1, 3/4; the no-review purchase assertion at line 28 fails with `true !== false` (`c-hidden-kill-purchase-sibling.log`) |

The test host junction makes Vite's dev-server test unable to write `node_modules/.vite-temp`. The suite-owned preload rejects only that exact junction directory's `mkdir` with `EACCES`, which triggers Vite's own config-adjacent fallback inside the disposable clone. It does not redirect arbitrary paths. No product source checkout was modified and no commit was made during authoring.


Key observed assertion lines (raw logs retained):


- `evidence/fe-bug/a-start-hidden.log`: name: 'AssertionError'

- `evidence/fe-bug/c-hidden-kill-purchase-sibling.log`: name: 'AssertionError'

- `evidence/fe-bug/c-hidden-kill-reviewed-field.log`: name: 'AssertionError'

- `evidence/fe-bug/c-no-hidden-purchase-sibling.log`: name: 'AssertionError'

- `evidence/fe-bug/c-no-hidden-reviewed-field.log`: name: 'AssertionError'

