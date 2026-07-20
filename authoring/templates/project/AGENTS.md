# Project Agent Instructions

## Scope

- Applies to this repository.
- Read the nearest nested `AGENTS.md` before editing a path when one exists.
- Preserve existing user changes and inspect repository evidence before mutation.

## Verification

- Use `TESTING.md` as the project verification source of truth.
- Run the smallest relevant check first, then the broader required checks.
- Do not claim completion without fresh verification evidence.

## Harness

- `.harness/project.yaml` is the tracked machine-readable project configuration; do not ignore `.harness/`.
- `.work/` and `agent-env.*.md` are local-only runtime/profile state and must not be committed.
- Require explicit approval before destructive, security-sensitive, or irreversible actions.
