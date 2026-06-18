# Mode: close

Close a completed Work Packet after implementation evidence and PR review surface exist.

`close` is orchestration-lane work by default. Do not run `close` in parallel for the same repo unless repo policy explicitly serializes state reconciliation elsewhere.


## Required reads

- Always read: this file, the `Phase handoff capsule` if present, linked issue/Work Packet and PR metadata/needed sections, final changed-file stats or commits, and these sections via `scripts/read-reference-section.py`: `Metadata-first Tracker I/O`, `Durable Body Ownership`, `Verification evidence`, `Final active-branch refresh policy`, `Korean reporting and summary policy`, and `Tracker and durable record policy`.
- Read if needed: shared-doc update targets, `Bounded auto approval policy` via `scripts/read-reference-section.py` when merge/issue closure is attempted under `auto`, and source files needed for scoped architecture review.
- Templates: `templates/close-report.md` for the detailed owner-surface close
  report and `templates/issue-close-capsule.md` for the short Issue close
  comment.
## Process

1. Read order: `Phase handoff capsule`; `git status --short`; `git diff --stat` or changed filenames; exact verification evidence capsule; only risky or disputed hunks/source files; Issue/PR metadata and only sections needed for the current gate; listed reference sections via `scripts/read-reference-section.py`; `templates/close-report.md`. Full raw PR bodies, full diffs, full logs, broad docs, or full `REFERENCE.md` are escalation, not default.
2. Require exact verification evidence. If missing, report unverified.
3. Record outcome, changed files or commits, verification evidence, docs updated, scoped architecture review result, diagnostics/operability evidence when relevant, remaining risks, and unverified assumptions. Follow the `Korean reporting and summary policy` reference section and `templates/korean-summary.md`; for close reports, emphasize completed outcome, tracker/PR state, remaining decision, and next action only when they affect follow-up.
4. Apply only confirmed shared-doc updates that reflect implemented behavior, verified architecture decisions, domain terminology, or verification evidence.
5. Do not apply speculative updates that were proposed during `init` but not validated by implementation.
6. Record each Proposed Shared Doc Update as applied, deferred, rejected, or no longer needed.
7. Persist each durable decision to its owner surface from `Durable Body Ownership`: parent issue for pre-run spec state, PR body for implemented evidence and final verification capsule, issue close comment for a short closure capsule, and tracked docs/ADRs for source-of-truth decisions. Link secondary surfaces instead of duplicating full close reports.
8. Treat a full close report in an Issue close comment as a duplication error. Issue close comments should follow `templates/issue-close-capsule.md`: `Closed by`, `Outcome`, `Verification`, `Remaining risk`, and `Next`.
9. Do not leave durable review knowledge only in `.scratch/`.
10. Reconcile artifact states: parent issue labels/status, PR draft/ready/merged/closed state, local seed draft status if any, and whether the linked issue is fully satisfied, partially satisfied, or blocked.
11. In manual mode, do not merge PRs, close PRs, or close issues unless the user explicitly approves or repo automation rules allow it.
12. In `auto`, merge or close only under the bounded auto approval reference section and auto-merge conditions.
13. If the session cannot continue safely, use `handoff` to produce a compact handoff.
14. If `close` is the terminal command, run final active-branch refresh from the reference section as the last step. If `next` will run afterward, defer refresh to `next`.
15. Update the `Phase handoff capsule` with close result, owner-surface durable mutations, `published_body_ref`, verification evidence capsule, remaining risks, next mode, and next stop condition.

## Output only

1. Outcome
2. Verification evidence
3. Docs updated
4. Shared-doc updates: applied/deferred/rejected
5. Architecture review result
6. Issue/PR/Work Packet state
7. Remaining risks
8. Close status
9. Active-branch refresh status, if run or skipped
10. Recommended next action
