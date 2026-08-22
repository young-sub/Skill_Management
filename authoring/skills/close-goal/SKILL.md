---
name: close-goal
description: Close a Harness contract Item by Item, persist result evidence, and transition retained work safely.
---

# Close Goal

Use [the runtime](scripts/core_harness.py), [the contract schema](schemas/contract.schema.json), [the work schema](schemas/work.schema.json), [the testing policy](references/testing-policy.md), and [the documentation policy](references/documentation-policy.md).

1. Match Result Items to Design Item IDs and order. Each Item needs observable implementation, relevant check results, Done status, and planned-versus-actual delta.
2. Recompute Impacted scope from every Git change since the captured source commit and the recorded logic assessment. A stale changed-path set blocks close. Require Full only for cross-cutting logic impact or an explicit human request; path triggers remain warnings.
3. A failed or required-but-unrun check blocks only the affected Item. Missing, unknown, or unexplained logic impact is `unresolved_logic_impact` and blocks completion. A material delta needs focused approval.
4. Update only mapped durable documents whose current truth changed. Ordinary work creates no tracked plan, decision, HTML Review, or evidence archive.
5. Persist the validated machine evidence as `result.json`; when a Skill/plugin/Harness capability could not run, include its name, intent, failure reason, fallback, disable method, and remaining unverified scope. Provide the human-facing Result only as the final chat summary.
6. Write `completed_at`, `retain_until`, and `delete_after` to `work.json`, then move the intact active directory to `.work/goals/completed/YYYY-MM/<work-id>`.
7. Re-resolve captured base movement and protection. Merge locally only when repository policy authorizes it and the base is unprotected; otherwise leave a verified branch and handoff. Never auto-push.
