---
name: agent-workflow
description: Delegate a coding task so it can be accepted without reading the diff. A deterministic state machine orders the work and hooks enforce it; acceptance tests are written apart from the implementation and sealed before it; a check outside the session runs them, reverts each changed hunk and reports untested changes and uncovered requirements; risk tiers decide what a person reviews. Also shows what is verified, reuses UI standards, builds guardrails and opens explicit-only capabilities.
disable-model-invocation: true
---
<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/skills/agent-workflow/SKILL.md -->
<!-- Source-SHA256: 2efd771dabd49457e05bc046c2f4f6c462373e08acb4a61c449b938043bd2818 -->


# Agent Workflow

For delegated behavior changes. Trivial edits and conversational work stay direct:
the person is there to judge them.

## Delegation loop

[`scripts/delegate.py`](scripts/delegate.py) holds the order; it calls no model. You launch
the sub-agents it prints prompts for, and the plugin's hooks advance it when they stop and
refuse tool calls the current stage does not allow. `D` below is
`python <this Skill's directory>/scripts/delegate.py`, always with `--root <repository>`.

1. **Queue.** `D queue add --id <task> --request-file <verbatim request> [--feature F]
   [--paths <globs>] [--link node_modules] [--preserve]` (`--preserve` for refactoring).
2. **Start.** `D next [--onto <integration ref>]` starts the first task that capacity allows
   (open correctness questions and unreviewed HIGH/MED below their limits, no running task on
   the same Feature or overlapping paths) in its own worktree, and prints the author's prompt.
3. **Author.** Launch it verbatim: Claude Code `Agent` with `subagent_type`
   `agentic-coding:acceptance-author`; Codex a sub-agent given the prompt, not a fork. The
   author writes tests and `result.json` where you cannot read them and replies `done`
   ([why](references/acceptance-author.md)). Its stop seals the tests; a test that does not
   fail on the base by assertion goes back to it.
4. **Questions.** Correctness questions wait for the person (`D status`, `D digest`); record
   each answer with `D answer --id <task> --question Q1 --text "..."` and relaunch the author
   with the prompt it prints. Preference questions take their default and appear in `D digest`.
5. **Implement.** `D implement --id <task>` prints the implementer's prompt (request and
   scenario text, never the tests or write paths); launch `agentic-coding:implementer` (Codex:
   a sub-agent). Its stop runs the sealed check; a failure goes back to it, and three failures
   stop the task for a person.
6. **Tier.** A passing check is classified under the integration ref's `.harness/risk.yaml`
   (none: the built-in HIGH list and nothing LOW; copy [the template](templates/risk.yaml) for
   the person to commit) and committed with `Agent-Task`, `Risk` and `Acceptance` trailers.
   - LOW: `D integrate --id <task> [--into <checked-out branch>] [--regression "<check>"]`
     rechecks on the integration tip and merges locally; nothing is pushed. No card unless asked.
   - MED: the person reviews the cards in `D digest` as a daily batch.
   - HIGH: dispatch the [verifier](references/independent-check.md) with only the verbatim
     request and diff; the person approves before integration.
7. **Report** the card from `D status --id <task>` for MED, HIGH or on request.

Failure events enter the same queue: `D event scan --base <integration ref>` (reverts),
`D event add --kind check-failure|correction --detail "..."`, and `D event finding --key <k>`
(a third occurrence queues a task to turn the finding into an executable check). Stopped
tasks wait for the person's `D resume`.

Without sub-agents or a runnable test command, say so on the card and fall back to the
[playbooks](playbooks/feature.md) ([bug fix](playbooks/bug-fix.md),
[refactoring](playbooks/refactoring.md)) with `probe_check.py prove`; sealing by hand is
`scripts/acceptance_gate.py seal`/`check`. Without a sealed contract, every behavior change
gets the verifier.

## Result card

Separate facts, inference and unverified claims (about 15 lines).

```
가정/Assumptions: <answered questions, defaults taken, or none>
Request → changed behavior: <one line>
Acceptance: <PASS (stated checks, contract hash) | FAIL | TAMPERED | STOPPED: reason | not sealed: reason>
Risk: <LOW | MED | HIGH: reasons from risk_gate.py>
Untested changes: <file hunk ... | none>
Uncovered requirements: <scenario ... | none>
Checks after the final edit: <check> ✓/✗ (command, raw location)
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
`setup-project-verification`, `fixing-accessibility`, `architect`, `swarm`, `multi-agent-review`, `maintain-project-verification`, `impeccable`,
`vercel-react-best-practices`, `prototype`, `zoom-out`, `explore-idea`,
`design-goal`/`execute-codex-goal`/`close-goal`, `setup-agent-harness`/`maintain-agent-harness`.
Installed resources, global settings, providers and publishing need their own authority.
