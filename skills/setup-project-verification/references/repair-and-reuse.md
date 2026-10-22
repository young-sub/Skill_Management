<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/references/repair-and-reuse.md -->
<!-- Source-SHA256: 7b9ed65fd6c80bac33480a670219a01f4f1fd32ae28b2a0f4a3774b5a8effcbe -->

# Repair and subsequent reuse

## Persist the feedback chain in existing work state

This persistence protocol applies to connected feedback work. A direct small
repair or one-off diagnosis can use its existing report; do not create workflow
state or run setup solely to register feedback. Preserve actual failure, cause,
owner and verification evidence in either path. Existing connected obligations
still apply; selecting a direct path cannot discard an open record.

With a connected invocation, `feedback --feedback <entry.json>` updates that
task directly; `review`, `maintain`, `lookup` and `resume` use the same selector.
For a subsequent related request, `start` with that context carries the existing
feedback/results into fresh work. Read-only `resume` restores the prior decision
and remaining stages without executing reproduction text or repairing code.

If a new connected feedback task is needed, use `project_workflow.py begin --root <project> --intent feedback --target <feature>
--state .work/task.json`, then `feedback --root <project> --state .work/task.json
--feedback <entry.json>`. Register `id`, `feature`, `observed`, `expected` and
`reproduction` first. Later updates with the same ID merge into that record; audit
retains missing stages and never executes reproduction text. The configured
workflow `state` and Harness start carry these records into related subsequent work;
the read-only prompt context exposes their causes/guardrails and pending work.

## Classify the feedback before choosing a repair

For a complaint registered under the wrong owner, first create and assess the
correct owner's feedback in the same task. Keep the original ID/Feature and
failure record. Submit a separate `feedback` update containing only `id`, the
original `feature`, and `supersession`:

```json
{"id":"old-incident","feature":"old-owner","supersession":{"feedback":"correct-owner-incident","reason":"Review explains why these records describe the same incident and identifies the actual owner.","references":["docs/feedback-triage.md"]}}
```

This operation also works when the original Feature was removed. Existing
project-relative references, original/target record digests and a current active
target owner bind the disposition. Self-links, missing targets, chains and
simultaneous edits to the original complaint are rejected. The target must
independently be current RESOLVED/ACCEPTED before lookup derives SUPERSEDED;
this does not mean the original owner was repaired. Original missing stages stay
in `original_remaining`, while `remaining` holds current reconciliation blockers.
Changed records/review references or an unresolved target reopen it. Re-review
the link explicitly; metadata edits do not refresh its captured bindings.
`supersession: null` revokes it; replaced/revoked links remain in
`supersession_history`. Lookup/resume neither migrate nor write these records.

A removed Feature still needs its separate removal review. A retired requirement
without a current successor stays open; this link is not generic issue dismissal.
Reason/references are review traceability, not authentication that a human approved
it or proof that two complaints have the same meaning. The Agent must inspect that
relationship; do not use an unrelated successful report to hide a failure.

`kind` defaults to `requirement_violation` for existing records. Optional
`candidate_id`, safe `evidence_refs`/`owner_refs`, and `user_review` connect the
original candidate and user response. `user_review` has `decision` (`agree`,
`intentional_difference`, `defer`, `opinion`) and an existing `reference`; defer
keeps non-repair dispositions open. Agreement is neither cause proof nor additional
change authority. Classification and evidence sufficiency remain Agent judgments.

For an intentional difference, an approval additionally needs a unique review `id`,
the exact `candidate_id`, `disposition: intentional_difference`, matching `scope`,
and nonempty `criteria_refs` covering all criteria linked to that Feature and every
consumed UI guide. The Agent owns the semantic Feature/criterion connections;
unrelated Features need not be selected. The CLI captures that subject, the complete
Feature/guide connection set and those revisions in `decision_binding`. A newly
added, removed or reconnected applicable criterion requires a new decision; partial
criterion selection cannot exclude an unreviewed requirement. Finer semantic
exclusions are not supported by this binding. General
problem agreement cannot approve a difference. Metadata edits and resubmitting the
same review and classification roundtrips preserve the original decision hashes;
other feedback kinds capture separate `confirmation_hashes`. Only a new linked approval ID binds a new
revision. Prior decisions remain in `decision_history`. These captured fields are
read-only input. Missing legacy binding stays OPEN pending explicit review, with no
lookup migration, including legacy decisions missing criterion-set connections.
File existence/hashes do not authenticate user identity, authority,
or actual semantic review; label synthetic approvals as fixtures and never record
an unseen UI candidate as user-approved.

| Kind | Evidence and disposition |
| --- | --- |
| `requirement_violation` | Source owner repair plus mechanism-appropriate evidence: fixed-oracle regression or reviewed structural/type constraint prevention. |
| `requirement_change` | `scope`, `reason`, `evidence_refs`, `owner_refs`, `reconsider`, `authorization_refs`; criteria bytes must change from registration, with fresh prepared `green_bundle` and `confirmation` for new and retained contracts. No old-oracle RED is invented. |
| `intentional_difference` | Scope/reason/evidence/owner/reconsider identify a common variant or explicit exception. The explicit subject/disposition/revision binding above plus current decision evidence yields ACCEPTED; generic agreement, absent/deferred/opinion/legacy review stays OPEN. Related criteria or decision changes reopen it in current and subsequent tasks. Feedback ACCEPTED is separate from Feature/product verification. |
| `oracle_tool_error` | Independent `evidence_refs`, scope/reason/owner/reconsider, `trace`, `root_cause`, changed `repair_paths` at the declared source/criteria owner, and fresh green confirmation. Repair the runner/oracle; preserve the actual original failure separately. |
| `environment_limit` | Preserve original failure and attempts. OPEN until `environment_recovery` links the registered capability, explicit cause classification, same observed target and fresh current PASS recheck. Configuration/attempt drift and manual disable reopen it. Environment availability is separate from product/task acceptance. |
| `unknown` | Preserve failure, conditions and next action. Always OPEN; agreement or a green file cannot confirm the cause. |

For environment recovery, retain `red_bundle`, `green_bundle`, `root_cause` and
the existing evidence/owner/scope/reconsider fields. `environment_recovery` names
`check`, `capability`, `classification` (`command_missing`, `endpoint_missing`,
`access_denied`, `os_mismatch`, `architecture_mismatch`), a nonempty `target`, its
`target_pointer` in both native raw reports, `configuration_refs` and
`attempt_captures`. Project runners own target/context/override observations and
expected results; the CLI never infers a tool command or a cause from one message.
The failed native capture and fresh current success use the same registered
command/cwd and distinct runs. Reference hashes and prior recovery attempts
remain in feedback. Missing raw/target or unresolved cause stays OPEN.
The project declares `extensions.workflow.environment_recovery[capability]`:
`check`, `recovery_command`, `target`, `target_pointer`, `failure_pointer`,
`environment_pointer` and `environment_variables`. Its native report must contain
the actual target, structured original cause and current selected nonsecret
environment values. Recovery feedback names that registered action; attempt
captures must match its argv/cwd/capability. Project config and criteria hashes
are pinned automatically. Changed inherited overrides reopen availability even
if an old green report is still present. Do not emit credentials in native reports.
Record Windows host, execution backend and container OS/architecture separately;
a Linux Docker context on Windows is valid. Inspect context and overrides,
retain original stdout/stderr, try a cause-matched command-level escalation when
authorized, and recheck the same endpoint after a real condition change. Avoid
unchanged retries, preserve manual disables and keep lookup read-only.

`confirmation` names active `check`, `expected_pointer`, and a distinct
`normal_pointer`. Both must be matched assertions in a current PASS prepared
native-JSON bundle bound to the current project Feature. Register the feedback
before changing criteria/owners so the CLI can capture the original hashes.
New related tasks inherit the same records and consume the current criteria and
active prevention; stale/missing observations reopen required work. Unrelated work
does not acquire a Full requirement. UI guide owns intent/variants/state/responsive
and accessibility references; actual values and behavior remain in shared code.

For automatic regression prevention, after diagnosis add `trace`, `root_cause`, `failed_prevention`, `repair_paths` (the
actual existing source owner), `red_bundle`, `green_bundle`, and `guardrail`:

```json
{"failure":"Negative quantity accepted","scope":"Order Domain","check":"order-flow","normal_exception":"Zero remains valid","reconsider":"Quantity contract changes","regression_pointer":"$.checks[0].rejected","normal_pointer":"$.checks[0].zero"}
```

Connect that failure/check/scope/normal_exception/reconsider to the Feature's
existing `prevention` rows. The code computes RESOLVED only after source bytes
change from the captured baseline, that link is active, a retained red native-JSON
bundle fails the original assertion, and a current prepared green bundle passes
the unchanged assertion plus a distinct nearby normal assertion. It does not
infer whether the diagnosis or normal counterpart is semantically sufficient.
Explanation/guide edits alone, missing raw, softened oracles, stale green or an
inactive guardrail leave OPEN with explicit `remaining`. Current check evidence
can require revalidation after a commit or unrelated condition change under the
existing conservative identity policy; preserved red evidence stays historical.
Other native adapters remain usable evidence, but this automatic feedback evidence
join currently requires prepared native-JSON bundles; absent bindings stay OPEN.

For alternate callers or bypasses, declare `bypass_pointers` on the feedback
guardrail and its active Feature prevention row before the RED/GREEN execution.
This optional nonempty list names distinct assertions other than the original
regression and nearby normal assertion. Each must retain its exact RED criterion
and pass in current GREEN; missing, failed or weakened bypass evidence keeps OPEN.
Existing records without the field retain their previous bounded evidence, not
an implicit claim that alternate bypasses were tested. Structural prevention uses
its existing `prevention_review.bypass` instead.

## Structural or type/constraint prevention

Use an existing Feature `prevention` row and matching feedback `guardrail` with `mechanism: structure` or `type_constraint`, `failure`, `scope`, existing source `owner_refs`, `normal_exception` and `reconsider`. No new registered check, JSON assertion adapter or fabricated RED/GREEN pair is required. The source owner must actually change. Automatic regression prevention keeps its fixed-oracle contract above.

A capture preselected for several Features can support each listed consumer's structural prevention review. Reuse its existing bytes and run identity; do not rerun solely to change the primary Feature label. Unrelated or malformed consumer labels and stale source/evidence remain insufficient.

Finish both matching declarations and any source/criteria/config edits before the final capture. Audit the feedback first to catch missing links or owners without running product commands; pending execution evidence is expected at that stage. Then capture the existing runner and submit the review. Editing project config after capture makes it stale and can force an otherwise unnecessary rerun.

Record `trace`, `root_cause`, `failed_prevention`, `repair_paths` and `prevention_review` after inspecting actual evidence:

```json
{"id":"quantity-review-1","analysis":"Both callers reach the shared validator; native output inspected.","original_failure":{"analysis":"Negative input was accepted.","references":[".work/original-observation.json"]},"bypass":{"analysis":"Direct and alternate caller now reject negative input.","references":[".work/validation.json","src/quantity.py"]},"normal":{"analysis":"Zero and positive remain valid.","references":[".work/validation.json"]},"captures":[".work/validation.json"]}
```

Use existing `run_check.py` for project-owned foreground validation, with `--feature <id>` and project-root cwd. Current captures must exit normally with zero, complete cleanup and identical before/after source identity and unchanged effective source bytes since capture (staging/committing those same bytes is allowed; the captured Git base must remain available). The Agent interprets native assertions, skips, screenshots or type/constraint results; capture exit alone never proves behavior. Original failure may be a report or directly observed artifact rather than an identical registered failing check. Bypass and normal observations reference actual execution and explain what it establishes.

The CLI pins the subject, owner/criteria/config and evidence bytes in read-only `prevention_binding`. Missing observations, inactive owner/link, changed evidence/source or running/failed/stale captures keep OPEN. New reviewed observations use a new review ID; resubmitting metadata or the same review cannot refresh old proof. Lookup executes nothing. Linked UI token/component paths count as source owners. A current structural repair with no registered checks can use these captures for this feedback task; required registered checks are never bypassed. Related tasks inherit prevention and reopen it when conditions change, but inherited proof cannot complete their new request. `resolution_basis` identifies Agent-reviewed prevention separately from automatic fixed-oracle joins. Capture shape and retained hashes reject incomplete or stale submissions; editable local files do not authenticate execution or semantic review. These are local consistency records, not protected attestation or general product acceptance. Ignored runtime/dependency conditions need project evidence.

Use expected outcome → reproduced observation → actual caller/state/data flow → cause owner → focused fix/prevention → original criterion and nearby normal case. When the task requests repair, continue through verification within authorization. An explanation/audit does not authorize mutation.

| Observed cause | Appropriate prevention |
| --- | --- |
| Product data/state error | Correct the existing state/domain/persistence owner; use fitting validation, type, transaction or DB constraint. |
| Repeated UI inconsistency | Existing shared token/component/state API; preserve intentional exceptions. Make recurrence mechanical with the project's token lint rule or browser screenshot baseline, proven against a synthetic violation. |
| Architecture drift (layer bypass, forbidden dependency, validation outside its boundary) | Repair the caller, then add the boundary rule to the project's existing linter/architecture tool. |
| Agent workflow behavior (finished without exercising the final edit, wrong tool or skipped guide) | Repair the plugin/project owner that routes or guards it: Skill routing, guide discovery or a host hook such as the packaged Stop guard. Another prose rule is insufficient. |
| Missed defect in verification | A discriminating user-flow or boundary regression, connected to its Feature. |
| Wrong target/report/exit | Runner adapter, capture or runtime identification. |
| Instruction exists but unused | Discovery or conflicting routing; do not append the same rule again. |
| Installed copy differs | Source/generated and authorized installed-root repair. |
| Environment limitation | Preserve BLOCKED, fallback and resume conditions without reducing access controls. |

Documentation alone does not repair a code defect. Do not soften expected values, assertions, skip lists or visual baselines. For a controlled fault, label it synthetic and isolate it from the original product. Keep the oracle fixed across RED/GREEN; if the oracle itself is wrong, preserve that finding and independently justify the correction.

## UI discovery and comparison

Start at the project's AGENTS/index and affected Feature's UI guide or registered
UI system. Follow its references to the actual token, component and state owners
and their other consumers before editing. If unregistered, follow existing imports
and styles directly; a small change needs no setup or new design system. A guide
links intent, relevant empty/loading/error/success states, responsive behavior and
keyboard/focus expectations to those owners. Code owns values and behavior; do not
copy token values or implementation into a second guide. Missing guidance is a
discovery/guide repair, not permission to replace the incumbent design.

Discover available capabilities by name: `impeccable` for design intent and visual
hierarchy, `fixing-accessibility` for semantics, keyboard/focus and form errors,
`vercel-react-best-practices` for affected React/Next.js rendering, fetching and
performance. Read only relevant rules. These complement the project's criteria;
none replaces the existing design or requires framework conversion, installation,
or a whole-project audit. If absent, use existing project tools and report the gap.

Before visual execution, name the intended difference and what must remain stable.
Compare the same route, viewport, theme, data and interaction state, pinning the
baseline source and served candidate. Capture relevant desktop/narrow views and
focus/state transitions using the existing browser path. Inspect the images and
interaction observations: screenshot existence or pixel difference alone is not
a verdict. Classify each material discrepancy as intended scope, requirement
violation, observation/environment error or unresolved. An intended difference
needs the request/decision and owner reference; never regenerate a golden merely
to hide a failure. Unrelated layout, contrast, focus or state regressions still fail.
For connected feedback use the existing explicit decision binding above; a direct
small task can record this comparison in its report without creating workflow state.

Repair repeated inconsistency at its shared owner and check the affected consumers.
Saving or changed serialization requires the actual saved value and fresh read;
pure styling can exclude persistence only with an impact reason. Do not convert
animation timing or observation failure into a product patch. After guide/observer
repair, run the same defect and a nearby valid or intentional variant with unchanged
behavioral criteria. Retain the original failed/missed observation and explain any
oracle correction independently. Do not silently weaken assertions or skip states.

Make updated criteria/shared implementation discoverable through existing project guidance. Verify reuse with a subsequent fresh-context request when claiming that benefit; do not supply the prior patch or long implementation instructions. Record the actual installed resource path, context/host, user request, tool execution, diff and run/raw references. A source edit or installation manifest alone proves neither discovery nor improved Agent behavior.

For `oracle_tool_error`, a tool created after task start may have no captured
baseline hash. Missing keys are not inferred absence. An explicit `red_bundle`
can supply a separate repair preimage only through its selected failing native
check: the same expected pointer must fail; root/Feature/check, raw/capture/assessment
bindings and unchanged source must validate. The root-local command must have
registered the exact owner dependency, whose hash matches the capture's per-file
untracked hash and measured dependency. Both current and red-plan source patterns
must own that path. Missing/ambiguous/tampered evidence leaves the repair OPEN.
A present task-start hash always takes precedence; baseline and `source_before`
remain unchanged. Fresh current green confirmation is still required. This does
not certify semantic or protected-host approval and does not support new-owner
preimages from commands outside the project root.
