---
name: swarm
description: Run several delegated tasks in parallel, each in its own worktree with a sealed acceptance contract, starting new ones only while the person's review queue has room; or resume interrupted parallel work by reconciling ownership, evidence and integration. Small coupled edits stay sequential.
disable-model-invocation: true
---
<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/skills/swarm/SKILL.md -->
<!-- Source-SHA256: f549969de51ee6e46bd0d91af2a02e8be8618603b34c96f0571f0cea2f0dcbd0 -->


# Swarm

Parallelize between tasks, not inside one: agent teams on a single task cost about two to five
times as much and rarely beat one agent, and shared locks or an integrator role became the
bottleneck. Each task runs the `agent-workflow` delegation loop in its own `git worktree`, with its
own sealed contract and risk tier.

1. **Start only within capacity.** Before starting a task, run
   `python <agent-workflow directory>/scripts/risk_gate.py capacity --root <checkout> --onto <integration ref>`.
   It counts open correctness questions (`## Open questions` in `.harness/decisions.md`) and
   unmerged branches whose tip says `Risk: HIGH` or `Risk: MED`, and exits nonzero when any count
   reaches its limit. The limits bound the person's queue; they do not remove the bottleneck,
   which only shrinks when fewer tasks reach the person.
2. **Disjoint tasks only.** Do not start two tasks that change the same files or Feature; set a
   shared interface first, then run its consumers.
3. **Integrate by tier** as `agent-workflow` step 6 says, one integration at a time; a LOW
   re-check is against the integration tip after the previous merge.

For partitioning one large change across agents, reconciling an interrupted handoff and
integration order, follow [parallel handoff](references/parallel-handoff.md).
