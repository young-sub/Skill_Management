<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/references/project-verification.md -->
<!-- Source-SHA256: 593bb7b95e1ee5bcd10a0ebbe63df12236d7e0d63ac3fa9189645c1630c8eed4 -->

# Project verification responsibilities

The project owns business requirements, invariants, Feature Map, UI implementation and runner interpretation. Shared tools capture execution and link evidence. Skills select work; neither a registry row nor a PASS string executes it.

## Task verification

Before editing or running checks, derive the expected behavior and failure verdict from the request and existing requirements. Identify the affected Feature and actual owners/callers, then select the applicable observations below. Mixed changes use the relevant criteria together; these are not new workflow modes or mandatory records.

| Task | Select and observe |
| --- | --- |
| New feature | Completion conditions and meaningful failure cases, including affected boundary/rejection and state effects. Observe the requested user result, not just successful execution. |
| Bug fix | Reproduce where feasible, trace the actual caller/data flow to the cause owner, repair there, and confirm the original failure plus nearby valid behavior and relevant regressions. When reproduction is unavailable, retain that limit and the alternative evidence; do not invent RED. Use the existing repair reference for connected feedback. |
| Refactoring | Identify the public behavior, callers and contracts to preserve before editing; compare equivalent baseline and changed observations, including relevant errors and side effects. A changed requirement is a behavior change and needs its own criteria. |

Reuse adequate existing checks and still-valid evidence. A tiny descriptive edit can use readback/diff alone. Lookup executes no product commands; source-only diagnosis keeps runtime behavior unknown. None of these tasks inherently requires setup, a contract, RED, six scope declarations or Full.

## Criteria and change impact

For shared-owner or interface changes, use [change impact](change-impact.md) to trace callers, types, state/data ownership and module boundaries before selecting regressions. Reuse the same investigation in design and review; small local edits stay direct.

Select executable checks and semantic review from actual business-rule and architecture impact in FE, API and Domain. Business review asks whether user outcomes, permission/input contracts and policy/state invariants satisfy requirements. Architecture review follows touched UI state/component owners, API validation/dependencies/transaction boundaries and Domain rule/type/module owners. Use the existing Feature/check/review connections; passing checks do not substitute for an applicable ownership or contract review. Explain relevant exclusions separately from unavailable observations, without filling unrelated cells.

In configured projects, shared UI ownership belongs in optional
`extensions.workflow.ui_systems`, keyed by system ID. Each system declares
`guide` (intent/reference file), `tokens` and `components` (existing code path
patterns within workflow roots), and `consumers` (Feature IDs). It does not copy
token values. Optional `exceptions` have `feature`, `reason`, `reference` and
`reconsider`; a declared exception is a semantic-review input, not an automatic
test exclusion. The guide links design intent, state behavior, responsive and
accessibility expectations to those owners; these details remain project-specific.

Audit reports missing guides/owners, removed consumers and broken exception refs.
Shared source/reference changes reopen affected consumers' map/UI review and
verification; preparation binds their actual shared input files too. If a guide
is missing during authorized setup or repair, the Agent creates it from the project's existing intent and code,
then re-audits the same connection. The CLI does not generate visual design or
decide whether a discrepancy is intentional. Removed systems and Features need
reconciliation through the existing retirement path; past result bundles stay intact.
An audit-only request reports the missing guide without writing it or launching checks.

Use existing requirement documents and user decisions as the expected outcome. A Feature connects ID/name, user action/result, invariant, FE, BE/API, Domain, data side effects, executable checks and the requirement source/revision. Non-applicable layers need a reason. Commands stay in the existing project registry; the map references them instead of duplicating argv.

Trace actual callers and data: external input → parsing/validation → typed domain model → business logic → persistence/external adapter. Review state/effect/transaction ownership at touched boundaries. Existing owners come first; new state machines, registries or domain modules need an observed complexity problem.

| Change | Required relevant observation |
| --- | --- |
| FE input/serialization/save/display or cross-layer contract | Input → API → Domain → persistence → fresh read/reload, through the affected entrypoint. Observe normal and meaningful failure paths with linked input/response IDs and saved/read values; rejected writes must preserve data or show the required rollback on fresh read. Separate layer passes cannot replace this flow. |
| Domain calculation/state | Deterministic normal, boundary and rejection cases; add caller/flow checks when the external contract changes. |
| Access/transaction/failure | Allow/deny, preserved data or rollback/readback and affected user state. Unavailable real credentials remain BLOCKED. |
| UI/shared component | Actual affected desktop/mobile, keyboard/focus and relevant loading/empty/error states. Saving requires readback; unrelated persistence can be excluded with reason. |
| Behavior-preserving architecture | Touched interface/callers and equivalent baseline GREEN; no unrelated flow requirement. |

## Execute and repair the existing guide

A usable project guide connects four steps to existing owners and commands:
preparation (dependencies, isolated data, served target and readiness), action
(actual user input/navigation), observation (expected state, visual/keyboard result
and affected save/fresh read), and cleanup (only owned processes/data, retained raw).
Execute these steps; a command list is not execution proof. Use readiness/state
signals rather than arbitrary sleeps. Preserve the first failure, distinguish a
product defect from a stale command, selector, timing or environment problem, and
repair that owner. Keep commands in their existing registry/runner, linking from
the guide instead of adding another runner.

Re-execute the repaired path and confirm the same defect is detected and nearby
normal behavior is allowed. A controlled defect is labeled and isolated. For UI,
the existing repair/reuse guidance owns visual comparison and capability selection.
Then give a subsequent related task only its short request and essential project
materials. Record which guide/owners it actually discovered and reused, execution,
extra hints, failures/retries and unexecuted scope. Supplied Skill entrypoints or
token names are assisted consumption, distinct from unaided discovery; a fresh
context is useful when discovery is the claim, not compulsory for every small edit.

## One plan, one raw execution

Before running, select Feature/check, expected result, criterion revision, required/excluded status and reason. Bind each actual run to command/cwd, source commit/diff, dependencies, fixture and served runtime identity. Preserve native exit/case/skip/error and raw assertion/observation location. A DB observation also needs its producing command, target, run and observed identifiers; matching values alone do not establish provenance.

For registered native JSON checks, the bundled viewer can prepare measured command/source/criteria/runtime bindings with `--prepare <assertions.json> --root <project> --plan-output <new-ignored-path>`. Supply the semantic selection, raw assertions and explicit dependency/fixture inputs; reuse this code path instead of authoring metadata collectors. Preparation runs no tests. See the [input, execution and reuse contract](result-viewer.md) for the exact specification and execution/lookup commands.

Reuse project adapters and direct CLI/CI. `run_check.py` captures a finite foreground process and an optional **new** native JSON report; never launch a detached service through it. Preserve native exit through shell wrappers. A unittest parser cannot interpret Vitest/browser reports. Do not fabricate runner-looking success output. Use project-owned native interpretation and retain any uncertainty.

One valid execution may support several claims; point to it rather than copying raw into multiple records. Do not rerun unchanged checks to fill a template. Revalidate source, requirements, commands, dependency/fixture/runtime conditions before reusing evidence. Tool records are editable consistency evidence, not signed attestation or Agent identity proof.

## Read-only results

Explain request/expected behavior → affected Feature and owner → check/review selection reason → actual observation and raw pointer → current validity → unverified scope and next action. Reuse the existing handoff/lookup and project adapter; this explanation needs no new report schema. Distinguish executed observations from semantic review, assisted consumption from unaided discovery, and fixture/package/product/native-host evidence. Retain failed, interrupted, retried and unexecuted attempts rather than counting them as success.

Show original execution/judgment separately from current reusable/stale/unverifiable status. Read the referenced raw and its actual assertion/observation; missing/expired raw remains unavailable even if an old summary says PASS. Changed or missing relevant condition identity prevents current PASS. Never execute commands contained in an old record during lookup.

Keep planned, not-run, skip and not_required distinct from success. Required zero/all-skipped cases, wrong Feature/run/target, unavailable runtime, masked native failure or unresolved observation block overall PASS. Preserve ISSUES and BLOCKED together. Native failure is a check failure until raw evidence distinguishes a product assertion from environment/runner error. Report successful bounded observations without hiding gaps.

Feature changes update map/guide/active selectors in the same functional diff/commit; completion review checks missing links, dead commands and removed-feature residues. Historical results are retained with their original target and criteria. Detailed runs live in the project temporary-work root; durable guides contain current methods, not copied PASS records.

## Detection value and measured maintenance

`project_workflow.py maintain --root <project> --state .work/task.json
--history-bundle .work/retained/bundle.json` is read-only. It consumes explicitly
linked review/feedback bundles plus named history; it does not scan all work or
run checks. `maintenance.checks` joins each failure/scope/normal exception to
native capture/raw assertion pointers, unique runs, measured elapsed time,
nonzero native exits, incomplete executions and original/current judgments.
Shared captures and repeated bundle references count once per check. Native
unittest capture bundles reuse the existing adapter too; unavailable/stale
assessment stays unavailable while actual native cost/exit remain observable.

`declared_overlap` means matching declared failure/scope, not semantic equivalence.
`same_conditions_outcome_variation` is reported only for repeated measured bindings
and the same assertions, and needs Agent investigation before calling it flaky.
Missing mappings/evidence retain the check; costs, counts and success rates never
authorize deletion. Inspect unique regressions and nearest valid counterparts.

Begin captures existing check/prevention links in the same work baseline. Removing
a check from a still-active Feature creates `check_retirements` and a
`check_preservation` obligation. The current semantic review's `check_decisions`
is keyed by removed check, with `action` (`retain`, `consolidate`, `remove`), `reason`
and `preservation` entries for every previously declared failure/scope. Each entry
uses the feedback guardrail shape, replacement `check`, `red_bundle` proving the
replacement detects the defect, `green_bundle` proving its current normal operation,
and optionally `original_bundle` if the old detector's failed assertion is in a
different bundle. The same oracle and distinct nearby normal assertion must remain.
The replacement prevention link must be active; missing prior detection scope or
evidence blocks preservation. Existing older baselines cannot invent absent prior
links. Feature retirement uses its separate semantic removal review.

For duplicate executions of the same runner, `action: consolidate` with
`reason: duplicate_execution` can instead supply `consolidation` containing
`target_check`, `source_plan` and `target_bundle`. Both proof paths are existing
project `.work` files. The source plan must bind the clean task baseline's actual
registered command and original raw assertions; the target is an already registered
shared check with a current, task-bound native execution. Only explicit report
output paths may differ in the command. Original assertions, criteria, runtime,
source inputs and declared prevention/coverage remain; the shared execution may
bind additional inputs. Registry/map metadata may change to connect the shared
check. Missing, weaker or stale proof blocks consolidation. This path reuses actual
old detection contracts without inventing retrospective prevention labels; it does
not establish equivalence between different runners or authorize deleting checks.

For a removed requirement inside a still-active Feature, `action: remove` with
`reason: requirement_retired` takes a separate proof branch. Its `retirement`
includes safe `authorization_refs`, changed `requirement_refs` captured before
maintenance, `remaining_impact`,
`references` to the actual remaining owners, and `retired_failures` accounting for
each prior prevention failure/scope. Source removal/change must be observed and
active coverage/prevention must no longer reference the check. These references
join the current semantic review hashes; revoked/stale evidence blocks removal.
No replacement detector is demanded for an actually retired requirement. Missing
proof or an active residual link remains BLOCKED. Older baselines without criteria
hashes cannot infer a requirement change. Full Feature removal still uses its
separate reconciliation. The Agent checks actual callers and semantic impact;
path hashes and submitted removal descriptions cannot authenticate that judgment.

Whole-path removal can retain the legacy nonempty `removed_entrypoints` and
`removed_callers`. For a rule-only change, use nonempty `entrypoints` and `callers`
lists instead. Each item names `name`, `disposition` (`removed`, `changed`,
`retained`, `not_applicable`), a truthful `reason` and safe existing `references`.
Empty removal lists alone are insufficient. Entry-point references must identify
an actual changed Feature source owner previously linked by `owner_refs` on the
retired check's prevention failure/scope. A change to unrelated source cannot satisfy
the rule's retirement. Caller references and their impact join the review hashes.
Execute the new behavior and retained normal contracts, preserving raw output in
the references. The local record validates bindings; actual behavior and authority
still require review. A retired rule needs no replacement detector, while missing
authority/changed criteria/prior failure scope or active residual coverage blocks it.
Legacy records without this rule-owner connection cannot infer it during retirement;
retain the check pending a separately reviewed ownership connection. Whole-path
legacy removal retains its existing proof contract.

The Agent decides whether the failures are equivalent and makes the actual scoped
code/registry consolidation. The CLI verifies connected evidence and records
PRESERVED or BLOCKED; it neither chooses checks to delete nor runs a pruning loop.
Prepared native-JSON bundles currently support the raw preservation join; other
project adapters must provide compatible bindings before that join can resolve.

Connected tasks register the assertion path once and reuse the existing native
preparation/execution CLI's task selector; see [task scope and execution](result-viewer.md#task-scope-and-required-execution).
Maintenance automatically consumes task `results` bundle pointers alongside
review/feedback/retirement evidence. The project continues to own Launch → Doctor
→ Drive → Evidence → Cleanup. Register the actual foreground adapter and assert
saved values, fresh read/reload and resource cleanup from its native report.
The common CLI captures that report; it does not invent browser/API/Domain
observations or supply a generic lifecycle runner. Non-JSON detail remains linked
through the existing project adapter/raw evidence contract when needed.
