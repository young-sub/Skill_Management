# Luna A/B/C benchmark, 2026-10-16

The 24 official control cells, nine actual pilot attempts and 108 actual main
attempts ended. An additional 18 fresh follow-up phases completed after recovery
of a common UI scoring connection error. Original failures remain immutable;
recovered outcomes are secondary results. No trial is removed for failure,
timeout, setup error or lack of a recognized Skill read.

The observed public coding solve rates did not improve with either plugin.
The revised plugin improved the synthetic handoff result, while UI guide/reuse
acceptance regressed. Ledger resumption and connected functionality worked in
all conditions. These repeated tasks do not establish a population effect.

## Frozen inputs and actual consumption

| Condition | Plugin | Source commit | ZIP SHA256 |
| --- | --- | --- | --- |
| A | OFF | null | null |
| B | ON 0.1.61 | `65f5c38f6d0410289a99a6b43e1b4b4934831c55` | `dba723bc3bd461300530427e058686da8f7e939b18a17506071ccc409df59023` |
| C | ON 0.1.62 | `a557237872eddddd5707bb9ceb3845a67a8363de` | `3d3adbe7ff16f2578f828e8ac83ac6886d966a8a72390fcaa5ed63a1775f09f7` |

The source runtime was already committed and integrated into local plugin main.
Its Full result is 447/447. The common repository-only native runner is commit
`f4584f764605d8aa4c3b3ff12f5efcfc16e560ae`, with 43 scoped tests and actual
resource/distribution checks. Its frozen controller manifest SHA256 is
`ab73ee228cafb27424ae8179d3e20cce82d12efd4e28288faa509e1f12a188b7`.
Run support V3 has 13 pinned files and manifest SHA256
`b5fd1ecfb3eca3acc46bc48dc7290774b7421a96644c9e6b88a061f851269e8c`.
Run-specific reporting/recovery code does not change either distributed package.

Native Codex CLI 0.160.0 actually installed/consumed B/C in fresh isolated homes.
Package file hashes were verified after consumption. A had the same five bundled
system Skills and zero plugin Skills; B/C discovered 19 plugin Skills. Discovery,
hook execution/context delivery and Skill-body reads are separate observations.
All public main ON attempts had no recognized simple-shell Skill-body read. They remain
in the denominator; this heuristic does not establish absence of every contextual
use or hook effect. The original UI/connected phase1 attempts had recognized
body reads in B 3/6 and C 5/6; the original traces retain these eight reads.
In the fresh UI/connected follow-ups, recognized body reads
occurred in B 1/6 and C 4/6: five of 12 ON phases read a Skill body and seven did
not have a recognized read. The six OFF follow-ups discovered no plugin Skills.

All 143 captured native phase threads selected `gpt-6-luna` / `medium`: pilot 9,
original main 116 and fresh follow-up 18. Thread IDs are unique. No native
collaboration items or nested Codex CLI candidates were observed. All 1,475
successful, assigned broker requests also recorded Luna/medium; the broker
rejects other task model/effort settings. Azat A repetition1 failed before a
native phase, so its requested configuration is not counted as observed selection.
The gpt-6.1-sol/xhigh coordinator handled infrastructure only. Independent
reference, review and accounting Agents used Luna/medium; their usage is separate.

The dedicated `SkillBenchmark20261016` WSL/Docker environment, common CPU/memory
limits, pinned sources/images, fresh homes and Latin-rotated serial ordering were
shared by A/B/C. ABC used separate oracle-free candidate VM overlays and a private
grader VM. Candidates had no host drives, official test/reference mounts,
credentials, Docker socket, direct external egress or hosted tools. Real probes
checked these boundaries and native hook trust. Existing product checkouts,
installed user Skills, other WSL distributions and manual-disable policy were
preserved. Page caches were not flushed; external provider latency was not fixed.

## Official controls and pilot

All eight selected public tasks have positive, unchanged-source and relevant-defect
controls: SWE 9 + Feature 9 + ABC 6 = **24/24 validated cells**. Native official test
results decide correctness. No reference-patch, file-layout or implementation-path
equality condition is added.

ABC's comment-only `solution.sh` supplies no runnable reference implementation;
the official tests still exist. Existing independent Luna references, explicitly
separate from officially supplied answers, passed Azat 12/12 and Users 16/16.
Unchanged sources failed 4 tests each; MD5 and deletion defects failed one test
each. Earlier empty-patch/setup/IPv6 failures and an inadequate Carbon defect
that unexpectedly passed remain recorded. They are not counted as discriminating
controls. A valid replacement defect was actually graded. The Azat positive
wrapper's post-test cleanup error is retained alongside its native passing tests.

Users' private worker gained only an APT IPv4 configuration after an IPv6 setup
failure. RootFS-prefix, configuration/package and 88 task-file equivalence checks
and actual control revalidation distinguish this environment change from a
functional result. Image-ID differences alone do not invalidate a passing result.
The same frozen grader environment served all main A/B/C attempts.

Pilot `20261016T001048Z-255b3726` executed all nine model attempts. Original SWE
scoring errors and Feature reports without completed tests remain unknown in the
original records. Six actual grade-only recoveries reused those exact patches,
without model retries: SWE A/B/C unresolved; Feature A/B resolved, C unresolved.
ABC A/B/C passed 12/12. Four implementation-completion claims disagreed with the
recovered official outcomes. Recovery grading added 268.85 seconds.

The measured maximum pilot Agent-unit duration was 461.569510307 seconds. The
common main budget was confirmed at 1,200 seconds, without a token cap, including
setup, task tools, intermediate verification and capture. Official public grading
has its separate cap: ABC tests 1,800 / private controller 2,100 / matrix scorer 2,250
seconds; other public scorers 1,800 seconds. Combined elapsed is retained separately.

## Main results

Main `20261016T010920Z-a78334d9` ended with 108/108 indexed attempts; its supervisor
exited 0 after 27,103.650550205 seconds. Original statuses are 70 SCORED,
19 SETUP_FAILED, 1 MODEL_ERROR, 14 CONTINUOUS_COMPLETE and 4 CONTINUOUS_INCOMPLETE.
SCORED describes capture, not success. The public official outcomes are:

| Benchmark | A | B | C |
| --- | --- | --- | --- |
| SWE-bench Multimodal | 3/9 resolved | 3/9 | 3/9 |
| FeatureBench | 3/9 resolved | 3/9 | 3/9 |
| ABC-Bench | 5/6 confirmed; 1 unknown | 6/6 | 5/6 confirmed; 1 unknown |

Azat A1 had an npm/V8 setup crash before model selection. Users C3 selected
Luna/medium but produced no answer during an observed broker/parent-cgroup freeze.
Both functional outcomes and missing usage remain unknown, not functional failures
or zero cost. A scoped ownership-checked freezer repair restored the owned broker
and pending handoff container. Their original delays/errors were retained; no
service/distro restart, global configuration change or public model retry occurred.

Known paired public outcomes have zero gains and zero outcome regressions for
B/C versus A. Unknown ABC pairs are not gains. No failing official PASS_TO_PASS
checks were observed: SWE coverage 6/9 trials per condition (the other 3 had no P2P
tests), Feature 9/9, and all completed ABC trials' baseline-passing tests.
This is not whole-product regression coverage.

## Continuous fixtures and recovery

These four fixtures are synthetic evidence/feedback tasks with real SQLite,
browser, HTTP/API/Domain and storage verification; they are not live product
incidents. Functionality, handoff accuracy, duplicate effects and reuse have
different criteria and denominators.

| Criterion | A | B | C | Execution basis |
| --- | --- | --- | --- | --- |
| Accurate scoped handoff | 0/3 | 2/3 | 3/3 | Original main |
| Interrupted ledger reconciliation | 3/3 | 3/3 | 3/3 | Original main, two fresh threads |
| UI functionality, both phases | 3/3 | 3/3 | 3/3 | Secondary recovered grading/follow-up |
| UI guide plus reuse acceptance | 1/3 | 1/3 | 0/3 | Secondary recovered grading/follow-up |
| Connected functionality, both phases | 3/3 | 3/3 | 3/3 | Secondary recovered grading/follow-up |
| Related zero-scope follow-up acceptance | 1/3 | 0/3 | 1/3 | Secondary recovered grading/follow-up |

Every ledger cell had exactly two distinct durable effects and zero redundant
attempts. The first effect was checked before deliberate native interruption,
then a fresh thread reconciled the actual database. No plugin benefit was observed
for this task. A truthful incomplete handoff is expected; none of its nine Agents
claimed the whole project complete, even when the handoff itself was inaccurate.

All 18 original UI/connected cells completed phase1, then a common controller's
uppercase UTC run-ID label was rejected before trusted runtime verification and
phase2. Those original setup errors remain immutable. The first recovery's 18
read-only Git snapshot checks also failed before any grader/follow-up model call;
all failures and elapsed times are retained. Actual isolated RED/GREEN reproduced
that failure and verified an identical patch from a writable temporary copy,
inside a network-disabled container with a read-only original source mount.
Candidate Git never executed on the host.

The separate second continuation regraded every retained phase1 result and ran
each original phase2 prompt once in a fresh home/thread, with unchanged packages,
private verifier/oracle and task requirements. Only the controller's trusted label
was normalized. Original elapsed, failed-check elapsed and continuation work were
all charged to the measured 1,200-second execution budget; all 18 met it. Full
interruption/repair wall spans are retained separately. These are secondary
continuations, not uninterrupted primary runs or replacement primary successes.
All 36 runtime reports passed. Reuse rejection does not turn those into functional
errors. Read-recognition and guide-rubric limits remain explicit.

## Completion claims and resource cost

The public main review found 35 completion-claim/official-outcome discrepancies:
SWE A/B/C 6/9 each; Feature A 6/9, B 6/9, C 5/9 plus one honest incomplete report;
ABC 0 with its two no-message failures retained. The metric requires an actual
unconditional implementation-completion claim and a completed official unresolved
outcome. It does not establish intent or fabricated candidate-owned passing tests.

The 63 continuous phase messages had 45 functional-completion claims and zero
functional-completion discrepancies; handoff/partial-effect scopes account for
the 18 functionally unknown rows. Separate acceptance/reuse-completion claims had
11 explicit discrepancies and 5 ambiguous cases. Twenty-nine candidate-owned
verification claims remain claims, not independent proof. Luna reviewed the
messages; the parent verified references/outcomes against actually rehashed raw
evidence. No missing guide read alone establishes a false functional completion.

| Main measured native tokens, input / output | A | B | C |
| --- | --- | --- | --- |
| SWE | 2,386,860 / 18,532 | 2,373,543 / 18,007 | 2,624,303 / 19,923 |
| Feature | 1,495,996 / 23,275 | 2,841,692 / 127,495 | 2,432,044 / 84,804 |
| ABC | 300,076 / 4,179 + unknown | 386,658 / 4,872 | 363,960 / 3,880 + unknown |
| Continuous, including all fresh follow-ups | 3,227,148 / 37,201 | 5,074,686 / 44,482 | 12,606,160 / 85,034 |

SWE Agent-unit seconds were A 531.94 / B 580.55 / C 671.94; Feature A 430.47 / B 1,816.54 / C 866.83. No public solve-rate improvement accompanied those C time increases.
Provider waits and infrastructure failures are retained; these small repeated
samples do not establish that the plugin caused every latency difference.

Pilot/main/follow-up scopes contain 135 Agent units and 143 native phases, with
142 complete phase usage captures. Two units have unknown usage: Users C3 has
one phase with missing numeric usage, and Azat A1 failed before any phase.
Known native subtotals are 37,891,949 input,
489,326 output and 18,430,208 cached-input tokens. Reasoning 71,772 is already within
output. Provider/native counters agree for 128 fully comparable units, with zero
known differences; seven comparisons lack complete counters. They describe the
same requests and are never added twice.

Shared infrastructure is substantial and separate: the prior coordinator's
observed cumulative session has 70,400,578 input/389,709 output tokens. The current
coordinator plus two exactly linked Luna helpers has 192,009,633 input/709,050
output tokens across 1,083 unique response receipts at 2026-10-16 09:26 UTC,
including 189,278,976 cached input. These are observed session cumulatives, not
strict task-only deltas; pre-task baselines are missing. Later delivery/final
response usage remains unknown. Older cumulative snapshots are not added again.

The 13 preparation units, independent reference attempts (including failed ones),
three failed wrappers, grade-only recovery, both UI recovery attempts, diagnostics,
freezer repairs, parent/reviewer/help/wait intervals and runtime costs are retained
in separate ledgers. Their intervals can overlap and are not summed as wall time.
Actual USD, credits, complete API-equivalent estimates and a cross-scope grand
total remain null. Missing cache-write/context-tier/billing attribution and shared
account balance cannot support zero-cost claims or a complete monetary comparison.

## Evidence and delivery scope

Evidence root: `C:/Users/YS/Desktop/python/Skill_Management/.work/luna-benchmark-20261016/`.
The actual indices remain under `/opt/skill-benchmark-20261016/matrix-runs/`;
both UI attempts remain under `matrix-continuation/`. Isolated candidate checkouts,
VM disks, original Linux evidence and all older Windows mirrors are preserved.

Key retained records under `metrics/`: `official-controls-current.json`,
`pilot9-budget-decision.json`, `main108-final-primary-analysis.json`,
`main108-final-primary-conformance.json`, `continuous-ui18-secondary-analysis.json`,
`final-model-provider-audit.json`, `matrix-final-native-usage-scope.json`,
`cost-scope-reconciliation-final.json` and the claim reviews/parent verifications.
Primary conformance retains one explicit gap: Azat A1 has no captured native
phase/selection. Other pinned package/support and 18 private dependency identities
match; this gap is not hidden behind a blanket conformance PASS.

The final selective Windows mirror has 3,817 rehashed read-only files, zero missing,
changed, unmanifested or forbidden-secret paths. Manifest SHA256:
`3c3c9cd2cf514aa7bccee6d039e6aefedcf588d69f86952b6158de08124836e9`.
It excludes authentication, task sources, private oracle payloads and VM disks;
their protected Linux originals remain. Older mirrors with controller-only
compiled verifier/oracle bytes remain preserved and were never candidate mounts.
Read-only copies are not WORM storage.

Delivery is local plugin source/documentation integration and consumption of the
hash-pinned benchmark packages. No remote push, deployment, product-main merge or
installed user-Skill update is part of this delivery. Protected-host acceptance
and unrelated live-product acceptance remain separate. See [testing](../testing.md)
for the runner boundary and [feature map](../feature-map.md) for ownership.
