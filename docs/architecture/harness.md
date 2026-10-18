# Harness Architecture

Human corrections and successful procedure extraction use the existing
`agent-workflow` / `diagnose` entrypoints and canonical
[feedback/success reference](../../authoring/references/feedback-and-success.md).
The resource map bundles that reference, its template and the existing repair
contract within each consuming Skill. Classification and extraction are Agent
judgments; existing feedback/prevention owns persisted repair evidence. There is
no new runtime, learning store, authoring framework or mandatory task lifecycle.
The existing strict cohort resource allowlist includes the three new Diagnose
resources; unknown resources are still rejected. No install authority is expanded.

Workflow persistence is selected for existing connected work or useful durable
evidence, not required for every small edit or one-off diagnosis. Direct work
retains actual verification in its existing report; it cannot discard open
connected obligations. Audit-only missing-guide findings do not authorize writes.
See [stage 0 compatibility](../research/stage0-compatibility-results.md).

Read-only task CLI calls reuse the measured Feature bases in nested
verification-scope projection; standalone viewer calls still inspect them.
The snapshot is invocation-local and each later call measures source, references
and raw again. Full results retain existing facts and decisions; lookup is not
a filesystem transaction. Environment feedback can resolve availability from a
current registered same-target native recheck while retaining failure and attempt
history. Manual disables remain authoritative. Capability captures separate the
declared target from host context; project probes own actual backend/container
identity and diagnosis.

The shared project-workflow owner derives request/impact/project/undetermined
work labels from existing task targets, measured source/reference bases and owner
links. It joins pending criteria to project commands/assertions and UI guides,
without another ledger. Existing obligations and undecided scope are preserved.
CLI lookup/resume/audit validate the same saved plan/effect binding; summaries and
the prompt hook project these facts. Individual current checks remain separate
from Agent review and task acceptance; a blocked task binding governs handoff.

Workflow 0.1.46 keeps decision revisions, investigation scope and retirement proof
in the existing task state. `project_workflow.py` owns those derived statuses;
`workflow_context.py` supplies bounded read-only projections; the result viewer
continues to own execution evidence rather than an investigation ledger. Exception
approvals bind subjects and consumed guide revisions, rule-only retirement binds
prior prevention owners, and related tasks retain investigation hashes without
recapturing observations. Local consistency does not authenticate review authors
or prove semantic sufficiency. Whole-Git execution staleness remains unchanged.

Project workflow Features can declare `coverage` without changing their partition.
Business/architecture perspectives and FE/BE/API/Domain responsibilities are
independent axes; cross-layer/E2E is a method. The existing workflow owner validates
links and scope-review records; result preparation snapshots that declaration and
the existing viewer joins it to actual native evidence. Semantic reviews retain
analysis/references and current-input validity separately from test verdicts.
See [the result contract](../../authoring/references/result-viewer.md).

Shared UI systems live in that same project extension: guide/token/component
references and consumer Feature IDs feed current bases, changed-work obligations
and prepared input hashes. Values remain code-owned; exceptions and design
sufficiency remain review inputs, not automated visual verdicts.

Feedback chains and check-retirement obligations stay in the existing work state.
Their direct raw-evidence joins reuse the result viewer. Read-only maintenance
collects only explicitly linked runs and measured cost/errors; semantic overlap
and unique-detector judgments belong to the Agent. There is no second ledger or
test-pruning engine.

## Control plane

`.harness/project.yaml` is JSON-compatible YAML. Its internal schema version is retained for machine compatibility. The file owns mapped roots, command descriptors, source-to-test candidates, Full warning triggers, document boundaries, retention, Git policy, and baseline debt. Unknown normative fields are rejected; provider extensions belong under `extensions`.

Older project files may contain redundant cohort and component-version declarations. The runtime recognizes only the exact known legacy shapes, normalizes them in memory without overwriting the file, and emits a digest-bound transaction for an approved migration. Unknown or mixed declarations fail closed.

## Work contract and authorization

`contract.json` is the canonical, language-independent Item contract. Every Item has stable identity, a concrete changed outcome, ordered behavior steps, observable verification, and stable Done criteria. Contracts contain the Items needed for meaningful review boundaries, with no fixed upper count. `design-create` accepts omitted descriptive `terms`, `depends_on`, and `non_goals` as empty lists and omitted `priority` as `core`; it expands only its input copy before validation. Decision state and material risk declarations remain explicit, including resolved/empty values. Saved contracts and `authorize` remain strict; no existing authorization payload is silently normalized.

Ordinary contracts are default-authorized from their canonical payload. Structured material risks describe actual effects, such as changing access controls or exposing private data, rather than any task mentioning security. User instructions establish permission; the runtime records it and checks consistency. A low-risk amendment changes descriptive title/outcome/steps/terms and preserves valid existing explicit authorization. Structural/material Item revisions use `amend --intent explicit_approve` with matching user permission; the flag records that permission, not a requirement to ask again. Veto and stable Item identity remain protected. Invalid or drifted authorization cannot be reused.

Use `amend --root <repo>` to persist a revision: the runtime checks the saved contract, updates it and the active manifest digest in one recoverable transaction, and preserves the original Git/dirty baseline. Designed but unstarted work retains its design-only state. Without `--root`, `amend` only returns a transformed contract for compatibility. `result.json` owns submitted evidence; validators do not execute or authenticate checks. Reassess evidence affected by the revision while reusing unaffected outcomes. Empty planned tests are allowed when observable Done evidence already establishes the outcome. The final chat response is the human-facing Design or Result summary.

## Runtime and state

Static inventory confines nested Git candidate probes to descendants of the
requested root. A worktree inside another Git repository does not include its
outer repository as a nested repository; real descendants remain discoverable.

Result evaluation rejects non-object `full` and Item `delta` values as incomplete evidence. Close leaves the work active without writing result artifacts when this validation fails.

The runtime selects dependency-ready core Items before optional Items and records only Git-reported staged/unstaged/deleted/non-ignored untracked baseline entries. Impact decisions record changed logic, affected behaviors, scope, and reason. Path rules yield candidates; local/capability scope selects exact tests, cross-cutting scope or an explicit request requires Full, and unknown scope blocks as `unresolved_logic_impact`. Close recomputes cumulative paths from the captured source commit. Independent Item worktrees use deterministic paths under the repository-owned, ignored `/.worktree/` directory; callers cannot place them outside the project. A commit contains the smallest complete functional unit that works from that commit alone; coupled Items sharing runtime, schema, documentation, or generated resources stay together. Planned test and Done IDs must match retained evidence one-to-one. A host Goal may track continuation but is not execution authority. Low-risk user changes become `approved_amendment`; material or high-risk deltas need focused approval. Legacy active work that already contains `review/design.html` remains valid only when the retained bytes match its stored digest; the runtime neither converts nor deletes it.

```text
.work/goals/active/<id>
  -> completed/YYYY-MM/<id>
  -> trash/YYYY-MM-DD/<id>
  -> deleted (exact-target approval only)
```

Manifest dates, not filesystem timestamps, drive retention. Transaction journals make broad setup and migration changes recoverable. `legacy-unclassified` is outside automatic retention.

## Environment exceptions

Configured `extensions.workflow` connects the existing project Feature Map, source patterns, criteria and command IDs to [project obligations](../../authoring/references/workflow-obligations.md). Normal Harness start captures its baseline in `work.json` and returns a compact reference; `project_workflow.py --work-id` reads that baseline and retains reviews in `workflow.json`. Resume preserves the baseline. Source/criteria/command changes reopen consumers; missing links and evidence remain PARTIAL. Current configured semantic reviews can be reused without repeating the whole survey. Harness maintain audits configured obligations and close directly checks its per-work state before lifecycle completion, even without an optional workflow begin. Older work retains configured-state checks. This remains editable local consistency: `READY_FOR_REVIEW` is not protected acceptance, and the explicit accept operation reports BLOCKED without a host-owned verifier boundary.

The cohort installer preserves replaced trees at its returned `preserved_previous` path, including user customizations. An already matching installation returns `reused: true` without rewriting it. Failed restoration retains both staging and backup recovery paths instead of deleting remaining previous bytes. This is recoverability for observed exceptions; process-crash recovery and hostile-process isolation require separate host evidence.

`.harness/environment-exceptions.json` is an ignored, repository-local machine exception document. If absent, the runtime does nothing. If present, schema version 1 requires each unique entry to contain non-empty `capability`, `status`, `reason`, `fallback`, `disable`, and `retry`; supported failure statuses are `verification_unavailable` and `execution_blocked`. A `skip_until_manual_reenable` entry prevents another invocation and selects the fallback. The resulting evidence carries the unavailable capability name, intent, reason, fallback, disable method, and remaining unverified scope for `result.json` and final chat. Environment failures never become approval blocks.

## Distribution

Task-native preparation and repository unittest execution share the existing
workflow obligation selector. The task's immutable identity/baseline is separate
from mutable review/feedback/result/investigation links; the same record owns the latter.
Without configured workflow, a diagnosis task uses that same identity/context and
record, creating no project config or execution workflow. Observations retain stable
entrypoint/state IDs and source/evidence hashes. Exact-context lookup/resume and the
bounded prompt hook remain read-only; an unknown or stale observation keeps scope
partial. Semantic inventory/cause/retirement judgments remain Agent responsibilities.
Reason-specific feedback and requirement retirement consume existing native bundles
and review hashes rather than adding another result store. Task records use `TaskStore`: a loaded `TaskState` binds the path and original byte
hash without adding persisted fields. Commit holds an OS file lock, compares the
revision and atomically replaces the JSON. Busy/stale writes fail explicitly;
callers reread and reapply semantic changes, never replay an effect automatically.
The lock file stays in place to avoid inode races; the OS releases ownership after
process exit. Read-only lookup creates no lock and preserves evidence bytes.
Plain dictionaries can create new records but cannot overwrite existing state.
Workflow/viewer now call public module functions; the runtime API static check
rejects old dict/private calls, missing names and wrong call arguments.
Execution may attach verified captures while semantic review is unfinished.
The result viewer projects declared task applicability and per-scope freshness
without executing commands; architecture structure is validated while meaning
remains Agent judgment. See the [task result contract](../../authoring/references/result-viewer.md#task-scope-and-required-execution).

`agent-workflow` selects task procedures; `setup-project-verification` connects the first product flow; `maintain-project-verification` repairs product-map, command and UI drift. Their shared references are generated from one canonical source into each self-contained Skill. Existing Harness runtime retains mapping/cohort/retention ownership, while projects own requirements, runner adapters and UI implementation. Combining these capabilities does not turn a Harness integrity PASS into a product PASS or require a contract for ordinary development.

The shared [task verification criteria](../../authoring/references/project-verification.md#task-verification) own feature completion/failure observations, bug reproduction/owner repair/regression and refactoring contract preservation. Entry skills route to that source; business/architecture impact selects checks and semantic review. Changed layer connections require normal and failure paths through input, API, Domain, storage and fresh read. This selection adds no runtime mode, state schema or runner.

The existing Impeccable entrypoint also loads the canonical repair/reuse reference when the request includes shared UI standards or subsequent-screen reuse. This bounded reverse route matters when a natural UI request selects the UI capability first: the shared implementation, existing guide and active Feature command must travel together. Ordinary visual refinement does not trigger project setup or unrelated maintenance.

`authoring/` is canonical. `scripts/sync-skill-resources.ps1` generates self-contained public resources and the manifest. Each installed Skill exposes only its owned commands. When a known command is invoked through the wrong Skill, that entrypoint reports the requested command, owning sibling Skill, and exact sibling script path; there is no shared launcher. The installed cohort is accepted only when its complete observed tree exactly matches the required manifest resource set and hashes; Skill prose is not a compatibility signal. The bundled manifest must retain valid metadata and the same Harness resource entries, but unrelated Skill additions, removals, or hash changes do not invalidate the cohort. Full distribution validation still covers all public resources. Installation stages and verifies the whole cohort before atomically replacing its owned Skill roots.

Harness maintenance requires a supported project configuration. If normalization fails, it reports the configuration finding and marks document, impact and baseline checks `not_checked`; it does not substitute empty defaults and invent drift. Independent environment, instruction, lifecycle, transaction, Git and requested installed-cohort audits continue. A standalone `extensions.workflow` project uses the project-workflow audit; its presence does not require full Harness installation.

Ordinary and Harness task starts now share map-review continuity: basis-current
reviews are reusable, task scope decisions reset, and unresolved product and
architecture findings remain independent of approval freshness. Architecture
carry is read-only input to the next review; resolution uses validated current
scope evidence. Reintroducing a retired Feature supersedes its old retirement
review, while a retirement retains the active finding baseline for stale checks.

## Request scope and mechanism-appropriate prevention

The current workflow keeps undeclared matrix cells visible as UNDECIDED without adding six mandatory scope actions. Registered criteria and explicit cell decisions still require evidence; new/changed unmapped sources still require ownership. Unchanged project debt is separate from current request readiness. The prompt context prioritizes selected Feature UI references and consumer-linked UI systems before unrelated project entries.

Structural/type-constraint prevention uses the existing feedback/Feature prevention link and existing foreground captures. A semantic review explains original failure, bypass resistance and nearby normal behavior; the runtime pins its subject, owner/criteria/config and evidence bytes, and validates current source/capture identity. Staging or committing identical bytes preserves reuse; observed content drift still reopens prevention. It does not parse arbitrary native output or infer correctness from exit zero. Automatic regression prevention retains fixed-oracle RED/GREEN joins. Both reopen on changed evidence/ownership; neither is protected-host attestation. See the [repair/reuse contract](../../authoring/references/repair-and-reuse.md).

Task start snapshots only dirty, nonignored paths outside inventory roots; local lookup compares those paths and newly changed Git paths with that baseline. Preexisting unchanged dirty files do not block a bounded request. Known reference documents retain their existing Feature bindings. Private/aliased paths are reported without reading contents; ignored files require explicit project evidence. Host-injected inventory remains authoritative and never triggers this local Git adapter.

`architect` owns technical design decisions and `design-goal` owns work contracts.
The canonical [change-impact procedure](../../authoring/references/change-impact.md)
is generated into architect, workflow/verification and review Skills. It connects
callers, types, state/data ownership and module boundaries to actual regressions;
small changes stay direct. No runtime mode, state store or schema is added.
