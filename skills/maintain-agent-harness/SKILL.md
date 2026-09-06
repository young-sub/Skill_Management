---
name: maintain-agent-harness
description: Audit Harness mapping, distributed resources, and retained work integrity when maintenance or drift diagnosis is requested. Defaults to reporting; repairs and cleanup follow the user's scope.
---
<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/skills/maintain-agent-harness/SKILL.md -->
<!-- Source-SHA256: 4e329e5dd6c143d10c7e54a270e3a195f37cc311ccc0001438ee67c66e158ea7 -->


# Maintain Agent Harness

Use [the runtime](scripts/core_harness.py). Choose `audit-work` for lifecycle-only questions or `maintain` for repository/cohort integrity. Read the [project](schemas/project.schema.json) or [work](schemas/work.schema.json) schema only to interpret relevant findings; [testing policy](references/testing-policy.md) applies if a repair changes behavior.

Report deterministic findings with affected paths, consequences, and the smallest useful repair. Inspect installed cohort hashes only when installation is in scope and its actual root is known. A missing environment-exception file is a no-op; invalid entries are findings. Exact unexpired brownfield baselines may suppress known findings. Report success as the checks performed, not proof of product correctness or model performance.

An ordinary audit is read-only. If the user also requested repair, proceed with covered reversible fixes and their relevant checks; do not stop merely because this skill defaults to reporting. Do not make routine implementation wait for a full maintenance audit, architecture review, or selector budget exercise.

When retention cleanup is requested, use the `close-goal` runtime's sweep to move manifest-expired completed work to recoverable trash. Unknown or contradictory legacy state stays unclassified. Physical deletion needs explicit authorization for the exact target. Worktree removal and production changes are separate scope.
