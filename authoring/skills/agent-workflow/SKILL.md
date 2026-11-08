---
name: agent-workflow
description: Verify a behavior change in the current tree with the project's own checks, then report what is verified. Follows the feature, bug-fix or refactoring playbook, proves new checks against a known fault, sends the verbatim request and diff to an independent verifier, and opens explicit-only capabilities. No hooks, sub-agent stages or task queue.
disable-model-invocation: true
---

# Agent Workflow

For behavior changes the person wants verified. Trivial edits and conversational work stay
direct: the person is there to judge them.

## Change loop

Work in the current tree; nothing here holds the order or blocks a tool call.

1. **Request.** Restate the requested behavior. State assumptions about ambiguous rules as
   input → expected-result examples; ask only when a wrong guess is hard to undo.
2. **Playbook.** Follow the [feature](playbooks/feature.md), [bug fix](playbooks/bug-fix.md)
   or [refactoring](playbooks/refactoring.md) playbook: the check comes first and fails for the
   reason the request names.
3. **Prove the check.** `python <this Skill's directory>/scripts/probe_check.py prove` shows the
   new check rejects a known fault while the base passes.
4. **Run the project's checks** after the final edit; keep the command and raw location.
5. **Independent check** for behavior changes: dispatch the [verifier](references/independent-check.md)
   with only the verbatim request and diff. A finding counts when it comes with a reproducible
   failing case; fix it or turn it into a user decision.
6. **Report** the card below.

## Result card

Separate facts, inference and unverified claims (about 12 lines).

```
가정/Assumptions: <answered questions, defaults taken, or none>
Request → changed behavior: <one line>
Checks after the final edit: <check> ✓/✗ (command, raw location)
Proved against a fault: <check: probe killed | not proved: reason>
Paths covered: <boundary: bypass search empty | each writer's status>
Independent check: <complete | N violations → M fixed, K for user decision | not run: reason>
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
`setup-project-verification`, `fixing-accessibility`, `architect`, `multi-agent-review`, `maintain-project-verification`, `impeccable`,
`vercel-react-best-practices`, `prototype`, `zoom-out`, `explore-idea`,
`design-goal`/`execute-codex-goal`/`close-goal`, `setup-agent-harness`/`maintain-agent-harness`.
Installed resources, global settings, providers and publishing need their own authority.
