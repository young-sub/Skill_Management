---
name: architect
description: Resolve software design choices for changes spanning callers, types, state or data ownership and module boundaries. Use for architecture decisions, complex refactoring or change-impact analysis; ordinary small edits stay direct. Work contracts belong to design-goal.
disable-model-invocation: true
---
<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/skills/architect/SKILL.md -->
<!-- Source-SHA256: f8820286240c95e76ca75c532644fa1e9b5454a070461717f4199db636862ac9 -->


# Architect

Own the technical decision: where behavior belongs, which contracts remain stable,
and how the implementation will demonstrate it. `design-goal` owns persistent
Items, dependencies, authorization and completion criteria, not architecture.
Neither capability requires the other. A design-only request stays read-only;
authorized implementation continues through code and affected regressions.

Use the [shared change-impact procedure](references/change-impact.md). Discover
the project's current design, callers and owners before introducing a new module,
service, abstraction or dependency. Prefer an existing owner and tools when they
fully solve the problem. Compare alternatives only for a real unresolved tradeoff;
do not manufacture multiple designs or demand a design document for a small edit.

Resolve internal choices from the requirements and evidence. Ask only when missing
information changes observable behavior, scope, authority or recovery risk;
continue independent work. Prototype an uncertain mechanism only when it would
change the decision, and keep experiment evidence distinct from product proof.

Use `multi-agent-review` when a material assumption needs counterexamples or
independent challenge, and `prototype` when same-condition candidate execution
would resolve a real tradeoff. Supply the original requirements, constraints and
raw evidence, not a desired verdict. Incorporate decisive objections and observed
candidate outcomes into adoption/rejection/deferral. Neither is mandatory for
small changes; no fixed reviewers, model, candidate count or separate skills are
needed. If unavailable, perform the bounded review/experiment with existing tools
and report the limit. Implement adopted changes and verify affected regressions.

For a substantial change, leave the decision and its reason in the existing task
notes or project design owner: affected interfaces/callers, type and state/data
owners, boundary/error invariants, rejected alternative if material, implementation
order and regression observations. Keep durable documentation only where future
work needs the decision; there is no required template, contract or new registry.

After implementation, reconcile the actual diff with the impact analysis and run
the selected behavior checks. Read raw outcomes, including errors and preserved
data. Explain the decision, implemented behavior, observations, assistance and
remaining uncertainty. A design document or submitted PASS is not completion.
