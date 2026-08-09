<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/templates/project/AGENTS.md -->
<!-- Source-SHA256: 9858e8bfb1a8657827bad4f10aee143a52b4de64dc7f8c25f88d708140e8cbb7 -->

# Project Agent Instructions

## Routing

- Read `docs/index.md` for current implementation knowledge and `.harness/project.yaml` for path ownership, impact, command, retention, and Git policy.
- Read the nearest nested `AGENTS.md` before editing a path. Preserve user changes and map coherent brownfield structures before proposing moves.

## Delivery

- Implement dependency-ready core Items before optional work. Use RED/GREEN for behavior changes and impact-selected verification for Item completion.
- Capture the current branch and commit as the base; do not assume a branch name. Preserve the dirty baseline.
- A commit unit is the smallest complete functional unit that works when checked out by itself, including required source, tests, docs, schemas, and generated resources. Commit every such unit after its mapped verification passes. Group coupled Items into one commit; split only independently working units. Never create an intentionally broken intermediate commit.
- Keep durable current truth under configured document roots. Contracts, reviews, evidence, logs, and transactions expire under `.work/`.

## Risk

- Require explicit approval for destructive actions, security/privacy or secret handling, irreversible migration, external cost, push, publish, or other high-risk state changes.
- Unknown legacy work is quarantined and never swept or deleted automatically.
