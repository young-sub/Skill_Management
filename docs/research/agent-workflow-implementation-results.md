# Agent workflow implementation and acceptance

<a id="continuous-plugin-improvement-2026-10-13"></a>

## Continuous improvement: source and actual product, 2026-10-13

The user applied the complete [continuous execution request](plugin-continuous-improvement-next-session.md).
Current plugin base was clean main `107850a`, 106 commits ahead of fetched
origin/main with no remote-only commits. Yeondoo Link was clean on
`evaluation/plugin-ui-20261012` at `bd03682`; its separate candidate worktree
remained at `e1b8a09`. Product main and fetched origin/main both were `220c945`.
Both existing product branches/worktrees are preserved.

The actual nested-worktree regression reproduced `ValueError` while converting
an outer Git ancestor into a root-relative nested repository. The canonical
`static_inventory` now restricts candidate probes to descendants of the requested
root. A real nested worktree confirms no outside-root Git probes; a real child
repository in a non-Git survey remains discoverable. Existing Git enumeration,
private/ignored-file exclusions and nested-boundary validation are unchanged.
Setup, CLI maintenance and cutover passed 57 tests; repository docs and installed
CLI acceptance passed 10 tests. Resource drift, distribution and formatting checks
passed. Raw RED/GREEN is retained under `.work/plugin-continuous/20261012/`.

This repairs the common source cause previously avoided by moving the worktree.
It does not alone complete direction §13. The subsequent units below connect
the actual product, measure candidate scale and exercise independent consumption;
native host acceptance remains a separate boundary; local-main delivery is recorded below. Baseline 0.1.48 was built from unchanged main
into a fresh path in that same temporary evidence root; no installation changed.

### Six outcomes and current completion boundary

| User outcome | Observed local implementation and evidence | Remaining boundary |
| --- | --- | --- |
| Task handoff and selected lookup at retained-history scale | Root-confined inventory; eight hook preview reads with exact independent selection; 32/128/512-record measurements; real product discovery and read-only lookup/resume invariance | Final 0.1.57 independent lookup at6289ea0 confirms thirteen current PASS/REUSABLE rows across seven consumers, zero producers, 163 unchanged named task/evidence inputs and 247 unchanged package files. Six Feature reviews are current. Seventeen broader coverage gaps remain; the final lookup took215.984s. Native hook acceptance is unobserved. |
| Business/architecture across FE, BE/API and Domain | Twelve actual MVP candidates mapped; consultation App dispatch, transition, memory/display and edit invalidation traced. Independent browser/API/SQLite/restart example retains frontend-failure/API-PASS contrast. | Current scoped reviews cover consultation, staff, comparison/purchase, privacy, runtime and verification connection. Requested Feature FE/Domain business/architecture rows PASS; BE/API N/A is reasoned for the memory-only consultation. The local device lock is not server authentication. Other project reviews remain open; provider generation APIs elsewhere are separate. No clinical, commercial or whole-product approval. |
| Repair and prevent feedback recurrence | Original adapter failures retained; descriptor/VM consumers repaired without changing browser conditions; real Git metadata and retired manifest/image observer guards; bound red preimage for new tool owners | Independent lookup caught an unregistered pointer in new image feedback; root corrected its linkage to the existing whole-report assertion, retaining raw, source, registry and baseline. A separate fresh follow-up confirms loader, app-runtime manifest and image feedback RESOLVED. The original misrouted staff entry stays OPEN. Local review does not authenticate human approval. |
| Maintain and reuse UI standards | Existing design guide, tokens and shared components/consumer links reused; six original suites, actual desktop/mobile/staff screenshots retained | Related staff screen review and focused privacy end/cancel/reset review are observed; UI remains draft. Staff owner architecture is reviewed using unchanged source and retained actual flow. CatalogImport is mapped but its modal is outside the six-suite run. |
| Executable verification guide and runtime connection | Actual clean6289ea0 execution through frozen0.1.57 binds thirteen judgments to three commands: native55/55, existing reporter9/9 and all six original browser suites PASS; 13 served-source matches, 120 PNG hashes and owned-resource shutdown | Seventeen broader coverage gaps and the original misrouted feedback remain. Earlier failures/checkpoints are retained as historical evidence. Speech/provider calls, native host/hook behavior and user acceptance are separate. |
| Keep or improve checks by measured value | Duplicate inventory and bundle observations reduced with complete result equality; current scope reuse API reads50→8 bundles and6359→1013 Git subprocesses on the same seven-Feature snapshot; original tests retained | No equivalent defect/valid-case evidence justified retirement. Whole-Git freshness protection remains. Single sequential scope timings750.360→129.681s are a controlled API projection, not whole CLI or general Agent speed/quality. |

The overall goal remains PARTIAL. The completed package consumption before the
tracked-owner follow-up used frozen 0.1.54 from
clean commit `b9612ab`, tree `7e5404002be4ff04a148a7affc92b3b3824f33d2`.
Its 247 actual files match the content inventory; inventory SHA-256 is
`61d70766fe6d403ae8effb965d864e2cff7bf9df474064eb925431b8bad6cfbb`.
Before and post-consumption receipts are `package-0.1.54-before.json` and
`package-0.1.54-post-final.json`: all 247 actual files are unchanged, with no missing
or additional file. The preceding independently consumed 0.1.53 package also
retains all 247 files unchanged (`package-0.1.53-post-final.json`). Both copied CLIs
use bytecode-disabled execution; no cache files were removed to manufacture equality. New connected-product exports retain all 102 files from six
artifact directories in `connected-product-export-final/`, bound to the original
paths by `connected-export-final-manifest.json`. Earlier packages/raw/exports
remain intact. Local-main integration is recorded below. Cleanup is limited to
the created plugin worktree/branch after checking retained evidence; the actual
product worktree/branch is retained independently.

### Real-product task-start source cost

The first real Yeondoo Link task connection exposed a further common cost after
the initial four priorities: one in-memory `begin` with an existing survey state
collected the same source inventory three times. The actual product contains
large tracked static audio assets. Baseline 0.1.49 read 5332 hash inputs totaling
858134878 bytes in 33.874 seconds. The minimal canonical 0.1.50 change shares one
inventory for initial Feature bases, prior-state reuse and the new baseline:
one inventory, 1888 reads, 289442107 bytes, 14.305 seconds. Both observations
performed two project inspections, ran zero product commands, created no task and
left Git status unchanged. They exclude the CLI final audit; cache condition and
concurrent verification load were uncontrolled, so byte/scan reduction is stronger
evidence than the single-sample timing difference.

Focused RED physically read the same linked runtime input three times. GREEN
preserves baseline/Feature bases, prior review/results/check links and observes a
changed input on the next request, invalidating the old review. Ordinary workflow,
refinement and affected Harness execution/forward regressions passed 119 tests.
Because ordinary and Harness persistent baselines share this entrypoint, Full
was selected for this unit and passed all 408 tests in 712.445 seconds, with no
skip/error reported. The old 0.1.48 Full failure remains historical; this is a new
run from the actual nested worktree after its root-inventory repair.

Existing independent connected-product checks also passed two tests: browser
quantity `2` and `0` became API IDs `1` and `2`, matched SQLite and fresh GET after
service restart; negative rejection and frontend-payload corruption stayed
distinct from passing API/Domain cases. Owned services/DB were cleaned, exported
raw/screenshots remained, and old output refusal preserved bytes. This synthetic
API/storage boundary is independent of Yeondoo Link's memory-only consultation.
Raw Full/targeted measurements live under `.work/plugin-continuous/20261012/`;
68 connected-artifact files were exported byte-for-byte to
`.work/plugin-continuous/20261012/connected-product-export/`. The manifest binds
original and retained roots and verifies every hash before eventual cleanup.

Before the later direct integration instruction, local-main integration was
rejected twice by automatic approval review: it did
not treat the goal-context approval as a trusted message authorizing the exact
protected/default-branch merge. At that checkpoint main remained at `107850a`; verified branch
commits/packages are preserved. The earlier pending approval question named only
`1f9263c` and `5fd36ae`; later verified units extend that stack, so that narrower
question is not approval for the current complete branch. No alternate transport or indirect Git integration was
used. Product source and evidence work continues independently.

### Shared bundle observation during real-product lookup

A real product task with six consumers of one native/browser bundle exposed
repeated full-bundle assessments in read-only lookup. Canonical 0.1.51 now
observes each bundle once per project inspection and copies the result before
consumer-specific command validation. The focused RED observed two reads for
two consumers; GREEN retains different consumer verdicts, independent command
rejection and remeasurement after raw mutation on the next call. Workflow,
refinement, hook, viewer and execution regression passed 149 tests in 334.494
seconds. Full 408 above applies to the preceding 0.1.50 unit; it is not attributed
to this subsequent change. Whole-Git/raw/runtime stale protection stays active.
On the same actual six-consumer product task with two retained bundles, baseline
performed 12 bundle evaluations in 194.790 seconds; current package performed
two in 40.423 seconds. Complete inspection JSON was equal, both executed zero
product commands, and all existing task/raw files retained their hashes. The
baseline snapshot covered 80 evidence files; the candidate covered 81 because a
separate failed preparation's supervision record had been added. That added log
was not a task or bundle input. These single samples overlapped briefly and
cache/load were uncontrolled; the deterministic evaluation reduction supports
the finding more strongly than timing. Raw records are `real-lookup-baseline.json`
and `real-lookup-candidate.json`. Final packaged independent follow-up is recorded below.

### Follow-up: tracked new tool owner and staff ownership

The prior 0.1.54 read-only matrix had staff architecture FE/Domain UNDECIDED.
Root reviewed App dispatch/lifecycle, StaffGate input/unmount handling and the
staff-lock device storage boundary against the retained actual PIN/native/browser
normal and refusal cases. An existing-format review registered in 334.652 seconds,
child exit 2, zero product commands. All four staff FE/Domain cells are now PASS;
both BE/API cells remain reasoned NOT_REQUIRED for this device UI gate. Whole
coverage stays PARTIAL with 20 gaps; this is no server authentication, exhaustive
race, clinical or human UI approval. The input, before-state, full stdout and
root receipt are in `final-consumption/review-staff-owner-scoped-0.1.54.*` and
`staff-owner-root-receipt.json` under the retained continuous-improvement evidence.

The separate consumer feedback has two actual blockers: staff-access does not own
scripts/browser-runner.mjs, and its later failing capture has the new runner already
tracked. Contrary to an initial independent review claim, the actual run02 bound
plan selects staff-access and includes its failed /suites/5/status assertion; root
read it and the reviewer corrected that claim. Selection is not the blocker.
Neither the feedback Feature nor immutable task baseline is silently rewritten.

Runtime 0.1.55 allows a missing new-tool preimage from a clean captured Git revision.
It retains bound red/selected failed assertion/root/unchanged-capture/current and
old owner/dependency checks, then verifies the exact Git blob SHA or deterministic
LF-to-CRLF checkout SHA against both declared and measured dependency hashes.
Dirty tracked captures, missing/different Git objects, custom checkout filters and
present malformed/unchanged baseline entries stay OPEN. No task baseline is filled.
The actual clean product red revision 1c9dfbf has blob SHA a9dc7903...; its CRLF
checkout SHA exactly matches captured fe2ed661... . Sandbox Git read exited 128;
the same read-only normal execution-permission retry passed, without settings changes.

Focused RED observed OPEN instead of RESOLVED in 11.048 seconds. Three focused
cases then passed in 62.447 seconds: tracked new-tool repair, dirty tracked refusal,
and existing untracked repair, including missing/different Git objects, raw tamper,
missing red, removed owner and malformed/present preimages. An initial byte-edit
attempt mismatched CRLF and made no source change; a mistakenly launched two-case
repeat retained the same RED (36.358 seconds). It is not GREEN evidence. Source
editing then preserved the original CRLF bytes; the successful checks are separate.
Independent source review found no material trust/path defect; it ran no tests.
The complete impacted workflow/refinement/hook regression passed 80 tests in
181.729 seconds. Package/update/repository-doc checks passed nine tests in
7.840 seconds; resource drift, distribution and formatting passed. Full was not
repeated for this bounded fallback; prior Full counts above are earlier sources.

This bounded runtime unit does not reclassify the old staff-specific record or
claim its resolution. A separate app-runtime owner feedback must use its selected
failed run-level /status and retained normal /cleanup/errors assertions, with the
original red/current green bundles. Clean 1aa2a8d (tree 49a15f7a246904235ee43086b9871f747e30c2f1) built
0.1.55 into a new 247-file package; inventory SHA
eaf34425da4ec7b7b5c683c73759d66436b92af654e8538edb9491c71c2e03e6.
Actual packaged feedback registration on the product task took 203.864 seconds,
child exit 2, whole PARTIAL and zero executed product checks. The new owner record
is RESOLVED with no remaining conditions; loader remains RESOLVED and the original
staff feedback stays OPEN. Root checked the full stdout and unchanged task ID,
baseline, prior reviews and original staff feedback. The new source_before still
lacks the runner; its preimage comes only from the bound clean red Git evidence.
owner-feedback-0.1.55-root-receipt.json retains these comparisons and stdout SHA.
Independent fresh-context related consumption used the new source package and
actual existing guide/task/context without expected verdicts or the repair patch.
The first sandbox lookup was BLOCKED (0.303 seconds, exit 2): actual Git stderr
from a separate read-only probe is dubious ownership. Those original outputs
remain intact. The normal execution-permission retry changed no Git setting and
completed at 20:02:26 UTC in 227.815 seconds, exit 2, PARTIAL, read_only true and
zero product commands; stdout 191999 bytes, stderr 0. Root initially described
uncollected completion as still running; actual supervisor times supersede that
status message. A sandbox CIM probe was Access Denied and supplies no OS proof.

Before/after 101 linked task/bundle/plan/raw/assessment/capture/context files have
the same SHA and length, missing zero. Root independently checked both snapshots
and current bytes. The snapshot excludes product sources/runtime dependencies;
previous actual source32/served13/PNG120 checks retain their separate scope.
The same twelve current native/browser judgments are PASS/REUSABLE with raw
AVAILABLE across consultation, staff-access, comparison-purchase, privacy-lifecycle,
ui-assets and app-runtime. Root independently verifies physical raw hashes.
The current in-task matrix additionally includes verification-connection; this
owner-scoped feedback consumes broader tool/shared-UI connections than the previous
four-consumer/eight-row snapshot. It does not imply their pending semantic reviews
passed. Coverage has 20 gaps and lookup 16 findings. Original staff feedback stays
OPEN; both loader and separate app-runtime manifest owner feedback are RESOLVED.
The independent consumer confirms reuse for the requested local consultation/
purchase continuation, keeping Chromium abort cause UNKNOWN and real clinical,
POS/payment, provider and user acceptance unverified. It issued no product tests,
source/state/config changes or installation. Model ID is UNKNOWN (only a generic
GPT-6 family label is available); no general model/Agent quality or latency claim.

Full original blocked/retried stdout, stderr, supervisor, input snapshots and helper
bytes remain under tracked-owner-consumption/ (elevated/ is the normal-permission
result). root-readonly-receipt.json and root-current-checks-receipt.json retain root
confirmation. A first root display projection used absent verification/raw_status
keys and returned None; no verdict or raw availability claim used those fields.
The actual check_results/evidence_status fields and physical raw hashes above are
the verified projection. All 247 files of 0.1.55 match the pre-consumption snapshot,
with no extra/missing/changed bytes; 0.1.53/0.1.54 also remain unchanged. The 102
connected-example export files still match both source and retained copies.
The 0.1.55 result-only follow-up 1cd589e adds no code beyond frozen 1aa2a8d; protected-main
integration and native current-package host acceptance remain separate pending
boundaries. The overall goal remains PARTIAL. Earlier 0.1.54 package/run/lookup numbers
below retain their original conditions and are historical after this source change.

### Feedback observation reuse and owner review, 2026-10-13

The same actual three-feedback task still evaluated six native bundles even
after result-link sharing: each feedback reopened its failing/current evidence.
Runtime 0.1.56 reuses the existing inspection-local pool across feedback,
check-retirement preservation and result consumers. Its key separates resolved
path and full-scope/item-only mode; every consumer receives a copy. The next
inspection has a fresh pool. Validation, raw/runtime/source hashes, scope review,
exception handling and consumer-specific assertions are retained. This is a
bounded observation snapshot, not atomic concurrent-state or protected acceptance.

The real fixture first retained RESOLVED/RESOLVED/OPEN for equal and differing
normal contracts, then failed on six views instead of two unique views. GREEN
keeps those different judgments, rejects changed raw on a later inspection, and
rejects missing task scope despite a pooled item-only PASS. Existing consumer
command/mutation isolation remains covered. A separate read-only code review
found no material issue; it ran no tests or product CLI.

The five affected workflow/refinement/hook/viewer/execution modules passed
153 tests in 409.561 seconds (supervisor 409.801, actual child exit 0).
Package/update/repository-document checks passed nine tests; resource drift,
distribution and formatting checks passed. Full was not repeated: this bounded
pool changes observation reuse in the existing workflow paths, not schema,
discovery, Harness baseline ownership or protected policy. Initial focused GREEN
reported two tests OK despite PowerShell stderr decoration producing outer exit
1; the definitive regression above captures the actual child exit and raw bytes.

On the unchanged actual product state, standalone feedback inspection fell from
six evaluations to three unique path/mode evaluations, 134.450 to 61.652 seconds.
Complete feedback JSON is byte-identical (SHA-256
bc805e1a71e8a046530b4fb6d86b801a437b5490fe404b93e75b03cc1dd7cb29).
Both observations executed zero product commands and kept the same 101 named
task/evidence files unchanged. That snapshot excludes product source/runtime
hashes; the viewer still remeasured those inputs. These sequential samples
overlapped regression load and had uncontrolled filesystem caches; reduced
evaluation count is stronger evidence than the timings. Raw baseline, candidate
and root equality receipt are under scoped-owner-review/ in the retained evidence.

The 0.1.55 CLI separately registered current app-runtime and verification-connection
owner reviews in 420.580 and 404.479 seconds. Whole status stays PARTIAL; gaps
went from 20 to 17, baseline/feedback/prior reviews were unchanged, and no product
check executed. App FE/Domain business and architecture are REQUIRED/PASS;
BE/API is reasoned NOT_REQUIRED for the local frontend delivery. Tooling owns
the verification-connection architecture/Domain cell; other cells refer back
to their product owners and are reasoned NOT_REQUIRED. This does not exempt
actual product business rules or authenticate a human review.

An actual read-only release check refused the draft catalog with exit 1 and
2972 review/publication issues; this expected refusal is not a release PASS.
Source-traced missing-catalog fallback is not claimed as a newly executed corrupt
catalog browser case. The reporter intentionally preserves aggregate PASS and
ambiguous duplicate-name lookup ISSUES; its existing fixture confirms that
distinction. An initial root suspicion of a reporter defect was corrected before
any product code or test expectations changed.

Fresh native discovery used normal authorized reads: codex plugin list --json
returned exit 0 in 26.417 seconds, twelve installed entries and no agentic-coding
entry or available package. The current package is not exposed by this host;
native current-package/hook acceptance remains unobserved. No installation,
global trust/configuration, provider or transport workaround was performed.

The verified unit is committed at 8a4a2fe and a new 0.1.56 package was built from
that clean source/tree 4fb974553ecad1560b60f4ee871166380229963f: nineteen Skills,
247 files, inventory SHA-256
5aafb76f4f01a5ba603552833689f31654d1d9b0fa76cff2da8fb37c2f3fa949.
Earlier 0.1.53/0.1.54/0.1.55 packages still have their 247 original hashes, with
no extra/missing files after the owner registrations and cost measurements.

A separate UI review noticed sticky staff actions covering question text in
full-page screenshots. Root reopened both captures and traced the existing
180px document scroll padding before treating that image as an accessibility
defect. A real focused browser run on unchanged 79d74b1 then reached all four
bilingual Korean/English staff questions at 1440x900 and 390x844. Eight observed
focused rectangles were fully above the bar and their centers received pointer
hits. Eight PNGs preserve the actual focus/scroll states; root reopened the
mobile third-question capture. This is focused keyboard reachability, not
whole-screen visual or comprehensive accessibility approval.

That observation completed in 10.144 seconds with 32 source fingerprints and
13 served-source checks unchanged, no page/HTTP/external-request errors, owned
PID 28784 stopped and browser closed. The initial diagnostic incorrectly looked
for the sibling action bar as a descendant and returned zero observations; its
failed report is preserved. Only that diagnostic selector/output path changed
for the subsequent run. No product source, test or configuration changed.
Raw observations are scoped-owner-review/staff-focus-2/; earlier failed raw
remains in staff-focus/. The screenshot overlap therefore does not establish
keyboard obstruction. Broad public assets, image-fetch effects, other asset
consumers, public-use rights and user acceptance remain unreviewed; ui-assets
owner/screen gaps remain visible, rather than turning this focused pass into
whole-Feature approval. Actual product source stays at 79d74b1.

An independent fresh context subsequently discovered the existing consultation/
comparison-purchase task and inspected it with the frozen 0.1.56 packaged
maintain-agent-harness workflow CLI. It executed no product test and made no
source/config/state or Git trust change. The first sandbox lookup returned
BLOCKED in 0.324 seconds; a preserved separate Git probe identified dubious
ownership. The same read-only lookup through normal require_escalated permission
returned child exit 2, PARTIAL in 141.090 seconds, stdout 236864 UTF-8 bytes and
empty stderr. It ran from 20:58:28.889 to 21:00:49.982 UTC. Those endpoints, rather
than a pending tool handle, establish completion. Model ID is UNKNOWN; this is
independent subsequent-context reuse, not a model-quality or attestation claim.

Root independently parsed actual current_status/current_reuse/raw_availability:
twelve rows across consultation, staff-access, comparison-purchase,
privacy-lifecycle, ui-assets and app-runtime are PASS/REUSABLE/AVAILABLE. The
seven-Feature in-task matrix includes verification-connection. All seventeen
gaps remain explicit. Loader and app-runtime owner feedback are RESOLVED; the
original misrouted staff feedback remains OPEN. Original failure/current run03
and provider, business/user acceptance boundaries were not rewritten.

The independent capture and root rehash confirm the same 101 named task/linked
evidence files before/after/current and all 247 frozen package files unchanged.
Root also rehashed each current physical raw path against its reported SHA.
Snapshot scope excludes product source/runtime hashes; the actual lookup still
remeasures those conditions. Evidence is pooled-feedback-consumption/ (including
the original failed run and elevated/ retry), root-receipt.json and
package-0.1.56-post-final.json. The 102 connected-example exports still match
both original and retained copies. Protected local-main integration and native
current-package host acceptance remain pending; the overall goal is PARTIAL.

### Reused scope proof and image observer follow-up

The reporter connection was semantically reviewed but still had no registered
check. Product metadata commits e386224, 7c441c5 and 5554dd0 connect the existing
nine named reporter fixtures through a dedicated reporter-native command and
its declared criterion/fixture. Seventeen original registry rows and two original
commands remained unchanged. Strict shared-report condition equality rejected
the first two preparations; it was preserved, and the separate command avoids
merging genuinely different inputs. No reporter test body was added or changed.

Actual 0.1.56 preparation03 completed in347.917s. Execution03 ran three commands:
native55/55 and reporter9/9 passed, but the surface suite retained one local
product-image ERR_ABORTED and the complete browser report was ISSUES. That run
completed with child exit1 in349.007s. Its155 files remain byte-identical.
Preparation04 completed in391.877s and reused native/reporting proof; only one
browser producer ran. The same surface image abort recurred, and owned runtime
cleanup completed. The final reader was interrupted after1114.773s: child exit-1,
stdout/stderr empty, state bytes unchanged, final task binding incomplete. Its
checkpoint/raw is preserved; this is not a completed CLI or a latency comparison.

That real reuse path exposed a separate common cost: _view_coverage reopens each
linked native bundle for every reusable Feature. Runtime0.1.57 gives one scope
observation one local pool, using the existing item-only/deep-copy join. Consumer
command checks remain independent, full-scope and item-only keys stay distinct,
and later calls reread current raw. Focused real native/Git fixture RED observed
two reads instead of one (4.548s); GREEN passed in4.642s, retaining PASS versus
ISSUES consumer rows, command refusal and next-call raw mutation rejection.
Five impacted workflow/refinement/hook/viewer/execution modules passed153 tests
in406.064s (supervisor406.308s, child exit0). Package/update/docs passed nine
tests in7.818s; drift, distribution and formatting checks passed. Full was not
repeated for this bounded observation-sharing change; earlier Full remains
separate evidence. Clean package/product consumption is recorded separately;
no full CLI speedup is inferred from the interrupted old reader.

A controlled localhost Chromium diagnostic ran the unchanged original surface
script while delaying that local image500ms. Image request38 preceded document
request39; its response/commit preceded the image abort. The manifest-only
observer retained that retired image as a failure. The diagnostic completed
in10.941s with source unchanged and owned cleanup. This reproduces one normal
retired-image lifecycle; it does not attribute the two earlier historical events.
The existing lifecycle guard gained retired versus current/foreign/unowned/reset
image cases and an independent HTTP404 control: actual RED exit1 (0.180s),
GREEN exit0 (0.188s), one named case, no skips. Same controlled browser GREEN
completed in11.461s, retaining the cancellation with no active errors and stable
changed source bytes. Product commit6289ea0 changes only observer, that guard
and the affected guide/map. All six original UI scripts remain unchanged.

The prior twelve-row/17-gap lookup at79d74b1 is historical after these source and
registry changes. Fresh0.1.57 preparation05 completed in418.333s, child exit0;
execution05 completed in395.871s, child exit0. Three producers bind thirteen
current PASS/REUSABLE judgments. Native55/55, reporter9/9 and all six unchanged
browser suites pass, with32 stable source hashes,13 served-source matches and120
PNG hashes. The owned server31036 stopped, both browsers closed and cleanup
errors are empty. The one retained cancellation is the staff speech manifest;
this run observed no image cancellation. Controlled GREEN separately verifies
the typed-image branch. Root rehashed all155 run05 files against the receipt.

Six current semantic reviews were recorded through the actual API, each freshly
inspecting source/evidence; review API recording/inspection time totals931.577s. Two
existing owner feedback records were refreshed and one scoped image record added.
All1721 baseline entries, bound results, execution plan, unrelated reviews and
the original misrouted staff entry remain unchanged. No producer ran while
recording reviews/feedback; historical review screenshots keep their prior scope.

The independent current-product-reuse-057 context discovered the existing task
and read the packaged guide/project map. Default sandbox Git ownership refusal
is retained; the same read-only lookup used normal escalation without changing
Git trust. Actual child exit2/PARTIAL took230.491s (supervisor exit0), ran zero
producers and selected no checks. Thirteen current rows remain PASS/REUSABLE,
with17 broader coverage gaps. Before/after163 named inputs and all247 package
files match. An old run04 native.json remains missing because that interrupted
round reused native proof; no substitute file was manufactured. Root separately
rehashes the three current physical raw reports against their reported hashes.

That independent lookup found new image feedback OPEN: root had chosen
/suites/4/status, outside the app-runtime check's registered assertions. Root
corrected only feedback linkage to its existing /status assertion, which is
ISSUES in red03 and PASS in green05; /cleanup/errors stays the distinct retained
contract. The registry, raw, source, repair preimages, bundles, all reviews and
other feedback are unchanged. First lookup/raw and the invalid proposal remain
retained. A separate fresh current-feedback-reuse-057 context then discovered
the same task through the packaged guide and product map. Default sandbox Git
refusal remains under its original directory; authorized-retry/ retains the
actual child exit2/PARTIAL after215.984s (supervisor exit0), stderr empty, zero
producer commands and no selected checks. All thirteen rows are current
PASS/REUSABLE, and the three owner tooling records are RESOLVED. The original
staff entry stays OPEN with revalidation/stale-decision/unobserved-owner-repair
reasons; moving its GREEN alone cannot make browser-runner a staff-owned source.
Seventeen broader coverage gaps remain. All163 named inputs and247 package files
are unchanged; the same old missing run04 native file is explicit. Root verifies
the physical current raw hashes and unchanged state SHA
101e7b707bae01b98d6f03d81c0c2205dc102f87b9f03b5f995659e9de247a0e.
This is independent read-only consumption, not another product execution.

Separately, scope-proof-measurement uses the actual05 plan and thirteen current
items with an immutable snapshot retaining task identity and baseline. Only
selection is projected to the supported current_evidence_reusable branch; it is
not literal CLI execution. Sequential .56/.57 _view_coverage measurements complete
in750.360/129.681s with50/8 item-only bundle reads and6359/1013 Git subprocesses.
Full coverage JSON is equal (SHA2377cc7d80624b78f64caaa8b9608c26f9ea7a83c238886d62b2d4ae8053a133),
including15 PASS,9 STALE and2 NOT_RUN rows from that pre-refresh snapshot.
Root physically rehashed all1453 retained snapshot/raw/artifact/package inputs;
none changed and no producer ran. One sequential sample per package, concurrent
load/cache conditions uncontrolled; this does not establish whole CLI speedup.

Frozen .53-.57 packages each retain247 files; failed red03/raw and current run05
each retain155 matching files, and102 connected exports match both source and
retained copies. Native current-package host acceptance and protected local-main
integration remain separate unresolved boundaries. Actual product6289ea0 and both
earlier product evaluation branches/worktrees remain clean and retained.

Current frozen0.1.57 originates at clean plugin commit a9888ce, tree
960c8ce0bd15d0e85dc7fb467c3ba9939e740855; inventory SHA is
a049a6e0b6a519394c432f87b2a676953842489f8446340da42f15d92a2cb17a.
Its19 skills/247 actual files were physically checked before and after current
execution and both independent lookups. The subsequent results-document commit
does not change this frozen runtime. Functional153 tests and package/docs9 tests,
resource drift and distribution are the actual current bounded checks; no new
Full is claimed. Native codex.exe plugin list --json completed with child exit0
in26.417s and listed12 installed plugins, with no agentic-coding/current package.
That discovery does not prove Skill invocation or automatic hook delivery. This
session has no permitted current-package native load/acceptance observation;
ordinary installation/global config/provider changes remain excluded.

The subsequent direct user instruction authorized local-main merge and branch
cleanup. The actual ff-only integration advanced clean main from107850a to
a527b28, incorporating all15 prepared commits without changing runtime bytes.
Post-merge package/update/docs checks passed9 tests; resource drift, distribution
and formatting passed. A results-only delivery note records that action on the
same development branch before its final ff-only integration. Cleanup is authorized
only for plugin-continuous-20261012 and wp-20261012-plugin-continuous; its receipt
owns the actual removal outcome. Before removal, the102 connected export files
must match their retained Main copies; the only other ignored files are51 Python
bytecode caches. No Product branch/worktree is selected for removal. The final
.work/plugin-continuous/20261012/final-delivery-state.json retains actual Git,
cleanup, package and raw integrity observations under the normal retention policy.

Native host acceptance remains unresolved. Actual permitted discovery did not
expose the current package, so no Skill invocation/automatic hook/protected-host
acceptance is inferred. The overall goal remains PARTIAL for that boundary and
the explicit product gaps. Resume native acceptance only through an authorized
host path that can load this package under the permitted configuration; current
CLI/review evidence cannot fill it. No push/install/provider/original DB change
occurred.

### Actual product task, observer repairs and independent consumption

At that earlier stage, the retained branch `evaluation/plugin-verification-20261013` had
`0b1edbb` (machine map, assertion registry, native reporter and owned browser
runner), `1c9dfbf` (Git-path metadata repair) and `79d74b1` (narrow manifest
cancellation observation with committed-document/identity guards). Product main and both earlier
UI evaluation branches/worktrees are preserved. The machine map covers 12 current
MVP Feature candidates. The survey stays PARTIAL; no consultation API/server DB,
real payment, clinical approval or global product completion was invented.

The actual selected task targets consultation, comparison/purchase and privacy.
Its shared browser/native owners select six consumers, twelve judgments and only
two producer commands. Old round 1 refused execution after selection changed;
rounds 2 and 3 preserved all six browser TypeErrors from the new adapter's
path/source descriptor mismatch. Root's first repair missed the VM filename
consumer. The final fix uses `source` at every consumer and directly loads all
six original functions in the focused guard; product conditions were unchanged.
Round 4 through immutable 0.1.51 passed native 53/53 with no failure/skip/cancel/todo,
all six full existing browser suites, 184 recorded original flow assertions,
13 exact served-source matches and 120 PNGs with verified retained hashes.
Browser duration was 57.452 seconds; its owned Vite server and two Chromium
instances closed with no cleanup errors. Full CLI duration includes preparation,
source/runtime checks and final audit and is separate from that browser time.

Independent fresh-context consumption discovered task/criteria/owner/checks
through ordinary README and packaged Skill guidance; it received no command order
or expected patch. It distinguished the survey from the exact existing task,
traced App action ? transition ? React memory ? display, separated purchase
request from store confirmation, and found shared CSS/component use in staff UI.
It read original failures and new normal raw without executing the product.
Its package comparison matched all 246 receipt files and version 0.1.51. Two
material interpretations needed root correction: ancestor Git HEAD is not the
non-Git package's source commit; CatalogImport already has Feature source,
criteria/coverage and UI-consumer linkage. Its modal remains outside the six-suite
browser run. These corrections are retained in the independent investigation.

The same independent consumption found `EADME.md` in the browser raw where native
Git status recorded `README.md`. Root reproduced this in a real temporary Git
repository: `.trim()` removed the first porcelain status space. `.trimEnd()` fixes
only output normalization. The actual blocked-run regression retains both pre/post
`status: " M", path: "README.md"`, launches no server/browser and preserves setup
failure. Four focused runner tests passed; named loader/no-overwrite/Git metadata
cases and prevention are connected to the existing app-runtime native command.
Old raw is unchanged, including its metadata error. No UI/business oracle changed.

After the first product commit, actual `lookup --summary` and task `resume`
preserved hashes of 1966 tracked-source/task/raw files, ran zero checks and retained
historical PASS/current UNKNOWN/current reuse STALE with raw available and facts
explicitly omitted. They took 70.919 and 70.136 seconds; the supervisor's record
was written outside the product, separately from CLI behavior. This is actual
read-only evidence, not only a fixture. Product mapping/semantic review remained
PARTIAL. Capture/selection changes require a new plan; lookup never launches one.

### Independent current execution and retired manifest observation

The final fresh-context Agent used immutable 0.1.53 on product `1c9dfbf`.
It independently selected the existing ordinary consultation task rather than
the whole-product survey. Root corrected its initial Harness-Skill assumption,
missing session/duplicate lookup handling, oversized stdout capture and Windows
JSON argument transport. Those interventions and parser errors are retained in
`final-consumption/operations.md`; model metadata is UNKNOWN. This is bounded
discovery/consumption with supervision, not a controlled demonstration of general
Agent superiority. Large stdout is retained with its actual UTF-16LE/BOM encoding.

Successful current preparation took 288.188 seconds, child exit 0, twelve selected
Feature/check judgments and zero executed tests. Explicit execution took 295.955
seconds, child exit 1 and two producer commands. Native passed 54/54 with no
failure/skip/cancel/todo. Five browser suites passed; the original staff script
returned PASS but the adapter promoted one manifest GET `net::ERR_ABORTED` to
ISSUES. Page/console/HTTP/external/cleanup errors were empty and owned resources
closed. The full current CLI also reported ISSUES/PARTIAL; it was not credited as
PASS. The raw lacks lifecycle attribution, so navigation and the manifest's
five-second abort timeout cannot be causally distinguished from that record.

Product commit `79d74b1` repairs only the observer/guard/registry/related guide.
Root's controlled localhost Chromium fixture reproduces normal document
replacement cancellation: the exact original observer preimage fails and the
current observer passes under the same manifest fixture. Both retain raw/events
and close their own server/browser. An independent challenge rejected a generic
GET exception. Eligibility is instead limited to the known same-origin/main-frame
static `/audio/manifest.json` request, a known earlier request identity, the exact
abort and a replacing document response/commit. The retained cancellation text
describes a retired static request and explicitly does not infer cause. Failed
navigation, live/unknown/unbound requests, other GET endpoints, mutating methods
and other network errors still fail. The independent final review found no blocking
event-order or cross-page identity defect, but an earlier request ID is only a
temporal ownership proxy: an independently aborted manifest near navigation could
still be classified as retired. Causal attribution remains unproven; the guard
does not test delayed independent aborts. Same-document changes and redirects are
covered, as are two pages' identical URL identities. Five native guard cases
passed; original browser/GUI assertions are unchanged. A retrospective run of the
current guard rejects the retained generic candidate (an extra API GET is wrongly
retired), separately from the final eligible-manifest GREEN. A CRLF-sensitive
fixture preimage recovery attempt and its missing-owner-path run failed; the
correct byte recovery verifies the original SHA before reuse. Earlier fixture
paths and product raw were preserved.

On clean product `79d74b1`, independent 0.1.54 preparation completed in 330.508
seconds, child exit 0 and zero executed tests. Its explicit execution completed
in 324.584 seconds, child exit 0 and two producer commands. Native passed 55/55
with no failure/skip/cancel/todo; browser passed all six suites in 56.517 seconds,
with 184 original flow facts. One retired static manifest is retained as a
cancellation with request ID 1501 and navigation ID 1506; actual request failures
and all other error arrays are empty. Vite PID 29280 stopped, both Chromium
instances closed and cleanup errors are empty. Root independently compared the
enclosing stdout/child supervisor, current twelve reusable judgments, all 32
source-file hashes, all thirteen served-source matches and all 120 retained PNG
hashes. Both browser Git snapshots are clean at `79d74b1`, source unchanged.
Root's first source-hash helper wrongly assumed a dict instead of the recorded
list and failed before confirming anything; the corrected receipt discloses it.
Current task status stays PARTIAL for unreviewed project areas, remaining staff
architecture and the separate OPEN consumer feedback. Independent consumption actually refreshed the original loader
feedback with run03 green and preserved round-3 red: RESOLVED, remaining empty,
zero executed commands. Root checked actual stdout SHA and child supervisor
(`feedback-loader-root-confirmation.json`). Exit 2 is the whole PARTIAL audit,
not a rejected registration. The immutable baseline and `source_before` still
lack the runner; no historical preimage was backfilled.

A separate consumer-scoped staff manifest feedback was actually registered and
remains OPEN with `oracle_or_tool_repair_not_observed`. It is not credited as a
resolved owner feedback: its repair path belongs to app-runtime, whereas the
record is scoped to staff-access. Root caught its proposed red pointer naming
passing suite 2; the Agent corrected it to failed suite 5 before registration.
The actual run02/run03 bundles and separate owner RED/GREEN remain intact.
An owner absent from the immutable baseline but already tracked at later RED
has no per-file untracked preimage for the current bounded fallback; this path
is not generalized. Neither missing ownership nor missing historic identity is
backfilled to clear the feedback. Both registration calls execute zero checks;
actual child exits 2 reflect the enclosing PARTIAL audit. These supervised
input corrections belong to Agent evaluation cost, not plugin effectiveness.

The first consultation/comparison-purchase reviews registered successfully but
left all applicability cells UNDECIDED. Root caught the mismatch between review
prose and actual matrix; the existing review format now records explicit FE/Domain
coverage links and reasoned BE/API NOT_REQUIRED for those two local-memory flows.
Actual refreshed matrices show four required cells PASS and two NOT_REQUIRED per
Feature, while current native verification stays PASS and zero commands execute.
This is not a global BE/API exemption: provider generation and other Features
remain separately unreviewed. The two first payload files were overwritten when
adding scope declarations without keeping before-byte copies; original input
bytes are UNKNOWN. First CLI stdout and normalized registered reviews are retained.
Subsequent scoped input names/RunIds are separate. Source, baseline and producer
raw were not changed to make the reviews pass. The first privacy screen review correctly remains NOT_RUN in its retained
registration. Because that missing observation was within authorization, root
performed one focused actual privacy UI observation instead of stopping there.
Its copied original browser-flow prefix preserves twelve original conditions
through end/cancel/reset; it is not a full-suite rerun. Actual child exit 0,
12.266 seconds, twelve PNGs: 1440px/390px dialogs have no horizontal overflow,
44px close/56px action heights and focus within the dialog after Tab; cancellation
preserves the existing consultation and ending returns to welcome with cart 0.
The original current full-flow evidence separately checks answer/product leakage.
All 32 recorded source/dependency file hashes and 13 served-source comparisons match; before/
after Git remains clean `79d74b1`. Owned Vite PID 7448 and Chromium closed with
no cleanup errors. Root opened the mobile dialog and reset image; the independent
consumer rechecked report SHA and three images before its review refresh.
`privacy-ui-root-receipt.json` binds twelve PNGs, report, copied source and driver.
Product-local `.work/privacy-ui-20261013/` retains artifacts and instrumented
prefix. Two root temporary-seam failures (duplicate export and Windows root-path
separator comparison) happened before app/browser execution; their source bytes
are retained. Console-error capture for this scoped report is UNKNOWN; it does
not replace the six-suite raw or establish complete accessibility/provider/
clinical acceptance. The independent consumer refreshed the privacy screen review using a separate
input/RunId and these retained facts. Privacy now has current required FE/Domain
business/architecture PASS with reasoned BE/API NOT_REQUIRED; staff business
passes while its architecture FE/Domain remain UNDECIDED and owner review NOT_RUN.
Root also visually opened the current 1440px/390px staff captures and confirmed
two-column/stacked layout, common cards/actions and review-needed notice. This
bounded screen observation does not approve all focus/scroll states or the UI. Final related read-only reuse is observed below; final 0.1.53/0.1.54 package
post-inventories match all original bytes without missing/additional files. Supervisor wrapper/inspection failures remain in the independent
operations log; failed before-hash evidence is UNKNOWN, not a passed check.

### Final related read-only consumption and delivery boundary

Final independent 0.1.54 lookup initially returned BLOCKED in 0.348 seconds:
Git ls-files exited 128 under sandbox permissions. The Agent first described it
as PARTIAL; root read the retained output and corrected that interpretation.
The three original outputs were copied byte-for-byte as
`lookup-0.1.54-sandbox-blocked.*`. An identical normal execution-permission retry
used the actual product cwd and retained task context, without safe.directory or
settings/transport changes. Child exit 2, 183.871 seconds, stdout 355730 bytes:
PARTIAL, read_only true, zero executed checks. Full raw is preserved as
`lookup-0.1.54-escalated.*`; a subsequent overly broad nested-object projection
truncated only the tool display, not the retained JSON, and is disclosed.

The actual continued consultation/purchase/staff lookup reuses eight current
required native/browser check rows for consultation, comparison-purchase,
privacy-lifecycle and staff-access. All are PASS, raw AVAILABLE, REUSABLE, selected
for task_verification_required. They bind native run
`b737066f-d39a-438c-a1ae-cb31a23bbc8d` and browser run
`b78b5946-5553-44c2-8bf7-04f8a40f9b5f`. Earlier explicit execution ran twelve
judgments across six consumers; current task applicability requires eight after
scoped review. Catalog-cart/speech are not required in this lookup and remain
unreviewed; they did not become reviewed global PASS. This is consumption of the
existing exact task, not a fabricated new-task identity or native host invocation.

Root independently checked complete stdout, current checks/matrix/feedback and
before/after snapshots. All eight named files match both snapshots and current
bytes: task state, run03 plan/bundle/native/browser, run02 bundle/browser, focused
privacy report. This sample is not every project file; source32, served13 and
PNG120 were checked separately. `final-lookup-root-confirmation.json` and
`readonly-hashes-root-confirmation.json` retain root results; the first root
projection used irrelevant reuse field names and was corrected after reading the
actual current_reuse field, preserving its initial derived receipt. Both final
packages still match all 247 actual files, with no missing/extra/cache artifact.

Seven review/refresh calls took 298.776-317.976 seconds each; two feedback calls
took 113.761/148.570 seconds. All those state-registration audits execute zero
product checks. Successful final prepare/execute took 330.508/324.584 seconds,
separate from the 56.517-second full browser run and 12.266-second focused UI
observation. Earlier duplicate lookup, invalid JSON transport, unsupported .NET
helpers, missing scope decisions, overwritten input pre-images and root/Agent
corrections are retained in operations.md and superseded records. These costs and
model-metadata UNKNOWN prevent claiming general Agent speed/quality superiority.
No new model transport, installed Skill, home/global setting or provider was added.

The earlier a5680a8 documentation unit changed only results/index; its runtime
and frozen 0.1.54 package remained bound to b9612ab. The 0.1.55 tracked-owner
follow-up above is the newer runtime source 1aa2a8d. Affected behavior/Feature evidence is
owned by workflow-obligations, verification-results, plugin-package, native-
verification and harness-setup units above; this unit adds no Feature logic.
Local plugin main integration remains rejected at the existing protected-branch
boundary. Main/worktree ancestry and cleanliness must be checked against the final
reviewable branch before a newly trusted approval; keep the created plugin branch
until integration is authorized and complete. Product branch/worktree 79d74b1 and
prior branches/raw remain retained. Native current-package hook/Skill/protected
acceptance needs an already permitted host exposing this package; whole product,
clinical, fulfillment, provider and user UI acceptance remain unverified. Overall
goal stays PARTIAL; none of this record declares full six-outcome completion.

### Added tool owner and bound repair preimage

Actual feedback registration exposed a further common false blocker: the task
started before its runner was created, so the immutable baseline has no runner
hash. The existing oracle/tool branch could not establish a repair even with an
actual retained failing native capture. A new 0.1.52 unit keeps missing baseline
keys unknown and uses a separate, recomputed red-capture preimage only for a
root-local declared tool owner. It requires selected historical failure on the
same expected pointer, current/red ownership, intact root/plan/raw/producer/
assessment binding, stable capture source and matching declared dependency,
measured dependency and per-file untracked hashes. Existing baseline hashes win;
neither baseline nor source_before is backfilled. Current green must still pass.

Focused native RED reproduced OPEN despite an actual failing/repair/normal chain.
GREEN covered the new owner and preserved the existing oracle path. Missing red,
removed ownership, a present unchanged baseline and raw tampering remain OPEN;
restoring exact bytes is reobserved. Both focused tests passed in 42.246 seconds.
A read-only probe against the actual product removed only the missing-preimage
blocker, preserved the task hash and kept stale green/current binding obligations
OPEN. Full for the new preimage path passed all 410 tests in 673.036 seconds with no
skip/error reported. A subsequent independent review reproduced a malformed
present hash (`null`) accepting a repair; the final narrow hash-value gate rejects
null/non-hash preimages rather than falling back. Full predates that final input
gate; its two focused native repair/normal and invalid-input rechecks passed
in 43.816 seconds. Resource drift, distribution and formatting checks passed. Final packaged related consumption confirms the original loader RESOLVED and preserves the separate consumer observer OPEN;
no protected-host or semantic approval is claimed.

### Portable package source identity

Fresh consumption initially attributed the package to an enclosing Git HEAD.
Root correction used the external frozen receipt, but ordinary portable discovery
had no build-origin file. Version 0.1.53 adds `build-origin.json` with source
commit/tree, source dirty flag and version. Its bytes are hashed in the package
inventory. The builder verifies its own checkout root; dirty path names/project
state/credentials are not included. Dirty builds explicitly require content hashes
rather than treating HEAD as all copied bytes. Missing origin in old packages
means source commit UNKNOWN unless a retained receipt is available.

The existing actual package consumer first failed for missing origin; GREEN
checks source identity against the builder checkout while running copied tools
outside it, validates origin's inventory hash and preserves no-overwrite/update
behavior. Package/update/docs verification passed nine tests. This is passive
packaging metadata, not execution or review authority; the affected Feature is
plugin-package and ordinary workflow discovery guidance. Full above belongs to
the shared runtime repair unit; this isolated builder change uses those targeted
checks and subsequent immutable product consumption.

### Coverage evidence in read-only summaries

The final independent 0.1.53 consumption exposed a presentation leak: check
results omitted large assertion values, but coverage rows repeated those same raw
observations. Tool-output truncation lost the complete independent stdout. The
original truncated attempt and duplicate lookup remain recorded rather than
being credited as an intact capture. Subsequent commands capture full stdout and
stderr to separate supervisor files before presenting small metadata.

The minimal 0.1.54 fix applies the existing viewer summary to coverage evidence
after validation. The complete matrix, row verdicts, raw locations/pointers,
bindings/hashes and observation counts remain. A focused RED with a large observed
value reproduced the leak; GREEN also preserves the original detailed result.
Presentation-only replay of a retained actual product summary reduced serialized
characters from 368328 to 140939 across 40 coverage rows and twelve raw records,
retaining the count of 102 observations and identical complete matrix and all raw
bindings. This replay launched zero product commands and is not new runtime or
Agent-quality evidence. Further metadata and scope remain intentionally complete;
large stdout still belongs in a retained file. Full above is not attributed to
this isolated presentation change; affected CLI/viewer regression and packaged
read-only follow-up are the selected verification.

Workflow/hook regression passed its 51 cases. The initial combined command also
had two loader errors from a nonexistent viewer test-class selector; that exit-1
run is retained. The two correctly selected viewer summary cases then passed,
including missing raw versus deliberately omitted observations. Repository docs,
resource drift, distribution and formatting checks passed. No repeated Full or
product run was used to verify this presentation-only path.

### Candidate scale and host detail

The current retained-task workload is a measured local history model: two Agents,
four tasks per day, four/sixteen/sixty-four days produce 32/128/512 retained
records. These are unique copies of one real `begin` record, about 4 KB each,
not evidence of a live scheduler or long-running Agent queue. Three warm-cache
hook samples per scale used the same unchanged fixture and explicit current task.

| Retained tasks plus configured record | Baseline median seconds | Candidate median seconds | Baseline/candidate state reads | Baseline/candidate total Path bytes |
| --- | --- | --- | --- | --- |
| 32 + 1 | 0.399 | 0.262 | 35 / 10 | 241144 / 142269 |
| 128 + 1 | 0.865 | 0.266 | 131 / 10 | 620824 / 142269 |
| 512 + 1 | 2.777 | 0.270 | 515 / 10 | 2139781 / 142269 |

The canonical hook opts into eight candidate reads; later candidate paths retain
`NOT_INSPECTED`. Default detailed CLI discovery remains complete. Explicit task
context resolves independently of previews, including the final retained task.
Unconfigured empty previews now disclose unknown omitted intents instead of
implying no diagnosis tasks exist. A focused RED read 64 records where the hook
needed only eight; GREEN retains later exact selection and observes changed bytes
on the next prompt. The previous no-context/no-config regression was updated for
this intentional omission disclosure, not by weakening a product oracle.

All scales retained one inventory/configured audit/project audit, 26 file hashes,
two Git subprocesses and zero product/test commands. Bundle evaluations were zero
because this fixture attached no native bundle; earlier native reuse/stale defenses
remain unchanged and are covered separately. Payload grew from about 4789 to 4960
characters to describe omitted/unknown records. Measurements exclude Git OS reads,
setup and cold-cache costs. Candidate paths are still enumerated, and actual
source/bundle audits are not bounded by eight. This establishes less redundant
record I/O within the tested history sizes, not whole-product or Agent superiority.
Raw baseline/candidate measurements remain in separate paths under the owned
temporary evidence root.

Workflow/hook/viewer/execution verification passed 73 tests, with the final hook
wording rechecked in its two focused tests. The earlier combined workflow/refinement
run passed its 74 non-hook cases and the new bounded-read case, while the previous
unconfigured-empty-output expectation failed as described above; that original
failure remains in `candidate-green.txt`. Plugin packaging/resource/docs checks
passed 14 tests. Resource drift, distribution validation and `git diff --check`
passed. Full is not required by these two isolated changes: static descendant
candidate probing affects setup/maintenance inventory, and opt-in preview loading
affects prompt discovery; executor, criterion evaluation and protected-host logic
remain unchanged. Configured Full triggers were assessed as candidate warnings.

Native `codex.exe plugin list --json` first failed at the current CODEX_HOME with
access denied. The normal authorized execution-permission retry succeeded, with
no home/settings/authentication change. Its twelve installed entries do not
include `agentic-coding`; the current local candidate is therefore not observed
as an installed native Skill or automatically delivered hook on this host.
[OpenAI packaging guidance](https://developers.openai.com/plugins/build/plugins)
also distinguishes bundled hook trust from package presence. Installation/trust
changes are outside this request. Native current-package discovery/Skill invocation,
automatic hook delivery and protected acceptance remain BLOCKED/unverified until
an already permitted host exposes the reviewed current package. Direct package
CLI success does not substitute for those observations. The two actual native
captures are `native-discovery.json` and `native-discovery-authorized.json`.

<a id="yeondoo-plugin-improvement-2026-10-12"></a>

## Scope guidance, hook reuse and Yeondoo Link pilot, 2026-10-12

The [authorized prompt](plugin-improvement-next-session.md) applies
[direction §12](agent-coding-system-direction.md#plugin-maturity-yeondoo-link).
Both checkouts initially were clean: plugin main `1d7462e`, version 0.1.47;
Yeondoo Link main `220c945`. Plugin fetch succeeded: local main was 103 commits
ahead of origin/main, with no remote-only commits. Yeondoo Link's existing remote
tracking ref equaled main; it was not fetched, so latest remote status is unverified.
The user confirmed the shared store device and friendly, clear pharmacy guidance;
that is a use-scene/direction decision, not approval of an unseen UI implementation.

### Common implementation and bounded evidence

Commit `efbd5b8` releases local package 0.1.48 at the existing
`workflow-obligations`/`verification-results`/`agent-workflow` owners. Undeclared
active applicability now produces advisory `next_actions`, independently of
review readiness and reusable native results. Explicit declared gaps retain their
blocking obligations; source-only work and reasoned NOT_REQUIRED remain valid.
The hook retains exact task/request, Feature references, current check reuse,
scope gaps, action counts and read-only detail pointers in bounded context. It
shares one source inventory and identical selected/active task audits per
invocation; later prompts remeasure bytes. Different states still assess their
evidence independently. Whole-Git/bundle stale protection is retained because
complete Feature-local dependency coverage has not been demonstrated.

Focused RED caught empty next actions with six active UNDECIDED cells and current
native PASS, duplicated inventory/audit, and hidden reusable evidence in the hook.
GREEN preserves real native PASS, source-only readiness and reasoned N/A;
payload pressure retains the selected task, and a later hook observes changed
source bytes. Existing checks remain: no retirement or softened oracle was needed.
The relevant initial workflow/refinement/hook run passed 75 tests. Full ran 404
tests: 402 passed, two environment/layout errors remained in that invocation.
The owned-child timeout cleanup test passed when rerun with normal execution
permission (1 test); the cutover/inventory test passed after moving only this
worktree from the repository's `.work` to an external temporary directory
(1 test). The original Full failure is retained, not renamed a passing Full run.
The pre-existing Harness inventory limitation with a Git ancestor was avoided
by worktree placement; it was not repaired or attributed to the hook change.
Resource drift, distribution validation and `git diff --check` passed.

Actual immutable package CLI consumption used small explicit task sets. Baseline
0.1.47 returned READY_FOR_REVIEW, coverage PARTIAL, native PASS and empty next
actions; 0.1.48 kept the same readiness/PASS and explained the remaining semantic
review. NOT_RUN, current reusable PASS, historical PASS/current STALE after a
shared-owner edit, omitted-but-observed raw, and unavailable raw remained distinct.
Lookup/task resume preserved all project hashes and executed zero checks; a
related task's prepare reused evidence without execution. The committed package
executed two native fixture commands, with full content integrity unchanged before
and after consumption. Supervisor retries are retained: an initial relative review
input used the wrong working directory, and an attempted `start --state` was
correctly rejected before execution; absolute input and `begin` corrected these
fixture-driver mistakes. They are not plugin successes or product defects.

| Hook fixture, three samples per package | 0.1.47 | 0.1.48 |
| --- | --- | --- |
| Unexecuted two-Feature task: inventory / audit / file hash calls | 2 / 2 / 12 | 1 / 1 / 6 |
| Same task with captured native bundle, now stale/raw unavailable: bundle assessments | 2 | 1 |
| Same captured task: Path API byte-read calls / project bytes | 50 / 125633 | 25 / 69471 |
| Same captured task: median wall seconds / context characters | 1.000 / 4171 | 0.518 / 5241 |

These are bounded fixture measurements, not large-project latency or general Agent
cost superiority. The read counts exclude Git/runpy OS reads; the larger context
retains useful evidence/actions. Both measured hook calls were read-only and ran
zero checks. The captured-bundle timing includes stale/unavailable inspection,
not a claim about an entirely valid production bundle.

Baseline package, experimental candidate and source-bound final package are
retained under `.work/plugin-improvement-20261012/`. The final
`candidate-0.1.48-efbd5b8` content inventory equals the experimental candidate used
for the independent product task. Experimental imports may create Python bytecode
cache files; distribution-file hashes are checked separately. The final CLI runs
disable bytecode writes and preserve every packaged content file. Raw command
outputs, focused RED, failed Full, package scenarios and hook measurements are
retained in that same owned directory. Product Agent logs/captures are separately
under `.work/plugin-evaluation/`; they are not protected-host acceptance.

### Product evaluation and remaining limits

The baseline and candidate workers receive fresh contexts, the same natural-language
request, product base and confirmed direction, a package discovery path and local
permission boundaries. They receive no expected patch, Skill order or grading
table. Both can read current project docs and their package's ordinary entrypoints.
External installed design guidance, cached design engine and browser tools are
recorded separately; the coordinator's port isolation, direction update and bounded
environment-retry instruction are interventions, not automatic plugin behavior.
Full UI approval, whole-project mapping, native installed discovery/hook delivery,
protected host acceptance and general quality/cost superiority remain outside this
bounded pilot. No installed Skill/Plugin, credentials, global permissions or
configuration, provider, remote branch or deployment is changed.

The baseline worker used 0.1.47 on real branch
`evaluation/plugin-ui-20261012`: commit `a1f1676` presents the three existing start
routes as illustrated cards, retains the original handlers and leaves questions
for a later task. Build, full surface/access checks and four languages × five
viewports (20 combinations) passed; `src/session.ts`, `src/content.ts` and
`data/ui.seed.json` did not change.
The stale access oracle expected two customer menus even though source/README
already defined consultation, product browsing and cart; the product test was
repaired against those independent sources. It is not a plugin defect.

The candidate worker used 0.1.48 from the same real product base on
`evaluation/plugin-ui-candidate-20261012`. Commit `7270537` prioritizes guided
discovery with existing UI tokens/components and preserves the original paths.
Node tests passed 41/41 and build passed. Its own browser operation remained
BLOCKED: offline Playwright/cache failures and system Chrome/154 GPU termination
prevented observation. A source review caught a weakened known-product viewport
assertion; `fbe16ab` restores it while retaining the new guided-entry assertion.
Supervisor browser review then independently exposed the old access-menu oracle;
`e1b8a09` repairs that single test and preserves the staff/PIN/re-lock checks.
Neither repair changes product data/state or supplies new provider functionality.

The separate supervisor reused available Playwright 1.58.2/Chromium 145 and
frozen product hashes. Surface full execution passed; UIUX only lines 1–94
passed (start viewport/audio assertions, not the subsequent consultation flow).
Four languages × mobile/desktop (8 combinations) passed. Final `e1b8a09` access
full execution passed; unchanged UI/guide hashes reused the earlier surface/UIUX
observations without rerunning them. The original access failure and a partial
lock continuation are retained separately. This is supervised product evidence,
not the candidate's autonomous browser success; different tool paths and retries
prevent a causal natural-language speed/quality superiority claim. Both UI drafts
are functionally viable within the measured scope; neither has user visual approval.

A fresh worker who had not seen the representative implementation conversation
then used final 0.1.48 against baseline-produced guide/code `a1f1676`, on the
same real development branch. It discovered README → screen design → question
and shared CSS owners, reused the existing bilingual `Text` and choice controls,
and committed `bd03682`. Selection instructions now use the shared language
component; short tablets use compact horizontal cards while phones retain their
intended different layout. Single choice, multi-select/Done, Back preserving
choices, empty-selection disablement and Skip recovery were directly observed.
A 320×568 overlap was found and repaired in the question title's existing media
rule, with failing/final captures retained. Node tests passed 41/41 before that
CSS-only adjustment; build passed afterward. The semantic consumer was real and
independent, but this demonstrates guide/code reuse, not a causal superiority of
the 0.1.48 runtime changes over 0.1.47. The product has no configured machine task
map; those task/bundle joins are proved separately by the packaged CLI fixtures.

The main agent reviewed the diff, raw and before/after PNGs rather than accepting
the worker's verdict alone. A final bounded supervisor-requested acceptance pass
measured all four languages at 320×568 and 1198×780 with `scrollY=0`: no horizontal
overflow, no first-answer/sticky-action overlap, and Korean question/instruction
text appeared once. Keyboard Tab showed a visible 3px focus outline; Space kept
the single-choice advance. At the short tablet, measured recipient-card bounds
put all six choices and actions in the first viewport. Phone later choices still
require intentional scrolling; scrolled captures are not counted as no-scroll
success. Original before/after, failing overlap and scrolled snapshots are retained.
This extra pass is explicitly a supervisor-added acceptance scope, not evidence
of an entirely unassisted run. It does not validate translations, medical facts,
real store use or every UI state. Owned local servers/browser sessions were closed.

### Retained delivery

The source-bound final package is 0.1.48 / `efbd5b8`, 19 Skills / 246 files (245 content files plus the inventory),
inventory SHA256 `967449b391a6ae5e142e3f568d0f3ef9f85d98a38a2f77fc659c74281a7dafa0`.
Its complete file set and hashes were unchanged after CLI, hook and fresh-context
consumption. The evaluation candidate's distribution inventory is identical.
Raw failures, commands, timings, limits and provenance remain under
`.work/plugin-improvement-20261012/`; product and supervised browser records are
under `.work/plugin-evaluation/{baseline,candidate,candidate-supervised-browser,followup}/`.
Connected-product artifacts from the temporary Full run were copied to the former
directory and 34 file hashes matched before removing the created plugin workspace.

Plugin functional unit `efbd5b8` and this evidence/navigation unit are integrated
only into local plugin main after rechecking its captured base and clean state.
Only the created plugin worktree/branch are removed; no push occurs. The actual
product branch `evaluation/plugin-ui-20261012` retains `a1f1676` → `bd03682`;
the same-base comparison branch/worktree `evaluation/plugin-ui-candidate-20261012`
retains `7270537` → `fbe16ab` → `e1b8a09`. Product main remains `220c945`,
with no product main merge, branch deletion or push. The separate local source
changes, product drafts and package/native-host limits must remain distinct.

The [0.1.46 design review](agent-workflow-refinement-review.md#post-0146-review)
reproduced additional kind-roundtrip, newly added criterion and task/global hook-gap
cases. Version 0.1.47 fixes them at their existing owners. Earlier results below
retain their historical scope; they do not retroactively cover the new cases.

<a id="d1d3-consumption-2026-10-09"></a>

## D1–D3 and result consumption, 2026-10-09

Version 0.1.47 preserves original exception decision hashes/binding/history through
feedback classification changes. Other classifications own separate confirmation
hashes; a new explicitly linked approval ID alone captures a new decision revision.
All criteria attached to that Feature plus consumed UI guides and their connection
set bind approval. Add/remove/reconnect changes and legacy missing connections stay
OPEN pending review; unrelated Feature criteria do not revoke the decision.
Finer criterion exclusions are unsupported until a reviewed relevance/revision
contract exists. This is editable local consistency, not authenticated user review.

The hook now separates active task cells/gaps from project cells/gaps, preserving
the full matrix in exact audit. The two-Feature fixture reports task=6/project=12
and six out-of-task cells. Large candidate discovery retains the exact selected
task/request, related criteria pointers and next action. Workflow lookup/resume/audit
accepts read-only `--summary`, joining Feature source/map/criteria, full scope,
expectations, historical status/current reuse, raw descriptor/count and obligations.
Viewer summaries mark omitted observations; positive counts mean values are in raw,
not missing runtime. Multiple tasks use a small explicitly named set of existing
state selectors, with no batch engine or all-task bundle scan on every prompt.

Focused RED reproduced withdrawn approval revival through four kinds, omitted new
criteria/legacy connections, and hook task gap=12. GREEN preserves OPEN in subsequent
tasks and accepts a new complete synthetic decision. The actual 0.1.46 package also
failed the same roundtrip assertion; the 0.1.47 package preserved OPEN. The affected
workflow/refinement/hook/viewer/execution run passed 143 tests in 314.384s. Its result
predates final bounded confirmation-history/doc refinements, whose affected checks
and final repository verification are recorded in the retained evidence.

Full ran 401 tests in 660.821s with no skips, including actual Chromium/API/Domain/
SQLite restart readback and the API-only PASS/frontend-fault distinction. Full
predates two final presentation corrections: exact detail-command root and
explicit missing/unreadable raw availability. Their focused RED is retained;
the final workflow/refinement/hook/viewer regression passed 48 in 75.567s.
No execution, approval or stale policy changed in those presentation corrections.
Resource drift, distribution validation, repository docs/cutover and formatting
are checked on the final source. Test counts identify these actual executions,
not a general reliability or Agent-quality score.

Package CLI acceptance reuses the existing rule-only quote retirement: quote(12)
and consumer.select(12) both return 12; zero returns zero and negatives are rejected.
The API/caller remain, cap check is retired, active normal contract passes and the
next related preparation executes zero checks. No replacement cap detector is
invented. The short maintenance Skill now matches this runtime proof rather than
requiring caller deletion or replacement detection for every retirement.
Source-only investigation remains possible without setup; requested runtime unknowns
and stale source observations survive subsequent tasks. Prior T5 UI/shared-owner and
detector-consolidation evidence is reused; no new product UI failure warranted redesign
or deleting further unique detectors.

Three explicit task lookups show retained stale evidence, no execution and current
PASS. A shared source-owner change invalidates the older result; current native
execution alone establishes fresh reuse. Lookup/resume/hook perform zero checks,
preserve all project/task file hashes and leave measured native execution counts
unchanged. Whole-Git/bundle invalidation is unchanged: shared-map edits can still
reopen broad review, because complete Feature-local dependencies are unproved.
Whole init remains distinct from the ability to handle a small scoped request.

Evidence, safe synthetic projects, baseline/candidate packages and exact argv/cwd/
raw results are retained at `.work/goal-reliability-20261009/` in the main checkout,
outside the created worktree. Native installed discovery is separately BLOCKED:
`codex.exe plugin list --json` cannot read the existing CODEX_HOME (os error 5).
No install/authentication/home/global setting is changed. Independent collaboration
contexts evaluate natural-language consumption separately from native host discovery;
their results and interventions must be inspected, not inferred from package success.

Independent fresh collaboration contexts compared the same natural quote request on
separate identical safe clones with 0.1.46 and 0.1.47, without answer patches, Skill
names or CLI sequences. Both completed the change, updated map/criteria/selector,
retired the rule while retaining API/caller, and reused current evidence on a later
related preparation with zero product executions. Main-agent inspection checked
their actual diffs, committed revisions, native raw values and counters. Baseline
executed three native checks (RED, precommit GREEN, postcommit GREEN); candidate
executed four (two old-contract baseline checks, precommit and postcommit contract).
Candidate assertions also cover caller negative rejection. These different selected
sequences do not establish a speed/cost improvement. Both exposed conservative
shared-map re-review; neither full init nor host-protected acceptance was claimed.

Two other fresh readers consumed the same three explicitly selected task records.
Both distinguished historical stale PASS, never-run and current reusable PASS, and
kept undecided product cells separate from check PASS. Before/after all 47 project
files matched and native calls stayed 3; reader product executions were zero. The
extra historical direct native call is in acceptance command raw, not assigned to
the never-run task. Candidate used three workflow summary lookups; baseline used
two bundle lookups and source/raw reads. Wrong-root reads, shell/JSON/BOM errors,
retries and source-discovered recovery instructions are retained, not hidden as
autonomous success. No supervisor supplied a corrective patch or CLI hint. Logged
child-process durations are not end-to-end Agent elapsed or comparative efficiency.
The minimal synthetic project's separate Core Harness audit lacks its full project
schema; ordinary workflow consumption remains independently observed. Full schema
setup was not added to clear that unrelated audit.

The final immutable 0.1.47 package contains 19 Skills and 246 files, built from
`eb76c6a6498bb13c09154e3d3a5b7fd489ba299f`. `frozen-provenance.json` ties every
package hash to that commit and records six actual lookup/resume reads with zero
product executions and unchanged project/package bytes. The ZIP SHA-256 is
`18fdae9ec2798ad65c90fa2d2f504112b7482918ae807f672f4f6976f2af188d`;
the package inventory SHA-256 is
`0f0abc877f41f1c05728ba235a7bf520d4b3d2ae7753ffcddf32794db726908d`.
`agentic-coding-0.1.47/` and its ZIP remain in the main evidence directory.
`worktree-evidence/` preserves all 35 connected-product/raw/log files byte-for-byte.
Embedded TEMP paths in those historical traces describe the executed environment;
after worktree cleanup use the archive, not those paths as current commands.
The first freeze readback completed six reads before child Git ownership rejection;
the retry used a single command-local verified safe-directory override, with no
global configuration change or product rerun. That failure and retry are retained.

## Post-review reliability, 2026-10-09

Version 0.1.46 implements the additional 0.1.45 counterexamples from the latest
refinement review. Live fetch found origin/main `e19134358141f901bb22c4af1aea17d7a9e2898c`;
local main retained 95 existing commits ahead of it. The clean review checkout
`3f6a2177ee6c08f1a9359804abac735a644ebe71` was fast-forwarded into local main,
then the implementation used a new dedicated worktree/branch. Existing branches,
the original Labeler, installed resources and global settings remain outside the change.

| Gap | Existing ownership, actual correction and verification |
| --- | --- |
| A1 | `record_feedback` preserves the captured decision hashes/binding on metadata and same-review writes. A fresh linked decision ID alone can bind a new revision; old review/hash/binding history and candidate IDs survive. Focused RED changed a revoked hash on reason-only update; GREEN keeps OPEN through metadata and related work, then accepts a new synthetic explicit approval. |
| A2 | `inspect_feedback` requires candidate, disposition, matching scope and explicit selected criteria revisions. Generic problem agreement, mismatched candidate/disposition/scope, missing legacy binding and target edits remain OPEN. Fixtures are explicitly synthetic; no unseen real UI candidate is recorded as user-approved. |
| A3 | Relevant selected requirements and all consumed UI guides bind the decision. Changing them reopens feedback and subsequent tasks; an unrelated Feature criterion preserves approval. Inspection rewrites neither records nor hashes. Feedback disposition is separate from the still-partial Feature/product result. |
| B | `inspect_check_retirements`, review validation and hash capture accept truthful entrypoint/caller dispositions. The quote cap is removed while `quote(amount)` and its caller remain: actual calls yield 12 and 0 through both paths. Prior prevention `owner_refs` bind the changed rule source, blocking unrelated or falsely referenced changes. Missing authority/failure/owner/disposition proof and active residual coverage remain BLOCKED. Legacy whole-path retirement and distinct-detector consolidation stay intact. |
| C | The existing investigation and hook expose requested/observed methods, stable unknown IDs, and outside-scope runtime. Source-only completion does not imply runtime observation. In-scope runtime unknowns and original stale hashes survive related tasks; legacy missing methods remain unspecified. Unknown/entry collisions and wrong-method substitutions cannot clear them. The original entry denominator and exact task selection are retained. |

The existing six-cell scope, prepare/execute/viewer, feedback confirmation,
shared UI guide/code ownership, active prevention selection and connected-product
runner are reused. No separate decision database, survey ledger, setup, natural-language
authority model, orchestration engine or narrower Git reuse identity was introduced.
Rule-only legacy records without a prior rule-owner connection remain BLOCKED
pending review, rather than inventing one at retirement. Submitted proof/hash
consistency does not authenticate authority or establish semantic sufficiency.

Changed deterministic branches were observed RED before implementation. Additional
independent review exposed a missing consumed-guide binding, unknown-ID collision
and misleading source reference; their focused RED/GREEN is retained separately.
The initial affected workflow/refinement/hook/viewer/execution regression passed
136 tests in 302.993s; the completed focused refinement suite passed 21 in 42.031s.
These counts identify executions, not a general reliability score. Full passed
397 tests in 618.007s with no skips after moving the owned worktree to TEMP and
allowing cleanup of test-owned child processes. The initial sandbox Full retained
two environment/path failures: Windows cleanup denied and a nested-worktree
ancestor misclassified by the existing inventory. Neither is a product GREEN.
The later hook-only correction observed a 7,145-character preview RED and bounded
its lists while preserving complete counts and exact task identity. The final
refinement/hook run passed 23 tests in 44.651s; Full predates only this final
preview correction and its added test.

The final local 0.1.46 candidate uses the existing builder (19 Skills, 246 files).
`acceptance-frozen/commands.json` retains 32 actual acceptance subprocesses with exact
argv/cwd, outputs and native exits. Quote cap retirement executed the existing
normal contract, retained negative-input rejection, and made the next related
task require zero new checks. No replacement cap detector was added. Feedback
reopened after revoked decisions/related criteria and stayed open on followup;
new explicit synthetic approval and unrelated criteria remained accepted. These
feedback states do not promote the incomplete whole product to PASS.
Investigation lookup/resume/hook launched zero runtime checks and preserved
all project file hashes. Requested runtime unknown `api-runtime` and stale
source observation `api-price` survived a related task; source-only completion
retained runtime as outside scope, not observed. Native quote execution count
remained two across read-only consumption.

The Full connected-product tests also reused real Chromium/API/Domain/SQLite
evidence: inputs 2 and 0 retained IDs 1 and 2 across POST, storage, restart and
fresh GET; a controlled FE payload error failed browser observation while direct
API/Domain checks passed. Business/architecture FE/API/Domain applicability,
reasoned exclusions and semantic review remain separate from check execution.
The API-only quote fixture requires no FE browser; source-only investigation
requires no runtime launch. Raw records, owned-server exit evidence and matrix
results remain under the worktree evidence archive, rather than new guides.

A fresh reader received only the natural-language task, package and record
pointers: 18 read-only shell calls, two tool composition errors, no product CLI
or test execution. Before/after hashes matched for 41 project/task files. It
misread the descriptor as lacking runtime evidence and inferred the wrapper cwd
incorrectly; the coordinator checked the actual raw native report and retained
both corrections in `fresh-reader-audit.json`. This is bounded record handoff,
not proof of autonomous package discovery or semantic correctness. Four earlier
acceptance harness failures (missing fixture field, expected-exit handling and
summary-only lookup) are retained; the corrected final package run passed.

Final source commit is `1875be96f23e38a1dd211c78dc2f8d800d56d92a`.
The final project-workflow regression passed 47 tests in 54.365s; repository
docs/cutover passed 13 in 3.067s. Resource drift, distribution validation and
`git diff --check` passed. The frozen package's nine additional CLI/viewer
readbacks preserved exact task IDs, OPEN feedback, current normal-contract PASS,
unknown/stale observations, all project file hashes and the execution count of
two. No tests ran during readback; every package file and ZIP byte remained
unchanged. The existing viewer consumed the actual raw assertion result.

The first freeze refused an extra Python bytecode cache created during candidate
execution; shipped file bytes were identical. The final trial used process-scoped
`PYTHONDONTWRITEBYTECODE=1` with a fresh builder output and exact inventory equality,
without changing global configuration. An initial readback assertion selected
the independent maintenance context for feedback; the corrected reader uses the
retained feedback context separately. Both harness failures remain evidence.

| Frozen artifact | Binding |
| --- | --- |
| `.work/post-review-implementation-20261009/agentic-coding-0.1.46-frozen/` | Byte-identical to the final executed candidate; each distributed source is checked against the source commit with CRLF normalization. |
| `agentic-coding-0.1.46.zip` | SHA-256 `91c5a29b9234715ad896d842cbf57bb7f4b5b8125fdb6b3061fa2c086447139d` |
| `package-files.json` | SHA-256 `2e457c5ecc664b3534abb2e251582519c9e927e5a6b8b54c07f15ec57b8ae5bd` |
| `frozen-provenance.json`, `frozen-readonly-readback.json` | Complete per-file/source hashes, actual commands and before/after evidence. |

Archived worktree captures retain their original absolute paths as historical
evidence; those paths are not runnable after worktree cleanup. The retained
acceptance projects and frozen package have separate preserved paths. Package
source bytes remain bound to the source commit even when later delivery docs
advance local main.

Evidence is retained outside the created worktree under
`.work/post-review-implementation-20261009/`: baseline/plan, RED/GREEN captures,
native-host BLOCKED, exact argv/cwd/stdout/stderr and package acceptance artifacts.
The new native `codex.exe plugin list` failed to resolve existing CODEX_HOME with
access denied / OS error 5 in the current sandbox. No host/security, credentials,
existing installation or global setting changes were used to bypass it. Direct
package execution remains distinct from native discovery/context/protected acceptance.
Long-running multi-writer or general Agent cost/quality remains unverified.

## R0–R4 implementation, 2026-10-09

Version 0.1.45 implements the reproduced refinement gaps on the existing workflow,
task/context, feedback, review and maintenance paths. The starting local main was
`f4c61721fdd8e8aefeb8df6ded5745c14343f2a1`; live fetch and fast-forward pull
preserved its 93 commits ahead of origin/main. Work used a new independent TEMP
worktree. The existing 0.1.43 review/findings continuity fixes were verified and
reused, not implemented again. Whole-Git invalidation and one writer per task
remain intentional; atomic replacement is not concurrent-write support.

| Scope | Implemented or reused behavior and actual evidence |
| --- | --- |
| R0 | Reused the real Chromium/API/Domain/SQLite fixture and runners. Browser input 2 and 0 yielded IDs 1 and 2 with the same values in POST, SQLite, restart and fresh GET. An independent API-only run saved those exact IDs/values and rejected -1. A controlled FE payload increment then failed the browser observation while direct API and Domain tests passed. This is a connected-flow counterexample, not separate cell PASS used as a substitute. |
| R1 | `diagnose` can retain investigation on the same ordinary or Harness task without creating workflow configuration. Stable entry IDs, conditions, permissions, source/evidence hashes, unknowns and next actions survive exact-context lookup/resume and the prompt hook. Removing prior entries, changing captured permissions and refreshing stale observations through metadata changes are rejected or remain PARTIAL. Large hook previews retain counts and exact-lookup routing. |
| R2 | Existing requirement violations keep original-oracle RED/GREEN and a distinct normal case. New requirement changes require authorization, changed criteria and real prepared current native confirmation. A deliberately wrong adapter was independently contradicted, actually failed, then repaired at the adapter and rechecked without changing product/requirement. Fresh tasks consume these decisions/results. Intended differences require linked actual user review; missing/deferred/opinion reviews stay OPEN. Environment limits and unknown causes never become resolved from agreement or supplied GREEN. |
| R3 | Existing actual duplicate-detector RED/GREEN consolidation and unique protection remain unchanged. A living Feature can retire one requirement with changed criteria, authorization, removed entrypoint/caller, remaining-consumer review and retired failure scopes, without inventing a replacement detector. The focused example actually calls the old entrypoint before removal, confirms entrypoint/menu absence afterward and executes the retained CLI. Missing scope proof, revoked authority and active coverage links remain BLOCKED. |
| R4 | Source/generated resources, affected regression selection, local package version and support documentation are updated. Natural-language package-use trials and a separate fresh-context reader exercise the real paths without Skill names, CLI sequence or an answer patch in their task. Local package use is separate from native discovery/installation/protected acceptance; the latter remains unverified for this candidate. |

The investigation report is an Agent-declared semantic inventory. It does not
prove every possible entrypoint or that a supplied source reference is direct
runtime observation. In the read-only survey, nine entries cover seven HTTP
branches and two documented verification paths under explicit source-only
conditions. Their READY_FOR_REVIEW means that declared source survey is ready
for review; each entry's runtime unknowns remain retained. A deterministic
observed/unobserved example remains PARTIAL, as do stale references. No existing
Labeler UI candidate was accepted or repaired on the user's behalf.

The first paired trial accidentally included the fixture's hidden `.harness`
configuration. It is preserved as configured source-survey evidence, not counted
as unconfigured acceptance. The coordinator corrected preparation once and used
a new pair without `.harness`; both have identical 15-file source hashes and Git
base `4d47249775c043fe1ac3332a0c3dad6fa3c79130`. The old package produced manual
read-only notes and no task context. The candidate created one investigation task;
a fresh Agent consumes its exact context without re-running the survey.
Both surveys found the declared maximum 100 versus lower-bound-only code/tests,
but kept 101 runtime behavior unverified rather than claiming a measured defect.

Candidate survey time was 138 seconds through evaluation preparation; the old
survey has only a measured 2.4-second record-writing interval, so these are not a
speed comparison. The old survey corrected one read-only shell syntax error;
the candidate survey reported no workflow retry. The fresh reader corrected one Windows selector-quoting error and one report-serialization error without launching product checks. Initial configured-trial serialization
rework and the preparation correction are retained, not hidden. Two independent
review counterexamples (metadata-only stale refresh and intended-difference
acceptance without user review) were reproduced RED, fixed and passed GREEN.
Usage/cost and complete model-call totals were not provided. No general Agent
effectiveness, latency or cost improvement is claimed from this bounded sample.

Actual commands and raw outcomes are retained below the owned evidence root
`C:/Users/YS/Desktop/python/Skill_Management/.work/r0-r4-delivery-20261009`.
`r0-r4/protocol.json` freezes requirements and comparison conditions;
`r0-r4/review.html` is a thin view of those records, not another result database.
Focused RED, second RED, independent-review RED/GREEN, native execution,
connected-browser/API-only/FE fault artifacts, final Full and packaging manifests
are kept separately. The initial Full ran 385 tests with one Windows child-tree
cleanup error under sandbox permissions; an identical focused host-permission
run passed. The failed run remains evidence and is not promoted to PASS.
The final host-permission Full passed 387 tests in 609.201 seconds with no skips;
its capture wall time was 609.5 seconds. Production workflow/hook code was fixed
before this run. The retirement runtime assertions were strengthened afterward
and the final affected module passed all 11 tests in 35.711 seconds. Distribution,
generated-resource drift and `git diff --check HEAD` passed. The earlier existing
native execution suite passed 50 tests; its evidence covers actual violation
RED/GREEN and detector consolidation, not a separate 50-test addition to Full.
Immutable source/package hashes are recorded in the delivery manifest and the
package-freeze section below.

`codex.exe plugin list` in the current sandbox failed with OS error 5 accessing
the existing CODEX_HOME. No global configuration/authentication or installed
resources were changed to bypass it. The recorded manual disable of in-app
browser control was honored; the existing Chromium fallback was used. Native
new-version discovery, context transmission and protected acceptance remain
unverified. Package hashes attest bytes, not natural-language task quality or
host enforcement. Removed-entrypoint/consumer sufficiency and evidence authority
remain semantic review responsibilities; local code checks binding consistency.

The original Labeler remains read-only at clean `6860d11f640b81fe2071e0a44c5b16e66673ccfa`.
Retained relocated absolute-path-bound task records are historical evidence;
actual fresh-context reuse is verified at their original trial paths before
worktree removal. Only this task's worktree/branch is removed after local main
integration. No push, deployment, installed-Skill update or global setting change
belongs to this delivery.

## R0–R4 package freeze and local delivery, 2026-10-09

The immutable 0.1.45 package is built from source commit
`3be9eec2f116020f04116d263a60dd50fb177c9b` with 19 public Skills and 246 total files.
All 245 payload hashes match the candidate used for the final unconfigured
natural-language survey and fresh-context read. Strict byte inventory validation
passes before and after direct frozen-package lookup. That lookup returns the
same task ID and nine entries, executes zero test commands and leaves all 17
project/source/task/evaluation file hashes unchanged. This attests direct local
package use; it does not establish native installed-host discovery or enforcement.

The frozen ZIP SHA-256 is
`1406519067e79e34541f31b151d039c6d051437861e6a7eb6b777601b8586f70`;
its inventory SHA-256 is
`ebe6d323f63f843f964da0899754f670f507a5790a1a01b315103161e6c6c8ad`.
`r0-r4/frozen-provenance.json` retains every file hash and the exact source commit;
`r0-r4/frozen-readonly-lookup.json` retains the actual lookup and unchanged hashes.
The preserved 0.1.44 package and installed resources are untouched.

Delivery retains source, synthetic trial Git histories, raw outcomes, trace and
screenshots below `.work/r0-r4-delivery-20261009`; no original project data or
credentials are copied. `r0-r4/delivery-manifest.json` records the final local main
commit, synchronized origin, merge, original Labeler state and worktree removal.
The durable source/package record is separate from expiring execution artifacts.

## Delivery scope, 2026-10-09

G1-G6 are completed within the bounded local implementation, independent trials,
package freeze, isolated product acceptance and product-discovered common repair
recorded below. This does not claim native installed-host acceptance or universal
Agent effectiveness. The final affected regressions passed; the 369-test full run
belongs to the earlier commit explicitly named below, not the final source.

Evidence and isolated project Git histories are retained before worktree removal at
`C:/Users/YS/Desktop/python/Skill_Management/.work/generic-completion-delivery-20261009`.
Regenerable node_modules directories are excluded. Relocated absolute-path-bound
records are historical evidence, not a claim of current reuse at the archive path.
The isolated Labeler source change is retained there and is not merged into the
original Labeler repository. Only Skill_Management local main integration is in scope.

## Generic workflow acceptance before product trial, 2026-10-09

The common implementation now preserves relevant reviews and unresolved findings,
requires fresh scope decisions, binds ordinary request metadata, bounds prompt
context, and rejects dot inventory roots. Dependency-scoped reuse was reviewed:
the declared inputs do not attest a complete transitive dependency closure, so
whole-Git invalidation remains intentional. No narrower reuse or speed improvement
is claimed. Unchanged task/bundle lookup and completed execution resume remain
read-only or zero-execution paths.

Product-independent Agent trials used the local package and ordinary task requests.
They created their own project connections from existing source and public local
runners. The API variant has no frontend; the web variant uses the existing real
Chromium/SQLite runner. Initial connection included both implementation ownership
and explicit untested boundaries; registered-file coverage alone was not treated
as complete functional discovery.

| Flow | Observed result and limit |
| --- | --- |
| Feature implementation | API item-by-ID: original valid-ID lookups failed, then 64 assertions passed with exact POST-returned IDs, invalid-ID rejection and restart readback. |
| Verification lookup | Main-agent read-only package views confirmed current PASS/REUSABLE with zero commands; stale historical runs and open semantic findings remain separate. |
| Feedback repair | API storage overflow: confirmed RED failed only the two overflow response assertions; committed fix passed 75 assertions, preserves maximum valid quantity and existing rows. A subsequent task inherited RESOLVED feedback and the prevention rule without rerunning. |
| Shared UI and next request | Guarded save/history reload passed 21 browser assertions; the subsequent saved-count change reused the guide and shared implementation, with RED/GREEN at 23 assertions. The final committed package run passed all 23; the main Agent independently confirmed current reuse and mobile/desktop screenshots. |
| Verification maintenance | An isolated copy with a deliberately stale command was BLOCKED on the real missing-file error; repaired command passed 58 assertions, and the next request reused it without execution. |
| Check value | In a disposable mutation, bypassing the Domain negative guard failed its unit test while the API test still passed through the SQLite constraint. Both checks were retained for distinct detection; the Domain command remains explicitly manual, not automatically selected. |

API source commits are `edd5267` (item lookup and semantic findings) and `8133246`
(storage-boundary repair). The separate maintenance trial ends at `a1d33e1`.
Web commits are `8c981e5` (shared save/refresh) and `c843fac` (saved count).
Their `.work/generic-completion/` projects retain original failures, fixed outcomes,
process-exit observations and subsequent-request records. Actual product-semantic
issues outside those bounded requests remain visible; PASS does not mean production
security, concurrency or every startup failure was verified.

The coordinating Agent supplied bounded requests and later review findings, clarified
one Windows execution boundary, and corrected scope/final-evidence sequencing.
This is package use by ordinary Agents with recorded coordination, not an unassisted
native-installation trial. Web r1-r3 repeated the same 14-assertion behavior after
late documentation edits; those recaptures added binding freshness rather than new
product coverage. Other retained input/oracle corrections are not counted as valid
RED evidence for product repair.

The tested candidate is 0.1.43, source `c2c98b1`; its 245 payload hashes match.
The independent audit found only an interpreter cache outside its manifest after
use. Strict package validation correctly rejects that used candidate as a clean
release input. A fresh build from `3901e2686e229d8634969be05ec5be37401abb7d`
passed strict validation with 246 total files and exactly the same 245 payloads.
The frozen `agentic-coding-0.1.43.zip` SHA-256 is
`54c0ee464bec140a83fcda69f8acfe3bb38583f9f3439894a2aba3065a9fcf14`;
its inventory SHA-256 is
`c036cd4ab9209b6f96d02dea067ab2571480794eed49874bb95b15404e8dfb84`.
`.work/generic-completion/frozen-provenance.json` records support boundaries.
The frozen artifact is retained separately from the product trial's identical
working package copy. No existing installation, global configuration, provider,
push or deployment changed.

Only after this G1-G4 acceptance and freeze, Labeler main was inspected. Its clean
main was `000ffd1a868c84abe4657785f1e8c7813a9df749`, 69 commits ahead of the clean
original checkout `6860d11`. A new independent Git snapshot contains 437 tracked
source files; `.dev.vars.example` was excluded along with all untracked data,
credentials and original Git state. Product acceptance ran in
`.work/generic-completion/labeler-product-acceptance`, initial snapshot `ab9766f`.
The bounded request covers product entry/management/search and Escape/IME behavior;
no Labeler-specific map, adapter or answer patch was supplied.

## Product-discovered common console repair, 2026-10-09

The 0.1.43 Labeler task completed its browser capture successfully (13 registered
assertions, native exit 0), saved its bundle and state, then failed while printing
JSON containing an en dash under Windows cp949. The browser was not rerun.
A UTF-8 read-only view confirmed the retained PASS. The same D1 was subsequently
read through a new Worker process and browser context.

Four focused REDs reproduced the same defect in workflow execute, result-viewer
execute, the prompt hook and Harness inventory. The nine terminal JSON print sites
now use ASCII-safe JSON serialization. Decoded values, state/evidence files,
digests and the hook's inner context are unchanged. Focused GREEN preserves
Unicode, completed-execution zero-command resume and read-only state bytes.
The affected workflow/hook/viewer regression passed 118 tests (353.311s),
and the configured Harness regression passed 143 (54.182s). Documentation checks
(3), resource drift and distribution validation also passed. Logs and actual exit
codes are retained in `.work/generic-completion/console-*`.
Version 0.1.44 was frozen from `a4edbb077b0f76e7c07876c48661f820615884d4`:
245 payload files, 246 total files, strict inventory and ZIP comparison passed.
ZIP SHA-256: `deabfe49e33cf73c5ab65b63fb828e8b1d4ddbdcf33462f8e90cbe034782748b`.
A separate working copy recovered the original Labeler task under explicit cp949,
without a UTF-8 override: execute-resume and lookup returned exit 0, PASS and zero
commands, preserving run `41d9bbbb-9826-4d55-87f0-67fa47e3c7b6`.
Follow-up prepare returned NOT_REQUIRED with zero commands; its fresh scope stays
PARTIAL. Korean names and the en dash survived JSON parsing; all 29 protected
task/evidence files retained their hashes. The original 0.1.43 failure is preserved.
The capture wrapper's setup guard and SystemExit bookkeeping errors are separately
recorded in wrapper-diagnostics.json and are not package failures.
The independent API project's cp949 bundle summary also returned PASS with zero
commands. Its successor lookup retained expected PARTIAL scope (exit 2); all 287
work files and Git status remained unchanged. Raw captures are in
`labeler-product-acceptance/.work/product-management-search-g6-package-0144-20261009`
and `g6-api-console-0.1.44` beneath `.work/generic-completion/`.
No installed distribution or global console setting changes.

## Actual product connection findings, 2026-10-09

The Labeler trial exposed project-owned observation and environment assumptions.
The original broad browser runner expected two quantity inputs simultaneously,
but the current print queue expands one row at a time. Its repair preserves both
saved quantities (2 and 3), click order and asynchronous restoration, and checks
the detail inputs one at a time. A later pamphlet-pagination timeout remains
unresolved and is outside the bounded product-search request; the broad runner
is not reported as passing.

The same Wrangler/local SELECT 1 failed with a fresh deep storage path and passed
with a shorter path in the same project (actual SQLite path length 248), as well
as a separate fresh TEMP path. This is evidence of a local path-length constraint,
not a proved operating-system threshold or a product SQL defect. No global path,
permission, provider or original data setting changed.

Live attempts created a category and two products through the actual UI and
Worker API. Repeated observation failures included the displayed range format,
selectors reaching a hidden PhraseManager, a leftover local variable, and a
network expectation that ignored the existing 10-second query cache. These are
retained rework, not product REDs. The main Agent independently checked the live
API observations and screenshot. A focused same-instance comparison then showed
an alpha result returning from cache in 1.219 seconds with no second alpha GET,
while a previously unqueried beta name produced one GET and the correct row.
The early input-event mismatch hypothesis was superseded by that observation.

Coordination included an independent print-runner review, local path probes,
review of selector/expected-value mistakes, the cache hypothesis, and final
commit/capture sequencing. This is supervised package use, not an unassisted
native-host success. Project-owned guides and assertions carry the resulting
prevention rules; no Labeler-specific rule belongs in the common plugin runtime.
The product commit is `bfeb622c7dbd85564d74e26c916bcc437fbb8eaf` (clean).
TypeScript and focused lint passed. Official browser run
`41d9bbbb-9826-4d55-87f0-67fa47e3c7b6` matched all 13 native assertions:
UI-created category/products, actual POST/GET IDs, search, immediate Escape
requests (23/53ms), and composition-event draft preservation with no intermediate
search. After owned Worker PID 19576 stopped, a new PID 17600/browser read the
same two IDs from the same fresh D1. The main Agent independently inspected both
raw reports, the final screenshot, and a read-only SQL query of the test database.
These timings measure request initiation, not API performance; synthetic composition
events do not establish physical OS IME behavior.

Task `e32b7bff-274c-4fcf-8518-f2a74bd548a9` reached READY_FOR_REVIEW. Follow-up
`5107d320-3988-458d-b6e6-14ff1acc8ddb` inherited its results/guide; prepare was
NOT_REQUIRED with zero selected/executed checks. Its fresh scope decisions remain
PARTIAL as intended, not a false completion. The 0.1.43 full task output required
a process-local UTF-8 override because of the console defect above. The 0.1.44
recovery above now works under cp949 without rerunning the browser. Resources and original failures remain under the
snapshot's `.work/product-management-search-*` paths. Owned services were stopped;
the main Agent separately identified and stopped the initial snapshot Vite PID
26048, which the later handoff had conservatively left untouched.

## Independent cleanup observation repair, 2026-10-09

The independent first-connection review found a project-runner observation defect:
the second owned server was terminated, but its raw record still said `running`.
This was not evidence of a live process leak. The source connected-product fixture
now records both waited process exit codes and final stopped states; its registered
native assertions require those states and no cleanup errors. The existing browser
regression first failed on `['stopped', 'running']`, then passed with two independent
real browser runs and retained, non-overwritten artifacts. Evidence is retained in
`.work/generic-completion/cleanup-{red,green}.log` and
`.work/connected-product-artifacts/5dbf6ceb-cad2-4c03-a6f1-40488cb4868e`.
This fixes the project-owned acceptance runner, not the plugin runtime. Old package
and project reports remain historical and unchanged. The web follow-up Agent also repaired the observation in its separately owned
project and its final 23-assertion run observed both service exits.

## Independent trial findings before package freeze, 2026-10-09

The clean `0aa96ae` source passed the full repository suite: 369 tests in 537.359s,
including actual browser artifacts retained under `.work/connected-product-artifacts/81986db5-66dd-4d36-8e19-5af817866832`.
This full run predates the two focused corrections below; do not attribute it to
the later source. The existing installed distributions remain untouched.

An independent code review found unbounded request context. A 6,013-character
request generated 14,262 characters of hook JSON; eight long task requests produced
57,847. The hook now previews requests and marks omitted detail while the task
record and exact lookup retain the complete content. Its fallback enforces the
5,500-character JSON budget. Focused RED/GREEN checks retain exact current-task
identity, eight candidates, unchanged state bytes and normal short requests.

The API first-connection Agent independently encountered `roots: ["."]` producing
zero inventoried sources. `Path` normalization removed dot segments before the
validation check. The canonical guard now rejects raw dot segments instead of
silently accepting an empty inventory. Dot, trailing-dot-root, prefixed-dot and
nested-dot cases failed before the fix; an ordinary `src` root still surveys both
source files. The original experimental package is unchanged and its failure is
retained separately from this correction. The final affected workflow/hook/docs
regression passed 49 tests (`.work/generic-completion/context-regression.log`);
generated drift, distribution and diff checks passed.

## Generic completion G1 request binding, 2026-10-09

Ordinary `start`/`begin` accept `--request-summary` and repeatable `--outcome-ref`
for safe existing project files. Candidates, task lookup and the read-only prompt
hook expose the same request. Multiple matching Features remain ambiguous until
explicit context/state selection; no timestamp or host session assumption is used.
The metadata is part of immutable task identity. Follow-ups supply their own
summary rather than silently inheriting the previous request. Harness work still
references its existing contract via work ID.

A focused real CLI RED/GREEN covers two requests with the same target, ambiguous
resume, exact lookup with byte-preserving state, hook readback, follow-up request
reset, outside-project reference rejection, and rejection of request edits through
lookup. The affected workflow/hook, documentation and Harness regression passed
91 tests (`.work/generic-completion/request-regression.log`). These are local
CLI/hook observations, not native-host task discovery.

## Generic completion G1 continuity repair, 2026-10-09

Work starts from local main `d3bb741` (contains `23e5d15`) in a new
`generic-completion-20261009` worktree, branch `wp-20261009-generic-completion`.
The original checkout at `172dfa3`, old work records and installed distributions
are preserved. The removed path in the request was recovered through main's
tracked execution prompt; no old worktree was reconstructed.

Ordinary follow-up tasks and Harness start now share current map-review reuse.
New scope decisions remain required. Stale reviews retain unresolved product and
architecture findings; omission in a replacement product review does not resolve
an issue. Architecture inheritance cannot be edited to claim repair without the
existing current-scope evidence validation. Retired Feature findings remain
visible, and a new active review supersedes obsolete retirement approval.

Focused tests first reproduced lost reviews/product findings, lost retired
findings, unvalidated inherited resolution, and active/retired shadowing. Each
was repaired with the same criterion and normal retirement/fresh-review controls.
Workflow/hook plus affected Harness and documentation checks passed 88 tests
before the final retirement correction. Final affected regression passed 90 tests;
resource drift, distribution validation and `git diff --check` also passed.
Logs are retained at `.work/generic-completion/{regression,drift,distribution}.log`.
The independent Agent review found the retirement shadowing boundary; its finding
was reproduced and fixed by the main Agent. This is local deterministic behavior
and independent code review, not package/native-host or product acceptance.

At the end of this initial unit, ordinary request binding and the reuse-boundary
review were still pending; the following units above record their resolution.
No Labeler preparation, installation, provider call, push or deployment occurred
during this common-state repair.


The prior 2026-10-07 user-function source was plugin **0.1.42** in the isolated
`wp-20261007-connected-workflows` worktree, based on `67e06d3eaedda203156b932bf1ac7e62be63df8a`.
The A/B/C/D sections below distinguish deterministic CLI behavior from reused
Agent diagnosis/design/semantic review. The package was not installed or published;
ordinary/global installs, original Labeler and protected branches were unchanged.
Local user-function completion does not resolve protected-host acceptance or prove
new native Agent quality/performance. Historical host-first limitations below are
not prerequisites for this implementation.

## Connected actual product use, 2026-10-07

The user can now connect an ordinary request once, prepare/execute its required
checks, restore its decisions, record feedback/review and inspect current results
through the same task context. Agent meaning/causal/visual judgments remain
explicit. The CLI never invents host session discovery or selects the newest task.

The project-owned [connected product](../../tests/distribution/fixtures/connected_product/docs/index.md)
uses the installed local Playwright/Chromium, stdlib HTTP and a fresh SQLite file.
It owns Launch/Doctor/Drive/Evidence/Cleanup. The packaged workflow/capture/viewer
does selection, execution binding, collection and current lookup. A real keyboard
form submission produces POST/API/Domain/storage observations; zero remains valid,
negative input is rejected, and a restarted service plus browser reload returns
the persisted values. Native reports contain 14 distinct observations, screenshots
of both 390px screens, trace, commands, target, IDs, API bodies and SQLite rows.
Service/temporary storage cleanup retains those observations and artifact hashes.

Actual usage was performed in a new independent Git project under
`.work/connected-acceptance/project`, using only new source files and fresh data.
The package entrypoint was `.work/packages/agentic-coding-0.1.42-connected/skills/agent-workflow/scripts/project_workflow.py`.
The final local package is `.work/packages/agentic-coding-0.1.42-final`; executable
workflow/viewer/capture bytes are unchanged between these builds. These are local
packages, not installation updates.

| Actual case | Observed result and retained limit |
| --- | --- |
| Two ordinary tasks and exact resume | No selector returned BLOCKED plus both candidates. Explicit context restored only task `9dc32824-1a48-46d5-a4e0-ddec50ae735d`; the independent task's bytes were unchanged. |
| Real defect and owner repair | Two independent registered RED executions detected the absent Domain negative guard and small shared UI token. Restoring the shared Domain boundary and CSS owner produced PASS; unchanged negative and valid-zero assertions were preserved. |
| PASS and semantic gaps | Tests passed while architecture rows were NOT_RUN and six task cells UNDECIDED. A later missing type-case connection was MISSING. Its unchanged, out-of-request branch was explicitly NOT_REQUIRED, with reason; no type-case test PASS is claimed. |
| Feedback and UI follow-up | Two feedback entries became RESOLVED with changed owner bytes, original RED/current GREEN and nearby normal assertions. The next UI task carried feedback/prevention/results and the same guide/token/component links; prepare reused the valid check with zero launches, while new semantic decisions remained pending. |
| Verification maintenance | The real trial exposed missing ownership for runner/config/assertion/test/guide assets despite COMPLETE registered coverage. Mapping was repaired, stale evidence was rejected and the changed conditions were executed once. The original task then reached READY_FOR_REVIEW with scoped COMPLETE coverage. |
| Detector consolidation | The old and replacement RED runs detected the identical negative criterion; replacement GREEN accepted zero. The obsolete registered detector/command/assertion was removed, the stale guide instruction repaired and retirement reported PRESERVED. The remaining full-stack check was retained because no independent equivalent evidence covered all its behavior. This bounded proof does not justify unrelated test deletion. |
| Observation failure | A separate source-only project ran with a process-local PATH lacking Node. It reported BLOCKED, zero observations, skipped browser drive and the actual prerequisite error. Its command ran; the browser action did not. This differs from the observed product assertion ISSUES. |
| Read-only and reuse | lookup, task resume and completed `execute --resume` launched zero commands and left source/task/evidence bytes unchanged. Follow-up prepare was NOT_REQUIRED. No service is started by a lookup request. |

Original raw/transcript evidence remains under `.work/connected-acceptance/`:
`summary.json`, `transcripts/01-*` through `transcripts/39-*`, project task runs
and the independent observation-blocked project. `use_cases.py` and
`maintain_and_blocked.py` and `repair_artifact_scope.py` are this request's fixed usage sequences, not shipped
workflow engines. They call the existing packaged CLI. The tracked project runner,
configuration and assertion sources are reusable; `.work` evidence follows the
repository retention policy. Historical October 6 evidence below belongs to the
previous worktree and was not copied into this one.

Final artifact comparison found an actual project-runner defect: two differently named
JSON reports used the same parent for trace/log files, so the first report's artifact
hashes no longer matched after the second command. That focused RED is retained
in `artifact-scope-red.json`; the initial raw observations survive, but those early
shared-path traces are incomplete proof. The source runner now gives each report
a new stem-named artifact/storage directory and refuses existing directories.
New two-detector RED and one-detector GREEN were executed for that changed owner;
all trace/log/screenshot hashes and disjoint paths were checked after cleanup.
Only the corrected runs back the final feedback/preservation links; historical
failures were retained. `artifact-scope-green.json` names the corrected raw reports.

A fresh Agent in the existing collaboration host received a natural-language
request for one exact task's results and the final package location, without CLI
or Skill ordering. It discovered agent-workflow and chose connect then lookup.
It reported the correct task, current reusable PASS, resolved feedback, preserved
detector and explicit exclusion with zero check/service launches. Independent
before/after hashes confirmed source/task/evidence bytes unchanged. This is one
package-path-routed natural lookup, not native plugin auto-registration, installed
acceptance, implementation/repair effectiveness or a general Agent benchmark.
Its retained observation is `agent-lookup.json`; it preceded the project's artifact
layout repair, while the package executable bytes remained identical.

Current runtime changes additionally measure explicitly registered public installed
dependency files during preparation, execution and lookup. Changed bytes invalidate
reuse; labels do not establish validity. This declaration does not cover every
transitive library, environment variable or remote dependency. Native SKIP, NOT_RUN,
UNKNOWN and observation BLOCKED are retained instead of becoming ordinary assertion
ISSUES. A native NOT_REQUIRED cannot silently exclude a selected required check.
The existing repository unittest adapter also consumes the same task context.

### Current maturity across seven user capabilities

Status **verified** means implemented and actually used in the bounded local
cases above. **Agent** identifies work supported by existing Skills and humanlike
judgment, not automatic code. General success/quality across projects remains
unverified; absent host context transport is an incomplete connection.

| View / status | User can do | Implemented code/CLI | Existing Skill / Agent responsibility | Actual evidence and scope | Remaining gap |
| --- | --- | --- | --- | --- | --- |
| 1. Delegate and inspect / verified + Agent | Connect one request, execute needed checks, resume and query gaps | Task identity/context, candidates, selected plan pointer, capture/bundle/current lookup and reuse | agent-workflow selects procedure and judges sufficient completion | Multiple tasks; actual packaged browser flow; zero-launch lookup/resume | Native installed-host discovery and automatic context transport unverified; no general completion-rate study |
| 2. Business and architecture × FE/API/Domain / verified + Agent | View six applicability/evidence cells and separate test PASS from review | Matrix, UNDECIDED/MISSING/NOT_REQUIRED/NOT_RUN/ISSUES/BLOCKED/STALE and structured architecture findings | Requirements, causal flows, ownership and semantic sufficiency | Real FE→API→Domain→SQLite→fresh read; per-owner reviews; tests PASS with review pending | One small quantity model; arbitrary JSON types excluded; concurrency/auth/production not tested |
| 3. Feedback improvement / verified + Agent | Attach complaint, trace owner repair, keep original defect and nearby normal case | Existing feedback record, changed owner baseline, bound RED/GREEN, unresolved chain and follow-up consumption | diagnose traces cause and chooses the actual repair | Domain error failure, shared boundary repair, negative RED and zero GREEN; two RESOLVED entries | Diagnosis quality and all prevention classes remain Agent work; broader user-impact evidence absent |
| 4. UI standards / verified + Agent | Reuse a guide and shared CSS/component, see affected consumers | Guide/token/component/consumer links and reopened obligations | impeccable/accessibility choose criteria and judge actual screens | Shared token repair, both 390px screenshots/DOM/focus/targets; 1280px keyboard drive and follow-up reuse | No frozen screenshot diff, broad screen-state inventory or full accessibility audit |
| 5. Verification maintenance / verified + Agent | Repair stale command/guide/observations and rerun only affected checks | Current definitions/conditions, source/runtime drift, capture binding and read-only maintenance | setup/maintain-project-verification own adapters, map and assertions; Agent judges missing routes | Browser input/order, duplicate report observations and Windows SQLite lifecycle were repaired; asset ownership gap and stale guide corrected | First connection still requires project analysis; only this project/runner demonstrated |
| 6. Structural guardrails / verified + Agent | Keep root-cause prevention active across related tasks | Active prevention/check joins, feedback carry-forward, revalidation and scope selection | Agent chooses type, boundary, shared state/constraint or check appropriate to the cause | Shared Domain function plus SQLite constraint; shared UI owner and unchanged regression/normal assertions; next-task reuse | No automatic guardrail invention; unlisted runtime drift and protected enforcement remain outside proof |
| 7. Remove unnecessary checks / verified + Agent | Inspect overlap/cost, consolidate with proof or retain | Historical execution joins and old/replacement RED + current GREEN retirement gate | Agent judges detector meaning and normal cases; counts never authorize deletion | Actual two-command RED to one-command GREEN; PRESERVED retirement, remaining detector retained | One equivalent-command case; no broad heterogeneous-suite deletion or efficiency comparison |

### Pinned pstack comparison

Compare against `cursor/plugins` **23e4138daa01c42d4969f7a5465f82704e64f798**,
pstack **0.15.6**, as fixed in [pstack analysis](pstack-analysis.md).
The pinned manifest/router/create/maintain/bug-fix and visual-parity/session-pickup/
hillclimb primary source bytes were checked again on October 7. No latest-version
claim, pstack execution or same-task/model/host head-to-head experiment was performed.
External instructions were read as evidence and were not adopted as authorization.

| Item | Our current provision | Useful pstack design | Our remaining gap / experiment needed |
| --- | --- | --- | --- |
| Entry and composition | Existing agent-workflow plus identity-bound current task | [poteto router](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/SKILL.md) has explicit task playbooks | One bounded natural lookup is separate from general installed discovery; compare real multi-task outcomes before ranking |
| Initial project verification and upkeep | Existing setup/maintain, registered native command/assertion and project-owned lifecycle | [create](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/create-verification-skill/SKILL.md) proves its generated path and retained evidence; [maintain](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/maintain-verification-skill/SKILL.md) requires live feature driving | Other project/platform first connections are unverified; setup/upkeep quality not compared |
| Full-stack results and gaps | Explicit business/architecture matrix, raw joins, selection and STALE reuse rules | Project feature maps and real control/evidence recipes | Semantic completeness remains Agent judgment; no equivalent pstack result experiment |
| Cause repair and prevention | Owner repair, unchanged failure + normal evidence, active prevention links | [bug fix](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/bug-fix.md) insists on same-surface cause and revalidation | Broader cause/prevention accuracy is unmeasured |
| UI and verification standards | Linked shared owners, actual DOM/screenshots and maintained driver | [visual parity](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/visual-parity.md) fixes a baseline and uses image diff | Pixel equivalence is not implemented by this example; generic visual quality not compared |
| Keep useful verification | Bound detector preservation and reasoned retention | [hillclimb](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/hillclimb.md) freezes a sensitive metric and preserves regression gates | This detector proof is not a pstack pruning experiment or a measured overall cost win |
| Interruption and follow-up | Exact state/context restores decisions, results, feedback and remaining obligations | [session pickup](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/session-pickup.md) reconstructs operational context before routing remaining work | Conversation/tool context transport depends on host/Agent; richer transcript recovery is not automatic |
| Packaging and actual completion | Local 0.1.42 package, real packaged CLI use; native install/protected acceptance separate | Pinned Cursor manifest and routed control/shipping ecosystem | No current pstack host run, current plugin installation or comparative completion/cost/quality study |

**Installable plugin:** local packaging/distribution checks and actual packaged CLI
use are confirmed; this task did not install the new version.
**Reliably delegated plugin:** bounded project execution/repair/lookup is confirmed
with explicit connection and Agent judgments. General native-host task completion,
context forwarding and protected acceptance remain unverified. Protected-host
absence does not block the implemented local user functions.

The next three priorities are host-owned explicit context transport/discovery,
additional real project runners/cases with environment/data conditions, and frozen
UI state baselines plus broader detector sensitivity evidence. No generic runner,
dashboard or duplicated task ledger was introduced.

Verification retained both the actual usage and focused implementation checks:
the A workflow/hook/viewer/docs/package modules ran 108 tests successfully; the B
execution/unittest modules reported 65 tests OK, with a PowerShell wrapper exit 1
from redirected stderr diagnostics (native exit was not separately retained).
New focused B tests returned exit 0 directly. The new actual two-report browser
regression ran one case without skips (12.114s), and configured-project cutover
ran nine tests successfully. Resource drift, distribution and formatting checks
passed. These groups overlap and are not summed as independent coverage; a full
repository suite and general native Agent evaluation were not run. See
`.work/delivery/unit-A-verification.json` and `unit-B-verification.json` for the
actual commands and wrapper limitation, rather than treating test counts as proof.

## Explicit request connection, 2026-10-07

The existing workflow CLI now starts ordinary task state or connects an exact
state/work ID, returning a project/immutable-identity-bound invocation context.
It composes existing native-JSON preparation and execution, retaining only the
prepared plan pointer in that same task. Review, feedback, maintenance, lookup
and task resume use that context. Multiple candidates never select by timestamp;
conflicting selectors or replaced task identity block attachment. The read-only
hook consumes the explicit environment selector when inherited, and otherwise
returns candidates. No host session ID, global setting or new task ledger is assumed.

Focused RED observed the missing `start` entrypoint and missing hook current-task
delivery. GREEN verified two independent tasks, restored decisions/feedback,
target conflicts, replaced identity, prepare without command launch, execute with
semantic review unfinished, read-only lookup/task resume, completed execution
resume with zero launches, and related-task result/feedback reuse. The existing
interruption case caught a staging regression; Harness staging again remains
outside the validated work directory, preserving its prior interruption behavior.
These are actual CLI subprocess checks, not installed-host natural-language
acceptance. Whole-system actual product evidence is recorded separately below.

## Task delegation connection, 2026-10-06

The CLI now connects task scope, execution and current results. Existing
`scope_reviews` hold explicit applicability for business/architecture × FE/BE/API/Domain;
the matrix is derived from those decisions and existing requirement/outcome rows.
Empty cells remain UNDECIDED. Matching declarations cannot be silently omitted.
`registered_status` is bounded row coverage; it is distinct from task scope and
check PASS. Multiple area tags do not grant every boundary a passing result.

The shared deterministic selector drives both `verify_product.py`'s existing
unittest path and native JSON preparation. Projects register the assertion file
once, then use `--prepare --pending-state` or `--work-id`, explicit execute and
read-only lookup. Task identity, baseline, selection and source conditions are
checked before execution; result links attach to the existing task record without
requiring semantic PASS. Partial valid evidence is reused per check; unrelated
Features stay out of prepared plans. Completed resume executes nothing. Missing
connections and reasoned exclusions stay visible, and exclusions are NOT_REQUIRED
rather than test PASS. Unittest discovery/import blockers retain their raw cause.

Architecture review retains actual flow/owner, contract/dependency/failure
boundaries and open/fixed/excluded findings. A string-only PASS cannot satisfy
the structure. Fixed findings bind changed owner bytes to the work baseline;
open findings remain ISSUES even after their coverage row or Feature is removed.
Later review requires an explicit disposition. Extra scope references stale independently. Semantic
adequacy and causal judgment remain Agent work. Prompt context, follow-up work
and maintenance consume the same scope, prevention and result links. Existing UI
consumer and retirement/detection preservation behavior is reused.

Actual local CLI evidence is retained at
`.work/fullstack-task-20261006/project-final/.work/transcripts` in the previous
`wp-20261006-full-stack-workflow` worktree; those files were not copied here.
The small project-owned HTTP adapter performs Launch, health Doctor, real POST/
GET Drive, disk persistence, server restart and fresh read, native Evidence and
owned-process Cleanup. Negative input produced ISSUES; the Domain owner repair
produced PASS while semantic review was still NOT_RUN. Lookup and completed resume
executed zero checks; feedback resolved with RED/GREEN and the zero normal case,
and the next task retained prevention/results. A later extra review-reference
change kept tests PASS while only the architecture row became STALE; lookup changed
no input files. A separate observation report
produced BLOCKED. FE was explicitly excluded because this trial has no UI.

Impacted regression logs are retained under `.work/regression-retained`. The
156-case run completed with 154 passes and two setup failures: generated drift
during a concurrent canonical edit, and a non-Git fixture incorrectly inheriting
the worktree's parent Git repository. After correcting those conditions, the
affected cases were rerun individually. The final workflow module also passed
34 cases, including preservation of unresolved architecture owner findings.

Regression fixture deletion stalled in Windows `os.unlink`. The task-local
fallback retains temporary fixtures and runs test bodies and product cleanup
checks unchanged. Initial fixtures are under `.work/regression-retained`;
the isolated non-Git fixture uses a new standard temporary directory to avoid
parent Git discovery. Normal fixture garbage collection remains unverified.
This is limited local CLI/product-adapter evidence. It does not establish general
Agent task effectiveness, installed-host discovery, browser UI behavior or
protected-host acceptance. No installation, global configuration, original Labeler,
protected branch, push or publication was changed. Historical sections below
retain their original version and acceptance scope.

## User-function completion: full-stack scope, 2026-10-06

This session started from branch `wp-20261004-agent-coding-foundation`, HEAD
`e7e4be0f1e627c6ab1e51aae9727a9870b5cba40`, with no tracked/untracked dirty.
The user's current implementation priority supersedes historical host-first gates.
Existing `.work` evidence and installations are preserved; protected host acceptance
is separate and remains unverified for the latest handoff.

The existing Feature/check preparation and viewer now retain requirement/outcome
coverage on independent business/architecture and FE/BE/API/Domain axes. Cross-layer
and E2E are methods. Actual capture/run/argv/cwd/native exit/raw pointers are joined
to test rows; Agent scope reviews retain analysis/references and input validity.
MISSING, NOT_RUN, failure, reasoned exclusion and STALE remain distinct. A test-scoped
PASS does not imply complete scope or semantic architecture acceptance.

Focused checks: `python -m unittest tests.distribution.test_project_workflow
tests.distribution.test_verification_results tests.distribution.test_verification_execution`
plus the new full-stack CLI case: 83 tests passed. The scope status/exclusion/stale
case also passed independently. The actual example uses
`.work/agentic-user-flow-20261006/project`: prepare captured no execution; execute
ran one native command; `--bundle --summary` ran zero and showed PASS / NOT_RUN /
MISSING for arithmetic, ownership review and display linkage respectively. Raw and
summary are retained in that new work directory. These are local synthetic CLI
observations, not new native Agent or live-product acceptance.

## Feedback repair and subsequent consumption, 2026-10-06

`project_workflow.py feedback` merges stages into the existing task state. Audit
calculates OPEN/RESOLVED and missing cause/owner/prevention/evidence links. Source
repair is measured against the captured work baseline; guide-only changes cannot
resolve it. Prepared red/green raw assertions must preserve the failing oracle and
include a distinct passing normal counterpart. Configured-state begin/Harness start
carry the chain forward, and read-only hook context surfaces causes and guardrails.
Automatic diagnosis/conversation collection is not implemented or required.

The focused owner-repair test and actual native red/green/normal integration test
passed; workflow/hook regression: 27 tests passed. The new local synthetic CLI example
retained `b-*.json` under `.work/agentic-user-flow-20261006`: red ISSUES (one command),
green PASS (one command), feedback RESOLVED with no remaining stages, and a fresh
change work received the same resolved guardrail. Missing/stale green reopens
revalidation; adapters without compatible prepared native-JSON evidence remain OPEN
until their project-owned evidence binding exists. Existing diagnosis is reused.

## Shared verification/UI maintenance, 2026-10-06

Optional `ui_systems` on the existing project workflow connects guide intent to code
token/component paths, Feature consumers and reasoned/reconsiderable exceptions.
Audit detects missing owners/guides, broken exception references and removed consumers.
Shared changes reopen consumer map/UI/verification work; preparation binds shared
source/guide inputs even for subdirectory runners. No token values are copied and
no visual-violation detector or CSS framework was added. Existing UI capabilities
perform project-specific guide generation, intention and visual sufficiency review.

Workflow/hook plus the A/B prepare/execute regressions passed: 30 tests. The shared
subdirectory input case verifies automatic UI-file bindings. Actual local CLI
`c-*.json` observations show a missing guide as NEEDS_REPAIR, an Agent-authored guide
as CONNECTED, and a shared token change reopening the consuming `order` Feature's
UI review and verification. The fixture explicitly records its CLI-only exception;
CONNECTED proves reference structure, not rendered UI correctness.

## Evidence-based check maintenance and package delivery, 2026-10-06

Read-only `project_workflow.py maintain` now collects explicitly connected runs
using existing native-JSON/unittest adapters: failure/scope/normal links, raw
assertion pointers, deduplicated native captures, measured elapsed time, native
failure/report/cleanup information, and original/current judgments. Declared
overlap is a semantic review candidate; comparable outcome variation is evidence
to investigate, not an automatic flaky-test classification. No count-based
deletion rule or universal pruning engine exists.

The captured work baseline retains check/prevention links. Removal from an active
Feature remains BLOCKED until a current reasoned `check_decisions` review binds
old and replacement defect detection, unchanged criterion, current normal evidence
and active replacement prevention. Unresolved deletion survives the next configured
work start. The Agent makes the scoped consolidation; the CLI validates its
connected evidence. Unknown detection scope retains the check.

Focused workflow/hook/native adapter/viewer/real consolidation regression: 64
tests passed. Final changed-edge checks (retirement persistence, invalid scope
review, consolidation, semantic staleness and full-stack round trip): 5 passed.
Post-execution semantic lookup: 1 passed. Packaging/document checks: 4 passed.
The final wrong-target preservation case initially failed; shared historical
binding validation now rejects both unbound old and replacement detectors. That
case and the feedback red/green regression passed (2 tests).
Consolidation proof bundles now feed maintenance automatically; their paths need
not be entered again as history. Its dedicated integration case covers that join
alongside old-detector target refusal and actual registry consolidation.
Resource drift, distribution validation and diff formatting passed. No Full or
repeated native Agent evaluation/installation was run.

Actual `d-*.json` CLI observations in `.work/agentic-user-flow-20261006` retain
two failing detectors (RED ISSUES), two green detectors, and one green detector
after scoped registry/assertion/prevention consolidation. Before evidence review,
the deletion was BLOCKED; afterward it was PRESERVED. Old captures remain intact.
Final packaged maintenance ran zero checks, automatically collected four unique
linked `sum` runs and one `redundant` run without re-entering proof paths,
retained the active detector and showed the removed
detector with preserved detection. Times are actual local capture wall time,
not a plugin performance comparison. The example's intentionally missing FE flow
and old feedback revalidation remain visible separately from this maintenance
proof; no global success flag hides them.

The packaged viewer was also executed directly with `--bundle --workflow-state
.work/maintain.json --summary`: zero test commands, original ownership review
NOT_RUN versus current Agent review PASS, actual sum PASS and missing display
link MISSING. Joining a later review reads the same task state; it never rewrites
or reruns a prior bundle. Malformed/unbound semantic review cannot become PASS.
The final package observations are `delivery-maintain.json` and
`delivery-lookup.json` in that same retained work folder.

Remaining boundaries: visual/design and causal/coverage equivalence require Agent
judgment; prepared native-JSON currently supports the detailed feedback/deletion
raw-preservation join. Other project runners need their own compatible bindings,
not a new universal parser. New native Agent behavior and the latest protected
handoff installation/execution were deliberately not evaluated in this session.

Execution began 2026-10-05 on `wp-20261004-agent-coding-foundation` at `aa536876fb9f8922e0cade072469ddc9a51267df`, with a clean worktree. This implements the [execution prompt](agent-coding-next-session.md); the prior review-only restriction does not apply to this authorized implementation. Source/distribution `c7c064a`, viewer soundness repairs `7e9eb8d`, and UI reuse/selection-reason follow-up `95eed81` are committed. T1–T6 were performed within the independent pilot. The whole delegation system remains PARTIAL/BLOCKED for the host and evidence limits below.

Subsequent user requirements are specified in the [completion design](agent-workflow-completion-design.md): all-feature initial mapping with partition/resume, mandatory map updates, Agent judgment versus enforced environmental boundaries, and demonstrated task benefit. The U1-U7 implementation below now reports against those criteria; T1-T6 remain earlier, separately bounded evidence. In particular, R04/R12 and T1 below establish bounded first-flow/lifecycle behavior; they do not satisfy complete initial mapping or non-bypassable enforcement. Labeler remains the test environment for plugin capabilities, not the product-development objective.

## Native recurring verification adoption, 2026-10-06

A natural-language price-verification maintenance request used installed 0.1.39
in the existing authenticated, trusted, unelevated host. Session
`01a11117-7e36-7912-81b2-380c38ca94e0` selected installed project/Harness maintenance,
used the report-directory capability and isolated the unchanged check's scratch
files via its registered working directory. It retained 65 assertions from the
existing requirements/check/plan. No Skill name, CLI sequence or patch was given.
The task took 151264 ms and ten tool calls, without a follow-up intervention;
the TUI subsequently exited zero. This is adoption evidence, not a general
cost/efficiency claim (the Agent still read substantial reference content).

Two real native runs each recorded 49 observations, zero skips and one command.
Both bundle lookups and completed resumes returned PASS with zero commands.
Independent controller inspection found exactly two invocation-log entries and
all 481 baseline file hashes unchanged, including product, original checks,
requirements, historical records and `.work/task.json`. The original workflow
state remains PARTIAL; the Agent did not claim local PASS discharged protected
acceptance. Connection edits remain in the isolated fixture alongside preserved
earlier dirty work; no product or global installation changes were committed.
Evidence: `.work/plugin-transition/recurring-native-v039/` and fixture
`.work/recurring-v039/`. The latest bounded U3/U7 adoption gap is now exercised.

Remaining acceptance requires the stable protected native host: install and run
the new fixed-task handoff, then verify its actual candidate-denial, task/result
binding and restart behavior. Current account-artifact preflight still blocks
that path before native/setup execution. Repeating ordinary PASS runs or adding
another wrapper would not establish this boundary. No further required code
change was identified by the bounded independent review; whole-goal completion
remains unproven while protected installation/execution cannot be exercised.

## Fixed-task protected handoff implementation, 2026-10-06

`host_handoff.py` connects an already reviewed protected task to its existing
verifier and canonical result. The host freezes `handoff.json` and the canonical
entrypoint in its policy snapshot. Callers provide only the expected task and
optional run ID. Host-selected candidate files must equal the reviewed snapshot
before and after the operation. A changed candidate blocks current handoff;
original protected results are retained. Lookup never runs checks, including
an explicitly empty run ID (a reproduced review defect, now rejected).

The existing installer supplies canonical handoff code when included in policy;
candidate bundle helper bytes are ignored. No new publisher, result ledger,
account setup, general plugin installation or semantic auto-approval was added.
The Feature Map and host-result test selector include this entrypoint.
Twenty-three host/handoff/install/result/document/cutover tests passed. These
exercise real snapshot/task binding and retained publisher records with a
substituted executor, not actual sandbox execution. Independent review found the
empty-ID defect; its failing counterexample then passed after the branch repair.

Current native preflight still reports
`sandbox_setup_incomplete:.sandbox-secrets/sandbox_users.json` without invoking
the CLI or setup. This handoff is not installed into the protected host in that
state. It covers explicitly mapped reviewed files; arbitrary-project mapping,
chat-to-task dispatch and native end-to-end acceptance remain unverified or
incomplete. The overall goal is not complete. No package version or generated
Skill resource changes are needed for this host-only implementation.

## Repeated verification without connection edits, 2026-10-06

Version 0.1.39 adds `--prepare --report-dir` for explicit `{report_dir}/file`
output arguments and native observation paths. Projects retain their registered
commands and reviewed assertions across runs; deterministic preparation resolves
only the declared output paths. Executables, other arguments and semantic
assertions are not templated. Workflow evidence checks use the same expansion.
The directory stays inside the project, actual expanded outputs must be ignored,
and existing reports cannot be overwritten. Commands running from a registered
subdirectory can use the same project-level report directory during execution
and subsequent read-only bundle lookup.

Two negative controls reproduced unignored actual outputs slipping past a dummy
filename check and subdirectory execution rejecting valid project report paths.
Both are repaired. Repeated real Python checks exercise preparation, capture,
assertion evaluation, exact workflow command matching and zero-command lookup;
configuration and assertion bytes remain unchanged. This is deterministic CLI
coverage, not new native-Agent browser or protected-acceptance evidence. The
host-006 environment and protected acceptance limitations below still apply.
The same two integration tests also passed against the installed 0.1.39 CLI
(four real check executions total); all 246 installed files match the built
package. The guarded update reused the existing home without approval prompts.
Retained installation receipts: `.work/plugin-transition/report-dir-v039/`.
Affected execution/viewer/workflow/hook/package/document tests passed (86 tests);
resource drift, distribution validation and `git diff --check` passed. Independent
review confirmed both reproduced path defects are fixed.

## Installed recurring UI verification, 2026-10-06

The existing isolated UI project now connects its three native output arguments
and five Feature/check observation paths through `{report_dir}`. Fixture commit
`125f645` retains this connection and its executable guide. Source, requirements,
DESIGN.md and all three original check scripts were unchanged (11 hashes checked).
No original Labeler, ordinary installation, global Git settings or protected
branch was changed. Git ownership trust was supplied only to the child process.

Using installed 0.1.39, two preparations each executed zero checks; two executions
each ran exactly three shared commands for five consumers, all PASS. Each run
observed 16 browser states, two order viewport scenarios and seven local VM
checks. Browser coverage includes 1280px/390px search/empty, keyboard add,
sessionStorage save/reload/readback, clear/reload, loading/error/retry and overflow;
order adds compact layout, keyboard focus and long-name wrapping. Two retained
screenshots were also inspected against the shared guide. Preparation took
6.59/7.16 seconds and execution 18.55/18.53 seconds on this fixture; these bounded
observations are not a general performance claim.

Registry, assertion specification and guide bytes were identical across both
runs. Subsequent lookup of both bundles was current PASS with zero test commands,
and each run's 39 retained files stayed byte-identical. The owned foreground
server served bytes identical to six local assets, was stopped by its session
handle, and port 4187 had no listener afterward. Evidence is retained under
`.work/plugin-transition/report-dir-v039/` and fixture
`.work/report-dir-v039-first/` / `.work/report-dir-v039-second/`.

These are controller-executed browser observations, not native sandbox Agent or
protected acceptance. Fixture commit changes the Git identity after validation;
the precommit bundles remain historical execution evidence and are not asserted
to be current PASS after that commit. No tests were replayed merely to refresh a
success label. Native Chrome/protected-host limitations remain separately open.

## Installed execution connection and environment regression, 2026-10-06

At `e07a4fa`, the native UI task had used the installed workflow but generated an
ad hoc report instead of a reusable bundle. The common entrypoint still described
the bundled CLI only as read-only, and setup left direct native capture as the
fallback despite the installed prepare/execute capability. Version 0.1.37 fixes
those discovery paths: reuse reviewed assertions and the existing CLI for measured
preparation, shared execution and bundle production; lookup stays read-only.
No new runner, collector or environment-enforcement instruction was introduced.
Canonical Skills, generated copies and the public manifest were synchronized.
Thirteen package/self-containment/document tests and distribution validation passed;
all 246 installed files match the candidate in the existing host-006 home.

A natural-language connection request selected the installed setup/workflow
resources. After the environment intervention below, the actual Agent added the
fixture's `docs/verification-assertions.json`, connected fresh registered report
paths and documented execution, resume and lookup. It preserved product code,
requirements, UI standard and all existing test assertions. The installed CLI
prepared five Feature/check selections with zero tests, executed three shared
producers, and wrote captures, checkpoints, bound conditions and a bundle. The
VM producer passed for both Features. Both Chrome launches failed with `spawn
EPERM` under the unelevated sandbox; the overall result remained BLOCKED. No
browser success is claimed for this run.

With the owned server stopped, actual installed lookup ran zero test commands
and kept the two VM consumer results reusable while retaining browser failures.
Main independently compared the Agent's before hashes: all 24 retained execution
files and all 97 protected/prior-evidence files remained unchanged. Lookup of an
older browser-success bundle retained historical PASS but rejected current reuse
after the registry/source changes. This validates connection and failure/lookup
behavior; fresh browser PASS through this new connection remains unverified.
The project still needs coordinated new report paths in its registry and assertion
specification for another run. That manual coupling is a remaining usability cost,
not a claimed fully automatic recurring execution path.
The isolated connection is retained in fixture commit `3912164`. Its commit
changes the Git identity after the observed lookup, so that pre-commit bundle is
historical; no post-commit current PASS is claimed. The resumed native turn took
398.772 seconds, in addition to the interrupted setup attempt. No efficiency
improvement is inferred from this single setup task.

The first native attempt failed before reading any files: the setup helper
returned `orchestrator_helper_launch_canceled` / Windows error 1223. Native logs
reported missing or incompatible sandbox accounts, and a live presence check
confirmed the isolated `sandbox_users.json` was absent. Its disappearance cause
is not established. **Correction to earlier no-prompt claims:** zero approval
events in an Agent transcript does not establish absence of native setup/UAC
activity; the native log also records provisioning during the preceding UI trial.
Approval policy never does not suppress that OS setup path.

The controller interrupted the pending native attempt and resumed the same
session with the previously authorized unelevated workspace sandbox, changing
only the isolated home's Windows mode. Ordinary shell work then ran without
setup. A combined server/check/cleanup command was rejected by automatic review;
the Agent used a separate foreground server session and closed that owned session.
These interventions are retained, not described as autonomous or prompt-free
success. The protected verifier has not been weakened: missing account artifacts
currently block new protected executions. Earlier accepted frozen results remain
historical evidence; routine development continues without repeated admin setup.

Evidence: `.work/plugin-transition/ui-connection-v037/` retains the request,
update/backup, environment change, invocation and source baseline. Native session:
`01a110f2-d8ea-7632-94a6-fbf179854082`. The fixture's
`.work/verification-connection-v1/` retains actual native captures, bundle,
read-only lookup/proofs, served-byte readiness and cleanup. Features:
`agent-workflow`, `verification-results`, `plugin-package`; U3/U7 remain bounded
by the recorded browser, recurring-path and protected-host gaps.

## Native UI verification after sandbox repair, 2026-10-06

Starting from clean `cce652b`, the existing UI fixture at `247a293` and the same
authenticated host-006 home were reused without setup, login, trust, permission
or package changes. An initial deterministic capability check ran the unchanged
`node verify.cjs` through the real elevated native sandbox and existing Windows
job controller. Chrome returned 16 observations, exit zero, no timeout, forced
cleanup or remaining job members. Ten checked product/criteria/guide files stayed
byte-identical. The controller stopped its own local server. This changes the
current environment finding: the earlier native Chrome `EPERM` is historical,
not a continuing block in this repaired environment.

A separate fresh native Agent request named no Skill and prescribed no command
order: verify the existing inventory/order desktop/mobile flows and shared guide,
preserving source, criteria, previous evidence and Git state. The Agent selected
and read the installed 0.1.36 `agent-workflow`, followed the project guide, started
its own local server, and ran the three existing checks once each. It inspected
the raw results and screenshots, then added an evidence-only browser check for
Tab order, focus visibility and keyboard Retry. Actual results were:

- Existing browser flow: 16 observations at 1280 and 390 pixels, including loading,
  search/empty, keyboard add, saved order reload, clear/reload and error/retry.
- Existing order review: two viewport observations, including saved quantities,
  long-name wrapping, empty recovery and keyboard clear.
- Existing VM-state check: seven observations; kept separate from browser proof.
- Supplemental browser check: both viewport observations passed Tab/focus and
  keyboard retry/hide assertions. It retained loading/empty/focus screenshots.

The Agent inspected all 18 screenshots against the shared guide; main separately
inspected mobile inventory and desktop order output. No guide discrepancy was
observed within those views. All four check commands exited zero. The Agent
terminated its own server; an independent port check found no listener. All 14
baseline file hashes and clean fixture Git state were preserved. Native task
duration was 163.067 seconds, with 13 command events and zero approval events;
the TUI exited zero. No controller follow-up or repair was needed for this task.

Evidence: `.work/plugin-transition/ui-sandbox-v036/` contains the deterministic
launcher/lifecycle capture, natural-language request, native invocation, exit and
`native-observed.json`. Native session is
`01a110ec-5de5-7e53-bc39-e9e2294f7b35`; the actual reports, screenshots, input
hashes and cleanup record are in the UI fixture's
`.work/verification-20261006-01/`. The capability check and fresh Agent task are
separate executions; their observations are not counted as additional coverage.

Features: workflow-distribution and verification-capture; U3/U5/U7 acceptance
evidence. This resolves the prior inner-native browser execution gap for this
fixture. It remains headless local Chrome, viewport emulation and sessionStorage,
not BE persistence, screen-reader speech, cross-browser or protected UI acceptance.
The fresh task did not produce a bound viewer bundle or protected workflow result.
Whole-system request-to-protected-acceptance integration remains incomplete. No
runtime or generated resource changed in this verification unit.

## Reused environment: installed Agent repair to protected acceptance, 2026-10-06

Starting at clean `dbde8df`, the guarded updater installed 0.1.36 into the existing
authenticated host-006 home. All 246 package files match the built candidate.
The same home's top-level defaults now select `approval_policy="never"` and
`sandbox_mode="workspace-write"`, preserving its existing elevated sandbox and
trusted workspace. No new home, login, trust registration, UAC setup, ordinary
installation change or user approval was needed for this trial.

A fresh native Agent task ran from the already trusted `native-agent-v023`
workspace and changed only its `.work/price-repair-v036` fixture. The transcript
shows the installed 0.1.36 `diagnose` Skill read, eight command executions,
117.310 seconds, and no approval events. Eleven parent-project files retained
their original hashes. The Agent reproduced float truncation and invalid-input
overwrites, observed five regression methods fail (13 failing subtests and four
errors), replaced the shared conversion with Decimal parsing and integer-ratio
arithmetic, then observed those methods pass. Actual before/after readback showed
save/quote `1.15` change from 114 to 115 and rejected save/catalog inputs preserve
the exact prior bytes. It also checked missing files, unmentioned catalog records,
zero, large exact amounts and empty updates. The TUI exited zero.

The controller independently reviewed the changed converter and its three callers,
then froze the original and Agent-repaired source separately with the existing
five-case price-save oracle and current semantic-review bases. The existing
protected parent, sandbox workspace and account were reused. Both installations
passed real candidate-account write/delete/create/rename/security-access denial
probes. Native verification independently read saved bytes:

| Snapshot | Observed result |
| --- | --- |
| Original converter | REJECTED, run `935ed4b3-0d34-4ee3-9834-f91c452352aa`: 114 cents, negative saved, and over-precision saved. |
| Actual Agent repair | ACCEPTED, run `fa43c8d3-89bc-4bba-a509-799a72877bfa`: 115/0/1230 cents; negative and over-precision inputs exit 3 and preserve `{"cents":731}` byte-for-byte. |

All ten protected executions completed without timeout, forced cleanup or remaining
job members. Protected acceptance covers only those five price-save cases; the
Agent's quote/catalog regressions are separate editable-fixture evidence. The
controller still reviews and stages the host bundle; this does not prove an
autonomous full-project handoff, FE coverage, concurrency or I/O-failure behavior,
or overall U1-U7 completion. No comparative speed/context reduction is claimed.

Evidence is retained under `.work/plugin-transition/repair-native-v036/`: update
receipt/backup, task request, invocation, original-file hashes, `observed.json`
with real command outputs, task metrics, reviewed frozen bundles, installer and
native results, and `summary.json`. Native session:
`01a110e5-a950-7401-b916-17a7620f50d1`. Feature coverage: `plugin-package`,
`host-install`, `host-verification`, and `host-result`; no public Feature behavior
or generated resource changed in this validation unit.

## Elevated setup repaired and native workflow acceptance exercised, 2026-10-06

The explicit native setup command returned
`orchestrator_elevation_required` from the ordinary process. Running that official
command from an elevated PowerShell process for the explicitly selected existing
Windows user and host-006 CODEX_HOME completed with exit zero. The account artifact
now exists; its contents were not read or copied. Native setup selected `elevated`
in this isolated home's Windows setting. It did not update the ordinary plugin
installation or account configuration. The earlier missing-artifact block is
resolved; the previous blanket Agent-execution block had already been disproved.
Setup logs are under `.work/plugin-transition/elevated-authority/explicit-*`.

Three fresh installations below the existing protected trial parent exercised
the new connection using the real native sandbox and process controller:

| Frozen case | Actual observations and workflow result |
| --- | --- |
| Normal, current review | `1.15 -> 115`, zero and `12.30 -> 1230`; negative and over-precision inputs exited 3 and retained prior saved bytes. Five cases and required review accepted: ACCEPTED. |
| Same product, missing review | The same five product outcomes passed, but the unresolved review prevented completion: BLOCKED. |
| Defect, supplied current review | `1.15 -> 114`; negative and over-precision values were wrongly saved. Those observed mismatches left verification obligations unresolved: BLOCKED, with raw failing facts retained. |

A subsequent focused correction preserves the distinction between observed
product defects and missing verification: pending workflow obligations now block
an otherwise accepted run without masking an already rejected native result.
RED reproduced BLOCKED instead of REJECTED; ten host/result/installer tests passed
after repair, including defective bytes with both current and stale review.
A fresh protected `workflow-defect-verdict-v1` installation reran the same five
cases and returned REJECTED, retaining all five execution lifecycle records and
the actual `114`, negative-save and over-precision mismatches. The earlier BLOCKED
record above is preserved as historical evidence. New receipts are retained as
`defect-verdict-*` in the same trial directory.

Every native case had no timeout, no forced descendant cleanup and zero remaining
job members. Actual candidate-account probes denied write/delete/create/rename
and security-descriptor changes during installation. A post-install probe also
denied write handles for policy, evaluator and review state, and denied forged
result creation. Read-only lookup of all three runs returned identical records
without altering retained run files or rerunning cases. Raw evidence and summary
are under `.work/plugin-transition/frozen-workflow-v036/`; protected installations
are `workflow-{normal,missing-review,defect}-v036` beneath the existing trial parent.

This proves the five-case frozen price-save workflow boundary and installer on
this host. The controller prepared/reviewed those inputs; it is not autonomous
end-to-end U1-U7 completion, broader quote/catalog/UI coverage, or a general
candidate-side `accept` interface. Whole-system acceptance remains incomplete.

## Frozen workflow obligations connected to host acceptance, 2026-10-06

The optional host `execution.json.workflow` now connects the existing obligation
evaluator to host-approved project policy, original baseline, semantic reviews,
frozen source/references and explicit Feature/check-to-case associations. This
addresses a missing implementation connection separately from native setup.
The evaluator accepts supplied inventory and evidence resolution; ordinary
Git/bundle audit behavior remains unchanged. The host supplies bound snapshot
hashes and independently collected case facts, never candidate Git configuration,
submitted bundles or a candidate PASS field. The installer supplies canonical
evaluator code. All snapshot inputs and associations participate in result reuse
identity. Semantic approval of those inputs remains the host owner's responsibility;
a case label alone does not establish coverage of a business requirement.

Focused RED observed the missing evaluator connection. The selected workflow,
hook, host/result/installer, package and documentation modules passed 39 tests.
Integration coverage substitutes the process launcher and demonstrates correct
product bytes plus stale review -> BLOCKED, then current review -> ACCEPTED;
missing/rejected observations and unbound references cannot discharge obligations.
Tests forbid subprocess invocation during frozen evaluation, and independent
source review found no blocker. Generated resources and the 0.1.36 package
(19 Skills, 246 files) were built and distribution-checked. This is source and
local integration evidence, not a new real protected-host acceptance run. Existing
protected installations were not updated; the elevated setup artifact is still
missing, ordinary `accept` remains BLOCKED, and whole-system completion is unproven.

## Native lookup and corrected sandbox scope, 2026-10-06

The prior statement that the missing sandbox account artifact blocks all native
Agent tasks was too broad. Direct inspection found host-006 already configured
with `windows.sandbox = "unelevated"`. With that existing configuration, the
authenticated 0.1.34 TUI completed a fresh natural-language read-only price
verification request in 58.494 seconds, using five tool calls. No configuration,
credential, trust or OS setup change was required. The missing artifact still
blocks the dedicated elevated protected-verifier path, not this observed task.

The Agent read requirements, current source and historical raw records, compared
Git/file hashes, and reported 49 historical observations, mutation findings and
the limits of current reuse. It did not execute tests, repair files or start
services; 13 tracked source/task/evidence inputs remained byte-identical.
It did not invoke the installed viewer or explicitly load a plugin Skill during
this turn, so this demonstrates native task availability and read-only behavior,
not autonomous selection of the new summary option. A separate controller call
to the installed viewer returned current PASS with no reasons and zero test
executions. The TUI then exited zero. Request, commands, hashes, session pointer
and controller result are retained under
`.work/plugin-transition/lookup-native-v034/`. No new approval was requested.
Whole-system protected acceptance and continuous-task acceptance remain incomplete.

The same native session was then resumed with a follow-up asking whether its
historical full-Harness findings were actionable, and authorizing repair only
for a demonstrated broken connection. It selected the installed 0.1.34
`maintain-project-verification` Skill and read the current workflow configuration.
In 33.748 seconds it correctly concluded that the missing full-Harness schema,
impact rules and documentation index did not establish a defect in this fixture's
direct `commands`/`extensions.workflow` connections. It added no setup files,
changed no product behavior and reran no checks. All 13 observed inputs and the
controller's complete current bundle lookup result stayed identical. Existing
tracked maintenance changes in the fixture were preserved; it was not a clean
fixture. The resumed TUI exited zero. Evidence is in `followup-observed.json`
and the same session transcript under the lookup trial above. This establishes
actual lookup-to-maintenance continuation and a no-repair normal case. The
explicit follow-up correcting the relevance of earlier findings is a controller
intervention, not evidence of autonomous perfect triage or complete U7 acceptance.

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
The authenticated host-006 remains at 0.1.34; the missing sandbox account artifact
blocks the elevated protected-verifier path. The subsequent ordinary native task
above disproves a blanket model-execution block. Whole-system acceptance remains incomplete.

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
Fresh read-only app-server discovery subsequently returned all 19 plugin Skills
from the 0.1.34 cache. `hooks/list` reported its workflow prompt hook enabled and
trusted, with no warnings/errors (hash
`86a1d69d52a90aec364318ef56881767c7085ec5a1b0c7b62c84d9fb2b1587ef`).
Both discovery processes exited zero without timeout; raw responses are retained
in the same evidence directory. No model task or hook execution was requested.
The sandbox setup marker still exists while the account artifact is absent;
discovery therefore does not establish model execution or protected acceptance.
There is no observed need to request hook trust again for this installed version.
Ordinary installations,
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
account file is unproven; the protected-verifier launcher remains blocked before launch.

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
| U2 | Same-authority child probe actually changed a task-local policy and wrote forged success; `accept` still refused protected acceptance. Configured local close rejects unresolved obligations and submitted success. Normal edits and native runs remain available. | The historical elevated sandbox trial established candidate-account write denial, process cleanup, frozen workflow/review checks and protected results for the declared price-save cases. Current native protected execution is BLOCKED because the isolated sandbox account artifact is absent; no setup is retried. The actual 0.1.36 Agent repair is rejected before and accepted after under the same fixed oracle. The fixed-task host handoff is implemented and tested with a substituted executor, but not yet installed or exercised across the actual protected boundary. Whole-project host policy integration and originating-request binding remain incomplete; ordinary editable workflow acceptance still reports BLOCKED. |
| U3 | Actual child runs produce current native facts, captures and bundles; zero/skip/missing/stale/changed-criterion cases reject reuse. Fresh installed v3 executed the price save/read/quote check once and then queried the bundle with zero test executions and 12 retained files unchanged. The authenticated 0.1.25 trial later queried without re-execution, resumed with zero commands and 14 files unchanged, then captured/bound the registered 41-case command after feedback. | External runtime attestation and independently authenticated semantic criteria are unavailable. Only explicitly selected facts are covered. |
| U4 | Fresh collaboration context read installed diagnose/workflow resources, traced save and quote to the same faulty float converter, repaired that owner with Decimal in fixture commit `d2f1181`, and preserved the original requirement/check. RED observed `1.15 -> 114` and invalid overwrite; GREEN observed 115, valid zero/12.30 and unchanged saved bytes on rejection. Installed v3 bundle moved the actual feedback obligation from PARTIAL to READY_FOR_REVIEW. Authenticated 0.1.25 diagnosis repaired the same shared owner; a subsequent user-shaped maintenance complaint resolved default-command and binding gaps with 41 native cases and zero remaining local obligations. | Controlled repairs with an explicit follow-up needed in the native trial, not longitudinal prevention effectiveness. The environment checks registered prevention connections and changed evidence; semantic cause/coverage remains review work. |
| U5 | A fresh Agent created a small inventory UI without an existing standard, shared CSS/guide and actual desktop/mobile/browser state checks. Loading/error/retry, zero stock, search/filter and restock interaction were exercised. Main inspected screenshots and removed duplicated token values from the guide. A separate fresh-context follow-up reuses these standards for the related request screen. | UI review and its explicit intervention are distinct from numeric/browser assertions. Two authenticated native sessions establish guide creation and fresh-context reuse. Their earlier inner Chrome failures are historical: after sandbox repair, the 0.1.36 natural-language native verification task ran all three registered checks plus focused keyboard observations without intervention, inspected screenshots and stopped its server. No protected UI acceptance is claimed. Whole-product accessibility and fully autonomous host completion are not established. Explicit interventions and follow-up evidence are recorded above and below. |
| U6 | Product feedback/map connection and Harness cohort drift were repaired. Read-only/non-Harness counterexamples remain covered. A controlled duplicate check list was reduced from two to one invocation per normal/float-defect state, preserving identical raw observations and exits. Removing the unique negative-write assertion produced a demonstrated false green and was rejected. Scanner false positive was fixed without removing real docstring checks. Authenticated native maintenance also repaired the fixture runner and connected its real execution. The subsequent 0.1.30 maintenance task consolidated ten duplicate calls; independently replayed normal/six-defect comparisons preserved detection and old raw, with current installed lookup and workflow binding. | The duplicate experiment is a scoped fixture comparison, not evidence of general suite speed/cost improvement. No useful product test was deleted. |
| U7 | Real cached local Skills CLI installed/refreshed 19 Skill trees for temporary Codex/Claude targets; full tree comparison passed. Fresh v3 installed Harness CLI ran seven end-to-end cases successfully. Exact-repeat/no-op, user-byte preservation, rollback and failed-restore retention have executable regression coverage. Task records and bundle lookup support restart without replaying completed commands. The 0.1.25 updater persistently rebinds the native local marketplace and preserves unrelated config; authenticated TUI repair, lookup and native session resume now have actual tool/context evidence. | Remote update is unverified/unsupported for the local source. Actual guard termination between native registration and installation now resumes with byte-preserved recovery; interruption inside native file copy and autonomous whole-system acceptance remain unverified; 0.1.35 now repairs a controlled attributable partial-copy state through the native installer. Earlier native repair needed follow-up for runner/evidence integration; the 0.1.36 repair now reaches bounded protected acceptance through explicit controller review/staging, not autonomous whole-system acceptance. Outer-sandbox taskkill failed while the focused process-control-authorized check passed. General installations and operational environments were not changed. |

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
