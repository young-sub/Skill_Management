# Agent Instructions

## Routing

- This repository distributes the Personal Agent Harness skills. Read `docs/index.md` for current implementation knowledge and `.harness/project.yaml` for path ownership, impact selection, commands, retention, and Git policy.
- Read the nearest nested `AGENTS.md` before editing a path. `back-up/` is read-only unless a task explicitly targets it.
- Canonical shared resources live under `authoring/`; generated public Skill resources live under `skills/`. Regenerate them with the configured resource-sync command instead of editing generated copies.

## Delivery

- Implement dependency-ready core Items before optional work. Use RED/GREEN for behavior changes; use baseline GREEN → structural change → equivalent GREEN for behavior-preserving document or test relocation.
- Select verification from `.harness/project.yaml`. Unresolved relevant impact blocks completion; Full is required only by a configured cumulative-impact trigger or explicit human request.
- Capture the current branch and commit as the base; never assume a branch name. Preserve the dirty baseline and commit only independently reviewable slices when repository policy or the human requests commits.

## State And Risk

- Durable current technical truth is tracked under the configured documentation roots. Contracts, reviews, evidence, logs, transactions, and completed Goal state expire under `.work/`.
- Require explicit approval for destructive actions, security/privacy or secret handling, irreversible migration, external cost, push, publish, or other high-risk state changes.
- Do not edit global provider configuration or installed Skills. Do not publish releases, rename remotes, change licensing, or auto-merge protected branches.

## Commands

- Impacted Harness tests: `python -m unittest tests.harness.test_core_first_schema tests.harness.test_core_first_setup tests.harness.test_core_first_design_execution tests.harness.test_core_first_close_lifecycle tests.harness.test_core_first_cutover tests.harness.test_core_first_forward_workflows tests.harness.test_core_first_cli_maintain tests.harness.test_core_first_installed_cli_e2e`
- Full: `python -m unittest discover -s tests -p "test_*.py"`
- Resource drift: `powershell -NoProfile -File scripts/sync-skill-resources.ps1 -Check`
- Distribution: `powershell -NoProfile -File scripts/validate-distribution.ps1`
- Formatting: `git diff --check`
