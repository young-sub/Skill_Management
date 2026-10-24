# `ui-consistency` validation

Validated in a disposable local clone at `984e4f646e08b75a8dfc4b9c62913670960c1659`; the source repository was not edited. The reference implementation is [ui-consistency.patch](../reference/ui-consistency.patch). The hidden test renders the product finder with its existing React SSR convention and checks that each selectable product name has a valid HTML label association to its enabled checkbox, while an already-added product stays disabled.

- **Starting tree (a):** `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false src/client/zz-eval-ui-consistency.test.tsx` exited 1 in 21.958s. The assertion at line 40 found no label containing the selectable product name.
- **Reference (b):** the same hidden command exited 0 in 20.996s (1 test passed). Existing client regression `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false src/client/ProductCatalogFinder.test.tsx` exited 0 in 19.004s (1 file, 12 tests passed).
- **Probe `keeps-product-name-associated` (c):** removing the label's checkbox association occurred once. The hidden test exited 1 in 19.651s at line 46 because neither an explicit `for` link nor a nested checkbox associated the visible product name.
- **Probe `keeps-added-catalog-item-disabled` (c):** removing the already-added condition from `disabled` occurred once. The hidden test exited 1 in 21.276s at line 53 because the added product checkbox no longer had `disabled`.

The hidden-free configured `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --changed 984e4f646e08b75a8dfc4b9c62913670960c1659 --configLoader runner --cache=false --maxWorkers=4 --testTimeout=20000 --hookTimeout=20000` command exited 0 for each probe: 35.078s after the association probe and 34.181s after the added-item probe (each 5 files, 34 tests passed). This repository has no jsdom or happy-dom dependency, so the hidden test follows the existing server-rendered client test approach and asserts DOM semantics; it does not run a browser interaction test.

Raw command output is retained under [`evidence/ui-consistency/`](../evidence/ui-consistency/).
