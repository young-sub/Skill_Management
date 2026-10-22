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

## Follow-up 0.1.85 — installed update, removal and actual use

The user authorized pushing to `main` and updating both hosts. `main` received the
0.1.84 commits (`ab01d9e`). Claude Code, the Orca Codex home and `~/.codex` were then
updated natively from the Git marketplace to 0.1.84. Each installed cache matched all
284 inventory hashes. Fifteen standalone global Skills in `~/.claude/skills` and
`~/.agents/skills` duplicated plugin Skills with older descriptions. They were copied to
`~/.agentic-coding-backup/global-skills-20261022` and removed. `write-a-skill` and
`synced` are not plugin Skills and remain.

The protected host verifier (`host_*`, `windows_job`, `install_host_verifier`, their
tests, five Features and the always-BLOCKED `accept` action) was removed. It was not
packaged or called, and the workflow/Harness regressions (211) passed afterward.
`finance-research` and `hwp-form-fill` stay in the plugin by user choice.

Actual use with installed 0.1.84, through headless Claude Code with a natural request
in an isolated clone of `yeondoo-link@d17f0c2` (raw: `.work/p2-real-20261022/`):

- Token guardrail request: the Agent ratcheted 96 legacy literals and caught new
  literals. It proved the rule with synthetic violations on the real stylesheet and
  wired it into `npm test`/`build` with no new dependency. It did not invoke any
  plugin Skill. An independent recheck confirmed 59/59 tests, a failing probe
  `#123456` with its line, a passing `var(--ink)`/`transparent` probe and a
  successful build.
- Guard probe: after an edit with "run nothing", the Stop hook blocked once. The
  Agent then stated that no execution was performed and why, and the next stop was
  allowed.

Repairs from these observations: the `agent-workflow` description now names
guardrails that stop recurrence. The guardrail criteria follow the project's
existing check convention instead of forbidding a project-local check script.
They also add the ratchet-baseline case for legacy literals.
