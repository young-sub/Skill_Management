# Project verification responsibilities

The project owns business requirements, invariants, Feature Map, UI implementation and runner interpretation. Shared tools capture execution and link evidence. Skills select work; neither a registry row nor a PASS string executes it.

## Criteria and change impact

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
is missing, the Agent creates it from the project's existing intent and code,
then re-audits the same connection. The CLI does not generate visual design or
decide whether a discrepancy is intentional. Removed systems and Features need
reconciliation through the existing retirement path; past result bundles stay intact.

Use existing requirement documents and user decisions as the expected outcome. A Feature connects ID/name, user action/result, invariant, FE, BE/API, Domain, data side effects, executable checks and the requirement source/revision. Non-applicable layers need a reason. Commands stay in the existing project registry; the map references them instead of duplicating argv.

Trace actual callers and data: external input → parsing/validation → typed domain model → business logic → persistence/external adapter. Review state/effect/transaction ownership at touched boundaries. Existing owners come first; new state machines, registries or domain modules need an observed complexity problem.

| Change | Required relevant observation |
| --- | --- |
| FE input/serialization/save/display or cross-layer contract | UI → API → persistence → fresh read/reload. Separate layer passes cannot replace this flow. |
| Domain calculation/state | Deterministic normal, boundary and rejection cases; add caller/flow checks when the external contract changes. |
| Access/transaction/failure | Allow/deny, preserved data or rollback/readback and affected user state. Unavailable real credentials remain BLOCKED. |
| UI/shared component | Actual affected desktop/mobile, keyboard/focus and relevant loading/empty/error states. Saving requires readback; unrelated persistence can be excluded with reason. |
| Behavior-preserving architecture | Touched interface/callers and equivalent baseline GREEN; no unrelated flow requirement. |

## One plan, one raw execution

Before running, select Feature/check, expected result, criterion revision, required/excluded status and reason. Bind each actual run to command/cwd, source commit/diff, dependencies, fixture and served runtime identity. Preserve native exit/case/skip/error and raw assertion/observation location. A DB observation also needs its producing command, target, run and observed identifiers; matching values alone do not establish provenance.

For registered native JSON checks, the bundled viewer can prepare measured command/source/criteria/runtime bindings with `--prepare <assertions.json> --root <project> --plan-output <new-ignored-path>`. Supply the semantic selection, raw assertions and explicit dependency/fixture inputs; reuse this code path instead of authoring metadata collectors. Preparation runs no tests. See the [input, execution and reuse contract](result-viewer.md) for the exact specification and execution/lookup commands.

Reuse project adapters and direct CLI/CI. `run_check.py` captures a finite foreground process and an optional **new** native JSON report; never launch a detached service through it. Preserve native exit through shell wrappers. A unittest parser cannot interpret Vitest/browser reports. Do not fabricate runner-looking success output. Use project-owned native interpretation and retain any uncertainty.

One valid execution may support several claims; point to it rather than copying raw into multiple records. Do not rerun unchanged checks to fill a template. Revalidate source, requirements, commands, dependency/fixture/runtime conditions before reusing evidence. Tool records are editable consistency evidence, not signed attestation or Agent identity proof.

## Read-only results

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
