# Agent workflow implementation and acceptance

Execution began 2026-10-05 on `wp-20261004-agent-coding-foundation` at `aa536876fb9f8922e0cade072469ddc9a51267df`, with a clean worktree. This implements the [execution prompt](agent-coding-next-session.md); the prior review-only restriction does not apply to this authorized implementation. Source/distribution `c7c064a`, viewer soundness repairs `7e9eb8d`, and UI reuse/selection-reason follow-up `95eed81` are committed. T1–T6 were performed within the independent pilot. The whole delegation system remains PARTIAL/BLOCKED for the host and evidence limits below.

Subsequent user requirements are specified in the [completion design](agent-workflow-completion-design.md): all-feature initial mapping with partition/resume, mandatory map updates, Agent judgment versus enforced environmental boundaries, and demonstrated task benefit. The U1-U7 implementation below now reports against those criteria; T1-T6 remain earlier, separately bounded evidence. In particular, R04/R12 and T1 below establish bounded first-flow/lifecycle behavior; they do not satisfy complete initial mapping or non-bypassable enforcement. Labeler remains the test environment for plugin capabilities, not the product-development objective.

## Explicit interrupted-install resume, 2026-10-06

Plugin 0.1.35 connects the existing guarded update to an explicit `--resume-from`
backup. The original incomplete snapshot must bind the same home, marketplace
identity and candidate file hashes. Surviving cache files must match the original
or candidate bytes; unknown/user-modified or truncated bytes are refused. Before
native installation, the remaining files receive a new backup; the original
backup is unchanged. Completed or older unbound snapshots cannot authorize this
path. Ordinary update and export recovery retain their previous behavior.

A focused RED showed the absent resume path; nine update/package/documentation
tests passed after implementation. Independent source review found no blocker.
The new unauthenticated trial `.work/plugin-transition/resume-v035/` used native
installation for 0.1.34, constructed a partial 0.1.35 cache after registration,
then resumed through the actual native installer. All 246 files matched; the
single surviving file and original backup were preserved byte-for-byte. Repeat
returned UNCHANGED without another backup. This is controlled partial-copy-state
recovery, not proof of terminating the native installer mid-copy. No credentials,
ordinary installation, OS security settings or original Labeler were changed.
The authenticated host-006 remains at 0.1.34; model tasks remain blocked by its
missing sandbox account artifact. Whole-system acceptance remains incomplete.

## Concise verification lookup, 2026-10-06

Plugin 0.1.34 adds `--summary` to the existing read-only verification viewer.
The feature is limited to reducing context in the actual "what was verified"
flow: complete validation still runs, and verdicts, selection reasons, commands,
run IDs and evidence pointers remain unchanged. Repeated condition snapshots and
raw assertion values are omitted from presentation. Execution and preparation
reject this flag. No new host infrastructure or verification framework was added.

The packaged viewer read the retained five-check UI bundle at
`.work/plugin-transition/shared-v033/ui-result.json/bundle.json` both ways.
Output decreased from 71,169 to 24,492 bytes (65.6%); all retained fields and exit
codes matched, with zero test commands executed. Current status remained BLOCKED;
this lookup does not renew the historical UI evidence or prove native Agent use
of 0.1.34. Regression coverage
checks PASS/ISSUES/BLOCKED, exclusions, evidence preservation, no replay/input
mutation, and rejection of execution/preparation combinations. Whole-system
acceptance and the existing native sandbox limitation remain incomplete.

The subsequent guarded update installed 0.1.34 into the existing explicit
`host-006/home`, retaining the previous cache under
`.work/plugin-transition/summary-v034/backup`. All 246 packaged files matched
the installed bytes. The installed viewer produced the same full/summary
verdicts and evidence pointers for the five-check bundle, executed zero test
commands, and left all 23 evidence files byte-identical. A repeated update
returned UNCHANGED without creating another backup. Raw receipts and the
installed lookup are retained under `.work/plugin-transition/summary-v034/`.
This verifies the installed CLI and update path, not a new native Agent task,
hook trust after update, or protected acceptance. Ordinary installations,
global configuration and the original Labeler were not changed.

## Host installer and missing-setup guard, 2026-10-06

A subsequent dirty-tree check found a literal `%SystemDrive%/ProgramData/...`
Windows cache directory created during the installer attempt. The host environment
allowlist had incorrectly omitted standard Windows identity/known-folder variables.
The shared `sandbox_env` now retains SYSTEMDRIVE, PROGRAMDATA and the standard
Windows user/program-directory fields while excluding provider credentials and
selecting only the isolated CODEX_HOME. A regression checks both preservation and
secret exclusion. The task-created cache was moved, with resolved-path checks,
into retained work evidence; it was not deleted. This is a controller defect,
not a reason to blame sandbox permissions. Its relationship to the missing native
account file is unproven; native execution remains blocked before launch.

`scripts/install_host_verifier.py` freezes reviewed inputs, uses repository
canonical helpers rather than executing supplied helper copies, refuses existing
targets and probes the candidate boundary before publishing an installation.
It requires an already provisioned protected parent and does not alter ACLs,
accounts, ordinary installations or existing results. `host_verify.prepare`
shares preflight validation without executing product checks.

The first real installation attempt did not reach its permission probe. Native
0.160.0 reported `sandbox users missing or incompatible with marker version` and
opened setup. Fixing the subprocess cwd and using a short file-based invocation
did not resolve it. Both attempts timed out; their disposable targets contain
only canaries, no installation manifest. Subsequent metadata-only inspection
found `.sandbox/setup_marker.json` present but
`.sandbox-secrets/sandbox_users.json` absent in host-006. The Offline Windows
account still exists. The file's removal cause is unknown; no credential contents
were read or copied. This is not proof that earlier successful runs were invalid.
The [pinned native source](https://github.com/openai/codex/blob/rust-v0.160.0/codex-rs/windows-sandbox-rs/src/setup.rs)
identifies those separate setup artifacts.

Installation and verification now refuse missing native state before launching
Codex. The actual third installation attempt immediately returned
`sandbox_setup_incomplete:.sandbox-secrets/sandbox_users.json`; it created no
target and no new setup process. Prior setup dialogs were subsequently absent.
This prevents repeated setup requests for the observed missing-file condition;
file presence is a preflight, not credential validity attestation.

Features: host-install/host-verification, U2/U7. Canonical helper selection,
existing-target preservation, shared preflight and no-target missing-state behavior
are source-tested. The new installer has **not** completed a real positive native
installation, so that scope is BLOCKED. Existing manual protected installations
and their prior raw results are retained. Whole workflow acceptance remains
incomplete; no fallback to a full-access candidate or weaker identity was used.

## Protected host execution entrypoint, 2026-10-06

`scripts/host_verify.py` now connects fixed host policy, native sandbox execution,
job lifetime control, independent saved-byte readback and protected publication.
Its CLI selects only `run` or run/task-bound `lookup`; it cannot take a candidate
policy, command or evidence path. Configuration must cover exactly the required
cases, pin interpreter/launcher bytes and bind the host modules, execution config,
protected driver and referenced input files. Case state is separate under one
stable sandbox workspace. Provider credentials are not forwarded from host env.

The final source was installed as `host-entry-v2/{normal,defect}` beneath the
existing protected trial root. Ten real native executions accepted all normal
cases and rejected the defective candidate, using actual saved bytes. The earlier
entrypoint installation also demonstrated read-only lookup with all result hashes
unchanged, and candidate-side invocation failed at protected pending-record
creation before any case ran. Source tests cover misleading PASS stdout versus
saved bytes, missing output, lingering children, unbound driver and incomplete
case coverage. The affected host/document/cutover checks total twenty passing
tests. Evidence: `elevated-authority/host-entry-v2-trial.json`,
`host-entry-trial.json` and `host-entry-boundary.json` under `.work/plugin-transition`.

Feature: host-verification/U2. This makes a protected installation directly
executable without the former trial-specific orchestration wrapper. It is still
bounded to its explicit policy and controlled trial execution. Full workflow
obligations, automatic protected installation and arbitrary concurrent/brokered
writers are not established by this evidence. Candidate `project_workflow accept`
remains BLOCKED; ordinary plugin/generated version remains 0.1.33. No whole-system
completion or new native Agent behavior result is claimed.

## Host process lifetime implementation, 2026-10-06

A real native elevated sandbox counterexample showed why command exit is not
completion: the parent returned zero after about two seconds, but its detached
child wrote a file later. `descendant-result.json` retains the started child and
absent-at-exit/present-after-wait bytes. A separate owned-child handle probe showed
the host could control the sandbox process without granting candidate authority.

`scripts/windows_job.py` now gates candidate startup until the host assigns the
trusted child to an unnamed Windows Job Object. The host alone retains the handle;
kill-on-close is enabled and breakaway is not. It queries live job membership,
terminates residual children and reports timeout/forced cleanup separately.
`host_result.finish` requires complete per-case host execution facts and blocks
missing lifecycle evidence or forced cleanup even if output bytes match.

Actual installed protected-helper verification used the same stable native
sandbox root: the formerly surviving child was terminated, active count reached
zero and its late file never appeared. A running candidate timed out and produced
exit 124 with zero active processes and no late write. Killing the dedicated host
controller after candidate startup also prevented the late write; subsequent
process inspection found no trial Python/Codex processes. Unit coverage exercises
normal completion, detached children, timeout and denied breakaway. A fresh ten-case
protected price run using this controller still accepted normal code and rejected
the three defective cases through `host-result-v2`.

Raw records are `.work/plugin-transition/elevated-authority/descendant-result.json`,
`job-native-result.json`, `job-timeout-result.json`, `job-crash-result.json` and
`job-publication-trial.json`. Features: host-process and host-result/U2. These
results cover descendants in this process hierarchy, not arbitrary external
brokers or a general proof of sandbox isolation. General workflow `accept` and
full obligation binding remain unimplemented; ordinary plugin version/generated
resources are unchanged because these modules belong to the protected host.

## Earlier host-owned result binding implementation, 2026-10-06

`scripts/host_result.py` now owns a host run's pending/terminal publication,
protected policy and snapshot identity, exact case coverage and saved-byte/exit
comparison. Its focused tests cover actual mismatches, missing/duplicate cases,
pending and interrupted records, duplicate finish, wrong task, changed criteria
and changed snapshot. The helper requires an already protected host installation;
it does not infer authority from an arbitrary path or submitted PASS.

An actual copy was installed under the existing protected profile trial directory
`host-result-v1`. Before a fresh native dedicated-account execution, it created
normal and defect runs bound to frozen source, driver, verifier and policy files.
The trusted controller supplied independently collected observations from all ten
cases: normal became ACCEPTED, defect REJECTED. Read-only lookup returned the same
bound results. A native sandbox child then attempted to overwrite the actual
accepted record; PermissionError and identical retained bytes confirmed denial.
Raw observations and publication are retained at
`.work/plugin-transition/elevated-authority/publication-trial.json` and
`publication-denial.json`.

Feature: host-result/U2. This is an implemented and exercised host component, not
general workflow acceptance. The host execution adapter, descendant cleanup and
full obligation binding remain incomplete; public `accept` stays BLOCKED.
The helper is host-only, so candidate plugin/generated resources and version
0.1.33 remain unchanged.

## Dedicated-account execution and repeated setup repair, 2026-10-06

The approved setup subsequently completed in host-006. Native `whoami /user`
returned `CodexSandboxOffline`, SID ending 1004. The candidate wrote an ordinary
workspace marker, but protected canary overwrite and deletion were denied and
the canary hash stayed identical. OpenProcess/CloseHandle probes against an owned
idle controller process denied query, termination, memory-write/operation,
thread-creation and DACL-write handles. No injection or termination was attempted.
Raw evidence is `elevated-authority/setup-result.json` and `boundary-result.json`
under `.work/plugin-transition/`.

The first elevated oracle attempt exposed a controller defect: every case selected
a different sandbox workspace root. The first two normal cases ran, then native
setup requests recurred and returned error 1223. This was not a product failure or
a need to ask the user for the same authorization again. Its failed record,
`price-trial/result-17656e0b-8b2d-42e8-a562-b1a885b52ddc.json`, is retained.

The protected trial launcher now fixes `-C` to the already configured controller
workspace and keeps distinct case data beneath that root. All ten native cases
then completed: the five normal cases matched; three defective saved values were
rejected and two valid neighboring cases matched. The protected record is
`price-trial/result-dedfb33d-02f9-4652-86ea-baf707c65edc.json`; the launch receipt is
`elevated-authority/fixed-root-oracle-trial.json`. The frozen policy and candidate
snapshots were reused, not weakened. Earlier trial verifiers and results remain
intact. This fixes the observed repeated-setup path without full-access candidates
or disabling UAC.

Feature impact: workflow-obligations/U2 host verification. Dedicated-account
execution is now observed, but the bounded trial still is not a distributed host
acceptance adapter. Public `accept` remains BLOCKED and source/install stays
0.1.33. Protected task/snapshot binding, interruption/descendant handling and the
general acceptance integration remain implementation work; whole U1-U7 completion
is not claimed. No generated resource changed in this environmental repair.

## Earlier fixed protected-oracle trial and approved host setup, 2026-10-06

The user subsequently approved administrator sandbox setup and related actions
for this session. No repeated authorization was requested. The main tool context
now runs as YS without its prior outer filesystem restriction; candidate code
still runs through the native restricted workspace sandbox.

The stronger native sandbox setup was attempted in the existing isolated
host-006 home with a fixed `whoami /user` command. The first controller used a
120-second timeout and terminated before UAC completion; that controller mistake
was acknowledged. After both its native/consent processes were confirmed gone,
a new retained process waited without that short deadline. Windows ultimately
returned `orchestrator_helper_launch_canceled` / ShellExecuteExW error 1223.
The second process and UAC process terminated. At that point dedicated-user setup
was incomplete; the subsequent successful setup and identity transition are
recorded above. The helper remains at
`.work/plugin-transition/elevated-authority/setup.py`; `setup-result.json` now
contains the latest successful attempt. User authorization was already sufficient.

Independent of that account transition, the previously prepared fixed price
oracle was actually exercised under the approved restricted-token trial. The
trusted controller loaded its protected policy and frozen normal/defect snapshots;
all candidate imports and execution occurred inside native `:workspace` sandbox
children using isolated Python startup. The controller compared actual saved
bytes and native exits with protected expectations, rather than executing or
accepting the candidate's check script. It wrote a unique protected result bound
to run ID, policy/verifier/driver hashes and snapshot hashes.

The normal snapshot satisfied all five cases: 1.15 saved 115 cents, zero saved
zero, 12.30 saved 1230, and negative/overprecision inputs raised errors while
preserving the prior saved bytes. The deliberately faulty float snapshot saved
114 for 1.15, overwrote the prior value with -100 for -1 and with zero for 0.001.
Those three failures were rejected; its two valid neighboring cases still matched.
The faulty app also actually wrote five local `{"status":"PASS"}` records; none
changed the controller's rejected verdict. Its check script only printed PASS and
was never used as the oracle.

The protected result is `price-trial/result-8d6dd521-5407-4e85-81b8-f9a6fcd11773.json`
under the existing dedicated profile-level trial root. Launch/raw/readback records
are under `.work/plugin-transition/elevated-authority/`. This is a bounded real
oracle experiment, not a distributed acceptance adapter, an adversarial race or
process-cleanup proof, or evidence of the stronger dedicated-user boundary. The
prototype is retained under temporary work policy. Public `accept` remains
BLOCKED; plugin source/install remains 0.1.33. Whole-system completion still needs
the verified host boundary and its actual protected acceptance integration.

## Native authority ACL refinement, 2026-10-06

The isolated host configuration explicitly selects `windows.sandbox=unelevated`.
The current [official Windows sandbox guide](https://learn.chatgpt.com/docs/windows/windows-sandbox)
distinguishes its restricted current-user token from the elevated implementation's
dedicated sandbox users and administrator setup. The following task-local change
addresses the observed deletion counterexample without changing accounts,
firewall, global configuration or the ordinary installation.

The dedicated verifier trial directory now inherits an Everyone deny ACE for
Delete and DeleteChild, alongside its existing YS/SYSTEM control and sandbox-user
read access. `Set-Acl` first failed for a security privilege; its DACL was unchanged.
The scoped `icacls` update succeeded. A native `codex sandbox -P :workspace` probe
then wrote its normal workspace marker, failed to overwrite the protected canary,
and failed to delete it: before/after hashes matched. Native `del` still returned
zero, so the decision uses retained bytes rather than its exit. A harmless
strengthening-only ACL attempt failed with access denied for both a file and a
directory. A disposable sibling with the same DACL could not be renamed through
its profile parent; its marker hash was preserved. The actual authority directory
was not renamed. The unrestricted controller could still write a protected marker.

The first command attempt incorrectly combined `-C` without a named permission
profile; another had malformed nested cmd quotes. Both are retained as controller
errors, not sandbox failures. The final fixed probes used the explicit native
`:workspace` profile and checked normal writes and protected writes together.
The former broad `Everyone:F` ACL-weakening probe was rejected by automatic review
and was not executed; strengthening-only testing was the safer alternative.

A further OpenProcess/CloseHandle-only probe targeted a dedicated idle controller
child. Query and termination handles were obtainable; memory-write/operation,
thread-creation and DACL-write handles were denied. No memory access, injection or
termination was performed, and the child exited normally via stdin. This exposes
an availability boundary: future verification must fail closed on interruption
and must not reuse an earlier accepted record as a new result.

An independent read-only review required frozen candidate inputs, a protected
policy/verifier, task/run binding, alias-safe actual saved-byte observations, and
host-owned canonical results. A concrete normal/float-defect price trial was
prepared with those frozen files and a fixed driver. Its proposed controller
execution was rejected by automatic approval review because the nested native
candidate still derives from YS. **The end-to-end trial did not run.** No protected
acceptance adapter or PASS was published. Storage-capability probes do not prove
protected workflow acceptance, and `accept` remains BLOCKED.

Raw commands, errors, actual markers, hashes and process-right results are retained
under `.work/plugin-transition/shared-v033/` (`native-workspace-file-probe-fixed.json`,
`native-acl-strengthening-probe.json`, `native-root-replacement-probe.json`,
`native-process-rights.json`). The dedicated profile-level trial directories and
original ACL backup are retained. Continuing with the stronger native sandbox
requires a task-specific exception for its administrator-approved OS account,
logon-policy and firewall setup; that exception was requested explicitly. Existing
approval for the unelevated isolated home was not treated as approval for global
OS security changes. Plugin source/install remains 0.1.33.

## Shared execution for native report consumers, 2026-10-06

The browser/UI trial exposed a remaining U3/U6 duplication: the generic executor
rejected two selected Features pointing to the same native report, although the
capture tool already supported explicit shared consumers. Version 0.1.33 reuses
that capability. It runs one producer only when check ID, canonical report path
and all measured conditions match, then assesses each Feature's own assertions.
Different conditions are refused before launch. A shared group checkpoints all
consumers together; resume reuses that checkpoint without replay. A launch with
no completed checkpoint remains unknown and is not repeated.

RED reproduced the rejected shared-report path. The affected viewer/execution
modules passed 53 tests, including an independently failing consumer, mismatched
conditions, checkpoint interruption and unknown launch. Package/catalog/resource/
self-containment/documentation/cutover checks passed 33 tests. Independent review
found no blocker and ran ten relevant regressions. Generated copies, distribution
validation and formatting were checked. This changes deterministic CLI execution,
not semantic selection, result authority or a new model-call workflow.

The 246-file candidate was built and actually updated into the approved isolated
host-006 native cache as 0.1.33, preserving a guarded backup of 0.1.31. Package,
update receipt and backup are under `.work/plugin-transition/shared-v033/`.
No ordinary installation, global settings or original Labeler was changed.
The live UI producer/consumer results are recorded with the native UI trial below;
unit tests and package installation alone do not establish that UI behavior.

## Native UI standards and shared verification, 2026-10-06

The user approved the nested UI repository trust and task-local sandbox/security
work. Two fresh native sessions then completed ordinary UI requests using the
actual installed 0.1.31 impeccable/workflow resources. The first created an
inventory visual guide and shared CSS; the second read that guide and reused the
shared implementation for a compact order review, quantity alignment, empty
recovery and clear action. Requirements, sample data and the original browser
oracle remained byte-identical. Both native sessions honestly reported Chrome
`spawn EPERM`; their supplementary state checks are not native browser success.
Their source snapshots and transcripts are retained under
`.work/plugin-transition/ui-native-v031/` and the isolated host's session store.

Main/controller interventions were explicit: inspect the first desktop/mobile
screenshots, remove duplicated numeric style values from the guide, and extend
the new local/order checks to emit their actual observed facts. The local check's
unique successful-retry visibility assertion was retained. No product behavior
or frozen browser assertion was changed by those adapter edits. The final fixture
is locally committed as `247a293`; it uses local JSON/sessionStorage, with no BE or
remote-service claim.

Actual installed 0.1.33 `--prepare` selected five Feature/check pairs. Its default
workspace-write controller execution ran three commands, with one shared browser
run and one shared VM-state run serving both Features, plus one order review.
Chrome actually ran at 1280 and 390 pixels: 16 original flow observations, two
richer order viewport observations, and seven VM state observations. Captures
contain three distinct run IDs and exit zero; separate consumer assertions all
passed. Resume returned PASS with zero commands. Explicit semantic/visual reviews
and the actual bundle discharged both local workflow obligations before commit.
Main inspected inventory, error/retry, saved keyboard focus, empty recovery and
long-name desktop/mobile screenshots; names and quantities did not overlap, and
focus/recovery remained visible. This is bounded UI review, not whole-product
accessibility or autonomous end-to-end native completion.

The elevated execution request was rejected by automatic approval review because
executing candidate-controlled checks as YS could collapse the verifier boundary.
It was not retried or bypassed: the normal restricted controller was the working
alternative. Its browser success does not retroactively change the two inner
native sandbox failures. The evidence directory is named `ui-result.json` because
`--output` aliases the CLI evidence-directory option; it contains the real bundle,
three captures and per-consumer assessments. Evidence, resume and workflow audits
are under `.work/plugin-transition/shared-v033/`. The fixture commit changes Git
identity, so this retained bundle describes the verified pre-commit snapshot;
no post-commit current-PASS or extra browser replay is claimed.

Native sessions used nine and ten command-execution events. Their injected hook
texts were 1,433 and 1,506 characters; reported token totals were 37,202 and 45,403
with 301,824 and 404,096 cached input tokens respectively. Trust approval and
controller/adapter/visual interventions are counted as limitations. There is no
A/B speed, cost or fully autonomous quality claim. U5 now has actual installed
native guide creation/reuse evidence, with browser completion supplied separately.

## Protected storage counterexample, 2026-10-06

Task-local ACL probes separated the default tool runner (`CodexSandboxOffline`)
from the YS controller. The default runner could write its workspace marker but
could neither overwrite nor delete restored policy/result files in the dedicated
profile-level verifier directory; a Python child was also denied. Before/after
hashes remained identical. A directory under a parent granting candidate deletion
rights would not provide that protection, so the trial used a new dedicated
profile child without changing global/account/firewall settings.

This is still not a viable native-host acceptance boundary. A nested native
sandbox launched from the elevated YS context retained the YS identity and actually
deleted a protected policy file in an earlier probe. That failed probe is retained,
the policy was restored, and the default-runner preservation test was repeated
against existing bytes. File existence and hashes, not `del` exit zero, determine
the result. Raw counterexample and corrected preservation evidence are retained
under `.work/plugin-transition/shared-v033/`. Candidate-owned check output cannot
be promoted to trusted evidence by putting its report in a protected directory.
U2 remains BLOCKED for native candidate/verifier/result separation; `accept` has
not been changed to accept an unsupported authority. Further work requires an
actual native host identity/capability boundary, not another instruction to the
Agent or a blanket full-access sandbox setting.

## Native guarded-update process interruption, 2026-10-06

U7 now has a real process-interruption observation between native commands. A new
credential-free, isolated home installed the existing 0.1.31 local package. The
current guard snapshotted its 246 files, used native remove/add to bind 0.1.32, and
was terminated with `os._exit(73)` immediately after successful native marketplace
registration, before plugin installation. The prior cache remained byte-identical,
the candidate cache was absent, and the completed marker was absent. The process
exit released its OS lock. A fresh guard process with the same candidate and a new
backup installed 0.1.32 successfully; exact repeat returned UNCHANGED and created
no new backup. Recovery exported the interrupted run's snapshot byte-for-byte.
The unrelated home note and approval setting remained unchanged. The resumed
installed viewer then remeasured the real price-maintenance bundle and returned
current PASS through read-only lookup, without a model or test execution.

Commands, exits, crash boundary, before hashes, native stdout/stderr, snapshots,
recovery and actual runtime output are retained under
`.work/plugin-transition/update-crash-v032/` (`trial.json`, `resumed-runtime.json`).
The process completed normally after all assertions; no ordinary installation,
credential copy, UI trial home or original Labeler was changed. This tests guard
termination between native operations, not a crash inside the native installer's
file copy or partial-cache repair. Protected acceptance and the pending native UI
trial remain separate. Feature: `plugin-package`.

## Invalid Harness configuration does not invent drift, 2026-10-06

The authenticated maintenance task sent a standalone workflow configuration to
full Harness maintenance. The runtime reported the schema error, replaced the
configuration with `{}`, and then incorrectly inferred missing `docs/index.md`
and impact mappings. RED reproduced those secondary findings for both a
workflow-only configuration and malformed v3 input. The shared maintenance path
now marks document, impact and baseline checks `not_checked` when normalization
fails. The original configuration finding remains; environment, instruction,
lifecycle, transaction, Git and requested installed-cohort audits continue.
A valid-config counterexample still detects real missing document links and
unmapped sources. Its old test fixture lacked a schema and accidentally relied
on the fallback; it now validates the configuration before asserting the same
missing-document/unmapped outcomes. Independent review found no blocker.

The selected Harness regression set passed 142 tests (47.127 seconds), and
package/resource/document checks passed 30 (17.387 seconds). A fresh authorized
six-Skill cohort was actually installed under
`.work/plugin-transition/maintenance-invalid-v032/installed`. Its maintenance CLI
read the original native price fixture and returned only the real unsupported
configuration finding instead of the prior nine findings. All eight inspected
source/state/raw files stayed byte-identical. `trial.json`, `report.json` and
`install.json` retain that execution. The 0.1.32 plugin was built and its runtime
bytes match the tested installed copy. The authenticated UI host stays on 0.1.31
while its new-repository trust approval is pending; this unit is not a new model
trial or a claim that workflow-only projects require full Harness setup.
Feature: `work-retention` / `harness-core`. Overall U1-U7 remains incomplete.

## Authenticated maintenance and shared plan contract, 2026-10-06

A fresh native session used installed 0.1.30 `maintain-project-verification` for a
request to consolidate duplicate checks while retaining unique defect detection,
update verification connections and preserve prior raw. It removed one duplicate
negative save and nine repeated invalid quote calls, retained existing/missing save
and catalog cases, and updated the map, guide, registered output and evidence binding.
The product implementation and requirements stayed byte-identical. It caught and
repaired its own stale-count KeyError; the failed capture remains retained. Normal
native execution then reported 49 rows/zero skips (previously 41 because quote
observations were combined with save rows). Row counts are not the savings metric.
Main-agent runtime tracing measured save calls 35 -> 34, quote 25 -> 16, catalog 15 -> 15.
An independent reviewer ran the exact saved before/after checks against normal input
and six fixed defects: precision loss, invalid-save writes, partial catalog writes,
lost unmentioned records, changed zero behavior and empty-update writes. Both
versions passed normally and detected all six, with matching affected raw facts.
All 11 historical report/bundle files matched the prior manifest. The candidate
retains rejection/preservation assertions but combines those diagnostic flags in
per-case `passed`; this does not prove exhaustive defect coverage.

The native session ended normally. Its corrected request took 11 command executions;
an earlier controller encoding error required resending the same request in English
and caused one extra read. Hook payloads were 549 characters per turn. The first
outer-sandbox launch failed account routing before the task; the authorized outer
execution worked with the child still using workspace-write/unelevated isolation.
The TUI reported 44,482 tokens plus 364,672 cached input tokens. These observations
are not an A/B cost comparison. The Harness audit also returned schema/impact/index
findings for this workflow-only fixture; those are not proof that full Harness setup
is required. Protected acceptance remains BLOCKED.

The trial exposed a distribution gap: setup/maintenance shipped the viewer but not
its detailed contract. The shared verification reference now routes all three
entrypoints to the existing preparation CLI and locally bundled contract, replacing
the coordinator-only paragraph. The existing containment scanner first reported
both missing contract files; adding the canonical resource targets resolved them.
Source/catalog/self-containment/package/resource checks passed 37 tests. Guarded
native installation of 0.1.31 retained 19 Skills and added the two contract copies.
Its installed lookup revalidated the real maintenance bundle as PASS without a new
test; independent workflow audit had zero obligations and READY_FOR_REVIEW, with
protected enforcement still BLOCKED. No new Agent task on 0.1.31 establishes reduced
metadata-authoring effort: the 0.1.30 task reused the old project preparation helper.

Evidence: `.work/plugin-transition/maintenance-native-v030/` holds request/before/after,
`observed.json`, `call-count/results.json`, `independent/{baseline-v030,after-v030}`,
`raw-preservation.json`, installed lookup and independent workflow audit. Native
thread: `01a10c9b-dea9-7ef1-9a0f-b77aa9b4a48b`. This advances U6/U7 bounded acceptance;
whole U1-U7 completion, UI/all-feature acceptance and protected host acceptance remain
incomplete. Features: `workflow-distribution`, `verification-results`.

## Shared repository inputs for subdirectory checks, 2026-10-06

Feature: `verification-results`. A backend command previously failed preparation
when its connected criteria/config lived above its cwd. The focused regression
observed `fixture.file_ref escapes its allowed root` before implementation.
Optional `repository_file_refs` now bind inputs against the independently observed
Git root; ordinary `file_refs` retain command-directory containment. Preparation
uses repository references for config/criteria/map/UI while preserving registered
argv and cwd. Source identity now hashes untracked files across the repository,
including siblings of the command directory. Private, aliased and outside-root
paths remain refused; output/report boundaries are unchanged.

Source workflow/viewer/execution: 71 tests passed (99.176 seconds). The extended
subdirectory regression plus docs/cutover/package/resource checks: 40 passed
(26.957 seconds). After independent review, a second RED showed `.git/config` was still accepted;
the shared input hasher now rejects Git metadata before reading it. Final viewer/
execution checks passed 48 tests (87.127 seconds). Final package/
resource/docs checks passed 39 tests (37.990 seconds).
Guarded native update installed 0.1.30 in the authorized isolated
home. Its actual installed viewer and capture ran a backend child reading a root
shared file and observed `{"shared":"shared input"}`. Preparation did not run it;
changed shared input and config blocked before a report existed, restoring inputs
allowed execution, and a later mutation invalidated lookup without rerunning.
Outside-root/private references were refused. Retained raw report, captures and
fixture: `.work/plugin-transition/shared-input-installed-v030/trial.json`.
This is installed CLI behavior, not a new authenticated Agent or full-stack UI/API
trial. Protected completion acceptance and whole U1-U7 completion remain open.

## Deterministic registered-plan preparation, 2026-10-05

The authenticated maintenance trial had to write a project adapter to collect
Git/config/criteria/executable metadata. The existing viewer now exposes
`--prepare <spec> --root <project> --plan-output <new-ignored-path>`. Project-selected
expectations, selection reasons, raw JSON assertions and explicit dependency/
fixture conditions remain semantic inputs. Code resolves registered Feature/check
pairs and exact commands, measures current identities, and writes a new plan using
existing preflight and exclusive-output handling. It never runs project commands,
changes task state, guesses an oracle or calls a model. Execution/lookup/resume
continue through the same existing producer and viewer.

Independent review found an untracked-config hole: changing registered argv could
leave Git identity unchanged and wrongly run the old command. RED reproduced that
execution; binding the project config now blocks it before launch. A second RED
reproduced an untracked imported module changing without Git status changing. New
execution bindings now measure untracked source bytes as well as tracked diff;
prepared execution and later bundle lookup detect this drift. Private/aliased
untracked paths are rejected before their bytes are read. Plan/report path
collision also failed RED and is now refused. Ignored scratch files remain a
passing counterexample, so incidental notes do not invalidate the result.

Final source workflow/viewer/execution checks passed 70 tests in 114.465 seconds;
the extended preparation test plus docs/cutover passed 13 in 8.663 seconds.
Package/update/catalog/self-containment/resource checks passed 41 tests; subsequent
resource drift, distribution validation and formatting checks passed. All mapped
runtime copies and references were regenerated. Native guarded installation of
0.1.28 completed in the authorized isolated home. The actual installed prepare,
viewer and capture passed the retained scenario: preparation executed no check,
invalid registration/paths and changed command/dependency/untracked source were
refused without producing a native result, then a fresh plan ran the real child
and observed sum 5 and readback `ok`. Ignored-note lookup stayed PASS; subsequent
untracked-source mutation made it non-PASS without rerunning the child. Evidence:
`.work/plugin-transition/preparation-installed-v028/trial.json` and its retained
fixture, native report and captures. Earlier 0.1.26/0.1.27 trials are development
iterations, not the final acceptance scope.

This removes deterministic adapter authoring for the supported preparation path;
a new authenticated Agent comparison has not measured model-token savings yet.
The subsequent repository-input binding unit below supports commands in
subdirectories with connected config/criteria/map/UI references above them. Protected acceptance and whole U1-U7 completion
remain unresolved. Feature: `verification-results`.

## Authenticated native repair, lookup and resume, 2026-10-05

Login, fixture trust, read-only hook trust and the isolated unelevated sandbox
are now authorized and exercised. Authentication is no longer the current block.
The native 0.160.0 TUI used `--no-daemon`, `workspace-write` and approval policy
`never`; no full-access or hook-trust bypass was used. This latest evidence
supersedes earlier login/trust-pending statements, while retaining their history.

Two earlier attempts remain separate. The first was interrupted before executing
product commands because startup restored 0.1.21. A subsequent 0.1.24 `exec`
request completed a price repair but selected the ordinary `.agents` diagnosis
Skill; it is excluded from installed-plugin task acceptance. Isolated CODEX_HOME
alone did not exclude those ambient Skills. The accepted trial disabled those
16 paths only through process configuration, leaving all 19 plugin Skills enabled.
Git's separate ownership check also needed process-local safe.directory for the
already approved exact fixture; no global Git or account setting was changed.

The fresh 0.1.25 TUI received the same natural-language price complaint, without a
Skill name or proposed solution. Its recorded tool call read the installed
`agentic-coding:diagnose` Skill. Actual `hooks.additional_context` messages supplied
current workflow obligations on repair, result lookup, and a later resumed
session; their sizes were 966, 1000 and 1000 characters. The initial 10 input-file
hashes were verified after retaining all previous attempt artifacts. During the
three-turn accepted trial, the controller provided no repair/tool instructions.

The Agent observed `1.15` becoming 114 cents, traced the shared float conversion,
repaired `pricing.cents`, preserved the original business requirements and checks,
and added boundary/invalid-input cases. The native command trace and report show
115 cents for save/quote, normal zero/decimal/large inputs, invalid input preserving
saved bytes, and catalog all-or-nothing/empty-update behavior. The 41 passing
assertions were obtained through a temporary-directory wrapper written by the
Agent: the original command first failed with PermissionError while writing
`catalog.json` inside Python's TemporaryDirectory under the restricted token.
This is conditional product evidence, not a pass for the registered command.
The wrapper also had a syntax/import repair before its successful execution;
those failures remain in the raw trace. No assertion result alone was accepted.

Result lookup issued one read-only command and no product checks. After TUI exit
and native `resume` of the same thread, the summary issued zero commands. All 14
fixture-file hashes were unchanged across lookup and resume, including invocation
history. Both responses retained the pending map review/verification/repair/
regression/normal-case obligations and the default-command failure. The hook did
not block these read-only requests or rerun tests. The Agent did not bind the
successful alternative execution or semantic review into workflow state, so
PARTIAL and enforcement BLOCKED remain. There is no authenticated proof of
end-to-end workflow completion or a protected acceptance boundary.

Evidence: `.work/plugin-transition/native-agent-control-v023/observed-v025.json`,
`lookup-before-v025.json`, the original/retained fixture and native session
`01a10c65-ea12-7862-9b6b-8f905461175f`. Repair/lookup/resumed-lookup command counts
were 10/1/0. Native reported usage after all three turns was 31,107 tokens plus
196,224 cached input tokens; hook character counts are not model token counts.
Features: `plugin-package`, `workflow-obligations`, `feedback-repair`,
`verification-results`. At this three-turn checkpoint, normal registered execution,
semantic/evidence binding and protected acceptance remained open.

A fourth turn then gave a natural follow-up complaint about the failed default
command and missing verification record, without tool or solution hints. The
Agent selected installed `agentic-coding:maintain-project-verification`, reproduced
the original command failure and repaired the fixture runner to create unique
ordinary directories with cleanup. No sandbox permissions, global settings or
original assertions were weakened. It updated the existing Feature Map and
TESTING guide, connected explicit native-report assertions using the installed
viewer/capture, and recorded its semantic analysis through the workflow runtime.
The exact registered `C:\Python312\python.exe check.py .work/report.json` then
executed once through capture, exited zero and produced all 41 passing cases with
zero skips. Main-agent review compared the case values, storage/catalog outcomes,
original requirement hash, command/cwd and actual native trace; a separate read-only
installed audit found READY_FOR_REVIEW, no findings and zero obligations. The
original workflow base and source hashes were retained. The capture itself still
has a null behavior verdict; the bound raw assertions own product assessment.

This resolves the runner and binding gaps for this fixture after explicit feedback;
it does not retroactively make the initial request autonomously complete. The
protected acceptance boundary remains BLOCKED. The fourth turn required source/API
inspection and a small project-specific plan adapter: cumulative native usage rose
to 73,604 tokens plus 708,224 cached input tokens. There is no matched baseline for
claiming efficiency improvement; reducing deterministic evidence-plan preparation
and integration friction remains a concrete maintenance opportunity. Original
Labeler, ordinary installations and remote environments were untouched. Final
evidence: `followup-v025.json`, `independent-final-audit-v025.json`,
`completed-hashes-v025.json` under the same control directory, and the actual
fixture `.work/price-evidence/` capture, raw report and bundle. The fixture is a
CLI/domain task, not a full-stack browser/API/DB acceptance trial.

## Persistent native update binding, 2026-10-05

User authorization completed fixture trust, read-only hook trust and the isolated
unelevated Windows sandbox. The authenticated TUI delivered the automatic workflow
hook and began a natural price-repair request, but selected installed 0.1.21 after
the earlier 0.1.23 update. The controller interrupted before the first proposed
product command. This is an installation defect, not product-task success or a
sandbox failure: the updater only overrode its invocation, leaving the native
marketplace registered to the old source. Earlier immediate install/list evidence
below does not establish persistence across native session startup.

The updater now snapshots the existing plugin and previous source, uses native
marketplace remove/add to retain the inspected source, and verifies that binding.
An identical package with stale registration is repaired without reinstalling;
only matching version, bytes and source are a no-op. Interrupted registration
retains a snapshot and can be retried with a new backup directory. Windows verbatim
and ordinary paths are compared by file identity. Independent review also found
that a same-name remote source must not be silently replaced: the final 0.1.25
guard refuses non-local registrations before snapshot or native mutation. No home/auth/config backup is
made, and native editing preserves unrelated config values.

The focused regression first failed with the old persistent source. Five package
and updater tests now pass, including interrupted rebind/resume, unchanged bytes,
Windows path spelling, no-op, changed-file refusal and corrupt recovery. Actual
isolated native update installed 0.1.24; unrelated config values were identical
and repetition was UNCHANGED. A fresh app-server discovered all 19 Skills from
0.1.24. Evidence: `.work/plugin-transition/host-006/update-v024-final.json` and
`.work/plugin-transition/native-agent-control-v023/discovery-v024/`. Authenticated
natural-task execution is evaluated separately. Final 0.1.25 native update also
preserved unrelated config and returned UNCHANGED on repetition. The distribution
suite ran 149 tests: 148 passed and one timeout-tree cleanup test failed because
taskkill was restricted by the outer sandbox. The same focused test passed in
1.964 seconds with the explicitly reviewed process-control permission. Resource
drift, distribution validation and 12 documentation/cutover tests passed. Feature:
`plugin-package`.

## Missing-cache recovery and authenticated-host preparation, 2026-10-05

A fresh independent `missing-cache-host` installed 0.1.23 through the native CLI.
Its known owned version directory was moved intact to a new retained location
within that fixture, simulating a missing cache without deleting previous bytes.
Repeating native `plugin add` recreated all 244 package files; both the restored
tree and retained original matched the initial hashes. The restored viewer and
capture then executed a real child check (sum 5 and readback `ok`) and produced
current PASS, with the existing runtime test passing in 1.277 seconds. Commands,
hashes and retained fixture are under
`.work/plugin-transition/missing-cache-host/trial.json`. This proves recovery from
an absent cache in that controlled topology, not an actual interrupted install
or safe overwrite of partial/user-modified cache contents. The guarded updater
continues to refuse those ambiguous states.

After explicit user authorization, device login in isolated `host-006/home`
completed successfully. Authentication is no longer the observed blocker for
that home; credentials were neither copied nor included in evidence. Interactive
CLI startup exposed a different host issue: its background Unix-domain socket
path exceeded SUN_LEN. The CLI-recommended `--no-daemon` reached the native trust
screen without moving the home or weakening the workspace sandbox. Automatic
approval review rejected trusting the entire independent fixture because prior
approval covered login/hook review, not folder trust. A separate narrowly scoped
folder-trust approval was requested; no trust bypass was used. Authenticated model
task execution remains unproven at this point. Feature: `plugin-package`.

## Active-work obligation handoff, 2026-10-05

RED confirmed the prompt hook only delivered the configured project-wide record;
an earlier active task's pending verification was absent when the shared record
was already ready. The hook now reads existing active records through the same
`work_record` baseline validation used by close and audits each independently.
At most eight identified candidates and three obligations per candidate enter the
bounded context. Total/omitted counts remain explicit, malformed work stays
BLOCKED, and no project commands or model requests execute. There is no trusted
session-to-work binding in this path, so it does not infer a selected task from
prompt text. Project status and per-work status remain separate.

Workflow/hook/package checks passed 25 tests in 29.046 seconds. Native guarded
update installed candidate 0.1.23 into `host-006`; all 244 files matched. Direct
subprocess execution of that installed hook passed the read-only scenario in
2.496 seconds. Its nine invocations include project-ready/task-A-pending/task-B-ready,
invalid task A with intact task B, eleven tasks with eight shown and three omitted,
unconfigured project and wrong event. The test compares file sets and bytes before
and after delivery, checks that prompt content is absent and that no task is
automatically selected. Raw inputs/outputs and argv are retained in
`.work/plugin-transition/hook-active-installed-v023/calls.json`. This is installed
handler behavior against fixture work records, not a trusted automatic host event
or authenticated Agent session. Feature: `workflow-obligations`.

## Verification obligations for changed criteria and standards, 2026-10-05

RED reproduced a false completion path: changing a registered check definition
without source edits, then refreshing semantic review, removed all obligations.
Criteria and UI-reference changes had the same source-only selection gap. Start
now records a separate verification-input basis (criteria/UI hashes and registered
check definitions). Audit retains execution obligations when that basis changes,
even after a current semantic review. Descriptive map-only edits keep their
review-only path. Legacy records without this separate basis conservatively
reopen execution for changes to their original complete basis; they must not be
reset to current inputs merely to clear an obligation. The existing workflow
owner, native execution and result viewer implement this without model calls.

Workflow/hook tests passed 24 cases. Close/maintenance assertions passed 51 cases
in a combined invocation that also had one erroneous, nonexistent test-module
name; that invocation is not reported as passing. The corrected native-adapter
plus docs/cutover invocation passed 26 cases. Native guarded update installed
0.1.22 into `host-006`; all 244 package files matched. Four focused tests against
its actual workflow/viewer/capture passed in 5.501 seconds, covering changed
commands, criteria, UI, legacy records and the map-only counterexample. The
criteria-only positive case executed a real child that read unchanged price 10,
bound current evidence and cleared the obligation; corrupting its raw result
reopened it. Run ID: `cf19df29-dad4-4d28-a9e4-3bd4af25f21e`. Retained fixtures and
commands are under `.work/plugin-transition/criteria-installed-v022/trial.json`.
This establishes local deterministic behavior, not authenticated Agent judgment
or protected acceptance. Features: `workflow-obligations`, `verification-results`.

## Native active-version rollback and return, 2026-10-05

The intact isolated `host-006` completed a native 0.1.21 → 0.1.16 → 0.1.21 round
trip through the existing guarded update. The historical candidate came from
the verified export of the real interrupted `host-002/guard-backup-0117` snapshot.
Only inventoried package files entered a separate recovery marketplace; no auth,
settings or ordinary installation was copied. Both native commands terminated
with UPDATED receipts, and separate native `plugin list` calls identified the
expected enabled version after each transition. All 244 candidate files matched
at each installation. The marketplace override did not change the registered
original source, which continues to offer the newer package. A later authenticated
session exposed that this binding can undo the selected version on startup; see
the persistent-binding correction above.

The restored 0.1.16 viewer/capture actually ran a child check against an independent
Git fixture and bound the observed sum 5 and readback `ok` to current PASS (1 test,
1.315 seconds). Capture ID: `bebbf843-81a4-4c72-9dcc-33d4909331ba`. Before-rollback
and before-return snapshots retain 244 and 245 files respectively; the additional
file is interpreter bytecode generated during that runtime check. Both snapshots
match their recorded hashes. A final repeated update returned UNCHANGED without
creating another backup. Raw receipts, version queries, fixture and hashes are
retained under `.work/plugin-transition/host-006/active-rollback-trial.json`.

This closes bounded native active-version rollback for an intact cache using
existing tools; it does not prove repair of a missing/corrupt active cache, restore
old hook trust, or resume an authenticated Agent task. No new rollback framework,
runtime or generated change was needed. Feature acceptance: `plugin-package`.

## Recovery export boundary repair, 2026-10-05

Inspection found that `recover` promised an unchanged active installation but
accepted a new output directory inside its home, including a missing cache after
a failed update. RED reproduced that write through the existing destructive-update
fixture. Recovery now reads the snapshot's home and refuses overlapping output
before copying. Existing separate export, corruption, user-edit refusal and
native update cases remain supported; package/update tests passed 4 cases normally.
This is a local path guard, not authenticated snapshot or host enforcement.

Candidate 0.1.21 was freshly installed with the native CLI into task-owned
`host-006`; all 244 package files match. Its actual recovery CLI refused a new
directory inside the original isolated home with exit 1 and no output creation.
The same installed CLI then exported the retained real interrupted-update backup
`host-002/guard-backup-0117` to a separate new directory with exit 0. All 244
exported files match the snapshot, and the original backup remains unchanged.
Commands, native installation receipts and comparisons are retained in
`.work/plugin-transition/host-006/recovery-trial.json`. This proves recovery export
from that interrupted native update, not rollback of active host registry/cache
state or authenticated Agent task continuation. Feature: `plugin-package`.

## Controller process-death recovery, 2026-10-05

The previous exception-based interruption coverage now has a real process-death
counterpart. The regression starts a separate controller, waits for its first
durable checkpoint while confirming the process is live, and kills only that
owned process. A new public CLI process resumes the pending check. The existing
assertions verify each product command ran once, old evidence remained unchanged,
and a repeated resume ran zero commands. Changed plan/dependency, missing raw,
truncated checkpoint and unknown-launch controls remain part of the same test.
Source execution passed with normal cleanup (1 test, 4.216 seconds). The actual
0.1.20 installed viewer and capture passed the same test (1 test, 4.287 seconds),
with its fixture retained under `.work/plugin-transition/process-death-installed-v020`
for inspection. Installed viewer bytes match the distributed file exactly.
Two setup assertions stopped before execution: an incorrect assumed capture
path and comparing canonical bytes with the generated header. The corrected
paths and comparison are recorded in `trial.json`.

This closes the specific checkpoint-boundary process-death gap for
`verification-results`, without changing runtime or generated resources. It is
not power-loss durability, a kill during an active product command, or interrupted
installation recovery. Those boundaries and protected acceptance remain separate.

## Installed Agent resume acceptance, 2026-10-05

After implementation commit `5b2cf55`, a fresh collaboration Agent received a
user-shaped request to finish interrupted price verification without repeating
completed checks or losing evidence. The independent fixture at
`.work/plugin-transition/resume-agent-v020` points to the actual native-installed
0.1.20 resources in `host-005`. No Skill name, resume flag, solution patch or
follow-up hint was supplied in the request. Existing project testing instructions
identify the original command and evidence locations. The Agent independently
selected the installed viewer's `--execute --plan ... --evidence-dir ... --resume`
path and completed the remaining persisted-price readback.

The controller had interrupted execution immediately after the first committed
checkpoint: 19 business cases were complete, while readback had not started.
Independent inspection found the command ledger exactly `rules`, `readback`,
each once; persisted price was 1230 cents, with one assertion and none skipped.
Of 19 initial files, only the append-only command ledger changed. Product,
criteria, plan, raw captures and initial checkpoints retained their bytes, and
fixture Git HEAD remained `1d5af482f55df8aa88afff7201b1c89d3655970d`, clean.
The parent then invoked the installed viewer against the canonical bundle:
exit 0, both required checks PASS, zero test commands, all 29 files unchanged.
Native run IDs are `2de24625-62fc-4d61-b3f4-89cc7c3a1ea0` and
`febee700-7fdf-484e-b415-7d252537dc4f`. Before/after hashes, request, actual argv,
captures and independent lookup are linked by
`.work/plugin-transition/resume-agent-control-v020/trial.json`.

This establishes bounded installed Agent resume behavior with zero interventions
after delegation. The interruption was controlled injection, not an OS crash;
the Agent was a fresh collaboration Agent, not an authenticated isolated native
CLI session. It does not establish protected completion acceptance or whole
U1-U7 completion. Feature impact is acceptance evidence for `verification-results`;
no runtime, generated resource or Feature Map contract changed in this follow-up.

Environment status was refreshed after old handles 71160, 88633 and 11677 returned
terminal exit 1 and installer PID 46292 was absent. Those earlier operations
remain unsuccessful. With that state change, the previously excluded
`test_symlink_file_reference_and_native_report_are_blocked_before_child` passed
normally (1 test, 0.799 seconds), and `tests.distribution.test_plugin_package`
passed normally (1 test, 5.836 seconds). This closes these specific outstanding
checks, including normal package fixture cleanup; it neither identifies the
earlier Windows stall's root cause nor retroactively turns interrupted suites
into passes. Hook trust, isolated login and protected acceptance remain separate.

## Interrupted verification resume, 2026-10-05

A read-only review confirmed a U3/U7 implementation gap: the viewer wrote the
joined bundle only after all commands and rejected existing captures/reports on
rerun. Completed work could not be resumed through the normal CLI. The repaired
execution path writes an exclusive, flushed launch marker before each command
and immutable normal-format bundles after completed checks. `--resume` validates
the same source plan and current evidence, reuses completed checks with current evidence, and
executes only never-started checks. It does not replay a launch whose outcome is
unknown. Completed final results, and the last checkpoint when final persistence
was interrupted, are readable without another command. This reuses the existing
viewer/capture; no model or scheduler is added. Checkpoints contain cumulative
snapshots, so storage is quadratic in check count; very large plans should use
existing partitions. This is local consistency, not protected acceptance.

RED observed absent interruption checkpoints. The execution assertions passed
21 cases, followed by two more final-write/unknown-launch cases. Their fixture
cleanup was deliberately retained in a diagnostic runner because the independent
Windows `unlink` stall remains unresolved; these results do not claim ordinary
suite cleanup passed. The unchanged viewer plus documentation suite passed
21 cases with normal cleanup. Resource drift, distribution and whitespace checks
passed. Independent review found two more interruptions: a truncated final descriptor
hid a complete checkpoint, and a completed assertion failure prevented later
checks. Both were reproduced RED and repaired. Bundle publication now uses a
flushed pending file and an exclusive atomic hard link; an invalid final descriptor
can only fall back to a fully completed, revalidated checkpoint. Known failure
observations are retained as ISSUES while never-started checks continue. A final
caller review also found that checkpoint fallback had not repaired the configured
canonical bundle path. RED/GREEN now proves that resume repairs that path and
normal workflow lookup reads it; torn descriptor bytes are retained separately.

Fresh native installation of candidate 0.1.18 into independent `host-003` returned
its actual plugin identity and cache path; all 244 package files match. The old
hung `host-002` installer was not retried. Three installed-runtime regressions
under `.work/plugin-transition/resume-installed-v018` exercised real child
commands and public CLI resume. First/second report calls occur once each;
resume executes only the second command and repeating the completed run executes
zero. Original captures/checkpoints remain byte-identical. Changed plan/dependency,
missing raw, truncated checkpoint and unknown-launch controls refuse execution.
The final-write interruption also resumes with zero execution. Native capture
IDs include `71071226-b893-493e-8f9e-eeb007b82289` and
`e7bea76e-c8a1-4f26-a395-212f49739e8a`. `trial.json`, the actual command plans,
reports, call ledger and captures are retained with the fixtures.

Final candidate 0.1.20 was freshly installed into `host-005`; all 244 package
files match. Seven installed resume regressions passed in 22.259 seconds under
`.work/plugin-transition/resume-installed-v020`, including known failure,
optional policy preservation and canonical consumer recovery. Final viewer/docs
21 tests passed normally; resource drift/distribution passed. The wider execution
attempt stopped at a symlink-negative child CLI and is not a passing suite. The
selected follow-up eventually completed 26 assertions in 171.217 seconds, with
that one unresolved case excluded. Its transient command wait was not terminal:
the same handle later returned exit 0. The attempted cleanup correctly refused
when its recorded parent had already exited. Earlier final-tail three assertions
also passed independently with retained fixtures. Fixture retention
avoids the separately reproduced Windows deletion stall; normal teardown is not
claimed. No security configuration or failure assertion was weakened.

The controller interruptions are fault injection in the installed runtime, not
claims of an actual OS crash or authenticated Agent task. Hook trust/login,
protected acceptance and old installer/process cleanup remain separate limits;
whole U1-U7 acceptance is still incomplete.

## Prompt-hook handoff and actual host discovery, 2026-10-05

The previous missing initial handoff prompted a fresh host check rather than
another reminder in Skills. Codex 0.160.0 reports hooks stable/enabled, and current
[official documentation](https://learn.chatgpt.com/docs/hooks) defines a
UserPromptSubmit context hook. The package now includes a read-only handler that
reuses the configured workflow owner to compute and return bounded obligations,
targets and references. It reads no user prompt/transcript, executes no product
commands, starts no work record and does not block lookup-only requests. Supplied
null state now also fails in the shared configured-audit entry used by this hook
and existing maintenance/close callers.

RED reproduced the absent handler. The handler/workflow checks passed 22 tests;
the related workflow, package, close and maintenance run passed 74 tests before
the later manifest assertion/test-harness correction. Final package assertions
also passed in a diagnostic run retaining its temporary fixture; ordinary cleanup
remains separately unverified below. The new package test executes the exact
distributed shell command, and validates the explicit compatibility hook path.

Actual guarded installation produced 0.1.15 and then 0.1.16 with that explicit
manifest path. Direct 0.1.16 handler calls observed existing completed feedback
state, refused configured null state, and returned empty output for an independent
unconfigured Git project without modifying its inputs. Retained records are in
`.work/plugin-transition/hook-handler-v016-02`. Initial trial assumptions were
corrected without rewriting evidence: the first invalid fixture had no configured
state, and a nested directory without its own Git repository correctly resolved
the parent project instead of being an independent unconfigured project.

Native discovery was repaired, rather than attributed to sandbox permissions.
Correcting the trial's stale marketplace registration alone still returned empty
hook lists. Minimal paired packages then isolated the `$schema` marker: without
it the identical definition was discovered; with it, both default and explicit
OpenAI-extension paths were empty. A full package copy without that marker also
exposed the hook. Candidate 0.1.17 omits the optional marker and retains the
compatibility manifest. Actual `hooks/list` now returns the installed 0.1.17
cache path, `source: plugin`, `enabled: true`, and `trustStatus: untrusted`;
`plugin/read` also exposes UserPromptSubmit. Reproduction records are under
`.work/plugin-transition/hook-schema-probes` and `host-002/captures/{hooks,plugin}-v017`.
Earlier empty probes remain retained. This was a packaging/host interpretation
compatibility issue, not evidence that hooks are unavailable or permissions must
be broadened. No hook was self-trusted or bypassed. Automatic event delivery,
authenticated Agent use and protected acceptance remain unverified.
The final hook/docs/cutover command passed 13 tests.
Resource drift, distribution validation and diff whitespace checks also passed.
The guarded 0.1.17 native installer wrote all 243 inventoried payload files, whose
hashes independently match the candidate, but did not return. After verifying
its exact PID, parent and command, termination was requested only for the owned installer and wrapper;
the installer remained visible after that request. The guard has a verified
snapshot but no completed receipt. Thus installed bytes
and native discovery are observed, while update-command completion is BLOCKED.
No duplicate update was launched to conceal that unfinished operation.

Package-test cleanup stalled at Python os.unlink, including a scoped external
retry; stack and a retained-fixture diagnostic separate successful assertions
from cleanup. A logged cleanup narrowed the wait to the generated consumer's
probe.py. A test variable collision was independently corrected; it had reused
the hook command in the old overwrite check. Do not count terminated cleanup
runs as passing tests or attribute the remaining wait to sandbox permissions
without further evidence. No product behavior or access policy was weakened.

## Follow-up feedback and plugin capture discovery, 2026-10-05

A fresh collaboration Agent received a user-shaped bulk-price repair request in
`feedback-followup-v013`, an independent copy of the earlier repaired price
fixture with a controlled new bulk-save fault. Only its project instructions
pointed to installed 0.1.13 capabilities; no Skill name, patch or required command
sequence was supplied in the request. The original fixture remained untouched.
The Agent read installed diagnosis guidance, reused the existing `pricing.cents`
owner, validated every bulk value before writing, extended the existing native
check and updated the map in fixture commit `7eb170f`. Original single-save,
quote, zero and unmentioned records remained supported. A separate fixed oracle
outside the Agent's allowed project observed six failures across four tests
before repair and passed all four afterward without changing its bytes. Invalid
later values preserved the original file bytes and did not create a new file.

Product success did not complete the configured workflow: the first post-Agent
audit still required semantic review and bound execution. The trial controller
had created the feedback task record but had not forwarded its computed
obligations with the initial request. One supervisory follow-up forwarded that
actual result. The Agent recorded semantic review without rerunning checks, but
could not discover the capture CLI outside the installed Skills directory and
correctly refused to fabricate a capture for earlier direct execution. This is
observed intervention and discovery overhead, not an unattended success.

The plugin's result CLI now resolves its own packaged capture tool for explicit
`--execute` calls. It checks the enclosing package identity and fixed script path;
it does not search PATH or unrelated installations. Standalone Skills still need
an explicit capture path, and `--run-check` remains an override. No model call is
used for this tool selection. The package integration regression first failed
because `--run-check` was required, then exercised implicit execution, refusal
without the package identity, and explicit-path compatibility. Related package,
execution and lookup tests passed 39 tests in 43.498 seconds; documentation,
generated-resource and distribution checks passed. Package 0.1.14 was guardedly
installed in isolated host-002 for continuation of the same task.

After the installation-update follow-up, the same Agent completed the connection
with one additional native execution because the earlier direct run had no
capture provenance. The installed CLI selected the package capture tool without
`--run-check`; its capture records the actual 19-case native run. The Agent bound
the current semantic review and retained prior RED/GREEN evidence. Fixture commit
`84f58f2` updates installed discovery and the new registered report path without
changing product code. Main independently re-read the bundle and audited the
task: current PASS, zero test executions during lookup, READY_FOR_REVIEW with no
obligations, and all 29 inspected tracked/evidence files unchanged. Raw commands,
fixed-oracle hash, before/after results and the two supervisory follow-ups are
retained in `feedback-followup-control/trial.json`. This demonstrates reuse of
the earlier repair owner and completion after explicit environmental handoff;
it does not erase the first incomplete report or establish automatic host
handoff. Source delivery includes the capture-discovery fix, its regression,
updated guidance and generated consumers as one functional unit.

The collaboration context and explicit project discovery bridge are distinct
from an authenticated isolated CLI host. A current `codex login status` for that
home still returned `Not logged in`. This trial does not establish protected
acceptance, disk-failure/concurrent-write atomicity, or general cost/speed gains.
U1-U7 overall remains incomplete; no ordinary installation or original Labeler
was changed.

## Retain unresolved product findings through retirement, 2026-10-05

Removing a Feature previously hid its product findings, and even an explicit
removal review carrying unresolved product findings could reach READY_FOR_REVIEW.
The shared workflow owner now retains earlier findings until a current removal
review explicitly reconciles them. Omission preserves them; a current review
with remaining findings completes map reconciliation but keeps the task PARTIAL.
Stale reconciliation restores earlier and retirement findings. Invalid retired
review shapes are rejected rather than causing an uncaught exception.

The new regression reproduced missing findings before the fix, then covered
removal, current unresolved review, field omission, explicit semantic resolution,
state serialization/resume, stale reconciliation and malformed review shapes.
Final focused workflow, close lifecycle, maintenance and documentation checks
passed 75 tests in 38.035 seconds. Verification scope is the retirement branch
and its existing completion/maintenance callers, not a new whole-system claim.

Actual installed package 0.1.13 was guardedly updated in isolated host-002.
`retirement-consumer-v013` uses its public CLI in separate processes against a
real Git fixture: remove the CLI source and mapping row, preserve its unresolved
caller finding, reject omission as resolution, resume without state mutation,
accept current explicit reconciliation, then change source and reopen the stale
review. A malformed retained review returns BLOCKED. Commands, stdout, stderr
and actual state remain in the fixture's `.work/`. The preceding 0.1.12 trial
also remains; it exposed the malformed-review exception corrected in 0.1.13.
This proves local obligation retention, not autonomous Agent diagnosis or actual
caller migration. An explicit empty product-findings list remains semantic
review input, not proof of product repair. U4 and the overall U1-U7 goal remain
incomplete; original Labeler and ordinary/global installations were untouched.

## Execute outstanding task verification, 2026-10-05

The existing project adapter now supports `--work-id <id>` or
`--pending-state .work/<record>.json` with `--all-checks --output <new-directory>`.
It invokes the sibling workflow CLI to recompute required execution from the
actual baseline, changed inputs and current native evidence. Only REQUIRED
Features are selected; unaffected or already verified Features are omitted.
The existing batch path handles shared checks. Workflow and Feature Map check
lists must agree before any command runs. Native PASS does not discharge a
separate product/semantic finding. If no execution is outstanding, the result is
NOT_REQUIRED with zero commands and no output directory, while selection-time
workflow status and remaining obligations stay visible. Bundles still require
semantic review/binding before current completion is reevaluated.

RED reproduced absent pending selection; an additional negative control showed
an empty supplied state being treated as no-impact work. The common audit now
rejects that invalid baseline. Regression covers selected execution, an untouched
Feature whose command must never run, reuse despite a separate product finding,
state preservation, missing/empty state rejection and no output on no-op.
Independent review then identified a supplied JSON `null` taking the intentionally
state-less audit path. A second RED reproduced the false NOT_REQUIRED result;
the CLI now rejects supplied null state. Final package 0.1.11 was installed and
its actual runtime returned BLOCKED for that record, with no test or output
directory (`pending-consumer-v0110/.work/null-check-v0111/process.json`).

Package 0.1.10 was guardedly installed in isolated host-002. The retained trial
`.work/plugin-transition/pending-consumer-v0110` used installed design/start,
workflow and close CLIs plus the project-owned adapter with byte-identical
installed capture/workflow/reader dependencies. Normal start captured the baseline
without manual workflow begin. Pending execution selected the changed price
Feature without a handwritten Feature list; native price 9 versus expected 10
failed, and close refused completion. Repair to `5 + 5` passed the unchanged
assertion and current review. A second pending-execution request returned
NOT_REQUIRED without a new directory or suite run. Close then completed and
retained the work state. Exactly two suites ran across failure and repair; raw
commands, captures and no-op result are retained in that fixture's `.work/`.

This connects configured native unittest work to deterministic execution; it is
not authenticated Agent task selection or a universal adapter for browser/API/DB
commands. Those require their existing native runners and criteria. The rest of
U1-U7 remains open, and no original Labeler or ordinary installation was changed.
The isolated host login was rechecked during this unit and remains `Not logged
in`; authenticated installed-Agent evaluation still awaits that isolated login.

Final-source validation passed: Full `python -m unittest discover -s tests -p
'test_*.py'` ran 296 tests in 268.315 seconds; focused adapter/workflow tests
passed 34 tests, documentation checks passed 3 tests, and resource drift,
distribution and Git whitespace checks passed.

## Shared native checks across selected Features, 2026-10-05

The existing project-owned unittest adapter now accepts
`--features <id> <id> --all-checks --output <new-directory>`. It resolves all
selected mappings before execution, then shares equal check ID/effective argv/cwd
within that batch. Different check IDs remain separate even with identical argv.
Capture records the preselected consumers before launching the command; each
Feature bundle references that same raw run. The distributed native reader
requires consumer membership, exact command/target, native outcome and current
Git identity. A relabeled bundle cannot claim an unselected Feature. Legacy
single-Feature captures and CLI arguments retain their behavior. This does not
authenticate editable captures or infer coverage from matching command text.

RED reproduced the missing multi-Feature execution path. Regression coverage
checks shared execution count, distinct IDs with identical commands, read-only
lookup, unselected-consumer refusal, stale results and shared failure propagation.
An independent read-only review found no material correctness/trust regression.
The earlier focused run passed the shared-check cases but failed the existing
Windows descendant-cleanup test under the default sandbox (`taskkill` exit 1).
A scoped elevated rerun passed that specific test; read-only process inspection
found no remaining matching child. That initial run is not reported as passing.

Package 0.1.9 was installed through the guard into isolated host-002. In
`.work/plugin-transition/shared-consumer-v019`, a project-owned adapter used
byte-identical copies of the installed capture and reader, while audit/review
called the installed workflow CLI directly. The native suite separately asserted
the price value and the quote function consuming it. Wrong value 9 caused both
assertions to fail in one suite invocation and both obligations remained PARTIAL.
Repair to 10 passed both assertions in one new invocation; both Feature bundles
reference the same run and reached READY_FOR_REVIEW. Total suite invocations were
two across failure and repair; lookup launched zero. Commands, captures/raw,
bindings and the count are retained in that fixture's `.work/`.

Validation: Full `python -m unittest discover -s tests -p "test_*.py"` passed
295 tests in 280.220 seconds. Documentation tests (3), distribution validation,
generated-resource drift and formatting checks also passed.

This is an observed two-consumer native unittest batch, not autonomous Agent
behavior, automatic affected-Feature selection, cross-batch caching or generic
browser/API/DB evidence sharing. The adapter remains project-owned; the common
plugin distributes capture and evidence consumption. Those remaining U3/host
boundaries and the rest of U1-U7 stay open.

## Descriptive-document impact selection, 2026-10-05

Broad source inventories previously required product execution even when only a
descriptive map changed. A Feature can now declare `documentation_only` as exact
paths with reviewed reasons. Work start retains that policy. An existing file
declared both before and after the change still requires current semantic review,
but does not by itself require product execution. Filename extensions do not
grant exemptions. New/deleted paths, mixed code changes, feedback/UI requests,
late declarations and legacy states without the policy snapshot remain subject
to their previous verification requirements. Audit exposes the changed paths and
the narrower `verification_changed` set. Project policy remains editable local
state, not a protected authorization boundary; executable/generator/Agent inputs
must not be declared descriptive merely to avoid their checks.

RED reproduced product execution being required after only a map clarification.
The regression also checks mixed code changes, late reclassification, legacy
records, document deletion and wildcard rejection. Actual guarded installation
of package 0.1.8 into host-002 was followed by public installed workflow CLI runs
in `.work/plugin-transition/documentation-consumer-v018`. A descriptive map edit
reached readiness after semantic review with zero suite runs; resume preserved
its state. Changing price 10 to 9, then attempting a late documentation exemption,
still required execution. The unchanged native assertion failed, remained
PARTIAL, and passed only after repair to `5 + 5`. There were exactly two suite
runs (failure and repair); lookup launched none. Commands, native raw output and
result are retained in that fixture's `.work/`. This is installed CLI behavior,
not autonomous Agent classification or general performance superiority.

Validation: Full `python -m unittest discover -s tests -p "test_*.py"` passed
294 tests in 258.977 seconds; documentation tests (3), distribution validation,
resource drift and formatting checks also passed.

The earlier Labeler state and product-gap evidence were not retroactively
rewritten to waive its existing obligation. New project declarations require
consumer review; this policy does not automatically classify every Markdown file
or invalidate already required tests. U1-U7 overall acceptance remains open.

## Mapping readiness and product gaps, 2026-10-05

The workflow now reports `mapping_status` independently from overall task
`status`. Review authors can explicitly separate `product_findings` from map
`findings`: known language-quality or data-completeness gaps stay visible without
being mistaken for missing feature mapping. Legacy findings remain blocking;
there is no automatic relabeling. Missing owners/references/commands, stale
reviews and unreconciled removals still block map readiness. Product findings
and missing/failed native execution continue to block overall task completion,
even when the map is ready. Neither readiness field is a product PASS.

RED reproduced the absent distinction and silent omission of a product finding;
the new regression verifies retained gaps, unchanged verification requirements
after a source edit, legacy map findings and malformed product-finding rejection.
Package 0.1.7 was guardedly installed into isolated host-002. The installed setup
CLI audited a copy of the retained Labeler review state at
`.work/agent-workflow-foundation-20261005/labeler/.work/u1-map-status-v017-02`.
The two product gaps were reclassified with their original text preserved after
reviewing the requirement links and snapshot references from fixture commit
`38296e5`. The repository-runtime mapping review was refreshed against its
two-row map-only diff. Actual CLI output was mapping READY_FOR_REVIEW, task
PARTIAL, two retained product findings, and a still-pending runtime verification
obligation. Prior evidence hashes were unchanged; no product tests or provider
calls were launched. This establishes local map-state separation for the retained
survey, not an independent proof of full semantic completeness or product quality.

Validation: Full `python -m unittest discover -s tests -p "test_*.py"` passed
293 tests in 256.485 seconds. Documentation tests (3), resource drift check,
distribution validation and diff formatting also passed.

The first installed audit failed because the elevated install process ran Git
as YS against a CodexSandboxOffline-owned fixture. Direct stderr established
Git's dubious-ownership rejection. Running audit under the original sandbox
account succeeded; no global safe.directory exception or permission change was
made. Failed output remains in `.work/u1-map-status-v017`. The broad fixture
repository-runtime source mapping still selects verification for a map-only
documentation edit; reducing that false positive remains separate work.

## Automatic configured-work obligations, 2026-10-05

Harness `start` now captures the configured workflow baseline in its existing
atomic work manifest before implementation. Resume preserves it; `--work-id`
audit/review uses that baseline without a separate manual `begin`. Current
project semantic reviews are reused, while changed inputs invalidate them.
Responses expose a compact reference rather than the entire source inventory.
`close` automatically checks the task's unresolved obligations, including when
the caller omits the optional project argument. Removing workflow configuration
does not silently discharge a baseline captured at start.

Two additional RED/GREEN cases repaired real omissions: an actual child-process
exit during review staging previously poisoned resume with an unexpected pending
file; staging outside the strict active directory now preserves resumability.
A minimal hand-written review containing only a matching basis and empty findings
previously counted as reviewed; audit now validates analysis and live references
too. These are consistency checks, not semantic authentication or tamper-proof
policy. A rewritten task baseline is rejected on resume.

Full: `python -m unittest discover -s tests -p "test_*.py"` passed 292 tests in
298.274 seconds. Package 0.1.6 was installed through the guarded native update
into the existing isolated host-002 home. Its public installed design/start,
workflow audit/review, and close CLIs were exercised in
`.work/plugin-transition/start-consumer-v016-02`. The original start baseline
survived resume; read-only audit created no review file; a submitted success claim
without native evidence was rejected. The native unittest then observed price 9
instead of the required 10, and close still rejected completion. Repairing the
implementation to `5 + 5` passed the unchanged assertion; close then completed
and retained the workflow record. Exactly two suite runs occurred, with no test
rerun on lookup. Commands/stdout/stderr, native captures and the final lifecycle
result are retained in that fixture's `.work/` directory.

The preceding `start-consumer-v016` attempt used an unsupported custom command
field in the trial configuration and was rejected before start. The corrected
trial uses the supported Feature selector; the failed attempt remains retained.
These are actual installed CLI effects and product-fixture observations, not
autonomous Agent selection. Ordinary non-Harness requests, protected acceptance,
authenticated host tasks and the remaining U1-U7 requirements are not completed
by this unit.

Independent U1 follow-up corrected only two map rows in the Labeler fixture,
commit `38296e5`: translation now references its requirements and catalog points
to its retained progress snapshot. Language-quality acceptance and live catalog
completeness remain unverified product claims. They must not be turned into a
requirement to call providers or improve the product merely to finish the map.
At this earlier point the local audit still conflated product gaps with map-review
findings. The subsequent mapping-readiness unit separated them; its installed
`u1-map-status-v017-02/result.json` records all 11 Features as mapping-ready while
retaining both product findings and task PARTIAL. Original
Labeler and prior evidence were preserved.

## Deleted-source verification obligations, 2026-10-05

A real staged-deletion regression showed that a surviving wildcard-mapped Feature
could reach READY_FOR_REVIEW after only an updated semantic review, with no tests:
the removed source had disappeared from the current Git inventory. The runtime
now matches changed baseline paths as well as current sources. New work records
retain initial Feature source patterns, so narrowing the current source map does
not erase the deleted file's original consumer. Older records with unmatched
deleted paths retain an explicit ownership finding instead of silently passing.
Existing unrelated-document and unaffected-partition cases remain accepted.

The corrected 0.1.5 package was installed through the guarded local updater in
`host-002`. An independent retained project under
`.work/plugin-transition/deletion-consumer-v015/` staged removal of a legacy price
module and narrowed its Feature source map. Installed public begin/review/audit
commands kept verification pending; the unchanged unittest then detected price
9 instead of required 10. After repairing the remaining owner, the same assertion
passed and the bound review reached READY_FOR_REVIEW. A fresh audit changed no
evidence bytes and did not rerun either test invocation. `trial.json` retains
commands and raw output; the suite ran exactly twice, for failure and repair.
This proves installed CLI behavior, not autonomous Agent selection or protected
acceptance. Cross-Feature execution deduplication and automatic task orchestration
remain separate incomplete requirements.

## Guarded plugin update, 2026-10-05

The distributed `scripts/update_plugin.py` now refuses ordinary user changes
before native local update, saves the previous plugin tree outside the host home,
and verifies the returned native identity/path plus installed candidate bytes.
Identical repeated updates make no native call. Recovery verifies retained bytes
and exports them to a new directory without overwriting the active installation.
This closes the previously observed unguarded update's ordinary user-file loss
path when using this command with no concurrent external installer/editor.

The real isolated `host-002` trial first refused a deliberate user note without
calling the native installer, then updated 0.1.2 to 0.1.3 once. Independent review
identified missing native receipt checks; a failing regression was added and the
guard corrected. The final packaged updater then performed actual 0.1.3 to 0.1.4
update, checked Codex's returned plugin ID/version/path, returned UNCHANGED on
repeat, and recovered previous file hashes exactly. Raw native output, receipts
and preserved files are under `.work/plugin-transition/host-002/`, including
`guarded-final-update-result.json` and `guard-backup-014/`.

Focused tests exercise extra/modified files, generated bytecode preservation,
destructive command failure, corrupt backup rejection, duplicate no-op, wrong
native receipt, cooperative lock contention, path overlap and a real Windows
junction. The destructive command is an injected fault, not a killed native-host
process. Inventory checks are local consistency, not authenticated provenance.
The lock does not coordinate direct native installers or other cache writers.
Active-install rollback after interruption and authenticated installed Agent
resumption remain unfinished U7 requirements; recovery export does not satisfy
them. Original Labeler, normal installations and global configuration were not
updated by this delivery. U1-U6 and overall acceptance remain open as recorded.

## Native unittest workflow connection, 2026-10-05

The existing unittest assessor and Git capture identity now have one canonical
source, distributed beside the workflow consumer. The repository adapter can
execute all checks registered to a Feature once and produce a capture bundle,
or bind an existing run without executing it. Workflow audit reuses that native
assessor directly; no project code or recorded test command runs during lookup.
Actual changes can now satisfy a verification obligation with native unittest
captures without fabricating a browser/API JSON report. Missing checks, mismatched
targets, stale source, skipped/zero suites and failed captures remain unresolved.
This is local consistency for unittest assertions, not protected host acceptance
or evidence about ignored inputs/dependencies/runtime identity.

Independent review identified unchanged Git status names hiding changed untracked
test inputs. A real regression test reproduced the false reuse; the shared capture
identity now hashes safe untracked file bytes and rejects private/aliased inputs
without reading them. Ignored runtime inputs still require separately bound native
conditions. A fully rewritten capture is not authenticated by this local reader;
host-owned acceptance remains a separate unfinished requirement.

The real repository `plugin-package` Feature was executed through `--all-checks`.
The 0.1.1 plugin was installed in the existing isolated marketplace, and its
installed workflow reader reassessed that bundle as PASS with zero test commands
and unchanged evidence bytes. All 237 recorded package hashes matched the cache.
Raw update execution and reader results are retained under
`.work/plugin-transition/host-001/`; the native bundle is under
`.work/plugin-transition/native-plugin-package-v011/`.

The update also exposed a real U7 gap: Codex removed the previous 0.1.0 cache,
including a deliberate test-only user note. The preservation assertion failed;
`update-result.json` records `old_user_file_preserved: false`. This was an isolated
fixture, not a normal installation. Native plugin update alone is therefore not
accepted as the user-change-preserving delivery path. A guarded update/backup
path remains required. Installed model task behavior is still unverified.

The corrected 0.1.2 package was freshly installed in `host-002`; all 237 recorded
file hashes matched. A retained independent Git fixture at
`.work/plugin-transition/native-consumer-v012/` ran the installed public
begin/review/audit CLI around a real price repair. Its unchanged unittest ran
once, the bound semantic review reached READY_FOR_REVIEW, read-only audit retained
identical evidence bytes and run count, and a later source change returned PARTIAL.
`trial.json` retains each argv, exit and raw output. This is installed CLI behavior,
not an autonomous Agent trial.

Final validation for this connection: **285 tests passed**, generated-resource and
distribution checks passed. The earlier 284-test pass preceded the untracked-input
repair and is not used as its evidence. Full used the scoped external execution
needed by the existing owned-process cleanup test.

## Plugin transition and environment recheck, 2026-10-05

The transition resumed from clean `3c3a5be` on the same branch. The [plugin
builder](../plugins.md) produces the current 19-Skill catalog and capture CLI from
existing sources, checks generated drift, and refuses an existing output directory.
The package integration test executes its capture tool outside the checkout and
checks preservation on a repeated build. It does not claim Agent task success.

An actual task-local Codex 0.160.0 marketplace install and duplicate add completed.
A fresh app-server returned all 19 enabled `agentic-coding:` Skills under the
isolated plugin cache with the expected plugin ID. The cache's capture CLI then
ran a real foreground command successfully. Raw CLI and discovery records are in
`.work/plugin-transition/host-001/captures/`. General installation and global
configuration were not changed. Authenticated autonomous task acceptance remains
separate; the isolated discovery home intentionally contains no copied credentials.

The earlier socket 10013 and process-cleanup failures below are historical, not
proof of an unavoidable host limitation. The same credential-free TLS handshake
failed inside the outer tool sandbox and succeeded with scoped external execution;
the exact owned-child cleanup test also passed there. Full tests for this package
unit passed: **282 tests**, with no skip or failure, using scoped external execution
for the existing process-cleanup requirement. Distribution validation passed.
This corrects the previous environment diagnosis without claiming authenticated
model execution or protected acceptance. `accept` still has no connected protected
host boundary, and the full U1-U7 task acceptance remains incomplete.

## U1-U7 implementation, 2026-10-05

This continuation started from clean `wp-20261004-agent-coding-foundation` at `864ee4f053463e843e2a41d4ad57799446113f70`. The coupled runtime/evidence/distribution unit is committed locally as `b1b710c`. The current design is [completion design](agent-workflow-completion-design.md), and the authorized execution is [next-session prompt](agent-workflow-next-session.md). New temporary evidence is under `.work/agent-workflow-foundation-20261005/`; earlier T1-T6 raw remains unchanged. Local source delivery, temporary installation, product observations, supervised Agent behavior and protected host acceptance are separate outcomes. Overall status remains **PARTIAL / BLOCKED**, not completion of the whole system.

### Implemented responsibility and execution boundaries

`authoring/scripts/project_workflow.py` reads the existing `extensions.workflow` config and task-owned work record. It inventories declared Git-visible roots, partitions the full survey, preserves the dirty baseline on resume, computes current source/criteria/map/UI/command bases, exposes unowned changes and stale reviews, and checks active prevention connections. These deterministic operations call no model. The project owns requirements and command selection; an Agent supplies concrete semantic analysis and actual map/code/guide repairs. The configured existing Harness maintenance and close paths call the same computation, including when the optional workflow CLI is skipped.

Behavior obligations require a current execution bundle, matching Feature/check and exact registered argv/cwd. Feedback cannot be cleared by a PASS field or a repeated unchanged analysis. UI requests require a connected standard and behavioral verification; initial mapping completeness and runtime coverage remain distinct. Audit and bundle lookup are read-only. Their local `READY_FOR_REVIEW`/`PASS` results cannot authenticate the Agent's analysis or protect editable policy/evidence. `accept` explicitly returns `BLOCKED` on this host.

The existing viewer now has opt-in `--execute --plan ... --run-check ... --evidence-dir ...` and read-only `--bundle ...`. Execution uses the existing capture runner, native JSON facts, preselected assertions, current Git state, declared dependency/fixture file hashes and executable identity. It never uses a success string as the product oracle. All inputs are remeasured at final result production and lookup. Main review reproduced and repaired two false-reuse paths: changing bound criteria after execution, and a later check changing an earlier check's ignored fixture. Thirty-eight execution/viewer tests passed after repair. This remains local consistency, not hostile-process attestation or external-service identity.

Installation reuses an already exact cohort without rewriting it. A replacement retains previous installed bytes, and a failed restore retains backup/staging paths for recovery. Existing hash-count coverage prevented redundant source hashing; the first implementation's extra scan was removed. Self-containment scanning now uses Python token spans for Markdown links: callable subscripts no longer create false missing-link findings, while real docstring links are still checked.

### Unit outcomes and evidence

| Unit | Implementation and actual acceptance evidence | Remaining scope |
| --- | --- | --- |
| U1 | Executable partitioned obligations; Git fixtures cover full API/CLI inventory, unconnected coverage, addition/deletion, shared criteria/command changes, stale/duplicate review and resume. Independent Labeler survey exported 319 safe tracked donor files, created 11 functional areas including roles/API/CLI/webhooks/recovery and retained the map in local fixture commit `c770500`. The subsequent installed audit records all 11 Features as reviewed/mapping-ready, while retaining translation quality and catalog completeness as product findings. | The shared-map dependency repair reopened all 11 reviews; the subsequent bounded section 3.2 review connected requirements, variants, shared flows and explicit execution gaps, and installed 0.1.32 now reports all 11 current mapping reviews valid. This establishes the isolated snapshot map within the observed survey boundary, not universal product completeness or host-protected semantic acceptance. The two product findings do not block map readiness and do not authorize provider/product work. File coverage (`unmapped=0`) alone is insufficient; runtime/provider/print acceptance is separate from this survey. |
| U2 | Same-authority child probe actually changed a task-local policy and wrote forged success; `accept` still refused protected acceptance. Configured local close rejects unresolved obligations and submitted success. Normal edits and native runs remain available. | Protected policy, verifier identity, result authority and bypass-resistant acceptance are BLOCKED. The earlier model-startup block is resolved in the approved isolated native trial; successful login/task execution does not supply protected result authority. No unsupported security promise is made. |
| U3 | Actual child runs produce current native facts, captures and bundles; zero/skip/missing/stale/changed-criterion cases reject reuse. Fresh installed v3 executed the price save/read/quote check once and then queried the bundle with zero test executions and 12 retained files unchanged. The authenticated 0.1.25 trial later queried without re-execution, resumed with zero commands and 14 files unchanged, then captured/bound the registered 41-case command after feedback. | External runtime attestation and independently authenticated semantic criteria are unavailable. Only explicitly selected facts are covered. |
| U4 | Fresh collaboration context read installed diagnose/workflow resources, traced save and quote to the same faulty float converter, repaired that owner with Decimal in fixture commit `d2f1181`, and preserved the original requirement/check. RED observed `1.15 -> 114` and invalid overwrite; GREEN observed 115, valid zero/12.30 and unchanged saved bytes on rejection. Installed v3 bundle moved the actual feedback obligation from PARTIAL to READY_FOR_REVIEW. Authenticated 0.1.25 diagnosis repaired the same shared owner; a subsequent user-shaped maintenance complaint resolved default-command and binding gaps with 41 native cases and zero remaining local obligations. | Controlled repairs with an explicit follow-up needed in the native trial, not longitudinal prevention effectiveness. The environment checks registered prevention connections and changed evidence; semantic cause/coverage remains review work. |
| U5 | A fresh Agent created a small inventory UI without an existing standard, shared CSS/guide and actual desktop/mobile/browser state checks. Loading/error/retry, zero stock, search/filter and restock interaction were exercised. Main inspected screenshots and removed duplicated token values from the guide. A separate fresh-context follow-up reuses these standards for the related request screen. | UI review and its explicit intervention are distinct from numeric/browser assertions. Two authenticated native sessions now establish guide creation and fresh-context reuse; both inner Chrome launches failed, while the default restricted controller completed the real browser checks. Whole-product accessibility and fully autonomous host completion are not established. Explicit interventions and follow-up evidence are recorded above and below. |
| U6 | Product feedback/map connection and Harness cohort drift were repaired. Read-only/non-Harness counterexamples remain covered. A controlled duplicate check list was reduced from two to one invocation per normal/float-defect state, preserving identical raw observations and exits. Removing the unique negative-write assertion produced a demonstrated false green and was rejected. Scanner false positive was fixed without removing real docstring checks. Authenticated native maintenance also repaired the fixture runner and connected its real execution. The subsequent 0.1.30 maintenance task consolidated ten duplicate calls; independently replayed normal/six-defect comparisons preserved detection and old raw, with current installed lookup and workflow binding. | The duplicate experiment is a scoped fixture comparison, not evidence of general suite speed/cost improvement. No useful product test was deleted. |
| U7 | Real cached local Skills CLI installed/refreshed 19 Skill trees for temporary Codex/Claude targets; full tree comparison passed. Fresh v3 installed Harness CLI ran seven end-to-end cases successfully. Exact-repeat/no-op, user-byte preservation, rollback and failed-restore retention have executable regression coverage. Task records and bundle lookup support restart without replaying completed commands. The 0.1.25 updater persistently rebinds the native local marketplace and preserves unrelated config; authenticated TUI repair, lookup and native session resume now have actual tool/context evidence. | Remote update is unverified/unsupported for the local source. Actual guard termination between native registration and installation now resumes with byte-preserved recovery; interruption inside native file copy and autonomous whole-system acceptance remain unverified; 0.1.35 now repairs a controlled attributable partial-copy state through the native installer. A native repair needed follow-up for runner/evidence integration; protected acceptance stays BLOCKED. Outer-sandbox taskkill failed while the focused process-control-authorized check passed. General installations and operational environments were not changed. |

### Retained observations and limits

The final restart repair is committed as `b3d01d9`. A real child exited during review serialization and reproduced an orphan `.pending` file permanently blocking the next write. Begin/review now stage unique temporary files and replace only complete JSON. The workflow suite passed 14 tests; an additional actual child-exit check covers both first initialization and review resume. The latest 19-tree install/refresh (`install-resume.json`) then ran that interruption/restart case through its installed CLI (`installed-resume-native.json`, exit 0), and read the retained feedback/UI state as READY_FOR_REVIEW without rerunning their checks (`resume-installed-feedback.json`, `resume-installed-ui.json`). One writer owns each record; concurrent same-record writes and abrupt installer-process recovery are not established by this test.

Independent obligation review reproduced targetless UI/feedback requests silently losing their specific requirements and removal before first review losing a reconciliation target. Both were repaired, together with initial-survey source changes previously missing a verification obligation. The 13-case workflow suite passes, including explicit retirement/reassignment review and normal resume. These focused checks follow the 278-test run; that earlier Full result is not relabeled as a 280-test pass. A separate 19-Skill/17-Feature source crosswalk found four map/config command mismatches, repaired and independently rechecked at `b1b710c` (`map-review.md`). The repository audit snapshot before the restart repair had 17 current map reviews, no unmapped files or structural findings, and 10 remaining behavioral bundle obligations. Existing unittest results have not been relabeled as native JSON bundles; this audit remains PARTIAL. Native adapter/documentation checks passed 12 cases after the connection corrections.

- `u1/survey.md` and `labeler/.work/u1-map-final/` retain the donor identity, role/entrypoint survey, actual review CLI calls, partition state and acceptance refusal. The correction trial used a separately copied CLI under `install-host-u1-correction`; it is not a full installed-package receipt. Removing full source lists reduced the initial pending audit from 31,899 to 9,197 bytes for the same inventory; the later 3,818-byte audit also has fewer pending obligations. These are response sizes, not measured model-token savings. The original v2 installation was preserved.
- `install-v2.json` and `install-v3.json` identify actual installed trees. `installed-e2e-native.json` retains the seven-case subprocess exit 0; an earlier PowerShell redirection reported outer exit 1 despite unittest OK, so the native subprocess capture resolves that ambiguity. No remote-update PASS is inferred from the install script's generic success text.
- `install-final.json` records another full 19-tree install/local-source refresh after the obligation-review fixes. Its installed CLI resumed the existing Labeler state with two genuine map obligations and the existing feedback state with no remaining local obligations (`final-installed-labeler.json`, `final-installed-feedback.json`). Canonical/generated checks, distribution validation and `git diff --check` passed before the source commit.
- `install-host-v2/feedback-project/.work/feedback-evidence.md` retains literal behavior, installed-resource hashes, repair and unchanged assertions. `final-connected/` retains the preselected plan, actual raw/capture, semantic review, before/after obligations and read-only lookup. The configured task record was updated through the installed review CLI. `feedback-final-audit.json` remains local READY_FOR_REVIEW with enforcement BLOCKED.
- `install-host-v2/feedback-project/.work/u6/` retains eight real native invocations across duplicate/candidate/unique-coverage contrasts. Duplicate/candidate child-time sums were about 177/85 ms in each two-state comparison; this small local observation does not support a general performance claim. Source/requirements/original oracle and prior raw were preserved.
- `host-probe/process.json` records the fresh isolated CLI timeout/socket 10013; `enforcement-probe/` records actual same-authority mutation and refusal. Collaboration Agents reading installed paths are supervised installed-resource behavior, not proof of automatic CLI Skill discovery or a protected verifier.
- UI evidence is deliberately layered. Initial `install-host-v2/ui-project/evidence/WORKFLOW-RECORD.md` records installed-resource use and main's token-guide correction. The fresh request-screen follow-up implemented actual shared styling, navigation, search/filter, pending/processing/completed states and session reload, but initially read the ordinary Impeccable resource and omitted guide updates. That attempt is not claimed as final-installed-Skill proof. Main required a bounded final-installed-resource review and guide/PRODUCT/README correction, retaining the original report. Main also required browser cleanup in `finally`.
- `requests-ui-correction.json` records that actual final-installed-resource review and its hashes, corrected guide ownership and raw browser stdout. The correction used owned server PID 42576 on port 4174 and stopped it. Earlier port 4173 listeners were unrelated; no ownership/cleanup claim is made for them. This corrects the first Agent's overbroad server-removal statement without hiding it. The final snapshot's DESIGN/PRODUCT/README bytes match this corrected fixture.
- The final independent snapshot under `install-host-final/ui-project/` connects the corrected standards, registered browser command and UI obligation. An owned ephemeral loopback server and real Chrome produced the actual JSON observations in `.work/connected/raw.json`: request `REQ-1042` completed and remained completed after reload, mobile processing changed its state, both mobile widths were 390, error retry restored three rows, and the empty list was hidden. Main inspected desktop/mobile screenshots. One installed execution moved the obligation to READY_FOR_REVIEW; lookup executed zero tests and preserved 11 files. The first lookup wrapper decoded Windows output with the wrong encoding; only lookup encoding was corrected, with no test rerun. The owned server was closed in `finally` and no longer accepted the follow-up connection. Browser-process attestation remains outside this observation.
- `full-final.log` records **278 tests, one environment error** in the existing owned timeout-child cleanup case (`WinError 32`, taskkill failure). This is not Full PASS. The earlier scanner failure was repaired; no assertion or skip was weakened to conceal cleanup failure. Task-owned child lifetime is bounded, and unrelated processes were preserved.

No new provider, package service, universal policy framework, global hook or permission weakening was introduced. Routine deterministic paths use Python/PowerShell/Git/native/browser code without LLM calls. Semantic survey, repair, visual judgment and independent challenge use Agents with bounded context. Main interventions included distinguishing map completeness from runtime coverage, repairing viewer findings and removing duplicate guide tokens. User approvals were not requested for already authorized local work; the environment restrictions remain visible instead of being converted into success.

## T1-T6 implementation history and responsibility

- `authoring/skills/agent-workflow/SKILL.md` coordinates intent, selected procedures, relevant capabilities, evidence and unresolved work.
- `authoring/skills/setup-project-verification/SKILL.md` connects the first actual flow from existing product requirements and tools.
- `authoring/skills/maintain-project-verification/SKILL.md` owns product Feature/guide/command/UI drift, alongside the existing Harness mapping/cohort/retention owner when both are affected.
- Shared `authoring/references/project-verification.md` and `repair-and-reuse.md` are generated into self-contained Skill trees. Existing diagnose, UI capabilities, multi-agent review, capture and project adapters remain in use. Public catalog, inventory, Feature Map and active verification selector are updated together.
- `authoring/scripts/verification_results.py`, its generated installed copy and direct `scripts/verification_results.py` wrapper join selected checks, captures and raw assertions. The [input contract](../../authoring/references/result-viewer.md) defines producer bindings and current-condition limits. Live Git identity is checked with fixed read-only commands; recorded commands are never executed during lookup.

Source/generated distribution is distinct from temporary installation, product execution, actual Agent selection and operational application. No ordinary installation, global settings, original Labeler files/refs/DB, protected branch, push, deployment or remote migration is changed.

## Independent target and host

New evidence root: `.work/agent-workflow-pilot-20261005/`. These are temporary retained records; if removed, this document remains a historical summary, not reproducible raw evidence.

`export.json` identifies the independent `git archive` export from the previous isolated Labeler commit `ecd7db768aef3c17c0ffc9834759944cf013b0f0`. It contains 319 safe tracked files and no shared Git/origin, original database, dependencies or uncommitted files. `t1-fixture.json` records removal of only the new copy's previous pilot guide/routing/selectors, retaining original product requirements, native tests and drivers. Existing pilot/raw records remain unchanged.

Initial npm registry access failed with `EACCES` (owned `npm-cache/_logs/2026-10-05T03_01_55_340Z-debug-0.log`). A narrowly authorized `npm ci --cache ../npm-cache --no-audit --no-fund --fetch-retries=0` installed 331 packages from the lockfile. Local Skills CLI installation then verified 19 Skill trees for the temporary Codex/Claude project roots (`install-local.json`). No dependencies were copied from the original product.

`host-discovery/captures/03-app-server/` preserves fresh Codex 0.160.0 initialize and skills/list requests/responses. All three new Skills are enabled at the temporary project's `.agents/skills` paths. This is host discovery evidence only. The one empty task-local CODEX_HOME CLI model probe encountered Responses socket error 10013 and timed out after 60 seconds (`04-exec-startup-probe/`); CLI model behavior remains **BLOCKED**. No credential copy, provider/model change or sandbox bypass was used. Actual task evaluations use separate collaboration-host contexts, installed-resource reads and retained commands/raw outputs; that fallback is reported separately.

## Acceptance tasks

| Task | Actual short request and outcome | Evidence and limit |
| --- | --- | --- |
| T1 | First connection completed from unconnected task-local state; product guide, map and selectors committed as `8e844f3` | `t1-fixture.json`, `t1/`; 29 native assertions and 12 browser checks, separately produced DB readback |
| T2 | Existing connection reused for actual product save verification; separate context performed read-only existing-result lookup | `t2/`, `t2-lookup/agent/`; browser/native/DB historical observations preserved, current reuse blocked by changed source and missing condition identity |
| T3 | Controlled +1 serialization defect reproduced; source/prevention `f372ad7`; fresh independent checks passed, reviewer-requested bundle coverage added as `ac6c2f1` | `t3/`, `t3-fix/`, `t3-independent/`, `t3-bundle/`; original product untouched; backend 29 PASS did not catch the browser defect |
| T4 | Both product and Harness maintenance selected, repaired and rechecked; commit `869f997`; audit-only and non-Harness counterexamples performed | `t4/`, `t4-repair/`, `t4-non-harness/`; missing selector resolved, 21 baseline Harness unmapped findings remain explicit |
| T5 | Shared UI repair and guide/active command connection completed; fresh-context category reuse committed `2323dbd`, including a discovered initial-load defect | `t5-red-run.json`, `t5-fix/`: 18 desktop/mobile checks and 3 native cases; `t5-reuse/`: 15 browser checks, 4 native cases and 8 independent empty/error/retry observations |
| T6 | Source/distribution/install and independent value review completed; four reproduced viewer findings repaired and independently rechecked, including a valid PASS neighbor | `source-final-unit-check.json`: 45 tests; corrected viewer 18 tests; install contract 18 tests; real install `install-review-final.json`; one unrelated timeout-cleanup check remains failing |

### Observations and producer links

The task prompts below did not name Skills, their invocation order or a correct source patch. Separate evaluation envelopes specified the isolated target, available installed-resource root, output ownership, forbidden effects and existing runtime/raw locations. Main provided bounded infrastructure handoffs and requested missing producer captures; this is supervised collaboration-host evidence, not a claim of unattended CLI autonomy.

| Task/context | Short user request | Actual installed selection / retained trace |
| --- | --- | --- |
| T1 `/root/t1_setup` | 이 프로젝트의 검증 체계를 마련하고 첫 실제 상품 저장 흐름을 확인해줘. | Installed setup responsibility, project docs/commands; `t1/request.md`, `installed-skill-resources.json`, `commands-and-runs.json` |
| T2 `/root/t2_verify` | 상품 저장 기능을 검증하고 무엇을 확인했는지 보여줘. | Existing installed/project verification paths; `t2/verification-plan.md`, `implementation-identity.md`, capture/raw files |
| T2 `/root/lookup`, fresh | 기존 결과만 보여줘. | Installed agent-workflow viewer; `t2-lookup/agent/existing-results.md`, exact native output/correction beside it |
| T3 `/root/t3_feedback`, then fresh `/root/t3_independent` | 입력 가격과 저장 가격이 달라. 원인을 추적하고 재발하지 않게 고쳐줘. | Workflow/diagnose/project capabilities; `t3-fix/fix-record.md`; verifier received requirement/base/diff/target/raw rather than implementer verdict; `t3-independent/independent-report.md` |
| T4 `/root/t4_audit`, then fresh `/root/t4_repair` | 개발 체계를 점검만 해줘. 수정하거나 검사를 실행하지 말고 문제와 근거만 보여줘. / 개발 체계를 점검하고 필요한 부분을 개선해줘. | Both product and Harness responsibilities; unchanged audit hashes in `t4/`; repair commands/diff in `t4-repair/`; reused-context non-Harness contrast in `t4-non-harness/` |
| T5 `/root/t5_ui` | 상품 화면의 작은 아이콘 버튼들을 UI 기준에 맞추고 다음 화면에서도 재사용할 수 있게 고쳐줘. | Independent `ui-repo`; temporary install and owned runtime under `t5-runtime/`; shared repair `04c9a21` and connection `5171806` |
| T5 `/root/t5_reuse`, fresh | 분류 관리 대화상자도 같은 UI 기준으로 점검하고 필요한 부분을 맞춰줘. | Fresh `reuse-host` installation, updated shared guide and existing CSS owners; `t5-reuse/evidence.md` records installed resource hashes, commands, raw and corrections |
| T6 `/root/t6_review`, fresh | 검증의 중복과 빈틈을 점검하고, 안전하게 줄일 수 있는 것과 유지할 것을 알려줘. | Installed resource discovery and independent probes; `t6-review/report.md`, `final-recheck-20261005-02/` |

- T1 browser run `022b9cd5-5025-47e4-acce-2a19ca72d6a4` produced `t1/browser-product-20261005T121500/observed.json`. Native run `033a9886-9b66-4c27-b4d4-387e697ec0f8` reported 29 passed, zero skipped. DB readback run `28f6a1ae-442f-4729-8d2a-10b8c9f43e51` includes generating argv/cwd, original browser run/hash, local DB path and product ID.
- T2 browser run `24a48318-8bb0-4a1f-a3f3-3c024ccdd48c` observed entered 3200, reload 3200, edit 3500/version 2, stale 409, incomplete bundle 400 without mutation, and mobile containment. Native run `e19d735b-35cd-4914-ad36-ffba1756b3df` passed 29 assertions. DB run `f84349f0-51fa-41f5-a004-f5c339d8c536` links that browser product to `[2, box, 3500, 350000]` in the new local DB. These are synthetic/local observations, not authenticated production evidence.
- T3 RED browser `068f805c-242f-4b05-a178-12f0864e19a1` observed `3201 !== 3200`; native mutant run `311441b6-79f3-46b0-b4aa-d729524c2856` still passed 29. The implementation agent added a focused serializer regression, observed RED `31a2d258-67ed-4f87-9c7a-78b492973411`, then GREEN `190e5708-4a87-4f5a-88e5-bef444b0916a`. The caller uses the repaired serializer; the Feature selector includes it. Browser GREEN `c093a5fe-ebc1-45bc-8590-02888eda8126` and new DB readback `a76bcfd0-1401-4f7d-822a-8d887da16bd0` preserve the same price/quantity/rejection criteria. Product typecheck/build/focused lint passed; full lint reported 1,471 errors outside the changed source, so whole-project lint is not claimed clean.
- T4 repair restored a missing `product-save` row and `client` selector, replaced a dead guide command and removed the selector for an actually removed synthetic preview command. Before/after Harness audit runs `765c3848-7e81-49ad-bfa4-0466c15cc68c` / `f3b038d7-bf6b-4f08-9e28-4824e885758e` changed 22 findings to the same 21 baseline findings. The repaired native adapter ran 29 cases; the restored client selector ran 48 Vitest cases plus 56 package pretests. Historical removed-feature raw remains separate. Audit-only tracked-file hashes are unchanged. In the non-Harness fixture, the agent reused the direct guide, excluded Harness maintenance and strengthened an accidentally ASCII-only Unicode test; baseline and strengthened versions both passed 2 cases. That is test-strengthening evidence, not defect RED/GREEN or a fresh-context claim.

### Lookup and verification limits

The T2 machine plan is explicitly a retrospective index of retained criteria and raw, not a newly claimed pre-execution frozen plan. The fresh lookup context used the installed viewer and did not rerun tests or start a service. Historical PASS and current STALE/UNKNOWN remain distinct; dependency/fixture/current-runtime identity was not retroactively invented.

Main verified all 34 T2 original files unchanged (`t2-lookup/evidence-after.json`). The lookup agent initially reported an outer shell exit 1; direct subprocess capture confirms the viewer's native exit is 2 for BLOCKED (`native-viewer-execution.json`). The original report is retained with a separate correction. Actual native negative runs `12725ef3-073e-41ed-9f1b-d94abb0a0635` (zero) and `41e91c43-aaa3-4911-b6ac-2818343f3f47` (two required skips) both returned native exit 0 / `success: true`. The viewer rejects their raw counts, and a subsequent read-only Agent request identified the misleading summaries. Wrong-target, missing-raw and changed-criteria lookups are retained under `t2-negative/`; no original record or product criterion was weakened.

Main review of the first viewer implementation found false current PASS from copied historical context and `not_applicable` identity groups. Main rejected those claims, preserved the original files under `.work/agent-workflow-viewer/20261005T-viewer/`, and added `main-review-invalidation.md`. Focused RED/GREEN records cover native exit/zero/raw mismatch, live source changes, missing identity, coexisting ISSUES/BLOCKED and required exclusions. The separate T6 reviewer then reproduced omitted raw aggregate ISSUES, inconsistent criterion revision and duplicate logical IDs. Main RED `b8fb2b6f-1204-495a-b638-87ca0abac333` and GREEN `8b4a4ddf-f459-4091-b390-0a49831a820c` cover all 17 viewer regressions; source/generated/docs were committed `7e9eb8d`. The same reviewer rechecked a fresh actual install under `t6-review/final-recheck-20261005-02/`: three negatives reject false PASS and the synchronized unique valid neighbor still returns PASS. The installed viewer hash matches generated `d5f932fc682c4b386a55d07bef605dd7269436f1126a038c278edb43e9b54ffb`. These probes use synthetic editable captures, not real runtime attestation.

T3's independent candidate browser/native/DB records are bound to committed `f372ad7`, closing the earlier dirty-source boundary. The reviewer found no remaining +1 source defect but identified missing valid-bundle browser/DB coverage. Additive checker/readback scripts, map and selectors were added in `ac6c2f1`; original frozen driver/raw stayed unchanged. Browser run `171e614c-8110-453d-9931-25d13bf6f97a` observed single `[2, box, 3200]` and bundle `[5, box, 8750]` in submitted API payload, saved response and fresh GET. DB producer run `db7e0943-4a5b-4cbe-b4e9-b424de050687` observes the same explicit product ID with minor amounts 320000/875000. Main inspected those raw values and links. Independent OS process/port ownership queries were denied; runtime identity remains launch-handoff plus served-source doctor evidence, not OS attestation.

Main then caught a stale default origin and an extension-only command entry in that follow-up. Product commit `c2439ed` now reads the isolated runtime configuration, creates a unique artifact and wires `product-save-browser` into an active selector/impact rule. Its actual default-command browser run `3b61699a-dad8-4e4d-8dab-d265bdf9d2d2` passed 7 checks at committed `c2439ed`; DB producer `5a673163-9ee9-484e-89eb-f8e3bba01452` binds the emitted artifact, browser run/hash and product `76b3c917-6a78-4338-9635-dc49f7dabadd` to both persisted offers. Exact commands and hashes are in `t3-bundle/bundle-record.md`; the first follow-up was not silently treated as complete.

The fourth T6 finding, missing selection explanations, was also repaired: every selected/excluded/not-required disposition now requires a nonblank string reason. `t6-review/reason-red.json` preserves the reproduced acceptance and missing diagnostic; the first GREEN attempt exposed an incorrect test access to `error` instead of the existing `remaining` diagnostics. That test was corrected without weakening the expected rejection. `reason-green-02.json` (`051312ab-669e-4e56-85c0-0a0c008f5a34`) passes 18 viewer tests, including the existing valid PASS neighbor. Earlier reviewer hashes identify their earlier installed version; they are not presented as the final source hash.

Fresh install `t6-review/final-all-findings/install-final.json` compared all 19 Skill trees. The independent reviewer reran the three negatives, valid PASS neighbor and six missing/blank reason probes against installed viewer SHA-256 `9bf7f2a61a94851b4558b7d60fbf8dffc917edc027170822effedac582dde015`, which main confirmed matches generated source. All invalid cases were rejected and the valid neighbor remained reusable. `final-all-findings/report.md` and `probe-results.json` retain actual commands and outputs. A subsequent contract wording clarification did not change that executable; these remain synthetic consistency probes, not product execution.

T5 uses a separate `ui-repo` export and synthetic local DB on port 4395. The unseeded first attempt was BLOCKED, then the existing product flow seeded a synthetic category/product and the UI baseline passed 18 checks. The isolated 28px control fault failed the unchanged observer; `04c9a21` repairs the shared CSS owner to the existing 44px standard with a flex shrink guard. The first Agent pass omitted durable guide/map/command updates. Main identified a routing gap and connected the UI entrypoint to the existing canonical repair/reuse reference instead of duplicating its rules. The literal prompt is preserved in `t5-fix/request-literal.md`; the first agent record paraphrased the discovered size as if part of the request. Supervised follow-up `5171806` connects the UI guide, Feature map, native selector and actual browser launcher. Browser run `be0bd910-a89f-4e92-8f14-b66c7b4efe21` uses the configured origin and unique artifact, passes 18 checks, and records CSS hash `2bc066f17ecb1454aea4f7a4a7ea5bc588663548d2420fc2ab0e8c73d1e50c61`. Exact commands and hashes are retained in `t5-fix/record.md` and raw. Main visually inspected the desktop/mobile evidence and settled mobile-open screenshot; a post-interaction scrolled screenshot alone did not show the close control. The 3 native cases cover focus/checkbox assertions, not CSS geometry.

The UI installation update failed during Harness cohort replacement with WinError 5 and reported rollback; it is not claimed as a complete final installation. `install-ui-reuse-failure.md` preserves the boundary. A separate new `reuse-host` install passed full 19-tree comparison (`install-reuse-host.json`). The fresh UI follow-up used that exact installation and a short category-dialog request, without the earlier patch or long UI instructions. No ordinary installation or permissions were changed.

That fresh context reused the updated UI guide and existing styles, repaired category control dimensions and Enter/Space selection, and connected the Feature, guide and active browser command in `2323dbd`. Main review rejected duplicate CSS overrides and new implementation-mirroring static assertions. It also required investigating the observed first-open empty tree rather than hiding it with an observer wait. `t5-reuse/delayed-before-fix/observed.json` reproduces a real delayed API response leaving the open editor empty. The final App loading/error boundary mounts the editor after a successful query; an intermediate broad prop-resynchronization effect was rejected because it could overwrite locally owned optimistic editing/undo state. Intermediate evidence remains retained.

Final active browser run `3378c564-5abc-4543-ae45-c6eb6b27a7c7` passed 15 checks, including delayed real API 200 / 2 returned rows / tree 0 → 2, 1440px and 390px geometry, Enter/Space selection, containment and Escape focus restoration. Native run `3064c7e5-9603-4d97-8e1e-c111714fa5b6` passed 4 cases; installed Node entrypoints passed typecheck, build and focused lint after the original npm subprocess transport failed. `t5-reuse/evidence.md` links exact commands and raw; `green-active-final/observed.json` retains the observations. Main inspected desktop/mobile screenshots and separately ran committed `2323dbd` through 8 boundary observations (`main-boundaries-run.json`, run `1e4de487-3868-45b0-9c73-fa10253599d7`): loaded empty data allows initial creation, a controlled 503 shows an error, actual local API retry returns and displays 2 rows, and focus returns on close. Empty/error responses are browser-local transport fixtures, not claims about an empty real DB; retry uses the actual local API. Before/after source hashes are unchanged. These checks do not claim complete keyboard tree navigation or whole-application accessibility coverage.

The owned product/UI runtime parents were stopped only after matching their recorded PID, process name and launch time (`product-server-cleanup.json`, `ui-server-cleanup.json`). This establishes exact parent cleanup, not independent process-tree attestation. The UI copy's pre-existing untracked `skills-lock.json` remains preserved. Original pilot files and raw were not rewritten.

The existing `test_timeout_stops_owned_child_activity_and_preserves_unrelated_process` failed in a broad distribution invocation and again in a focused run (`timeout-cleanup-recheck.json`): Windows tree cleanup returned 1, followed by temporary-directory WinError 32. Its capture/test source is unchanged from `aa53687`; no successful baseline execution was established in this session. Do not label it a clean baseline or a passing suite. Resume by reproducing owned-process cleanup in a host that supports the required process-tree operation; do not weaken its assertion. The changed viewer tests and packaging checks passed independently.

## Retained and excluded capabilities

The donor setup capability was narrowed to first connection. UI-refine is absorbed by the UI procedure and existing UI capabilities; improve-workflow by cause ownership/diagnose/product maintenance; resume-work by existing Git/Harness state recovery. Clear-writing has no acceptance task here and is excluded. No public Plugin/MCP/dashboard/central database, automatic full fan-out, cron or Stop-loop is introduced. Direct native CLI/CI paths remain available.

Existing capture regressions for zero/skip/stale/wrong-target/report handling remain useful. Backend/native assertions and the browser flow catch different failures; neither replaces the other. Static option/label/class checks are candidates for review, but no equivalent defect and valid-case evidence yet justifies deleting them. Test-count reduction, long-term reliability, cost or speed improvement are not claimed.

## Delivery and remaining verification

| Layer | Delivered evidence | Limit |
| --- | --- | --- |
| Management source/generated | `c7c064a`, `7e9eb8d`, `95eed81`; viewer 18 focused tests, workflow packaging 22 tests, final distribution and resource-drift checks | Packaging is not proof of Agent behavior; whole distribution suite is not claimed green |
| Temporary installation | Fresh 19-Skill tree comparisons, app-server discovery, final viewer independent install and UI reuse-host install | Existing UI-root update failed; ordinary user installation is unchanged |
| Local product behavior | New isolated browser/native/DB captures; actual price defect RED/GREEN and valid bundle readback | Synthetic local data; original Labeler and production are untouched |
| Agent behavior | Short requests in collaboration contexts with actual installed-resource reads, tools, diffs and raw links | Supervised handoffs/corrections occurred; independent CLI model execution remains BLOCKED |
| Real-environment application | None | General install, protected integration, providers, push, publish and deployment were not authorized |

Resume the CLI task only when this host can execute a task-local model request through its existing authorized configuration without socket10013; do not infer that discovery alone suffices. Reproduce the unchanged timeout child-cleanup failure on a host where owned process-tree handling can be inspected; the underlying cause is not conclusively separated from host permissions. For a current-reusable product PASS, capture a new preselected plan and measured source/criteria/command/dependency/fixture/runtime identities with the new run instead of backfilling T2's missing historical identities. Existing source/criteria/zero/skip negatives remain binding. The failed in-place temporary update requires a separate controlled reproduction before claiming that update path works; fresh installation is the observed fallback. None of these limits authorizes global configuration or permission changes.

## Requirement status

R01–R16 are the acceptance criteria in the [requirements review](agent-coding-requirements-review.md). The table distinguishes implemented responsibility and bounded observation from general effectiveness. It does not upgrade the old design-review verdicts into production acceptance.

| Requirement | Status within this pilot | Current implementation / observed evidence | Remaining scope |
| --- | --- | --- | --- |
| R01 Existing assets and missing responsibilities | Observed within scope | Three responsibility entrypoints share canonical references; reuse Harness, diagnose, UI, native capture/adapters and direct CLI; real temporary install | No comparative efficiency or universal superiority claim |
| R02 Candidate and responsibility decisions | Observed within scope | Workflow procedures absorb UI-refine/improve-workflow/resume-work responsibilities; domain/boundary ownership is explicit; no automation service added | Automation remains intentionally excluded because no authorized recurring trigger is needed |
| R03 Natural request selection and composition | PARTIAL / BLOCKED | Actual collaboration contexts discovered installed resources; T1 setup, T2 verify/lookup, T3 diagnose, T4 both maintain responsibilities | CLI model task execution BLOCKED by Responses socket10013; no claim of automatic invocation across every host |
| R04 Feature lifecycle | Observed within scope | T1 creates product-save connection; T3 adds caller regression to map/active selector in one commit; T4 repairs new-connection omission, deleted-command residue and dead guide | Synthetic lifecycle contrasts; initial product map still excludes design/print flows and is not exhaustive |
| R05 Business and architecture | Observed within scope | Actual ProductForm submit → API validation/worker → D1 → fresh read observed; backend-only false negative demonstrated; existing state/data owners retained; reviewer-requested valid bundle path added and observed | No whole-system architecture proof |
| R06 Result consumption and current reuse | PARTIAL / BLOCKED | Direct/generated viewer with check/criterion/run/raw/producer identity; historical observations separated from current STALE/UNKNOWN; new DB producer links retained | Project-authored criteria and external condition identity are not authenticated; T2 lacks sufficient current identities, correctly BLOCKED |
| R07 Meaningful verification and failure | Observed within scope | Actual normal/+1 defect comparison; real Vitest zero and required-skip controls reject misleading success; wrong-target/missing-raw/stale controls; focused viewer RED/GREEN | Existing process-tree cleanup test fails in this environment; no blanket distribution-suite PASS |
| R08 Independent review and repair | Observed within scope | Fresh T3 verifier inspected requirement/diff/target/raw and independently ran native/browser/DB; requested bundle gap repaired; separate T6 reviewer identified four viewer findings, main repaired, same reviewer rechecked fresh installed copy and valid neighbor | Collaboration traces are not signed identity attestation |
| R09 Feedback to reusable improvement | Observed within scope | Serializer-owner correction and active regression; shared UI guide/implementation consumed by a fresh later context; discovered loading defect added to reusable browser command | Supervised review corrections occurred; no longitudinal recurrence measurement |
| R10 Appropriate prevention | Observed within scope | Real serialization code correction plus focused regression; original frozen browser assertions unchanged; existing native boundary cases retained | Controlled defect only; no claim that original Labeler contained this bug |
| R11 Shared UI standards and reuse | Observed within scope | Existing common styles repaired, guide/map/command connected; fresh short category request reused them; desktop/mobile, selection, delayed load, empty/error/retry observed | Bounded local screens/states; no whole-product visual or accessibility claim |
| R12 Product and Harness maintenance | Observed within scope | T4 actually repaired both responsibilities and reran them; audit-only hash preservation and non-Harness direct-command counterexample | 21 pre-existing unmapped Harness findings remain visible; no whole-project maintenance-clean claim |
| R13 Verification value | Observed within scope | Native/browser catch different defects; serializer/cheap deterministic checks retained; static assertions reviewed as candidates | No justified deletion or measured test-time saving; do not reduce counts without equivalent defect and normal-case evidence |
| R14 Boundary and distribution architecture | Observed within scope | Project owns business meaning and native reports; shared runner captures facts; viewer reads; Skills select; canonical/generated and direct CLI preserved | No new universal Domain framework, Plugin, registry database or runtime attestation service |
| R15 Actual delivery and layered evidence | PARTIAL / BLOCKED | Source commits `c7c064a`, `7e9eb8d`, `95eed81`; real local Skill installation/discovery; T1–T6 collaboration tasks and local product/browser/DB observations | Overall delegation system remains PARTIAL/BLOCKED for CLI host behavior and current-reuse/update/cleanup limits above; no speed/cost claim |
| R16 History, isolation and constraints | Observed within scope | New independent tracked exports, synthetic DB only, old raw preserved, copied-current false PASS explicitly invalidated, no general install/original/remote changes | `.work` follows retention and is not permanent archival proof; real-environment application was not authorized |


## U1 shared map connection repair, 2026-10-06

The isolated Labeler fixture at `38296e5` declared requirements/source references
for all eleven Features, but none of their `map` lists included the actual
`docs/feature-map.md`. The runtime inventory caught the document only as a
`repository-runtime` source. Changing the guest/local-preview meaning therefore
left its prior semantic review valid. This was a project connection defect;
the existing runtime already invalidates declared map dependencies.

Fixture commit `3a8e7ba` connects the shared map to all eleven Features and distinguishes
anonymous in-memory browsing from role-specific local sessions with D1/R2
persistence. The Agent checked `App.LocalRoleEntry`, `GuestApp`, `localAccess`
and the existing account setup instructions; no product server/provider was
run. The map also identifies its source/requirements revision and separates
historical mapping readiness from current product evidence. It no longer calls
translation quality or catalog completeness a map-partition blocker.

Actual installed 0.1.32 CLI evidence is retained under
`.work/plugin-transition/u1-semantic-repair-v032/`. Before connecting the map,
the changed guest row still reported `reviewed=true` and `mapping_ready=true`.
After connection, every Feature had a `map_review` obligation and no valid
review; inventory/configuration had no unmapped, unlinked or structural findings.
These are observed obligation transitions, not a product behavior PASS. Old
review records are preserved; no new semantic approval is fabricated. The
fixture's current mapping remains PARTIAL pending fresh review of the linked
requirements/flows. Its two product-quality findings remain separate.

A whole-file shared dependency deliberately reopens all eleven reviews even for
one changed row. That review burden remains a limitation; no section parser,
additional model call or per-row registry was added. The installed audit itself
calls no model or product check. No source/runtime/generated resource changed,
so no new package version or installation was needed. Original Labeler, the
ordinary installation and global configuration remain unchanged. U5's separate
native UI trial still awaits trust approval for its nested Git repository;
unelevated sandbox approval is already in effect and is not that folder trust.

Validation: the installed audit retained the old review bytes and all 318
unrelated tracked fixture files unchanged. Repository documentation/cutover
checks passed 12 tests; both diffs passed `git diff --check`. The bounded
independent crosswalk is retained at
`.work/plugin-transition/u1-semantic-crosswalk-v032/crosswalk.md`; its remaining
reference/flow review suggestions are not claimed implemented by this unit.


## U1 semantic references and current review, 2026-10-06

Fixture commit `463d80b` connects all eleven map entries to existing requirement
sections, API/script variants, shared owners, persistence/external effects and
related Features. It distinguishes method registration from fresh evidence and
marks product execution unverified throughout this survey. No new command
registry, runtime or generated resource was added. A bounded independent review
checked relative links and representative routes/sections; main review corrected
punctuation and an operator paid-guard overstatement against `entitlements.ts`.
Operator identity/role guards are distinct from customer entitlement gating.

The actual installed 0.1.32 CLI registered eleven explicit semantic reviews
against the new input bases, then a read-only repeat returned the same result
without changing state. `mapping_status=READY_FOR_REVIEW`, eleven current map
reviews, no structural/unmapped/unlinked findings; overall status remains
PARTIAL with the two preserved product findings. The inherited baseline predates
separate `verification_bases`, so its conservative legacy fallback retains
execution obligations; it was not reset or retroactively exempted to clear them.
This is editable local review, not authenticated/protected acceptance. No product
test, provider call or model call was made by the CLI operations.

Evidence: `.work/plugin-transition/u1-semantic-completion-v032/` retains the
before snapshot, explicit proposals, individual review records, actual CLI argv,
final audit, independent-review resolutions and integrity comparison. All 319
unrelated tracked fixture files and the prior review record remained unchanged.
The map's whole-document dependency still reopens eleven semantic reviews for a
one-row edit; no token or review-cost reduction is claimed. U1 mapping work for
this observed snapshot is now reviewed; full U1-U7 task and protected acceptance
remain incomplete, and the pending native UI trial was not granted new trust.
