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

Rerun with installed 0.1.85 (fresh clone, same request, hook events captured):
the UserPromptSubmit hook delivered the compact `TASK_NOT_SELECTED` context and the
Stop hook allowed completion because tests ran after the final edits. The Agent again
invoked no plugin Skill. This time it scanned all `src/**/*.css` and registered the
new tests in the project's required `verification-assertions.json`/Harness native
check. An independent recheck passed: 60/60 tests, a failing `#123456` probe, a
passing token probe and a successful build. Two runs cannot attribute the deeper
integration to the description change, and Skill discovery for this request remains
unobserved. The product outcome met the criteria both times by following the
project's own Harness guidance. Both clones stay under `.work/p2-real-20261022/`.
The original `yeondoo-link` is unchanged at `d17f0c2`.

## Open defect (recorded 2026-10-23, not yet fixed)

`lookup/resume/audit --report` writes through `sys.stdout` with the console encoding.
On Windows (cp949), redirecting it to a file produces non-UTF-8 Markdown, so Korean
outcome text is garbled in UTF-8 viewers. The failure was observed on the real
yeondoo-link task `9d3d9e0c…`. With `PYTHONIOENCODING=utf-8` the output is correct, and
JSON output is unaffected because it is ASCII-escaped. Fix: emit the report as UTF-8
(`sys.stdout.reconfigure(encoding='utf-8')` before writing). Add a test that decodes the
subprocess bytes as UTF-8 with Korean outcome text.

## Independent re-review on Labeler — 2026-10-23 (recorded, not yet fixed)

Raw: `.work/review-20261023/` (scenario transcripts, mutation logs, `SYNTHETIC-DEFECTS.txt`).
Product findings are recorded in each product's `docs/검증_공백_기록.md`.

Skill timing, measured with headless Claude Code and installed 0.1.85, using
natural prompts and no hints:

| Scenario | Expected | Observed | Cost |
| --- | --- | --- | --- |
| S1 one-line README edit | no Skill | no Skill, explained no Feature impact | $0.28 / 45 s |
| S4 explain PIN lock | zoom-out or direct | direct | $0.37 / 51 s |
| S7 "where were we, continue" | recall | `recall`, read-only | $0.85 / 150 s |
| S3 / L2 "show what is verified" | agent-workflow `--report` | no Skill, no CLI; hand-parsed raw (13 / 25 Bash) | $0.68 / $1.34 |
| L4 align modal UI | UI guide discovery | no Skill; found `ui-ux-upgrade.md`, browser-verified | $1.39 / 421 s |
| L1b customer complaint (planted C2) | diagnose / agent-workflow | no Skill; correct cause commit, RED→GREEN test; **bypass (settle order) unchecked** | $0.46 / 174 s |
| L3 "connect verification" | setup-project-verification | `setup-project-verification`; 5 Features, executable ledger-boundary rule, real local payment flow, found PortOne defect | $9.65 / 1885 s |

Plugin defects observed:

1. The hook reads stdin with the cp949 locale, so raw UTF-8 Korean prompts lose
   development detection and unconfigured projects get no guidance (L2 native `{}`).
2. `--report` file output is not UTF-8 (see the open defect above).
3. `maintain` crashes on a project without workflow configuration
   (`'NoneType' object is not subscriptable`).
4. An unconnected project reports `NOT_CONFIGURED` with exit 0 and "No Harness setup is
   required". A delegated task in Labeler therefore leaves no matrix, report or
   feedback record, and the user is not told.
5. Matrix decisions live only in task state. Project-level "not applicable" cannot be
   declared, so cells such as Skill_Management FE/API stay UNDECIDED forever.
6. Copied review text is accepted: yeondoo staff-access architecture:Domain reuses
   the consultation analysis.
7. The Stop guard counts any non-inspection command as exercising the edit and
   does not see Bash file writes.
8. Business value is hard-coded `NOT_ASSESSED_BY_CODE_CHECKS` and nothing asks the
   human. Both products had documented targets that were never linked.

Verification-strength evidence: Labeler detected 7/10 mutants; the full suite
missed frozen-lot reservation, spend order and expired grants. yeondoo-link
detected 3/8, and its browser suite passed purchase-confirm and scene-reset
mutants, so a PASS matrix overstated protection. A recurring date-fixed test
breaks Labeler `npm test` for every Agent.
