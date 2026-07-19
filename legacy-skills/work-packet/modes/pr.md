# Mode: pr

Finalize the implementation PR record as a local body file after implementation has produced a diff.
This mode manages the PR as a local document and does NOT call `gh`, the connector, or `mcp_pat`;
the live PR create/update is deferred to `publish`, which can batch several packets. Until then the
record carries `tracker_publish_state: local_pending`. The exception is an explicit `--draft-pr-first`
opt-in already reconciled in `run` when the channel is directly reachable.

Each implementation branch/worktree owns exactly one PR-sized Work Packet. Do not let parallel sessions update the same PR body, linked issue state, labels, or close report.


## Required reads

- Precondition (before any tracker action): resolve the access path via the `Access path resolution` reference section — read the env profile, match the git remote, detect the orchestrator, decide the tracker channel. STOP if the profile is absent.
- Always read: this file, the `Phase handoff capsule` if present, Work Packet or issue sections needed for PR creation, implementation diff/verification evidence summaries, and these sections via `scripts/read-reference-section.py`: `Access path resolution`, `Metadata-first Tracker I/O`, `Tracker and durable record policy`, `Korean reporting and summary policy`, `Branch naming policy`, `Bounded auto approval policy`, and `Verification evidence`.
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
10. Write the PR body to a local **body file** and record `tracker_publish_state: local_pending` plus the local body-file ref. Do not create or update the remote PR here; that is `publish` mode's job. Keep the body file publishable so the later live call is mechanical.
11. Do not auto-create the PR from `pr` mode, even under `auto`. `auto` produces the local PR record and stops short of publishing; live PR create/update happens only when the owner runs `publish`.
12. If PR or linked issue state appears stale because another session modified it, stop and ask the orchestration lane to reconcile.
13. Update the `Phase handoff capsule` with PR URL/state/head ref, `published_body_ref`, tracker/PR mutation metadata, verification evidence pointer, next mode, and next stop condition. Do not fetch the full PR body after creation only to confirm metadata.

## PR body must include

Use `templates/pr-body.md`.

## Output only

1. Branch
2. Local PR body-file path and `tracker_publish_state: local_pending`
3. Linked issue/tracker reference (local ref until published)
4. Verification status
5. Shared-doc update status
6. Next command (`publish` to create/update the PR, or `close`)
