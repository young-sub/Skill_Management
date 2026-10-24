# Yeondoo Link and anchor validation

All Yeondoo runs used a fresh local clone pinned to `d17f0c2322056a4d804c911b83d6cc1b1738a083`; the anchor used a separate fresh Labeler clone pinned to `984e4f646e08b75a8dfc4b9c62913670960c1659`. Each clone's `node_modules` was a junction to its matching `eval-deps` copy. No package installation or commit was used. Raw command output, exit codes, and runtimes are under the corresponding `evidence/` folders.

The Yeondoo regression command is explicit and independent of Skill_Management:

```text
node --experimental-strip-types --test scripts/session.test.mjs scripts/cart.test.mjs
```

## `cart-item-to-compare`

The starting-tree hidden command was `node --experimental-strip-types --test scripts/zz-eval-cart-item-to-compare.test.mjs`. It exited 1 in 0.279 s: all four subtests failed because the action was unsupported; the first candidate-order assertion is at hidden test line 58, with no-op assertions at lines 103, 123, and 138.

Applying `reference/cart-item-to-compare.patch` made the hidden command pass 4/4 in 0.244 s and the Yeondoo regression command pass 12/12 in 0.236 s. The client change also passed `node node_modules/typescript/bin/tsc --noEmit --pretty false` in 0.543 s.

Each mutation below matched its `find` text exactly once in the reference tree. The configured regression command passed for each mutation; the hidden command failed on the named assertion:

| Probe | Hidden result | Regression result | Failure |
| --- | --- | --- | --- |
| `duplicate-add-toggles-existing-comparison-item` | exit 1, 0.221 s | exit 0, 0.220 s | Existing item must remain unchanged, hidden line 103. |
| `sixth-item-is-accepted` | exit 1, 0.257 s | exit 0, 0.268 s | Sixth-item rejection, hidden line 123. |
| `new-item-keeps-stale-review` | exit 1, 0.229 s | exit 0, 0.255 s | Successful addition must clear only the new item's old review data, hidden line 63. |

For the partial implementation, I routed `compare-cart-item` through the existing `candidate` toggle after checking that the cart contains the product. This passes the regression command in 0.239 s but fails the hidden suite in 0.209 s because repeating an already-compared item toggles it out (hidden line 103). The partial patch is retained as `evidence/y-cart-item-to-compare/d-partial.patch`.

The hidden oracle exercises the session transition, not browser reachability. The reference adds a localized action to each cart row, and the TypeScript check passes, but there is no browser-interaction result for this scenario.

## `medicine-catalog-classification-bypass`

The planted fault changed `tylenol500.kind` from `medicine` to `cosmetic`; its exact replacement matched once. With that fault applied, the hidden command `node --experimental-strip-types --test scripts/zz-eval-medicine-classification.test.mjs` exited 1 in 0.220 s. The overview assertion failed at hidden line 25 and the purchase-request assertion failed at line 31, as intended.

The nonempty `reference/medicine-catalog-classification-bypass.patch` reverses the fault to the canonical medicine classification. Applying it made the hidden command pass 5/5 in 0.245 s and the Yeondoo regression command pass 12/12 in 0.225 s.

Each exact probe matched once on the reference tree:

| Probe | Hidden result | Regression result | Failure |
| --- | --- | --- | --- |
| `hides-approved-and-cosmetic-overviews` | exit 1, 0.212 s | exit 0, 0.244 s | Forcing overview lookup to false hides confirmed-medicine and ordinary-cosmetic overviews; hidden lines 38 and 46 fail because those overviews should be visible. |
| `medicine-purchase-bypasses-pharmacist-gate` | exit 1, 0.235 s | exit 1, 0.237 s | Purchase remains incorrectly allowed for Tylenol and another medicine; hidden lines 31 and 55. |

The plausible partial implementation special-cases Tylenol in the purchase-review rule but leaves its catalog classification and overview rule untouched. It passes regression in 0.256 s and fails hidden in 0.200 s on the overview assertion at line 25. Its patch is retained as `evidence/y-medicine-catalog-classification-bypass/d-partial.patch`.

## `rule-all-paths` anchor

The scenario object, hidden test, reference patch, probes, and regression command are unchanged from v1. The copied hidden test and reference patch have the same SHA-256 hashes as their v1 sources.

Starting-tree hidden command:

```text
set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false tests/zz-eval-rule-all-paths.test.ts
```

It exited 1 in 9.790 s with all 6 tests failing. The assertions cover create/update (hidden line 21), legacy copy (line 40), bulk import/update (lines 54 and 70), shared catalog add (line 89), and restore (line 102).

Applying the unchanged `reference/rule-all-paths.patch` made the hidden command pass 6/6 in 10.382 s. The unchanged explicit regression command exited 0 in 43.248 s:

```text
set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/product.test.ts tests/productImportPerformance.test.ts tests/backup.test.ts tests/productCatalog.test.ts src/client/ProductForm.test.tsx src/client/ProductCatalogFinder.test.tsx
```

Both unchanged probes matched exactly once. Their hidden command failed as required; their configured regression command passed:

| Probe | Hidden result | Regression result | Failure |
| --- | --- | --- | --- |
| `allows-overlong-create-description` | exit 1, 10.675 s | exit 0, 45.122 s | Create/update, legacy-copy, and shared-catalog assertions fail; hidden lines 21, 40, and 89. |
| `skips-restore-description-guard` | exit 1, 12.769 s | exit 0, 43.811 s | Restore rejects no overlong value; hidden line 102. |

The partial implementation limits only the create schema to 300 characters and leaves update, copy, import, and restore paths unchanged. It passes the regression command in 39.016 s and fails the hidden command in 10.050 s: update, legacy-copy, and restore assertions fail at lines 21, 40, and 102. The partial patch is retained as `evidence/rule-all-paths/d-partial.patch`.

The superseded cart-transfer prototype logs remain under `evidence/y-cart-transfer/` with an audit note; they are excluded from all active scenario results. The comparison-flow hidden oracle is reducer-only, as described above.
