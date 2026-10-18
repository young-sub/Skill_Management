---
name: zoom-out
description: Explain how current code works and fits the user flow, or why a design decision was made from recorded history and constraints. Use for broader context, call/ownership explanations and historical rationale; distinguish facts, inference and unknowns.
---

# Zoom Out

Go up one level of abstraction, selecting only the perspective the question needs:

- **How:** trace the current entrypoint, callers, rules/types, state/storage owner
  and observable output. Cite concrete paths and distinguish inspected source from
  observed execution; reading code does not prove runtime success.
- **Why:** start with supplied rationale, then relevant design notes, bounded Git
  history and accessible linked records when needed. Explain the constraints and
  alternatives at the time. Label **confirmed reason**, **inference**, and **unknown**
  explicitly where applicable. Current code alone cannot prove historical intent;
  absent or conflicting records remain absent or conflicting. Say what should be
  preserved, changed or avoided and the risk only as relevant to the question.

Use established project vocabulary and a few evidence pointers. Do not require
both perspectives, repeat adequate supplied history, or search unrelated records.

Explain why these boundaries matter to the user's current question. Use a small diagram only if it makes the flow clearer. Do not inventory unrelated modules, invent a glossary, or create documentation artifacts for a short explanation.

Keep this step read-only: zero product commands, task/state/evidence writes or
pending-command replays. Use `recall` only when recovering prior work state is
actually needed. When this occurs during an authorized task, give the explanation
and resume that task unless the user explicitly pauses or replaces it.
