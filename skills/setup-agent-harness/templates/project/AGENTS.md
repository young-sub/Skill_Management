<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/templates/project/AGENTS.md -->
<!-- Source-SHA256: ac38b610f8eae75842ed2b0876016c6ca61a95540cc014a9c0e48c96c0bb9c84 -->

# Project Agent Instructions

## Routing

- Read `docs/index.md` for current implementation knowledge and `.harness/project.yaml` for path ownership, impact, command, retention, and Git policy.
- Read the nearest nested `AGENTS.md` before editing a path. Preserve user changes and map coherent brownfield structures before proposing moves.

## Delivery

- Implement dependency-ready core Items before optional work. Use RED/GREEN for behavior changes and impact-selected verification for Item completion.
- Capture the current branch and commit as the base; do not assume a branch name. Preserve the dirty baseline and commit each independently verified Item.
- Keep durable current truth under configured document roots. Contracts, reviews, evidence, logs, and transactions expire under `.work/`.

## Risk

- Require explicit approval for destructive actions, security/privacy or secret handling, irreversible migration, external cost, push, publish, or other high-risk state changes.
- Unknown legacy work is quarantined and never swept or deleted automatically.
