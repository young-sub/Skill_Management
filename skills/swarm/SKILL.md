---
name: swarm
description: Run several delegated tasks in parallel, each in its own worktree with a sealed acceptance contract, starting new ones only while the person's review queue has room; or resume interrupted parallel work by reconciling ownership, evidence and integration. Small coupled edits stay sequential.
disable-model-invocation: true
---
<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/skills/swarm/SKILL.md -->
<!-- Source-SHA256: 1da554a1519b172984cbbc11cd0fa7eb4203e53872f75c7013326d756e941967 -->


# Swarm

Parallelize between tasks, not inside one: agent teams on a single task cost about two to five
times as much and rarely beat one agent, and shared locks or an integrator role became the
bottleneck. Each task runs the `agent-workflow` delegation loop in its own `git worktree`, with its
own sealed contract and risk tier.

1. **Queue every task** with `delegate.py queue add --id <task> --request-file <request>
   --paths <globs> [--feature F]` (in `<agent-workflow directory>/scripts/`).
2. **Start with `delegate.py next`.** It starts the first queued task only while open correctness
   questions and unreviewed HIGH and MED work stay below their limits (`--max-questions`,
   `--max-high`, `--max-med`; the same counts as `risk_gate.py capacity`) and no running task has
   the same Feature or overlapping path globs; a task without globs runs alone. Each starts in its
   own worktree. Launch its author, then later its implementer, as background sub-agents and call
   `next` again; the hooks advance each task when its sub-agent stops. The limits bound the
   person's queue; they do not remove the bottleneck, which only shrinks when fewer tasks reach
   the person.
3. **Integrate by tier**, one at a time: `delegate.py integrate` for LOW rechecks against the
   integration tip after the previous merge; MED and HIGH wait in `delegate.py digest`.

For partitioning one large change across agents, reconciling an interrupted handoff and
integration order, follow [parallel handoff](references/parallel-handoff.md).
