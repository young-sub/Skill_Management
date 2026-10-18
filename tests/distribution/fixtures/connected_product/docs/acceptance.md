# Acceptance and code ownership

## User behavior

- A submitted non-negative integer is saved and shown in history.
- Zero is valid.
- A negative quantity receives HTTP 422 with “Quantity cannot be negative” and creates no row.
- The same saved values remain visible after the service process restarts and the browser reloads the history screen.
- The entry form works with Tab and Enter; both screens fit 1280px and 390px viewports without horizontal overflow.

## Ownership

domain.py is the single owner of the quantity rule. app.py validates API input through that function before writing. The SQLite CHECK(quantity >= 0) is the last storage boundary; it must not replace the domain error or turn a normal invalid submission into an internal server error.

ui.js owns the shared app-nav component and the page interactions. Both HTML screens load that component and the tokens in shared.css. docs/ui-guide.md describes the intent and points to the code owner; token values live only in CSS.

## Project runner

From this fixture's project root run `python run_project.py --report .work/connected-acceptance/<new-run-id>/browser.json`. The project runner owns service launch, readiness and SQLite doctor checks, the real Chromium drive, evidence collection, a process restart, and cleanup. The report path and its sibling artifact directory must be new. It retains raw browser responses, loading/empty/error/success observations, database rows before and after restart, desktop/mobile screenshots for both routes and mobile history after restart, a Playwright trace, and the server log; the temporary SQLite database and port file are removed during cleanup. Both owned service processes retain their observed stopped state and exit code after cleanup; registered assertions require their termination and no cleanup errors.

The configured browser check is an end-to-end observation. It delays a real empty-history response to observe loading, then uses a controlled 503 response to exercise the read-error presentation. These route interceptions are observer conditions, not product defects. The isolated test_domain.py covers the business boundary directly; neither a successful server health response nor an HTTP success status alone passes the user flow.

The Feature also owns its runner, registered assertions, Domain test, project configuration and linked guides. Those assets belong in the same source mapping; COMPLETE registered test coverage cannot hide an unmapped ownership gap.

This example uses the existing local Windows Playwright installation. For another host, verify its public executable/module files once and update assertions.json installed_file_refs; browser_runtime() reports the discovered paths. Do not install or treat a runtime version label as evidence of unchanged bytes. Unlisted transitive dependencies and production concurrency/authentication remain outside this example's claims.

Each report uses a new sibling directory named after its report stem for screenshots, trace, log and temporary storage. Two selected checks with different JSON report names must never overwrite each other's proof. The runner refuses an existing report or artifact directory, including an interrupted run.
