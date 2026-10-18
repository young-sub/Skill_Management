# Change impact and design decisions

Use this procedure for the part of a change whose contracts or ownership can move.
For a local edit, inspect its owner and direct consumers and verify the affected
behavior directly. No design document, workflow state, contract, full setup or
whole-project check is required merely to use this procedure.

## Trace before choosing

Start with the requested observable result and failure conditions. Read applicable
project guidance, current design, Feature Map and existing checks; use symbol and
call-site searches to follow the affected path, not just the edited file.

- **Callers and contracts:** entrypoints, internal/direct callers, exports and
  adapters; input/output shapes, aliases, status/errors and side effects that must
  remain compatible. Search dynamic/configured consumers too when present.
- **Types and validation:** representation across boundaries, parsing/coercion,
  domain invariants and serialization. Static types do not validate external input;
  preserve runtime validation and the caller-visible error contract.
- **State and data ownership:** who reads/writes each value, lifetime and source of
  truth, transaction/rollback, failure after partial progress, concurrent writers,
  persisted old data and fresh reads. Consider only risks reached by this change.
- **Module boundaries:** dependency direction, existing rule/transaction owners,
  shared helpers, duplicated policy and public import paths. Put the rule at its
  owner; keep boundary-specific translation at the boundary.
- **Reach:** affected tests/fixtures/config/exports/generated resources and guides.
  Follow shared owners to their other consumers. Mark an unavailable caller or
  environment unknown rather than treating the search as proof of no impact.

Reuse this investigation across design, implementation and review. The useful
output is a bounded decision plus affected behavior and checks, not a new graph
database or mandatory checklist file. Select `architect` when ownership or
interface tradeoffs need resolution; absent that optional Skill, use this same
procedure and existing project conventions.

## Choose and demonstrate

Prefer the smallest complete change in the existing structure and tools. Add an
abstraction or dependency only for a concrete requirement or observed complexity.
Keep necessary validation, error handling and data preservation when moving code.
Do not silently turn a refactor into changed behavior. For an incompatible change,
identify affected callers and required migration/compatibility before implementation;
destructive migration or external actions need their own authority.

Before execution, select expected outcomes and failure verdicts from requirements:
new behavior needs normal and meaningful failure cases; refactoring needs equivalent
baseline/candidate observations; a bug needs feasible reproduction and nearby valid
use. Map each selected regression to the affected contract or owner. Use existing
runners and assertions; add a check only for a missing failure detector. Follow
changed connections through input, API, Domain, storage and fresh read, including
rejected writes or rollback. Unaffected layers need no ceremonial execution.

After editing, inspect the actual diff and remaining call sites for missed consumers,
weakened errors or duplicated state/rules. Run the impacted checks and inspect their
raw observations; expand only for changed behavior, failures or unresolved risk.
Record semantic ownership review separately from executed behavior. Preserve failed,
retried and unexecuted attempts and existing user data/evidence.

When evaluating reuse, give a fresh context a short related request and essential
project materials. Record what it discovered and applied, what hints it received,
and actual implementation/regressions. Supplied Skill paths are assisted consumption;
discovery inside a supplied catalog is distinct from native-host unaided discovery.
