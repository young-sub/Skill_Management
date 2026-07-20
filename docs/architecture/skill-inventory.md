# Harness V2 Skill Inventory

## Purpose

This inventory defines current distribution ownership. The completed V2 record is archived at `docs/archive/plans/harness_v2_implementation_plan.md`; this document records its mapping against the current worktree.

## Public Skills

These skills remain discoverable under `skills/<name>/SKILL.md` and retain their behavior during the Core Workflow refactor.

| Class | Skills |
| --- | --- |
| Compatibility and support | `multi-agent-review`, `prototype`, `webapp-testing`, `zoom-out` |
| Harness V2 Core | `setup-agent-harness`, `explore-idea`, `design-goal`, `execute-codex-goal`, `diagnose`, `close-goal`, `maintain-agent-harness` |
| Professional and domain | `finance-research`, `find-skills`, `frontend-design`, `teach`, `theme-factory`, `web-artifacts-builder`, `write-a-skill` |

Expected public catalog count: 18.

## Preserved Legacy Skills

These implementations are replacement or absorption candidates. WP-01 moves them to `legacy-skills/<name>/` and renames their entrypoint to `SKILL.legacy.md`, preserving resources while preventing installer discovery.

`diagnose`, `grill-me`, `grill-with-docs`, `handoff`, `improve-codebase-architecture`, `project-agent-bootstrap`, `setup-matt-pocock-skills`, `tdd`, `to-issues`, `to-prd`, `triage`, `work-packet`.

Expected preserved legacy count: 12.

## Intentionally Absent

- `caveman`: professional/excluded in the plan but intentionally removed in baseline commit `c9d3388`; WP-01 does not recreate it.
- `codex-delegation`: replacement/archive candidate intentionally removed in baseline commit `c9d3388`; WP-01 does not recreate it.

## Harness V2 Core Catalog

`setup-agent-harness` has separate greenfield and brownfield boundaries. Greenfield keeps the deterministic `plan/apply/validate` compatibility flow. Brownfield begins with `reconcile`, which inventories existing instructions, docs, manifests, CI, verification commands, Git boundaries, and ignore state without executing repository content or mutating target files. Its deterministic PlanArtifact records authority/router/TESTING proposals and tracked/local-only policy for a separately approved apply workflow.

WP-02 through WP-05 added all seven Core Skills. `future_core_skills` is now empty; WP-06 owns release and Pilot evidence rather than another Skill.

## Distribution Invariants

- Public directory name equals frontmatter `name`.
- Public frontmatter contains only `name` and `description`, both required.
- Public resources do not resolve outside their owning Skill directory. The self-containment scanner reports stable rule IDs for relative escape, absolute/file URI, repository-root, cross-Skill, missing-resource, and reparse-point violations; governed exceptions require an owner, reason, and review date in `distribution/self-containment-allowlist.json`.
- `legacy-skills/` contains no discoverable `SKILL.md`.
- Generated resources come from `authoring/resource-map.json` and include the canonical source SHA-256.
- Pilot execution is read-only by default; only `--update-baseline` may refresh normalized tracked pilot reports.
- Release proof is split into pilot, local-source install/refresh, and remote GitHub update evidence and is valid only when its clean Git commit/tree matches the release candidate.
