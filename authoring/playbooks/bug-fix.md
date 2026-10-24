# Bug fix

Use for incorrect behavior against an existing requirement; changing the requirement
is a feature decision. Small repairs do not require workflow state or a contract.

1. Reproduce the reported failure where feasible before editing. Retain input,
   expected/actual outcome and raw evidence; absent reproduction stays a limit,
   not invented RED. Separate product, requirement, oracle and environment causes.
2. Search callers and trace the failing input/state/data to its cause owner. Repair
   that owner once, preserving boundary errors and valid use. Use `diagnose` for
   unresolved causes and [repair and reuse](../references/repair-and-reuse.md) for
   feedback/prevention; do not duplicate its procedure.
   A guard is a fix only when that state can legitimately occur; revert edits made
   for a hypothesis the evidence refuted.
3. Confirm the original failure is prevented, nearby valid use still works, and
   affected callers/regressions pass. `probe_check.py prove` shows the regression
   fails without the fix; for a business rule, register the original fault and each
   alternate path as probes so a later reintroduction is caught. Keep the original
   failure evidence.

Completion needs cause/owner plus observed repair and relevant regression, not
RESOLVED alone. Use [project verification](../references/project-verification.md)
for impact/currentness. If reproduction or execution is unavailable, explain the
alternative evidence and unresolved claim; continue independent authorized repair
without treating a guessed cause as proven.
