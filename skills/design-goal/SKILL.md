---
name: design-goal
description: Create and default-authorize an Item-based Harness contract from repository evidence and human decisions.
---
<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/skills/design-goal/SKILL.md -->
<!-- Source-SHA256: 6c6f2bc72de0ea8df55025de96cea69a44a00370edd6eff5260e46120a62d5e2 -->


# Design Goal

Use [the runtime](scripts/core_harness.py) and [the contract schema](schemas/contract.schema.json).

1. Research repository evidence and close internal choices that follow convention. Interview only while product, state, permission, failure, or hard-to-reverse decisions remain open.
2. Build an in-memory contract candidate with one to five behavior-oriented Items, then invoke the runtime's single `design-create` entrypoint. Omit the work ID for a generated identity; an explicit ID must conflict instead of overwriting an existing namespace. Never pre-create the work root or write its authority files independently.
3. Let `design-create` reserve `.work/goals/active/<work-id>` atomically and write only `contract.json`.
4. Validate complete Item/test/done/dependency coverage. Required unresolved decisions block authorization.
5. A valid ordinary design is `default-authorized` against the canonical contract and continues without an affirmative phrase or hash. A veto remains in force for the same contract. Structured destructive, security/privacy, secret, irreversible, costly external, push, publish, or global-configuration risk requires explicit approval.

Return the authorized work path and Item IDs, then continue through `execute-codex-goal` without another approval step. A host Goal may track the work but is not required.
