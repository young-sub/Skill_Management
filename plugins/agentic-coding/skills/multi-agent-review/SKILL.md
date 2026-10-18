---
name: multi-agent-review
description: Challenge a decision, design assumption, plan or implementation with concrete counterexamples, failure conditions and evidence. Use for adversarial design review or multi-agent review; a main-only review needs no delegation, and real agents follow the user's request and permissions.
---

# Multi-Agent Review

Review the actual decision and its consequences. A review does not authorize implementation or external writes.

Bind the question to the user's named project and its actual entrypoints before
searching. Parent repository/tooling guidance governs the work but is not the
review subject. Resolve overloaded terms at the product callsite before assessing
work readiness: input validation and row commits concern the storage transaction;
Git commits and Harness Items concern delivery only when that is the user's subject.
The presence of `.harness` policy does not select the latter. Missing Git history,
Items or old test reports does not block a source-based product design review.
If both meanings remain plausible after reading the callsite, state that ambiguity
and review the supported product case instead of silently switching subjects.

A counterexample or assumption-review request can use this Skill in a single
agent. A restriction on additional delegation does not prevent that review;
do not present it as independent-agent evidence. Use real reviewers only when
requested or useful within the applicable delegation authority.

## Scope And Models

- Natural-language requests for multiple agents authorize delegation; no magic flag is required. `--subagents allowed` remains a supported expression of that intent. Otherwise follow the applicable delegation permissions.
- Choose each agent's specialization, tools, model, and reasoning effort for its assigned question, evidence needs, and risk. Respect explicit user constraints and host capabilities; there is no fixed model requirement or mandatory inheritance. Report a material selection limitation honestly.
- Honor explicit user counts and roles within host limits; there is no requirement that challengers outnumber researchers. Stage work if concurrency is limited. Report infeasible constraints and use an honest fallback.
- Without specified counts, select agents for distinct evidence or challenge questions the review actually needs. Add an agent only for an unanswered question. For a generic review with no explicit request for real agents, use a main-only pass if coordination would cost more than it saves.

For a design or implementation review, use [change impact](references/change-impact.md) to challenge actual callers, types, state/data owners and module boundaries. Reuse the existing impact analysis and check its omissions against the diff; this does not require a separate design document.

## Review Loop

Use the smallest loop that answers the question:

1. Frame the decision, constraints, assumptions, and evidence that could change the answer. Keep the frame in context; no separate document or fixed word count is required.
   Challenge the strongest material assumption: identify a concrete counterexample,
   failure condition and a way to check it. Include the original requirement,
   constraints and raw sources; do not lead reviewers toward the preferred answer.
2. Delegate bounded, non-overlapping evidence questions only when they add coverage. Use [the brief](templates/brief.md) only as needed. Prefer read-only work and file/source pointers. Give independent reviewers the raw question and primary evidence before a preferred verdict when practical, reducing anchoring. Work locally on independent evidence while agents run when useful.
3. Combine material claims with their evidence and inspect primary sources for central, disputed, high-risk, or outcome-changing claims. Agent reports are indexes, not proof; do not accept conclusions by agent count.
4. Adjudicate material objections and give the conclusion, decisive evidence, unresolved risks, and useful next action in the user's language. Preserve a strong supported minority objection and do not force a verdict when missing evidence could reverse it. The [report guide](templates/final-report.md) is optional structure, not a mandatory set of headings or quotas.
   State whether each decisive objection changes, rejects or leaves the design
   intact and why. A hypothetical objection is not an observed failure. When a
   small experiment would settle it, use `prototype` or existing project checks
   within authorization. Adopted changes still need implementation and affected
   regressions; review agreement is not product completion.

The main agent owns the final decision and verifies material claims. Missing evidence limits the conclusion; ask only if a user decision is necessary, and continue independent authorized review. If real agents are unavailable, state that and perform the useful single-agent portion without presenting simulated roles as independent agents.
