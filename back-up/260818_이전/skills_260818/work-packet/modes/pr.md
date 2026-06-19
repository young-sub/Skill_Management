# Mode: pr

Create or update the implementation PR after implementation has produced a diff, unless `--draft-pr-first` already created the PR.

Each implementation branch/worktree owns exactly one PR-sized Work Packet. Do not let parallel sessions update the same PR body, linked issue state, labels, or close report.


## Required reads

- Always read: this file, the `Phase handoff capsule` if present, Work Packet or issue sections needed for PR creation, implementation diff/verification evidence summaries, and these sections via `scripts/read-reference-section.py`: `Metadata-first Tracker I/O`, `Tracker and durable record policy`, `Korean reporting and summary policy`, `Branch naming policy`, `Bounded auto approval policy`, and `Verification evidence`.
- Read if needed: PR metadata/comments when updating an existing PR, repo branch/CI policy, and shared-doc update status.
- Template: `templates/pr-body.md`.
## Prerequisites

- There is an implementation branch or diff.
- Configured tracker reference exists; when GitHub Issues are configured, the parent issue exists.
- Local verification evidence exists, or missing checks are clearly reported.
- Shared-doc updates required before implementation have been applied or are covered by scoped overrides.

## Process

1. Read order: `Phase handoff capsule`; `git status --short`; `git diff --stat` or changed filenames; exact verification evidence capsule; only risky or disputed hunks; tracker/PR metadata and only sections needed for the current gate; listed reference sections via `scripts/read-reference-section.py`; `templates/pr-body.md`. Full raw diff, full logs, or full tracker/PR bodies are escalation, not default.
2. Inspect branch, commits, default branch, and existing PR metadata.
3. Do not proceed if unrelated dirty changes would mix with the PR.
4. In `pr`, update only PR metadata, body, labels, review state, and linked tracker surfaces. Source, tests, docs, commits, and branch content remain owned by `run`; return to `run` for code or doc changes.
5. Use the repo branch convention; otherwise use `wp-<work-packet-id>-<slug>` or `issue-<issue-number>-<slug>`.
6. Link to the parent GitHub Issue when GitHub Issues are configured; use a local Work Packet path only when local markdown is explicitly configured.
7. Use closing keywords only if the PR fully resolves the issue and targets the default branch. Otherwise use `Related to #N` or `Part of #N`.
8. Include Korean non-normative summary and English canonical sections. Follow the `Korean reporting and summary policy` reference section and `templates/korean-summary.md`; for PRs, emphasize implemented impact, the reviewer decision made easier, and the scope boundary that matters for review. Include `### 핵심 구현 결과` under the Korean summary: leave it empty or `TBD: fill after implementation is complete` for initial/draft PR creation, and fill it when updating the PR after implementation is complete.
9. Include Implementation Contract summary, scoped overrides used, and shared-doc updates applied/deferred/rejected.
10. Create or update the PR from a body file or short-output path when possible; retain only PR URL/number/state/head/base refs and `published_body_ref`. If GitHub CLI is unavailable, output the exact command and PR body instead of pretending the PR was created.
11. In `auto`, treat routine PR create/update prompts as approved under the bounded auto approval policy unless `--no-auto-pr` is present.
12. If PR or linked issue state appears stale because another session modified it, stop and ask the orchestration lane to reconcile.
13. Update the `Phase handoff capsule` with PR URL/state/head ref, `published_body_ref`, tracker/PR mutation metadata, verification evidence pointer, next mode, and next stop condition. Do not fetch the full PR body after creation only to confirm metadata.

## PR body must include

Use `templates/pr-body.md`.

## Output only

1. Branch
2. PR URL or exact command to create it
3. Linked issue/tracker reference
4. Verification status
5. Shared-doc update status
6. Next command
