# Delegated-work verification — 0.1.86 / 0.1.87

The user defined the core value on 2026-10-23: let an agent take on many tasks and let the
user see and trust the results. It covers six capabilities: verification visibility, feedback
and self-improvement, the UI style guide, verification guides, root cause with real
guardrails, and keeping only checks that catch defects. This round implements the seven
improvements from the independent re-review. They were judged with fixed natural-language
scenarios on real projects, using installed plugins (Claude Code, two Codex homes), not
fixtures. Raw: `.work/scenario-gate/`, `.work/review-20261023/`.

## Implemented

| # | Change | Where | Focused proof |
| --- | --- | --- | --- |
| 1 | Hooks decode UTF-8 payload bytes; `--report` and the gate runner write UTF-8; `maintain` handles unconfigured projects | `workflow_context.py`, `completion_guard.py`, `project_workflow.py` | `test_workflow_robustness`: 3 project shapes × lookup/resume/audit/maintain × JSON/summary/report; raw-UTF-8 Korean hook payloads |
| 2 | Unconnected projects report `connection: NOT_CONNECTED` (read-only exit 3); report and hook say so and name setup | same | same suite |
| 3 | Feature `scope` (NOT_REQUIRED / APPLIES, reason, decider); `business_value` as a human decision (MEASURED / PROXY / DEFERRED); *Questions for the user* in report and summary | `project_workflow.py`, `workflow-obligations.md` | `test_scope_business` (fails when the features are disabled) |
| 4 | Automatic prevention needs `bypass_pointers` or `bypass_absence` with inspected Feature sources; diagnose enumerates alternate paths and records feedback | `project_workflow.py`, `diagnose` | `test_project_workflow` feedback contract |
| 5 | REVIEW_ONLY for Agent-only cells; copied REQUIRED analysis rejected; Stop guard counts shell writes as edits; controlled-fault probe guidance | same, `project-verification.md` | `test_scope_business`, `test_completion_guard` (old guard fails 4 new cases) |
| 6 | Deterministic prompt `route`; paid scenario gate `scripts/run_skill_scenarios.py` with `tests/scenarios/skill_routing.json` | hook, runner | 13 observed prompts routed as expected (`fixtures/route_prompts.json`); `test_skill_scenarios` |
| 7 | Setup completes only when committed in the product repo, with a lean contract; 0.1.87 also commits every cell decision to Feature `scope` | `setup-project-verification` | scenario below |

The affected regression set passed after the final edits: 320 tests + 1 updated, plus
distribution validation, resource drift and package/marketplace tests. Full was not run.

## Scenario gate, installed 0.1.86 (all PASS)

| Scenario (project) | Expected | Invoked | Probes / notes | Cost |
| --- | --- | --- | --- | --- |
| trivial README line (Labeler) | none | none | — | $0.23 / 40 s |
| show what is verified (Labeler) | agent-workflow | agent-workflow | rendered the report with 0 commands; said NOT_CONNECTED; asked which flow to connect | $0.67 / 100 s |
| customer complaint, planted C2 (Labeler) | diagnose | diagnose | reintroduced fault **caught**; settle-order bypass **caught** (missed in the 0.1.85 run); stated that no feedback record exists and offered setup | $0.60 / 198 s |
| UI consistency (Labeler) | agent-workflow | agent-workflow | used `ui-ux-upgrade.md`, aligned to the shared modal footer, updated the guide, browser-verified at 1440/390 | $1.90 / 487 s |
| resume previous work (yeondoo-link) | recall | recall | found the recorded gap list and implemented it in the clone (5 mutant-killing tests, `--surface` token); measured 7 taps against the 2–4 business target and escalated the judgement | $3.09 / 592 s |
| connect free-tier verification (Labeler) | setup-project-verification | setup-project-verification | committed `d505fd4`: business cells PASS via executable checks, architecture REVIEW_ONLY, own probes 8/8 server + 4 UI after adding 2 regressions, 189-line contract (previously 704), asked for business value with drafted options | $6.74 / 1676 s |

Before 0.1.86, the same prompts invoked no Skill for "show what is verified" (twice), the
complaint and the UI request, and the alternate settle path was unprotected.

## Real-repository results

- **Skill_Management:** 132 UNDECIDED cells → 0 (FE/BE-API NOT_REQUIRED, Domain APPLIES
  from the Feature Map). The user's business value is recorded as PROXY with deferred
  workload measurement. The report has no open questions.
- **Labeler (original, `wp-20261005-local-changes`):**
  - Before: unconnected (0 Features).
  - The free-tier connection was cherry-picked (`e6d1184`). The user's business value
    decision (free-to-paid conversion, measurement deferred to the first post-launch
    settlement) and durable APPLIES scope are recorded (`2f4de89`).
  - The plugin's prepare/execute in the original ran `free-tier-api` PASS. The first
    `free-tier-e2e` run without the documented `PLAYWRIGHT_MODULE` exited 1 and stayed
    UNKNOWN, not PASS. With it, the run passed with a real browser and isolated local D1.
  - Six cells stay APPLIES until a task records its review. Nothing was pushed.
- **yeondoo-link:** the user's business value (2–4 taps, measurement deferred until a
  tap-count observation exists) is recorded uncommitted with the gap list. The remaining 12
  scope questions are listed in the report.

## Findings fixed during verification

- The 0.1.86 setup kept cell applicability only in ignored task state, so the original
  checkout showed six UNDECIDED cells. 0.1.87 makes setup commit every decision to `scope`.
- Heredoc-fed scripts placed backspace bytes in a route regex; the UTF-8 fixture test
  exposed the gap and the bytes were repaired.
- The scenario runner's own dry-run printed cp949; its test caught the same defect class
  as item 1.

## Limits

- Each scenario ran once; model variance is not measured. The gate is paid and manual.
- Codex hook trust for the Stop guard and route was not observed natively.
- Labeler product defects stay unfixed and recorded (`docs/검증_공백_기록.md`): PortOne
  `redirect: "error"`, expired lots shown as usable, date-fixed pretest, copy without a
  notice.
- Architecture cells in the new connections are REVIEW_ONLY except where a rule exists.

## 0.1.87 rerun: setup persists decisions

Scenario `connect-translation-credits` (Labeler original at `2f4de89`, installed 0.1.87)
invoked `setup-project-verification`. It committed three units (`bd59749`, `2f0c69e`,
`05a7c83`), and the new Feature `translation-credits` carries all six cells in committed
`scope`. A project-level `audit --report` with no task state shows both Features'
decisions and no open questions; business value is inherited from the recorded project
decision. The Agent ran 22 controlled-fault probes. Six initially survived, so it added
regressions, and 20 now fail the registered checks; the two survivors are function-level
re-checks shadowed by middleware. Architecture is ISSUES with an open finding: the credit
formula is duplicated in four places. It reported two product decisions. Cost was
$9.54 over 2173 s; the shared contract file is 468 lines for two Features. This
connection remains in the scenario clone and was not applied to the original.
