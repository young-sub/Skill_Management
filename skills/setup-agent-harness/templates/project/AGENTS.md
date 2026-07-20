<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/templates/project/AGENTS.md -->
<!-- Source-SHA256: 04cb908a547709f1036a3510b3fd6df3935faa6e0e27c58d9fc9ed85bb156752 -->

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
