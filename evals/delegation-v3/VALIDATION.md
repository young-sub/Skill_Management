# delegation-v3 validation (2026-10-27)

Clone: `C:/e/a3/l`, Labeler at `984e4f646e08b75a8dfc4b9c62913670960c1659`, `node_modules` junction to
`C:/e/deps/labeler/node_modules` (a fresh copy of the read-only original). Every state started from
`git checkout -- . && git clean -fd`, then applied the named patch. All hidden files (v2 and v3) were installed after
the regression command. Commands are the strings in `scenarios.json`
(`set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 <files>`).

| Scenario | State | Regression | v2 hidden | v3 hidden | Failing assertion (v3 check) |
| --- | --- | --- | --- | --- | --- |
| rule-all-paths | base (no patch) | — | — | exit 1 | `expected 337 to be less than or equal to 300` (create and edit) |
| rule-all-paths | v2 reference | — | — | exit 1 | `expected 337 to be less than or equal to 300` (create and edit) |
| rule-all-paths | v3 reference | exit 0 (33.1 s) | exit 0 | exit 0 | — |
| b-sequence-category-branch-copy | base | — | — | exit 1 | `expected true to be false` (preview `canApply`); positive control passed |
| b-sequence-category-branch-copy | v2 reference | — | — | exit 1 | `expected true to be false`; positive control passed |
| b-sequence-category-branch-copy | v3 reference | exit 0 (14.3 s) | exit 0 | exit 0 (2/2) | — |
| a-import-offer-sequence | base | — | — | exit 1 | `expected 'invalid' to be 'update'` |
| a-import-offer-sequence | v2 reference | — | — | exit 1 | `expected 'invalid' to be 'update'` |
| a-import-offer-sequence | v3 reference | exit 0 (20.0 s) | exit 0 | exit 0 | — |

The other nine scenarios have no file under `reference/`; their `reference_patch` points to
`evals/delegation-v2/reference/<id>.patch` unchanged, and their hidden checks are the v2 files copied byte-for-byte
under `hidden/v2/` (`build_scenarios.py --check` compares SHA-256 with the v2 sources).
`scripts/run_delegation_eval.py` `load_scenarios` accepts `scenarios.json`.

## Fixes in the three v3 references

- `rule-all-paths`: the create/update schemas also check the description length after `normalizeText`
  (NFKC), the form the worker stores.
- `b-sequence-category-branch-copy`: `restorePlan` computes the restored tree (current categories with the backup's
  parent links applied) and adds an `invalid_category_hierarchy` conflict when any category would be deeper than three
  levels or in a cycle. This uses the existing restore conflict convention: preview `canApply: false`, apply HTTP 409
  `backup_conflict`, nothing written.
- `a-import-offer-sequence`: the blank-offer test ignores the single-quantity value for legacy-layout rows, because the
  legacy parser always supplies `1` for a column that layout does not have.

## Not added

- Concurrency races on the same expected version (`a-import`, `a-update`): a stricter reading than the request.
- Legacy-layout rows with offer data replacing the whole list: the existing regression test
  `tests/product.test.ts:540` ("keeps extra bundle rows when a legacy workbook updates the visible offer columns")
  requires keeping tiers the legacy layout cannot show. A check following the request literally would fail every
  implementation that keeps the regression suite green, so this is a user decision, not a hidden check.
