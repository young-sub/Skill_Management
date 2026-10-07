# Connected Product UI guide

## Intent

This is a small inventory tool. Keep the quantity form and saved history calm, readable, and direct. Use native links, a labeled number input, and a real submit button.

## Shared owners

- Tokens, colors, spacing, surfaces, focus treatment, and responsive rules live in shared.css.
- Interactive target sizing has one owner: the --control-size token in shared.css.
- AppNav in ui.js owns the same navigation component on both / and /history.
- Both screens load the shared stylesheet and script. Keep additions within those owners when they affect both screens.
- Add no page-specific token copies. A token change belongs in shared.css.

## Required behavior

- Navigation, fields, buttons, and status messages remain usable by keyboard and have visible focus.
- The history list is announced after its API read and retains a clear empty state.
- At the configured narrow viewport, navigation, content, and saved rows remain visible without horizontal scrolling. Navigation padding, surface color, and keyboard focus treatment match across both routes.
- Interactive targets on both routes meet --control-size.
- Keep API rejection visible through the status region; do not hide a server or domain failure behind a successful-looking form.

## Evidence

The configured browser run records the Tab order, keyboard submission, both routes, the narrow layout measurement, screenshots, and a Playwright trace. Those observations show current screens; this guide alone does not establish visual consistency.
