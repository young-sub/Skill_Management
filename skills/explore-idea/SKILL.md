---
name: explore-idea
description: Explore a problem, user value, constraints, and the smallest useful MVP without creating implementation artifacts. Use when an idea needs read-only repository research or product clarification before an implementation contract is appropriate.
---

# Explore Idea

## Contract

- Operate read-only by default. Do not create or modify files.
- Repository exploration is limited to read-only inspection.
- Treat implementation, migration, provider, and destructive actions as out of scope.
- Do not invoke `design-goal` or any other user-invoked Skill automatically.

## Workflow

1. Restate the problem and identify the user who experiences it.
2. Inspect repository evidence only when it materially resolves scope or feasibility.
3. Separate verified facts, assumptions, constraints, and open decisions.
4. Propose the smallest useful MVP and whether a throwaway prototype would reduce risk.
5. Summarize the problem, user value, constraints, MVP, and unresolved decisions.

If the user chooses implementation, say that `design-goal` is the next explicit step and stop. Do not invoke `design-goal`.
