# Verification visibility, guardrails and cleanup — 0.1.84

Base: clean `f1467e8` (0.1.83) on `wp-20261020-luna-0178-results`. Order follows the
2026-10-22 review: P0 broken lookup, P1 human view and completion guard, P2 executable
guardrail criteria, P3 removal of stale material. Installed plugins, global Skills and
other repositories were not changed.

## P0 — lookup on legacy task state

`lookup --state .work/project-verification/state.json --summary`, the candidate the hook
advertises in this repository, raised `AttributeError` because that state predates the
`results` field. `test_summary_reads_legacy_state_without_result_links` reproduced it
(RED) and passes after the summarizer treats a null result map as empty. The real
repository lookup now returns 27 Features with zero commands executed.

The noisy prompt context seen in this repository (162 `UNDECIDED` cells, 27 obligations,
`enforcement: BLOCKED`) comes from the installed 0.1.78 hook. The current source hook
returns a compact `TASK_NOT_SELECTED` candidate list for the same prompt. Only an
authorized installed-plugin update removes that noise.

## P1 — human report and final-edit guard

`lookup/resume/audit --report` renders the complete read-only result as Markdown:
task acceptance, a Feature × business/architecture × FE/API/Domain table of declared
decisions, `NOT_REQUIRED` reasons, expected outcomes, current/historical check status
with capture/raw paths, feedback, remaining request actions and the project-remainder
count. It renders from the full result, so summary size omissions do not hide cells.
`test_report_renders_scope_matrix_outcomes_and_remainder_without_writes` checks the
cell values, the exclusion reason, the outcome, the remainder separation, rejection with
`--summary` and unchanged state bytes.

`hooks/completion_guard.py` is a packaged `Stop` hook. Within the current turn, it
blocks one stop when non-documentation files inside the project were edited after the
last command that is not pure inspection. `test_completion_guard` covers block,
execution-after-edit, inspection-only commands, documentation/outside/previous-turn
edits, `stop_hook_active`, opt-out and unreadable input. The package regression runs
the distributed command with `CLAUDE_PLUGIN_ROOT`. Parsing was also checked against
this session's actual Claude Code transcript. Limits: any executed command clears the
guard, whether or not it is the right check. Codex transcript compatibility was not
observed, and an unknown format allows the stop.

## P2 — executable guardrail criteria

`project-verification.md` gains *Executable guardrails before semantic review*.
Architecture boundaries and token/visual expectations are expressed in the project's
existing linter or browser runner, registered and linked as `kind: test` coverage, with
a synthetic-violation proof. The prevention table in `repair-and-reuse.md` adds
architecture-drift and Agent-behavior classes. Setup connects these where they can be
stated mechanically. This repository's own example is the static public-API boundary
check in `test_runtime_api`. This is guidance; it was not exercised on an external
product in this round.

## P3 — removal

The Feature Map keeps current rows and ownership notes (229 → 62 lines). Dated
release/stage paragraphs moved verbatim to
[the change history](archive/feature-map-history.md), with links rebased and checked.

Not removed, pending a user decision:

- Installed 0.1.78 plugin and the older standalone global Skills that duplicate
  `agentic-coding:*` with different descriptions. These need an authorized
  installed-resource update.
- The `host-*` protected-verifier Features and scripts. They were last changed on
  2026-10-06, `accept` is hard-wired to BLOCKED, and they are not in the plugin
  package. They are a deletion candidate, not deleted.
- `finance-research` and `hwp-form-fill` ship in the coding plugin catalog. Splitting
  them changes what users install.

## Verification

| Check | Result |
| --- | --- |
| `test_project_workflow`, `test_workflow_refinement` (with report test) | 127 run; the only failure was the untracked-file ownership audit, fixed by mapping |
| `test_repository_docs`, `test_workflow_hook`, `test_completion_guard`, `test_plugin_package`, `test_runtime_api` | 20 OK |
| Resource drift, distribution validation, `git diff --check` | passed |

## Release packaging

`scripts/build_plugin.py` built 0.1.84 (22 Skills, 285 files) into
`.work/packages/agentic-coding-0.1.84`. The prior tree is preserved at
`.work/packages/agentic-coding-0.1.83-preserved`. Replacing `plugins/agentic-coding`
added only `hooks/completion_guard.py` and removed nothing. The `plugin-package`
selector, `test_repository_docs` (24 OK), resource drift and distribution validation
passed. The packaged `--report` rendered this repository's real state. The packaged
guard allowed this session's actual transcript, where tests ran after the final code
edits; the blocking case is covered by fixtures. The Full suite, isolated-home
installs from both catalogs, native Codex delivery and any installed or global
update were not run.
