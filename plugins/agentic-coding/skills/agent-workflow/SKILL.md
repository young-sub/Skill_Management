---
name: agent-workflow
description: Deliver delegated coding work across FE, API/backend and business logic with acceptance checks derived from the request, proof that new tests catch the defect, affected existing checks and a result card. Also shows what is verified, reuses UI standards, builds guardrails and opens explicit-only capabilities. Trivial edits stay direct.
---
<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/skills/agent-workflow/SKILL.md -->
<!-- Source-SHA256: a61ec68ef3bfbcc5773200220c750ffbc5466a698125b4ed76ec7f57c4a2d2b4 -->


# Agent Workflow

Deliver the outcome inside the authorized scope, prove it, and report it so the
user can delegate more. Trivial edits (copy, typo, one config value) need none of
this. When the prompt context carries a `route`, invoke that Skill first unless
the request is a trivial edit.

## Delivery loop

1. **Scope.** Read the project's AGENTS/index and the Feature Map rules, owners and
   checks for the touched area. Trace callers and state/data owners through
   FE → API → Domain → storage; use [change impact](references/change-impact.md)
   when ownership or contracts are shared.
2. **Acceptance first.** Before changing behavior, write or name the checks that
   decide success. Derive expected values from the request and the documented rule,
   never from running the new code. Run them on the current code and confirm they
   fail for the intended reason; if reproduction is infeasible, say why.
3. **Fix at the owner, on every path.** List every place that writes or enforces
   the same rule (callers, other endpoints, triggers, imports, background jobs) and
   cover each with a check. When the request states the rule for all saves or all
   users, apply it on every such path; exempting one (for example restore or import)
   is the user's decision, so ask instead of deciding it. A guard is a fix only when that state
   can legitimately occur. Revert changes made for a hypothesis the evidence refuted;
   after two failures on one premise, test the premise before the next fix.
4. **Prove the checks catch the defect.** A failure observed in step 2 for the intended
   reason is the proof. Only for tests written after the change, run
   `python <this Skill's directory>/scripts/probe_check.py prove --root <project> --base HEAD --tests <new or changed tests> --command "<test command>" --skip-current`:
   the tests must fail without the source change. Pass ignored dependency directories
   with `--link node_modules` instead of creating links in the copy yourself. For a
   business, architecture or UI rule worth protecting, add a probe to
   `.harness/probes.json` and run `probe_check.py probes`. A surviving probe means the
   rule is not protected yet.
5. **Run affected existing checks once, after the final edit.** In one batch, run the
   new tests with the Feature's registered checks and the existing tests that exercise
   the changed modules on every touched layer; rerun only what a later edit affects.
   New tests alone are not completion. Open a browser only for a visual or interaction
   change that no automated UI test covers.
6. **Independent check.** For any behavior change, launch a fresh verifier that gets only
   the user's request verbatim and the diff, per [independent check](references/independent-check.md).
   Fix the violations its failing tests show; a stricter reading than the request goes to
   *User decisions*. Your own checks cover the paths you chose; this covers the ones you did not.
7. **Report the result card.**

Settle questions that running code can answer (behavior, performance, layout) by
experiment. Ask the user only for decisions they own: business value, scope,
irreversible or outward-facing actions.

Playbooks add task-specific cases: [feature](playbooks/feature.md),
[bug fix](playbooks/bug-fix.md), [refactoring](playbooks/refactoring.md).

## Result card

End delegated work with at most about 15 lines:

```
Request → changed behavior: <one line>
Affected: <Feature / rule IDs> | business: <FE/API/Domain> | architecture: <boundary or owner>
Checks after the final edit: <check> ✓/✗ (command, raw location)
Proof: <tests fail without the change ✓ | probe <id> killed ✓ | not run: reason>
Paths covered: <writers/enforcers checked, or the uncovered one>
Independent check: <complete | N violations → M fixed, K for user decision (tests: paths) | not run: reason>
Unverified: <what was not observed and why>
User decisions: <decision, recommendation, what happens without an answer> or none
```

Keep observed results, inference and unverified claims separate. Fixture, product,
package and native-host evidence are different evidence.

## Capabilities

Auto-invocable Skills (Skill tool): `diagnose` for incorrect behavior or a complaint,
`recall` to resume prior work, `setup-project-verification` to connect verification
for a flow, `fixing-accessibility` for interaction and accessibility.

Explicit-only capabilities stay out of the context until needed. When one of these
needs arises, read `SKILL.md` in the named sibling Skill directory (same parent as this
Skill's directory) and follow it. If that directory is absent, continue here.

| Need | Sibling Skill |
| --- | --- |
| Design choice across modules, interfaces or data ownership | `architect` |
| Parallel implementation over disjoint files, or resuming delegated work | `swarm` |
| Adversarial review of a plan or implementation | `multi-agent-review` |
| Prune, merge or repair checks, Feature Map or guide drift | `maintain-project-verification` |
| Visual design quality, redesign or critique | `impeccable` |
| React/Next.js performance | `vercel-react-best-practices` |
| A runnable experiment before production code | `prototype` |
| Explain how or why code works | `zoom-out` |
| Unclear problem or value | `explore-idea` |
| Work contract lifecycle | `design-goal`, `execute-codex-goal`, `close-goal` |
| Harness configuration | `setup-agent-harness`, `maintain-agent-harness` |

Use `swarm` only when the user asked for parallel work or the split is clearly
independent; say that you are doing so.

## Show what is verified

Render `lookup --report` for a task or `audit --report` for the project with the
bundled [CLI](scripts/project_workflow.py) and answer from it. Add the
`probe_check.py probes` matrix when probes exist: it shows how many synthetic
defects each Feature's checks detect per business/architecture/UI × layer. An
unconnected project reports NOT_CONNECTED: say so and offer setup. Ask the report's
*Questions for the user* in the same turn and record the answers. Do not run tests,
repairs or services for a results request.

## Feedback, UI standards and guardrails

- Human correction or a turn worth repeating: [feedback and success reuse](references/feedback-and-success.md).
  A first clear correction is enough; praise alone is not a rule request.
- UI standards: the project guide and its tokens/components own values. Follow
  [UI discovery and comparison](references/repair-and-reuse.md#ui-discovery-and-comparison);
  a drift guardrail is a lint or visual check plus a probe that it rejects.
- Guardrail: express the rule in the project's existing linter, type system or test
  runner. Prove it rejects a synthetic violation (probe) and still allows nearby valid
  code. A written rule without enforcement is not a guardrail.

## Persistent workflow state

Only for an existing task or an explicit request: use the bundled CLI with
[workflow obligations](references/workflow-obligations.md) and
[result lookup](references/result-viewer.md). Never guess among active tasks; lookup
writes nothing and runs no product command. Installed resources, global settings,
providers and publishing need their own authority.
