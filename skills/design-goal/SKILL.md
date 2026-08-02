---
name: design-goal
description: Create an Item-based Harness v3 contract and Korean Design Review from repository evidence and human decisions.
---

# Design Goal — Harness v3

Use [the runtime](scripts/core_harness.py), [the renderer](scripts/render_item_review.py), [the contract schema](schemas/contract.schema.json), and [the human-readability policy](references/human-readability-policy.md).

1. Research repository evidence and close internal choices that follow convention. Interview only while product, state, permission, failure, or hard-to-reverse decisions remain open.
2. Create `.work/goals/active/<work-id>/contract.json` with two to five behavior-oriented Items. Every Item defines stable ID, What, ordered How steps, first-use terms, observable Test, Done, dependencies, non-goals, decision state, material risks, and core/optional priority.
3. Render `review/design.html` in Korean. It is a scriptless decision surface with behavior-matched visuals, not a Markdown dump or technical authority.
4. Validate complete Item/test/done/dependency projection coverage. Required unresolved decisions block authorization.
5. A valid design is `default-authorized`: bind the canonical server-rendered Review to the contract and continue without asking for an affirmative phrase or hash. A clear user veto stops it. Destructive, security/privacy, secret, irreversible, costly external, push, or publish risk still requires explicit approval.

Do not begin implementation in this Skill. Return the authorized work path and Item IDs; a host Goal may track the work but is not required.
