---
name: execute-codex-goal
description: Execute a default- or explicitly-authorized Core-First Harness Item contract with impact-selected verification and complete functional-unit commits.
---

# Execute Codex Goal

Use [the runtime](scripts/core_harness.py), [the contract schema](schemas/contract.schema.json), [the work schema](schemas/work.schema.json), [the testing policy](references/testing-policy.md), and [the execution policy](references/goal-execution-policy.md). The authorized contract is authority; a host Goal is optional tracking state.

1. Verify default or explicit authorization against the canonical contract and fail closed on veto, contract drift, unresolved decisions, unknown legacy project declarations, or incomplete lifecycle transactions. Existing active work with a legacy HTML digest may continue only when its retained Review still matches that digest; never rewrite or delete it automatically.
2. Capture the current branch and commit as base and record the dirty baseline. Create a feature branch only when repository policy or the reviewed work requires one; never assume the default branch.
3. Select the first dependency-ready core Item; optional work cannot displace incomplete core behavior.
4. For a behavior change, observe the smallest relevant RED, implement the core behavior, observe GREEN, and refactor. For a behavior-preserving move, use baseline/equivalent GREEN.
5. Inspect changed functions, branches, state transitions, configuration rules, direct callers, and public behavior with the existing diff and symbol searches. Record `changed_logic`, `affected_behaviors`, `scope`, and `reason`; select exact tests from that logic assessment. Treat path mappings, Feature commands, and Full triggers only as candidates. Unknown impact blocks completion without auto-Full; Full runs only for cross-cutting logic impact or an explicit human request.
6. A commit unit is the smallest complete functional unit that works when checked out by itself, including required source, tests, docs, schemas, and generated resources. Commit every such unit after its mapped verification passes and exclude dirty baseline files. Group coupled Items into one commit; split only independently working units. Never create an intentionally broken intermediate commit. Create independent Item worktrees only through the runtime-owned `/.worktree/` directory; callers never choose an external path. Record concise evidence in `.work/goals/active/<work-id>/agent/evidence.jsonl`.
7. Apply an unambiguous low-risk user delta immediately as `approved_amendment`. Request focused approval only for material public contract, acceptance, architecture, destructive, security/privacy, secret, irreversible, or costly external change.

Use `diagnose` only for the current failure and affected surface. Stop at high-risk boundaries or a genuine blocker, not for unrelated existing debt.
