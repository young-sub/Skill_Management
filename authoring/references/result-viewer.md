# Existing-result lookup

Source identity is shared only within one lookup and exact command/capture cwd.
Before returning, a final Git snapshot rechecks those observations; a changed or
unavailable source invalidates current reuse. Each later invocation measures again.
This reduces repeated reads without making lookup a lock or a transactional snapshot
of a concurrently edited repository. Raw, criterion and runtime bindings still apply.

Use the bundled `scripts/verification_results.py` for compatible project records. The default lookup path reads files and runs fixed read-only Git identity queries; it never executes captured argv, tests or services, or writes inputs. Direct CLI/CI remains independent of Skills.

The existing workflow entrypoint also offers connected `prepare`, `execute`,
read-only `lookup` and task `resume`, composing this viewer without a new runner.
See [request context](workflow-obligations.md#connect-the-current-request-once).
Its plan pointer belongs to the existing task; the original viewer commands and
project-specific adapters remain usable independently.

Workflow task `lookup/resume/audit --summary` leads with task handoff and
request/impact actions. It retains pending IDs, scope denominators and omission
counts. Repeated check evidence uses `evidence_ref: feature/check` into
`features[].check_results`; verification's own coverage IDs/counts stay separate
from project coverage. Full output retains producer and condition details.
Viewer `--summary` keeps its original producer descriptors. Both retain raw
path/hash/pointer descriptors. A positive `observation_count` with
`observations_omitted: true` means validated values were omitted from presentation,
not that runtime was unobserved. Repeat the same lookup without `--summary` to
see assertions and actual values. Summary `raw_availability: UNAVAILABLE`
identifies missing/unreadable raw, while
`NOT_ATTACHED` distinguishes a capture-only native adapter without a JSON descriptor.
Retained historical PASS with `current_reuse: STALE` and `current_status: UNKNOWN` requires
revalidation. NOT_RUN denotes no execution. Native runner BLOCKED is distinct from
an observed product assertion ISSUES. Neither summary launches a check or repairs
an evidence record.

Workflow, result-viewer, prompt-hook and Harness terminal JSON uses ASCII escapes
for non-ASCII characters, preserving decoded values on legacy console encodings.
This does not change UTF-8 state/evidence files, digests, or the hook context after
JSON decoding. A completed execution can be inspected or resumed without rerunning
its checks even if an older CLI failed while printing the completed result.

```
python <agent-workflow>/scripts/verification_results.py --plan plan.json --record capture.json --assessment assessment.json --observation observed.json --current-context current.json --pretty
```

Repeat record/assessment/observation arguments for multiple checks. Exit 0 means all required checks are currently reusable PASS, 1 means issues, 2 means blocked/incomplete. Always inspect `items`, `historical`, `current`, `remaining`; ISSUES and BLOCKED can coexist.

For concise lookup, add `--summary` to `--plan` or `--bundle`. It performs the
same validation and preserves exit codes, historical/current verdicts, selection
reasons, commands, run IDs and evidence paths/hashes/pointers. It omits repeated
condition snapshots and raw assertion values from the output only. Omit the flag
to inspect those details. Summary lookup never reruns tests and cannot combine
with `--execute` or `--prepare`.

## Project-owned input

Create the plan while selecting checks, before execution. Add actual run/raw bindings after execution without rewriting criteria. Each check requires:

- `id`, `feature_id`, `expected`, `criteria_revision`, `required` (boolean), and `selection: {status: selected|excluded|not_required, reason: ...}`. Every disposition requires a nonblank string reason. Each Feature/check pair is unique. `criteria_revision` must equal `conditions.criteria.revision`; inconsistent identities are blocked. Required exclusions prevent overall PASS. Optional exclusions remain distinct from PASS.
- `conditions` with nonempty `source`, `criteria`, `command`, `dependency`, `fixture`, `runtime` objects. Source uses `revision` and `diff` (HEAD and binary tracked-diff SHA-256); new execution bindings also retain an aggregate hash of Git-visible untracked file bytes. Private or aliased untracked paths are refused without reading their contents. Ignored scratch files remain outside source identity; command uses exact `argv` and absolute `cwd`. Other identities are project-specific, observed values, not invented labels. Missing identity remains unknown; do not replace it with `not_applicable` to get PASS.
- Optional `run_id` to disambiguate repeated runs. Ambiguous records are unavailable, never picked by timestamp.
- `raw_observations` with `path`, `sha256`, `pointer`, `producer` and `assertions`. Producer requires the actual `run_id`, `capture_path` and exact `argv`, or matching `json_report_path`/`json_report_sha256` for a capture's embedded native report. Include `capture_sha256` when retaining the binding. Pointers use JSON Pointer or `$.checks[0]` notation.

Assertions are project-selected raw facts, not a generic runner parser. Each has a pointer into the raw document and exactly the applicable comparison: `equals` (strict type/value), `min_count` (positive array length), or `min` (positive numeric threshold). For example, a Vitest plan can require `$.numPassedTests` min 1, `$.numPendingTests` equals 0 and `$.numFailedTests` equals 0; a browser plan must assert actual entered/saved/reloaded values and expected cases, not merely `status: PASS`. Check the project's actual report shape and mandatory cases before selecting pointers. A zero count, missing pointer or mismatch cannot establish current PASS.

Captures use the existing `run_check.py` format. Assessments bind `feature`, `check`, `run_id`, `status`, and observed `conditions`; if `evidence` is supplied its `sha256` must match the capture. A project raw observation without identity fields may be joined only through an explicit raw descriptor. These are editable consistency records, not authenticated attestation.

`current.json` supplies independently checked current conditions under `conditions`, or per-check overrides under `checks: {"feature/check": {conditions: ...}}`. The viewer independently compares live Git HEAD/diff/status to the capture. It cannot independently attest an external runtime, dependencies, fixture, or the completeness of project criteria. Recheck those identities through the project guide; copied historical values are not current evidence. Without a current context, show historical observations and keep current reuse unavailable.

The output preserves capture path/hash/argv/exit, raw paths/hashes/pointers/producer, assertion values, original judgments, current reuse reasons and conditions. A raw document's top-level `status`, when present, participates in judgment even without `--observation`; an ISSUES/BLOCKED report cannot be hidden by selecting only its successful sub-observations. Unknown status vocabulary remains UNKNOWN for project interpretation. A historical PASS can be STALE or UNKNOWN today. Native nonzero exit, timeout, cleanup failure, required skip/not-run, missing raw or changed conditions prevent current PASS. Read-only requests never backfill missing evidence by rerunning or changing source.

## Prepare a registered execution plan

For a configured project, the same CLI can assemble deterministic plan metadata:

```text
python <agent-workflow>/scripts/verification_results.py --prepare .work/assertions.json --root <project> --plan-output .work/plan.json
```

The input is `{"schema_version":1,"checks":[...]}`. Each check has exactly
`id`, `feature_id`, `expected`, `required`, `selection`, `raw_observations`,
`dependency`, and `fixture`. Selection and native assertions use the formats above;
the last two fields are explicit nonempty project condition objects, for example
`{"file_refs":["requirements.lock"]}` or the project's identified dependency kind.
The Agent still chooses meaningful observations and explains selection; preparation
does not infer a business oracle or decide which checks can be omitted.

Preparation resolves the Feature/check pair through `.harness/project.yaml`, copies
the registered argv/cwd, measures Git and executable identity, hashes connected
criteria for their revision, and binds project configuration, criteria/map/UI references plus declared
fixture/dependency files. It reuses execution preflight without starting a check,
reading a native result or asking a model. A report must be new and at least one
check selected. Unknown Feature/check pairs, supplied command/source overrides,
unsafe paths and existing output are refused. The plan output must be Git-ignored
so writing it does not invalidate its own source snapshot. No task state is changed.

Run the resulting plan with `--execute` as below. Source or dependency changes
between preparation and execution still block; prepare a new plan after reviewing
the change. Existing report files are retained, not silently removed. File references
use command-directory-relative `file_refs` or explicit Git-root-relative
`repository_file_refs`. Preparation binds connected config/criteria/map/UI files
through the latter, preserving the registered subdirectory command and cwd. Preparation
is not execution, a semantic review, or protected completion acceptance.

For recurring runs, register the native output argument and its raw-observation
`path` as the same explicit template, for example `{report_dir}/browser.json`.
Pass `--report-dir .work/run-2/native` alongside `--prepare`, `--root` and
`--plan-output`. Preparation expands only declared report arguments and raw paths;
it leaves the registry and assertion file unchanged. This is a path prefix, not a
general template language: executable selection, embedded command strings,
undeclared arguments, escaping paths and non-ignored output directories are
refused. Existing report files remain protected by the normal no-overwrite check.
Fixed-path registrations continue to work without this option.

The prepared conditions retain the resolved report directory and exact expanded
argv. Workflow evidence checking resolves the current registered template against
that directory before comparing the captured command and cwd; another executable
or argument cannot satisfy the check. Two fresh run directories therefore do not
change source/configuration identity or stale the earlier result merely by
choosing another output location. Use `--bundle` for lookup and the original plan
with `--resume` for interrupted work; neither requires a new report directory.

When a project uses an already installed browser or library outside its checkout,
declare the actual public files in `dependency.installed_file_refs` as explicit
absolute paths. Preparation, preflight and read-only lookup hash those files
again. Relative, missing, private or aliased paths are refused; this option never
installs a dependency, launches a discovery command or reads fixture/credential
data outside the project. Bind the files that determine the selected runner's
behavior. A version string or an old Doctor report alone is not current identity;
unlisted transitive inputs remain outside the reuse claim.

Native reports may retain top-level BLOCKED, SKIP or NOT_RUN. The execution
assessment preserves those observation states, and unrecognized report statuses
remain UNKNOWN; a missing assertion in an unobserved case is not classified as a
product assertion failure. Incomplete capture execution is BLOCKED. Required
zero/skipped cases still cannot PASS, and only the plan may exclude a check.
Project runners own the actual case/count/skip/error classification and meaningful
assertions; the common viewer is not a parser for every runner.

## Explicit execution

For a retained execution, `python <agent-workflow>/scripts/verification_results.py --bundle .work/verification/run-1/bundle.json` performs read-only lookup. It remeasures all current inputs, including those an earlier or later check might have changed. Bound requirements, selection, command, and raw assertions must still match the original plan; editable files are consistency evidence, not protected attestation.

Execution is a separate, opt-in CLI path. The caller provides a preselected plan
and a new evidence directory. In an installed agentic-coding plugin the CLI uses
that package's `scripts/run_check.py` automatically; no project copy or tool-path
search is needed. A standalone Skill requires `--run-check`; an explicit path
also overrides the plugin default. Discovery checks only the enclosing package
identity and fixed local path, never PATH or unrelated installations. This is
local tool selection, not package authentication or protected acceptance.

```
python <agent-workflow>/scripts/verification_results.py --execute \
  --plan plan.json --run-check <project>/scripts/run_check.py \
  --evidence-dir .work/verification/run-1 --pretty
```

Before starting any child, the executor validates the selected check's exact `conditions.command.argv` and absolute `cwd`, current `conditions.source.revision`/`diff`, and each native `raw_observations` descriptor. A selected check must provide one new report path and explicit `equals`, `min_count`, or `min` assertions. Report paths and evidence captures cannot be reused. Excluded and `not_required` checks are not run.

`conditions.dependency.file_refs` and `conditions.fixture.file_refs` may list project files (the `files` key is accepted as an alias). The executor measures their SHA-256 values before preflight and immediately before every child; a prior child changing a later check's inputs prevents that child from starting. It also records the selected command's resolved executable, executable SHA-256, and wrapper Python version when the executable is the wrapper itself; the same runtime identity is remeasured before each child and during bundle lookup. File references must be relative, non-private, and free of symlink/junction components. `file_refs` stay inside the command directory; `repository_file_refs` use the independently observed Git root and cannot escape it. Both are hashed before execution and during lookup; `.git` metadata references are refused. Source identity includes untracked files across that repository, including siblings of the command directory. Native report paths must be new, non-private, non-aliased, and inside either the command project or the evidence directory. A changed or missing file makes reuse stale or unknown. The source plan is never rewritten; generated `bound-plan.json`, captures, assessments, `current-context.json`, and a persisted `bundle.json` are written under the supplied evidence directory.

Selected Feature/check pairs may share one native report only when their check
ID and complete measured execution conditions are identical (including command,
cwd, source, criteria, dependencies, fixture and runtime). The executor uses the
capture tool's existing `--also-feature` consumers, runs that producer once, and
assesses each Feature's own expected values independently. A failure for one
consumer never inherits another consumer's PASS. Different conditions sharing a
report are refused before launch. Different report paths are separate executions.

A shared producer publishes one checkpoint containing all consumer assessments.
An interrupted launch without that checkpoint remains unknown and is not replayed;
a completed group resumes without running its command again. This is local
condition/evidence reuse, not protected result authority.

Each selected command is passed unchanged to the existing `run_check.py` with an explicit `--json-report` path. The executor reads the resulting capture and native report, creates the producer/assessment binding from the run ID and assertion observations, and then calls the same viewer. It derives `PASS` only when the native process exits successfully and every plan assertion matches. It does not infer a verdict from a report's `PASS` string, stdout, timestamps, zero counts, or a submitted result field. Missing reports, zero/skip assertion failures, wrong target/run bindings, stale conditions, and nonzero/timeout captures remain non-PASS. A mutation of the original plan during a child also invalidates the execution result. The JSON response includes an `execution.bundle` descriptor and `execution.bundle_path` for the persisted descriptor; `view_bundle(bundle_path)` or `view_bundle(descriptor)` remeasures source and declared file references, verifies the original-plan hash, and joins the same viewer without executing or writing. Passing that descriptor back to the ordinary lookup path remains read-only.


## Resume interrupted execution

Repeat the same `--execute --plan ... --evidence-dir ...` command with `--resume`.
Each command has a durable launch marker, and each completed check has an
immutable `checkpoint-N-bundle.json` readable by the normal `--bundle` lookup.
Resume revalidates the original plan and current raw/conditions, keeps completed
current checks (including intact known failures), and executes only never-started checks. A completed failed check stays ISSUES while pending checks continue. Selected
optional checks retain their original optional policy. The completed final bundle
is a read-only no-op on repeat. The last complete checkpoint also remains usable
if writing the final bundle was interrupted. Resume repairs the canonical
`bundle.json` used by workflow consumers and preserves a torn descriptor as
`bundle.interrupted-<sha256>.json`. Raw/capture/checkpoint files remain unchanged.
Use one controller per execution directory; external concurrent edits are unsupported.

A start marker without a completed checkpoint means the outcome is unknown:
resume refuses to replay that command, even if a raw report exists. Inspect and
reconcile the actual operation before planning any retry; removing a marker is
not evidence that retry is safe. Changed criteria/source/dependencies, missing
raw and damaged checkpoints also block reuse. Preserve the old run and create a
new plan/output path when a repair changes the conditions. These local files are
not a protected acceptance boundary. No LLM call is needed to resume or look up.
# Full-stack scope on the existing Feature

Declare `coverage` once on an `extensions.workflow.features` entry. Each row has
`id`, project-relative `requirement`, `outcome`, `perspectives` (`business`,
`architecture`), `areas` (`FE`, `BE/API`, `Domain`) and `kind` (`test`, `review`).
Test rows reference an existing `check`; an absent/inactive link is MISSING.
Optional `method` is `direct`, `cross-layer` or `e2e`; connection methods are not
responsibility areas or partitions. Declare only applicable scope; the Agent owns
that semantic selection. Existing Features without declarations remain supported.

```json
{"id":"save-readback","requirement":"docs/requirements.md","outcome":"Saved order survives reload","perspectives":["business"],"areas":["FE","BE/API","Domain"],"kind":"test","method":"e2e","check":"order-flow"}
```

Preparation snapshots the selected Features' scope from the registry, binds its
requirement files, and execution/bundle/`--summary` retain `coverage.rows`, separate
axis counts and `coverage.gaps`. Rows link run/argv/cwd/native exit/raw pointers and
original judgment/current reuse. Scope completeness is separate from check-scoped
PASS: NOT_RUN, MISSING, ISSUES, BLOCKED, STALE and reasoned NOT_REQUIRED remain visible.
No missing row causes a command to run automatically.

For architecture/business semantic review, record `scope_reviews` keyed by the
coverage row ID in the existing workflow review. Each entry has `status` (PASS,
ISSUES, BLOCKED, NOT_REQUIRED), `analysis`, existing-file `references`, and `reason`
for an exclusion. PASS here is explicitly an Agent semantic review, never an
automated-test verdict. `--prepare ... --workflow-state .work/task.json` snapshots
these reviews; changed Feature inputs or reference bytes make them STALE. Without
a review they remain NOT_RUN. For a review completed after execution, use
`--bundle <bundle.json> --workflow-state .work/task.json --summary`: it reads the
same project's current review record without rerunning tests. Review rows retain
original `historical_status`/`historical_evidence` separately from the current
analysis/reference binding; changed inputs or incomplete reviews remain stale or
blocked. Historical plans/raw are preserved. Lookup never
executes a command from the scope or reviews.

## Task scope and required execution

`coverage.registered_status` counts declared rows only. `coverage.status` describes
the declared task scope; neither attests that every requirement was discovered.
`coverage.matrix` projects business/architecture × FE/BE/API/Domain independently,
with `in_task` identifying the current work's impact. Method remains direct,
cross-layer or e2e. Empty cells are UNDECIDED, never PASS or an automatic exclusion.

In the existing Feature review's `scope_reviews`, use cell keys such as
`business:Domain`. Each cell decision has `status: REQUIRED`, `coverage: [row IDs]`,
`analysis` and existing-file `references`, or `status: NOT_REQUIRED` with a nonblank
`reason`, analysis and references. Required cells must account for every matching
declared row, either by an explicit link or a reasoned row exclusion. A check
tagged with several areas does not automatically confirm the other cells.
MISSING connections, NOT_RUN, ISSUES, BLOCKED with reasons, UNDECIDED,
NOT_REQUIRED and STALE remain distinct. Rows retain original run, command, target,
judgment and raw pointers. Check PASS, scope completion and workflow obligations
are separate results; exclusions are not test passes.

Register the reusable assertion file once at `extensions.workflow.assertions`.
For later tasks, the existing CLI recomputes required checks instead of asking
the Agent to reconstruct the command order or rewrite assertions:

```text
python <agent-workflow>/scripts/verification_results.py --prepare --root <project> --pending-state .work/task.json --plan-output .work/run-2/plan.json --report-dir .work/run-2/native
python <agent-workflow>/scripts/verification_results.py --plan <project>/.work/run-2/plan.json --execute --evidence-dir <project>/.work/run-2/evidence
python <agent-workflow>/scripts/verification_results.py --bundle <project>/.work/run-2/evidence/bundle.json --summary
python <agent-workflow>/scripts/project_workflow.py audit --root <project> --state .work/task.json
```

Standalone/repository execution also passes `--run-check <project>/scripts/run_check.py`;
the plugin already discovers its bundled capture tool. `--work-id` selects the
existing Harness baseline instead of `--pending-state`. An explicit
`--prepare <assertion-file>` remains supported. Preparation selects affected
Features, keeps same-Feature exclusions/reuse explanations, and starts no command.
Missing required assertions block. With no pending checks it returns NOT_REQUIRED
and creates no plan; required Features without check connections remain BLOCKED.

Execution rechecks task identity, selection and measured conditions, then retains
the bundle pointer in that task's existing `results` field independently of
semantic review. Review does not have to be complete to see real test results.
Valid check evidence is reused individually; only unavailable checks are selected
again. Completed `--resume` and lookup execute zero commands and do not change the
task state. Existing bundles remain preserved. Single-writer task updates remain
the supported concurrency boundary, not host-protected attestation.

An architecture review row needs structured `architecture` evidence alongside
its Agent analysis: nonempty `flows` with owner file, call/state/data descriptions
and references; `boundaries` covering contract/dependency/failure with analysis
and references; and `findings` with problem, owner, references and open/fixed/excluded
disposition. Open findings remain ISSUES even with a submitted PASS. Removing a
coverage row or retiring its Feature keeps the owner/problem/reference evidence
and product-resolution obligation; a later review cannot drop their IDs without
a disposition. Exclusion
needs a reason. A fixed finding's `repair` binds owner `path`, `before_sha256` from
the work baseline and actual `after_sha256`; unchanged owner bytes cannot claim a
repair. Code validates structure and freshness, while the Agent judges meaning
and sufficiency. Scope references are hashed independently so changing one
review's extra reference stales that review, rather than every sibling review.
