# Testing And Impact Selection

Runtime 0.1.66 changes only the handoff explanation: task binding/effect
blockers are described only when actually observed, with their retained reasons.
Selection, execution, acceptance states and private-path protection are unchanged.
Focused RED/GREEN and the workflow/refinement/hook selectors cover PASS, NOT_RUN,
ISSUES, actual task-plan mismatch and project-only remainder; no new Full run is
required for this output-only change. Package consumption is a separate claim,
and documentation/output changes do not establish an Agent performance gain.

Runtime 0.1.65 retains investigation handoff correctness,
including unconfigured start/lookup before observations and no-task audit.
Focused failures reproduce an empty hook in an unconfigured Git checkout and a
ready handoff with a pending observation. Normal complete source inspection stays
ready without setup/tests; stale references reopen it. Hook and lookup checks
preserve source/evidence bytes and execute zero product commands. These changes
affect shared discovery and acceptance, so this unit selects Full after focused
checks, plus resource/distribution checks. Fresh-project package consumption and
Agent effectiveness are separate from these repository regressions.

Runtime 0.1.62 tests task-first bounded summaries, all omitted IDs, same-call
Feature-basis reuse and alternate-project isolation, structured same-target
environment recovery, manual disable/context/config drift, and Windows cleanup
stdout/stderr with the original timeout intact. Source/guide/assertion/raw changes
must still invalidate reuse on the next call. This changes shared workflow/viewer
and capability collection logic; Full is selected once after focused failures,
plus required resource, distribution and documentation checks. A prior 300-second
impact-run timeout is incomplete evidence, not a failed product assertion.

`python scripts/evaluate_benchmark.py --manifest <run.json> --output <new-result.json>`
is the separate official-evaluator connection. The manifest owns exact argv/cwd,
task/data/evaluator revisions, image digest, report path/verdict JSON pointer,
patch/trace/package paths with SHA-256, plugin condition/version/source, model/CLI,
budget/permissions and explicit cost/usage (`null` when uncollected). It calls
`run_check.py`, retains its native JSON report and raw external verdict, and
reports capture completeness separately. Exit zero never implies a solved task.
Existing reports/results are rejected to prevent accidental cached trials.
OFF uses `plugin.condition: "A"` with null version/source/package; supplying
an ON package identity for A is rejected. ON conditions retain the package hash
requirement. OFF capture still pins the task patch, trace and evaluator inputs.
Pins are supplied metadata and measured artifact identities; the connector does not
attest upstream checkouts, enforce model budgets, authenticate an evaluator, or
isolate hidden tests. Those belong to the evaluation environment. The
`benchmark-evaluation` selector exercises synthetic transport only; it never uses
the repository unittest assessor to grade another evaluator. Official gold,
no-patch and defect controls must run before model trials with solution/tests
outside Agent-readable mounts. If prerequisites or costs are not authorized,
keep the official trials unperformed with their original planned denominators.

`python scripts/run_benchmark_agent.py --manifest <agent.json> --output <new-result.json>`
starts a dedicated app-server and a fresh thread for each phase. The manifest format
is `codex-benchmark-agent-v1`: `task_id`, condition `A`/`B`/`C`, local `cwd`, optional
container `server_cwd`, `server_argv`, `model: gpt-6-luna`,
`reasoning_effort: medium`, positive `timeout_seconds`, and nonempty `phases`
containing unique IDs and prompts. `environment` configures only the launched
server; never put credentials in a manifest or argv. A phase may declare a
candidate-relative `interrupt_when_file`: after the actual effect marker appears,
the controller requests native interruption before starting the next fresh thread.
The marker is evidence to inspect; it does not prove effect correctness.

The runner checks the server-selected model/effort before sending the task,
preserves discovery, hook/tool notifications and failures in a new JSONL trace,
and sums each thread's final cumulative usage once. Missing usage, credits and
USD stay unknown. Reasoning output is a subset of output, never added twice.
`run_check.py` enforces one local process-tree wall budget across all phases;
the controller's capture directory stays outside candidate mounts. Remote
execution requires `snapshot_argv`, a controller-owned transport/helper running
`run_benchmark_agent.py --snapshot <candidate-cwd>` inside that same sandbox.
Candidate Git configuration must never execute in the host controller. The helper
captures the initial commit and final binary patch, including untracked files,
without changing the candidate index. Tokens have no enforced cap.
A Docker exec transport requires an external
container lifetime limit because killing its local client cannot attest remote
cleanup. Keep this controller, result files and evaluator outside candidate
mounts. The runner captures tracked and untracked Git changes against the initial
HEAD using a temporary index, preserving the candidate's index and source state.
Its trace and patch hashes can feed the existing evaluator manifest directly.

This repository-only runner is common to all conditions; it is not added to one
plugin condition. The fixed plugin runtime remains 0.1.62 unless its distributed
behavior changes. The current impact is benchmark execution/capture plus docs and
selector routing, so scoped runner/evaluator/capture and documentation/cutover
checks apply. The current [execution record](research/luna-benchmark-execution.md)
contains 24 actually validated official control cells, nine pilot and 108 main
attempts, with original setup/model/scoring errors and explicit unknowns retained.
The 18 secondary UI continuations reuse first-phase artifacts and preserve both
failed snapshot checks and their consumed time; they do not overwrite primary
results. Official tests determine functional correctness, without reference-patch
or implementation-path equality. Synthetic fixture runtime, handoff, duplicate
effects, guide/reuse acceptance and completion claims have distinct scopes.
The 143 actual native threads and safe broker metadata verify Luna/medium consumption;
one pre-model setup failure has no selected-model evidence. Usage scopes include
parents/helpers/preparation/retries, with missing monetary cost null. Documentation
reconciliation changes no frozen runtime, grader, package or task inputs, so its
checks are repository-docs, core-first-cutover and diff formatting; it does not
repeat the already valid 447-test runtime or 43-test runner units.

Delegated-handoff regressions distinguish explicit request, measured shared/input
impact, unchanged project remainder and missing-baseline scope. They preserve
obligations and UNDECIDED applicability, connect pending checks/Agent reviews to
registered expectations, guides and raw, and reject invented missing commands.
Audit shares lookup/resume plan/effect validation. The native completed-run case
now checks audit too, preserving state/raw and single execution of the effect.
Hook tests preserve task action scopes and project counts under bounded output.
Features: workflow-obligations, verification-results and agent-workflow. This
changes common workflow projections and audit dispatch. Registered assertion-file
drift also promotes linked active consumers into required verification using the
existing bundle's pinned file hash, without changing execution/replay policy or
Harness schema. The latter affects prepare/selection and downstream consumers;
this delivery selects Full once after focused/impact failures are repaired, plus
required resource, distribution and documentation checks.

The check-identity migration cases use a clean Git-backed original plan and a fresh
native replacement execution. They require unchanged assertions, criteria, fixtures,
command behavior and other consumers; malformed, stale and colliding proof is rejected.
This preserves an identity-only move and does not weaken removal/consolidation evidence.

The checkpoint lookup regression executes the first of two native commands, interrupts
its controller, and retains an unresolved second launch marker. Lookup/resume must
preserve the first current PASS while exposing the unknown effect as BLOCKED; they
execute zero commands and preserve state/raw. Malformed completion indices and marker
names remain unknown, while ordinary completed-run markers do not prevent reuse.
The execution replay refusal is unchanged and checked alongside the lookup repair.

The current consumption regression in `test_project_workflow` preserves task and
feedback visibility for unavailable/misbound/malformed prepared plans in lookup/resume,
including summary output. Both return BLOCKED with a reconciliation action while
state/raw remain unchanged and execute still refuses the plan. The focused normal
connected execution/resume case checks that valid plans retain their behavior.
The viewer/execution regression checks invocation-local Git observation reuse,
different command/capture cwd keys, and later raw/tracked/untracked source changes.
A final source recheck rejects tracked or untracked edits made during lookup.
Standalone current-context input cannot replace live Git measurement. These bounded
changes select workflow/refinement/hook/viewer/execution and distribution checks;
they do not change execution policy, Harness baseline, schema or test discovery.

Version 0.1.58 adds focused feedback supersession cases in the workflow refinement
selector: original identity preservation, removed-owner reconciliation, independent
successor validity, input order, stale/revoked links, malformed records and zero-run
lookup. The existing native RED/GREEN/normal execution case also consumes a linked
successor in a later task and reopens both records after source drift. Fixtures for
intentional differences are synthetic approvals; these tests are not real UI review.
The change affects feedback completion/obligation consumers and distributed CLI
state handling, so this delivery also runs Full and resource/distribution checks.

The 0.1.48 workflow/refinement/hook cases retain real native PASS when scope is
undeclared, exercise advisory next actions versus blocking declared gaps, permit
source-only review and reasoned N/A, and measure single-invocation inventory/audit
sharing. A later hook must observe changed bytes; selected check reuse and exact
references survive payload trimming. Full is selected for this shared runtime
change; package/CLI and independent product evaluations are separate evidence.

The workflow/refinement/hook selectors cover classification-roundtrip revocation,
complete applicable criterion/guide connection bindings (including legacy review),
task/project gap denominators and selected-task retention under payload pressure.
The viewer/execution selectors cover omitted observation counts and exact task
`lookup --summary`: historical PASS/current STALE, NOT_RUN and current reusable
evidence remain distinct. Existing native captures prove shared-owner invalidation;
all lookup/resume/hash checks execute zero tests. The same explicit state selectors
support small task comparisons. See the [0.1.47 results](research/agent-workflow-implementation-results.md#d1d3-consumption-2026-10-09)
for package consumption and independent natural-language evaluation limits.

`tests.distribution.test_workflow_refinement` covers investigation without setup,
stable denominator/context/permissions, read-only fresh-process resume, stale
observation preservation, bounded hook previews, feedback kinds and actual native
requirement/tool confirmation with subsequent zero-execution reuse. It also covers
reason-specific retirement, revoked proof and remaining active links. The existing
focused cases now cover withdrawn-decision metadata/same-ID updates, explicit
approval subjects and relevant criteria revisions, retained quote/caller retirement,
unrelated-source rejection, and legacy/scoped investigation unknowns. Approval inputs
are synthetic fixtures, not user UI reviews. Exact package CLI/hook lookup and
fresh-task reuse retain hashes and execute zero checks. Whole-Git stale identity
is unchanged; these feedback dispositions never imply a complete product PASS.
For an immutable local package trial, set `PYTHONDONTWRITEBYTECODE=1` only on
the child-process environment and compare the complete package inventory before
and after execution. A Python cache is a changed artifact even when shipped source
bytes match; preserve the failed attempt and use a fresh build destination.
The existing
connected-product suite now contrasts direct API/Domain/SQLite restart readback
with a deliberately corrupted frontend payload; cell PASS cannot conceal that
connected failure. These are isolated synthetic cases, not original Labeler edits.

The workflow/result selectors also cover full-stack scope preparation and semantic
review staleness, feedback owner repair with actual red/green/normal native JSON,
shared UI consumer/input bindings, measured maintenance deduplication and real
registry consolidation with preserved detection. New task-local CLI usage evidence
is retained under `.work/agentic-user-flow-20261006`; it is synthetic/local, not
native Agent or protected-host acceptance. `maintain` and bundle lookup run zero
test commands. No broad evaluation or sandbox reconfiguration is needed for these
user-function checks.

Choose the smallest useful regression case or validation while editing. If a change cannot affect executable behavior, no new test is required. At Item completion, inspect the changed function, method, branch, state transition, or configuration rule plus its direct callers and public behavior using the existing diff and symbol searches. Record `changed_logic`, `affected_behaviors`, `scope`, and `reason`. Documentation-only changes with no executable, schema, test-discovery, or workflow effect may use `scope: none` and `tests: []`; use the relevant document, resource, or distribution check instead. Paths and filenames only discover candidate tests/features; they do not decide scope.

Local impact runs the smallest relevant behavior tests. Capability impact adds only relevant contract/integration tests. Cross-cutting impact runs Full. Unknown or unexplained logic impact remains `unresolved_logic_impact` and requires investigation; it does not automatically expand to Full. CI uses Full as a safe fallback only when it cannot determine the changed file set. A configured `full_trigger` emits a candidate warning; only a cross-cutting logic assessment or explicit human Full request sets `full_required`. Generated prose, Skill instructions, and manifests use focused resource/distribution checks unless their actual logic impact crosses boundaries. `not_required` names the matched assessment/rule; it never means passed.

Current selectors are machine-readable in `.harness/project.yaml`. `candidate_tests` and `candidate_features` come from path mapping, and each `feature_commands` entry is explicitly marked `fallback_candidate`. Local and CI descriptors must identify the same capability even when their argv differs. Close recomputes the cumulative Git path set from the captured source commit and rejects a stale assessment. Resource sync, distribution validation, and `git diff --check` are required when their mapped surfaces change.

Selector and command `argv` are ordered tokens, not sets: the same path may appear after both `--project` and `--changed`. Set-like source prefixes, tests, triggers, and Full warnings reject duplicates.

Dynamic capability collection consults ignored `.harness/environment-exceptions.json` first. `skip_until_manual_reenable` must prove the original subprocess was not called and that the recorded fallback plus complete environment evidence was selected. File absence is a no-op; schema or entry errors are maintain findings.

Behavior-preserving test relocation uses baseline GREEN, a path-independent identity (`capability + suite/class + test + parameter`), ownership-confined structural change, equivalent GREEN, unchanged public behavior, and working local/CI selectors.

The five representative workflows run only through installed Skill CLI entrypoints: tiny default-authorized work, brownfield cleanup transaction, large-suite impact selection, low-risk amendment rebind, and parallel worktree creation/commit/integration. Internal function imports remain unit-test seams, not acceptance evidence.

The project-workflow interruption regression exits a real child during begin/review serialization, verifies that no partial state is exposed, and resumes through a fresh CLI process. Orphan temporary attempts do not require manual deletion. This tests one writer per work record; concurrent edits to the same record and abrupt install-process recovery remain separate limits.

`complete` and `close` check submitted record consistency; they do not execute or authenticate reported product checks. Inspect actual command outcomes and observable behavior before marking checks passed. Reuse evidence while the relevant code, acceptance criteria, and execution conditions remain unchanged. Prompt changes need task-based review of resulting agent behavior; line counts and wording assertions do not establish model quality or speed.

Windows Impeccable transport regressions run with `python -m unittest tests.distribution.test_impeccable_launcher`. Native cmd and Git Bash launchers download a compiled fixture and its checksum from loopback into temporary version caches, reuse that cache across working directories, expose transport failures, and refuse missing or mismatched checksums. A failing curl fixture exercises PowerShell fallback without weakening certificate validation. This verifies local transport/cache behavior, not public release availability or live TLS/revocation access. On other platforms the native Windows cases are skipped; a skip is not PASS for those paths.

## Direct execution and verdict binding

`tests.harness.test_core_first_setup` covers a real worktree inside its parent
repository and a real child repository in a non-Git survey. The former rejects
outside-root Git probes; the latter preserves descendant discovery. Run setup,
CLI maintenance and cutover regressions for this inventory boundary.

`python -m unittest tests.distribution.test_project_workflow` exercises real Git fixtures: partition/resume, unconnected Features, changed consumers, unmapped additions/deletions, stale review, active prevention links, audit-only, private-path refusal and the existing maintain/close boundaries. Source review remains separate from runtime verification; a submitted PASS cannot discharge a missing run. `tests.distribution.test_verification_execution` exercises the viewer producer with actual child-process reports and fixed assertions. It also exercises same-plan `--resume`: completed commands stay single-run, stale/missing evidence and unknown launches are refused, and a completed checkpoint survives interruption while writing the final bundle. Controller interruption is injected at the persistence/launch boundary; this is separate from an OS process-death or authenticated Agent trial. The self-containment scanner uses Python tokens to distinguish callable subscripts from Markdown links while still checking real docstring/comment references.

Installer regression cases retain user bytes after refresh, avoid rewriting a matching install and retain recovery copies after a denied restore. Temporary installation is distinct from host Agent discovery/behavior and protected enforcement. The Windows timeout-child cleanup case remains an environment limitation when `taskkill` is denied; report its actual error rather than treating the rest of the suite as Full PASS.

For configured native-JSON checks, the same viewer's `--prepare <spec> --root <project> --plan-output <new-ignored-path>` builds registered commands and measured conditions from explicit semantic assertions without running a check. Preparation tests cover ignored/untracked config changes, untracked source byte changes, stale dependencies, report/output collisions, and unchanged ignored scratch files. The existing execution path still verifies prepared inputs before launching.

For existing multi-check evidence, `scripts/verification_results.py` joins the project plan, captures and raw observations without rerunning tests. The [input contract](../authoring/references/result-viewer.md) defines required checks, raw assertions, producer bindings and current-condition identity. Its current PASS is bounded by the project's selected criteria; it does not authenticate editable records or independently attest external runtime/fixture conditions. Run the `verification-results` selector for viewer regressions. The [implementation acceptance record](research/agent-workflow-implementation-results.md) separately records real task-local product and Agent observations.

The [Feature Map](feature-map.md) is the single user-function map. `scripts/run_check.py` captures finite foreground argv without a Skill handoff. It creates output parents, reserves a new evidence path, records a unique run ID, optional Feature/check IDs, cwd, Git HEAD/tracked diff hash/status before and after, stdout/stderr, elapsed time, native exit or unavailable/timeout. Its `behavior_verdict` remains null even when exit is zero. Use trusted checks with bounded output; argv/stdout/stderr must contain no secrets. Do not start background services with it.

```powershell
python scripts/run_check.py --cwd . --output .work/checks/native-01.json -- python -m unittest tests.distribution.test_public_catalog
python scripts/verify_product.py --feature native-verification --check verification-capture --output .work/checks/capture-01.json
```

The repository adapter reads IDs from the Markdown map and argv from `.harness/project.yaml` command descriptors/feature selectors. It executes one configured unittest command using the current Python interpreter and captures a new record. It reports JSON with `PASS` (exit 0), `ISSUES` (exit 1), or `BLOCKED` (exit 2). PASS requires a nonempty, unambiguous unittest success summary without skipped/expected-failure cases, correct run/Feature/check/argv/cwd, and matching before/after/current Git identity. Command failure produces ISSUES; unavailable, timeout, missing, wrong-target, unlinked or stale evidence produces BLOCKED. This is a check-scoped verdict, not a product-wide release decision. Native commands and CI remain independently usable; unsupported runners require their existing native checks and review.

To reassess a particular record without execution, use its returned run ID:

```powershell
python scripts/verify_product.py --feature native-verification --check verification-capture --evidence .work/checks/capture-01.json --run-id <returned-run-id>
```

The verdict includes the evidence path/hash and command identity. Before and after must also match current code: committing or changing tracked or safe untracked file bytes invalidates reuse. Ignored output belongs under `.work/`; evidence outside it may itself change Git status. Ignored inputs, installed dependency versions, fixture/runtime data, inherited environment and server identity are **not attested**. `HARNESS_SKILLS_ROOT` changes execution conditions and requires fresh evidence. Records are editable local files, not signed attestations; reassessment checks consistency, not hostile tampering or independent verifier identity. Inspect raw output and behavior for the actual acceptance criteria. A forged unittest-looking record is not authenticated by this adapter.

For runners whose stdout only names a separate JSON report, pass `--json-report <new-path>` to `run_check.py` and give that same path to the native reporter. Relative report paths resolve against `--cwd`. The capture rejects an existing report before execution and embeds the resulting JSON, raw-file SHA-256 and path in the execution record. Missing or malformed reports record an error; they do not rewrite the native exit or assign PASS. A project adapter must interpret its runner's actual selected cases, skips, errors and counts. This binds the collected report to a fresh invocation without authenticating an editable record or proving which process wrote it. Report contents, like argv/stdout/stderr, must contain no secrets. The repository unittest adapter remains unittest-specific; do not fabricate unittest output for Vitest or browser checks.

Timeout requests termination of the owned foreground process/tree (Windows taskkill, POSIX process group), preserves partial output, and records cleanup command, stdout/stderr, native exit and status in `timeout_tree_cleanup`. The check remains `execution: timeout` when cleanup raises an OS error. Failed cleanup or failed/timed-out pipe drain sets `cleanup_incomplete`. A detached child or an exited parent retaining child pipes may escape; a zero cleanup-tool exit does not prove all descendants terminated. The helper does not provide a process sandbox or replace the deferred Agent eval supervisor. No model/provider call is needed for these native checks.

The unittest adapter distinguishes discovery/import failure as BLOCKED and retains its raw cause; other nonzero native failures remain check-scoped ISSUES and require interpretation. Product-level consumers must inspect the raw failure and retain unavailable or unknown observations as `BLOCKED`, rather than calling every command failure a product defect. The current `--evidence` command reassesses one record against current Git identity; it is not a task-history viewer or a multi-layer result aggregator. Task selection and multi-layer scope lookup now use the workflow/result CLIs; their bounded acceptance evidence and remaining limits are recorded in the [implementation results](research/agent-workflow-implementation-results.md).
# Native unittest workflow connection

`python scripts/verify_product.py --feature <feature-id> --all-checks --output .work/<new-run>`
runs that Feature's registered unittest checks once and produces a workflow
`bundle.json`. For an existing capture, `--check <check-id> --evidence <capture>
--run-id <run-id> --bundle-output <new-bundle>` creates its binding without rerunning.
Use that project-relative bundle in a workflow semantic review. Audit reuses the
same canonical unittest assessor, not a stored PASS. Missing checks, wrong targets,
failed/zero/skipped suites and stale Git identity leave the obligation unresolved.
Lookup performs no test execution and writes no evidence. The adapter is scoped
to native unittest assertions and does not establish UI, Agent behavior, ignored
data, dependency or runtime identity. Native JSON observations retain their
existing richer condition binding in the result viewer.

For a preselected group of Features using the same native unittest checks, run
`python scripts/verify_product.py --features <id> <id> --all-checks --output <new-directory>`.
Equal check IDs/effective argv/cwd run once in the batch; separate IDs do not merge.
Each Feature bundle binds the same raw run only when it was named before execution.
Lookup rechecks current identity without rerunning. This is declared unittest coverage,
not automatic selection of affected Features or sharing of unrelated browser/DB criteria.

Use `--work-id <id>` or `--pending-state .work/<record>.json` instead of `--features`
to select currently required execution through the sibling workflow CLI.
The adapter refuses mismatched map/workflow check sets before execution.
NOT_REQUIRED means no commands ran; unresolved semantic/product obligations remain visible.
Returned workflow status is the pre-execution selection snapshot; current_workflow_status is recomputed after result attachment. Bundles attach to the task independently of semantic review; use read-only audit for current completion status.

The existing unittest adapter also accepts the workflow's `--context` or inherited
`AGENT_WORKFLOW_CONTEXT` with `--all-checks --output <new-directory>`. It resolves
the same exact state/root/immutable task identity and never guesses a task. Explicit
Feature selection remains independent. The workflow's connected `prepare` and
`execute` compose the native-JSON viewer; project-specific unittest execution
continues through this existing adapter.

Native-JSON execution retains runner BLOCKED/SKIP/NOT_RUN/UNKNOWN separately from
observed assertion ISSUES. Explicit installed public dependency files are measured
through `dependency.installed_file_refs` during prepare/preflight/lookup; unlisted
runtime inputs are outside the reuse claim. The connected-product fixture is a
project-owned browser/HTTP/Domain/SQLite example, not a common runner engine.

The `connected-product` selector runs `python -m unittest tests.distribution.test_connected_product`.
It executes the actual project runner twice with different report names, verifies
both flows and retained artifact hashes after cleanup, and confirms an existing
report cannot be overwritten. Artifacts/storage use one new directory per report.
An unavailable existing browser prerequisite is an explicit unittest skip, not a
verified product pass; this task's Windows execution ran the case without skips.
No dependency installation or shared user database is involved.

Registered preparation supports subdirectory commands: keep local `file_refs` relative to command cwd and declare shared inputs as `repository_file_refs` relative to the observed Git root. Config/criteria/map/UI bindings are automatic; changed shared inputs block execution and invalidate lookup.

Task-mode native JSON preparation uses the same pending selector, registered assertion path, immutable task binding and automatic result links. Scope matrix gaps and structured architecture review are tested with the workflow/result selectors. The historical HTTP trial under `.work/fullstack-task-20261006` belongs to the previous worktree and excluded FE. The current `.work/connected-acceptance` trial adds real Chromium/FE/API/Domain/SQLite/restart evidence through the packaged CLI, including feedback/UI repair, preservation and follow-up reuse. Its natural-language result lookup is a separate bounded collaboration-host case; installed Agent and protected-host acceptance remain unverified.

The 0.1.52 refinement acceptance creates a tool after task start, observes its
actual native failure, repairs it, and confirms normal/current evidence without
backfilling the task baseline. Missing red, removed ownership, a present unchanged
baseline and raw tampering remain OPEN; restoring exact retained bytes permits
remeasurement. This changes feedback resolution at the shared ordinary/Harness
boundary, so Full is selected. Product/native host consumption is separate.

The shared-result fixture in `tests.distribution.test_verification_execution`
also observes actual linked native proof through reusable scope checks. One
scope observation reads a shared bundle once while retaining different consumer
PASS/ISSUES rows and command rejection. A later call rereads changed raw; this
inspection-local sharing does not weaken whole-Git, source or scope guards.
