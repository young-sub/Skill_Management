# Project Agent Instructions

## Routing

- Read `docs/index.md` for current implementation knowledge and `.harness/project.yaml` for path ownership, impact, command, retention, and Git policy.
- Read the nearest nested `AGENTS.md` before editing a path. Preserve user changes and map coherent brownfield structures before proposing moves.

## Delivery

- Implement dependency-ready core Items before optional work. Use RED/GREEN for behavior changes and impact-selected verification for Item completion.
- Capture the current branch and commit as the base; do not assume a branch name. Preserve the dirty baseline and commit only independently reviewable slices when repository policy or the human requests commits.
- Keep durable current truth under configured document roots. Contracts, reviews, evidence, logs, and transactions expire under `.work/`.

## Risk

- Require explicit approval for destructive actions, security/privacy or secret handling, irreversible migration, external cost, push, publish, or other high-risk state changes.
- Unknown legacy work is quarantined and never swept or deleted automatically.
