---
name: diagnose
description: Investigate a reproducible implementation or verification failure, distinguish its root cause from environment limits, and apply a focused fix when authorized. A Harness contract is optional.
---
<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/skills/diagnose/SKILL.md -->
<!-- Source-SHA256: 7ddc086ef25f270ad3580d1f0ee7d7622e809457cedfb38c2804ebb1b6ba1e67 -->


# Diagnose

Use existing repository checks and diagnostics. Consult [execution policy](references/goal-execution-policy.md) when the failure belongs to an active Harness contract.

1. Reproduce the reported input/entry point and failing output with the smallest relevant check. Confirm the current checkout, runtime, and endpoint when using existing logs or a running server.
2. Trace the failing behavior through its callers and state owner. Form a falsifiable hypothesis; instrument only what distinguishes likely causes. Separate code failure, missing evidence, and environment failure.
3. If a retry produces the same evidence, change the hypothesis or check instead of repeating it. Honor loaded manual-disable records. Escalate scope only when the observed cause crosses the current boundary.
4. For an authorized fix, add the smallest regression proof when it prevents recurrence, observe RED when that evidence is useful, fix the shared root cause, and observe GREEN. Reuse existing evidence when it already proves the behavior; do not add a test solely to document a one-off diagnosis. A diagnosis-only request ends with evidence and the proposed fix. No contract creation is required for a small repair.
5. Recheck affected public behavior and relevant sibling callers. Expand verification only for newly affected logic or an explicit request; unrelated baseline debt is not a completion gate.

For active contract work, append only new failure/cause/fix/check evidence to `.work/goals/active/<work-id>/agent/evidence.jsonl`; otherwise a concise task record or chat is enough. Reuse permission for covered live checks; obtain missing authorization only for real external effects, cost, or sensitive changes. Report unresolved causes without inventing certainty.
