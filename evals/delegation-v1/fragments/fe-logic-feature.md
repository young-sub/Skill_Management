# Yeondoo Link: `fe-logic-feature`

The buyer can move every selected quantity from purchase review into the cart in one action. Quantities merge with existing cart items; any item that is unclassified, known out of stock, needs pharmacist approval, or would exceed 99 causes the whole transfer to be rejected. The UI adds a localized cart action in the purchase screen and reports successful adds through the existing live status region.

Prompt: 구매 검토 화면에서 선택한 상품들을 장바구니에 한 번에 담는 `add-selected-to-cart` 동작을 추가해 주세요. 기존 장바구니 수량에 선택한 수량을 더하고, 상품별 수량은 99개를 넘지 않게 해 주세요. 재고가 없거나 분류가 정해지지 않은 상품은 담을 수 없고, 약사 확인이 필요한 의약품은 확인이 끝난 뒤에만 담을 수 있어야 합니다. 하나라도 담을 수 없는 상품이 있으면 일부만 추가하지 말고 장바구니를 그대로 두고 선택도 유지해 주세요.

Pinned source: `C:/Users/YS/Desktop/python/yeondoo-link`, `d17f0c2322056a4d804c911b83d6cc1b1738a083`. Validation clone: `C:/Users/YS/AppData/Local/Temp/claude/eval-authoring/delegation-20261024-yeondoo`. The hidden test imports the existing `transition` module and exercises its public action; it does not require an exported implementation helper.

| Stage | Command / outcome | Runtime | Evidence |
| --- | --- | ---: | --- |
| (a) pinned start | `node --experimental-strip-types --test scripts/zz-eval-fe-logic-feature.test.mjs` -> exit 1, 0/6 passed | 0.279 s | `a-start-hidden.log`: first acceptance assertion expected cart `{illiyoon_cream: 5}`, actual `{}` (line 36); the baseline has no bulk-cart action. |
| (b) reference hidden | Same hidden-only command -> exit 0, 6/6 passed | 0.246 s | `b-hidden-pass.log` |
| (b) reference regression | `set "NODE_OPTIONS=--require=C:/Users/YS/Desktop/python/Skill_Management/evals/delegation-v1/evidence/fe-logic-feature/vite-temp-safe-host.cjs" && node --experimental-strip-types --test scripts/*.test.mjs` -> exit 0, 62/62 passed (56 existing + 6 hidden) | 2.427 s | `b-regression-pass.log` |
| (b) production build | `npm run build` -> exit 0; TypeScript and Vite build pass | 8.533 s | `b-build.log` |
| (c) hidden-free baseline | The runner probe command -> exit 0, 56/56 existing test cases | 2.765 s | `c-no-hidden-baseline.log` |

The reference implementation is [reference/fe-logic-feature.patch](../reference/fe-logic-feature.patch). Every probe matcher occurs once in the reference tree. Runner-style probe commands were run with hidden files absent; all passed on the reference tree. Applying each mutation separately and installing the hidden file only for the mutation-kill check produced:

| Probe mutation | Hidden-free runner command | Hidden acceptance kill |
| --- | --- | --- |
| Remove the explicit unclassified-product rejection | exit 0, 56/56, 2.485 s (`c-no-hidden-classification.log`) | exit 1, 5/6; 'an unclassified selection prevents every item' fails (`c-hidden-kill-classification.log`) |
| Remove the catalog out-of-stock rejection | exit 0, 56/56, 2.613 s (`c-no-hidden-catalog-stock.log`) | exit 1, 5/6; 'a catalog item marked out of stock' fails (`c-hidden-kill-catalog-stock.log`) |
| Bypass the medicine pharmacist gate | exit 0, 56/56, 2.535 s (`c-no-hidden-pharmacist-gate.log`) | exit 1, 5/6; 'a pharmacist-required product' fails (`c-hidden-kill-pharmacist-gate.log`) |

The test host junction makes Vite's dev-server test unable to write `node_modules/.vite-temp`. The suite-owned preload rejects only that exact junction directory's `mkdir` with `EACCES`, which triggers Vite's own config-adjacent fallback inside the disposable clone. The helper does not redirect arbitrary paths. The hidden logic suite does not render the button DOM; `npm run build` checks that the UI integration type-checks and bundles. No product source checkout was modified and no commit was made during authoring.
