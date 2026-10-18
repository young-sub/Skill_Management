# Connected Product UI guide

## Intent

This is a small inventory tool. Keep the quantity form and saved history calm, readable, and direct. Use native links, a labeled number input, and a real submit button.

## Shared owners

- Tokens, colors, spacing, surfaces, focus treatment, and responsive rules live in shared.css.
- Interactive target sizing has one owner: the --control-size token in shared.css. A larger value is valid when the rendered controls meet it on both routes and at both viewports.
- AppNav in ui.js owns the same navigation component on both / and /history.
- Both screens load the shared stylesheet and script. Keep additions within those owners when they affect both screens.
- Add no page-specific token copies. A token change belongs in shared.css.

## Required behavior

- Navigation, fields, buttons, and status messages remain usable by keyboard and have visible focus at desktop and mobile widths.
- The history list announces loading, empty, populated, and failed reads; the form exposes pending, success, and rejected-write states through its status region.
- At 1280px and 390px, navigation and content remain visible without horizontal scrolling. Navigation padding, surface color, and keyboard focus treatment match across both routes at each width.
- Interactive targets on both routes meet the rendered --control-size token and remain at least 44px tall.
- Keep API rejection visible through the status region; do not hide a server or domain failure behind a successful-looking form.

## Execute and review

From this fixture's project root, run `python run_project.py --report .work/connected-acceptance/<new-run-id>/browser.json`. Use a new report path and artifact directory. The runner uses the existing Node, Playwright, and Chromium files; if its doctor cannot find them, retain BLOCKED and do not install a replacement for this check.

1. **Prepare:** the runner hashes the installed browser files, starts the API on a free local port, waits for `/health`, checks SQLite integrity, and records that the new database is empty.
2. **Act:** Chromium holds the empty-history read until loading is observed, releases it to observe the empty state, sends a controlled 503 to observe read-error handling, then saves 2 with Tab and Enter, rejects -1, accepts 0, reads history, and reloads after the service restart.
3. **Observe:** inspect the 16 registered checks in `browser.json`; compare `observed.browser.before_restart.shared_ui` for both routes at 1280px and 390px. The check records token values, rendered target sizes, navigation styles, focus-visible styles, and overflow. Review `entry-1280.png`, `entry-390.png`, `history-1280.png`, and `history-390.png` in the sibling artifact directory; `history-390.png` retains the pre-restart keyboard focus, and `history-390-after-restart.png` records the fresh post-restart read. The 48px token variant is valid when rendered targets meet it and shared UI/focus/responsive checks still pass; the oracle does not require exactly 44px.
4. **Clean up:** require both service records to say `stopped`, `cleanup.errors` to be empty, and the recorded database and port-file paths to be absent. Preserve the JSON, screenshots, trace, and log with their reported hashes.

These fixture observations show the current example only; they do not establish consistency in another product or host.
