---
name: agent-workflow
description: Coordinate a coding task through relevant project capabilities, actual verification, and results. Use for feature additions, bug fixes, behavior-preserving refactoring, work recall/resume, complex design and change impact, connecting verification, viewing results, guardrails that stop a mistake or style/architecture drift from recurring (lint, boundary or regression checks), human corrections, reusing successful decisions or extracting a repeatable procedure from a satisfactory turn or artifact, and reusing UI standards. Select only needed procedures; ordinary small edits stay direct.
---
<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/skills/agent-workflow/SKILL.md -->
<!-- Source-SHA256: 72e47b1a68e87c5c667a75b1cd94993075780b5e3d40a980500c08d558283958 -->


# Agent Workflow

Understand the request and authorized scope. Read the project's AGENTS/index and relevant verification guide, then trace the affected code/callers/tests. Select a procedure below only for a remaining need, execute, and explain the observed result. Read checkout/dirty baseline and applicable capability exceptions once; reuse that investigation across capabilities while its inputs remain current.

| Request | Bounded responsibility |
| --- | --- |
| Initial verification connection | `setup-project-verification`: map the agreed scope and connect existing commands. Whole-map PARTIAL does not block independent scoped work. |
| Add/change behavior | [Feature playbook](playbooks/feature.md): completion and meaningful failure cases. |
| Fix incorrect behavior | [Bug-fix playbook](playbooks/bug-fix.md): feasible reproduction, cause-owner repair and nearby valid use. |
| Preserve behavior while restructuring | [Refactoring playbook](playbooks/refactoring.md): equivalent baseline, callers, errors and side effects. |
| Explain how / why | `zoom-out`: current flow/ownership or recorded design reasons; source, execution, inference and unknowns stay distinct. |
| Remember / continue prior work | `recall`: recover the handoff and reconcile current state first; only an actual resume request proceeds to authorized execution. |
| Design / complex change | `architect` resolves technical ownership and interface choices; [change impact](references/change-impact.md) traces callers, types, state/data and module boundaries. `design-goal` manages work contracts only when needed. |
| Parallel implementation / delegated resume | `swarm`: disjoint ownership, dependencies, existing task/execution handles, evidence and main-agent integration. Independent challenge stays in `multi-agent-review`. |
| Verify | Project guide/adapter and the affected actual user flow. Select from behavior and risk; inspect raw outcomes. |
| Investigate | Existing task can retain read-only observations without workflow setup. Unknown observations stay unknown. |
| Show results | Connect/read existing work; for a person render `lookup --report` (Markdown Feature × business/architecture × FE/API/Domain view). No tests, repairs, services or new task. |
| Maintain | `maintain-project-verification`; also `maintain-agent-harness` only for affected Harness mapping/cohort/retention. |
| Feedback | Existing `diagnose`: actual caller/state/data flow, cause owner, focused repair and appropriate prevention. |
| Keep this approach / make it repeatable | [Feedback and success reuse](references/feedback-and-success.md): classify the signal, improve the existing owner or discovery, and extract only the context needed for the next invocation. |
| UI standards / visual comparison | Discover Feature UI references and registered UI systems, then follow [UI discovery and comparison](references/repair-and-reuse.md#ui-discovery-and-comparison). Select `impeccable` for design, `fixing-accessibility` for interaction/accessibility and `vercel-react-best-practices` only for React/Next.js impact. |

For implementation with shared ownership or contract impact, use [change impact](references/change-impact.md) before choosing the design and affected regressions; keep local edits direct.

For missing task or impact criteria, consult the applicable section of [project verification](references/project-verification.md); setup/maintenance use the same criteria. For feedback/UI use the relevant section of [repair and reuse](references/repair-and-reuse.md). Links are discovery paths, not a recursive reading checklist: reuse already-read criteria instead of reopening Skill bodies and their shared references. Missing optional capabilities use existing project commands; never count missing checks as passed or turn the task into a tooling installation.

For human direction corrections, successful decisions or an explicit request to reuse a turn/artifact, read [feedback and success reuse](references/feedback-and-success.md). A first clear correction is enough; no repeated mistake is required. Praise alone does not request a persistent rule.

## Select only needed mechanics

Small edits use existing project tools directly: no task, setup, contract or copied
stage checklist. For persistent or selected workflow work, use the bundled
[CLI](scripts/project_workflow.py) and [workflow obligations](references/workflow-obligations.md)
for exact task selection, start/connect and explicit execution/resume. Never guess
among active tasks. Completed checkpoints are reused; unknown launches are not replayed.

For existing results and native evidence, follow [result lookup and execution](references/result-viewer.md).
It owns handoff/currentness, omitted detail, preparation/execution, capture and
Windows UTF-8 transport. Lookup runs zero product commands and writes no state.
Start with summary/status and exact evidence pointers; search a large report for
the relevant failed observation before reading its section. Expand when omitted
context affects the decision; retain applicable accessibility, UI and connected-flow criteria.
Historical PASS/current STALE and missing evidence are not current acceptance.
For direct checks captured with `run_check.py`, use its read-only `--lookup` after
the final edit; source currentness and the command's behavior outcome are separate.
Reuse project runners/parsers; missing binding does not justify inventing native JSON.

For connected feedback and guide repair, use [repair and reuse](references/repair-and-reuse.md).
Classify the cause, repair its owner and observe prevention; a small direct repair
can keep evidence in its existing report. A rule or RESOLVED label is not proof.
Execute affected guides and verify reuse when discovery is uncertain; retain hints,
failures, retries, skill non-use and non-execution.

Report requested behavior, affected Feature, selected checks/reasons, actual
observations/raw, current validity and remaining actions. Keep fixture, package,
product, catalog discovery and native-host evidence separate. An unrelated project
gap is not a common blocker. Installed resources, global settings, providers and
publishing require their own authority.
