# Feature map

## connected-product-flow

The user enters an integer quantity on the entry screen, saves it, and reads persisted items on the history screen.

The feature crosses these owned paths:

- FE: index.html, history.html, ui.js, and shared.css.
- BE/API: app.py serves the pages and /api/items.
- Domain: domain.py owns the quantity rule used by the API.
- Storage: app.py writes SQLite rows guarded by a database constraint.

The connected-product-full-stack check drives both screens and checks keyboard submission, loading/empty/error/success states, responsive layout at 1280px and 390px, shared navigation/focus/target sizing, actual API responses, stored rows, restart, and fresh browser read. Architecture scope still needs an Agent review.
