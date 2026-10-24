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
