---
name: recall
description: Recover a project's goal, decisions, last completed work, remaining work and execution state from handoff or accessible records, then reconcile with the current checkout. Use for remembering where work stopped or continuing prior work; recall itself is read-only.
disable-model-invocation: true
---

# Recall

Recover the starting point for the requested project/topic, not a history of every
session. Use a sufficient supplied handoff directly and verify only its currentness;
do not search again for information already supplied. Otherwise search accessible
project notes, task records or conversation records within the relevant topic and
period. Do not assume a host-specific transcript directory, MCP or model.

Read current branch/HEAD and dirty changes, the exact relevant task and any linked
execution records. Never select a different active task because it is nearby.
Compare source/criteria/runtime identity and raw availability before reusing results.
An old PASS is historical; changed conditions are stale, missing evidence is
unverifiable, no execution record is absent, and an unfinished launch is unknown.
A recorded PID alone does not establish current ownership or completion. Preserve
contradictions, inaccessible records and missing history instead of filling gaps.

Give a short evidence-linked handoff: original goal and constraints, decisions and
their reasons, last confirmed completion, unfinished/failed/unknown work, current
differences, and the next useful action. Distinguish confirmed records from inference
and unknowns. Past approval remains scoped to its original action/purpose/budget;
never transfer it or a preference to another task as authority. Do not copy secrets
or unnecessary transcript text, create a memory DB, or write automatic memory.

Recall/lookup alone runs **zero product commands** and writes no task, state or
evidence. Do not rerun commands found in records. Existing project lookup tools may
be used only in their read-only mode; reading Git/files is not product execution.
Missing records need a bounded gap report, not setup or invented completion.

When the user actually asks to resume, finish recovery then take the authorized
next action through the project's existing execution flow or `agent-workflow`
(`execute-codex-goal` for an existing Harness contract). Reuse valid evidence and
completed checkpoints. For delegated work with assignment ownership, outstanding
workers or integration to reconcile, use an available `swarm` capability; recovery
alone does not require spawning more agents. First reconcile a pending launch with its owning process,
raw output or observable effects; never resend an unknown effect. If only that
action is blocked, continue independent authorized work and state what evidence
would unblock it. A recall-only question ends with the handoff, not execution.
Do not force recall, zoom-out and architect into a fixed sequence.
