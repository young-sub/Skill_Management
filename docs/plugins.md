# Agentic Coding plugin

The local plugin packages the public catalog from the existing canonical/generated
Skill distribution, plus `scripts/run_check.py`. It does not copy a project's
Feature Map, business criteria, UI tokens, credentials, or repository state.
The package identity and version are owned by `distribution/plugin.json`.

## Build

```powershell
python scripts/build_plugin.py --output .work/plugins/agentic-coding-0.1.0
```

The builder first runs the existing generated-resource check. It selects tracked
files from the public Skill catalog, rejects aliased/private sources, and refuses
to overwrite any existing destination. Use a new build directory for each update.
`plugin.json` and its older Codex compatibility overlay share one identity.
`package-files.json` records content hashes; it is not a signature or task verdict.
The installed capture CLI is `<plugin-root>/scripts/run_check.py`; workflow and
result tools remain in the installed `skills/agent-workflow/scripts/` directory.
The repository-specific unittest adapter remains in this repository, not in the
common plugin. Project native runners and business assertions retain ownership
of product judgments.

## Capabilities and current boundary

`agent-workflow` routes natural-language tasks to implementation, verification and
lookup, feedback repair, UI standards, or maintenance. `setup-project-verification`
and `maintain-project-verification` connect and improve the project's own guides
and commands. Existing diagnosis, execution, review and UI Skills are reused.
See the [system direction](research/agent-coding-system-direction.md) and
[acceptance design](research/agent-workflow-completion-design.md) for the complete
required behavior; packaging alone does not satisfy those requirements.

The builder never installs, publishes, changes global settings, or enables hooks.
Local marketplace installation, fresh-host discovery, installed Agent task
behavior, and protected acceptance are separate checks. An editable local state
file is not a protected acceptance boundary. Ordinary installation and remote
publication remain separate authorized actions.

For an isolated Codex host, place the built package at
`<marketplace>/plugins/agentic-coding` and create
`<marketplace>/.agents/plugins/marketplace.json`:

```json
{"name":"agentic-coding-local","plugins":[{"name":"agentic-coding","source":{"source":"local","path":"./plugins/agentic-coding"}}]}
```

Set `CODEX_HOME` only for the test process to a new task-owned directory, then run:

```powershell
codex plugin marketplace add <marketplace> --json
codex plugin add agentic-coding@agentic-coding-local --json
```

Do not point this isolated procedure at the ordinary account home. Fresh-host
`skills/list` exposes names such as `agentic-coding:agent-workflow` with the
installed cache path and plugin ID. The isolated home establishes installation
and discovery without credentials; it does not inherit an authenticated model
session. Current measured outcomes are in the [implementation results](research/agent-workflow-implementation-results.md).

## Verification

```powershell
python -m unittest tests.distribution.test_plugin_package
```

This builds outside the checkout, runs the packaged capture CLI against a real
foreground command, starts the packaged workflow/result CLI entrypoints, checks
catalog parity, and proves that a second build preserves existing user files by
refusing overwrite. It does not prove model selection, task completion, hook
enforcement, or live provider behavior. Full CI runs this test with the existing
distribution suite and builds the package after resource checks.
