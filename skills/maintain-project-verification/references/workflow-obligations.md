<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/references/workflow-obligations.md -->
<!-- Source-SHA256: 0eac78272029dbab661a1e68315c51a2b8be64431cd105a36f8afefb520d2c08 -->

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

Feedback and UI intents require at least one explicit `--target`; an omitted target cannot silently turn either into a map-only request. UI targets need a connected standard and actual verification. Source edits during initial mapping also require verification. Removed features remain explicit `removal_review` obligations, including before their first review. Reconcile their reported basis through the same review command, explaining retirement or reassignment and referencing the updated map; deleting a configuration row does not erase the obligation.

`READY_FOR_REVIEW` means mapping links and submitted analysis are current, not product PASS or independently established semantic completeness. Initial map completion does not require all automatic checks. Behavior changes and feedback still require actual verification. Harness maintenance invokes this computation when configured; close refuses unresolved obligations even if the optional CLI was skipped. Nonconfigured projects retain their existing workflow.

A changed-behavior review can reference a task-local `bundle` JSON produced by the result viewer's explicit execution path. Audit reopens its plan/captures/raw/current inputs through read-only bundle inspection, then checks Feature/check IDs and exact registered argv/cwd. Missing, stale or mismatched evidence cannot discharge the obligation. Feedback also needs an observed repair relative to the original basis; a new analysis or PASS flag alone is insufficient. Map/UI meaning and whether a regression covers the reported cause remain review responsibilities, distinct from those mechanical checks.

`accept` returns BLOCKED because no protected verifier identity/policy/results boundary exists on this host. An Agent with equal filesystem authority can modify config/records or skip commands; the local close guard cannot prevent that bypass. A hash, fresh context or submitted PASS is not enforcement. Draft/test/map edits remain allowed; no global hook or general installation is performed.
