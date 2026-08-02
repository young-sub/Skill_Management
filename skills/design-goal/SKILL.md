---
name: design-goal
description: Create an Item-based Harness v3 contract and Korean Design Review from repository evidence and human decisions.
---

# Design Goal — Harness v3

Use `scripts/core_harness.py`, `scripts/render_item_review.py`, and `schemas/contract.schema.json`.

1. Research repository evidence and close internal choices that follow convention. Interview only while product, state, permission, failure, or hard-to-reverse decisions remain open.
2. Create `.work/goals/active/<work-id>/contract.json` with two to five behavior-oriented Items. Every Item defines stable ID, What, ordered How steps, first-use terms, observable Test, Done, dependencies, non-goals, decision state, material risks, and core/optional priority.
3. Render `review/design.html` in Korean. It is a scriptless decision surface with behavior-matched visuals, not a Markdown dump or technical authority.
4. Validate complete Item/test/done/dependency projection coverage. Required unresolved decisions block approval.
5. Treat an unambiguous natural-language approval of the displayed Review as authority. Store the contract and rendered-review digests internally with the utterance, actor, time, and visible IDs; never ask the human to paste Work ID, path, or hash.

Do not begin implementation in this Skill. Return the approved work path and Item IDs; a host Goal may track the work but is not required.
