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

## 0.1.89와 평가 세트 v2

0.1.88 transcript 분석에서 추가 비용은 증명 명령(실행당 0.08회)이 아니라 부분 테스트 실행(+1.9회)과 브라우저 확인(+0.9회)에서 나왔다. 0.1.89는 구현 전 실패 확인을 증명으로 인정하고, 증명은 나중에 쓴 테스트에만 `--skip-current`로 돌리며, 새 테스트와 영향받는 기존 검사를 최종 편집 뒤 한 번에 실행하고, 브라우저는 자동 UI 테스트가 덮지 못하는 변경에만 연다. L4(모든 경로)는 그대로다.

`evals/delegation-v2/`는 OFF가 놓치기 쉬운 유형으로 실행 전에 고른 새 과제 11개와 v1 `rule-all-paths` 앵커로 구성했다(Codex 작성). 12개 모두 시작 실패·참조 통과·회귀 통과를 독립 재검증했다. 여러 프롬프트가 적용 경로를 직접 나열하므로 경로 발견보다 구현의 빠짐없음을 잰다. 결과를 본 뒤 과제·프롬프트·hidden·probe·판정 기준은 변경하지 않았다.

### 실행 조건과 경로 오류 복구

초기 평가 기준은 `main@b347eec`이며, 이번 재개 시작은 `wp-20261024-v2-0189-evaluation@cdd0deec6d0f6c5a03a2047bd723262080efb2f5`(깨끗한 working tree)다. 별도 깨끗한 checkout의 `2800da212b3f791097ef604888c210961cbbaebe`에서 `scripts/build_plugin.py`로 0.1.89를 빌드했다. 고정 패키지 `package-files.json`의 SHA256은 `868239003b6266c4f8e6ef8e6be302a3e211d281d1367f43fc087533adf9cb1f`다. 재개 전 303개 파일 해시가 모두 일치했다. 평가 대상 패키지는 실행기 수정과 분리했다.

실행 조건은 `--condition off=off --condition lean=plugin:<고정 0.1.89 package> --reps 2 --jobs 2 --deps-root <eval-deps> --copy-deps --prune-clones`다. 사용자가 $90 상한을 해제하고 모든 남은 셀의 시도를 지시했다. 원본 working tree를 복사하지 않는 고정 ref clone, 독립 의존성 사본, 과제별 세션 시간 제한, 고정 probe·회귀·hidden 판정을 유지했다. 최초 셀의 예산 제한은 발동하지 않았고 이후 제거했다. 실제 모델·CLI는 init 기록의 `claude-opus-5-5` / `2.1.310`다. OFF의 agentic-coding 미로드와 lean의 고정 0.1.89 로드를 확인했다. 다른 설치 플러그인은 양 조건에 동일하게 남는다. reasoning effort는 명시 고정하지 않았다.

이전 중단 원인은 실행기가 읽기 쉬운 결과 경로 아래에 clone까지 만든 설계였다. 의약품 과제의 126자 추적 파일 경로가 합계 276자가 되어 Git checkout이 `Filename too long`으로 실패했다. 같은 셀의 무료 clone 시도 2회가 제외됐고, 유효 20셀과 누적 $35.6892176을 보존했다. `core.longpaths=true` 우회는 이번 재개에 사용하지 않았다.

실행기 근본 수정 `e6b34ef7badf26c12b63dbe33cb8c7fe62097576`는 clone과 의존성 사본을 `.work/e/<8자 셀 해시>/r`, `d/<의존성>`로 분리한다. 결과 경로에는 `workspace.json` 매핑을 남긴다. clone 전에 고정 ref의 `git ls-tree`와 의존성 최장 상대 경로를 계산하고, 기본 상한 240자(파일 259·디렉터리 248자 이내)를 적용한다. 초과 시 `%SystemDrive%/e/<hash>`로 전환하고 그래도 불가능하면 유료 세션 없이 `path_budget_exceeded`로 제외하고 다음 셀로 간다. clone·checkout은 `core.longpaths=false`를 명시한다. 정리는 소유한 짧은 루트 내부만 허용하고 junction을 `cmd /c rmdir`로 끊은 뒤 개별 unlink/rmdir하며 재귀 삭제하지 않는다.

무료 실제 대조 시험은 의약품 과제의 고정 ref에서 1,736개 추적 파일 존재, 최장 파일 blob 바이트 일치, Node 읽기, 실제 의존성 복사, 설정·원본 프로젝트 상태 전후 동일 및 정리 후 잔여물 없음을 확인했다. 최장 파일 절대 경로는 189자였다. 호스트의 `LongPathsEnabled`는 요청의 예상값 0과 달리 현재 1이었으며 변경하지 않았다. 경로는 기본 제한 아래이며 Git 긴 경로 지원은 명시적으로 껐다. 증거는 `.work/delegation-eval/v2-0189-20261025-shortpath-control/`에 있다.

기존 유효 20셀은 긴 작업 경로, 새 시도 28셀은 짧은 작업 경로에서 실행됐다. 경로 전략은 각 구간의 OFF·lean에 똑같이 적용했다. `--resume-from`으로 기존 유효 결과와 모든 비용을 유지하고 이미 유료 실행된 셀은 재실행하지 않았다. 셀 예외가 전체 행렬을 중단하지 않으며 상태를 원자적으로 저장한다.

### 누적 결과

서로 다른 셀 48/48개를 시도했다. 누적 시도 50회, 유효 48/48셀, 제외 시도 2회다. 총 기록 비용은 $84.6308, 비용 미상 시도 0회다. 제외 시도도 비용 합계에 남기고 행동 판정은 유효 셀만 사용한다. 미완료·제외 결과를 추정하지 않았다.

새 28셀을 모두 마쳐 `pending=0`이다. 실행기 종료 코드 1은 검증 실패 셀이 있다는 뜻이며, 인프라 오류나 행렬 실행 중단이 아니다.

| 조건/과제 | 검증된 성공 | 거짓 완료 | probe 검출/적용 | 회당 비용 USD | 회당 토큰 | 성공당 토큰 | 회당 시간 초 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| off | 22/24 | 2/24 | 29/38 | 1.7229 | 2,514,273 | 2,742,843 | 593.1 |
| lean | 21/24 | 3/24 | 32/40 | 1.8034 | 2,920,126 | 3,337,287 | 587.5 |

| 조건/과제 | 검증된 성공 | 거짓 완료 | probe 검출/적용 | 회당 비용 USD | 회당 토큰 | 성공당 토큰 | 회당 시간 초 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| a-offer-quantity-all-paths / off | 2/2 | 0/2 | 3/4 | 2.9013 | 5,333,440 | 5,333,440 | 943.8 |
| a-offer-quantity-all-paths / lean | 2/2 | 0/2 | 2/4 | 2.9722 | 5,911,294 | 5,911,294 | 854.3 |
| a-product-source-stale-all-paths / off | 2/2 | 0/2 | 0/2 | 2.3974 | 4,259,538 | 4,259,538 | 829.4 |
| a-product-source-stale-all-paths / lean | 1/2 | 1/2 | 0/2 | 1.8982 | 3,285,231 | 6,570,462 | 500.9 |
| a-product-name-whitespace-complaint / off | 2/2 | 0/2 | 4/4 | 1.0981 | 939,312 | 939,312 | 429.1 |
| a-product-name-whitespace-complaint / lean | 2/2 | 0/2 | 4/4 | 0.9817 | 730,358 | 730,358 | 504.1 |
| a-import-offer-sequence / off | 2/2 | 0/2 | 2/2 | 3.0089 | 3,289,544 | 3,289,544 | 936.3 |
| a-import-offer-sequence / lean | 2/2 | 0/2 | 2/2 | 2.8435 | 3,831,298 | 3,831,298 | 775.2 |
| a-update-offer-list-complaint / off | 2/2 | 0/2 | 4/4 | 1.1552 | 1,574,250 | 1,574,250 | 395.0 |
| a-update-offer-list-complaint / lean | 2/2 | 0/2 | 4/4 | 1.4092 | 2,015,268 | 2,015,268 | 441.0 |
| b-sequence-category-branch-copy / off | 2/2 | 0/2 | 0/0 | 2.4697 | 2,596,519 | 2,596,519 | 879.5 |
| b-sequence-category-branch-copy / lean | 2/2 | 0/2 | 0/0 | 2.7006 | 3,901,713 | 3,901,713 | 973.4 |
| b-entitlement-design-save-api / off | 2/2 | 0/2 | 4/6 | 0.8932 | 1,207,678 | 1,207,678 | 409.8 |
| b-entitlement-design-save-api / lean | 2/2 | 0/2 | 4/6 | 1.1779 | 1,809,953 | 1,809,953 | 396.2 |
| b-contract-catalog-default-page / off | 2/2 | 0/2 | 0/4 | 0.9565 | 1,217,292 | 1,217,292 | 321.1 |
| b-contract-catalog-default-page / lean | 2/2 | 0/2 | 0/2 | 1.2786 | 2,113,466 | 2,113,466 | 508.9 |
| b-cross-path-custom-unit-limit / off | 2/2 | 0/2 | 2/2 | 1.1060 | 1,498,755 | 1,498,755 | 534.6 |
| b-cross-path-custom-unit-limit / lean | 2/2 | 0/2 | 6/6 | 1.2297 | 1,926,356 | 1,926,356 | 668.5 |
| cart-item-to-compare / off | 2/2 | 0/2 | 6/6 | 1.7980 | 3,359,078 | 3,359,078 | 431.8 |
| cart-item-to-compare / lean | 2/2 | 0/2 | 6/6 | 2.1422 | 4,161,106 | 4,161,106 | 480.0 |
| medicine-catalog-classification-bypass / off | 2/2 | 0/2 | 4/4 | 1.0207 | 1,622,508 | 1,622,508 | 227.9 |
| medicine-catalog-classification-bypass / lean | 2/2 | 0/2 | 4/4 | 0.7029 | 989,088 | 989,088 | 172.6 |
| rule-all-paths / off | 0/2 | 2/2 | 0/0 | 1.8694 | 3,273,362 | 미상 | 778.7 |
| rule-all-paths / lean | 0/2 | 2/2 | 0/0 | 2.3044 | 4,366,386 | 미상 | 774.3 |

토큰은 input/output/cache read/cache creation의 합계다. stock report의 `tokens_per_verified_success`는 input/output만 합산하므로 채택 판단에는 `analysis.json`의 네 항목 합계를 사용한다. 회당 비용·토큰·시간은 평균이다. 기존 20셀 시간은 정리 전, 새 셀 시간은 정리 후 wall time으로 clone·의존성 복사·세션·채점을 포함한다. 시간 차이는 이 계측 범위 차이까지 포함한다. 적용 문자열이 없는 probe는 probe 분모에서만 제외했다.

**판정: 채택 기준 미달**. 유효 셀의 검증 성공률 차이 -4.17%p(기준 +15%p), 거짓 완료 2/24 → 3/24(기준 절반 이하), 성공당 토큰 2,742,843 → 3,337,287(기준 OFF 이하). 세 조건을 모두 충족해야 채택한다.

성공 차이가 난 과제:

- `a-product-source-stale-all-paths`: OFF 2/2, lean 1/2.

첫 반복 `rule-all-paths`는 OFF·lean 모두 거짓 완료였다. OFF hidden은 초과 설명의 기존 상품 복제와 복원 차단을 놓쳤고, lean은 복제 차단을 놓쳤다(`rule-all-paths/{off,lean}/rep1/hidden0-retry.log`). lean이 복원 경로를 더 덮었어도 전체 과제 성공으로 세지 않았다. 두 세션 모두 프로젝트 전체 테스트를 추가 실행했으므로 이 과제의 비용·시간에는 자체 검증 범위가 반영됐다. 실행기 인프라 실패가 아닌 구현 결과로 유지했고 세션을 재시도하지 않았다.

`a-product-source-stale-all-paths` 두 번째 반복은 OFF 성공, lean 거짓 완료였다. lean은 복원이 상품 원문을 바꿨을 때 승인 번역 상태를 “원문 변경”으로 바꾸지 않아 hidden 2건이 실패했다(`a-product-source-stale-all-paths/lean/rep2/hidden0-retry.log`). 회귀 62건은 통과했고 의존성·포트·프로세스 오류가 없었으므로 인프라 제외하지 않았다. 이 반복의 lean 비용 $2.0623은 OFF $2.7253보다 작았지만, 그 절약을 성공 개선으로 보지 않는다.

전체 lean 비용은 OFF보다 $1.9333(+4.68%), 총 토큰은 9,740,485(+16.14%) 많았다. 추가 토큰의 9,502,116개(97.55%)는 cache read였다. OFF/lean의 output은 448,887/495,454, cache creation은 2,172,440/2,364,026이다. 비용을 개별 도구에 배분할 수는 없지만, 더 긴 문맥을 반복 소비한 흔적이 토큰 증가 대부분을 설명한다. 성공당 토큰은 2,742,843 → 3,337,287(+21.67%)로 실패 수 증가까지 반영한다.

증가가 큰 과제는 `rule-all-paths`(+ $0.8701), 장바구니(+ $0.6884), 카탈로그 기본 페이지(+ $0.6442), 권한·디자인 저장(+ $0.5694)였다(각 과제 두 반복 합계). 앵커 lean 두 번째 세션은 부분 검사 뒤 복원 테스트 fixture를 수정·재검사하고 전체 npm test/typecheck/lint까지 실행했다(`rule-all-paths/lean/rep2/session1.jsonl:306,455,466,478,498`). 분류·분기 복사 lean은 전체 검증 뒤 두 번째 세션에서 복제 검사 재실행과 typecheck/lint를 반복했다(`b-sequence-category-branch-copy/lean/rep2/session1.jsonl:329`, `session2.jsonl:206,240,264,276`). 권한 저장 lean도 부분 검사·증명·전체 검증을 실행했다(`b-entitlement-design-save-api/lean/rep2/session1.jsonl:204,234,279,317`). 장바구니 lean에는 반복 npm test, 보조 복사본과 브라우저 4종·빌드 검증이 추가됐다(`cart-item-to-compare/lean/rep2/session1.jsonl:114,122,330,365,413,477,564`). 이 과정의 환경 우회와 재검증 역시 해당 세션 비용에 남긴다.

정규식 집계의 검사 명령은 OFF 115회, lean 100회로 lean이 오히려 적고, 증명 관련 명령은 0/15회였다. 따라서 “검사 호출 수가 늘어서”라는 단일 설명은 이 결과에 맞지 않는다. 명령 하나의 검사 범위, 문맥·수정량, 도구 출력과 재검증을 함께 봐야 한다. UI 브라우저 증거와 고정 hidden 성공은 별개이며, 아래 보조 검증의 외부 의존성 사용도 구분한다.

### 실행 경계 감사에서 남은 한계

부모 실행기의 clone·복사·정리는 소유한 짧은 작업 경로 안에서 수행됐지만, `bypassPermissions` 세션 자체의 파일 접근을 OS 수준으로 가두지는 않았다. `cart-item-to-compare`의 기존 OFF rep1과 새 OFF/lean rep2가 보조 typecheck·빌드·브라우저 검증에 원본 `yeondoo-link/node_modules`를 참조했다. 기존 OFF rep1과 새 lean rep2는 Temp 보조 복사본에 원본 의존성 junction도 만들었다. 새 lean rep2는 junction을 끊은 뒤 `Remove-Item -Recurse`로 보조 폴더를 정리했다(`session1.jsonl:365,372,583,590`). 이는 사용자가 금지한 재귀 정리를 세션 내부에서 막지 못한 운영상 위반이다. 이 임시 폴더는 현재 없고 원본 의존성 폴더는 존재한다. `boundary-audit.json`에 명령과 transcript 위치를 보존했다.

원본 프로젝트의 HEAD·Git status, 설정·설치 등록 파일 해시, 레지스트리는 전후 동일했다. 그러나 원본 의존성 `.vite`와 `.vite-temp`의 최종 수정 시각은 이번 보조 검증 시간대(2026-10-25 12:18:37, 12:20:16 KST)였다. 실행 전 원본 의존성 전체 해시가 없어 바이트 무변경이나 변경 범위를 입증하지 못한다. 원본 캐시를 지우거나 되돌리지는 않았다. 따라서 “원본 checkout 전체 무변경” 또는 “세션 전체가 격리됐다”고 주장하지 않는다. 추후 실행에서는 고정 후보·프롬프트를 바꾸는 대신 세션 호스트의 원본 쓰기 금지와 전용 임시·검증 의존성 경계를 강제해야 한다. 이는 이번 실행에서 미해결인 격리 문제다.

고정 probe·회귀·hidden은 모두 각 평가 clone과 평가 의존성에서 실행됐고 해당 로그에 인프라 오류가 없었다. 보조 검증의 외부 참조는 성공을 대체하는 근거로 쓰지 않았으며, 사후에 새 제외 기준을 만들어 유리한 셀을 고르지도 않았다. 위 표는 공식 유효 48셀의 결과이고, 세션의 보조 검증·안전 준수까지 검증했다는 뜻은 아니다.

과제별 비용·도구 관측(명령 수는 비용의 직접 배분이 아님):

- `a-offer-quantity-all-paths`: off: $5.8026, cache read 10,290,160, output 60,959, Bash 88, 검사 명령 19, 증명 명령 0; `.work/delegation-eval/v2-0189-20261024-run/cells/a-offer-quantity-all-paths/off/rep1/session1.jsonl:289`, `.work/delegation-eval/v2-0189-20261025-resume2/a-offer-quantity-all-paths/off/rep2/session1.jsonl:218` / lean: $5.9445, cache read 11,460,137, output 62,807, Bash 100, 검사 명령 13, 증명 명령 1; `.work/delegation-eval/v2-0189-20261024-run/cells/a-offer-quantity-all-paths/lean/rep1/session1.jsonl:317`, `.work/delegation-eval/v2-0189-20261025-resume2/a-offer-quantity-all-paths/lean/rep2/session1.jsonl:275`.
- `a-product-source-stale-all-paths`: off: $4.7947, cache read 8,202,298, output 51,725, Bash 78, 검사 명령 13, 증명 명령 0; `.work/delegation-eval/v2-0189-20261024-run/cells/a-product-source-stale-all-paths/off/rep1/session1.jsonl:180`, `.work/delegation-eval/v2-0189-20261025-resume2/a-product-source-stale-all-paths/off/rep2/session1.jsonl:234` / lean: $3.7963, cache read 6,307,513, output 35,982, Bash 66, 검사 명령 4, 증명 명령 0; `.work/delegation-eval/v2-0189-20261024-run/cells/a-product-source-stale-all-paths/lean/rep1/session1.jsonl:194`.
- `a-product-name-whitespace-complaint`: off: $2.1962, cache read 1,789,286, output 13,893, Bash 37, 검사 명령 8, 증명 명령 0; `.work/delegation-eval/v2-0189-20261024-run/cells/a-product-name-whitespace-complaint/off/rep1/session1.jsonl:85`, `.work/delegation-eval/v2-0189-20261025-resume2/a-product-name-whitespace-complaint/off/rep2/session1.jsonl:130` / lean: $1.9635, cache read 1,393,048, output 11,175, Bash 35, 검사 명령 6, 증명 명령 0; `.work/delegation-eval/v2-0189-20261024-resume1/cells/a-product-name-whitespace-complaint/lean/rep1/session1.jsonl:110`, `.work/delegation-eval/v2-0189-20261025-resume2/a-product-name-whitespace-complaint/lean/rep2/session1.jsonl:139`.
- `a-import-offer-sequence`: off: $6.0179, cache read 6,235,249, output 59,848, Bash 103, 검사 명령 19, 증명 명령 0; `.work/delegation-eval/v2-0189-20261024-resume1/cells/a-import-offer-sequence/off/rep1/session1.jsonl:199`, `.work/delegation-eval/v2-0189-20261025-resume2/a-import-offer-sequence/off/rep2/session1.jsonl:143` / lean: $5.6871, cache read 7,241,141, output 72,334, Bash 85, 검사 명령 12, 증명 명령 0; `.work/delegation-eval/v2-0189-20261024-resume1/cells/a-import-offer-sequence/lean/rep1/session1.jsonl:187`, `.work/delegation-eval/v2-0189-20261025-resume2/a-import-offer-sequence/lean/rep2/session1.jsonl:187`.
- `a-update-offer-list-complaint`: off: $2.3104, cache read 2,968,907, output 23,356, Bash 41, 검사 명령 7, 증명 명령 0; `.work/delegation-eval/v2-0189-20261024-resume1/cells/a-update-offer-list-complaint/off/rep1/session1.jsonl:89`, `.work/delegation-eval/v2-0189-20261025-resume2/a-update-offer-list-complaint/off/rep2/session1.jsonl:99` / lean: $2.8185, cache read 3,818,445, output 29,872, Bash 43, 검사 명령 6, 증명 명령 5; `.work/delegation-eval/v2-0189-20261024-resume1/cells/a-update-offer-list-complaint/lean/rep1/session1.jsonl:195`, `.work/delegation-eval/v2-0189-20261025-resume2/a-update-offer-list-complaint/lean/rep2/session1.jsonl:177`.
- `b-sequence-category-branch-copy`: off: $4.9395, cache read 4,928,079, output 54,407, Bash 91, 검사 명령 20, 증명 명령 0; `.work/delegation-eval/v2-0189-20261024-resume1/cells/b-sequence-category-branch-copy/off/rep1/session1.jsonl:79`, `.work/delegation-eval/v2-0189-20261025-resume2/b-sequence-category-branch-copy/off/rep2/session1.jsonl:120` / lean: $5.4011, cache read 7,430,412, output 77,654, Bash 99, 검사 명령 15, 증명 명령 0; `.work/delegation-eval/v2-0189-20261024-resume1/cells/b-sequence-category-branch-copy/lean/rep1/session1.jsonl:128`, `.work/delegation-eval/v2-0189-20261025-resume2/b-sequence-category-branch-copy/lean/rep2/session1.jsonl:126`.
- `b-entitlement-design-save-api`: off: $1.7864, cache read 2,279,259, output 20,172, Bash 41, 검사 명령 1, 증명 명령 0; `.work/delegation-eval/v2-0189-20261024-resume1/cells/b-entitlement-design-save-api/off/rep1/session1.jsonl:158` / lean: $2.3557, cache read 3,448,513, output 24,607, Bash 50, 검사 명령 5, 증명 명령 1; `.work/delegation-eval/v2-0189-20261024-resume1/cells/b-entitlement-design-save-api/lean/rep1/session1.jsonl:124`, `.work/delegation-eval/v2-0189-20261025-resume2/b-entitlement-design-save-api/lean/rep2/session1.jsonl:204`.
- `b-contract-catalog-default-page`: off: $1.9129, cache read 2,287,811, output 23,461, Bash 33, 검사 명령 0, 증명 명령 0; 집계 정규식에 맞는 검사 명령 없음 / lean: $2.5571, cache read 4,052,818, output 29,510, Bash 55, 검사 명령 9, 증명 명령 0; `.work/delegation-eval/v2-0189-20261024-resume1/cells/b-contract-catalog-default-page/lean/rep1/session1.jsonl:158`.
- `b-cross-path-custom-unit-limit`: off: $2.2120, cache read 2,829,342, output 25,096, Bash 43, 검사 명령 8, 증명 명령 0; `.work/delegation-eval/v2-0189-20261024-resume1/cells/b-cross-path-custom-unit-limit/off/rep1/session1.jsonl:123`, `.work/delegation-eval/v2-0189-20261025-resume2/b-cross-path-custom-unit-limit/off/rep2/session1.jsonl:129` / lean: $2.4593, cache read 3,682,313, output 30,010, Bash 53, 검사 명령 9, 증명 명령 8; `.work/delegation-eval/v2-0189-20261024-resume1/cells/b-cross-path-custom-unit-limit/lean/rep1/session1.jsonl:133`, `.work/delegation-eval/v2-0189-20261025-resume2/b-cross-path-custom-unit-limit/lean/rep2/session1.jsonl:150`.
- `cart-item-to-compare`: off: $3.5960, cache read 6,499,088, output 45,363, Bash 73, 검사 명령 6, 증명 명령 0; `.work/delegation-eval/v2-0189-20261024-resume1/cells/cart-item-to-compare/off/rep1/session1.jsonl:236`, `.work/delegation-eval/v2-0189-20261025-resume2/cart-item-to-compare/off/rep2/session1.jsonl:277` / lean: $4.2845, cache read 8,064,926, output 51,160, Bash 80, 검사 명령 4, 증명 명령 0; `.work/delegation-eval/v2-0189-20261024-resume1/cells/cart-item-to-compare/lean/rep1/session1.jsonl:248`, `.work/delegation-eval/v2-0189-20261025-resume2/cart-item-to-compare/lean/rep2/session1.jsonl:114`.
- `medicine-catalog-classification-bypass`: off: $2.0414, cache read 3,105,643, output 25,478, Bash 46, 검사 명령 5, 증명 명령 0; `.work/delegation-eval/v2-0189-20261025-resume2/medicine-catalog-classification-bypass/off/rep1/session1.jsonl:75`, `.work/delegation-eval/v2-0189-20261025-resume2/medicine-catalog-classification-bypass/off/rep2/session1.jsonl:81` / lean: $1.4057, cache read 1,873,144, output 15,929, Bash 35, 검사 명령 5, 증명 명령 0; `.work/delegation-eval/v2-0189-20261025-resume2/medicine-catalog-classification-bypass/lean/rep1/session1.jsonl:53`, `.work/delegation-eval/v2-0189-20261025-resume2/medicine-catalog-classification-bypass/lean/rep2/session1.jsonl:73`.
- `rule-all-paths`: off: $3.7388, cache read 6,304,607, output 45,129, Bash 74, 검사 명령 9, 증명 명령 0; `.work/delegation-eval/v2-0189-20261025-resume2/rule-all-paths/off/rep1/session1.jsonl:148`, `.work/delegation-eval/v2-0189-20261025-resume2/rule-all-paths/off/rep2/session1.jsonl:150` / lean: $4.6088, cache read 8,449,435, output 54,414, Bash 89, 검사 명령 12, 증명 명령 0; `.work/delegation-eval/v2-0189-20261025-resume2/rule-all-paths/lean/rep1/session1.jsonl:220`, `.work/delegation-eval/v2-0189-20261025-resume2/rule-all-paths/lean/rep2/session1.jsonl:306`.

### 제외·복구·미해결 오류

복구한 오류는 긴 결과 경로와 clone 작업 경로를 결합했던 실행기 설계다. 실제 고정 ref 무료 대조 시험과 경로 예산·자동 루트 전환·세션 미시작·결과 매핑·정리 범위·고정 ref clone·중단 재개·셀 예외 후 계속 실행 회귀 테스트로 검증했다. 기존 코드에 현재 31개 테스트를 적용한 RED는 25개 실패, 수정 후 실행기 테스트 31개와 문서 검사 14개가 통과했다. 과거 sandbox CIM/cp949 검사 실패는 프로세스 조회가 가능한 실행과 프로세스 한정 UTF-8로 해결했으며 테스트를 생략하거나 약화하지 않았다.

| 제외 시도 | 단계 / 원인 | 세션 / 비용 | 증거 |
| --- | --- | --- | --- |
| medicine OFF rep1 최초 | clone checkout / Filename too long (276자), exit 128 | 미시작 / 0달러 (원본 cost는 null) | `resume1/cells/medicine-catalog-classification-bypass/off/rep1/classified.json` |
| medicine OFF rep1 재시도 | 같은 clone 경로 오류 반복, exit 128 | 미시작 / 0달러 (원본 cost는 null) | `resume1/retry1/medicine-catalog-classification-bypass/off/rep1/classified.json` |

위 경로의 `resume1`은 `.work/delegation-eval/v2-0189-20261024-resume1/`이다. 두 시도는 비용·이력에 보존했고 근본 수정 뒤 같은 셀을 새 경로에서 정상 실행했다. 새 28셀의 인프라 제외·유료 재시도는 없었다. 마지막 두 앵커 셀도 첫 반복과 같이 OFF는 복제·복원, lean은 복제 hidden이 실패했으며 구현 실패로 유지했다.

미해결 인프라 오류는 없다. 미해결 운영 문제는 위 경계 감사의 세션 외부 의존성 접근·재귀 정리 차단 부재와 원본 의존성 바이트 보존 미검증이다. 실행기의 파일 정리 범위 검사만으로 세션 전체의 접근 경계를 보장하지 못한다.

### 표본과 증거의 한계

과제당 조건별 2회, 같은 제품·실패 유형의 12과제이므로 일반적인 위임 성공률이나 통계적 우월성을 확정하지 못한다. 경로를 직접 나열하는 프롬프트와 v1 앵커가 포함된다. 긴/짧은 작업 경로 구간의 차이도 있다. 동일한 제품·의존성에서 실행했지만 실행 순서와 호스트 부하가 시간에 영향을 줄 수 있다.

실행 전 SHA256 302개 중 43개가 불일치했다. 41개는 CRLF→LF로 일치하고, 나머지는 과거 authoring 증거 `evidence/a-offer-quantity-all-paths/c-reference-product.ts`, `d-reference-backup.ts`로 Git blob도 manifest와 다르다. 이미 이를 보고한 뒤 사용자가 실행을 지시했다. 재개 전에도 대조만 했으며 파일을 고치지 않았다. 전체 세트의 byte-exact freeze 검증 통과로 주장하지 않는다.

고정 probe 명령은 지정된 기존 테스트 파일만 실행하므로 후보가 새 파일에 쓴 검사를 누락할 수 있다. 최초 가격 옵션 lean은 `tests/offerRules.test.ts`에 quantity=1000 사례를 썼지만(최초 raw `lean/rep1/session1.jsonl:297`) 해당 probe는 그 파일을 실행하지 않는다. 공식 probe 미검출을 보호 테스트 부재로 해석하지 않는다. 관측 후 명령·점수를 보정하지 않았고 추가 테스트의 mutant 검출도 별도로 실행하지 않았다. 도구 집계의 검사 명령은 vitest/npm/playwright 정규식에 맞는 호출이며 Node 직접 실행 등은 누락될 수 있어 실제 transcript와 함께 해석한다.

Raw: `.work/delegation-eval/v2-0189-20261024-run/`(최초 5셀), `.work/delegation-eval/v2-0189-20261024-resume1/`(기존 누적 20셀·무료 실패 2회), `.work/delegation-eval/v2-0189-20261025-resume2/`(새 셀과 통합 `state.json`, `report.json`, `report.md`, `analysis.json`). 무료 대조·설정 보존·freeze 대조 증거는 `.work/delegation-eval/v2-0189-20261025-shortpath-control/`다. 과거 출력은 덮어쓰거나 지우지 않았다.

Feature는 `agent-workflow` 평가 실행 경로이며 Feature Map과 testing 문서를 갱신했다. 평가 대상 Skill은 변경하지 않았다. 설치본·전역 설정·레지스트리 변경과 push는 하지 않았다. 원본 프로젝트의 Git 상태는 같지만, 위 경계 감사의 원본 의존성 접근·캐시 한계는 남는다. 최종 보존 범위와 잔여물 확인은 resume2의 `preservation.json`에 기록한다.
