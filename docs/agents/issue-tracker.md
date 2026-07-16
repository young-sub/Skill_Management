# Issue Tracker Config

## Tracker Mode

- Mode: `local_markdown`
- Canonical active tracker: `docs/plans/<owner-slug>/<feature-slug>/` (gitignored)
- GitHub Issue/PR publishing: disabled for this repository unless the owner later changes policy.
- Migration policy: never change tracker mode silently.

## Tracker Channel And Access Path

- The gitignored `agent-env.<slug>.md` declares tracker channel `none` for this repository.
- Git SSH fetch/pull/push is an independent code channel and is not disabled by tracker mode.
- `publish` remains outside `auto`, but is not needed while the channel is `none`.

## Durable Records

- Local Work Packet: `docs/plans/<owner-slug>/<feature-slug>/work-packet.md`.
- Local planning artifacts: sibling `spec.md`, `tickets.md`, and optional `issues/` records.
- The entire `/docs/plans/` tree is gitignored and owner/feature namespaced for parallel work.
- Decisions and source-of-truth updates: tracked docs and ADRs when introduced.
- `.scratch/`: ephemeral drafts, logs, and intermediate outputs only.
- Because the complete local plan tree is gitignored, mirror settled shared decisions,
  acceptance criteria, and verification evidence into tracked source-of-truth docs, ADRs, or a PR
  body when one exists; do not rely on generated plan files as the only cross-clone record.
- Publish state axes remain independent: `git_publish_state` and `tracker_publish_state`.

## Local Work Packet Contract

Each record includes `title`, `status`, `labels`, `created_at`, Korean summary, goal, non-goals,
decisions, slices, acceptance criteria, verification, risks, implementation contract, phase handoff
capsule, and close evidence. Use `ready-for-agent` only when blocking decisions are closed.

When `to-spec` or `to-tickets` says "publish to the issue tracker", it must resolve this configured
mode. In `local_markdown`, it writes inside the gitignored plan directory above, verifies the whole
directory is ignored, and
performs no `gh`, connector, or remote PR operation. `to-tickets` writes blocking edges as text in
dependency order.

## Branch Policy

- Base/integration branch: `main`, resolved from `refs/remotes/origin/HEAD`.
- Protected branches: `[main]`; never auto-push or auto-merge into them.
- Suggested implementation branch: `wp-<work-packet-id>-<slug>`.
