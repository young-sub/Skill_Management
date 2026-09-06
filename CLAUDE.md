# Agent Instructions

## Routing

- This repository distributes the Personal Agent Harness skills. Read `docs/index.md` for current implementation knowledge and `.harness/project.yaml` for path ownership, impact selection, commands, retention, and Git policy.
- Read the nearest nested `AGENTS.md` before editing a path. `back-up/` is read-only unless a task explicitly targets it.
- `authoring/resource-map.json` identifies canonical sources and generated `skills/` copies. Regenerate mapped resources; edit unmapped independent skills at their own source paths.
- Keep the latest global instructions in `authoring/global/AGENTS.md`. For every global revision, follow `docs/agents/global-guidance.md` and retain the previous bytes in `back-up/global-agents/`.

## Delivery

- Use the contract lifecycle only at the Work Packet threshold or when explicitly requested; small clear changes use direct development. See `docs/agents/workflow.md`.
- Select verification from actual logic impact and `.harness/project.yaml`. Full requires cross-cutting logic impact or an explicit request; configured triggers are candidate warnings. See `docs/testing.md`.
- Capture the current branch and commit as the base; never assume a branch name. Preserve the dirty baseline.
- Commit each verified complete functional unit with its required tests, docs, schemas, and generated resources. Keep coupled Items together; the execution policy defines commit boundaries.

## State And Risk

- Durable current technical truth is tracked under the configured documentation roots. Contracts, reviews, evidence, logs, transactions, and completed Goal state expire under `.work/`.
- Repository authoring does not authorize installed-Skill updates, provider changes, push, publish, remote/licensing changes, or protected-branch integration. Preserve explicit user authorization within its named scope.

## Commands

- Impacted Harness tests: `python -m unittest tests.harness.test_core_first_schema tests.harness.test_core_first_setup tests.harness.test_core_first_design_execution tests.harness.test_core_first_amendment tests.harness.test_core_first_close_lifecycle tests.harness.test_core_first_cutover tests.harness.test_core_first_forward_workflows tests.harness.test_core_first_cli_maintain tests.harness.test_core_first_installed_cli_e2e`
- Full: `python -m unittest discover -s tests -p "test_*.py"`
- Resource drift: `powershell -NoProfile -File scripts/sync-skill-resources.ps1 -Check`
- Distribution: `powershell -NoProfile -File scripts/validate-distribution.ps1`
- Formatting: `git diff --check`
