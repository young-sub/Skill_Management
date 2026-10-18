---
name: agent-workflow
description: Coordinate a coding task from a natural-language request through relevant project capabilities, actual verification, and results. Use for connecting project verification, verifying or viewing feature results, repairing user feedback, improving the development workflow, or reusing UI standards. Select only the needed procedures; ordinary small edits stay direct.
---
<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/skills/agent-workflow/SKILL.md -->
<!-- Source-SHA256: 266b5d29c5c7a00fc4c1eef2ed28bdf67fb0f559ac8db39e3322f8e7063be409 -->


# Agent Workflow

Understand the request and authorized scope, then discover existing project criteria/code/guides, select only needed changes and verification, execute, explain results, and reuse improvements in the next related task. Read AGENTS/index, checkout/dirty baseline and applicable capability exceptions once. Share that investigation across selected capabilities; the user need not name Skills or their order.

| Request | Bounded responsibility |
| --- | --- |
| Initial verification connection | `setup-project-verification`: map the agreed scope and connect existing commands. Whole-map PARTIAL does not block independent scoped work. |
| Implement/change | Existing development flow and touched callers. Connect only a missing verification path; small work needs no contract or full-project setup. |
| Verify | Project guide/adapter and the affected actual user flow. Select from behavior and risk; inspect raw outcomes. |
| Investigate | Existing task can retain read-only observations without workflow setup. Unknown observations stay unknown. |
| Show results | Connect/read existing work. No tests, repairs, services or new task. |
| Maintain | `maintain-project-verification`; also `maintain-agent-harness` only for affected Harness mapping/cohort/retention. |
| Feedback | Existing `diagnose`: actual caller/state/data flow, cause owner, focused repair and appropriate prevention. |
| UI standards | Discover Feature UI references and registered UI systems before proposing changes; reuse shared token/component owners and relevant UI capability. |

For setup/verification/maintenance read [project verification](references/project-verification.md). For feedback/UI read [repair and reuse](references/repair-and-reuse.md). Missing optional capabilities use existing project commands; never count missing checks as passed or turn the task into a tooling installation.

## Select and execute existing work

For ordinary small edits and one-off investigations, use existing project tools and report evidence directly; no new workflow state, setup or contract is required. Use the bundled [workflow CLI](scripts/project_workflow.py) when continuing selected work or when persistent evidence/reuse is needed, with exact input contracts in [workflow obligations](references/workflow-obligations.md). These commands are alternatives, not a required sequence; a lookup-only request never calls `start`:

```text
python <skill>/scripts/project_workflow.py start --root <project> --intent <intent> --target <feature> --request-summary <outcome> --outcome-ref <existing-requirement-file>
python <skill>/scripts/project_workflow.py connect --root <project> --state <exact-task-path>
python <skill>/scripts/project_workflow.py lookup --root <project> --state <exact-task-path> --summary
```

`start` creates work; `connect` selects it. `--state` accepts a relative path or an absolute path within that project's `.work`; registry paths remain relative. Use the returned `task_context` through inherited `AGENT_WORKFLOW_CONTEXT` or `--context`. Harness work uses `--work-id`. Never guess among task candidates. For a related new request, `start` with prior context carries feedback/results and captures a new baseline and request.

For selected workflow work, use only the needed `prepare`, explicit `execute`, `review`, `feedback`, or read-only `lookup`/task `resume` with the same selector. `execute --resume` is an explicit effect: completed checkpoints are reused, unknown launches are never replayed. A stale write must be reread and explicitly reapplied, not blindly retried.

When an unconfigured investigation needs a persistent record, use `start --intent diagnose --request-summary <request> --investigation <observations.json>`; later `investigate` updates that record. Otherwise a concise evidence report is enough. Missing observations remain INCOMPLETE. Preserve permissions, stable scope IDs, source/runtime observation methods and unknowns. Do not force setup, `feedback` or Feature review onto an unconfigured diagnosis.

For registered native JSON, use the [verification CLI](scripts/verification_results.py) and [execution contract](references/result-viewer.md): prepare measured bindings, execute selected commands once, then read the resulting bundle. A project-owned unittest or other native adapter remains its own producer/parser. Reuse it and its pending-task selector; do not invent native JSON, shell metadata collectors or a second generic runner. Without compatible binding, report bounded native evidence and the binding gap.

## Read results and choose the next action

Inspect `handoff` first: current request, measured impact, project remainder and unresolved scope are separate. Follow pending criteria to their existing command, guide, raw observation and current validity. Required unexecuted/failed checks and required semantic reviews remain obligations. An undeclared six-cell matrix is an impact map, not six compulsory declarations or executions. It stays UNDECIDED; do not report it as full-stack completion.

The summary omits detail, not evidence. It retains verdicts, counts, criterion IDs and exact detail pointers; large-project previews, semantic review bodies and feedback bindings may be omitted. `observations_omitted` with a positive count points to raw. Capture the exact lookup without `--summary` when needed and read only the relevant JSON fields or raw pointer, rather than printing the whole report. Historical PASS/current STALE is not current success. Task-misbound evidence is not acceptance. Semantic review after execution joins the existing bundle/state without rerunning unchanged commands.

When stdout must be retained, use the package's existing `scripts/run_check.py --cwd <project> --output <new-capture.json> -- <lookup argv>`. It refuses overwrite. Read completed `stdout` JSON; exit zero is not task acceptance. A capture with `execution: running` is unfinished: wait on its owning process/tool and inspect the same path. If the owner stopped, preserve unknown status and reconcile instead of launching another capture.

For non-ASCII text or programs sent to native stdin on Windows, save a UTF-8 file with the editor, then use that capture's `--stdin-file <file>` before `--`. It validates UTF-8 and passes a byte snapshot, recording its hash; it does not use PowerShell's text pipeline encoding. Read back the resulting artifact. This protects that transport only: already replaced `?` characters are valid UTF-8 and cannot be recovered or identified as corruption automatically. Never send secrets through a retained check.

## Improve and explain

For connected feedback work, register feedback before repair and complete the same record with actual cause/owner and mechanism-appropriate evidence. A direct small repair can retain the failure, cause and verification in its existing task report without creating workflow state. Prefer structure, then type/constraint, then an automatic check, then minimal documentation. The [repair contract](references/repair-and-reuse.md) distinguishes fixed-oracle regression from reviewed structural prevention. Neither a rule sentence nor RESOLVED alone proves repair.

For guide work, read the project's prerequisites, user action, expected result, owner paths, existing command, failure diagnosis and cleanup. Code owns values/behavior; guides own intent and use. Execute the guide and fix the responsible owner. Evaluate guide reuse on a different related request, with a fresh context only when discovery is uncertain. Record hints/assistance; an answer patch, token name or CLI sequence supplied to the consumer is not unaided discovery.

Keep one concise plan for nontrivial work. Use Harness contracts only when coordination/risk or the user requires them. No fixed agent count, compulsory Full or repeated inventory. Independent review is useful for material persistence/cross-layer uncertainty; give bounded requirements, target and raw evidence, not the desired patch/verdict.

Report the requested behavior, Feature, what/why checked, observations and evidence, excluded/unverified scope and next action. Separate product/Harness/UI outcomes and fixture/package/product/native-host evidence. Preserve failures, current valid evidence and user state. BLOCKED names a cause and resume condition while independent authorized work continues. Installed resources, global settings, providers and publishing require their own authority.
