# Harness Architecture

## Control plane

`.harness/project.yaml` is JSON-compatible YAML. Its internal schema version is retained for machine compatibility. The file owns mapped roots, command descriptors, source-to-test candidates, Full warning triggers, document boundaries, retention, Git policy, and baseline debt. Unknown normative fields are rejected; provider extensions belong under `extensions`.

Older project files may contain redundant cohort and component-version declarations. The runtime recognizes only the exact known legacy shapes, normalizes them in memory without overwriting the file, and emits a digest-bound transaction for an approved migration. Unknown or mixed declarations fail closed.

## Work contract and authorization

`contract.json` is the canonical, language-independent Item contract. Every Item has stable identity, a concrete changed outcome, ordered behavior steps, observable verification, and stable Done criteria. Terms, dependencies, non-goals, structured risk flags, and priority are present only when relevant. Contracts contain one to five Items.

Ordinary contracts are default-authorized from their canonical payload. Explicit approval is reserved for destructive, security/privacy, secret, irreversible migration, external cost, push, publish, and global-configuration risks. A veto remains bound to the unchanged contract. `result.json` owns machine evidence; the final chat response is the only human-facing Design or Result summary.

## Runtime and state

The runtime selects dependency-ready core Items before optional Items and records only Git-reported staged/unstaged/deleted/non-ignored untracked baseline entries. Impact decisions record changed logic, affected behaviors, scope, and reason. Path rules yield candidates; local/capability scope selects exact tests, cross-cutting scope or an explicit request requires Full, and unknown scope blocks as `unresolved_logic_impact`. Close recomputes cumulative paths from the captured source commit. Independent Item worktrees use deterministic paths under the repository-owned, ignored `/.worktree/` directory; callers cannot place them outside the project. A commit contains the smallest complete functional unit that works from that commit alone; coupled Items sharing runtime, schema, documentation, or generated resources stay together. Planned test and Done IDs must match retained evidence one-to-one. A host Goal may track continuation but is not execution authority. Low-risk user changes become `approved_amendment`; material or high-risk deltas need focused approval. Legacy active work that already contains `review/design.html` remains valid only when the retained bytes match its stored digest; the runtime neither converts nor deletes it.

```text
.work/goals/active/<id>
  -> completed/YYYY-MM/<id>
  -> trash/YYYY-MM-DD/<id>
  -> deleted (exact-target approval only)
```

Manifest dates, not filesystem timestamps, drive retention. Transaction journals make broad setup and migration changes recoverable. `legacy-unclassified` is outside automatic retention.

## Distribution

`authoring/` is canonical. `scripts/sync-skill-resources.ps1` generates self-contained public resources and the manifest. Each installed Skill exposes only its owned commands. When a known command is invoked through the wrong Skill, that entrypoint reports the requested command, owning sibling Skill, and exact sibling script path; there is no shared launcher. The installed cohort is accepted only when its complete observed tree exactly matches the required manifest resource set and hashes; Skill prose is not a compatibility signal. Installation stages and verifies the whole cohort before atomically replacing its owned Skill roots.
