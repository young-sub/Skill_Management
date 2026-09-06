<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/templates/project/CLAUDE.md -->
<!-- Source-SHA256: fe29a4fc2858639d44fc2edfa82d7ad53f8e90a9a09944c80f8c05bb496f1510 -->

# Project Agent Instructions

## Routing

- Read `docs/index.md` for current implementation knowledge and `.harness/project.yaml` for path ownership, impact, command, retention, and Git policy.
- Load ignored `.harness/environment-exceptions.json` once per task when present; refresh after relevant environment changes and honor manual-disable entries.
- Read the nearest nested `AGENTS.md` before editing a path. Preserve user changes and map coherent brownfield structures before proposing moves.

## Delivery

- Use contract Items only when the task warrants a Work Packet or the user requests one. Otherwise follow ordinary development without setup or contract creation.
- Select checks from actual logic impact and `.harness/project.yaml`; Full requires cross-cutting logic impact or an explicit request. Path triggers are warnings.
- Capture the current branch and commit as the base; do not assume a branch name. Preserve the dirty baseline.
- Follow the configured Git policy: commit complete functional units after relevant verification, including required source, tests, docs, and generated resources. Keep coupled Items together.
- Keep durable current truth under configured document roots. Contracts, reviews, evidence, logs, and transactions expire under `.work/`.

## Risk

- Reuse user authorization within scope; ask only for uncovered high-risk actions. Completion does not authorize push, publish, or protected-branch integration.
- Unknown legacy work is quarantined and never swept or deleted automatically.
