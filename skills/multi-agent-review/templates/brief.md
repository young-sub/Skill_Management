# Subagent Brief

Use the fields that make the assignment unambiguous; a short message is enough for a small task.

- Question and lens: the bounded evidence or challenge question.
- Context: constraints and primary file/source pointers; include an existing claim summary only when needed. Avoid supplying the preferred verdict to a blind reviewer.
- Scope: read-only by default, allowed tools/actions, excluded paths and decisions.
- Model: inherit the current model at or above the user's GPT-5.6 Sol floor. State an override and its reason only when one is needed and supported.
- Result: concise material findings, evidence pointers, uncertainties, and the strongest counterexample. No raw dumps or final team verdict.
- Stop: the evidence needed to answer the question, or the specific missing input that prevents it. Do not search beyond the assigned boundary.

For a challenge, request the failure mode, supporting evidence, and what would resolve or falsify it. For research, request evidence both for and against the relevant claim. Use [an evidence note](evidence-card.md) only when a disputed claim needs more detail. The main agent adjudicates; repeated formatting fields and low-value objections are unnecessary.
