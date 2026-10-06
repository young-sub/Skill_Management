# Agentic Coding plugin

The local plugin packages the public catalog from the existing canonical/generated
Skill distribution, plus native capture and guarded-update scripts. It does not copy a project's
Feature Map, business criteria, UI tokens, credentials, or repository state.
The package identity and version are owned by `distribution/plugin.json`.

## Build

```powershell
python scripts/build_plugin.py --output .work/plugins/agentic-coding-0.1.20
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
The host-only [`host_result.py`](../scripts/host_result.py) publisher binds a
protected `policy.json`, explicit snapshot files and a unique run. The host calls
`begin(authority_root)` before execution, then `finish(authority_root, run_id,
observations, executions=executions)` with independently collected
`{id, exit, saved_hex}` facts. Each execution has `id`, `exit`, `timed_out`,
`descendants_killed` and `remaining`, collected by the host process controller.
Missing lifecycle evidence, timeout or forced descendant cleanup blocks acceptance
even when the saved bytes match. The
policy declares `task`, nonempty `snapshot` paths and nonempty expected `cases`
with those same three fields. `lookup(authority_root, run_id, task)` remeasures
policy, publisher and snapshot bytes. Missing/duplicate/extra cases are BLOCKED;
complete but different bytes/exits are REJECTED. Pending, malformed terminal,
wrong-task and stale records cannot become accepted by lookup or repeated finish.

This helper is installed by a trusted host alongside its protected policy and
snapshots, not copied into candidate-writable plugin resources. It does not create
ACLs, authenticate arbitrary supplied directories, execute checks, or prove child
process cleanup. Only host-collected observations may reach `finish`; a candidate
report is not that interface's trusted caller. Its ACCEPTED verdict covers the
declared snapshot and cases, not all workflow obligations. Ordinary plugin
`project_workflow.py accept` remains BLOCKED until the actual host adapter owns
those obligations and the complete execution lifecycle.

[`windows_job.py`](../scripts/windows_job.py) supplies Windows process lifetime
control around an existing native sandbox launcher. Its trusted isolated-Python
child waits before executing candidate code. The host assigns it to an unnamed
[Windows Job Object](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)
with kill-on-close and without breakaway, then opens the gate. The job handle stays
in the host. Normal completion measures remaining processes; lingering children
are terminated and reported, while timeout and controller death also terminate
the job. `run(launcher, command, cwd=..., timeout=..., env=...)` returns lifecycle
facts, not a product verdict. Pin the installed helper, interpreter and launcher;
keep the sandbox workspace root stable. This does not attest unrelated brokered
services, external effects or every possible sandbox escape.

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
installed discovery reported the prompt hook from its cache as enabled and
untrusted. Subsequent authorized login and hook review enabled the 0.1.25 native
repair/lookup/resume trial: automatic context delivery and installed diagnosis
were observed. A subsequent feedback turn repaired its default command and bound
actual execution to the local workflow; protected acceptance remains unsupported.
See the current implementation results. Installation itself does not
grant hook trust. No ordinary home or project trust setting was changed.

The read-only context includes separate summaries for up to eight existing active
Harness work records, using the same baseline reader as close. Project-wide status
does not replace those per-work obligations. Invalid work records remain visible
as BLOCKED, and omitted work counts are explicit. There is no trusted host
session-to-work binding: these are identified candidates, not an automatically
selected task. The hook neither reads the prompt to guess a work ID nor executes
the pending checks.

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
version with the same persistent source returns UNCHANGED without another native call; different bytes under the
same version require a new version. Backups contain no whole-home, config or auth
copy. Aliased and private paths are refused. Concurrent guard calls use an OS lock;
direct native installers and concurrent editors do not participate in that lock.
Concurrent external cache changes remain unsupported; this guard cannot prevent
the host from deleting files written by another process during its native update.

If the native operation fails or the wrapper is interrupted after snapshot
creation, the backup remains. `recover` verifies it and exports the previous
version directories into a new destination without overwriting active or user
files. Destinations inside or overlapping the snapshot's installation home are
refused before copying, including a missing active cache after failed installation.
It does not automatically roll back the installed version or replay an
interrupted native command. If copying a backup/export itself is interrupted,
retain it and retry using a new destination; no completed snapshot is claimed.
An intact active package can be rolled back using the same guarded native update:
place a verified historical package in a separate local marketplace with the
same marketplace name, then pass that marketplace and a new backup directory to
`update`. For an exported snapshot, select one version and copy only its inventoried
files plus `package-files.json`; interpreter caches remain preserved in the export
but are not candidate package members. Validate the candidate before installing.
The native host, rather than a direct cache copy, owns the active version change.
The guard persistently binds the marketplace to the inspected local source using
native marketplace remove/add, preserving unrelated home settings. Existing non-local
marketplace registrations are refused before any mutation. Temporary
command overrides were insufficient: a fresh native session restored the old
registered version. A same-version install with a stale binding returns REBOUND
after snapshot and registration repair, without reinstalling package files.
If removal succeeds but registration fails, the snapshot retains the former source;
retry the guard with the same candidate and a new backup directory. No completion
is claimed until the persistent binding and installed bytes are verified. Keep
the registered local marketplace available for later host starts.
The guard still refuses missing/corrupt active caches. In an isolated host with a
wholly absent version directory, native `codex plugin add` against the verified
local marketplace can recreate it; this was tested with all old bytes retained
outside the cache. Do not apply that operation over partial or user-modified
contents, because native installation can delete them. Preserve and inspect such
contents first. Repair of a partially damaged active cache remains unverified.
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
An isolated native 0.1.21 to exported 0.1.16 to 0.1.21 round trip additionally
confirmed active version discovery, real child-command verification through the
restored viewer, byte-exact snapshots and a duplicate UNCHANGED result. It does
not establish restoration of hook trust, credentials or an interrupted model task.
A separate native 0.1.31 to 0.1.32 trial terminated the guard process immediately
after the native marketplace registration completed, before plugin installation.
The OS lock was released on process exit; rerunning with the same candidate and a
new backup installed successfully, then returned UNCHANGED on repeat. Both the
old 246-file snapshot and unrelated home settings/files survived; export recovery
matched that snapshot and the resumed installed viewer read real retained evidence.
This establishes restart between native commands, not interruption inside a native
file-copy operation or repair of a partially corrupted cache.
Full CI runs these tests with the existing
distribution suite and builds the package after resource checks.
