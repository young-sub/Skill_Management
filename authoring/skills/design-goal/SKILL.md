---
name: design-goal
description: Create an Item-based Harness contract and Korean Design Review from repository evidence and human decisions.
---

# Design Goal

Use [the runtime](scripts/core_harness.py), [the renderer](scripts/render_item_review.py), [the contract schema](schemas/contract.schema.json), and [the human-readability policy](references/human-readability-policy.md).

1. Research repository evidence and close internal choices that follow convention. Interview only while product, state, permission, failure, or hard-to-reverse decisions remain open.
2. Build an in-memory contract candidate with one to five behavior-oriented Items, then invoke the runtime's single `design-create` entrypoint. Omit the work ID for a generated identity; an explicit ID must conflict instead of overwriting an existing namespace. Never pre-create the work root or write its authority files independently.
3. Let `design-create` reserve `.work/goals/active/<work-id>` atomically and write `contract.json` plus the Korean `review/design.html`. The Review is a scriptless decision surface with behavior-matched visuals, not a Markdown dump or technical authority.
4. Validate complete Item/test/done/dependency projection coverage. Required unresolved decisions block authorization.
5. A valid ordinary design is `default-authorized`: bind the canonical server-rendered Review to the contract and continue without asking for an affirmative phrase or hash. A veto remains in force for the same contract. Structured destructive, security/privacy, secret, irreversible, costly external, push, publish, or global-configuration risk requires explicit approval.

Do not begin implementation in this Skill. Return the authorized work path and Item IDs; a host Goal may track the work but is not required.
