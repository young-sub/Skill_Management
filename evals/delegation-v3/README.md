# Delegated coding evaluation v3

v3 is v2 with three hidden checks added. Prompts, projects, pinned refs, faults, probes, regression commands and
budgets are byte-identical to `../delegation-v2/scenarios.json`; `build_scenarios.py` asserts the prompts match.

## Why

The offline independent path check ([record](../../docs/research/independent-path-check-offline.md)) replayed tests
that fresh verifiers wrote against the v2 reference implementations. Three of them showed requested behaviour the v2
hidden checks never exercised, so v2 counted defective implementations as verified successes.

| Scenario | Added hidden check | Requested behaviour |
| --- | --- | --- |
| `rule-all-paths` | `stored-description-limit-after-normalization` | "300자를 넘는 내용은 저장되지 않게": the stored (NFKC-normalized) description, on create and edit |
| `b-sequence-category-branch-copy` | `restore-keeps-category-tree-within-three-levels` | "분류 트리는 언제나 최대 3단계": an update restore that re-parents an existing category |
| `a-import-offer-sequence` | `legacy-layout-blank-offer-cells-keep-current-offers` | "가격 옵션 칸이 모두 비어 있으면 ... 현재 옵션 전체를 ... 유지": the older spreadsheet column layout |

The three references under `reference/` fix those defects; the other nine use the v2 reference. Each scenario's
`reference_patch` names the file. Hidden checks carry `origin: "v2"` or `"v3"` so reports can score v2-only success
separately. Evidence is in [VALIDATION.md](VALIDATION.md).

## Bias

All three additions come from defects an independent verifier found. A condition that runs a verifier with the same
prompt is therefore favoured on these checks. Report v2-origin and v3-origin results separately, and do not treat the
additions as a sample of all missing checks: they are the ones one verifier happened to find.

## Rebuild

```powershell
python -B evals/delegation-v3/build_scenarios.py          # write scenarios.json and hidden/v2 copies
python -B evals/delegation-v3/build_scenarios.py --check  # verify only
```
