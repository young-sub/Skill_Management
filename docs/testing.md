# Testing and impact selection

Actual Labeler storage acceptance uses the project-specific
`scripts/verify_labeler_storage.mjs`; isolated setup, environment inputs and raw
boundaries are in [the sequential verification record](research/delegation-verification-20261022.md).
It is opt-in local-product acceptance, not part of fixture-only Full runs.

For a direct captured check, after the final edit use
`python scripts/run_check.py --cwd . --lookup <ignored-capture.json>`.
This read-only check reports source CURRENT/STALE/UNKNOWN and retains the command
exit code; interpret behavior from the original assertions/output. It neither
executes tests nor attests ignored inputs, dependencies or runtime identity.

Prompt-hook regressions compare the same retained fixture and request modes,
including unconfigured development/nondevelopment, unselected candidates and
explicit task context. Measure elapsed p50/p95 alongside file/Git calls and UTF-8
context bytes; small local samples are not model token/cost or native-host latency
claims. Snapshot task/evidence bytes and require zero product commands during
lookup. Scoped source reuse additionally needs actual execution, independent
related/shared/addition/deletion controls, unrelated edits, saved-context replay
rejection and only-affected reexecution. Legacy undeclared inputs must retain
conservative stale checks. The [local improvement record](research/luna-0.1.79-local-improvements.md)
links the retained measurements and failed attempts.

For non-secret Unicode input to a foreground native command, `scripts/run_check.py --stdin-file <UTF-8-file> --cwd <project> --output <new-capture> -- <argv>` snapshots and passes exact input bytes, independently of the calling shell's output encoding. Relative input paths resolve against cwd. Invalid UTF-8 fails before launch; input path/size/hash are retained. Use the editor to create the file and inspect output bytes. Existing `?` replacement is irreversible and valid UTF-8, so this does not detect arbitrary previously damaged prose or protect commands that bypass this transport.

Choose the smallest useful regression case or validation while editing. If a change cannot affect executable behavior, no new test is required. At Item completion, inspect the changed function, method, branch, state transition, or configuration rule plus its direct callers and public behavior using the existing diff and symbol searches. Record `changed_logic`, `affected_behaviors`, `scope`, and `reason`. Documentation-only changes with no executable, schema, test-discovery, or workflow effect may use `scope: none` and `tests: []`; use the relevant document, resource, or distribution check instead. Paths and filenames only discover candidate tests/features; they do not decide scope.

Local impact runs the smallest relevant behavior tests. Capability impact adds only relevant contract/integration tests. Cross-cutting impact runs Full. Unknown or unexplained logic impact remains `unresolved_logic_impact` and requires investigation; it does not automatically expand to Full. CI uses Full as a safe fallback only when it cannot determine the changed file set. A configured `full_trigger` emits a candidate warning; only a cross-cutting logic assessment or explicit human Full request sets `full_required`. Generated prose, Skill instructions, and manifests use focused resource/distribution checks unless their actual logic impact crosses boundaries. `not_required` names the matched assessment/rule; it never means passed.

Current selectors are machine-readable in `.harness/project.yaml`. `candidate_tests` and `candidate_features` come from path mapping, and each `feature_commands` entry is explicitly marked `fallback_candidate`. Local and CI descriptors must identify the same capability even when their argv differs. Close recomputes the cumulative Git path set from the captured source commit and rejects a stale assessment. Resource sync, distribution validation, and `git diff --check` are required when their mapped surfaces change.

Selector and command `argv` are ordered tokens, not sets: the same path may appear after both `--project` and `--changed`. Set-like source prefixes, tests, triggers, and Full warnings reject duplicates.

Dynamic capability collection consults ignored `.harness/environment-exceptions.json` first. `skip_until_manual_reenable` must prove the original subprocess was not called and that the recorded fallback plus complete environment evidence was selected. File absence is a no-op; schema or entry errors are maintain findings.

Behavior-preserving test relocation uses baseline GREEN, a path-independent identity (`capability + suite/class + test + parameter`), ownership-confined structural change, equivalent GREEN, unchanged public behavior, and working local/CI selectors.

The five representative workflows run only through installed Skill CLI entrypoints: tiny default-authorized work, brownfield cleanup transaction, large-suite impact selection, low-risk amendment rebind, and parallel worktree creation/commit/integration. Internal function imports remain unit-test seams, not acceptance evidence.

The project-workflow interruption regression exits a real child during begin/review serialization, verifies that no partial state is exposed, and resumes through a fresh CLI process. Orphan temporary attempts do not require manual deletion. TaskStore process regressions additionally cover concurrent stale writers; abrupt install-process recovery remains separate.

`complete` and `close` check submitted record consistency; they do not execute or authenticate reported product checks. Inspect actual command outcomes and observable behavior before marking checks passed. Reuse evidence while the relevant code, acceptance criteria, and execution conditions remain unchanged. Prompt changes need task-based review of resulting agent behavior; line counts and wording assertions do not establish model quality or speed.

Windows Impeccable transport regressions run with `python -m unittest tests.distribution.test_impeccable_launcher`. Native cmd and Git Bash launchers download a compiled fixture and its checksum from loopback into temporary version caches, reuse that cache across working directories, expose transport failures, and refuse missing or mismatched checksums. A failing curl fixture exercises PowerShell fallback without weakening certificate validation. This verifies local transport/cache behavior, not public release availability or live TLS/revocation access. On other platforms the native Windows cases are skipped; a skip is not PASS for those paths.

## Native capture reuse and observation

Named command descriptors may declare `evidence_inputs` (project-relative files,
directories or patterns). Review all transitive dependencies before opting in.
The unittest adapter always adds the registry, selected test modules and each
consumer's Feature sources/map/criteria. Shared execution binds their union.
Matching additions/deletions or changes invalidate the capture; unrelated edits
outside this declared scope do not. Ignored files, aliases and sensitive inputs
cannot be declared. Without opt-in, whole-Git invalidation remains in force.
This does not attest installed dependencies or external runtime state.

`verify_product.py` uses CLI `--timeout`, then the command's `timeout_seconds`,
then 300 seconds. The measured long `workflow-obligations` check declares 900.
Capture publishes a running stage/PID and a timeout-cleanup stage; timeout is
never PASS. Cleanup targets the process tree started by that capture, retains
cleanup failures and bounds pipe draining. Inspect a retained cleanup failure
before retrying; it is not permission to stop unrelated processes.

The connected-product fixture accepts `--artifact-dir` inside an accessible
workspace. It probes write/read access before launch and refuses to overwrite
existing artifacts. Browser capture, runner readability and actual visual
observation are separate facts. The agent must open the screenshot itself and
record its observation; readable bytes alone do not prove a visual review.

## Commands

Use `.harness/project.yaml` feature selectors for affected behavior. Common direct commands:

```powershell
python -m unittest tests.distribution.test_project_workflow tests.distribution.test_workflow_refinement tests.distribution.test_workflow_hook tests.distribution.test_completion_guard
python -m unittest tests.distribution.test_verification_results tests.distribution.test_verification_execution
python -m unittest tests.distribution.test_task_store tests.distribution.test_runtime_api tests.distribution.test_check_capture
python -m unittest tests.distribution.test_repository_docs
powershell -NoProfile -File scripts/sync-skill-resources.ps1 -Check
powershell -NoProfile -File scripts/validate-distribution.ps1
git diff --check
```

Run `sync-skill-resources.ps1` without `-Check` after canonical edits. For cross-cutting runtime impact run `python -m unittest discover -s tests -p "test_*.py"` once after focused regression. Required browser acceptance uses `CONNECTED_PRODUCT_REQUIRED=1`; missing prerequisites fail, optional local skips remain unverified. The existing connected-product runner must retain normal observations, reject the UI payload fault while API/Domain controls pass, clean up owned resources and preserve artifacts. Hosted CI is a separate execution boundary.

## Execution, lookup and preservation

For parallel implementation, freeze identical input/interface/oracle before comparing
sequential and delegated runs. Keep exclusive file ownership and one integration
writer; inspect actual integrated behavior, including rejected writes and fresh read.
Reconcile completed, failed, pending and unknown execution handles before resume.
Existing checkpoint, unknown-launch and worktree regressions remain the runtime
checks; worker PASS and catalog discovery are not integrated or native-host proof.
The [stage 6 record](research/stage6-parallel-delegation-results.md) retains attempts,
conflicts, rework, assistance, non-use and unknown usage/cost separately.


For effect evaluation, freeze the short request, source/catalog, project and existing
oracle before each consumer or control launch. Preserve failures, non-use, retries
and unexecuted cases; count coached corrections separately. A description-only
comparison does not establish whole-stage effectiveness, and supplied-catalog
discovery does not establish native-host discovery. Keep unchanged defect/normal
controls separate from model outcomes; uncollected usage and cost remain unknown.
The [stage 5 record](research/stage5-effect-evaluation-results.md) reuses existing
batch, connected-product and lookup/resume checks without a new runner.

Stage 4A consumption selects task playbooks from a short request and the whole
source catalog, then inspects actual implementation/normal and failure observations.
For recall, hash project state/evidence before and after the read-only phase and
inspect command history for zero product execution. Exercise dirty source,
historical/missing evidence, unknown launches and absent rationale separately;
only an actual resume request may perform the recovered next action. Reuse existing
lookup/resume regression tests for completed/unknown effects. For design comparison,
fix equal inputs and criteria before experiments and inspect the adopted change's
affected regressions. Record assisted consumption, catalog discovery, native-host
discovery, retries and non-use separately; see the [4A record](research/stage4a-playbooks-recall-results.md).

For design changes, use [change impact](../authoring/references/change-impact.md)
to select affected callers, types, state/data and module boundaries. Define failure
criteria before consuming `architect` on an isolated implementation, then inspect
actual code, normal/error behavior and fresh-read data preservation. Follow-up
short-request discovery and tiny direct edits test different claims; record hints,
failures, retries and unexecuted paths separately from distribution validation.

For UI guide reuse, use the existing
[comparison procedure](../authoring/references/repair-and-reuse.md#ui-discovery-and-comparison)
and [guide execution steps](../authoring/references/project-verification.md#execute-and-repair-the-existing-guide).
The connected-product fixture exercises its project-owned guide and observer;
keep intentional visual variants separate from injected regressions and inspect
the screenshots as well as keyboard/state/save observations. Fresh-context reuse
records the short request, discovered owners, assistance and actual run; package
checks alone cannot establish discovery. See the [stage 3 results](research/stage3-ui-guide-reuse-results.md).

For human corrections and success extraction, use the
[feedback/success procedure](../authoring/references/feedback-and-success.md).
Before consumption define failure/bypass/nearby-normal and new-context output
criteria. Exercise the changed guidance on an isolated task, then consume the
extracted procedure with short input in a fresh context. Existing feedback
regressions cover inheritance and stale proof; distribution checks cover links and
generated resources. Neither establishes model compliance. Preserve assistance,
failure/retry/non-execution and unaided-discovery limits in the existing task report.

For feature, bug-fix and refactoring tasks, select the applicable [task criteria](../authoring/references/project-verification.md#task-verification) before execution. The [stage 1 consumption record](research/stage1-task-verification-results.md) reuses stage 0 tasks and the existing connected-product runner; instruction routing needs actual consumption, while package/link checks establish distribution only. Connected changes retain both normal persistence/reload and rejected-write readback, independently of layer test results.

Use [Feature Map](feature-map.md) and the existing registered command/adapter. `scripts/run_check.py --cwd <project> --output <new-capture.json> -- <argv>` captures finite foreground execution, source identity, stdout/stderr, native exit and cleanup. A new `--json-report` binds the real runner report. Never start detached services through this capture. Running captures are unfinished invocations: wait on their owner and inspect the same path. Unknown launches are not replayable.

The [result viewer contract](../authoring/references/result-viewer.md) owns native JSON prepare/execute/bundle lookup. [Workflow obligations](../authoring/references/workflow-obligations.md) owns start/connect, absolute in-project task selectors and read-only audit/lookup/resume. Reuse these commands; do not add another runner or parser. Lookup executes zero product commands and preserves state/raw. A completed checkpoint preserves already executed effects.

The repository unittest adapter remains available:

```text
python scripts/verify_product.py --feature <feature> --all-checks --output .work/<new-run>
python scripts/verify_product.py --pending-state .work/<task.json> --all-checks --output .work/<new-run>
python scripts/verify_product.py --feature <feature> --check <check> --evidence <capture> --run-id <id>
```

Use `--work-id`/`--context` for the existing task selector; `--features <id> <id>` shares one identical check/argv/cwd execution among preselected consumers. Required zero/skipped/error cases, wrong target, stale source or unavailable evidence cannot be PASS. Native command failure requires raw inspection to distinguish product, oracle and environment causes. Ignored data, dependencies, external runtime and authenticated host identity are outside the unittest adapter's claim.

Semantic review after execution joins the existing evidence; it does not require another run. Report selected behavior/reason, actual observations, current reuse, required unverified scope, cleanup and remaining conditions. Skill instruction changes affect Agent behavior: check actual discovery/consumption when that behavior changes, not only wording or link counts.

## Boundaries and retained evidence

`tests.distribution.test_plugin_package` builds outside the checkout and exercises
the packaged tools. It also checks that the portable README resolves only to
included package files and that its bytes are in the content inventory. This
checks distribution/navigation, not whether a model follows the guide correctly.

For plugin packaging/hook changes, use the native discovery and session loading
commands in [the plugin guide](plugins.md#native-use-in-codex-and-claude-code).
Check each host's plugin identity, namespaced Skills and hook status. A native
local transport test can establish Skill-body and hook-context delivery without
paid inference; it cannot establish model task success. A protected verifier is
not required for these checks. Keep native failure/timeout and cleanup records.

The public API static check and TaskStore process regressions protect shared ownership, stale-writer rejection, interrupted writes and explicit reapplication. Existing execution tests protect state/effects and required evidence. Do not replace these with submitted success flags. Public API checks are not whole-program type proof.

Keep failures, retries, assistance, raw reports and screenshots under `.work/`; cleanup removes only owned temporary resources. Frozen-package verification pins the clean source commit and package hashes before/after actual consumption (`PYTHONDONTWRITEBYTECODE=1` for child processes). Do not overwrite old evidence or call prior tests current. Fixture, package CLI, real product, native discovery/hook and protected-host acceptance are separate results.

[Historical testing notes](research/archive/testing-through-0.1.68.md) retain earlier version-specific regressions and benchmark manifests. Benchmark commands live in `scripts/evaluate_benchmark.py` and `scripts/run_benchmark_agent.py`; use their help and the [benchmark plan](research/agentic-harness-benchmark-plan.md) only when evaluation can change adoption. Unknown model/usage/cost stays unknown. [Hardening results](research/core-hardening-results.md) and [implementation results](research/agent-workflow-implementation-results.md) are prior evidence, not new runs.

## Skill scenario release gate

Before publishing a release that changes routing, hooks or Skill text, install it and run
the fixed scenarios against real projects (paid headless sessions):

```powershell
python scripts/run_skill_scenarios.py --scenarios tests/scenarios/skill_routing.json --output .work/scenario-gate/<new-dir>
```

Each scenario clones the named project, optionally plants one labelled synthetic fault,
runs `claude -p` with the installed plugin and records invoked plugin Skills, the hook
`route`, Stop-guard blocks, cost and post-session probes (the fault re-applied, or an
alternate-path fault, must make the named checks fail). Exit 1 blocks the release.
`--dry-run` lists scenarios without cloning or model calls; `tests.distribution.test_skill_scenarios`
checks the gate logic without model runs.

## Delegation effect evaluation

A release that claims better delegated outcomes must beat plugin OFF on the held-out
suite in `evals/delegation-v1/` (paid headless sessions; prompts and hidden files are
frozen before the first paid run):

```powershell
python scripts/run_delegation_eval.py --scenarios evals/delegation-v1/scenarios.json --output .work/delegation-eval/<new-dir> `
  --condition off=off --condition lean=plugin:<built package> --reps 3 --jobs 2
```

Every condition disables the installed `agentic-coding` plugin through `--settings`;
`plugin:<dir>` loads one package with `--plugin-dir`, so no global configuration
changes. Hidden acceptance tests are copied in only after the sessions and probes.
The report gives verified success, false completion (claimed done while hidden or
regression checks fail; crashes and timeouts excluded), probe kill rate of the tests
the agent left behind, tokens, cost and wall time per condition. Adoption criteria and
results live in the version's research record. `tests.distribution.test_delegation_eval`
checks the runner with a fake executable.

The v2 suite is `evals/delegation-v2/scenarios.json`. Clones and private dependency
copies use `--work-root` (default `.work/e/<8-character cell hash>/r` for the clone),
while transcripts, checks and `workspace.json` remain in the readable output cell.
Before cloning or launching a paid session, the runner scans the pinned Git tree
and dependency sources. `--path-limit` defaults to 240 characters, retaining room
below Windows file (259) and directory (248) limits for generated files. It falls
back to `%SystemDrive%/e/<hash>` if needed; an impossible plan records
`path_budget_exceeded` with lengths and offending paths without launching a session.
Git clone and checkout explicitly disable `core.longpaths`; no host setting changes.
`--copy-deps --prune-clones` gives each cell private dependencies and removes only
its short workspace, detaching junctions first without recursive deletion.

A device claimed to differ from OFF is first falsified offline, with no coding agent:
`evals/path-check-offline/` runs only an independent verifier on frozen v2 reference and
partial implementations against criteria committed before the first verifier session
([record](research/independent-path-check-offline.md)). `tests.distribution.test_path_check_offline`
checks its inventory and scoring without a model.

Before a paid ON/OFF run, a candidate device is replayed on the recorded ON failures:
`evals/failure-replay/` rebuilds failed attempts from their transcripts on fresh clones, keeps
only those that reproduce their recorded regression/hidden results, and counts how many each
candidate would have changed under rules committed before the first verifier session.
`evals/l5-on-off/` holds the pre-registered criteria and the one-command runner for the next
comparison (`off`, `on`, one ablation). `tests.distribution.test_failure_replay` and
`tests.distribution.test_l5_on_off` check replay, ablation removals and scoring without a model.

`--resume-from <state.json>` reuses valid cells and retains all prior attempts and
costs. Reopening an output with `state.json` resumes its unattempted cells. Paid or
interrupted cells are never silently replayed. Cell exceptions are recorded as
excluded infrastructure results and the remaining matrix continues; reports judge
only valid cells and retain excluded evidence and unknown costs explicitly.
