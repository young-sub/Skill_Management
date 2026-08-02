---
name: diagnose
description: Diagnose a current Harness v3 implementation or verification failure with a bounded root-cause loop.
---

# Diagnose — Harness v3

Use [the execution policy](references/goal-execution-policy.md) for evidence and retry boundaries.

1. Reproduce the exact observable failure with the smallest mapped check.
2. Minimize the affected surface and state a falsifiable hypothesis.
3. Instrument only the boundary needed to distinguish causes.
4. Identify the Root cause from evidence; do not expand into unrelated baseline debt.
5. Add the smallest Regression proof, observe RED, fix the root cause, and observe GREEN.
6. Reverify only Impacted checks unless new evidence expands the mapping or triggers Full.

Record failure, diagnosis, regression, retry, and result in the current `.work/goals/active/<work-id>/agent/evidence.jsonl`. Live/Eval remains separately authorized. Do not mutate tracker, global provider state, or unrelated work.
