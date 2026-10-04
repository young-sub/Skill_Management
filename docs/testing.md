# Testing And Impact Selection

Choose the smallest useful regression case or validation while editing. If a change cannot affect executable behavior, no new test is required. At Item completion, inspect the changed function, method, branch, state transition, or configuration rule plus its direct callers and public behavior using the existing diff and symbol searches. Record `changed_logic`, `affected_behaviors`, `scope`, and `reason`. Documentation-only changes with no executable, schema, test-discovery, or workflow effect may use `scope: none` and `tests: []`; use the relevant document, resource, or distribution check instead. Paths and filenames only discover candidate tests/features; they do not decide scope.

Local impact runs the smallest relevant behavior tests. Capability impact adds only relevant contract/integration tests. Cross-cutting impact runs Full. Unknown or unexplained logic impact remains `unresolved_logic_impact` and requires investigation; it does not automatically expand to Full. CI uses Full as a safe fallback only when it cannot determine the changed file set. A configured `full_trigger` emits a candidate warning; only a cross-cutting logic assessment or explicit human Full request sets `full_required`. Generated prose, Skill instructions, and manifests use focused resource/distribution checks unless their actual logic impact crosses boundaries. `not_required` names the matched assessment/rule; it never means passed.

Current selectors are machine-readable in `.harness/project.yaml`. `candidate_tests` and `candidate_features` come from path mapping, and each `feature_commands` entry is explicitly marked `fallback_candidate`. Local and CI descriptors must identify the same capability even when their argv differs. Close recomputes the cumulative Git path set from the captured source commit and rejects a stale assessment. Resource sync, distribution validation, and `git diff --check` are required when their mapped surfaces change.

Selector and command `argv` are ordered tokens, not sets: the same path may appear after both `--project` and `--changed`. Set-like source prefixes, tests, triggers, and Full warnings reject duplicates.

Dynamic capability collection consults ignored `.harness/environment-exceptions.json` first. `skip_until_manual_reenable` must prove the original subprocess was not called and that the recorded fallback plus complete environment evidence was selected. File absence is a no-op; schema or entry errors are maintain findings.

Behavior-preserving test relocation uses baseline GREEN, a path-independent identity (`capability + suite/class + test + parameter`), ownership-confined structural change, equivalent GREEN, unchanged public behavior, and working local/CI selectors.

The five representative workflows run only through installed Skill CLI entrypoints: tiny default-authorized work, brownfield cleanup transaction, large-suite impact selection, low-risk amendment rebind, and parallel worktree creation/commit/integration. Internal function imports remain unit-test seams, not acceptance evidence.

`complete` and `close` check submitted record consistency; they do not execute or authenticate reported product checks. Inspect actual command outcomes and observable behavior before marking checks passed. Reuse evidence while the relevant code, acceptance criteria, and execution conditions remain unchanged. Prompt changes need task-based review of resulting agent behavior; line counts and wording assertions do not establish model quality or speed.

Windows Impeccable transport regressions run with `python -m unittest tests.distribution.test_impeccable_launcher`. Native cmd and Git Bash launchers download a compiled fixture and its checksum from loopback into temporary version caches, reuse that cache across working directories, expose transport failures, and refuse missing or mismatched checksums. A failing curl fixture exercises PowerShell fallback without weakening certificate validation. This verifies local transport/cache behavior, not public release availability or live TLS/revocation access. On other platforms the native Windows cases are skipped; a skip is not PASS for those paths.

## Direct execution and verdict binding

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

The verdict includes the evidence path/hash and command identity. Before and after must also match current code: committing, changing tracked content, or changing listed untracked paths invalidates reuse. Ignored output belongs under `.work/`; evidence outside it may itself change Git status. Untracked file contents, installed dependency versions, fixture/runtime data, inherited environment and server identity are **not attested**. `HARNESS_SKILLS_ROOT` changes execution conditions and requires fresh evidence. Records are editable local files, not signed attestations; reassessment checks consistency, not hostile tampering or independent verifier identity. Inspect raw output and behavior for the actual acceptance criteria. A forged unittest-looking record is not authenticated by this adapter.

For runners whose stdout only names a separate JSON report, pass `--json-report <new-path>` to `run_check.py` and give that same path to the native reporter. Relative report paths resolve against `--cwd`. The capture rejects an existing report before execution and embeds the resulting JSON, raw-file SHA-256 and path in the execution record. Missing or malformed reports record an error; they do not rewrite the native exit or assign PASS. A project adapter must interpret its runner's actual selected cases, skips, errors and counts. This binds the collected report to a fresh invocation without authenticating an editable record or proving which process wrote it. Report contents, like argv/stdout/stderr, must contain no secrets. The repository unittest adapter remains unittest-specific; do not fabricate unittest output for Vitest or browser checks.

Timeout requests termination of the owned foreground process/tree (Windows taskkill, POSIX process group), preserves partial output, and records the cleanup exit when attempted. A detached child or an exited parent retaining child pipes may escape; `cleanup_incomplete` means pipe draining timed out. A zero cleanup-tool exit does not prove all descendants terminated. The helper does not provide a process sandbox or replace the deferred Agent eval supervisor. No model/provider call is needed for these native checks.
