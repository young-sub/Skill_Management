---
name: close-goal
description: Close a Harness v3 contract Item by Item, render the Korean Result Review, and transition retained work safely.
---

# Close Goal — Harness v3

Use `scripts/core_harness.py`, `scripts/render_result_review.py`, and the bundled schemas/templates.

1. Match Result Items to Design Item IDs and order. Each Item needs observable implementation, relevant check results, Done status, and planned-versus-actual delta.
2. Require Impacted checks for that Item. Require Full only when cumulative impact matches a configured trigger or the human requested it; otherwise record `not_required` with the matched rule.
3. A failed or required-but-unrun check blocks only the affected Item. Unresolved impact blocks completion. A material delta needs focused approval.
4. Update only mapped durable documents whose current truth changed. Ordinary work creates no tracked plan, decision, Review, or evidence archive.
5. Render Korean `review/result.html` with the same Item identities and behavior visual grammar. Do not expose raw Markdown, hashes, frontmatter, detailed logs, or audit appendices.
6. Write `completed_at`, `retain_until`, and `delete_after` to `work.json`, then move the intact active directory to `.work/goals/completed/YYYY-MM/<work-id>`.
7. Re-resolve captured base movement and protection. Merge locally only when repository policy authorizes it and the base is unprotected; otherwise leave a verified branch and handoff. Never auto-push.
