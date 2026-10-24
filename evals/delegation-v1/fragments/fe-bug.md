# Yeondoo Link: `fe-bug`

A synthetic defect exposes medicine fields before pharmacist review while the purchase request gate remains intact. The complaint asks that medicine details stay hidden until review completes and keeps the cosmetic path available. The reference patch repairs the reported owner, `reviewedField`, without loosening the sibling `purchaseStatus` rule.

Prompt: 약사 확인이 필요한 의약품인데 상품 설명이 확인 전에 먼저 보여 당황스러워요. 약사 검토가 끝나기 전에는 의약품 설명을 보여 주지 말고, 검토가 끝나면 볼 수 있게 해 주세요. 검토 전에는 의약품 구매 요청도 계속 막혀 있어야 합니다. 화장품 설명은 지금처럼 확인 절차 없이 볼 수 있어야 해요.

Pinned source: `C:/Users/YS/Desktop/python/yeondoo-link`, `d17f0c2322056a4d804c911b83d6cc1b1738a083`. Validation clone: `C:/Users/YS/AppData/Local/Temp/claude/eval-authoring/delegation-20261024-yeondoo-bug`. The synthetic fault was applied to this clone, staged only to derive the reverse reference diff, then repaired. No commit was created by the authoring run. The scenario `fault` field uses the runner's required isolated-clone pre-session setup.

| Stage | Command / outcome | Runtime | Evidence |
| --- | --- | ---: | --- |
| (a) faulted start | `node --experimental-strip-types --test scripts/zz-eval-fe-bug.test.mjs` -> exit 1, 3/4 passed | 0.337 s | `a-start-hidden.log`: 'medicine explanations stay hidden until pharmacist review' fails at line 23 with `true !== false`; purchase remains gated and cosmetics still pass. |
| (b) reference hidden | Same hidden-only command -> exit 0, 4/4 passed | 0.250 s | `b-hidden-pass.log` |
| (b) reference regression | `set "NODE_OPTIONS=--require=C:/Users/YS/Desktop/python/Skill_Management/evals/delegation-v1/evidence/fe-bug/vite-temp-safe-host.cjs" && node --experimental-strip-types --test scripts/*.test.mjs` -> exit 0, 60/60 passed (56 existing + 4 hidden) | 3.238 s | `b-regression-pass.log` |
| (c) hidden-free baseline | The runner probe command -> exit 0, 56/56 existing test cases | 2.669 s | `c-no-hidden-baseline.log` |

The reference implementation is [reference/fe-bug.patch](../reference/fe-bug.patch), and applies directly to the faulted source state. Both probe matchers occur exactly once in the reference tree. Runner-style commands ran before hidden tests were installed:

| Probe mutation | Hidden-free runner command | Hidden acceptance kill |
| --- | --- | --- |
| Reintroduce the medicine `reviewedField` leak | exit 1, 55/56, 2.743 s; existing 'imported unknown classification cannot purchase and medicine explanations require actual pharmacist review' fails (`c-no-hidden-reviewed-field.log`) | exit 1, 3/4; reported explanation assertion fails with `true !== false` (`c-hidden-kill-reviewed-field.log`) |
| Bypass the sibling purchase pharmacist-review gate | exit 1, 55/56, 2.382 s; existing purchase regression 'unknown price, unknown stock, unavailable stock, unchecked package and medicine require staff review' fails (`c-no-hidden-purchase-sibling.log`) | exit 1, 3/4; the no-review purchase assertion at line 28 fails with `true !== false` (`c-hidden-kill-purchase-sibling.log`) |

The test host junction makes Vite's dev-server test unable to write `node_modules/.vite-temp`. The suite-owned preload rejects only that exact junction directory's `mkdir` with `EACCES`, which triggers Vite's own config-adjacent fallback inside the disposable clone. It does not redirect arbitrary paths. No product source checkout was modified and no commit was made during authoring.
