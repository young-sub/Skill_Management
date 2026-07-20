---
name: close-goal
description: Validate Harness completion gates, create a human-readable Completion Review, and archive eligible ephemeral work without deletion.
---

# Close Goal

Use after every approved Plan is complete and implementation verification has been recorded. Review the result across Spec, Standards, Maintainability, Architecture, and Diagnostics before invoking the deterministic helper.

## Inputs

Prepare JSON files with `findings` and `checks` arrays. Each finding has `severity` and `title`. Targeted, Feature, Fast, and Full must each appear exactly once with `status: passed`, a nonempty exact command and evidence, and `returncode: 0`. Treat unrun Live or Eval checks as `unverified`, never as passed or failed.

Run:

```text
python scripts/close_goal.py --contract-root <.work/active/work-id> --source-root <repository> --findings <findings.json> --verification <verification.json> --current-month <YYYY-MM>
```

## Gates

- Any High finding blocks completion and archive.
- The generated Contract engine must confirm the canonical approved hash, required sections, and DAG. Every GOAL Plan, or the SPEC runtime state, must be `completed`.
- Missing, duplicated, failed, or evidence-free Targeted, Feature, Fast, or Full verification blocks completion.
- Any git-tracked text document referencing `.work/` blocks completion. Move important decisions and structural knowledge into durable repository documents, then rerun the gate.
- Failure to enumerate tracked files is a blocking gate, not absence of references.
- Never claim an unrun check passed or failed.
- Never overwrite an existing archive destination or delete work.

On success the helper creates `RESULT.md` and escaped scriptless `artifacts/completion-review.html`. It creates `HANDOFF.md` only when `.harness/project.yaml` sets `handoff.target` to `local` or `both`, then moves the intact work directory to `.work/archive/YYYY-MM/<work-id>`.

The Completion Review is a decision aid. The Markdown result and durable repository documentation remain authoritative.
