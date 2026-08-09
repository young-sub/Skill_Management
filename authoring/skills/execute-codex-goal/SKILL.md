---
name: execute-codex-goal
description: Execute a default- or explicitly-authorized Core-First Harness Item contract with impact-selected verification and policy-selected commits.
---

# Execute Codex Goal

Use [the runtime](scripts/core_harness.py), [the contract schema](schemas/contract.schema.json), [the work schema](schemas/work.schema.json), [the testing policy](references/testing-policy.md), and [the execution policy](references/goal-execution-policy.md). The authorized contract is authority; a host Goal is optional tracking state.

1. Verify default or explicit authorization against a freshly rendered canonical Review and fail closed on veto, contract/Review drift, unresolved decisions, unknown legacy project declarations, or incomplete lifecycle transactions.
2. Capture the current branch and commit as base and record the dirty baseline. Create a feature branch only when repository policy or the reviewed work requires one; never assume the default branch.
3. Select the first dependency-ready core Item; optional work cannot displace incomplete core behavior.
4. For a behavior change, observe the smallest relevant RED, implement the core behavior, observe GREEN, and refactor. For a behavior-preserving move, use baseline/equivalent GREEN.
5. Resolve Impacted tests from exact behavior, mapped paths/dependencies, cross-cutting rules, and the Feature selector. Unknown relevant impact blocks Item completion; Full runs only on a configured trigger.
6. When repository policy or the human requests commits, commit only independently reviewable verified paths and exclude dirty baseline files. Record concise evidence in `.work/goals/active/<work-id>/agent/evidence.jsonl`.
7. Apply an unambiguous low-risk user delta immediately as `approved_amendment`. Request focused approval only for material public contract, acceptance, architecture, destructive, security/privacy, secret, irreversible, or costly external change.

Use `diagnose` only for the current failure and affected surface. Stop at high-risk boundaries or a genuine blocker, not for unrelated existing debt.
