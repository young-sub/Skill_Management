# AGENTS.md

## Scope

- Applies to this repository, which is the managed source for installable agent skills.
- Global agent instructions remain authoritative; this file contains repo-specific evidence only.

## Repo Map

- `skills/`: active skill packages; each package is rooted at `SKILL.md`.
- `docs/plans/`: gitignored agent-local plans, specs, tickets, and implementation notes.
- `docs/agents/`: Work Packet control-plane configuration.
- `docs/archive/`: tracked archive only for workflows that explicitly publish remote records; local
  personal plans remain under ignored `docs/plans/`.
- `back-up/`: historical snapshots; exclude from active-skill validation and do not edit for normal work.

## Source Of Truth

- Workflow: `docs/agents/workflow.md`
- Tracker: `docs/agents/issue-tracker.md`
- Triage states: `docs/agents/triage-labels.md`
- Domain and ownership: `docs/agents/domain.md`
- Upstream ownership/provenance: `UPSTREAMS.md`

## Commands

- Work Packet audit: `python skills/work-packet/scripts/audit-work-packet-skill.py`
- Matt skill audit: `python scripts/audit_matt_skills.py`
- Repository search: exclude `back-up/` unless historical evidence is explicitly required.

## Work Tracking

- Tracker mode: `local_markdown`; GitHub Issues and PRs are not required for this repository.
- Use `$work-packet` for non-trivial capability work.
- Active local record: `docs/plans/<owner-slug>/<feature-slug>/` (gitignored).
- `.scratch/` is ephemeral only and never the durable tracker.
- Base/integration branch: `main`; treat `main` as protected and require human action before direct push or merge.
- Suggested implementation branch: `wp-<work-packet-id>-<slug>`.

## Agent / Skill Use

- Use `$project-agent-bootstrap` when this control plane drifts.
- Keep `work-packet` and `project-agent-bootstrap` local-owned; never overwrite them from upstream.
- Follow `UPSTREAMS.md` once present for skill ownership and upstream provenance.
- Follow `UPSTREAMS.md` for the active catalog, atomic replacements, and update policy.

## Repo Constraints

- Do not commit `agent-env.*.md`; it is local access-routing state.
- Do not edit `back-up/` as part of active skill maintenance.
- Do not add an automated upstream sync daemon, package manager, or generator unless separately approved.
- Remote tracker publishing, deployment, destructive cleanup, and protected-branch writes require explicit approval.

## Verification And Done

- Run the Work Packet audit plus the active plan's static and behavior smoke checks.
- Report commands, results, skipped checks, unverified assumptions, and remaining risks.
- Mirror settled shared decisions into tracked source-of-truth docs; personal plan files remain ignored.
