---
name: agent-workflow
description: Coordinate a coding task from a natural-language request through relevant project capabilities, actual verification, and results. Use for connecting project verification, verifying or viewing feature results, repairing user feedback, improving the development workflow, or reusing UI standards. Select only the needed procedures; ordinary small edits stay direct.
---

# Agent Workflow

Read the project AGENTS/index, current checkout and dirty baseline, requirement sources, and applicable capability exceptions once. Identify the user's intent, authorized changes, affected Feature and expected outcome. Reuse that investigation and evidence across the selected capabilities. Do not require the user to name Skills or repeat their order.

| Request | Select the necessary work |
| --- | --- |
| Initial project verification | Available `setup-project-verification`; reconcile the complete function map, partition/resume large surveys, then connect actual checks. Map completeness and execution coverage are separate. |
| Implement a feature | Existing development workflow; requirements and touched callers first. If the affected Feature lacks a runnable verification connection, use the setup responsibility for that missing path, then implement, verify and update affected map/guide/active selectors in the same functional commit. Small work needs no contract. |
| Verify a feature | Project verification guide/adapter; select checks from changed behavior, run the real native and affected user flow, inspect raw outcomes. |
| Investigate without changes | Retain request, permissions, full entrypoint denominator or affected scope, observations, unknowns and next action in the existing task. Workflow setup is optional. |
| Show existing results | Read existing plan, capture and raw observations only. Separate original judgment from current reuse. Do not run tests, repair files or start services. |
| Inspect/improve the development workflow | Available `maintain-project-verification` plus `maintain-agent-harness` when actual Harness mapping/cohort/retention is involved. Inspect shared facts once and retain both areas' findings. Audit-only stays read-only; authorized improvements include repair and recheck. |
| Feedback or recurrence | Available `diagnose`; trace expected behavior through callers, state and data to its owner, fix and prevent the concrete failure. |
| Improve UI consistency or standards | Discover project UI guide/token/component paths and use the relevant existing UI capability. Repair shared implementation and affected guidance, then verify actual states and subsequent reuse. |

Load [verification responsibilities](references/project-verification.md) for setup, verification, maintenance or feedback. For feedback/UI work also read [repair and reuse](references/repair-and-reuse.md). If a named capability is unavailable, perform its bounded responsibility using project commands; do not silently treat missing checks as passed or install a new framework.

For configured projects, [workflow obligations](references/workflow-obligations.md) provides the direct audit/resume CLI. Consume its affected references and perform the required semantic work. Local consistency and host-protected acceptance are distinct; the CLI reports the unsupported enforcement boundary explicitly.

For delegated handoff, inspect `handoff` and action scopes before choosing work:
current request, required impact, project remainder and unresolved scope stay
separate. Follow each pending criterion to its existing command/guide/raw and
current validity; repeat exact lookup without `--summary` when details are omitted.
Do not accept task-misbound PASS, turn undecided cells into N/A, or count a current
check as semantic review. Report the current request separately from overall debt.

For guide reuse, discover the target Feature's project guide and registered
UI systems before proposing a new procedure. Read their prerequisites, existing
token/component consumers, command or interaction, expected outcome, raw location
and cleanup. Reuse changed style/verification guidance in a different relevant
follow-up when evaluating the guide itself; record discovery hints and assistance.
Missing project-specific steps belong in the project guide/selector, while a
failed common discovery instruction belongs here. Unapproved UI candidates stay
draft; product screen review debt is not a missing plugin feature.

Without configured workflow, use that same CLI's `start --intent diagnose
--request-summary <request> --investigation <observations.json>`, as defined in
[investigation without setup](references/workflow-obligations.md#investigation-without-workflow-setup).
Starting without `--investigation` is allowed, but retains INCOMPLETE until actual
observations are recorded. Unconfigured diagnosis uses `investigate`, not Feature
`feedback`/`review`; connect project verification first when that capability is
needed. An empty task record does not contain a cause, repair or test result.
With existing work, `investigate --investigation <observations.json>` updates its
record using the exact context. Keep one writer per task, source/permission bounds,
stable screen/viewport/state IDs and directly observed evidence. `lookup`/task
`resume` restore the same unknowns without launching commands or creating setup.
Observe new scope through separately authorized execution; a representative
capture never completes unobserved states. Full inspection keeps the entrypoint
denominator; a small investigation need not initialize the entire project.

Connect the selected request once through the same CLI: `start --intent <intent>
--target <feature> --request-summary <user-outcome> --outcome-ref <existing-requirement-file>`
creates ordinary task state, or `connect --state <exact path>` /
`--work-id <id>` selects existing work. Retain its `task_context` in the invocation's
`AGENT_WORKFLOW_CONTEXT` or pass `--context` when the host does not inherit it.
Then use `prepare`, explicit `execute`, `review`, `feedback`, read-only `lookup` or
read-only task `resume` without rebuilding state/run paths. `execute --resume` is
a separate effect and never replays unknown launches. A new `start` carrying the
old context retains feedback/results for a related follow-up with a new baseline.
Record the ordinary request summary and existing expected-outcome references;
Harness work retains its contract through `--work-id` instead of duplicating it.
A follow-up records its own request; the previous summary is not silently reused.
Do not guess among candidates or imply that a host supplies session identity.
For lookup-only requests, connect/read existing work; never start a new task.

When the project already provides the native unittest adapter described in its guide, reuse its `--work-id <id> --all-checks --output <new-directory>` (or `--pending-state` for an existing non-Harness record) to execute recomputed pending checks; use explicit Feature selection when no task record exists or bind an existing capture with `--evidence` and `--bundle-output`. The workflow audit consumes that bundle directly without rerunning tests. This producer belongs to the project and is not bundled as a universal product adapter. If absent, setup must connect the project's actual runner first. Do not fabricate native JSON observations to make unittest output fit the browser/API viewer.

For registered native JSON checks, the bundled [verification CLI](scripts/verification_results.py) prepares measured bindings with `--prepare`, runs selected checks once with `--execute`, and joins their captures, assessments and raw observations into a reusable bundle. Read its [input and reuse contract](references/result-viewer.md). Reuse the project's reviewed assertion specification and execution connection; if missing, use the setup responsibility to connect them within the authorized scope. In an installed plugin the CLI discovers its bundled capture script automatically. Keep criterion selection and visual judgment with the Agent; let the CLI collect identities, run commands and build the bundle instead of recreating that work in shell snippets.

For lookup-only requests use `--bundle` (optionally `--summary`) or read existing raw evidence. Lookup runs no recorded command. If compatible bindings are missing, report that limit; do not manufacture a successful plan or backfill evidence through execution. A native pass without a bundle remains bounded native evidence, not current reusable workflow acceptance.

For task history, use workflow `lookup --summary --state <exact task path>` (or the
exact context/work ID). Compare a small explicitly named set by repeating this
read-only lookup; never audit all candidate bundles on every prompt. The summary
joins Feature source/map/criteria, the full scope matrix, expected checks, historical
status, current reuse, raw descriptors and next obligations. `current_status:
UNKNOWN` with `current_reuse: STALE` means retained results need revalidation.
`observations_omitted` with a positive `observation_count` means values are in raw,
not unobserved; repeat the same lookup without `--summary` or open raw path/pointer.
Missing/expired bundles remain unavailable. Hook task gaps cover active cells;
project gaps include out-of-task cells. A compact hook retains the selected task
and exact lookup pointer. Without host context it exposes candidates, not a guess.

For a connected task, use `--prepare --root <project> --pending-state .work/task.json`
(`--work-id` for Harness work), with new plan/report paths. The registry's
`extensions.workflow.assertions` supplies reviewed assertions; the CLI selects
pending checks, reuses valid results and explains exclusions. Explicit execution
attaches the resulting bundle to that task independently of semantic review.
Use the subsequent read-only workflow audit for current obligations and its
business/architecture × FE/BE/API/Domain matrix. Record applicability and
architecture flow/boundary/finding evidence in the existing `scope_reviews`;
an empty cell remains UNDECIDED. The input contract specifies those fields.

Consume the result's `coverage` alongside test verdicts. Project Feature `coverage` connects requirements/outcomes to independent business/architecture perspectives and FE/BE/API/Domain responsibilities; cross-layer/E2E describes the method. Fill only applicable links. Record semantic `scope_reviews` through the existing workflow review and include `--workflow-state` during preparation when those reviews are needed in retained results. Report semantic review separately from executed tests and retain missing, excluded and stale scope.

If semantic review follows execution, join the current record with `--bundle ... --workflow-state .work/task.json` during read-only lookup. The original review status remains historical; the current analysis is separately bound. Never rerun unchanged commands merely to attach a later review.

For feedback, register the complaint/expected behavior/reproduction with the existing workflow `feedback` action before repair. Extend that same record with actual flow, cause, failed prevention, owner paths, guardrail and red/green bundles as described in [repair and reuse](references/repair-and-reuse.md). Audit computes unresolved stages and revalidation; consume prior active prevention and retained feedback on subsequent related changes. Diagnosis remains the existing Agent capability, not automatic root-cause analysis.

Keep a single concise plan for nontrivial work. Use the existing Harness contract only when coordination/risk or the user requires it. Never force Full, all playbooks, a fixed agent count or new setup on every request. Current user authorization remains authoritative; global installs, provider changes and publishing are separate effects.

For material persistence or subtle cross-layer changes, use available independent review with bounded context: requirements, base/diff, actual target, raw evidence, permitted fixture/output paths. Do not supply the desired patch/verdict or let the verifier change the product/oracle. Verify its material claims yourself. Return ISSUES with reproduction and owner to the implementer; recheck only evidence invalidated by the resulting diff. BLOCKED retains cause, fallback and resume condition while independent work continues.

Report Feature, criteria, selected/excluded checks, actual observations and remaining gaps. Preserve product, Harness and UI outcomes separately; ISSUES and BLOCKED can coexist. Source changes, generated distribution, temporary installation, product behavior, Agent behavior and real-environment application are different claims. Metadata, a verifier file or submitted PASS does not prove execution.
