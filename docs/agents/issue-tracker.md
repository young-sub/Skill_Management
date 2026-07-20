# Issue Tracker Config

## Tracker Mode And Channel

- Mode: `local_markdown`.
- Canonical tracker: `docs/work-packets/<owner-slug>/`.
- Env profile: gitignored root `agent-env.<slug>.md`, created by `$work-packet init` and matched to `git@github.com:young-sub/Skill_Management.git`.
- Tracker channel is `none` for the core local workflow and is never discovered by network probing.
- The code channel remains SSH. Optional live Issue/PR publication requires a later explicit profile change and human-triggered `publish` step.
- Do not migrate tracker mode without explicit approval.

## Durable Records

- Active local pending records: `docs/work-packets/<owner-slug>/`.
- Published immutable archive: `docs/archive/work-packets/<owner-slug>/`.
- Completed V2 implementation record: `docs/archive/plans/harness_v2_implementation_plan.md`.
- Completed plan and design archive: `docs/archive/`.
- Decisions: tracked plans and future `docs/adr/` records.
- `.scratch/` and `.work/`: ephemeral only, never durable sources.

Track `git_publish_state` (`local_only`, `committed`, `branch_pushed`) independently from `tracker_publish_state` (`local_pending`, `issue_published`, `pr_published`, `handoff_pending`).

## Issue And PR Policy

- Titles and canonical sections are English.
- Add `## Korean Summary (non-normative)` at the top for review speed; English canonical sections and source-of-truth docs prevail on conflict.
- Use closing keywords only for a fully resolving PR against `main`.
- When the configured channel is unavailable, emit the exact command and body, mark `handoff_pending`, and do not claim publication.
