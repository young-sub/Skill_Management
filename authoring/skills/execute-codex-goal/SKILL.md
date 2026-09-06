---
name: execute-codex-goal
description: Execute an existing authorized Harness Item contract, verify affected behavior, and commit complete functional units. Does not require a contract or Harness setup for ordinary development outside this workflow.
---

# Execute Codex Goal

Use [the runtime](scripts/core_harness.py) with the existing contract; a host Goal is optional tracking state. Read [testing policy](references/testing-policy.md) for impact selection, [execution policy](references/goal-execution-policy.md) for amendments/commits, and the [contract](schemas/contract.schema.json) or [work](schemas/work.schema.json) schema only when constructing or diagnosing those records.

1. Verify contract authorization and reuse existing user permission within scope. Veto, drift, unresolved decisions, unknown legacy declarations, and incomplete transactions block dependent work. Retained legacy HTML must match its stored digest; do not rewrite it to pass validation.
2. Use `start` to capture the actual branch, source commit, and dirty baseline; resume existing work without resetting that baseline. Create a feature branch only when policy or the work requires it.
3. Select the first dependency-ready core Item; optional work cannot displace incomplete core behavior.
4. For non-trivial behavior changes, observe a focused RED before the fix where feasible, then GREEN; explain a concrete exception. Behavior-preserving moves use baseline/equivalent GREEN. Test observable outcomes, not trivial wording or implementation shape.
5. Inspect changed logic and direct callers with existing diff/symbol searches. Record `changed_logic`, `affected_behaviors`, `scope`, and `reason`; select exact relevant checks. Path mappings, Feature commands, and Full triggers are candidates. Unknown impact requires investigation, not automatic Full. Full runs for cross-cutting logic impact or an explicit request. Stop expanding checks after required checks pass unless new evidence changes scope.
6. Actually run the selected checks and capture commands, outcomes, and relevant runtime/browser/print evidence in `.work/goals/active/<work-id>/agent/evidence.jsonl`. A check selection, success flag, or Result validator does not execute tests or prove product behavior.
7. Commit complete functional units with required source, tests, docs, schemas, and generated resources after mapped verification. Keep coupled Items together and preserve the dirty baseline. Use runtime-owned `/.worktree/` paths only for independent work whose benefit exceeds coordination cost.
8. Apply an unambiguous low-risk descriptive delta as `approved_amendment`. `amend` preserves veto, identity, decisions, acceptance criteria, dependencies, scope, risks, and priority. Structural/material revisions use a revised canonical contract and `authorize --intent explicit_approve` after matching user authorization; a covered mechanical edit needs no new human confirmation. Never remove risks merely to obtain default authorization.

Load `.harness/environment-exceptions.json` once per task when present; refresh after relevant environment changes. Honor `skip_until_manual_reenable`, use its fallback, and retain capability/failure/unverified-scope evidence for `result.json` and final chat. Environment failure is `verification_unavailable` or `execution_blocked`.

Use `diagnose` for an unexplained current failure. Continue authorized independent work around a blocker; do not make unrelated debt a completion gate. Finish through `close-goal` when the contract's required behavior and verification are complete.
