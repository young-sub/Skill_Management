---
name: design-goal
description: Create an Item-based Harness v3 contract and Korean Design Review from repository evidence and human decisions.
---

# Design Goal — Harness v3

Use [the runtime](scripts/core_harness.py), [the renderer](scripts/render_item_review.py), [the contract schema](schemas/contract.schema.json), and [the human-readability policy](references/human-readability-policy.md).

1. Research repository evidence and close internal choices that follow convention. Interview only while product, state, permission, failure, or hard-to-reverse decisions remain open.
2. Create `.work/goals/active/<work-id>/contract.json` with one to five behavior-oriented Items. Require stable ID, What, ordered How steps, observable Test, and Done; add terms, dependencies, non-goals, risk flags, or priority only when they affect the work.
3. Render `review/design.html` in Korean. It is a scriptless decision surface with behavior-matched visuals, not a Markdown dump or technical authority.
4. Validate complete Item/test/done/dependency projection coverage. Required unresolved decisions block authorization.
5. A valid ordinary design is `default-authorized`: bind the canonical server-rendered Review to the contract and continue without asking for an affirmative phrase or hash. A veto remains in force for the same contract. Structured destructive, security/privacy, secret, irreversible, costly external, push, publish, or global-configuration risk requires explicit approval.

Do not begin implementation in this Skill. Return the authorized work path and Item IDs; a host Goal may track the work but is not required.
