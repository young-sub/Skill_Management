# Testing And Impact Selection

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

Timeout requests termination of the owned foreground process/tree (Windows taskkill, POSIX process group), preserves partial output, and records the cleanup exit when attempted. A detached child or an exited parent retaining child pipes may escape; `cleanup_incomplete` means pipe draining timed out. A zero cleanup-tool exit does not prove all descendants terminated. The helper does not provide a process sandbox or replace the deferred Agent eval supervisor. No model/provider call is needed for these native checks.

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
