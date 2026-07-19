<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/references/goal-execution-policy.md -->
<!-- Source-SHA256: 4c78d072f25a38a13141bf30482d652aa0cb185dc57695c0627e89ba0d767664 -->

# Goal Execution Policy

- A human declares the Codex Goal; Harness skills do not create a Goal wrapper.
- Execution requires an active Goal, an approved Contract, matching Work ID and canonical contract hash, and a valid dependency DAG.
- Execute the first dependency-ready pending Plan, record state transitions atomically, and verify each slice before advancing.
- Stop only for contradictory approved requirements, unapproved public contracts, destructive migration risk, new secrets or cost, security/privacy risk, broad unapproved architecture, an invalid test seam, missing required environment, or no viable implementation path.
- A Hard Stop records evidence, completed Plans, alternatives, impact, and the exact resume path in `BLOCKED.md`.
