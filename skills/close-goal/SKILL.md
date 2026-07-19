---
name: close-goal
description: Validate Harness completion gates, create a human-readable Completion Review, and archive eligible ephemeral work without deletion.
---

# Close Goal

Use after every approved Plan is complete and implementation verification has been recorded. Review the result across Spec, Standards, Maintainability, Architecture, and Diagnostics before invoking the deterministic helper.

## Inputs

Prepare JSON files with `findings` and `checks` arrays. Each finding has `severity` and `title`. Each check has `kind` and `status`; include exact commands and evidence when available. Treat unrun Live or Eval checks as `unverified`, never as passed or failed.

Run:

```text
python scripts/close_goal.py --contract-root <.work/active/work-id> --source-root <repository> --findings <findings.json> --verification <verification.json> --current-month <YYYY-MM>
```

## Gates

- Any High finding blocks completion and archive.
- Any git-tracked text document referencing `.work/` blocks completion. Move important decisions and structural knowledge into durable repository documents, then rerun the gate.
- Never claim an unrun check passed or failed.
- Never overwrite an existing archive destination or delete work.

On success the helper creates `RESULT.md` and escaped scriptless `artifacts/completion-review.html`. It creates `HANDOFF.md` only when `.harness/project.yaml` sets `handoff.target` to `local` or `both`, then moves the intact work directory to `.work/archive/YYYY-MM/<work-id>`.

The Completion Review is a decision aid. The Markdown result and durable repository documentation remain authoritative.
