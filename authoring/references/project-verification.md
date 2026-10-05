# Project verification responsibilities

The project owns business requirements, invariants, Feature Map, UI implementation and runner interpretation. Shared tools capture execution and link evidence. Skills select work; neither a registry row nor a PASS string executes it.

## Criteria and change impact

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
