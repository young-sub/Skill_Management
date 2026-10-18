<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/playbooks/bug-fix.md -->
<!-- Source-SHA256: 2e9efcf800bd023868e724bb43601066ec57e7c48415cf2e0edfca17cc4da293 -->

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
3. Confirm the original failure is prevented, nearby valid use still works, and
   affected callers/regressions pass. Keep the original failure evidence.

Completion needs cause/owner plus observed repair and relevant regression, not
RESOLVED alone. Use [project verification](../references/project-verification.md)
for impact/currentness. If reproduction or execution is unavailable, explain the
alternative evidence and unresolved claim; continue independent authorized repair
without treating a guessed cause as proven.
