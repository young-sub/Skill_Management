# Testing Policy

- Change behavior through RED, GREEN, and REFACTOR cycles, one observable vertical slice at a time.
- Accept RED only when the intended assertion fails; collection, syntax, fixture, permission, and environment failures are blockers.
- Run Targeted checks first, then Feature and Fast suites. Run the Full suite once near Goal completion unless evidence requires another run.
- Live and Eval checks are opt-in and must stay inside the approved Test Envelope.
- Record exact commands, results, skipped checks, unverified assumptions, and remaining risks.
- Preserve existing dirty changes and use temporary directories for install or migration smoke tests.
