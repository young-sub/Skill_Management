# Harness v3 Architecture

## Control plane

`.harness/project.yaml` is JSON-compatible YAML with schema version 3. It owns mapped roots, command descriptors, source-to-test impact, Full triggers, document boundaries, retention, Git policy, baseline debt, and the active cohort. Unknown normative fields are rejected; provider extensions belong under `extensions`.

## Work contract and reviews

`contract.json` is the canonical, language-independent Item contract. Every Item has stable identity, a concrete changed outcome, ordered behavior steps, observable verification, and stable Done criteria. Terms, dependencies, non-goals, structured risk flags, and priority are present only when relevant. Contracts contain one to five Items. Design and Result HTML are Korean decision documents with the same IDs and order.

Each Item exposes four primary blocks only: purpose, process, tests, and expected or actual result. The purpose block may explain unfamiliar terms and material non-goal or risk boundaries. Design test tables state what is verified, how it is tested, and the observable pass condition. Result tables state what was verified and what was observed. Exact commands, criterion-level evidence, internal priority, and non-material plan deltas remain in agent records. Internal digests bind default or explicit authorization but are not shown to humans. Arbitrary caller-supplied HTML is never an authorization input; the server renders the canonical Review. Veto and structured high-risk boundaries fail closed.

## Runtime and state

The runtime selects dependency-ready core Items before optional Items, records only Git-reported staged/unstaged/deleted/non-ignored untracked baseline entries, runs Impacted checks, and commits verified Items separately. Planned test and Done IDs must match retained evidence one-to-one. A host Goal may track continuation but is not execution authority. Low-risk user changes become `approved_amendment`; material or high-risk deltas need focused approval.

```text
.work/goals/active/<id>
  -> completed/YYYY-MM/<id>
  -> trash/YYYY-MM-DD/<id>
  -> deleted (exact-target approval only)
```

Manifest dates, not filesystem timestamps, drive retention. Transaction journals make broad setup and migration changes recoverable. `legacy-unclassified` is outside automatic retention.

## Distribution

`authoring/` is canonical. `scripts/sync-skill-resources.ps1` generates self-contained public resources and the manifest. The public runtime exposes JSON CLI commands for authorization, cleanup/recovery, baseline/start/complete/commit, close/sweep/delete, maintain, and cutover. A cutover changes the active Skill instructions, shared implementation, schemas, templates, manifest, and installed cohort atomically.
