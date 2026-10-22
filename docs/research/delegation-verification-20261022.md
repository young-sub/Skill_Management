# Five sequential verification improvements

Base: clean `3ee488f` on `wp-20261020-luna-0178-results`.
Work: `.work/goals/active/20261022-delegation-verification`.
Raw: `.work/delegation-verification-20261022/`; failed attempts are retained.

## Outcome visibility

`lookup --summary` exposes expected outcomes, requirement/axes, current status,
selection reason and check evidence references per Feature. Missing declarations
remain UNDECLARED. Business value is not inferred from code-test results.
I1 focused RED/GREEN and workflow/hook/docs regression are retained in the raw root.

## Labeler storage acceptance

The user selected Labeler. The clean product source is `000ffd1`; its archived
copy, dependencies reused by junction, local database and build are isolated under
the raw root's `labeler/`. No original source, credentials, shared database or
installed plugin was changed. Only the copy's Vite cache location was adapted.

`scripts/verify_labeler_storage.mjs` is a project-specific adapter, not a generic
runner. It uses real Chromium, Labeler Worker and local D1; no API is mocked.
Set `LABELER_ROOT`, `LABELER_DATABASE` (inside that root's `.work`), `UI_BASE_URL`
(use `http://localhost:4387/` for local secure session cookies), `PLAYWRIGHT_MODULE`
to the existing Playwright module, and a new `UI_EVIDENCE_DIR`. Run
`node scripts/verify_labeler_storage.mjs`. Each run creates uniquely named synthetic
categories/products, retains the database and raw report, and closes its browser.
The caller owns server startup/shutdown; do not aim this at shared data.

Preparation uses the product's `LABELER_LOCAL_STATE_ROOT` and
`node scripts/local-state.mjs d1 migrations apply DB`, then the existing Vite build
with `--configLoader runner` and a copy-local `cacheDir`. Serve the built Worker
with the existing Wrangler `dev --local --ip 127.0.0.1 --port 4387 --persist-to`
pointing at that exact isolated state. Keep Wrangler logs inside the copy.

The generated `no_bundle: true` dev configuration reproduced a local proxy crash
after an early body-bearing denial. A separate sibling `verification.wrangler.json`
with `no_bundle: false` enables Wrangler's own request-draining middleware; product
code and denial expectations remain unchanged. This is a local verification setup,
not a production change. The upstream [body-draining issue](https://github.com/cloudflare/workers-sdk/issues/15203)
describes the same failure class. Earlier failures and server logs remain retained.

The adapter checks UI payload/API values, independent SQLite ID/owner/price,
zero price, negative-price rejection with unchanged data, account mismatch,
anonymous writes, cross-account reads, fresh API read and browser reload. It
hashes relevant source/build files before/after; this is not remote attestation.
`LABELER_PAYLOAD_FAULT=1` deliberately corrupts only the outgoing browser price
and must fail the unchanged positive-save assertion. Use a new evidence directory.

`labeler-green-12` passed 24 observations. Desktop and mobile screenshots were
opened: saved synthetic products and prices were visible on desktop; the mobile
table uses horizontal overflow. This does not establish whole-product accessibility.
`labeler-payload-fault` rejected the FE fault. Earlier selector, preparation and
proxy failures are not successes or evidence of product defects.

## I3: Feedback prevention

Declared `bypass_pointers` must identify distinct alternate failure observations
in the original RED and current GREEN evidence, with unchanged assertions. The
active Feature prevention mapping must retain them. Missing, aliased, duplicated,
failing or weakened bypass proof cannot resolve feedback. Existing undeclared
and structural-prevention contracts retain their behavior. `i3-final.json` covers
real failure/fix/follow-up runs and the alternate -2 path; earlier failures remain.
Independent review found that a feedback record could omit pointers declared in
the Feature prevention mapping. `bypass-omission-red.json` reproduces that gap;
the final fix compares the optional field in both directions, so omission cannot
resolve feedback. The interrupted pre-review final suites are retained separately
from the final runs on this correction.

## I4: Guide reuse

Task summaries and selected hook Features expose existing testing/UI guides,
shared token/component owners, scoped exceptions and prevention references, with
omitted counts. Missing guides remain NEEDS_REPAIR. `i4-final.json` and
`i4-hook-final.json` verify discovery and hook consumption.

A fresh-context agent received only the frozen package path, isolated connected
product path and the 48px request. It discovered the existing shared token,
changed that owner, strengthened the browser minimum from 44px to 48px, and
updated the existing UI guide and Feature map. Its browser report under
`reuse-product/.work/ui-48px-20261022-01/browser.json` passed all 16 observations,
including both routes at 1280/390px, saving 2 and 0, rejecting -1, and reading
`[2, 0]` after restart. Screenshots were inspected and both owned services stopped.
This is assisted package consumption, not unaided native-host discovery or a
claim about Labeler's UI consistency. No dependency installation was needed.

## I5: Detection-preserving maintenance

Read-only maintenance now reports prior/active check counts, removals with or
without current preservation proof, and capture-deduplicated execution cost.
Historical elapsed time is not a speedup claim; model token/cost is not measured.
The executable consolidation scenario removes an actual registered redundant
check and command (2 active checks become 1). Removal is blocked until original
and replacement defect detection plus normal-case evidence is connected; wrong
original target evidence reopens the block. `i5-final.json` passes this scenario.
This reduces the demonstrated fixture's checks, not arbitrary product suites.

The five changes are packaged as 0.1.83 in the repository. Installed/global
plugins and production Labeler are outside this implementation. Final suite and
package verification captures are retained beside the per-item evidence.
