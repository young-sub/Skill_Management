# Repair and subsequent reuse

## Persist the feedback chain in existing work state

With a connected invocation, `feedback --feedback <entry.json>` updates that
task directly; `review`, `maintain`, `lookup` and `resume` use the same selector.
For a subsequent related request, `start` with that context carries the existing
feedback/results into fresh work. Read-only `resume` restores the prior decision
and remaining stages without executing reproduction text or repairing code.

Use `project_workflow.py begin --root <project> --intent feedback --target <feature>
--state .work/task.json`, then `feedback --root <project> --state .work/task.json
--feedback <entry.json>`. Register `id`, `feature`, `observed`, `expected` and
`reproduction` first. Later updates with the same ID merge into that record; audit
retains missing stages and never executes reproduction text. The configured
workflow `state` and Harness start carry these records into related subsequent work;
the read-only prompt context exposes their causes/guardrails and pending work.

## Classify the feedback before choosing a repair

`kind` defaults to `requirement_violation` for existing records. Optional
`candidate_id`, safe `evidence_refs`/`owner_refs`, and `user_review` connect the
original candidate and user response. `user_review` has `decision` (`agree`,
`intentional_difference`, `defer`, `opinion`) and an existing `reference`; defer
keeps non-repair dispositions open. Agreement is neither cause proof nor additional
change authority. Classification and evidence sufficiency remain Agent judgments.

| Kind | Evidence and disposition |
| --- | --- |
| `requirement_violation` | Existing fixed-oracle RED/GREEN/normal and active prevention chain below; source owner repair required. |
| `requirement_change` | `scope`, `reason`, `evidence_refs`, `owner_refs`, `reconsider`, `authorization_refs`; criteria bytes must change from registration, with fresh prepared `green_bundle` and `confirmation` for new and retained contracts. No old-oracle RED is invented. |
| `intentional_difference` | Scope/reason/evidence/owner/reconsider identify a common variant or explicit exception. A linked `user_review` of `agree` or `intentional_difference` plus current evidence yields ACCEPTED without a product-repair obligation; absent/deferred/opinion review stays OPEN. Changed references reopen it. |
| `oracle_tool_error` | Independent `evidence_refs`, scope/reason/owner/reconsider, `trace`, `root_cause`, changed `repair_paths` at the declared source/criteria owner, and fresh green confirmation. Repair the runner/oracle; preserve the actual original failure separately. |
| `environment_limit`, `unknown` | Preserve failure, conditions and next action. Always OPEN; agreement or a green file cannot manufacture a confirmed cause or resolution. |

`confirmation` names active `check`, `expected_pointer`, and a distinct
`normal_pointer`. Both must be matched assertions in a current PASS prepared
native-JSON bundle bound to the current project Feature. Register the feedback
before changing criteria/owners so the CLI can capture the original hashes.
New related tasks inherit the same records and consume the current criteria and
active prevention; stale/missing observations reopen required work. Unrelated work
does not acquire a Full requirement. UI guide owns intent/variants/state/responsive
and accessibility references; actual values and behavior remain in shared code.

For a requirement violation, after diagnosis add `trace`, `root_cause`, `failed_prevention`, `repair_paths` (the
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

Use expected outcome → reproduced observation → actual caller/state/data flow → cause owner → focused fix/prevention → original criterion and nearby normal case. When the task requests repair, continue through verification within authorization. An explanation/audit does not authorize mutation.

| Observed cause | Appropriate prevention |
| --- | --- |
| Product data/state error | Correct the existing state/domain/persistence owner; use fitting validation, type, transaction or DB constraint. |
| Repeated UI inconsistency | Existing shared token/component/state API; preserve intentional exceptions. |
| Missed defect in verification | A discriminating user-flow or boundary regression, connected to its Feature. |
| Wrong target/report/exit | Runner adapter, capture or runtime identification. |
| Instruction exists but unused | Discovery or conflicting routing; do not append the same rule again. |
| Installed copy differs | Source/generated and authorized installed-root repair. |
| Environment limitation | Preserve BLOCKED, fallback and resume conditions without reducing access controls. |

Documentation alone does not repair a code defect. Do not soften expected values, assertions, skip lists or visual baselines. For a controlled fault, label it synthetic and isolate it from the original product. Keep the oracle fixed across RED/GREEN; if the oracle itself is wrong, preserve that finding and independently justify the correction.

For UI, inspect existing design intent, references, token and component owners, responsive behavior and relevant states. Guide owns intent and source references; code owns token values and implementation. Repair repetition at the shared owner and verify real interaction, not screenshot existence. Do not convert animation timing or observation failure into a product patch.

Make updated criteria/shared implementation discoverable through existing project guidance. Verify reuse with a subsequent fresh-context request when claiming that benefit; do not supply the prior patch or long implementation instructions. Record the actual installed resource path, context/host, user request, tool execution, diff and run/raw references. A source edit or installation manifest alone proves neither discovery nor improved Agent behavior.
