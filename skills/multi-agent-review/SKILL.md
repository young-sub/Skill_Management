---
name: multi-agent-review
description: Review a decision, plan, or implementation with separable evidence gathering and independent challenge when the user requests multiple agents or applicable instructions authorize delegation. Use evidence and main-agent judgment, with agent counts proportional to the question.
---

# Multi-Agent Review

Review the actual decision and its consequences. A review does not authorize implementation or external writes.

## Scope And Models

- Natural-language requests for multiple agents authorize delegation; no magic flag is required. `--subagents allowed` remains a supported expression of that intent. Otherwise follow the applicable delegation permissions.
- Choose each agent's specialization, tools, model, and reasoning effort for its assigned question, evidence needs, and risk. Respect explicit user constraints and host capabilities; there is no fixed model requirement or mandatory inheritance. Report a material selection limitation honestly.
- Honor explicit user counts and roles within host limits; there is no requirement that challengers outnumber researchers. Stage work if concurrency is limited. Report infeasible constraints and use an honest fallback.
- Without specified counts, select agents for distinct evidence or challenge questions the review actually needs. Add an agent only for an unanswered question. For a generic review with no explicit request for real agents, use a main-only pass if coordination would cost more than it saves.

## Review Loop

Use the smallest loop that answers the question:

1. Frame the decision, constraints, assumptions, and evidence that could change the answer. Keep the frame in context; no separate document or fixed word count is required.
2. Delegate bounded, non-overlapping evidence questions only when they add coverage. Use [the brief](templates/brief.md) only as needed. Prefer read-only work and file/source pointers. Give independent reviewers the raw question and primary evidence before a preferred verdict when practical, reducing anchoring. Work locally on independent evidence while agents run when useful.
3. Combine material claims with their evidence and inspect primary sources for central, disputed, high-risk, or outcome-changing claims. Agent reports are indexes, not proof; do not accept conclusions by agent count.
4. Adjudicate material objections and give the conclusion, decisive evidence, unresolved risks, and useful next action in the user's language. Preserve a strong supported minority objection and do not force a verdict when missing evidence could reverse it. The [report guide](templates/final-report.md) is optional structure, not a mandatory set of headings or quotas.

The main agent owns the final decision and verifies material claims. Missing evidence limits the conclusion; ask only if a user decision is necessary, and continue independent authorized review. If real agents are unavailable, state that and perform the useful single-agent portion without presenting simulated roles as independent agents.
