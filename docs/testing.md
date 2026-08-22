# Testing And Impact Selection

Use the exact TDD or regression case while editing. At Item completion, inspect the changed function, method, branch, state transition, or configuration rule plus its direct callers and public behavior using the existing diff and symbol searches. Record `changed_logic`, `affected_behaviors`, `scope`, and `reason`. Paths and filenames only discover candidate tests/features; they do not decide scope.

Local impact runs exact behavior tests. Capability impact adds only relevant contract/integration tests. Cross-cutting impact runs Full. Unknown or unexplained impact becomes `unresolved_logic_impact`, blocks completion, and does not auto-expand to Full. A configured `full_trigger` emits a candidate warning; only a cross-cutting logic assessment or explicit human Full request sets `full_required`. Generated prose, Skill instructions, and manifests use focused resource/distribution checks unless their actual logic impact crosses boundaries. `not_required` names the matched assessment/rule; it never means passed.

Current selectors are machine-readable in `.harness/project.yaml`. `candidate_tests` and `candidate_features` come from path mapping, and each `feature_commands` entry is explicitly marked `fallback_candidate`. Local and CI descriptors must identify the same capability even when their argv differs. Close recomputes the cumulative Git path set from the captured source commit and rejects a stale assessment. Resource sync, distribution validation, and `git diff --check` are required when their mapped surfaces change.

Selector and command `argv` are ordered tokens, not sets: the same path may appear after both `--project` and `--changed`. Set-like source prefixes, tests, triggers, and Full warnings reject duplicates.

Dynamic capability collection consults ignored `.harness/environment-exceptions.json` first. `skip_until_manual_reenable` must prove the original subprocess was not called and that the recorded fallback plus complete environment evidence was selected. File absence is a no-op; schema or entry errors are maintain findings.

Behavior-preserving test relocation uses baseline GREEN, a path-independent identity (`capability + suite/class + test + parameter`), ownership-confined structural change, equivalent GREEN, unchanged public behavior, and working local/CI selectors.

The five representative workflows run only through installed Skill CLI entrypoints: tiny default-authorized work, brownfield cleanup transaction, large-suite impact selection, low-risk amendment rebind, and parallel worktree creation/commit/integration. Internal function imports remain unit-test seams, not acceptance evidence.
