---
name: close-goal
description: Finish an existing Harness contract by reconciling actual Item evidence, cumulative impact, durable docs, and retained work state. Use after implementation, not as a mandatory ceremony for ordinary small edits.
---

# Close Goal

Use the `close` command in [the runtime](scripts/core_harness.py). Consult [testing policy](references/testing-policy.md), [documentation policy](references/documentation-policy.md), and the [contract](schemas/contract.schema.json)/[work](schemas/work.schema.json) schemas only for the affected closing requirements.

1. Match Result Items to contract IDs/order, planned tests, and Done criteria. Reconcile observable implementation, actual check results, and planned-versus-actual deltas. Result validation checks consistency; it does not run commands or authenticate submitted evidence. Inspect the underlying evidence before claiming completion.
2. Recompute cumulative Impacted scope from every Git change since the captured source commit. Reuse still-current check evidence; rerun only when relevant code, conditions, acceptance criteria, or required scope changed. Full requires cross-cutting logic impact or an explicit request; path triggers are warnings.
3. Failed or required-but-unrun checks leave affected Items incomplete. Unknown impact needs investigation. Reuse existing authorization for material deltas within scope; ask only about an uncovered decision or risk. Do not erase failures to close the contract.
4. Update mapped durable docs only where current truth changed. Prepare `result.json` with capability failure, fallback, disable method, and remaining unverified scope when relevant. Ordinary work creates no tracked plan, HTML Review, or evidence archive.
5. Invoke `close` with the contract, result, and cumulative impact. It validates the records, persists evidence and retention dates, then moves intact work to `.work/goals/completed/YYYY-MM/<work-id>`. `complete` is an optional validation-only preflight, not a required preceding step or additional product check. Leave incomplete work active.
6. Re-resolve captured base movement and protection before any authorized integration. Leave a verified branch when integration is not authorized; never infer push/publish permission from completion. Summarize delivered behavior, checks, and material remaining limits in final chat.
