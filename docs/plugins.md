# Agentic Coding plugin

The local plugin packages the public catalog from the existing canonical/generated
Skill distribution, plus native capture and guarded-update scripts. It does not copy a project's
Feature Map, business criteria, UI tokens, credentials, or repository state.
The package identity and version are owned by `distribution/plugin.json`.

## Build

```powershell
python scripts/build_plugin.py --output .work/packages/agentic-coding-0.1.45
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

Task delegation uses the existing workflow/result CLIs: register
`extensions.workflow.assertions`, prepare with `--pending-state` or `--work-id`,
execute into fresh paths, then inspect the bundle and read-only task audit.
Execution retains result links independently of unfinished semantic review.
The [task input contract](../authoring/references/result-viewer.md#task-scope-and-required-execution)
defines the scope matrix, selection/reuse and architecture evidence. Building
0.1.42 does not update an existing installation or establish host task acceptance.

Version 0.1.42 adds explicit request context on the same workflow entrypoint:
`start` creates small-task state, `connect` selects existing state/work ID,
`prepare` retains its selected plan pointer, and `execute` uses the existing
capture/viewer. `lookup` and task `resume` restore decisions/evidence without
execution; `execute --resume` is the distinct opt-in continuation. Retain the
returned `task_context` in process-scoped `AGENT_WORKFLOW_CONTEXT` or pass
`--context` explicitly. The hook reads that selector and never guesses among
tasks. Context validates project and immutable task identity; it neither assumes
a host session ID nor changes global settings. See the
[connection contract](../authoring/references/workflow-obligations.md#connect-the-current-request-once).

The project-owned [connected product example](../tests/distribution/fixtures/connected_product/docs/index.md)
drives two real browser screens through API/Domain/SQLite and restarts the service
before fresh read. It reuses the packaged entrypoint and existing capture/viewer,
with screenshots/trace retained after cleanup. Its explicit installed runtime
file references are measured during prepare, execute and lookup; native SKIP,
NOT_RUN, UNKNOWN and observation BLOCKED remain distinct from assertion ISSUES.
See [current actual-use results](research/agent-workflow-implementation-results.md#connected-actual-product-use-2026-10-07)
for task connection, feedback/UI repair, detector preservation and the bounded
host evidence. A project selects the installed dependency files that constrain
reuse; unlisted transitive runtime changes remain outside that declaration.

## Capabilities and current boundary

Version 0.1.45 adds investigation records on the existing task/context without
workflow setup, reason-specific feedback dispositions and partial-requirement
retirement proof. Lookup/resume stay read-only; evidence and permission boundaries
remain explicit. See the [investigation contract](../authoring/references/workflow-obligations.md#investigation-without-workflow-setup),
[feedback kinds](../authoring/references/repair-and-reuse.md#classify-the-feedback-before-choosing-a-repair)
and [retirement proof](../authoring/references/project-verification.md#detection-value-and-measured-maintenance).
Native installation and protected acceptance remain separate from local package use.

Version 0.1.44 fixes JSON terminal output on legacy console encodings. Unicode
values survive JSON parsing, while stdout/stderr use ASCII escapes so a successful
execution cannot fail merely when printing its result. Saved UTF-8 evidence and
state hashes are unchanged. The original 0.1.43 product trial remains separate
from the corrected package and its subsequent checks.

Version 0.1.43 adds ordinary/Harness follow-up review and unresolved-finding
continuity, request summaries and outcome references, bounded prompt previews,
and explicit rejection of invalid dot-segment inventory roots. Experimental
package trials, the clean frozen artifact and their support limits are recorded in the
[implementation results](research/agent-workflow-implementation-results.md).
This source version does not update any installed Skill or Plugin.

`agent-workflow` routes natural-language tasks to implementation, verification and
lookup, feedback repair, UI standards, or maintenance. `setup-project-verification`
and `maintain-project-verification` connect and improve the project's own guides
and commands. Existing diagnosis, execution, review and UI Skills are reused.
See the [system direction](research/agent-coding-system-direction.md) and
[acceptance design](research/agent-workflow-completion-design.md) for the complete
required behavior; packaging alone does not satisfy those requirements.

Version 0.1.40 connects project-declared full-stack scope to prepare/execute/lookup,
feedback repair evidence to subsequent work, shared UI ownership to consumer
obligations, and read-only check maintenance to measured native records and
detection-preserving consolidation. The CLI performs structural joins, state and
evidence checks; Agents retain diagnosis, architecture/design sufficiency and
semantic consolidation judgment. Read the [usage contract](../authoring/references/project-verification.md)
and [current implementation evidence](research/agent-workflow-implementation-results.md).
No automatic feedback collector, visual detector, universal parser or host-enforced
request registration is claimed. The local package does not update an installed
copy or change protected-host acceptance.

The builder never installs, publishes, changes global settings, or trusts hooks.
[`install_host_verifier.py`](../scripts/install_host_verifier.py) stages a reviewed
host bundle with `--bundle PATH --target NEW_PATH` below an **already provisioned
protected parent**. It freezes declared inputs as bytes, supplies canonical host
helpers instead of importing bundle helpers, refuses existing targets, probes the
native candidate's write/delete/create/rename and security-descriptor access, then
validates configuration and writes an installation manifest. Failed targets are
retained; nothing is overwritten or recursively cleaned up. This command does not
provision accounts/ACLs or authorize unreviewed policies/drivers.

Both installation and execution check for the native setup marker and sandbox
account file before invoking the native CLI. Only file presence is inspected;
credential contents are never read or copied. Missing setup returns BLOCKED
without invoking a setup dialog. Presence alone does not attest credential
validity; the native launcher still validates its own state. The missing-account
trial was subsequently repaired with the explicit native setup command running
from an elevated process against that same isolated home. Fresh installations
then passed real candidate-account boundary probes; see the current
[native results](research/agent-workflow-implementation-results.md).

For repeated authorized development trials, reuse the same authenticated isolated
home and trusted workspace. Set that home's top-level `approval_policy = "never"`
and `sandbox_mode = "workspace-write"`. For ordinary development that must avoid
administrator setup prompts, use the authorized `[windows] sandbox = "unelevated"`
mode. The elevated native host can request setup even with approval policy never
if its account artifacts disappear; that policy does not suppress Windows UAC.
The native task launcher also passes `--ask-for-approval never --sandbox workspace-write`
explicitly. These settings suppress per-command approval prompts, not sandbox
restrictions. Do not recreate the home, repeat account setup, or change the ordinary
installation for each task. Checks outside the authorized environment remain
BLOCKED; a new trust boundary is a separate operation, not a reason to repeat
setup for routine tests. The protected verifier still explicitly requires its
elevated account artifacts and boundary probe; ordinary unelevated execution
does not substitute for protected acceptance. Keep that scope BLOCKED if its
required account state is absent instead of silently weakening its boundary.

The protected-host [`host_verify.py`](../scripts/host_verify.py) entrypoint joins
execution, independent saved-byte readback and result publication. Install it with
`host_result.py`, `windows_job.py`, `policy.json`, `execution.json` and the frozen
driver/inputs in the host-owned directory, outside the candidate workspace.
Run that installed file with isolated Python and `run`; use
`lookup --run-id ID --task TASK` for a read-only lookup. There is no CLI switch for
an alternate policy, command, authority directory or submitted result.

`execution.json` declares absolute `workspace`, `home`, `codex` and `python`
paths, `codex_sha256`, `python_sha256`, a positive finite `timeout`, and `cases`.
Each case has `id`, `argv`, relative `saved` and `initial_hex`. The case IDs must
exactly cover the protected policy. Commands use the pinned Python with `-I` and
a protected driver; `{authority}` and `{runtime}` expand to protected inputs and
fresh per-case output directories. Referenced protected files must be in the
policy snapshot, including all files of a referenced directory. Bind the three
host modules and `execution.json` too. The host checks executable bytes before
and after execution, keeps the native sandbox root fixed, and reads saved bytes
only after job cleanup. Missing/aliased outputs or incomplete execution block
acceptance. The current adapter supports Python drivers; FE/BE tools can be
invoked by an explicitly reviewed driver with their dependencies bound by the
host policy. This is not automatic full-project obligation discovery.

`execution.json` may additionally bind a reviewed workflow snapshot:

```json
"workflow": {
  "root": "project",
  "state": "project/state.json",
  "checks": {"price": {"price-check": ["saved-price", "invalid-price"]}}
}
```

The snapshot directory contains `.harness/project.yaml`, candidate source and
references; every file, the baseline/review state, and canonical
`project_workflow.py` must be included in `policy.json`'s snapshot. The installer
supplies that evaluator from repository canonical source, never from bundle code.
The installation owner reviews the original baseline, semantic reviews and exact
Feature/check-to-case associations. An unrelated oracle does not validate a check
merely because its identifier is mapped. Relocation changes only the state root;
source/review bases remain intact.

The host recomputes obligations using frozen file hashes and its collected
case observations. It never runs candidate Git, imports candidate modules or
reads submitted verification bundles. Stale/missing reviews, unmapped sources,
unresolved findings and missing/rejected case evidence prevent acceptance even
when the other product cases pass. A complete native product mismatch remains REJECTED even
when workflow review is pending; missing review blocks an otherwise passing run.
Workflow findings remain in the protected raw record, and rejected runs retain
their execution lifecycle facts. Without `workflow`, acceptance covers only
the declared cases. Integration coverage and the actual five-case native
price-save trial both distinguish accepted normal behavior from missing review
and defective behavior. That bounded host trial does not establish whole-system
acceptance. The ordinary candidate-side `accept` stays BLOCKED.

For a reviewed task, optionally include canonical `host_handoff.py` and
`handoff.json` in the protected policy snapshot. The installer supplies the
handoff code from this repository, not from candidate bundle code. The host-owned
configuration has exactly `candidate` (an absolute candidate checkout path) and
`files` (candidate-relative path to protected snapshot-relative path):

```json
{"candidate":"C:/isolated/project","files":{"src/price.py":"project/src/price.py"}}
```

Invoke the installed `host_handoff.py --task TASK` with the pinned Python, or add
`--run-id ID` for read-only lookup. There is no authority/configuration/command
path argument. The task must match the protected policy, and mapped candidate
bytes must match the reviewed frozen snapshot both before and after execution.
A changed candidate blocks current handoff while preserving the original run.
The returned run ID and result come from the existing protected publisher;
no candidate success submission or duplicate result ledger is introduced.

The host reviewer owns mapping completeness and baseline/oracle/semantic review.
Unmapped files are outside this binding, so a partial map never establishes
whole-project acceptance. This entrypoint does not provision accounts, install
an unreviewed task, discover the originating chat, or approve semantic changes.
Its actual native execution still needs the existing sandbox boundary; current
missing-account preflight remains BLOCKED without requesting setup.

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
session-to-work discovery. With an explicit `AGENT_WORKFLOW_CONTEXT`, the hook
validates and exposes that task separately. Otherwise these remain candidates;
standard non-Harness task states are listed too. The hook neither reads the prompt
to guess a work ID nor executes pending checks.

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
python scripts/update_plugin.py update --home <explicit-task-home> --marketplace <same-candidate-marketplace> --backup <new-backup-directory> --resume-from <interrupted-backup-directory>
```

The marketplace must contain one local `plugins/agentic-coding` entry. The guard
can explicitly resume an interrupted update whose snapshot binds the same home,
marketplace identity and exact candidate bytes. Remaining cache files must match
either the original snapshot or the candidate; unknown/user-modified bytes are
refused. Missing files are allowed only on this explicit path. The attempt saves
the remaining files in a new backup before the native installer runs, and retains
the original backup. Completed or older snapshots without candidate hashes cannot
authorize this recovery. This is a serialized local recovery check, not protection
against a concurrent external installer or tampering with the backup itself.

For ordinary updates, the guard
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
Ordinary updates still refuse missing/corrupt active caches. In an isolated host with a
wholly absent version directory, native `codex plugin add` against the verified
local marketplace can recreate it; this was tested with all old bytes retained
outside the cache. Do not apply that operation over partial or user-modified
contents, because native installation can delete them. Preserve and inspect such
contents first. `--resume-from` supports missing files and surviving bytes tied
to its original update snapshot; truncated or unattributed bytes remain refused.
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
The 0.1.35 trial then constructed a partial-copy state after registration (one
candidate file retained, original cache moved intact to trial storage). Explicit
resume used the actual native installer to restore all 246 package files, kept
the original backup and partial file bytes, and returned UNCHANGED on repeat.
This is controlled interruption-state recovery, not an actual mid-copy crash.
Full CI runs these tests with the existing
distribution suite and builds the package after resource checks.
