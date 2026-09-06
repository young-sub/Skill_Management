---
name: multi-agent-review
description: Review a decision, plan, or implementation with separable evidence gathering and independent challenge when the user requests multiple agents or applicable instructions authorize delegation. Use evidence and main-agent judgment, with agent counts proportional to the question.
---

# Multi-Agent Review

Review the actual decision and its consequences. A review does not authorize implementation or external writes.

## Scope And Models

- Natural-language requests for multiple agents authorize delegation; no magic flag is required. `--subagents allowed` remains a supported expression of that intent. Otherwise follow the applicable delegation permissions.
- Inherit the current model. Respect the user's model floor: GPT-5.6 Sol or GPT-6 Astra, with no downgrade for mechanical work. Override model/reasoning only when requested or justified by the applicable instructions and supported by the host. Never pretend a requested model was enforced when it was not.
- Honor explicit user counts and roles within host limits; there is no requirement that challengers outnumber researchers. Stage work if concurrency is limited. Report infeasible constraints and use an honest fallback.
- Without specified counts, start with the smallest useful team: one evidence researcher and one independent challenger, or just a challenger when the main agent already has the evidence. Add an agent only for a distinct unanswered question. For a generic review with no explicit request for real agents, use a main-only pass if coordination would cost more than it saves.

## Review Loop

1. Frame the decision, constraints, main assumptions, and evidence that could change the answer. Keep the frame in context; no separate document or fixed word count is required.
2. Delegate bounded, non-overlapping evidence questions. Use [the brief](templates/brief.md) only as needed. Prefer read-only work and file/source pointers. Give independent reviewers the task and primary evidence before a preferred verdict when practical, to reduce anchoring.
3. Work locally on independent evidence while agents run. Research and critique may overlap when they have independent inputs; wait only for real dependencies. Stop adding work when new outputs repeat existing findings.
4. Combine material claims with their evidence. Inspect primary evidence for central, disputed, high-risk, or outcome-changing claims. Compressed agent reports are indexes, not proof; do not accept conclusions by agent count.
5. Adjudicate material objections: sustained when supported and consequential, reserved when plausible but unresolved, overruled when refuted or immaterial. Preserve a strong minority objection. Do not force a verdict when missing evidence could reverse it.
6. Give the conclusion, decisive evidence, unresolved risks, and useful next action in the user's language. The [report guide](templates/final-report.md) is optional structure, not a mandatory set of headings or quotas.

The main agent owns the final decision and verifies material claims. Missing evidence limits the conclusion; ask only if a user decision is necessary, and continue independent authorized review. If real agents are unavailable, state that and perform the useful single-agent portion without presenting simulated roles as independent agents.
