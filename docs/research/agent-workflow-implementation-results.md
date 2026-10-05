# Agent workflow implementation and acceptance

Execution began 2026-10-05 on `wp-20261004-agent-coding-foundation` at `aa536876fb9f8922e0cade072469ddc9a51267df`, with a clean worktree. This implements the [execution prompt](agent-coding-next-session.md); the prior review-only restriction does not apply to this authorized implementation. Source/distribution `c7c064a`, viewer soundness repairs `7e9eb8d`, and UI reuse/selection-reason follow-up `95eed81` are committed. T1–T6 were performed within the independent pilot. The whole delegation system remains PARTIAL/BLOCKED for the host and evidence limits below.

Subsequent user requirements are specified in the [completion design](agent-workflow-completion-design.md): all-feature initial mapping with partition/resume, mandatory map updates, Agent judgment versus enforced environmental boundaries, and demonstrated task benefit. The U1-U7 implementation below now reports against those criteria; T1-T6 remain earlier, separately bounded evidence. In particular, R04/R12 and T1 below establish bounded first-flow/lifecycle behavior; they do not satisfy complete initial mapping or non-bypassable enforcement. Labeler remains the test environment for plugin capabilities, not the product-development objective.

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
The current local audit still conflates these product gaps with map-review
findings; separating those outcomes remains implementation work. Original
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
| U1 | Executable partitioned obligations; Git fixtures cover full API/CLI inventory, unconnected coverage, addition/deletion, shared criteria/command changes, stale/duplicate review and resume. Independent Labeler survey exported 319 safe tracked donor files, created 11 functional areas including roles/API/CLI/webhooks/recovery and retained the map in local fixture commit `c770500`. Nine areas locally reviewed; translation quality and catalog completeness remain unresolved. | Full semantic initial-map acceptance is PARTIAL for those two real gaps. File coverage (`unmapped=0`) is not proof of semantic completeness. Labeler runtime/provider/print acceptance was not executed in this survey. |
| U2 | Same-authority child probe actually changed a task-local policy and wrote forged success; `accept` still refused protected acceptance. Configured local close rejects unresolved obligations and submitted success. Normal edits and native runs remain available. | Protected policy, verifier identity, result authority and bypass-resistant acceptance are BLOCKED. CLI model startup encountered Responses socket error 10013. No unsupported security promise is made. |
| U3 | Actual child runs produce current native facts, captures and bundles; zero/skip/missing/stale/changed-criterion cases reject reuse. Fresh installed v3 executed the price save/read/quote check once and then queried the bundle with zero test executions and 12 retained files unchanged. | External runtime attestation and independently authenticated semantic criteria are unavailable. Only explicitly selected facts are covered. |
| U4 | Fresh collaboration context read installed diagnose/workflow resources, traced save and quote to the same faulty float converter, repaired that owner with Decimal in fixture commit `d2f1181`, and preserved the original requirement/check. RED observed `1.15 -> 114` and invalid overwrite; GREEN observed 115, valid zero/12.30 and unchanged saved bytes on rejection. Installed v3 bundle moved the actual feedback obligation from PARTIAL to READY_FOR_REVIEW. | One controlled repair, not longitudinal prevention effectiveness. The environment checks registered prevention connections and changed evidence; semantic cause/coverage remains review work. |
| U5 | A fresh Agent created a small inventory UI without an existing standard, shared CSS/guide and actual desktop/mobile/browser state checks. Loading/error/retry, zero stock, search/filter and restock interaction were exercised. Main inspected screenshots and removed duplicated token values from the guide. A separate fresh-context follow-up reuses these standards for the related request screen. | UI review and its explicit intervention are distinct from numeric/browser assertions. Whole-product accessibility and authenticated host behavior are not established. Follow-up evidence is recorded below. |
| U6 | Product feedback/map connection and Harness cohort drift were repaired. Read-only/non-Harness counterexamples remain covered. A controlled duplicate check list was reduced from two to one invocation per normal/float-defect state, preserving identical raw observations and exits. Removing the unique negative-write assertion produced a demonstrated false green and was rejected. Scanner false positive was fixed without removing real docstring checks. | The duplicate experiment is a scoped fixture comparison, not evidence of general suite speed/cost improvement. No useful product test was deleted. |
| U7 | Real cached local Skills CLI installed/refreshed 19 Skill trees for temporary Codex/Claude targets; full tree comparison passed. Fresh v3 installed Harness CLI ran seven end-to-end cases successfully. Exact-repeat/no-op, user-byte preservation, rollback and failed-restore retention have executable regression coverage. Task records and bundle lookup support restart without replaying completed commands. | Remote update is unverified/unsupported for the local source. Abrupt process-death install recovery, reliable Windows descendant cleanup and autonomous CLI model behavior remain unverified/BLOCKED. General installations and operational environments were not changed. |

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
