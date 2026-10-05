# Project workflow obligations

Existing project config owns `extensions.workflow`; a task record under `.work` retains review progress. The bundled `scripts/project_workflow.py` computes obligations from current bytes and registered connections without calling a model. Requirements, feature meanings, causes and visual judgments remain Agent work. Review records are Agent inputs, not authenticated proof.

```json
{"extensions":{"workflow":{
  "roots":["src","scripts"],
  "state":".work/current/feature-review.json",
  "features":[{
    "id":"product-save","partition":"products",
    "sources":["src/products/*","src/shared/prices.py"],
    "map":["docs/feature-map.md"],"criteria":["docs/products.md"],
    "checks":["product-save"],"ui":["docs/ui.md"],
    "prevention":[{"failure":"negative price accepted","check":"product-save","normal_exception":"zero is allowed"}]
  }]
}}}
```

Check IDs reference existing commands or `impact.feature_selectors`. Shared sources may belong to several Features. Git-visible files inside declared roots must have owners; this does not prove the declared product boundary or semantic survey is complete. Keep credentials, databases and generated output outside inventory roots. Private paths, aliases and outside-root references are rejected. Empty checks explicitly mean unconnected coverage. Map documents own user/role/trigger, requirements, invariants, variants, state/data responsibilities, structural guarantees and verification gaps; the config owns only machine links.

```text
python <skill>/scripts/project_workflow.py begin --root <project> --state .work/current/feature-review.json --intent init
python <skill>/scripts/project_workflow.py audit --root <project> --state .work/current/feature-review.json
python <skill>/scripts/project_workflow.py review --root <project> --state .work/current/feature-review.json --review <analysis.json>
```

`begin` preserves a matching existing record and its dirty baseline. `audit` writes nothing and launches no checks. A review contains `feature`, exact current `basis`, concrete `analysis`, existing `references`, and `findings`. Stale reviews are refused. Partitions remain PARTIAL until links and review inputs reconcile. Source, criteria, command, map and shared UI changes invalidate consumers; unrelated documents do not. Paths never select Full automatically.

For configured Harness work, normal `start` captures the workflow baseline inside
its existing atomic `work.json` write; a separate workflow begin is unnecessary.
Use `audit` or `review --root <project> --work-id <id>` to consume that baseline.
Review progress is stored in the work directory's `workflow.json`; audit does not
create it. Resume never replaces the baseline, and a conflicting review record is
rejected. Close checks this per-work state directly, even when the optional CLI
was not called, and refuses a missing workflow configuration for such work.
Existing legacy work without this baseline retains its configured-state check.

At start, current semantic reviews from the project's configured state can be
reused; changed inputs still require review and changed behavior requires actual
execution. Prior behavior PASS is not a shortcut for new changes. Source hashes
remain in the retained manifest; the start response returns only a compact work
ID/state reference. This integrates existing Harness work, not every host's
natural-language request lifecycle. Projects without this extension stay direct.

Feedback and UI intents require at least one explicit `--target`; an omitted target cannot silently turn either into a map-only request. UI targets need a connected standard and actual verification. Source edits during initial mapping also require verification. Deletions, including staged deletions absent from the current Git inventory, are matched against Feature source patterns using the retained baseline; a new semantic review alone cannot discharge their verification. Removed features remain explicit `removal_review` obligations, including before their first review. Reconcile their reported basis through the same review command, explaining retirement or reassignment and referencing the updated map; deleting a configuration row does not erase the obligation.

`READY_FOR_REVIEW` means mapping links and submitted analysis are current, not product PASS or independently established semantic completeness. Initial map completion does not require all automatic checks. Behavior changes and feedback still require actual verification. Harness maintenance invokes this computation when configured; close refuses unresolved obligations even if the optional CLI was skipped. Nonconfigured projects retain their existing workflow.

New records retain each Feature's initial source patterns as well as file hashes,
so narrowing a source map after deletion does not erase its original consumer.
For older records without those patterns, deletion still matches current owners.
An unmatched deleted path reports `baseline_source_ownership_unavailable` rather
than silently accepting the work. Recover its original Feature connections from
the retained baseline before reconciling that legacy record; do not replace the
baseline with current files to clear the finding.

Begin/review writes use a unique task-local temporary file followed by replacement. Harness review attempts stage under `.work` outside the strictly validated active-work artifact directory, so an orphan cannot prevent Harness resume. Abrupt process exit leaves the previous valid state intact (or no initial state), and a fresh invocation can resume without deleting an orphan attempt. One writer owns a task record; concurrent writes to the same record are not supported. Interrupted attempt files remain subject to the existing `.work` retention policy.

Inspection validates review analysis, findings and existing references as well as
the current basis. Writing a minimal success-shaped record directly cannot omit
those fields. This checks record completeness, not whether its semantic analysis
is correct; editable manifests, policy and reviews are not authenticated evidence.

A changed-behavior review can reference a task-local `bundle` JSON produced by the result viewer's explicit execution path. Audit reopens its plan/captures/raw/current inputs through read-only bundle inspection, then checks Feature/check IDs and exact registered argv/cwd. Missing, stale or mismatched evidence cannot discharge the obligation. Feedback also needs an observed repair relative to the original basis; a new analysis or PASS flag alone is insufficient. Map/UI meaning and whether a regression covers the reported cause remain review responsibilities, distinct from those mechanical checks.

`accept` returns BLOCKED because no protected verifier identity/policy/results boundary exists on this host. An Agent with equal filesystem authority can modify config/records or skip commands; the local close guard cannot prevent that bypass. A hash, fresh context or submitted PASS is not enforcement. Draft/test/map edits remain allowed; no global hook or general installation is performed.
# Native unittest evidence

Projects using the existing unittest adapter can bind captures with
`verify_product.py --feature <id> --check <id> --output <new-capture> --bundle-output <new-bundle>`.
For every check registered to one Feature, use `--all-checks --output <new-directory>`;
the resulting `bundle.json` binds each selected check to its actual native run.
Attach that project-relative bundle path to the semantic review's `bundle` field.
Workflow audit uses the same native unittest assessor to reread stdout, exit,
counts, skips, exact target and current Git identity. It never runs the suite or
loads project code during lookup, and ignores submitted bundle verdict fields.
The native-JSON path remains available for browser/API/DB observations.
Unittest captures establish only their assertions; ignored inputs, dependencies,
live runtime identity and protected acceptance require separate evidence.
