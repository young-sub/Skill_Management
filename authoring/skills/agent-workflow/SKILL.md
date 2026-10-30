---
name: agent-workflow
description: Deliver delegated coding work across FE, API/backend and business logic with acceptance checks derived from the request, proof that new tests catch the defect, affected existing checks, an independent verifier and a result card. Also shows what is verified, reuses UI standards, builds guardrails and opens explicit-only capabilities. Trivial edits stay direct.
---

# Agent Workflow

Trivial edits stay direct. Invoke the prompt context's `route` Skill first.

## Delivery loop

1. **Acceptance first.** Derive checks from the request and recorded
   `.harness/decisions.md`, not new-code output. List the 1-3 points whose behavior
   admits multiple readings (or none). In interactive sessions ask; in delegated/headless
   work choose a reading and put it on the first `가정/Assumptions` card line.
2. **Fix at the owner.** When enforcing a rule on stored data, find every writer: run `LSP findReferences`
   on the writing function (text search if no `LSP` tool), and text-search table/column writes too
   (SQL INSERT/UPDATE, ORM calls, import/restore jobs). Cover each writer with a check.
3. **Verify.** Run acceptance and affected existing checks after the final edit.
   Use `probe_check.py prove` optionally, when a new test's ability to catch the
   defect is in doubt; pass ignored dependencies with `--link node_modules`.
4. **Independent check.** For behavior changes, dispatch a fresh verifier with only
   the verbatim request and diff using [the template](references/independent-check.md).
   Fix demonstrated violations and register each as a probe; undecided readings go
   to *User decisions*. Run `probe_check.py probes` for registered faults.
5. **Report the result card.**

Playbooks: [feature](playbooks/feature.md), [bug fix](playbooks/bug-fix.md),
[refactoring](playbooks/refactoring.md).

## Result card

Separate facts, inference and unverified claims (about 15 lines).
Distinguish fixture, product, package and native-host evidence.

```
가정/Assumptions: <chosen readings, confirmed answers, or none>
Request → changed behavior: <one line>
Affected: <Feature / rule IDs> | business: <FE/API/Domain> | architecture: <owner>
Checks after the final edit: <check> ✓/✗ (command, raw location)
Proof: <tests fail without change | probe killed | not run: reason>
Paths covered: <writers/enforcers checked, or uncovered>
Independent check: <complete | N violations → M fixed (probes: ids), K for user decision (tests: paths) | not run: reason>
Unverified: <what and why>
User decisions: <decision, recommendation, default> or none
```

## Other requests

- **Results:** use [CLI](scripts/project_workflow.py) `lookup --report` or `audit --report`;
  no tests, repairs or services. Include recorded decisions and ask its user questions.
  NOT_CONNECTED: offer setup. Existing task state only: [obligations](references/workflow-obligations.md)
  and [lookup](references/result-viewer.md); never guess among tasks.
- **Correction/reuse:** [feedback](references/feedback-and-success.md).
- **Decision answers:** [record before acting](references/independent-check.md#recorded-decisions).
- **UI standards:** [project tokens/components](references/repair-and-reuse.md#ui-discovery-and-comparison).
- **Guardrail:** enforce through lint/types/tests; a probe must reject a violation
  while nearby valid code passes.

## Capabilities

Explicit-only: read the sibling Skill's `SKILL.md` when needed; if absent, continue here:
`diagnose` (reported incorrect behavior), `recall` (resume prior work),
`setup-project-verification`, `fixing-accessibility`, `architect`, `swarm`, `multi-agent-review`, `maintain-project-verification`, `impeccable`,
`vercel-react-best-practices`, `prototype`, `zoom-out`, `explore-idea`,
`design-goal`/`execute-codex-goal`/`close-goal`, `setup-agent-harness`/`maintain-agent-harness`.
Installed resources, global settings, providers and publishing need their own authority.
