<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/references/workflow-obligations.md -->
<!-- Source-SHA256: e03d3f4990b2c06d5945ada44aa23affb279af1bd194dbb7601b46ce96c0d5dc -->

# Project workflow obligations

The prompt hook projects existing project/task obligations; it never chooses a
task, creates configuration or runs project checks. Fresh projects without work
retain ordinary Skill discovery and project guides without an automatic prompt
to initialize workflow. Use the existing guides, owners and native runners.
The hook and task handoff keep an investigation INCOMPLETE while requested
observations, inventory or reference bindings are incomplete or stale. A current
complete source-only investigation can be ready without running product checks;
that does not certify runtime behavior or whole-project completion.
An unconfigured diagnosis may start before observations exist; its exact task
context remains readable and INCOMPLETE. Add actual observations with
`investigate`. Feature `feedback`/`review` and connected `prepare`/`execute`
require project verification setup; rejection must occur before record mutation.
An empty task record is not evidence of a recorded cause, repair or test result.

Existing project config owns `extensions.workflow`; a task record under `.work` retains review progress. The bundled `scripts/project_workflow.py` computes obligations from current bytes and registered connections without calling a model. Requirements, feature meanings, causes and visual judgments remain Agent work. Review records are Agent inputs, not authenticated proof.

The CLI accepts `--state` relative to `--root` or as an absolute path inside the
same project's `.work`. It normalizes only this invocation selector before the
existing confinement, alias and private-path checks. Configuration and retained
context paths remain project-relative. For saved lookup output, use the existing
plugin `scripts/run_check.py` with a new capture per call as shown in
`agent-workflow`; full and summary stdout must have separate captures.

Misrouted feedback can retain its original identity while referencing a reviewed
same-task successor. SUPERSEDED is derived only from current link bindings and
an independently RESOLVED/ACCEPTED active-owner successor; stale/invalid links
remain OPEN with `feedback_reconciliation` as the next action. Removed Features
retain separate removal review obligations, including when feedback is pending.
The agent-workflow repair/reuse reference owns the input and revocation rules.

`lookup --summary` (also `resume`/`audit`) reduces presentation after the same
current evidence inspection. It retains exact task identity/request, Feature
source/map/criterion references, complete scope matrix, excluded checks, original
results/current reuse, raw pointers and next obligations. Coverage-row evidence
uses the same omission/count markers as check results; large assertion values
stay in the detailed lookup and original raw. For several tasks, name a small set
of exact states and invoke this lookup once per state. Candidate
discovery reads identity metadata only; it does not validate every bundle. No new
task registry or automatic batch execution is involved. Use the same exact lookup
without `--summary` for observed assertion values and complete retained records.

The prompt hook's `scope.gap_count` and `cell_count` cover `in_task` cells;
`project_gap_count`/`project_cell_count` include the full matrix and
`out_of_task_count` describes the difference. PASS and reasoned NOT_REQUIRED are
not gaps; UNDECIDED, NOT_RUN, STALE and unavailable evidence stay visible. Expanded
scope follows the current audit, including changed shared owners. Bounded context
keeps an explicitly selected task and its detail pointer ahead of other candidates.
Without a host-provided context, candidates are discovery only, not selection or
proof of automatic host delivery. Whole-map/Git changes remain conservatively stale;
complete Feature-local dependency coverage has not been established.

`READY_FOR_REVIEW` describes retained review readiness, not scope completion.
`next_actions` includes task-local applicability/evidence guidance even when
legacy undeclared scope leaves no blocking obligations. Such guidance is
advisory: it preserves current reusable checks and source-only/small work;
reasoned NOT_REQUIRED remains valid and six executions are never inferred.
Explicit declared scope gaps retain their existing blocking obligations.
The hook preserves selected Feature references, current check reuse and an exact
read-only detail pointer when trimming. It shares one source inventory and audits
identical selected/active task state within a single invocation. New invocations
remeasure bytes; different task states still inspect their own evidence. This
does not weaken Git/bundle stale checks or claim a persistent discovery cache.

Task `begin` shares one current source inventory for its initial Feature bases,
prior-state reuse assessment and new baseline. That snapshot lives only for that
call. The CLI's final audit and later requests still observe current files;
execution and lookup do not inherit a persistent source cache. Prior evidence,
feedback and review decisions keep their existing independent validity checks.

One project inspection shares native bundle observations across feedback,
check retirement and result consumers. Standalone feedback inspection also
shares within that call. Full scope and item-only observations have separate
keys; each consumer receives its own copy before applying its contract. The
next inspection remeasures current inputs. Caller-supplied observation pools
must remain local to one inspection; they are not persistent validity records.
One native bundle scope observation also shares item-only linked proof reads
across Features whose checks reuse current evidence. Consumer command checks
remain independent, and the next scope observation reads current raw again.

The hook enumerates candidate paths but reads only the first eight candidate
records in stable selector order. `task_candidate_count` includes discovered
records in a configured project; `task_candidate_omitted` and
`task_discovery_complete` distinguish uninspected records, whose intent and
validity remain unknown. An unconfigured investigation preview also reports
`task_record_count` separately from the inspected diagnosis candidates. Even an
empty diagnosis preview cannot establish absence when records were omitted.
Exact task context is resolved before previews; explicit CLI candidate discovery
still loads all records. `resume --root <project>` without invocation context or a
selector returns the complete candidate paths; select `--state`/`--work-id` for
full details. Later prompts
read current bytes again; no cross-invocation cache is used.

## Investigation without workflow setup

`start --root <project> --intent diagnose --request-summary <request>
--investigation <record.json>` uses the same `.work/tasks/<task-id>/state.json`
and explicit context even when `.harness/project.yaml` or its workflow extension
is absent. It creates no project config, execution plan or second task ledger.
With an existing task, use `investigate --context <context> --investigation
<record.json>`; that task's ID and baseline remain intact. `connect`, `lookup`
and task `resume` read retained records and current hashes with zero launches.
Verification/review/feedback still require configured project connections.

The Agent supplies `scope` (`whole-project` or `targeted`), `inventory_status`
(`partial` or `complete`), `inventory_refs`, `source_refs`, `allowed`, `forbidden`,
`next_actions`, and `entries`. Each entry has a stable `id`, `location`, `access`,
`conditions`, `expected`, `status` (`observed`, `unobserved`, `blocked`,
`not_applicable`), `evidence` (safe project-relative files), and issue `owner`
(`product`, `plugin`, `tool`, `environment`, `agent`, `unknown`). Observed entries
also require `observed` text and direct evidence; blocked/excluded entries need
a reason. Keep observation separate from optional `hypothesis` and user decisions.
For UI, encode actual screen/viewport/state identities; do not generate imaginary
combinations or count one capture as every substate. `location`/`access` may name
a route/command; evidence paths must exist and remain within the project.

An update may add entries and observations but cannot remove IDs, change their
location/access/conditions/expectations or expand recorded permissions. A different
scope/condition is new work. Unchanged observations keep their prior hash binding,
so updating next actions cannot refresh stale evidence. Changed sources/evidence
and unobserved/blocked entries keep the investigation PARTIAL. A complete inventory
needs references; its semantic completeness remains Agent judgment. Full-project
requests retain all discovered entrypoints and unknowns; small requests need only
affected owners and consumers. READY_FOR_REVIEW means the declared investigation
is ready for semantic review, never automatic proof that the product is correct.
The hook gives bounded counts/previews; exact lookup retains every ID and detail.
Each task has one writer; atomic replace does not provide concurrent update safety.

Declare `requested_methods` (`source`, `runtime`, `retained_evidence`) on the same
investigation and `observation_method` on each entry. Method absence is reported as
`unspecified`, never inferred as runtime observation. `unverified` on an entry
accepts stable `{id, method, reason}` items; legacy text items get deterministic IDs.
`total` remains the entry denominator. Derived `unobserved` includes requested
unknown IDs; `out_of_scope` lists unrequested methods as outside scope/not executed.
Thus a source-only survey can be READY_FOR_REVIEW with runtime explicitly outside
scope, while a request including unobserved runtime remains PARTIAL. Legacy missing
request scope keeps unknowns visible conservatively. Exact CLI and the bounded hook
expose request methods, observed method counts, unknowns and outside-scope counts.
Existing unknown IDs cannot disappear without a corresponding observation entry;
that entry still carries normal evidence/status/stale rules. Lookup changes no files
and refreshes no hashes. No additional investigation ledger or setup is involved.
Method-unspecified legacy unknowns remain explicitly unspecified; an explicit
source-only request does not infer they are runtime observations. Related follow-ups
with an explicit prior context retain the investigation's original scope, permissions,
IDs and observation hashes. They do not recapture stale observations at the new task
baseline; unrelated targeted Features do not inherit the survey. A different survey
scope requires a new unlinked task rather than rewriting the retained scope.

## Follow-up review and finding continuity

Ordinary `start` with an explicit prior context and configured-state `begin`/Harness
start share the same inheritance rules. Current map reviews remain reusable;
new-task `scope_reviews` are empty so old applicability decisions cannot exempt
new work. Stale reviews with unresolved product or architecture findings remain
visible without counting as current approval. Architecture findings travel inside
the review, independently of task scope decisions, until an explicit disposition.
Omitting `product_findings` in a replacement review preserves them; an explicit
empty list with the required review analysis records their resolution. Retired
Feature findings also remain visible. Prior task records are never rewritten.

## Connect the current request once

Read `handoff`, `action_scope_counts` and each `next_actions[].scope` before
accepting a delegated task. `request_required` follows explicit targets (or an
init survey); `impact_required` follows changed owners, shared consumers or
verification inputs; `project_remaining` requires an unchanged measured baseline
outside explicit targets. Missing scope/baseline or unresolved ownership remains
`scope_undetermined`. These are derived work labels, never scope exclusions or
permission to remove existing obligations. Impact review can be required while
individual business/architecture and FE/BE/API/Domain applicability is UNDECIDED.

Each action's `pending` connects criterion ID/status, execution check versus Agent
semantic review/scope decision, project-registered command and expectation,
guide/token/component owners, retained bundle/raw and current validity. Missing
commands or assertion contracts remain explicit; lookup does not invent an argv
or expected result. The project owns commands/expectations; the Agent owns the
meaning/applicability decision and must inspect the referenced sources/raw.
`pending_ids`, counts and omission markers in `--summary` retain the denominator;
use `detail_command` without `--summary` for all pending rows and observations.
PASS checks do not discharge Agent reviews. STALE retains historical PASS;
NOT_RUN, BLOCKED and UNDECIDED have different recovery actions. Lookup, task resume
and audit validate plan binding and unknown launches without execution or writes.
Task BLOCKED prevents adopting adjacent Feature PASS as this task's acceptance;
otherwise `handoff.reusable_checks` permits only those current criteria, never a
whole task/product PASS. Project-wide PARTIAL remains visible independently;
when only measured `project_remaining` work remains, the current task can be
READY_FOR_REVIEW without claiming project completion. A changed registered
assertion file pinned by a linked active check reopens that consumer's verification
and impact action; stale retired aliases do not reopen their replacement.

`start --root <project> --intent change --target <feature>` creates ordinary task
state under `.work/tasks/<task-id>/state.json`; no Harness contract is required.
Use `--request-summary <text>` and repeatable `--outcome-ref <existing-project-file>`
to bind the ordinary request to this record. Candidates, lookup and the read-only
prompt hook expose that request; ambiguous candidates are never selected by time.
The hook uses bounded request previews with an omission marker; exact lookup keeps
the complete request and references. Inventory roots must name explicit files or
directories without dot segments; `.` is rejected rather than treated as an empty survey.
References must be safe existing project files. The summary is part of immutable
task identity, not a completion claim. New follow-ups record their own summary.
These options belong only to `start`/`begin`; lookup cannot rewrite them. Harness
work uses its existing `--work-id` contract reference, without a second request ledger.
For existing work, use `connect --root <project> --state <exact .work path>` or
`--work-id <id>`. Both return `task_context`, an invocation selector containing
the project, existing state pointer and immutable task identity. Connect is read-only.

Pass that string through `--context` or the process-scoped `AGENT_WORKFLOW_CONTEXT`
environment variable. It is not a global setting, session ID or separate state
ledger. Within an inherited process environment, subsequent commands need only:

```powershell
Remove-Item Env:AGENT_WORKFLOW_CONTEXT -ErrorAction SilentlyContinue
$startJson = python <skill>/scripts/project_workflow.py start --root <project> --intent change --target <feature> | Out-String
$startExit = $LASTEXITCODE
$start = $startJson | ConvertFrom-Json
if ($startExit -notin @(0, 2) -or $start.status -notin @('PARTIAL', 'READY_FOR_REVIEW') -or -not $start.task_context) {
  throw "start did not return a valid task context (exit=$startExit, status=$($start.status))"
}
$env:AGENT_WORKFLOW_CONTEXT = $start.task_context
python <skill>/scripts/project_workflow.py prepare
python <skill>/scripts/project_workflow.py execute
python <skill>/scripts/project_workflow.py lookup
python <skill>/scripts/project_workflow.py resume
```

`start` may exit 2 while returning a valid `PARTIAL` task context; this means work
remains and is safe to continue only after the status/context guard above. A
`prepare` or `execute` exit 2 reports a verification outcome such as BLOCKED,
NOT_RUN or failed assertions; inspect its JSON and do not treat it as the start
status.

Preparation selects pending registered native-JSON assertions without launching
commands and retains only the plan pointer in that same task state. Execution
uses the existing viewer/capture/checkpoints and attaches results to that task.
Standalone Skills may need `--run-check <project capture tool>`; the plugin and
this source repository discover their existing capture tool. `execute --resume`
continues never-started checks, refuses unknown launches and does no work for a
completed run. `lookup` and task `resume` read decisions, reviews, feedback, linked
results, current gaps and any completed checkpoint; they never execute or repair.
Verification exit codes report the check operation; task status still reports
unfinished semantic work independently.

A later `start` with an explicitly retained context creates a fresh baseline and
carries result/feedback/prevention links from that task. It does not reuse its
task-specific scope decisions as new semantic judgments. Without context,
`resume`/`lookup` return candidates and require an exact selector, even with one
candidate. Standard task records, configured state and active Harness work are
discoverable; custom `.work` paths require explicit `--state`. No timestamp picks
a task. Conflicting selectors, another project, or replaced task identity block
the operation. If a host does not inherit the environment, the Agent must retain
and pass the context explicitly; transparent conversation binding is unverified.
The prompt hook reads this same explicit context when available and remains
read-only. Natural-language intent and procedure selection belong to the Agent.

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

Audit also returns `execution_selection`: selected Feature/check pairs, reasons
for selection/reuse/exclusion, and required Features with missing connections.
The native JSON CLI and repository unittest adapter use the same deterministic
selector. Task identity/baseline is bound before execution and checked again
before storing result pointers. `results` holds existing bundle paths in the same
task state; it does not add a parallel result ledger or make a semantic review.
Read-only audit reassesses these results even when Agent review is unfinished.
Subsequent configured-state begin/start retains result links, feedback and active
prevention. Maintenance consumes these linked runs without another history list.

The [result contract](result-viewer.md#task-scope-and-required-execution) defines
task applicability decisions in existing `scope_reviews` and the derived scope
matrix. An applicable but unreviewed architecture boundary remains an obligation
alongside passing tests. Architecture findings retain owner/code repair or a
reasoned exclusion; structural validation does not certify semantic sufficiency.
The prompt context exposes bounded scope gaps from this audit for later work.

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

`mapping_status` reports map readiness separately from the overall task `status`.
Missing owners/references/commands, stale or incomplete semantic reviews and
unreconciled retirements keep mapping PARTIAL. A complete map may explicitly
describe unverified product quality or incomplete data: record these as optional
`product_findings` (nonempty strings) in the review. They remain visible in audit,
including on stale reviews, and keep overall task completion PARTIAL; they do not
require product repair merely to establish mapping readiness. Existing `findings`
still block mapping and are never automatically reclassified. The Agent must
justify any reclassification against the actual requirements and mapped sources.
Native verification failures or missing execution remain task obligations even
when `mapping_status` is READY_FOR_REVIEW. Neither readiness field is product PASS.
Retirement does not hide product findings: prior findings remain visible until a
current removal review explicitly reconciles `product_findings`. Omitting that
field preserves earlier findings; an explicit empty list records semantic
resolution, not execution proof. A stale removal review reopens reconciliation
and retains both earlier and retirement findings. Current removal reviews may
complete mapping while product resolution still blocks the task.

New records retain each Feature's initial source patterns as well as file hashes,
so narrowing a source map after deletion does not erase its original consumer.
For older records without those patterns, deletion still matches current owners.
An unmatched deleted path reports `baseline_source_ownership_unavailable` rather
than silently accepting the work. Recover its original Feature connections from
the retained baseline before reconciling that legacy record; do not replace the
baseline with current files to clear the finding.

For a source inventory that also contains purely descriptive documents, a Feature
may declare exact project-relative paths and reasons, for example
`"documentation_only":{"docs/feature-map.md":"Descriptive index; no runtime or generator consumes it."}`.
This is project-owned impact policy, not an inference from `.md` or a free-text
waiver submitted after implementation. Review consumers before declaring a file;
executable specifications, generated-code inputs, configuration and Agent
instructions that alter execution must not be classified as descriptive prose.
Wildcards and missing reasons are rejected. Start snapshots the declarations.
Only an existing file declared both at start and now avoids automatic product
execution; it still invalidates semantic review. New/deleted paths, other changed
sources, feedback and UI requests retain their execution obligations. A later
declaration cannot excuse an already changed path; legacy states without the
snapshot remain conservative. Audit exposes both `changed` and
`verification_changed` so selection is inspectable. Existing document/link checks
remain available. This local policy is not protected against an actor rewriting
the project and manifest with equal authority.

Start also snapshots each Feature's verification inputs separately from its map:
criteria and UI reference hashes plus registered check definitions. Changing these
inputs requires current execution even when source files are unchanged. A fresh
semantic review alone cannot discharge that obligation. Map-only descriptive
edits retain their review-only path. Audit exposes `verification_inputs_changed`
alongside source impact. Older records lacking this baseline conservatively
require verification when their original complete Feature basis changes; preserve
that original baseline rather than restarting work to erase pending obligations.

Begin/review writes use a unique task-local temporary file followed by replacement. Harness review attempts stage under `.work` outside the strictly validated active-work artifact directory, so an orphan cannot prevent Harness resume. Abrupt process exit leaves the previous valid state intact (or no initial state), and a fresh invocation can resume without deleting an orphan attempt. One writer owns a task record; concurrent writes to the same record are not supported. Interrupted attempt files remain subject to the existing `.work` retention policy.

Inspection validates review analysis, findings and existing references as well as
the current basis. Writing a minimal success-shaped record directly cannot omit
those fields. This checks record completeness, not whether its semantic analysis
is correct; editable manifests, policy and reviews are not authenticated evidence.

A changed-behavior review can reference a task-local `bundle` JSON produced by the result viewer's explicit execution path. Audit reopens its plan/captures/raw/current inputs through read-only bundle inspection, then checks Feature/check IDs and exact registered argv/cwd. Missing, stale or mismatched evidence cannot discharge the obligation. Feedback also needs an observed repair relative to the original basis; a new analysis or PASS flag alone is insufficient. Map/UI meaning and whether a regression covers the reported cause remain review responsibilities, distinct from those mechanical checks.

For a tool owner missing from the immutable task baseline, a bound root-local failing capture can supply a separate repair preimage. Its selected failed assertion, declared owner and dependency hashes must match. Untracked files use the captured per-file hash; already tracked files require an unchanged clean capture and an exact blob hash at the captured Git revision (LF or its Windows CRLF checkout). Dirty tracked captures and unavailable/mismatched Git objects remain OPEN. Existing baseline entries always take precedence; no baseline is backfilled.

`accept` returns BLOCKED because no protected verifier identity/policy/results boundary exists on this host. An Agent with equal filesystem authority can modify config/records or skip commands; the local close guard cannot prevent that bypass. A hash, fresh context or submitted PASS is not enforcement. Draft/test/map edits remain allowed; no global hook or general installation is performed.
# Native unittest evidence

Projects using the existing unittest adapter can bind captures with
`verify_product.py --feature <id> --check <id> --output <new-capture> --bundle-output <new-bundle>`.
For every check registered to one Feature, use `--all-checks --output <new-directory>`;
the resulting `bundle.json` binds each selected check to its actual native run.
For multiple selected Features use
`--features <id> <id> --all-checks --output <new-directory>`. The adapter resolves
all selections before execution and shares only equal registered check IDs,
effective argv and cwd within that batch. Distinct check IDs remain separate
even with identical commands. Captures record their preselected consumers;
each Feature receives its own bundle referencing the same shared run. A bundle
cannot relabel that capture as an unselected consumer. The final source identity,
native exit and counts are reassessed for every consumer. Coverage is the
project's declared check-to-Feature mapping, not inferred from matching command
text. Different raw-JSON criteria/fixtures and cross-batch caching are not merged.
Attach that project-relative bundle path to the semantic review's `bundle` field.
The same project adapter can select pending execution directly with
`--work-id <id> --all-checks --output <new-directory>`, or
`--pending-state .work/<record>.json --all-checks --output <new-directory>`.
It calls the sibling workflow CLI to recompute actual obligations and current
evidence, then executes only Features whose `verification_status` is REQUIRED.
Workflow and Feature Map check lists must agree before commands launch. Missing,
empty, wrong-target or old unsupported records cannot produce a no-op success.
Current native evidence is reused even if a separate product finding remains;
no pending execution returns NOT_REQUIRED with zero commands and no output
directory, never product PASS. `workflow_status` and remaining obligations are
the selection-time snapshot; semantic review and binding the returned bundle
remain explicit work. Automatic selection does not invent missing project runners
or make unsupported browser/API/DB checks into unittest commands.
Workflow audit uses the same native unittest assessor to reread stdout, exit,
counts, skips, exact target and current Git identity. It never runs the suite or
loads project code during lookup, and ignores submitted bundle verdict fields.
The native-JSON path remains available for browser/API/DB observations.
Unittest captures establish only their assertions; ignored inputs, dependencies,
live runtime identity and protected acceptance require separate evidence.
# Feedback state and follow-up consumption

Read-only `lookup` and task `resume` retain task, feedback, criteria and remaining
work when a prepared plan is missing or bound to a different state path. The
verification section reports BLOCKED and its cause, including in `--summary`;
`execution_plan_reconciliation` requires inspecting the existing effects before
any explicit prepare/execute. Copying a task for evaluation does not authorize
executing its original plan. Neither query rewrites the plan/state nor retries a
command; execute keeps the exact task/path binding requirement.

Read-only `maintain` adds measured `maintenance` for explicitly linked bundles.
Removing baseline checks from an active Feature retains `check_retirements` and
`check_preservation` until a current reasoned review connects preserved defect and
normal evidence. Details live in [verification responsibilities](project-verification.md).
An explicitly reviewed `check_identity_migrated` rebind is narrower: the old plan
must bind to the same task and a clean Git preimage, and a newly captured native
bundle must be current and reusable. The registered command, required result,
assertions, criteria, runtime, dependencies and fixture inputs remain equivalent;
only that Feature's check ID and its explicit report-output path can change. The
full project and assertion registries must match that exact transformation, and
the map edit changes only the leading command-ID token while preserving labels
and notes. Missing original Git bytes, stale proof, collisions or any unrelated
consumer/prevention change keep the retirement BLOCKED. This is not a generic
check-removal path. A shared old command remains registered for its other
Features; rebinding one consumer does not retire those uses.

The existing work JSON now retains `feedback` by incident ID. `feedback --feedback
<entry.json>` merges an explicit complaint/repair stage; audit returns each chain's
computed OPEN/RESOLVED and `remaining`, not a submitted done flag. The feedback
playbook selected by agent-workflow supplies fields and native evidence bindings.
Configured-state begin/Harness start retain it in the next work record and the
prompt hook exposes pending causes/guardrails. No automatic conversation collection
or universal host request registration is implied.

A project inspection observes each shared native bundle once, then copies that
observation for each Feature before applying its registered command and criteria.
This invocation-local reuse preserves independent consumer judgments. Later
lookup/resume calls remeasure raw, source, runtime and whole-Git identity; no
observation survives across requests and no product command runs during lookup.

Portable plugin consumers read `<plugin-root>/build-origin.json` for build source
identity and `package-files.json` for copied content. Do not substitute an enclosing
repository Git HEAD. Old packages without a build origin require a retained build
receipt; otherwise source commit is UNKNOWN. Build metadata is not native host
acceptance or semantic/task success.
