# Agentic Coding plugin

The local plugin packages the public catalog from the existing canonical/generated
Skill distribution, plus native capture and guarded-update scripts. It does not copy a project's
Feature Map, business criteria, UI tokens, credentials, or repository state.
The package identity and version are owned by `distribution/plugin.json`.

## Build

```powershell
python scripts/build_plugin.py --output .work/plugins/agentic-coding-0.1.17
```

The builder first runs the existing generated-resource check. It selects tracked
files from the public Skill catalog, rejects aliased/private sources, and refuses
to overwrite any existing destination. Use a new build directory for each update.
`plugin.json` and its older Codex compatibility overlay share one identity.
`package-files.json` records content hashes; it is not a signature or task verdict.
The installed capture CLI is `<plugin-root>/scripts/run_check.py`, with its shared
native unittest evidence reader beside it; workflow and
result tools remain in the installed `skills/agent-workflow/scripts/` directory.
The installed result CLI's `--execute` selects the package's capture script
automatically. Use `--run-check` only to override it or with a standalone Skill.
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

The builder never installs, publishes, changes global settings, or trusts hooks.
Local marketplace installation, fresh-host discovery, installed Agent task
behavior, and protected acceptance are separate checks. An editable local state
file is not a protected acceptance boundary. Ordinary installation and remote
publication remain separate authorized actions.

## Read-only request handoff

The package includes `hooks/hooks.json` and `hooks/workflow_context.py`, with an
explicit compatibility-manifest hook path. `UserPromptSubmit` resolves the Git
project from the supplied working directory and reuses its existing workflow
audit and configured task state. It delivers a bounded summary of outstanding
obligations and references. It does not interpret the prompt, read transcripts,
start a task, run project checks, write project files, or block lookup requests.
Projects without workflow configuration receive no additional context; invalid
configuration/state produces an unavailable warning. Full results remain in the
existing audit CLI. This handoff does not implement protected completion.

OpenAI documents plugin hooks and a separate trust review before command hooks
run ([plugin packaging](https://developers.openai.com/plugins/build/plugins),
[hook lifecycle](https://learn.chatgpt.com/docs/hooks)). The local Codex 0.160.0
probe isolated a compatibility defect: adding the portable `$schema` marker made
bundled hooks disappear, including with an explicit extension path. The package
omits that optional marker and retains its compatibility manifest. Actual 0.1.17
installed discovery now reports the prompt hook from its cache as enabled and
untrusted. Direct installed-handler execution is verified separately; automatic
host delivery and authenticated Agent behavior still require user hook review
and a logged-in isolated host. Installation does not grant hook trust. No ordinary
home or project trust setting was changed for this probe.

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

## Guarded local update and file recovery

The isolated 0.1.0 to 0.1.1 update showed that the native host deletes its old plugin
cache, including local changes. Use the distributed `scripts/update_plugin.py`
for subsequent local updates. Run it from the new package or repository, outside
the cache being replaced, and stop other plugin installers first:

```powershell
python scripts/update_plugin.py update --home <explicit-task-home> --marketplace <local-marketplace> --backup <new-backup-directory>
python scripts/update_plugin.py recover --backup <backup-directory> --output <new-recovery-directory>
```

The marketplace must contain one local `plugins/agentic-coding` entry. The guard
checks both packages, refuses changed/missing/extra installed files before native
installation, and binds the native command to that inspected local marketplace.
Interpreter bytecode beside a packaged Python source is permitted and preserved.
It retains and verifies every previous plugin file before invoking `codex plugin
add`, then checks its returned identity/path and installed bytes against the candidate. An identical installed
version returns UNCHANGED without another native call; different bytes under the
same version require a new version. Backups contain no whole-home, config or auth
copy. Aliased and private paths are refused. Concurrent guard calls use an OS lock;
direct native installers and concurrent editors do not participate in that lock.
Concurrent external cache changes remain unsupported; this guard cannot prevent
the host from deleting files written by another process during its native update.

If the native operation fails or the wrapper is interrupted after snapshot
creation, the backup remains. `recover` verifies it and exports the previous
version directories into a new destination without overwriting active or user
files. It does not automatically roll back the installed version or replay an
interrupted native command. If copying a backup/export itself is interrupted,
retain it and retry using a new destination; no completed snapshot is claimed.
Active-host rollback and authenticated Agent task resumption remain U7 work.
Inventory hashes detect ordinary drift, not maliciously rewritten inventories.

## Verification

```powershell
python -m unittest tests.distribution.test_plugin_package tests.distribution.test_plugin_update
```

This builds outside the checkout, runs the packaged capture CLI against a real
foreground command, starts the packaged workflow/result CLI entrypoints, checks
catalog parity, and proves that a second build preserves existing user files by
refusing overwrite. It does not prove model selection, task completion, hook
enforcement, or live provider behavior. Guard tests also cover changed/extra files,
destructive native failure, backup corruption, concurrency and byte-for-byte
recovery. The destructive command stand-in is fault injection, not native-host
crash evidence. Separate isolated native 0.1.2 to 0.1.3 and final 0.1.3 to 0.1.4
trials confirmed guarded update, user-note refusal before invocation, native
identity/path matching, duplicate no-op and recovery export. Path-overlap and
real Windows junction rejection are also exercised by the unit suite.
Full CI runs these tests with the existing
distribution suite and builds the package after resource checks.
