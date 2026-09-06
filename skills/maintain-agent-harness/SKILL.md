---
name: maintain-agent-harness
description: Audit Harness mapping, distributed resources, and retained work integrity when maintenance or drift diagnosis is requested. Defaults to reporting; repairs and cleanup follow the user's scope.
---
<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/skills/maintain-agent-harness/SKILL.md -->
<!-- Source-SHA256: 84c5c8303da708960cd2c39c0b934b706b7d7d601830525088c4e09d1d808774 -->


# Maintain Agent Harness

Use [the runtime](scripts/core_harness.py). Choose `audit-work` for lifecycle-only questions or `maintain` for repository/cohort integrity. Read the [project](schemas/project.schema.json) or [work](schemas/work.schema.json) schema only to interpret relevant findings; [testing policy](references/testing-policy.md) applies if a repair changes behavior.

Report deterministic findings with affected paths, consequences, and the smallest useful repair. Inspect installed cohort hashes only when installation is in scope and its actual root is known. A missing environment-exception file is a no-op; invalid entries are findings. Exact unexpired brownfield baselines may suppress known findings. Scope conclusions to the integrity checks actually performed.

An ordinary audit is read-only. If the user also requested repair, proceed with covered reversible fixes and their relevant checks. Maintenance is on demand, not a prerequisite for routine implementation.

When retention cleanup is requested, use the `close-goal` runtime's sweep to move manifest-expired completed work to recoverable trash. Unknown or contradictory legacy state stays unclassified. Physical deletion needs explicit authorization for the exact target. Worktree removal and production changes are separate scope.
