# Harness v3 Architecture

## Control plane

`.harness/project.yaml` is JSON-compatible YAML with schema version 3. It owns mapped roots, command descriptors, source-to-test impact, Full triggers, document boundaries, retention, Git policy, baseline debt, and the active cohort. Unknown normative fields are rejected; provider extensions belong under `extensions`.

## Work contract and reviews

`contract.json` is the canonical, language-independent Item contract. Every Item has stable identity, a concrete changed outcome, ordered behavior steps, terms, observable tests, completion criteria, dependencies, non-goals, decision state, risk, and core/optional priority. Design and Result HTML are Korean decision documents with the same IDs and order; they must preserve this behavioral depth instead of reducing Items to keyword status cards.

Design reads in decision order: changed outcome, behavior design, verification scenarios, completion criteria, then material dependencies, boundaries, and risks. Result reuses the behavior visual and adds observable outcomes, behavior-level check summaries, criterion-by-criterion evidence, and the concrete planned-versus-actual impact. Exact commands remain secondary evidence. Internal digests bind approval but are not shown to humans.

## Runtime and state

The runtime selects dependency-ready core Items before optional Items, preserves the dirty baseline, runs Impacted checks, and commits verified Items separately. A host Goal may track continuation but is not execution authority. Low-risk user changes become `approved_amendment`; material or high-risk deltas need focused approval.

```text
.work/goals/active/<id>
  -> completed/YYYY-MM/<id>
  -> trash/YYYY-MM-DD/<id>
  -> deleted (exact-target approval only)
```

Manifest dates, not filesystem timestamps, drive retention. Transaction journals make broad setup and migration changes recoverable. `legacy-unclassified` is outside automatic retention.

## Distribution

`authoring/` is canonical. `scripts/sync-skill-resources.ps1` generates self-contained public resources and the manifest. A cutover changes the active Skill instructions, shared implementation, schemas, templates, and manifest as one cohort.
