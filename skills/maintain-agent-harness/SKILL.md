---
name: maintain-agent-harness
description: Report deterministic Harness resource, mapping, and work-lifecycle integrity.
---
<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/skills/maintain-agent-harness/SKILL.md -->
<!-- Source-SHA256: ad70e9204ee439f966dd24f50cf9480b11d031aadf63cfc03e25d9da27b134f5 -->


# Maintain Agent Harness

Use [the runtime](scripts/core_harness.py), [the project schema](schemas/project.schema.json), [the work schema](schemas/work.schema.json), and [the testing policy](references/testing-policy.md). Default to the `maintain` report-only command.

Audit instruction mirrors, direct `docs/index.md` links, unmapped impact surfaces, the exact installed cohort tree, retired Harness names, typed work namespaces, transaction markers, branch/worktree state, and the optional ignored `.harness/environment-exceptions.json`. A missing exception file is a no-op; an invalid file is a finding. Optional brownfield baselines may suppress only exact unexpired findings; selector budgets and broad architecture analysis are not default maintenance gates.

A deterministic safe sweep may move manifest-expired `completed` work to recoverable `trash`; it is idempotent and uses manifest dates. Unknown or contradictory legacy dates move to `legacy-unclassified` and are never swept automatically. Physical trash deletion requires explicit approval of the exact target and reports that recovery is no longer available.

Never rewrite production/test/document content, remove worktrees, or delete trash during an ordinary maintenance audit.
