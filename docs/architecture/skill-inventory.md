# Harness V2 Skill Inventory

## Purpose

This inventory defines WP-01 distribution ownership. `harness_v2_implementation_plan.md` is authoritative; this document records its mapping against the current worktree.

## Public Skills

These skills remain discoverable under `skills/<name>/SKILL.md` and retain their behavior during the Core Workflow refactor.

| Class | Skills |
| --- | --- |
| Compatibility and support | `multi-agent-review`, `prototype`, `webapp-testing`, `zoom-out` |
| Professional and domain | `finance-research`, `find-skills`, `frontend-design`, `teach`, `theme-factory`, `web-artifacts-builder`, `write-a-skill` |

Expected public catalog count: 11.

## Preserved Legacy Skills

These implementations are replacement or absorption candidates. WP-01 moves them to `legacy-skills/<name>/` and renames their entrypoint to `SKILL.legacy.md`, preserving resources while preventing installer discovery.

`diagnose`, `grill-me`, `grill-with-docs`, `handoff`, `improve-codebase-architecture`, `project-agent-bootstrap`, `setup-matt-pocock-skills`, `tdd`, `to-issues`, `to-prd`, `triage`, `work-packet`.

Expected preserved legacy count: 12.

## Intentionally Absent

- `caveman`: professional/excluded in the plan but intentionally removed in baseline commit `c9d3388`; WP-01 does not recreate it.
- `codex-delegation`: replacement/archive candidate intentionally removed in baseline commit `c9d3388`; WP-01 does not recreate it.

## Future Core Catalog

WP-02 through WP-05 will add `setup-agent-harness`, `explore-idea`, `design-goal`, `execute-codex-goal`, rewritten `diagnose`, `close-goal`, and `maintain-agent-harness`. WP-01 must not invent those behaviors merely to populate the catalog.

## Distribution Invariants

- Public directory name equals frontmatter `name`.
- Public frontmatter contains only `name` and `description`, both required.
- Public resources do not resolve outside their owning Skill directory.
- `legacy-skills/` contains no discoverable `SKILL.md`.
- Generated resources come from `authoring/resource-map.json` and include the canonical source SHA-256.
