# Parallel handoff

How `swarm` partitions, launches, reconciles and integrates parallel assignments. Moved here unchanged in 0.2.1.

Deliver one integrated working result, not a collection of agent verdicts. Use
available host delegation and project tools within the user's authority. If real
agents are unavailable, perform useful sequential work and disclose the limit;
never simulate parallel agents. No new router, runner, task database or mandatory
contract is needed.

A delegated-work continuation may need only the main agent to reconcile existing
assignments and integration evidence. Do not spawn replacements for completed or
unknown work merely because this Skill supports parallel implementation.

## Partition before launch

Bind the request to the named project, current branch/commit, dirty files and
active executions. Recover an existing handoff before creating more work. Select
the exact existing task/context when applicable; unrelated active work is not
this assignment. Reuse project instructions, criteria and verification commands.

For each bounded assignment, give the worker:

- Purpose and observable outcome; raw inputs and the agreed interface.
- Exclusive writable files/worktree, read-only dependencies and forbidden paths.
- Prerequisites and which assignments must finish before this one can start.
- Completion and failure criteria, relevant checks and required raw evidence.
- Who reviews the change, who integrates it, and the return artifact: diff/commit,
  files changed, commands/results, deviations from the brief, every provable issue
  found (not only the first), unresolved issues and execution handles.
- A timebox: on expiry return partial results and stop. Acceptance checks and
  fixtures are read-only for the worker; it may not edit the oracle to pass.

A mechanical edit a script can apply in one pass is scripted, checked on one unit
against a hand-made edit, then run; it is not split across agents by hand. A revision
round goes to a fresh worker with one brief merging the original instructions, every
later instruction and the previous report, so no instruction silently drops.

Keep this in the existing task/handoff or conversation for short work. The main
agent owns the dependency list and integration; worker completion is provisional.
Do not send previous candidate answers to an independent reviewer.

Parallelize only dependency-ready work with disjoint write ownership. Shared
interfaces, manifests, generated files, lockfiles and task records have one writer.
Set the interface first, then parallelize consumers; otherwise keep them sequential.
Reuse existing worktree support when isolation helps. Separate branches do not
remove semantic conflicts. In a shared checkout prohibit workers from checkout,
reset, broad staging, committing others' files or changing shared configuration.
If scope crosses ownership, the worker returns the needed change to the integrator
instead of editing it. Record any reassignment before another writer starts.

## Execute and reconcile

Use the host's spawn/message/wait/resume tools and keep each returned agent/session
identifier. Reuse project runners and task/context commands; do not have multiple
workers update the same task state. Agent reports point to evidence, not proof.
The main agent checks actual diffs, ownership and raw results before integration.

On interruption, failure or resume, inventory every assignment against its
artifact, current source, execution handle and observed effects:

| Observed state | Next action |
| --- | --- |
| Not started, prerequisites satisfied | Launch once with the recorded ownership. |
| Still running | Contact/wait on its existing owner; do not launch a replacement. |
| Completed with current evidence | Reuse the checkpoint and inspect its artifact; do not replay effects. |
| Failed with known terminal state | Preserve failure; repair its owner, then retry only the missing/failed scope with new evidence. |
| Launch/effects unknown or owner unreachable | Inspect retained process/output/state and effects read-only. Keep unresolved work unknown; do not blindly resend. Continue independent safe work. |
| Source/interface changed since completion | Reassess affected evidence and rerun only invalidated checks; do not automatically redo implementation or external effects. |

Task lookup/resume reads retained state; execution resume is a separate operation.
Use existing checkpoint-aware execution only after reconciling the selected plan
and its owner. A timeout, missing reply or agent restart is not proof that nothing
ran. Preserve failed, retried, stopped, unexecuted and unknown assignments in the
handoff; do not erase them when a later attempt succeeds.

## Integrate and verify

Integrate in dependency order under one owner. Inspect overlapping files and
semantic conflicts (interfaces, ordering, shared state), preserving user changes.
Resolve conflicts explicitly; do not take one side wholesale or overwrite dirty
files. Review the integrated diff against the original outcome and every assignment
to catch omitted work. Use `multi-agent-review` only when independent challenge is
needed and authorized; it does not own implementation scheduling or integration.

Run affected checks against the integrated tree, including the user flow across
changed boundaries and meaningful failures. Where storage is affected, inspect
fresh reads after success and rejected writes. Separate worker-local results from
integration evidence. Follow project commit policy only after that evidence holds.

Report delivered behavior, reused checkpoints, conflicts/rework, outstanding work
and evidence. When comparing sequential/parallel work, freeze equal task inputs,
criteria, tools and evidence scope before launch; count missed defects, false
completion, user intervention, rework, conflicts and duplicate effects. Retain all
attempts and skill non-use. Uncollected time/usage/cost stays unknown. Catalog
discovery, assisted execution and native-host unaided discovery are distinct claims.
