---
name: execute-codex-goal
description: Execute an approved Core-First Harness v3 Item contract with impact-selected verification and per-Item commits.
---

# Execute Codex Goal — Harness v3

Use `scripts/core_harness.py` and the bundled contract/work schemas. The approved contract is authority; a host Goal is optional tracking state.

1. Verify the internal approval bundle and fail closed on contract/Review drift, unresolved decisions, unsupported version, mixed cohort, or incomplete legacy transaction.
2. Capture the current branch and commit as base, record the dirty baseline, and create the configured feature branch. Never assume the default branch.
3. Select the first dependency-ready core Item; optional work cannot displace incomplete core behavior.
4. For a behavior change, observe the smallest relevant RED, implement the core behavior, observe GREEN, and refactor. For a behavior-preserving move, use baseline/equivalent GREEN.
5. Resolve Impacted tests from exact behavior, mapped paths/dependencies, cross-cutting rules, and the Feature selector. Unknown relevant impact blocks Item completion; Full runs only on a configured trigger.
6. Commit only the verified Item paths, excluding dirty baseline files. Record evidence in `.work/goals/active/<work-id>/agent/evidence.jsonl`.
7. Apply an unambiguous low-risk user delta immediately as `approved_amendment`. Request focused approval only for material public contract, acceptance, architecture, destructive, security/privacy, secret, irreversible, or costly external change.

Use `diagnose` only for the current failure and affected surface. Stop at high-risk boundaries or a genuine blocker, not for unrelated existing debt.
