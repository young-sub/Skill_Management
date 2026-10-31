---
name: agent-workflow
description: Delegate a coding task so it can be accepted without reading the diff. Acceptance tests are written apart from the implementation and sealed before it; a check outside the session runs them, reverts each changed hunk and reports untested changes and uncovered requirements. Also shows what is verified, reuses UI standards, builds guardrails and opens explicit-only capabilities.
disable-model-invocation: true
---
<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/skills/agent-workflow/SKILL.md -->
<!-- Source-SHA256: c5d88a278f398ad5d7254c9e63ef04fe736dddf26b73e2df3b1c0f3509465123 -->


# Agent Workflow

For delegated behavior changes. Trivial edits and conversational work stay direct:
the person is there to judge them.

## Delegation loop

1. **Author.** Before implementing, launch a fresh sub-agent with the
   [author template](references/acceptance-author.md). It sees the verbatim request,
   `.harness/decisions.md` and the base commit, never the implementation, and returns
   acceptance tests outside the worktree, scenarios, questions and every write path the
   rule applies to.
2. **Questions.** Correctness questions are answered before sealing (headless: stop and
   list them under *User decisions*). Preference questions take their default and go to
   the `## Pending` section of `.harness/decisions.md`.
3. **Seal.** `python <this Skill's directory>/scripts/acceptance_gate.py seal --root <worktree>
   --base <base> --tests <outside>/<path>=<path> ... --command "<runner>"
   [--report <junit.xml|vitest.json>] --scenarios <file> [--link node_modules] [--preserve]`.
   It refuses tests that do not fail on the base by assertion (with `--preserve`, that
   do not pass on it). Re-author a refused test; never weaken it.
4. **Implement** from the scenario text only: the tests and the author's write-path list
   stay with the gate, so the implementer's own search for paths is checked, not copied.
   Fix at the owner. Enforce a rule on stored data at one boundary every writer crosses
   (DB constraint or single owner) and confirm a search for writes bypassing it (SQL, ORM,
   import/restore jobs; `LSP findReferences` if available) finds none; otherwise list each
   writer's status. Run the affected existing checks after the final edit.
5. **Check.** `acceptance_gate.py check --root <worktree>`; the Claude Code Stop hook runs it,
   in Codex run it before finishing. Fix the implementation, never the sealed tests;
   after three failed checks the contract is `STOPPED` until a person re-seals it.
6. **Tier.** `python <this Skill's directory>/scripts/risk_gate.py classify --root <worktree>
   --base <integration ref>` reads `.harness/risk.yaml` from that ref (none: copy
   [the template](templates/risk.yaml) and let the person commit it) and prints LOW, MED or HIGH.
   - LOW: commit with the `risk_gate.py trailers` lines, then `risk_gate.py recheck --root <worktree>
     --onto <integration ref> --regression "<affected check>"` must pass; integrate only while the
     integration tip still equals the `onto` it reports. No card unless asked.
   - MED: commit with trailers; the person reviews MED work in a daily batch from the cards.
   - HIGH: dispatch the [verifier](references/independent-check.md) with only the verbatim
     request and diff; the person approves before integration.
   Without a sealed contract, every behavior change gets the verifier.
7. **Report** the result card for MED, HIGH or on request.

Without a sub-agent or a runnable test command, say so on the card and fall back to the
[playbooks](playbooks/feature.md) ([bug fix](playbooks/bug-fix.md),
[refactoring](playbooks/refactoring.md)) with `probe_check.py prove`.

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
