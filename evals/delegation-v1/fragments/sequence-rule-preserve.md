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
