> Historical record through 0.1.68; not current execution instructions. See [current design](../agent-coding-system-direction.md) and [current work](../plugin-continuous-improvement-next-session.md). Original bytes: Git ea7e11d.

# 0.1.46 이후 위임 신뢰성 검토와 개선 순서

<a id="post-0146-review"></a>

현재 후속 상태: 아래 D1–D3는 0.1.46에서 재현한 역사적 반례다. 0.1.47의
실제 수정·CLI/패키지 소비·검증과 남은 한계는
[후속 구현 결과](../agent-workflow-implementation-results.md#d1d3-consumption-2026-10-09)가 소유한다.

2026-10-09, clean local main `ef25cf2cf0795f3af69aafb2a03fe0f95c24c550`, 패키지 0.1.46을 기준으로 검토했다. [현재 설계](agent-coding-system-direction-through-0.1.68.md), canonical runtime/호출자/기존 회귀, [실제 구현 결과](../agent-workflow-implementation-results.md#post-review-reliability-2026-10-09), [고정 pstack 조사](../pstack-analysis.md)를 대조했다. 두 독립 검토는 읽기 전용이었고, 핵심 발견은 주 Agent가 코드와 실제 CLI/hook으로 확인했다.

**방향은 유지하되, 현재 구현의 남은 상태 전이와 조회 범위 오류를 먼저 고친다.** 이미 완료한 R0–R4와 원래 A–C를 다시 만들지 않는다. 이 변경은 설계 보완이며 아래 새 runtime 결함의 구현은 아니다. 직전 0.1.45 검토 전문은 Git `ef25cf2:docs/research/agent-workflow-refinement-review.md`에 보존된다.

## 요구별 판단

| 요구 | 적절한 현재 설계·재사용할 기능 | 구체적으로 보완할 점 |
| --- | --- | --- |
| 많은 업무 위임과 검증 조회 | task/context, prepare/execute/lookup, raw/viewer와 stale 판단 | 현재 task와 프로젝트 전체 공백을 분리. 여러 ordinary task 비교와 raw 상세 발견 경로를 기존 조회 위에 추가 |
| 비즈니스·아키텍처 × FE·BE/API·Domain | 6셀은 적용 범위 지도, E2E는 셀을 연결하는 검증 방법 | 요구→기대/관찰→실제 assertion/검토 근거를 제시. API-only FE는 이유 있는 N/A 허용 |
| 피드백·자가 개선 | 원인 owner, 실제 실패/정상 검증, 활성 prevention, 후속 task 승계 | 분류 왕복으로 승인 근거가 살아나지 않게 하고 적용 기준 집합 변경도 재검토 |
| UI/UX guide 유지 | 의도·용어·계층·상태·반응형·접근성은 guide, 값·공통 동작은 코드 소유 | CONNECTED와 시각·사용성 판정 구분. 신규 소비 화면에서 variant 유지와 실제 guide/공유 owner 선택을 확인 |
| 검증 guide 유지 | argv/cwd·fixture/runtime·assertion·raw producer·정리를 기존 경로에 연결 | runner 실패/skip/잘못된 대상과 제품 실패 구분. 새 context가 유효한 명령·근거를 찾는지 인수 |
| 실질적 가드레일과 검사 정리 | 원인별 코드/type/constraint/shared owner 예방, 중복 통합, 규칙-only 폐기 | 중복·요구 폐기·책임 이동·불안정 환경을 구분. 고유 검출·정상 허용·우회 경로의 근거 없는 삭제 보류 |

사용자 가치·전환·수익 같은 사업 가설은 운영/사용자 관찰이 필요하다. 가격·권한·전이 같은 코드 업무 규칙 PASS로 사업 성과를 입증하지 않는다. 아키텍처는 실제 호출자, 계약, 상태·부작용 owner, 의존 방향, 실패/rollback 경로를 검토한다. 구조 설명의 존재는 적절한 구조의 증명이 아니다.

## 현재 버전에서 재현한 세 가지 공백

### D1. 분류를 왕복하면 철회된 승인이 살아난다 — 우선 수리

격리 fixture에서 명시적 예외 승인 후 같은 승인 파일을 철회 내용으로 바꿨다. 실제 CLI 순서는 `ACCEPTED → OPEN → kind=unknown의 OPEN → kind=intentional_difference의 ACCEPTED`였다. 새 `user_review`는 없었고 ID·내용도 같았다. 새 관련 task도 ACCEPTED를 승계했다. whole-product는 PARTIAL이므로 제품 전체 false PASS로 표현하지 않는다.

원인은 [record_feedback](../../../authoring/scripts/project_workflow.py)의 intentional_difference 분기 밖에서 `decision_hashes`를 재캡처하면서 이전 `decision_binding`을 보존하는 것이다. 돌아온 분류와 옛 binding의 subject가 다시 일치해 최신 철회 파일 hash를 유효한 승인 근거로 사용한다. 기존 메타데이터/same-review 회귀는 단일 분류 안의 갱신을 검증했다.

최소 개선: 기존 레코드에서 승인 결정의 근거와 분류별 확인 근거를 구분해 보존한다. 분류 전이는 현재 예외 효력을 해제하되 과거 승인 이력/원본 hash를 재작성하지 않는다. 예외로 돌아갈 때 새 연결된 결정이 없으면 OPEN을 유지한다. 정상 재분류 자체를 금지하거나 별도 승인 DB를 만들지 않는다.

인수: 다른 허용 분류 경유에서도 철회 상태 유지, 새 명시적 승인만 재결합, 정상 재분류·ID/이력 유지, 조회와 다음 task의 동일 판단. 기존 requirement_change/oracle 확인 경로도 회귀 범위에 포함한다.

### D2. 새로 추가된 관련 기준을 기존 예외가 무시한다 — 우선 수리

독립 fixture에서 기존 기준·승인 파일은 그대로 두고 같은 Feature의 `criteria`에 “terminal-price 예외를 금지한다”는 새 파일을 추가했다. lookup과 다음 task에서 기존 feedback은 ACCEPTED였다. 다른 Feature의 무관한 기준 변경과 구분되는 반례다. 전체 제품은 PARTIAL이었다.

[difference_review_matches / inspect_feedback](../../../authoring/scripts/project_workflow.py)는 승인 당시 선택한 `criteria_refs`의 현재 집합 포함 여부와 선택 파일 hash를 검사한다. 선택 집합 밖의 새 관련 요구 추가는 결정 효력 검토에 연결되지 않는다. 기존 A3의 “연결된 파일 내용 변경” 방어는 유효하며 이번 반례와 다르다.

최소 개선: 결정이 검토한 Feature/범위의 **적용 기준 집합**도 기존 binding에 연결한다. 추가·제거·재연결로 관련성 판단이 미완료면 재검토로 둔다. 같은 Feature의 새 기준은 보수적으로 검토하고 무관한 Feature 변경은 승인을 무효화하지 않는다. 더 세밀한 제외는 이유와 검토 revision이 있을 때만 허용한다. CLI 자연어 판정이나 전체 Git/bundle stale 보호 축소는 도입하지 않는다.

인수: 기존 파일 내용 변경 및 새 관련 기준 추가·연결 변경 후 OPEN, 근거 있는 무관한 변경의 승인 유지, 새로운 유효 결정 후 재사용. 구형 레코드에 집합 연결이 없으면 추정 승인/조회 migration을 하지 않는다.

### D3. hook의 현재 task 공백에 범위 밖 Feature가 포함된다 — 조회 신뢰성 수리

실제 CLI에서 API만 대상으로 task를 시작했다. exact lookup은 API 활성 6셀과 CLI의 `in_task=false` 6셀을 구분했지만 실제 hook의 `current_task.scope.gap_count`는 12였다. 미리보기는 앞 6개만 보여 집계 범위가 더 모호해졌다. 조회 전후 파일 hash는 같고 실행은 0회였다.

[scope_context](../../../authoring/scripts/workflow_context.py)는 `in_task`를 확인하지 않고 전체 matrix를 합산한다. 반면 [coverage_summary](../../../authoring/scripts/project_workflow.py)는 active 셀로 task 상태를 판정한다. 상태와 공백 개수의 분모가 다르다.

최소 개선: task의 active gap과 프로젝트 전체 gap을 구분하고 exact audit의 전체 matrix는 유지한다. 인수는 두 Feature 중 하나만 선택했을 때 task=6/project=12, 범위 확대·무관한 Feature 미확인 보존, bounded hook·정확한 task·읽기 전용이다. 새 상태 파일이나 dashboard는 필요 없다.

## 다음에 투자할 개선과 확인 방법

### 검증 요약을 실제 판단까지 연결한다

[task_candidates](../../../authoring/scripts/project_workflow.py)는 ordinary task의 ID·의도·대상·요청을 발견하지만 검증 상태를 합산하지 않는다. [summarize_results](../../../authoring/scripts/verification_results.py)는 전체 검증 후 표시량을 줄이기 위해 raw observations를 생략한다. 둘 다 자동으로 제품 결함이라는 뜻은 아니다. 다만 이전 fresh reader는 descriptor에서 raw로 이동하지 않고 “runtime 근거 없음”으로 오해했다. 오류와 원시 근거 정정은 [구현 결과](../agent-workflow-implementation-results.md#post-review-reliability-2026-10-09)에 남아 있다.

기존 조회에 **선택한 task → Feature/6셀 → 주장과 실제 관찰 → raw 위치 → 현재 유효성/미확인/다음 행동**을 짧게 연결한다. 상세 생략과 실제 근거 누락을 구별하고, 여러 task 비교는 명시적 선택·제한된 묶음으로 시작한다. 모든 프롬프트에서 모든 bundle을 재검사하거나 새 장부를 먼저 만들지 않는다.

인수: 결과 보유·미실행·stale task가 섞여도 새 문맥이 실행 없이 구분하고 raw를 찾아 설명한다. 같은 base의 독립 task 둘 중 공유 owner가 바뀌는 최소 사례로 낡은 근거 차단과 필요한 재검증을 확인한다. 같은 task 동시 쓰기는 전제하지 않는다.

### UI·검증 guide의 효과는 다음 소비 작업으로 평가한다

[inspect_ui_systems](../../../authoring/scripts/project_workflow.py)는 guide/token/component 존재와 소비자 연결을 확인한다. 시각 의미를 판정하지 않는 것은 올바른 책임 경계다. 기존 T5의 공유 UI 수리와 새 context 재사용은 재사용할 근거이며 다시 미구현으로 분류하지 않는다.

다음 개선은 알려진 불편이나 새로운 소비 상태가 있을 때 한정한다. 예를 들어 저장 오류 상태가 공통 component에서 누락되면 공유 owner를 수리하고 guide에 복구 의도·사용법을 연결한 뒤 새로운 화면 요청의 재사용을 본다. 정상/destructive variant, keyboard, 관련 viewport와 요청한 persistence 경로를 확인한다. 실제 값의 문서 복사, screenshot 개수, 모든 화면 전수 검사를 목표로 삼지 않는다.

검증 guide도 기존 명령/adapter의 깨진 전제조건·report·producer 연결을 고친 뒤, 새 문맥이 argv/cwd·fixture/runtime·assertion·raw·정리를 따라 실패와 정상 사례를 관찰하는지 본다. runner 오류를 제품 수리로 연결하거나 exit 0을 위해 정답을 바꾸면 실패다. 최초 setup은 합의한 전체 조사 범위를 완성하고 이후 매 변경에는 관련 범위만 갱신한다.

### 검사 정리는 실패 유형별로 한 건씩 진행한다

| 정리 사유 | 필요한 근거 | 잘못된 삭제 근거 |
| --- | --- | --- |
| 중복 통합 | 남기는 검사에서 같은 결함 검출·정상 허용, 활성 selector | 이름·failure 문자열·coverage 중복만 같음 |
| 요구 폐기 | 변경 권한·기준·source·과거 실패 범위, 유지 API/소비자, 새 동작·남은 계약 | 가짜 삭제 목록 또는 폐기 규칙의 replacement test 강제 |
| type/constraint 책임 이동 | 실제 금지 경계·우회 입력·정상 허용, 기존 compile/contract 소비 | type 선언이 외부 runtime 입력까지 막는다는 추정 |
| flaky/환경 문제 | 원시 실패·조건, 관찰 수단 수리, 미검증 범위·복구 조건 | skip·재시도 PASS로 고유 검출 공백을 숨김 |

기존 detector 통합과 rule-only quote 사례를 유지한다. option/label/class 검사도 소비 계약을 지킬 수 있으므로 외형만 보고 삭제하지 않는다. 실행·유지 비용이 문제가 된 한 검사의 실제 검출 차이를 확인한다. 일반 mutation framework, 자동 삭제 점수, 고정 테스트 수는 필요 없다.

## 순서·완료 조건과 이번 변경 범위

1. D1·D2는 결정 소유 경계, D3는 요약 소비 경계에서 수리한다. 각각 새 focused RED → GREEN과 정상 반례를 인수하고 원래 A–C는 기존 회귀로 재사용한다.
2. 작은 조회 개선을 새 문맥에서 평가한다. 기존 필드가 충분하면 새 명령 대신 출력·안내를 보완한다.
3. 관측된 guide 소비 실패나 검사 중복 한 건으로 지속 개선 효과를 평가한다. 근거 없는 전수 정리·재설계는 하지 않는다.

거짓 완료·놓친 결함·정상 과업 오탐·개입·재작업·중복 실행·시간을 같은 조건에서 기록하고 미측정 수치를 추정하지 않는다. 정답 패치·Skill 이름·CLI 순서를 미리 주는 평가는 자율 발견을 입증하지 못한다. Agent 합의도 주 Agent의 raw 확인을 대신하지 않는다.

이번에는 격리 fixture의 CLI/hook과 기존 코드/근거를 확인했다. `.work/design-review-0146-20261009/`에 재실행 가능한 probe source와 JSON을 보존한다. fixture 임시 경로는 종료 후 제거됐으며 현재 제품 경로로 표현하지 않는다. 임시 자료가 없어도 재현할 수 있는 조건은 D1–D3 본문과 기존 refinement fixture에 있다.

source/배포 리소스·버전·기존 설치본·원본 연두라벨은 변경하지 않는다. 변경 Feature는 `documentation`; `feedback-repair`와 `workflow-obligations` 지도에는 확인된 제한만 명시한다. 이번 문서 검증은 repository docs와 diff 검사이며 Full/브라우저/제품 성능 검증이 아니다. Native host 발견/보호 수락, 장기 다중 writer, 일반 Agent 품질·비용 개선은 이번 확인 범위 밖이다.

pstack은 `23e4138daa01c42d4969f7a5465f82704e64f798`의 고정 분석으로 사용했다. 실제 실행 경로, 고정 평가 기준, 원인 owner 예방, 최종 revision 근거는 채택한다. 고정 10개 검증·상시 다중 Agent·모든 변경의 성능 검사·일률적 주석 삭제·patch-id만의 재사용은 채택하지 않는다. 최신 외부 상태나 동일 과업 우월성을 이번에 조사하지 않았다.
