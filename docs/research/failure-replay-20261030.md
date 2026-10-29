# 플러그인 ON 실패 원인 집계와 후보 장치 재생 (2026-10-30)

다음 고도화 지점을 기록으로 고르기 위한 조사다. 시작은 `wp-20261026-independent-path-check@a10f894`(깨끗한 working tree)다.
도구와 판정 규칙은 [failure replay](../../evals/failure-replay/README.md)가, 다음 평가의 사전 기준은
[L5 ON/OFF](../../evals/l5-on-off/README.md)(커밋 `a238650`, 유료 실행 전)가 소유한다.

## 원천

- 유효한 플러그인 ON 시도 64회: v1 0.1.87 16회(`%TEMP%/claude/delegation-eval-run5-v087`), v1 0.1.88 24회(`-run3` 1–2회차와
  `-run4-rep3`), v2 0.1.89 24회(`.work/delegation-eval/v2-0189-*`). 셀마다 `result.json`의 `verified_success`,
  `false_completion`, `stop_blocks`, `plugin_skills`, hidden 로그를 읽었다.
- `evals/delegation-v1/evidence`, `evals/delegation-v2/evidence`는 과제 작성(authoring) 증거로, 후보 Agent 시도가 아니다.
- `~/.claude/projects/C--e-w-*` 22개 전사본은 모두 2026-10-26 오프라인 경로 검증의 Claude 검증자 세션이다(코딩 시도 아님).
  `evals/path-check-offline/items.json`의 부분 구현도 작성된 패치다. 둘 다 실패 표에 넣지 않았다.
- `git log plugins/`: 각 시도의 빌드(0.1.87 `9f89615`, 0.1.88 `c9b6a56`, 0.1.89 `987dba7`)와 그 안의 장치를 확인했다.

## 실패 표 (유효 ON 64회 중 12회 실패)

| 원인 | 건수 | 실패 경로 | 당시 장치 (L1~L6) | Stop guard 차단 | 실패 시도 비용 합 |
| --- | --- | --- | --- | --- | --- |
| 같은 규칙의 다른 쓰기 경로 누락 (거짓 완료) | 6 | 복제 `duplicateProduct` 3건 (0.1.88 v1 r2, 0.1.89 v2 r1·r2), 백업 복원 3건 (0.1.87 v1 r1·r2, 0.1.89 `a-product-source-stale` r2) | 0.1.87 2건: Skill 미호출로 L1~L6 미로드. 0.1.88·0.1.89 4건: `agent-workflow` 호출로 L1·L2·L3·L4·L6 로드, L5 없음. 이 중 `probe_check.py prove` 실행 1건 | 0/6 | $13.58 |
| hidden 기대와 다른 동작 (`fe-logic-feature`: 99개 초과 시 잘라서 담음, 담은 뒤 선택 비움) | 5 | `add-selected-to-cart` 일괄 담기 | 0.1.87 2건 미로드, 0.1.88 3건 L1·L2·L3·L4·L6 로드 | 0/5 | $7.87 |
| 기존 회귀 timeout (`tests/fieldTranslations.test.ts` 5초), hidden은 통과 | 1 | `GET /api/translations/jobs` 변경 셀의 무관한 기존 테스트 | 0.1.88 L1·L2·L3·L4·L6 로드 | 0/1 | $0.58 |

모든 실패는 거짓 완료였고, 미완료를 밝힌 시도는 0회다. 0.1.87·0.1.88·0.1.89의 Stop guard 규칙은 "마지막 실행 뒤 코드 편집"뿐이었고,
유효 ON 64회 전체에서 `stop_blocks`는 0이다.

판정에서 제외된 ON 실패 6건은 따로 둔다: 중단된 v1 실행 2건(`delegation-eval-run2`의 `rule-all-paths` 복원 경로, `api-contract-change`),
공유 의존성 손상으로 무효가 된 run3 3회차 4건.

추정(표 밖): `fe-logic-feature`는 OFF도 3/3이 같은 해석으로 실패해 요청 문구와 hidden 기대가 어긋난 과제 결함으로 보인다.
timeout 1건은 같은 테스트가 다른 셀에서 통과하므로 환경 부하로 보인다. 두 원인은 플러그인 장치로 막을 대상이 아니다.

## 선택한 원인

건수 × 비용이 가장 큰 원인은 **같은 규칙의 다른 쓰기 경로 누락**이다(6건, $13.58, 평균 $2.26; 다음은 5건 $7.87).
L4(모든 경로 지침)가 로드된 4건에서도 났다.

## 후보 재생

시도들은 diff를 남기지 않았다. 그래서 `tools/reconstruct.py`로 전사본의 파일 변경 호출을 새 clone에서 다시 실행했다(`npm`/`npx`는 no-op).
복원한 9개(실패 6, 같은 과제·세대의 검증된 성공 대조 3)는 모두 기록된 회귀·v2 hidden 결과와 실패 단언 이름까지 같았다.
판정 규칙은 검증자 실행 전에 커밋했다(`cfced84`).

| 시도 | 놓친 경로 | 당시 guard | 현재 guard | B 경로 수 / 놓친 경로 위치 | A 판정 | A 규칙상 변화 | A가 놓친 경로를 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.1.88 v1 r2 | 복제 | 통과 | 차단 | 216 / 262번째 줄 | incomplete (NFKC) | 예 | 지목 안 함 |
| 0.1.87 v1 r1 | 복원 | 통과 | 차단 | 246 / 96번째 줄 | complete | 아니오 | 질문으로 |
| 0.1.87 v1 r2 | 복원 | 통과 | 차단 | 1 / 없음 | incomplete (NFKC) | 예 | 질문으로 |
| 0.1.89 v2 r1 | 복제 | 통과 | 차단 | 211 / 256번째 줄 | incomplete (NFKC) | 예 | 지목 안 함 |
| 0.1.89 v2 r2 | 복제 | 통과 | 차단 | 1 / 없음 | incomplete (NFKC, 복제) | 예 | 위반으로 |
| 0.1.89 stale r2 | 복원 | 통과 | 차단 | 해당 없음 | incomplete (복원) | 예 | 위반으로 |
| 대조 0.1.88 v1 r1 | — | 통과 | 차단 | 1 | incomplete (NFKC) | 예 (v3 hidden도 실패하는 실제 결함) | — |
| 대조 0.1.88 v1 r3 | — | 통과 | 차단 | 0 | complete | 아니오 | — |
| 대조 0.1.89 stale r1 | — | 통과 | 통과 | 75 | incomplete (계정 간 복원) | 아니오 (참조 구현도 같은 테스트 실패) | — |

| 후보 | 실패 6건 중 바뀌었을 것 | 판단 |
| --- | --- | --- |
| A. 현재 L5 독립 검증 (0.1.91–0.1.94, 같은 모델 새 맥락) | 사전 규칙 5건. 놓친 경로를 위반으로 지목 2건, 질문으로 2건, 못 찾음 2건 | 유지, ON/OFF로 측정 |
| B. 쓰기 경로 계산 (`inventory.py`, 모델 없음) | 원출력 기준 3건(경로 211–246개 속 96–262번째 줄). 프롬프트에 담을 수 있는 60줄 안에서는 0건 | 버림 |

- 현재 Stop guard는 실패 6건 모두에서 독립 검증을 요구했을 것이다. 당시 guard는 0건을 막았다.
- A의 사전 규칙상 변화 5건 중 3건은 v3 hidden이 잡는 NFKC 결함이다. 기록된 v2 hidden 실패 경로를 위반으로 지목한 것은 2건이므로
  v2 hidden 결과가 뒤집힐 수 있는 상한은 2/6이다(수정 단계는 재생하지 않음).
- A의 "질문으로" 2건은 결과 카드의 사용자 결정으로 올라간다. 기준대로면 구현자는 고치지 않으므로 headless 평가에서 hidden 결과는 바뀌지 않는다.
- B는 사전 규칙상 M=3이라 기계적 탈락 대상은 아니다. 다만 놓친 경로가 211–246개 목록의 96번째 줄 이후에 있다.
  이전 설계가 프롬프트에 넣던 60줄 상한 안에서는 0건이라 버렸다. 60줄 판정은 결과를 본 뒤 추가한 사후 기준이다.
- 검증자 9회 비용은 $8.02다. 오염 표지는 0건이다.

## 다음 평가

[사전 기준](../../evals/l5-on-off/README.md): delegation-v3 24셀 × `off`/`on`(0.1.94)/`on-no-l4`. 판정 기준은 다음과 같다.

- H: 성공 +3 이상.
- H-v2: v2 기원 검사에서 손실 없음.
- F: 거짓 완료가 OFF의 절반 이하.
- T: 성공당 토큰이 OFF의 1.20배 이하.
- V: 유효 셀 22개 이상.
- ablation: L4는 성공 손실이 1 이하이고 거짓 완료가 늘지 않으면 제거한다.

```powershell
python -B evals/l5-on-off/tools/run.py --output .work/l5-on-off/20261030-run
```

예상 비용은 $130–180이며, 이 문서는 그 지출을 승인하지 않는다.

## 한계

- 표본은 Labeler 실패 6건이고, 그중 5건이 `rule-all-paths`다. 인벤토리는 이 과제로 조정됐고, v3 hidden 추가분은 같은 계열 검증자가 찾은 결함이다.
- 복원 diff는 편집 스크립트 재실행이라 일치 근거는 회귀·hidden 재현뿐이다. 검증자 테스트 파일 목록에는 시도가 만든 새 테스트 파일도 섞인다.
  A의 판정은 "시도에서 실패하고 참조에서 실패하지 않는 테스트 이름"으로만 셌다.
- `named`/`asked`(위반·질문 문구의 경로 키워드)와 60줄 판정은 첫 결과를 본 뒤 추가한 설명 지표다. 사전 규칙의 숫자는 바꾸지 않았다.
- 원자료는 `.work/failure-replay/20261029/`(precheck·verify·retest·`report.json`)이며 `.work` 보존 정책에 따라 만료된다.
  복원 패치는 `evals/failure-replay/attempts/`에 커밋했다.
