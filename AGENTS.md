# AGENTS.md

## Scope

- Applies to this repository, the source distribution for the Personal Agent Harness skills.
- Global agent instructions govern generic behavior; this file contains repository-specific routing only.
- Read the nearest nested `AGENTS.md` before editing a path when one exists.

## Repo Map

- `skills/`: publicly discoverable Agent Skills; each published skill must be self-contained.
- `authoring/`: canonical shared policies and templates, generated into individual skills.
- `legacy-skills/`: non-discoverable preservation area for replaced workflow skills.
- `tests/` and `scripts/`: distribution, installation, contract, runtime, and release verification surfaces.
- `back-up/`: historical snapshots; read only unless a task explicitly targets them.

## Source Of Truth

- Completed V2 implementation record: `docs/archive/plans/harness_v2_implementation_plan.md`
- Parent design record: `skill_recreate_plan.md`; implemented behavior and current architecture docs win on conflict.
- Agent workflow: `docs/agents/workflow.md`
- Tracker and durable records: `docs/agents/issue-tracker.md`
- Triage vocabulary: `docs/agents/triage-labels.md`
- Domain and architecture pointers: `docs/agents/domain.md`
- Distribution inventory: `docs/architecture/skill-inventory.md`

## Commands

- Test: `python -m unittest discover -s tests -p "test_*.py"`
- Resource drift: `powershell -NoProfile -File scripts/sync-skill-resources.ps1 -Check`
- Distribution: `powershell -NoProfile -File scripts/validate-distribution.ps1`
- Install smoke: `powershell -NoProfile -File scripts/test-install.ps1` (downloads/executes the external `skills` package; requires explicit approval).
- Formatting: `git diff --check`

## Work Tracking

- Tracker: local markdown under `docs/work-packets/<owner>/`; GitHub Issue/PR publication is optional.
- Use `$work-packet` for non-trivial capability work; any live Issue/PR publication is a separate human-triggered step.
- Implementation branches use `wp-<id>-<slug>` unless repository evidence establishes another convention.
- `main` is the resolved integration branch and is treated as protected; do not auto-push or auto-merge into it.

## Agent / Skill Use

- Use `$project-agent-bootstrap` when this control plane drifts.
- Use `$test-driven-development` for behavior changes: observe RED before implementation, then GREEN and refactor.
- Keep the main session responsible for shared interfaces, root docs, source-of-truth docs, and final verification.

## Repo Constraints

- Do not edit `back-up/` or global provider configuration unless explicitly requested.
- Do not expose replaced workflow skills through a public `SKILL.md`; preserve approved legacy copies in a non-discoverable form.
- Do not publish releases, rename the remote, change licensing, modify global homes, or delete legacy content without explicit approval.
- `.work/` is gitignored runtime state and must never be a tracked source of truth.

## Verification And Done

- Record commands, results, unrun checks, assumptions, and remaining risks.
- Public skills must eventually pass frontmatter, self-containment, expected-catalog, and clean-install checks from WP-01.
- Archive completed plans under `docs/archive/` only after implementation and verification are complete.
