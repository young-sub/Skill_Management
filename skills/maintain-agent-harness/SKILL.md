---
name: maintain-agent-harness
description: Audit Agent Harness instruction, resource, work-state, durable-link, retention, and worktree drift without changing repository state.
---

# Maintain Agent Harness

Run the deterministic report-only audit with an explicit current date:

```text
python scripts/maintain_harness.py --source-root <repository> --current-date <YYYY-MM-DD>
```

When the host already has explicit registered and observed worktree paths, supply a JSON object with `registered` and `observed` arrays through `--worktrees`. Do not scrape ambiguous console output to invent worktree ownership.

The report covers byte drift between `AGENTS.md` and `CLAUDE.md`, tracked durable references into `.work/`, active/archive/trash retention eligibility, mapped resource drift, deterministically broken Markdown relative paths, and explicit residual or unregistered worktree paths.

## Safety

This version is always report-only. Every proposed action has `applied: false`. It does not move, delete, replace, repair, or clean any file or worktree, even when content is stale. There is no Apply implementation in this release.

If remediation is needed, summarize exact targets and evidence and obtain explicit approval for a future apply path. Do not infer deletion authority from a maintenance request or from retention eligibility.
