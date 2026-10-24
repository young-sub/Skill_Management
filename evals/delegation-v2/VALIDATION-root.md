# Offer-list complaint validation

## `a-update-offer-list-complaint`

Feature: delegated-work evaluation assets. Fresh clone `root-offer-complaint` at Labeler `984e4f646e08b75a8dfc4b9c62913670960c1659`, with the required evaluation dependency junction.

The synthetic fault independently caps standalone updates and cached batch updates at three offer rows. The reference removes both caps; its resulting product source is byte-identical to the pinned original. No commit or dependency installation was performed.

Hidden command H: `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/zz-eval-offer-list-complaint.test.ts`

Explicit regression command R: `set "WRANGLER_LOG_PATH=.work\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/product.test.ts tests/productImportPerformance.test.ts src/client/ProductForm.test.tsx`

| Stage | Command | Exit codes by attempt | Seconds by attempt |
| --- | --- | --- | --- |
| a-start-hidden | H | 1, 1 | 12.141, 11.453 |
| a-start-regression | R | 1, 1 | 26.219, 27.875 |
| b-reference-regression | R | 0 | 23.781 |
| b-reference-hidden | H | 0 | 9.062 |
| c-probe1-hidden | H | 1, 1 | 9.032, 9.359 |
| c-probe2-hidden | H | 1, 1 | 10.406, 9.532 |
| d-partial-regression | R | 0 | 25.39 |
| d-partial-hidden | H | 1, 1 | 9.063, 8.875 |

Nonzero commands were repeated once, matching the judging retry rule. Both failures were assertion failures, rather than runtime/setup failures. The starting regression also fails: the reported standalone four-tier case is already covered; the sibling cached batch case is not.

Failing assertion evidence (the complete outputs and all attempts are in `evidence/a-update-offer-list-complaint/final/results.json`):

- a-start-hidden: `evidence/a-update-offer-list-complaint/final/a-start-hidden-retry.log:17` — AssertionError: expected [ { quantity: 10, …(2) }, …(2) ] to deeply equal [ { quantity: 10, …(2) }, …(3) ]
- a-start-hidden: `evidence/a-update-offer-list-complaint/final/a-start-hidden-retry.log:46` — AssertionError: expected [ { quantity: 10, …(2) }, …(2) ] to deeply equal [ { quantity: 10, …(2) }, …(4) ]
- a-start-regression: `evidence/a-update-offer-list-complaint/final/a-start-regression-retry.log:16` — AssertionError: expected [ { …(5) }, { …(5) }, { …(5) } ] to match object [ { quantity: 10, …(2) }, …(3) ]
- c-probe1-hidden: `evidence/a-update-offer-list-complaint/final/c-probe1-hidden-retry.log:16` — AssertionError: expected [ { quantity: 10, …(2) }, …(2) ] to deeply equal [ { quantity: 10, …(2) }, …(3) ]
- c-probe2-hidden: `evidence/a-update-offer-list-complaint/final/c-probe2-hidden-retry.log:16` — AssertionError: expected [ { quantity: 10, …(2) }, …(2) ] to deeply equal [ { quantity: 10, …(2) }, …(4) ]
- d-partial-hidden: `evidence/a-update-offer-list-complaint/final/d-partial-hidden-retry.log:16` — AssertionError: expected [ { quantity: 10, …(2) }, …(2) ] to deeply equal [ { quantity: 10, …(2) }, …(4) ]

Both probes match exactly once on the reference tree. Probe 1 restores only the standalone cap and kills the direct-edit hidden case; probe 2 restores only the cached-batch cap and kills the spreadsheet hidden case.

The first-obvious partial removes the reported standalone cap while leaving the independent cached batch cap. Its exact fault-relative diff is `evidence/a-update-offer-list-complaint/final/partial.patch`. Direct hidden cases pass, the five-tier spreadsheet fresh read returns only three tiers, and the same full explicit regression command passes. This is the required discriminating control.

Earlier shared-clamp prototype logs under `evidence/a-update-offer-list-complaint/` are superseded; only the `final/` records describe the shipped fault and probes.
