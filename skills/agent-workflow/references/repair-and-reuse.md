<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/references/repair-and-reuse.md -->
<!-- Source-SHA256: a7f7786540380e12b3c2c0b3334674482773f0897a02e781d073fc0ca3e96190 -->

# Repair and subsequent reuse

## Persist the feedback chain in existing work state

Use `project_workflow.py begin --root <project> --intent feedback --target <feature>
--state .work/task.json`, then `feedback --root <project> --state .work/task.json
--feedback <entry.json>`. Register `id`, `feature`, `observed`, `expected` and
`reproduction` first. Later updates with the same ID merge into that record; audit
retains missing stages and never executes reproduction text. The configured
workflow `state` and Harness start carry these records into related subsequent work;
the read-only prompt context exposes their causes/guardrails and pending work.

After diagnosis add `trace`, `root_cause`, `failed_prevention`, `repair_paths` (the
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
