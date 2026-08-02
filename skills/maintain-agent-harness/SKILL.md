---
name: maintain-agent-harness
description: Audit Harness v3 configuration, mappings, resources, work lifecycle, baselines, branches, and worktrees.
---

# Maintain Agent Harness — Harness v3

Use [the runtime](scripts/core_harness.py), [the project schema](schemas/project.schema.json), [the work schema](schemas/work.schema.json), and [the testing policy](references/testing-policy.md). Default to the `maintain` report-only command.

Audit instruction/resource cohort drift, `docs/index.md` reachability and authority, source-document boundaries, source-to-test mapping and selector budgets, baseline fingerprints, typed work namespaces, transaction markers, branches, and worktrees. Report new/worsened findings separately from exact unexpired baseline debt.

A deterministic safe sweep may move manifest-expired `completed` work to recoverable `trash`; it is idempotent and uses manifest dates. Unknown or contradictory legacy dates move to `legacy-unclassified` and are never swept automatically. Physical trash deletion requires explicit approval of the exact target and reports that recovery is no longer available.

Never rewrite production/test/document content, remove worktrees, or delete trash during an ordinary maintenance audit.
