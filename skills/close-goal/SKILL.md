---
name: close-goal
description: Close a Harness contract Item by Item, persist result evidence, and transition retained work safely.
---
<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/skills/close-goal/SKILL.md -->
<!-- Source-SHA256: bf150eb9a1374a585c139f7238a667ac825cfcf79684c128606183e707c7e93a -->


# Close Goal

Use [the runtime](scripts/core_harness.py), [the contract schema](schemas/contract.schema.json), [the work schema](schemas/work.schema.json), [the testing policy](references/testing-policy.md), and [the documentation policy](references/documentation-policy.md).

1. Match Result Items to Design Item IDs and order. Each Item needs observable implementation, relevant check results, Done status, and planned-versus-actual delta.
2. Require Impacted checks for that Item. Require Full only when cumulative impact matches a configured trigger or the human requested it; otherwise record `not_required` with the matched rule.
3. A failed or required-but-unrun check blocks only the affected Item. Unresolved impact blocks completion. A material delta needs focused approval.
4. Update only mapped durable documents whose current truth changed. Ordinary work creates no tracked plan, decision, HTML Review, or evidence archive.
5. Persist the validated machine evidence as `result.json`; provide the human-facing Result only as the final chat summary.
6. Write `completed_at`, `retain_until`, and `delete_after` to `work.json`, then move the intact active directory to `.work/goals/completed/YYYY-MM/<work-id>`.
7. Re-resolve captured base movement and protection. Merge locally only when repository policy authorizes it and the base is unprotected; otherwise leave a verified branch and handoff. Never auto-push.
