---
name: agent-workflow
description: Deliver delegated coding work across FE, API/backend and business logic with acceptance checks derived from the request, proof that new tests catch the defect, affected existing checks, an independent verifier and a result card. Also shows what is verified, reuses UI standards, builds guardrails and opens explicit-only capabilities. Trivial edits stay direct.
---
<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/skills/agent-workflow/SKILL.md -->
<!-- Source-SHA256: 0cef4701bd16323cd4a15fd6f971a9499b4c2325b78acb75aa21851d80d2ecf9 -->


# Agent Workflow

Deliver the outcome inside the authorized scope, prove it, and report it so the user
can delegate more. Trivial edits (copy, typo, one config value) skip this. When the
prompt context carries a `route`, invoke that Skill first unless the request is a
trivial edit.

## Delivery loop

1. **Scope.** Read the project's AGENTS/index, the Feature Map rules, owners and checks
   for the touched area, and `.harness/decisions.md`. Trace callers and state/data owners through
   FE → API → Domain → storage ([change impact](references/change-impact.md) when
   ownership or contracts are shared).
2. **Acceptance first.** Write or name the checks that decide success. Expected values
   come from the request and documented rules, never from running the new code. Confirm
   they fail on the current code for the intended reason, or say why that is infeasible.
3. **Fix at the owner, on every path.** List every place that writes or enforces the
   same rule (callers, other endpoints, triggers, imports, background jobs) and cover
   each with a check. A rule stated for all saves or all users applies to every such
   path; exempting one (for example restore or import) is the user's decision, so ask
   instead of deciding it. A guard is a fix only when that state can
   legitimately occur. Revert changes made for a refuted hypothesis; after two failures
   on one premise, test the premise.
4. **Prove the checks catch the defect.** The step-2 failure is the proof. For tests
   written after the change, run `python <this Skill's directory>/scripts/probe_check.py prove --root <project> --base HEAD --tests <tests> --command "<test command>" --skip-current`:
   the tests must fail without the source change. Pass ignored dependency directories
   with `--link node_modules` instead of creating links in the copy yourself. For a
   business, architecture or UI rule worth protecting, add a probe to
   `.harness/probes.json` and run `probe_check.py probes`; a surviving probe means the
   rule is not protected yet.
5. **Run affected existing checks once, after the final edit:** the new tests, the
   Feature's registered checks and existing tests of the changed modules on every
   touched layer, in one batch; rerun only what a later edit affects. New tests alone are not completion. Open a browser only
   for a visual or interaction change no automated UI test covers.
6. **Independent check.** For a behavior change, a fresh verifier gets only the request
   verbatim and the diff ([independent check](references/independent-check.md)). Fix
   the violations its failing tests show and register each as a probe; a stricter
   reading goes to *User decisions*.
7. **Report the result card.**

Settle what running code can answer by experiment. Ask the user only for business
value, scope and irreversible or outward-facing actions. Playbooks:
[feature](playbooks/feature.md), [bug fix](playbooks/bug-fix.md),
[refactoring](playbooks/refactoring.md).

## Result card

At most about 15 lines; keep observed results, inference and unverified claims apart.
Fixture, product, package and native-host evidence are different evidence.

```
Request → changed behavior: <one line>
Affected: <Feature / rule IDs> | business: <FE/API/Domain> | architecture: <boundary or owner>
Checks after the final edit: <check> ✓/✗ (command, raw location)
Proof: <tests fail without the change ✓ | probe <id> killed ✓ | not run: reason>
Paths covered: <writers/enforcers checked, or the uncovered one>
Independent check: <complete | N violations → M fixed (probes: ids), K for user decision (tests: paths) | not run: reason>
Unverified: <what was not observed and why>
User decisions: <decision, recommendation, what happens without an answer> or none
```

## Other requests

- **What is verified:** render `lookup --report` (task) or `audit --report` (project)
  with the bundled [CLI](scripts/project_workflow.py) and answer from it. When probes
  exist, add the `probe_check.py probes` matrix (killed/total per business/architecture/UI × layer;
  *Origins* shows how many came from independent checks or feedback). Include the area's
  `.harness/decisions.md` lines. NOT_CONNECTED: say so and offer setup. Ask the
  report's *Questions for the user* in the same turn and record the answers. Run no
  tests, repairs or services for a results request.
- **Correction or a turn worth repeating:** [feedback and success reuse](references/feedback-and-success.md).
  A first clear correction is enough; praise alone is not a rule request.
- **Answer to a User decision:** record it per [recorded decisions](references/independent-check.md#recorded-decisions) before acting.
- **UI standards:** the project guide and its tokens/components own values; follow
  [UI discovery and comparison](references/repair-and-reuse.md#ui-discovery-and-comparison);
  a drift guardrail is a lint or visual check plus a probe it rejects.
- **Guardrail:** express the rule in the project's linter, type system or test runner
  and prove with a probe that it rejects a synthetic violation and still allows nearby
  valid code. A written rule without enforcement is not a guardrail.
- **Existing task state** (only for an existing task or an explicit request): the CLI
  with [workflow obligations](references/workflow-obligations.md) and
  [result lookup](references/result-viewer.md). Never guess among active tasks; lookup
  writes nothing and runs no product command.

Installed resources, global settings, providers and publishing need their own authority.

## Capabilities

Auto-invocable: `diagnose` (incorrect behavior, complaints), `recall` (resume prior
work), `setup-project-verification` (connect verification for a flow),
`fixing-accessibility` (interaction and accessibility). Explicit-only: when the need
arises, read `SKILL.md` in the sibling Skill directory (same parent as this one) and
follow it; if absent, continue here. `architect` design across modules, interfaces or
data ownership · `swarm` parallel work over disjoint files or resuming delegated work
(only when asked or clearly independent; say so) · `multi-agent-review` adversarial
review · `maintain-project-verification` prune, merge or repair checks, Feature Map or guide drift ·
`impeccable` visual design · `vercel-react-best-practices` React/Next.js performance ·
`prototype` runnable experiment · `zoom-out` explain code · `explore-idea` unclear
problem or value · `design-goal`/`execute-codex-goal`/`close-goal` work contracts ·
`setup-agent-harness`/`maintain-agent-harness` harness configuration.
