# Triage Labels and States

Use this file only when the project uses tracker labels/states or needs a mapping to Work Packet states.

## State Labels

| Work Packet state | Tracker label/state | Notes |
|---|---|---|
| needs-triage | <label> | Raw item or unclear actionability |
| draft | <label> | Blocking decisions remain |
| ready-for-agent | <label> | Ready for implementation |
| blocked | <label> | Waiting on human, dependency, or approval |
| in-progress | <label> | Implementation started |
| verification | <label> | Implementation done, checks pending |
| done | <label> | Closed with evidence |

## Type Labels

| Type | Tracker label | Notes |
|---|---|---|
| bug | <label> | Use `diagnose_first` when failure/root cause is unclear |
| feature | <label> | Product capability |
| architecture | <label> | Boundary/design change or ADR-level work |
| docs | <label> | Documentation/source-of-truth update |
| diagnostics | <label> | Logs, structured events, reports, snapshots |
| test/eval | <label> | Tests, evals, verification harness |
| refactor | <label> | Behavior-preserving local cleanup |

## Priority / Risk Labels

| Meaning | Tracker label | Notes |
|---|---|---|
| high priority | <label> | <policy> |
| high risk | <label> | <policy> |
| approval required | <label> | Stops auto flow |

## Rules

- Do not create or rename tracker labels without approval unless repo policy allows it.
- If labels conflict with issue/PR body status, report the conflict in the setup report.
- Work Packet state should be derived from acceptance criteria, blocking decisions, and verification plan, not labels alone.
