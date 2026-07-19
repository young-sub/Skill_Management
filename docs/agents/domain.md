# Domain And Source-Of-Truth Config

## Product And Architecture

- Product overview and active requirements: `harness_v2_implementation_plan.md`.
- Parent design and rationale: `skill_recreate_plan.md`.
- Current implementation surface: distributable skills under `skills/`.
- Planned boundaries: `authoring/`, `skills/`, `legacy-skills/`, `scripts/`, and `tests/` as defined by WP-01.
- Architecture and ADR directories are not configured yet; WP-01 decides whether separate records are needed.

## Verification And Operations

- Verification policy is currently specified in sections 10 and WP-01 of `harness_v2_implementation_plan.md`.
- No implemented repository-wide test command exists yet.
- Distribution verification must cover skill-directory/name matching, valid frontmatter, self-contained resources, legacy non-discovery, expected catalog, and clean Codex/Claude installation.
- Runtime diagnostics are out of WP-01 scope.

## Active Planning And Archive

- Active plan: `harness_v2_implementation_plan.md`.
- Durable local Work Packets: `docs/work-packets/<owner-slug>/`.
- Published Work Packet archive: `docs/archive/work-packets/<owner-slug>/`.
- Completed/stale plans: `docs/archive/` after close.

## Unresolved Decisions

- Repository rename, public license, catalog registration, native provider plugins, global instruction installation, and final legacy storage format remain explicitly deferred by the active plan.
