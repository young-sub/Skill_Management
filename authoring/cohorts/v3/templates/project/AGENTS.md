# Project Agent Instructions

## Routing

- Read `docs/index.md` for current implementation knowledge and `.harness/project.yaml` for deterministic path, impact, command, retention, and Git policy.
- Read the nearest nested `AGENTS.md` before editing a path.
- Preserve existing user changes and map coherent brownfield structures before proposing moves.

## Delivery

- Implement the approved core Item before optional work and verify the affected surface from configured impact rules.
- Capture the current branch as base; do not assume a branch name. Commit each independently verified Item.
- Require explicit approval for destructive, security/privacy, secret, irreversible, costly external, push, or publish actions.

## State

- Durable technical truth is tracked under configured document roots. Goal contracts, reviews, evidence, logs, and transactions expire under `.work/`.
- Unknown legacy work is quarantined; it is never swept or deleted automatically.
