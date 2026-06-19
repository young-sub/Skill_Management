# AGENTS.md

## Scope

- Applies to this repository.
- Global `AGENTS.md` governs generic agent behavior; this file contains repo-specific commands, source-of-truth docs, constraints, and workflow conventions.
- Before planning or editing a path with a nested `AGENTS.md`, read the nearest nested file.

## Repo Map

- Runtime/language/package manager: <evidence-backed summary>
- Main packages/surfaces: <short list>
- Primary entrypoints: <short list>

## Source Of Truth

- Agent workflow: `docs/agents/workflow.md`
- Tracker config: `docs/agents/issue-tracker.md`
- Triage labels/states: `docs/agents/triage-labels.md` or <not used>
- Domain/product context: `docs/agents/domain.md`
- Architecture: <path or `not configured`>
- ADRs/decisions: <path or `not configured`>
- Verification/runbook: <path or `not configured`>
- Active plan/roadmap: <path or `not configured`>

## Commands

- Install: `<command>`
- Build: `<command>`
- Test: `<command>`
- Typecheck: `<command>`
- Lint/format: `<command>`
- Run locally: `<command>`

## Work Tracking

- Tracker: <GitHub Issues | GitLab Issues | local markdown | existing tracker>
- Work Packet flow: use `$work-packet init|ready|issue|run|pr|close|next|auto` for non-trivial capability work.
- Durable record: <issue/PR, tracked docs, ADRs, implementation plan, or configured tracker>
- Branch convention: `<convention>`
- PR/MR convention: <short repo-specific convention>

## Agent / Skill Use

- Use `$project-agent-bootstrap` if this repo setup or `docs/agents/*` drifts.
- Use `$work-packet` for PR-sized implementation work.
- Delegated skills/config: see `docs/agents/workflow.md`.
- If a delegated skill or CLI tool is unavailable, report the fallback and do not claim unavailable actions occurred.

## Repo Constraints

- Do not edit: <generated/read-only/vendor paths>
- Secrets/env: <policy>
- Migrations/deployments/external calls: <approval or policy>
- Generated files: <source command or policy>

## Verification And Done

- Minimum local verification before claiming completion: `<commands>`
- Evidence format: commands run, results, unrun checks, unverified assumptions, remaining risks.
- Docs/archive updates: <repo-specific paths/policy>
