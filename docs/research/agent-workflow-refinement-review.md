# 0.1.45 이후 위임 신뢰성 검토와 보완 우선순위

2026-10-09 재검토. 기준은 clean main `f8db21ebf14d276a3e6d78a891b67786b9dd7836`와 패키지 0.1.45다. [현재 설계](agent-coding-system-direction.md), [구현 결과](agent-workflow-implementation-results.md), canonical 코드·호출자·기존 회귀와 [고정 pstack 조사](pstack-analysis.md)를 대조했다. 이전 0.1.44 검토는 Git `f8db21e:docs/research/agent-workflow-refinement-review.md`에 보존돼 있다. R0–R4는 수행된 범위이며 다시 실행할 미완료 목록이 아니다.

**방향은 유지한다. 다음 개선은 더 많은 Skill·검사·상태 파일을 만드는 것보다, 결정의 유효성·미확인 표시·정당한 검사 폐기와 실제 후속 소비를 정확하게 만드는 데 우선한다.** 이번 변경은 설계 보완이다. 아래 재현된 코드 문제는 아직 수리하지 않았으며, 기존 387개 Full 통과가 이 추가 사례의 통과를 뜻하지 않는다.

## 사용자 요구별 판단

| 요구 | 현재 토대와 판단 | 더 필요한 개선 |
| --- | --- | --- |
| 무엇을 검증했는지 확인 | Feature/check, 6셀 scope, 실제 capture/raw, 원래 판정과 현재 재사용, lookup/resume가 있다 | 요약에서도 요청 범위·관찰 방식·미확인을 보존한다. source 조사 완료와 runtime 완료가 섞이지 않게 한다 |
| business/architecture × FE/BE/API/Domain | 두 관점과 세 책임 영역의 6셀은 적절하다. E2E는 셀 사이 연결 증명이며 별도 일곱 번째 셀이 아니다 | business는 사용자 결과·업무 규칙, architecture는 계약·의존·상태/실패 owner로 검증한다. 사업 성과 가설은 사용자/운영 관찰의 별도 주장이다 |
| 사용자 불편·자가 개선 | feedback 종류, 원인 owner, RED/GREEN·정상 사례, 예방과 후속 task 승계가 있다 | 사용자 결정의 대상·기준 revision과 실제 후속 적용을 더 엄격하게 연결한다. 설명 변경으로 철회된 결정을 되살리지 않는다 |
| UI/UX 기준 생성·지속 개선 | ui_systems가 guide·token·component·consumer·예외를 연결한다. 실제 공유 UI/후속 요청 시험도 있다 | 같은 의미/상태의 일관성과 의도된 variant를 구분하고, 기준 변경 시 예외를 재검토한다. 값의 원본은 코드에 둔다 |
| 검증 guide 고도화 | 프로젝트가 명령·adapter·fixture·Launch/Doctor/Drive/Evidence/Cleanup을 소유한다 | 관찰 실패를 제품 결함으로 오인하지 않는 사례, 의미가 유지되는 실제 명령 교체, 새 context 소비를 인수한다 |
| 실질적 가드레일·검사 정리 | 실제 위반 수리, detector 통합과 일부 요구 폐기 경로가 있다 | 규칙만 폐기하고 API/호출자는 유지하는 정상 경우를 허용한다. 고유 방어·정상 허용·우회 경로는 계속 확인한다 |

가정한 규모는 한 프로젝트에 여러 독립 task를 위임하고 공통 source/설정의 작성자를 조정하는 운영이다. 같은 task의 동시 다중 writer, 대규모 무인 운영, native host 강제 수락까지 입증한 것으로 확대하지 않는다.

## 재현된 문제와 가장 작은 보완

### 1. 철회된 동의가 설명 수정만으로 다시 유효해진다 — 우선 수정

[record_feedback](../../authoring/scripts/project_workflow.py)의 기존 항목 merge가 보존된 `user_review`를 그대로 가져오면서 `decision_hashes`를 현재 파일로 다시 만든다. 실제 격리 사례에서 `intentional_difference` 동의는 ACCEPTED였고 동의 파일을 철회 내용으로 바꾸자 OPEN이 됐다. 이어 새 user_review 없이 `reason`만 수정했는데 ACCEPTED로 복귀했다.

최소 보완은 기존 task 안에서 결정 내용과 근거 revision을 고정하고, 설명·원인·owner 메모 갱신은 기존 결정의 hash를 유지하는 것이다. 새 사용자 결정이 들어온 경우에만 그 대상·근거 revision을 명시적으로 갱신한다. 별도 승인 DB나 자연어 권한 판독기를 만들지 않는다. 근거가 달라진 이전 결정은 새 동의로 간주하지 않는다.

인수: 동의 철회 → OPEN → 설명/owner 갱신 후에도 OPEN; 새로 연결된 유효한 결정으로만 해소. 단순 조회는 파일과 판정을 갱신하지 않는다.

### 2. 동의의 대상과 기준 revision이 충분히 묶이지 않는다 — 우선 수정

두 사례를 확인했다. `kind=intentional_difference`에 일반 `decision=agree`를 주면, 참조 문서가 “이 차이는 버그이고 고쳐야 한다”여도 ACCEPTED다. CLI가 문장의 의미를 판단하지 않는 것은 의도된 경계이지만, `agree`만으로는 **문제 존재에 동의**했는지 **차이를 유지하는 처분에 동의**했는지 구별되지 않는다.

또한 별도 동의 파일·owner가 그대로인 상태에서 Feature의 `criteria`를 “예외 금지”로 바꿔도 feedback은 ACCEPTED이고 다음 task에도 그대로 승계됐다. 전체 Feature 판정은 PARTIAL이므로 이를 제품 전체의 거짓 PASS로 확대하지 않는다. 문제는 feedback 자체가 현재 유효한 예외처럼 표시된다는 것이다. `criteria_before`는 저장하지만 이 분기에서는 기준 변경 판단에 쓰이지 않는다.

최소 보완은 후보/주장 ID, 동의한 처분, 적용 범위, 요구·UI 기준 revision을 기존 feedback 결정에 결합하는 것이다. 일반적인 문제 동의는 예외 승인으로 해석하지 않는다. 결정의 의미에 필요한 참조가 바뀌면 재검토 상태로 돌린다. 영향 없는 결정은 유지하며 같은 동의를 매 작업마다 다시 요구하지 않는다. 구형 기록은 확인 가능한 결합만 재사용하고 빠진 권한/기준을 추정하지 않는다.

인수: 문제 동의와 variant 승인을 구분; 관련 기준 변경 후 재검토; 기준과 결정이 그대로인 다음 관련 task에서는 유효 결정 재사용. 형식·hash 검증이 실제 사용자 신원/권한 인증은 아니라는 host 경계는 유지한다.

### 3. 업무 규칙만 폐기하는 정상 변경이 막힌다 — 검사 정리 전에 수정

[inspect_check_retirements](../../authoring/scripts/project_workflow.py)의 `requirement_retired` 분기는 `removed_entrypoints`와 `removed_callers`를 모두 비어 있지 않게 요구한다. 하지만 상한 규칙을 폐기하면서 같은 `quote(amount)`와 소비자를 유지하는 변경은 정상이다. 격리 실행에서 상한 제거 후 12와 0을 그대로 반환했고, 변경 권한·기준·source·실패 범위·남은 영향 근거가 있어도 두 제거 목록이 비었다는 이유만으로 BLOCKED였다.

최소 보완은 **요구 폐기와 진입점 폐기를 구분**하는 것이다. 제거/변경/유지되는 진입점·호출자를 사실대로 설명하고 적용되지 않는 제거 목록에는 이유를 허용한다. 대신 남은 요구와 소비자 영향, 폐기된 실패 범위, 활성 연결 정리, 실제 새 동작과 정상 계약을 확인한다. 빈 목록을 무조건 허용하거나 삭제된 것처럼 꾸미게 해서는 안 된다.

인수: endpoint 전체 폐기와 endpoint 유지·규칙 폐기 모두 정당하게 처리; 권한/기준/남은 소비자 근거가 없거나 활성 coverage가 남으면 계속 BLOCKED; 다른 실패를 잡는 검사는 유지. 존재하지 않는 대체 detector는 만들지 않는다.

### 4. 소스 조사와 runtime 미확인이 요약에서 구별되지 않는다 — 조회 가시성 보완

[inspect_investigation](../../authoring/scripts/project_workflow.py)과 [investigation_context](../../authoring/scripts/workflow_context.py)를 실제 호출했다. source-only 항목을 observed로 기록하고 부가 `unverified`에 runtime 미확인을 남기면 원문에는 보존되지만 요약은 READY_FOR_REVIEW / unobserved_count=0이다. 0.1.45 자연어 조사도 source-only 완료와 항목별 runtime 미확인을 사용했다.

이는 source 조사가 완료됐다는 판정 자체의 오류가 아니다. 부가 필드가 정식 미확인 집계와 연결되지 않아 짧은 context에서 관찰 범위를 오해할 여지가 있다. 최소 보완은 관찰 방식과 요청 범위를 기존 조사/요약 계약에 명시하는 것이다. 요청에 포함된 미관찰 runtime은 안정적인 별도 항목으로 남기고, 요청 밖 runtime은 미실행/범위 밖임을 표시한다. source 조사만 요청했을 때 브라우저 실행을 강제하거나 작업을 미완료로 만들지 않는다.

인수: 전체 원문·CLI 요약·hook에서 같은 분모와 필요한 미확인을 확인; source-only 완료는 허용하되 runtime 확인으로 표시되지 않음; 기존 observed/unobserved·stale·읽기 전용 재개 반례 유지.

## 기능별 구체적인 개선 방법

**Full-stack 검증:** 하나의 핵심 사용자 흐름에 요구 출처와 실제 expected/observed를 연결한다. FE 입력/실패 상태, BE 권한·transaction·실패 후 데이터, Domain 계산/전이/불변조건을 각각 본다. 공유 상태 owner·의존 방향·외부 경계는 실제 caller와 코드 근거로 검토하고, 결정적으로 검사 가능한 계약·금지 의존·중복 호출은 기존 test/lint에 둔다. 구조 설명의 존재만으로 architecture PASS를 만들지 않는다. 저장 흐름은 입력→API→Domain→저장→fresh read의 ID/값을 대조한다. API-only의 FE 비적용을 정상 허용한다.

**사용자 피드백과 가드레일:** 증상, 기대 출처, 실제 관찰, 원인 가설, 확인된 owner를 구분한다. 제품 위반은 원래 기준 RED/GREEN·가까운 정상 사례, 요구 변경은 새 기준과 유지 계약, tool 오류는 독립 근거와 수정한 관찰 수단으로 확인한다. 가드레일은 validation/type/transaction/constraint/단일 owner/shared component 중 원인을 막는 가장 작은 위치에 둔다. 다음 관련 요청이 실제 예방을 소비하는지 확인한다. 재발 불가의 범위는 확인한 실패 유형·호출 경로·조건에 한정한다.

**UI/UX guide:** 현재 화면을 그대로 표준으로 추출하지 않는다. 작업 목적·용어·정보 위계·component 상태·반응형·접근성·variant/예외를 필요한 수준으로 정하고 코드 참조를 연결한다. 공유 component 두 소비 화면에서 정상/오류·keyboard·관련 viewport를 실제 확인한다. 이후 새 context의 세 번째 화면 작업이 guide와 공유 owner를 재사용하는지 확인하되 이전 패치를 답안으로 주지 않는다. 의미가 다른 destructive action과 일반 action을 같은 스타일로 강제하지 않는다. screenshot 차이는 검토 후보이며 사용자 가치나 결함의 자동 판정이 아니다.

**검증 guide:** 현행 명령/cwd·요구/assertion·fixture/runtime·raw producer·정리 방법을 한 경로로 연결한다. runner가 깨진 경우 원래 실패를 보존하고 관찰 수단을 수리한 뒤 실제 기능을 다시 확인한다. 명령을 바꿔 exit 0만 얻는 것으로 끝내지 않는다. 필요한 프로젝트 adapter 한 개를 연결하며 범용 parser나 doctor부터 만들지 않는다. 실행 전에 필요한 map/기준 수정을 마쳐 같은 동작의 불필요한 재측정을 줄인다.

**많은 task 위임:** 기존 task/context·scope·results를 재사용하고, 선택한 task들의 완료/미확인/차단·근거·다음 행동을 읽기 전용 요약으로 보여주는 것을 우선한다. 공통 코드/설정은 한 owner가 통합한다. 독립 task 두 개가 같은 기반에서 시작한 뒤 공유 owner가 바뀌는 작은 병합 사례로 낡은 결과의 재사용 차단과 필요한 재검증을 확인한다. 같은 기록 다중 writer나 새 orchestration DB는 실제 수요·충돌 인수가 생길 때 별도 판단한다.

**불필요한 검증 제거:** 각 검사가 막는 실패·정상 허용·고유 검출을 기존 prevention/maintenance에 연결한다. 중복 통합, 요구 폐기, 구조적 예방 이동, flaky 도구 수리를 서로 다른 이유로 다룬다. 알려진 실패 하나를 넣었을 때 실제로 검출하는지 필요에 따라 확인하고 비용은 실측한다. 전체 mutation framework·검사 점수·고정 검사 수·상시 Full은 도입하지 않는다. 높은 위험의 고유 방어는 드물게 실패한다는 이유로 삭제하지 않는다.

## 작은 구현 순서와 채택 기준

| 순서 | 기존 소유 위치 | 완료해야 할 실제 반례 |
| --- | --- | --- |
| 먼저 | `record_feedback` / `inspect_feedback` / repair 계약 / 관련 회귀 | 철회된 결정의 metadata 재승인 방지, 문제 동의와 예외 승인 구분, 기준 변경 뒤 유효성 재검토와 정상 승계 |
| 다음 | `inspect_check_retirements` / maintenance 계약 / 관련 회귀 | API 유지·규칙만 폐기하는 정상 허용과 근거 부족·잔존 보호의 차단 |
| 함께 영향 확인 | investigation/context/viewer의 기존 요약 | source 완료·요청 내 미관찰·요청 밖 미실행을 원문과 동일하게 표시, 조회 실행 0회 |
| 그 후 작은 인수 | 기존 독립 프로젝트·실제 runner·패키지 | 요구/피드백→공유 owner 수리→UI/검증 guide 갱신→다른 context의 관련 요청→낡은 근거 차단 및 정상 재사용 |

변경한 결정적 분기의 focused RED/GREEN과 기존 영향 회귀를 우선한다. 자연어 인수는 관련 동작이 바뀐 최종 후보에 수행한다. 거짓 완료·놓친 결함·정상 작업 오탐·개입·재작업·중복 실행·시간을 같은 조건에서 비교하되, 사용량/비용이 없으면 미측정으로 둔다. 이번의 코드 재현 수나 과거 387개 테스트를 일반 위임 신뢰도 점수로 바꾸지 않는다.

## pstack에서 유지·제외할 점

고정 조사 기준 `23e4138daa01c42d4969f7a5465f82704e64f798`의 실제 실행 경로, 측정 기준 고정, 원인 owner의 구조적 예방, 최종 revision에 연결된 독립 검토는 유지한다. orch 기록·Agent 합의는 실행 증명이나 host 권한 보장을 대신하지 않는다. 고정 10개 검증 경로·항상 다중 Agent·모든 PR 성능 검사·일률적 주석 삭제·patch-id만으로 현재 결과 재사용은 채택하지 않는다. pstack 최신 버전이나 동일 과제 실행 우열은 이번 검토 대상이 아니다.

## 이번 확인의 범위

- 실제 canonical 함수와 기존 테스트 fixture로 위 다섯 세부 사례를 실행했다. 제품 원본은 수정하지 않았고 HTTP/브라우저·외부 서비스·native 설치 host는 실행하지 않았다. 순수 Python quote 호출과 반환값은 직접 확인했다.
- 재현 코드와 JSON은 `.work/post-r0-r4-review-20261009/{probe.py,probe_decision_refresh.py,probe_criteria_only.py,reproductions.json}`에 있다. 장기 판단에 필요한 관찰·조건·수정 방향은 본문에 남겼다.
- 문서 정합성은 `python -m unittest tests.distribution.test_repository_docs` 3개 통과와 `git diff --check`로 확인했다. 이번 Feature 영향은 `documentation`; runtime·배포 리소스·버전은 바꾸지 않는다.
- 0.1.45의 native host 접근 제약, 선언된 inventory의 완전성, 의미 검토의 충분성, 장기 무인 효과는 여전히 별도 한계다. 이 검토는 추가 구현·설치·main 통합 권한을 새로 만들지 않는다.
