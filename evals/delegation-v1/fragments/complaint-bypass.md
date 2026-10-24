## complaint-bypass

The complaint is a product-description limit mismatch: new products reject descriptions above 500 characters, while editing an existing product accepts them. The planted defect changes only `updateProductSchema` in `src/shared/product.ts` from 500 to 800. The hidden API check exercises both PATCH and sibling POST, then confirms a rejected edit preserves the old description.

Clone: `C:\Users\YS\AppData\Local\Temp\claude\eval-authoring\complaint-bypass-20261024`, detached at `984e4f646e08b75a8dfc4b9c62913670960c1659`, with `node_modules` junctioned to the source. The fault's exact find occurs once. The fault was staged only to form a reference diff; no commit was created during authoring. `fault.commit_message` is provided for the runner's pre-session fault commit. The reference patch changes the limit back from 800 to 500 and applies cleanly to the faulted tree.

Commands ran with `WRANGLER_LOG_PATH=.work\eval-wrangler.log`.

| Check | Exit | Runtime | Result |
| --- | ---: | ---: | --- |
| Faulted starting tree hidden check: `npx vitest run --configLoader runner --cache=false tests/zz-eval-complaint-bypass.test.ts` | 1 | 12.32 s | The PATCH branch accepted the 501-character description: expected status 400, received 200 (`zz-eval-complaint-bypass.test.ts:30`). The sibling create assertion passed. |
| Reference hidden check, same command | 0 | 11.76 s | 1/1 passed; the edit was rejected and the stored description stayed unchanged. |
| Regression: `npx vitest run --configLoader runner --cache=false --maxWorkers=2 tests/product.test.ts src/client/ProductForm.test.tsx` | 0 | 28.18 s | 2 files, 20 tests passed. |
| Probe 1: change the create schema's `.max(500)` to `.max(800)`; hidden check | 1 | 13.41 s | Exact find is 49 UTF-8 bytes and occurs once. The sibling create assertion failed: expected 400, received 201 (`:25`). |
| Probe 1 command, with hidden file moved out: same two-file regression command | 0 | 27.91 s | 2 files, 20 tests passed. |
| Probe 2: change the update schema's `.max(500).optional()` to `.max(800).optional()`; hidden check | 1 | 12.92 s | Exact find is 60 UTF-8 bytes and occurs once. PATCH assertion failed: expected 400, received 200 (`:30`). |
| Probe 2 command, with hidden file moved out: same two-file regression command | 0 | 26.88 s | 2 files, 20 tests passed. |

The broad `--changed` command exceeded five minutes and encountered unrelated timeouts and an Undici `bad port` worker-start error on the junctioned host during the other Labeler scenario. This scenario therefore uses the exact existing product tests most likely to be touched rather than a broad changed-file run.

Raw output: `evidence/complaint-bypass/complaint-bypass-a-start-hidden.txt`, `complaint-bypass-b-reference-hidden.txt`, `complaint-bypass-b-regression.txt`, `complaint-bypass-c-probe1-hidden.txt`, `complaint-bypass-c-probe1-command-hidden-free.txt`, `complaint-bypass-c-probe2-hidden.txt`, and `complaint-bypass-c-probe2-command-hidden-free.txt`.
