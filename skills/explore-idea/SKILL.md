---
name: explore-idea
description: Clarify a problem, user value, constraints, and the smallest useful experiment through read-only exploration. Use before the user has chosen an implementation direction, not as a gate for already clear, authorized work.
---

# Explore Idea

Exploration itself is read-only: inspect existing evidence without creating code, plans, contracts, or setup artifacts.

1. Identify the user, problem, and desired improvement. Reuse context already supplied instead of asking the user to repeat it.
2. Inspect only repository evidence that resolves feasibility or scope. Distinguish observed facts, assumptions, and meaningful open decisions.
3. Propose the smallest useful MVP or experiment. Compare alternatives only when the tradeoff changes the decision; a prototype is useful only if trying it resolves uncertainty.
4. Summarize the direction, constraints, and remaining decision briefly. Ask only about an answer that materially changes the outcome.

If the user later authorizes implementation, switch to the appropriate workflow and proceed. Small, clear changes use direct development. Use `design-goal` when a contract is explicitly requested or persistent coordination is needed across review boundaries or material risk; explore unresolved product decisions before creating a contract. Do not require the user to invoke another skill or repeat approval. The exploration request alone does not authorize implementation.
