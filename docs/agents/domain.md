# Domain And Source-Of-Truth Config

## Product / Domain Sources

- Product: this repository manages reusable agent skill packages under `skills/`.
- Agent-local requirements and implementation plans: `docs/plans/` (gitignored).
- Skill contract: each active package's `SKILL.md`, bundled resources, and invocation metadata.
- Upstream provenance and ownership: `UPSTREAMS.md` once created by the active plan.

## Ownership Boundaries

- `upstream-derived`: track upstream structure and behavior closely.
- `local-adapted`: preserve explicit local contracts while adopting upstream changes semantically.
- `local-owned`: never replace from upstream; includes `work-packet` and `project-agent-bootstrap`.
- `back-up/` is historical evidence, never an active skill surface.

## Architecture And Verification Sources

- Orchestration: `skills/work-packet/SKILL.md` and `skills/work-packet/REFERENCE.md`.
- Bootstrap: `skills/project-agent-bootstrap/SKILL.md` and its references/templates.
- Current audit: `skills/work-packet/scripts/audit-work-packet-skill.py`.
- Active verification plan: section 7 of the active adoption plan.

## Active Planning And Archive

- Agent-local plans and Work Packets: `docs/plans/<owner-slug>/<feature-slug>/` (gitignored).
- Shared outcomes: tracked source-of-truth docs such as `UPSTREAMS.md` and affected skill files.

## Unresolved Gaps

- Capture the current upstream release/SHA and complete ownership catalog during the active plan.
- Add repository-wide static and behavior-smoke verification.
