# 0.1.88 lean delegation

[설계 기준](agent-coding-system-direction.md)의 첫 구현이다. 출발점은 clean
`wp-20261020-luna-0178-results@46356b2`(0.1.87), 작업 branch는 `wp-20261024-lean-delegation`이다.

## 바꾼 것

| 영역 | 변경 | 근거 |
| --- | --- | --- |
| Skill 노출 | 17개 Skill을 명시 호출 전용으로 전환(Claude `disable-model-invocation: true`, Codex `agents/openai.yaml` `allow_implicit_invocation: false`). 자동 호출은 5개 | 설명 합계 6,544자 → 자동 호출 5개 약 1,700자 |
| 명시 호출 연결 | `agent-workflow` capability 표가 필요에 따라 형제 Skill의 `SKILL.md`를 읽는다. 경로 링크가 아닌 이름 기반 선택 의존이라 단독 설치를 유지한다 | 사용자 요청 |
| 프롬프트 hook | 선택된 task가 없으면 Git·runtime을 실행하지 않고 route가 있을 때만 한 줄. task 후보 목록·미설정 안내 제거 | 0.1.87은 설정된 프로젝트의 모든 프롬프트에 후보 목록 주입 |
| route | 증상 표현 중심으로 재작성. 일반 변경 요청도 `agent-workflow`로. 따옴표 문구 편집·질문은 제외 | 아래 측정 |
| 위임 장치 | `agent-workflow`를 L1–L5(수락 기준 먼저, 테스트 유효성 증명, 같은 규칙의 모든 경로, 영향받는 기존 검사, 결과 카드)로 재작성. 플레이북·`diagnose`·`swarm`에 pstack 원칙 반영 | 거짓 완료·검출 누락 기록 |
| probe 등록부 | `probe_check.py probes|prove`: 격리 worktree에서 인공 결함 적용, Feature × 관점 × 계층 killed/total, 새 테스트가 변경 없이 실패하는지 증명 | 실제 제품에서 효과가 측정된 유일한 장치(Labeler 4/11 → 9/11) |
| 평가 | `scripts/run_delegation_eval.py`, `evals/delegation-v1/` | 사용자 기준: OFF 대비 측정 가능한 이득 |

## route 측정

키워드 router는 처음 보는 표현에 약했다. 최종 구조는 명시 유형(결과 조회·재개·검증 연결·가드레일·UI)을 먼저 보고,
질문·방법 문의·리뷰·요약·추천·이름 변경·버전·따옴표 문구 편집·짧은 메시지는 직접 처리한다. 증상 표현은 `diagnose`,
나머지 메시지는 작업으로 보고 `agent-workflow`로 보낸다.

| 프롬프트 세트 | 0.1.87 | 키워드 0.1.88 (중간) | 최종 0.1.88 |
| --- | --- | --- | --- |
| 기존 관찰 13개 (0.1.87 튜닝에 사용) | 13/13 | 13/13 | 13/13 |
| held-out 48개 (0.1.87 측정 후 작성) | 26/48 | 48/48 (튜닝) | 48/48 |
| 새 문맥 agent 40개 (`route_fresh.json`) | 14/40 | 첫 측정 25/40 → 튜닝 후 40/40 | 40/40 |
| 두 번째 새 문맥 40개: 필요할 때 플러그인 로드 (`route_fresh2.json`) | 7/31 | 첫 측정 15/31 | 30/31, 단순 요청 로드 0/10 |
| 평가 과제 프롬프트 9개: route 부여 | 2/9 | 4/9 | 9/9 |

평가 과제에서 키워드 router가 5/9를 놓쳐 첫 유료 평가(5회, $7.44)를 중단하고 기본 작업 route로 바꿨다. 이 변경은
평가 프롬프트의 route 여부를 본 뒤 이뤄졌으므로 평가 프롬프트의 route 9/9는 일반화 근거가 아니다. 일반화 근거는
두 번째 새 문맥 세트의 30/31이다(이 구조로 처음 측정, 세트 내용은 앞선 키워드 측정 때 이미 봤음). 증상 서술형
버그 다수는 `diagnose` 대신 `agent-workflow`로 가며, 그 버그 수정 플레이북과 `diagnose` 연결이 처리한다.

## Host 확인 (Claude Code 2.1.309, `claude-opus-5-5`, 2026-10-24)

같은 사소한 프롬프트, 전역 `agentic-coding` 비활성(`--settings`), 패키지는 `--plugin-dir`로만 로드했다.
Git 저장소이지만 Harness 설정이 없는 빈 프로젝트다.

| 조건 | 첫 요청 입력 토큰 (cache 포함) | OFF 대비 | 모델이 본 `agentic-coding` Skill |
| --- | --- | --- | --- |
| OFF | 29,547 | — | 없음 |
| 0.1.87 | 31,931 | +2,384 | 22개 |
| 0.1.88 | 30,079 | +532 | 5개 (agent-workflow, diagnose, fixing-accessibility, recall, setup-project-verification) |

0.1.87은 설정된 프로젝트에서 매 프롬프트 task 후보 JSON(약 700자)을 추가로 주입했다. 0.1.88은 route가 없으면
주입하지 않는다. 명시 호출 연결 확인: 병렬 구현 요청에 모델이 `agent-workflow`를 호출한 뒤 capability 표에 따라
`skills/swarm/SKILL.md`를 직접 읽었다(Skill 이름을 프롬프트에 준 도움 받은 1회).

## 평가 중 발견한 사고와 수리

두 번째 유료 평가(8회, $11.24) 중 0.1.88 agent가 `probe_check.py prove`의 임시 worktree 안에 직접 `node_modules`
junction을 만들었다. 정리 단계의 `git worktree remove --force`가 그 junction을 따라가 원본 Labeler의
`node_modules`에서 `.bin`과 패키지 약 20개를 지웠다. 평가를 즉시 중단했고, lockfile 변경 없이 `npm install`로
빠진 패키지만 복구한 뒤 별도 clone에서 Labeler 테스트 통과를 확인했다. 원본 소스와 Git 상태는 변하지 않았다.

- `probe_check.py`는 이제 사본 안의 모든 symlink·junction을 만든 주체와 관계없이 먼저 끊은 뒤 사본을 지운다.
  수정 전 코드에서 외부 파일이 지워지는 회귀 테스트로 재현했다.
- `agent-workflow`는 링크를 직접 만들지 말고 `--link node_modules`를 쓰라고 안내한다.
- 평가 runner는 `--deps-root`로 평가 전용 의존성 사본에 연결하고, `--prune-clones`로 채점 후 링크를 끊고
  clone을 지운다. agent의 `npm install`이 사용자 프로젝트를 바꾸지 않는다.
- 같은 실행에서 `rule-all-paths`의 0.1.88 agent는 복원 경로를 찾았지만 스스로 예외로 두고 공개했다. 요청이
  모든 저장에 규칙을 말할 때 경로 예외는 사용자가 정할 일이라는 문장을 L4에 추가했다.

중단된 두 평가(13회, 약 $19)는 판정에 쓰지 않는다. 각 결과 파일은 보존한다.

## 평가 결과 (2026-10-24)

`evals/delegation-v1/` 8개 과제, Claude Code 2.1.309 headless, `claude-opus-5-5`, 전역 플러그인 비활성 후
`--plugin-dir`로만 로드했다. OFF·0.1.88은 각 24회(run3의 1–2회차와, 공유 의존성 손상으로 무효가 된 3회차를
실행별 의존성 사본으로 다시 돌린 결과), 0.1.87은 16회다. 패키지는 `c9b6a56`에서 빌드한 고정 사본이다.
원본 raw는 `%TEMP%/claude/delegation-eval-run3`, `-run4-rep3`, `-run5-v087`의 `result.json`·transcript·판정 로그다.

| 조건 | 검증된 성공 | 거짓 완료 | probe 검출 (적용 n) | 회당 비용 | 회당 토큰 | 성공당 토큰 | 중앙 시간 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OFF | 18/24 (75%) | 6/24 | 0.67 (12) | $1.28 | 1.61M | 2.14M | 517초 |
| 0.1.87 | 12/16 (75%) | 4/16 | 0.75 (8) | $1.39 | 1.87M | 2.50M | 503초 |
| 0.1.88 | 19/24 (79%) | 5/24 | 0.86 (14) | $1.58 | 1.98M | 2.51M | 638초 |

| 과제 | OFF | 0.1.87 | 0.1.88 |
| --- | --- | --- | --- |
| rule-all-paths (같은 규칙의 모든 저장 경로) | 0/3 | 0/2 | 2/3 |
| api-contract-change | 3/3 | 2/2 | 2/3 (기존 테스트 5초 timeout 1회) |
| fe-logic-feature (요청 문장이 모호, 모든 조건 동일 해석) | 0/3 | 0/2 | 0/3 |
| 나머지 5개 | 15/15 | 10/10 | 15/15 |

**판정: 채택 기준 미달.** 미리 정한 기준(성공 +15%p, 거짓 완료 절반, 성공당 토큰 OFF 이하)을 넘지 못했다.
0.1.88은 OFF보다 성공 +1, 거짓 완료 −1, probe 검출이 높았지만 표본이 작아 차이를 주장할 수 없다.
회당 비용·토큰·시간은 약 23% 늘었다. 0.1.87은 Skill이 한 번도 호출되지 않았고(OFF와 같은 성공률) 회당
토큰이 OFF보다 16% 많았다.

관찰한 사실:
- 차이를 만든 과제는 `rule-all-paths` 하나다. L4에 "모든 저장에 대한 규칙에서 경로 예외는 사용자 결정"을
  넣은 뒤의 두 실행 중 두 번 성공했다. 같은 과제에서 OFF와 0.1.87은 모두 복원 경로를 놓치고 완료를 주장했다.
- 추가 비용은 테스트 실행 증가에서 나온다(증명 단계와 영향받는 기존 검사). 만점 과제에서도 같은 비용이 든다.
  예: `complaint-bypass` OFF 회당 $0.52, 0.1.88 $0.97, 둘 다 3/3.
- 8개 중 5개는 모든 조건이 만점, 1개는 모두 실패해 과제 세트의 변별력이 낮다.
- 평가 중 세 가지 결함을 고쳤다: probe 정리의 링크 추적(원본 의존성 삭제 사고), junction인 `node_modules`의
  `--link` 거부, 실행 간 공유 의존성 손상과 남은 dev 서버.

다음 판단에 필요한 것:
- 변별력 있는 과제 세트 v2: 여러 쓰기 경로·우회 경로·후속 회귀처럼 OFF가 반복해서 놓치는 유형 10–12개.
  모호한 `fe-logic-feature`는 요청 문장을 고치거나 제외한다.
- 비용 절감: 증명과 추가 검사를 업무 규칙·버그 수정처럼 효과가 관찰된 유형으로 한정하고 같은 과제에서 다시 잰다.
- 그 전까지 이 플러그인이 위임 결과를 개선한다고 보고하지 않는다. 확인된 개선은 상시 컨텍스트 감소(OFF 대비
  +2,384 → +532 토큰), route가 필요한 요청에서 플러그인을 로드하는 비율, 그리고 `rule-all-paths` 유형의 방향성이다.

유료 실행 합계는 약 $125다(중단·무효 실행 약 $30 포함). 설치본·전역 설정은 바꾸지 않았다.

## 0.1.89와 평가 세트 v2 (중단)

0.1.88 transcript 분석에서 추가 비용은 증명 명령(실행당 0.08회)이 아니라 부분 테스트 실행(+1.9회)과 브라우저
확인(+0.9회)에서 나왔다. 0.1.89는 구현 전 실패 확인을 증명으로 인정하고, 증명은 나중에 쓴 테스트에만
`--skip-current`로 돌리며, 새 테스트와 영향받는 기존 검사를 최종 편집 뒤 한 번에 실행하고, 브라우저는 자동 UI
테스트가 덮지 못하는 변경에만 연다. L4(모든 경로)는 그대로다. 패키지는 `2800da2`에서 빌드했다.

`evals/delegation-v2/`는 OFF가 놓치기 쉬운 유형으로 미리 고른 새 과제 11개와 v1 `rule-all-paths` 앵커로
구성했고(Codex 작성), 12개 모두 시작 실패·참조 통과·회귀 통과를 독립 재검증했다. 여러 과제가 적용 경로를
프롬프트에 직접 나열하므로 경로 발견보다 구현의 빠짐없음을 잰다.

앞선 OFF와 0.1.89 각 24회 평가는 사용자 요청으로 첫 실행들이 끝나기 전에 중단했다. 당시 완료된 실행이 없어
0.1.89의 효과는 **측정되지 않았다**. 아래 새 실행은 같은 조건을 사용한다([testing](../testing.md#delegation-effect-evaluation)):
`--condition off=off --condition lean=plugin:<0.1.89 package> --reps 2 --deps-root <eval-deps> --copy-deps --prune-clones`.

### 2026-10-24~25 실행 상태: 인프라 오류로 중단

기준은 `main@b347eec`, 결과 branch는 `wp-20261024-v2-0189-evaluation`이다. 별도 깨끗한 checkout의 `2800da212b3f791097ef604888c210961cbbaebe`에서 `scripts/build_plugin.py`로 0.1.89를 빌드했다. `package-files.json`의 SHA256은 `868239003b6266c4f8e6ef8e6be302a3e211d281d1367f43fc087533adf9cb1f`다. 실제 실행은 Claude Code `2.1.310`, `claude-opus-5-5`이며 완료 셀의 init에서 OFF의 agentic-coding 미로드, ON의 고정 0.1.89 로드를 확인했다. 다른 설치 플러그인은 양 조건에 동일하게 남는다.

최초 5셀 뒤 앞선 4셀 평균으로 전체 비용을 $115.49로 전망해 중단했으나, 사용자가 재개 및 $90 상한 해제를 명시 지시했다. 기존 결과를 재사용하고 나머지를 순서대로 실행했다. 두 조건 모두 원본 working tree를 복사하지 않는 고정 ref clone, 독립 의존성 사본, 동시 2셀, 과제별 세션 시간 제한, 고정 probe·회귀·hidden 판정을 유지했다. 최초 셀의 예산 제한은 발동하지 않았고 재개부터 제거했다.

현재 중단은 의약품 분류 OFF의 clone checkout 실패가 같은 셀의 1회 재시도에서도 반복됐기 때문이다. Windows Git의 최장 경로가 276자였고 `Filename too long`으로 종료했다. 두 실패 모두 Claude 세션 시작 전이라 비용은 없으며 행동 판정에서 제외했다. 이미 진행 중이던 장바구니 ON을 마친 뒤 최초 지시인 “인프라 오류가 반복되면 중단·보고”를 지켰다. 미완료 28셀의 결과를 추정하거나 실패로 넣지 않는다.

해결책은 전역 설정 변경 없이 새 clone에만 `git clone ... -c core.longpaths=true`를 적용하는 것이다. 별도 무료 대조 시험에서 285자 경로, 고정 커밋의 1,736개 파일 존재, 최장 파일의 Git blob 바이트 일치, 전역 Git 설정 보존 및 비재귀 정리를 확인했다. `.work/delegation-eval/v2-0189-20261025-longpath-control/control.json`에 증거가 있다. 후속 28셀 실행은 준비됐으며, 반복 오류 중단 조건 이후의 사용자 재개 지시를 기다린다.

실행 전 SHA256 302개 중 43개가 불일치했다. 41개는 CRLF→LF로 일치하고, 나머지는 과거 authoring 증거 `evidence/a-offer-quantity-all-paths/c-reference-product.ts`, `d-reference-backup.ts`로 Git blob도 manifest와 다르다. 이를 보고한 뒤 사용자가 실행을 지시했다. 과제·프롬프트·hidden 파일은 수정하지 않았으며, 전체 세트의 byte-exact freeze 검증 통과로 주장하지 않는다.

기존 5셀을 재사용하고 사용자의 명시 지시로 $90 상한을 해제해 나머지를 실행했다. 누적 시도 22회, 행동 판정 포함 20/48셀, 인프라 제외 시도 2회다. 알려진 세션 비용 합계 $35.6892, 비용 미상 시도 0회. 중단 사유: `infrastructure failure repeated in same cell`(의약품 분류 OFF의 clone 경로 길이 오류).

| 조건 | 검증된 성공 | 거짓 완료 | probe 검출/적용 | 회당 비용 USD | 회당 토큰 | 성공당 토큰 | 회당 시간 초 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| off | 10/10 | 0/10 | 13/17 | 1.7892 | 2,731,589 | 2,731,589 | 683.2 |
| lean | 10/10 | 0/10 | 14/17 | 1.7797 | 2,854,656 | 2,854,656 | 613.6 |

토큰은 input/output/cache read/cache creation의 합계다. 시간은 clone·의존성 복사·세션·채점을 포함한 정리 전 wall_seconds 평균이다. 제외된 시도는 행동 지표에서 빼고 비용에는 남긴다. 적용 문자열이 없는 probe는 probe 분모에서만 제외한다.

| 과제 / 조건 | 검증된 성공 | 거짓 완료 | probe 검출/적용 | 회당 비용 USD | 회당 토큰 | 성공당 토큰 | 회당 시간 초 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| a-offer-quantity-all-paths / off | 1/1 | 0/1 | 2/2 | 2.8034 | 5,034,494 | 5,034,494 | 932.5 |
| a-offer-quantity-all-paths / lean | 1/1 | 0/1 | 1/2 | 3.2220 | 6,501,086 | 6,501,086 | 968.8 |
| a-product-source-stale-all-paths / off | 1/1 | 0/1 | 0/1 | 2.0695 | 3,682,669 | 3,682,669 | 1,037.6 |
| a-product-source-stale-all-paths / lean | 1/1 | 0/1 | 0/1 | 1.7340 | 2,972,593 | 2,972,593 | 489.2 |
| a-product-name-whitespace-complaint / off | 1/1 | 0/1 | 2/2 | 1.1451 | 1,612,035 | 1,612,035 | 484.4 |
| a-product-name-whitespace-complaint / lean | 1/1 | 0/1 | 2/2 | 0.8474 | 1,194,814 | 1,194,814 | 539.2 |
| a-import-offer-sequence / off | 1/1 | 0/1 | 1/1 | 3.1870 | 4,357,121 | 4,357,121 | 1,117.8 |
| a-import-offer-sequence / lean | 1/1 | 0/1 | 1/1 | 3.0650 | 4,122,098 | 4,122,098 | 884.2 |
| a-update-offer-list-complaint / off | 1/1 | 0/1 | 2/2 | 1.0433 | 1,282,838 | 1,282,838 | 351.8 |
| a-update-offer-list-complaint / lean | 1/1 | 0/1 | 2/2 | 1.1818 | 1,414,021 | 1,414,021 | 394.8 |
| b-sequence-category-branch-copy / off | 1/1 | 0/1 | 0/0 | 2.8324 | 4,167,110 | 4,167,110 | 995.3 |
| b-sequence-category-branch-copy / lean | 1/1 | 0/1 | 0/0 | 2.2470 | 3,208,134 | 3,208,134 | 908.6 |
| b-entitlement-design-save-api / off | 1/1 | 0/1 | 2/3 | 0.9204 | 1,291,983 | 1,291,983 | 408.8 |
| b-entitlement-design-save-api / lean | 1/1 | 0/1 | 2/3 | 0.9314 | 1,223,820 | 1,223,820 | 276.8 |
| b-contract-catalog-default-page / off | 1/1 | 0/1 | 0/2 | 1.0055 | 1,266,415 | 1,266,415 | 324.9 |
| b-contract-catalog-default-page / lean | 1/1 | 0/1 | 0/0 | 1.4995 | 2,619,007 | 2,619,007 | 644.1 |
| b-cross-path-custom-unit-limit / off | 1/1 | 0/1 | 1/1 | 1.2364 | 1,682,280 | 1,682,280 | 742.1 |
| b-cross-path-custom-unit-limit / lean | 1/1 | 0/1 | 3/3 | 1.1660 | 1,759,425 | 1,759,425 | 532.9 |
| cart-item-to-compare / off | 1/1 | 0/1 | 3/3 | 1.6489 | 2,938,948 | 2,938,948 | 437.0 |
| cart-item-to-compare / lean | 1/1 | 0/1 | 3/3 | 1.9031 | 3,531,558 | 3,531,558 | 496.8 |
| medicine-catalog-classification-bypass / off | 미실행 | — | — | — | — | — | — |
| medicine-catalog-classification-bypass / lean | 미실행 | — | — | — | — | — | — |
| rule-all-paths / off | 미실행 | — | — | — | — | — | — |
| rule-all-paths / lean | 미실행 | — | — | — | — | — | — |

**판정: 불완전한 행렬로 판정 보류**.

성공 차이가 난 과제:

- 동일하게 관측된 과제에서 성공 수 차이 없음.

과제별 비용·도구 관측:

- `a-offer-quantity-all-paths` — off: 비용 $2.8034, cache read 4,849,569, output 29,533, Bash 43, 검사 8, 증명 0; 근거 `.work/delegation-eval/v2-0189-20261024-run/cells/a-offer-quantity-all-paths/off/rep1/session1.jsonl:289` / lean: 비용 $3.2220, cache read 6,307,489, output 34,349, Bash 53, 검사 7, 증명 1; 근거 `.work/delegation-eval/v2-0189-20261024-run/cells/a-offer-quantity-all-paths/lean/rep1/session1.jsonl:317`.
- `a-product-source-stale-all-paths` — off: 비용 $2.0695, cache read 3,541,054, output 19,052, Bash 35, 검사 6, 증명 0; 근거 `.work/delegation-eval/v2-0189-20261024-run/cells/a-product-source-stale-all-paths/off/rep1/session1.jsonl:180` / lean: 비용 $1.7340, cache read 2,850,996, output 15,945, Bash 30, 검사 4, 증명 0; 근거 `.work/delegation-eval/v2-0189-20261024-run/cells/a-product-source-stale-all-paths/lean/rep1/session1.jsonl:194`.
- `a-product-name-whitespace-complaint` — off: 비용 $1.1451, cache read 1,525,922, output 12,596, Bash 18, 검사 5, 증명 0; 근거 `.work/delegation-eval/v2-0189-20261024-run/cells/a-product-name-whitespace-complaint/off/rep1/session1.jsonl:85` / lean: 비용 $0.8474, cache read 1,130,927, output 9,191, Bash 15, 검사 3, 증명 0; 근거 `.work/delegation-eval/v2-0189-20261024-resume1/cells/a-product-name-whitespace-complaint/lean/rep1/session1.jsonl:110`.
- `a-import-offer-sequence` — off: 비용 $3.1870, cache read 4,121,385, output 39,775, Bash 51, 검사 10, 증명 0; 근거 `.work/delegation-eval/v2-0189-20261024-resume1/cells/a-import-offer-sequence/off/rep1/session1.jsonl:199` / lean: 비용 $3.0650, cache read 3,894,710, output 38,949, Bash 44, 검사 7, 증명 0; 근거 `.work/delegation-eval/v2-0189-20261024-resume1/cells/a-import-offer-sequence/lean/rep1/session1.jsonl:187`.
- `a-update-offer-list-complaint` — off: 비용 $1.0433, cache read 1,199,427, output 11,355, Bash 18, 검사 3, 증명 0; 근거 `.work/delegation-eval/v2-0189-20261024-resume1/cells/a-update-offer-list-complaint/off/rep1/session1.jsonl:89` / lean: 비용 $1.1818, cache read 1,316,136, output 11,301, Bash 13, 검사 2, 증명 0; 근거 `.work/delegation-eval/v2-0189-20261024-resume1/cells/a-update-offer-list-complaint/lean/rep1/session1.jsonl:195`.
- `b-sequence-category-branch-copy` — off: 비용 $2.8324, cache read 3,974,090, output 41,159, Bash 52, 검사 13, 증명 0; 근거 `.work/delegation-eval/v2-0189-20261024-resume1/cells/b-sequence-category-branch-copy/off/rep1/session1.jsonl:79` / lean: 비용 $2.2470, cache read 3,048,618, output 30,132, Bash 44, 검사 11, 증명 0; 근거 `.work/delegation-eval/v2-0189-20261024-resume1/cells/b-sequence-category-branch-copy/lean/rep1/session1.jsonl:128`.
- `b-entitlement-design-save-api` — off: 비용 $0.9204, cache read 1,223,030, output 10,365, Bash 22, 검사 1, 증명 0; 근거 `.work/delegation-eval/v2-0189-20261024-resume1/cells/b-entitlement-design-save-api/off/rep1/session1.jsonl:158` / lean: 비용 $0.9314, cache read 1,151,458, output 10,199, Bash 19, 검사 2, 증명 0; 근거 `.work/delegation-eval/v2-0189-20261024-resume1/cells/b-entitlement-design-save-api/lean/rep1/session1.jsonl:124`.
- `b-contract-catalog-default-page` — off: 비용 $1.0055, cache read 1,188,820, output 12,262, Bash 14, 검사 0, 증명 0; 근거  / lean: 비용 $1.4995, cache read 2,521,336, output 17,842, Bash 32, 검사 9, 증명 0; 근거 `.work/delegation-eval/v2-0189-20261024-resume1/cells/b-contract-catalog-default-page/lean/rep1/session1.jsonl:158`.
- `b-cross-path-custom-unit-limit` — off: 비용 $1.2364, cache read 1,589,307, output 14,579, Bash 23, 검사 5, 증명 0; 근거 `.work/delegation-eval/v2-0189-20261024-resume1/cells/b-cross-path-custom-unit-limit/off/rep1/session1.jsonl:123` / lean: 비용 $1.1660, cache read 1,676,722, output 14,107, Bash 24, 검사 4, 증명 5; 근거 `.work/delegation-eval/v2-0189-20261024-resume1/cells/b-cross-path-custom-unit-limit/lean/rep1/session1.jsonl:133`.
- `cart-item-to-compare` — off: 비용 $1.6489, cache read 2,834,446, output 20,527, Bash 34, 검사 5, 증명 0; 근거 `.work/delegation-eval/v2-0189-20261024-resume1/cells/cart-item-to-compare/off/rep1/session1.jsonl:236` / lean: 비용 $1.9031, cache read 3,414,506, output 23,677, Bash 40, 검사 1, 증명 0; 근거 `.work/delegation-eval/v2-0189-20261024-resume1/cells/cart-item-to-compare/lean/rep1/session1.jsonl:248`.

도구 호출은 작업량의 관측이며 비용의 직접 배분이 아니다. 비용 차이의 원인은 토큰 구성 및 해당 transcript의 실제 검사·수정·재검사 순서와 함께 해석한다.

제외한 시도와 사유:

- `C:\Users\YS\Desktop\python\Skill_Management\.work\delegation-eval\v2-0189-20261024-resume1\cells\medicine-catalog-classification-bypass\off\rep1`: CalledProcessError: Command '['git', 'clone', '-q', '--local', '--no-hardlinks', 'C:\\Users\\YS\\Desktop\\python\\yeondoo-link', 'C:\\Users\\YS\\Desktop\\python\\Skill_Management\\.work\\delegation-eval\\v2-0189-20261024-resume1\\cells\\medicine-catalog-classification-bypass\\off\\rep1\\repo']' returned non-zero exit status 128.
- `C:\Users\YS\Desktop\python\Skill_Management\.work\delegation-eval\v2-0189-20261024-resume1\retry1\medicine-catalog-classification-bypass\off\rep1`: CalledProcessError: Command '['git', 'clone', '-q', '--local', '--no-hardlinks', 'C:\\Users\\YS\\Desktop\\python\\yeondoo-link', 'C:\\Users\\YS\\Desktop\\python\\Skill_Management\\.work\\delegation-eval\\v2-0189-20261024-resume1\\retry1\\medicine-catalog-classification-bypass\\off\\rep1\\repo']' returned non-zero exit status 128.

probe 해석 한계: 사전 고정 명령은 지정된 기존 테스트 파일만 실행하므로 후보가 새 파일에 쓴 검사를 누락할 수 있다. 예를 들어 최초 가격 옵션 ON은 `tests/offerRules.test.ts`에 quantity=1000 사례를 썼지만(최초 raw `lean/rep1/session1.jsonl:297`) 해당 probe 명령은 그 파일을 실행하지 않는다. 따라서 공식 probe 미검출을 후보의 보호 테스트 부재로 해석할 수 없다. 관측 후 probe 명령을 바꾸거나 점수를 보정하지 않았으며, 새 테스트가 그 mutant를 실제 검출하는지도 별도로 실행하지 않았다.

표본 한계: 과제당 조건별 2회이고 같은 제품·실패 유형의 12과제여서 일반적인 위임 성공률이나 통계적 우월성을 확정하지 못한다. 경로를 직접 나열하는 프롬프트와 v1 anchor가 포함된다. 초기 SHA256 편차는 원본 preflight에 보존했고 파일은 수정하지 않았다. reasoning effort는 명시 고정하지 않았다.

Raw: `.work/delegation-eval/v2-0189-20261024-run/`(최초 5셀), `.work/delegation-eval/v2-0189-20261024-resume1/`(추가 셀과 누적 state/report/analysis). 원본 결과를 덮어쓰지 않았다.

정리는 소유한 경로 안에서 junction을 `cmd /c rmdir`로 분리한 뒤 파일 unlink와 디렉터리 rmdir를 사용했다. 재귀 clone 삭제는 사용하지 않았다. 최초 5셀과 재개 구간의 모든 실행 clone·전용 의존성 사본 부재를 확인했고, 과거 출력은 보존했다. 전역 설정·설치본을 변경하는 명령, push는 실행하지 않았다. 재개 중 기록한 전역 설정·설치 등록 파일 해시도 종료 시 같았다.

검증 범위: package inventory 파일 해시와 junction 외부 대상 보존·비재귀 정리·범위 밖 삭제 거부 시험은 통과했다. 기존 runner 단위 검사 20개는 Windows 임시 디렉터리 잠금 오류 1개 및 cp949 reader 오류가 있어 통과로 주장하지 않는다. Feature는 `agent-workflow`의 평가 증거이며 기능·평가 정의를 바꾸지 않아 Feature Map 행 변경은 없다. 초기 불균형 행렬의 Markdown 렌더링 오류는 저장된 JSON에서 재생성했으며 유료 셀 재실행이나 판정 변경은 하지 않았다.
