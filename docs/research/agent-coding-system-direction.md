# Agent Coding 업무 위임·검증·지속 개선 체계

현재 기준: **2026-10-09 / 0.1.45 / main `f8db21e` 재검토**. 목표는 많은 업무를 위임하면서 요구·실행·근거·미확인·후속 개선을 확인하는 것이다. 기존 task/context, 6셀 scope, 실제 runner, feedback/prevention, UI guide와 maintenance를 유지한다. [최신 보완 검토](agent-workflow-refinement-review.md)에서 재현한 **결정의 유효성, 규칙만 폐기하는 경우, 관찰 범위 요약**을 다음 개선의 우선순위로 삼는다.

[R0–R4](agent-workflow-completion-design.md#review-driven-refinement)와 [실행된 요청](agent-workflow-next-session.md)은 수행 범위의 기록이다. [구현 결과](agent-workflow-implementation-results.md#r0r4-implementation-2026-10-09)는 실제 동작과 host 한계를 소유한다. 이번 문서 보완은 추가 런타임 수리·설치·일반 위임 효과의 입증이 아니다. 아래 제안과 현재 구현을 구분한다.

Agent는 요구·원인·시각·검사 가치의 의미 판단을, CLI는 상태·실행·근거 결합을, 프로젝트는 정답·runner·코드·UI 기준을 소유한다. 우회 불가 권한/수락이 필요한 경우에만 지원 host 경계를 별도로 검증한다. 로컬 기록의 정합성과 보호된 수락은 같은 보장이 아니다.

현재 실행·권한·Git 정책은 [Agent workflow](../agents/workflow.md), 명령과 검증은 [Testing](../testing.md)을 따른다. 과거 G1–G6/T1–T6와 U1–U7 설계는 기존 범위와 책임을 설명하는 근거이며 일괄 재구현할 목록이 아니다. 과거 문서의 미래형 지시나 승인 기록이 새 작업 권한을 만들지 않는다.

## 1. 목표와 논의 과정

2026-10-07 현재 구현은 요청 context → 기존 task → prepare/execute → lookup을 연결하고, 독립 시험 프로젝트의 실제 Chromium·API·Domain·SQLite·재시작 조회와 피드백/UI 수리·검사 통합·후속 재사용까지 확인했다. 세부 성숙도와 고정 pstack 비교는 [현재 구현 결과](agent-workflow-implementation-results.md#connected-actual-product-use-2026-10-07)를 따른다. 이는 설치 갱신, 일반 Agent 업무 효과, 보호 호스트 수락의 확인을 뜻하지 않는다.

목표는 Agent에게 많은 업무를 위임하면서 **무엇을 검증했고, 어떤 결과를 신뢰할 수 있으며, 발견한 불편이 어떻게 재발 방지로 이어졌는지** 확인하는 것이다. 최상위 판단은 실제 업무의 효율·효과·정확성과 사용자 개입/재작업 감소다. `Confidence / Verification Cost`는 실제 결함 검출력과 실행·유지 비용을 함께 판단하는 기준이다. 테스트 수·coverage·Skill 수·차단 횟수를 목표로 삼지 않는다. 새 제약의 결함 검출 이득과 정상 과업 오탐·비용을 비교해 이득 없는 제약은 축소/제거하되 기존 권한 경계를 완화하지 않는다.

| 논의 단계 | 확인·판단 | 현재 결론에 미친 영향 |
| --- | --- | --- |
| PStack 조사 | Mode/Router가 요청을 Playbook에 연결하고 필요한 Skill·Principle을 선택한다. 검증 경로 구축·유지, 고정 평가 기준과 구조적 예방이 유용하다 | 능력 집합 위에 업무 조합과 완료 판단을 둔다. 전체 구조를 복제하지 않는다 |
| 10/3~4 후보 검토 | 환경 식별, 실제 사용자 행동, 원인별 개선, 안전한 재개 등의 지식은 유용하지만 후보 전체의 Agent 품질 우월성은 미입증이다 | 후보 전체 병합 대신 책임별 축소 도입·흡수 |
| 기반 구현·Labeler 파일럿 | 실제 앱·API·D1·PDF 검증과 통제 결함 대조가 가능했다. BE 검사는 놓친 FE 가격 전달 오류를 브라우저가 검출했다 | 사용자 기능과 계층을 연결한 검증, 실행 근거와 판정 분리가 필요 |
| 초기 최소화 판단 | 직접 명령을 우선하고 새 Router·독립 Skill 도입을 보류했다 | 실제 실행 토대는 유지한다. 당시 파일럿 범위의 결정이다 |
| 이후 사용자 요구 | 관련 Skill을 한 번에 조합하고 검증 조회·피드백·UI 기준·검증 유지보수를 하나의 업무로 수행해야 한다 | 얇은 `agent-workflow`와 두 공통 검증 Skill을 도입한다. 이전 Router 전면 보류 결론을 대체한다 |
| 구현 이후 전체 init·환경 집행 논의 | Labeler는 시험 환경이며, 전체 기능의 최초 지도와 매 고도화 갱신, Agent 판단과 우회 불가 환경 통제, 제약의 실익이 필요하다 | 한 흐름 setup 완료를 전체 init으로 확대한다. 분할·재개·통합과 보호된 수락을 별도 인수하며 기존 파일럿 PASS를 소급 확대하지 않는다 |

우선 기능은 (1) 위임 업무의 검증 가시성, (2) 비즈니스 모델·아키텍처 및 FE/BE/Domain 검증, (3) 피드백과 자가 개선, (4) UI/UX 기준 고도화, (5) 검증 기준 고도화, (6) 원인 추적·실질적 가드레일·불필요한 검증 제거다.

기존 인수는 공통 작업 상태 수리 → 범용 프로젝트 연결 → 업무 흐름 시험 → 독립 검증·패키지 고정 → 격리 제품 인수 → 공통 결함 수리 순서로 진행했다. 새 고도화도 제품별 정답을 공통 기능에 먼저 주입하지 않고 범용 반례부터 확인한다. 연두라벨의 가격·인쇄·Cloudflare 구조를 공통 기능의 설계 기준이나 하드코딩으로 삼지 않는다. 연두라벨에 맞춰 연결을 미리 수작업한 뒤 범용 setup의 성공으로 보고하지 않는다.

새 프로젝트의 기존 명령·기준·실행기를 조사하고 실제 연결하는 능력까지 플러그인의 기능이다. 프로젝트별 지도·가이드·최소 adapter는 이 능력을 사용한 결과물이며 해당 프로젝트가 소유한다. 범용성은 공통 작업 절차와 프로젝트별 실행·정답의 분리로 평가하고, 무설정으로 모든 기술 스택을 지원한다고 주장하지 않는다. 실제 사용할 수 있는 실행·관찰 수단과 미지원 범위를 명시한다.

자가 개선은 관찰한 문제의 원인 소유 위치를 고치고 후속 요청에서 개선을 소비하는 흐름이다. 제품 결함은 프로젝트 코드, 연결 결함은 프로젝트 명령·가이드·adapter, 공통 결함은 플러그인 canonical 소스·기존 절차에서 수리한다. 공통 수정은 원래 실패와 다른 프로젝트의 정상 사례로 검증하고 새 패키지로 구분한다. 설치본·전역 규칙의 자동 변경이나 무한 재시도를 뜻하지 않는다.

이전 설계와 수행 완료 프롬프트는 [아카이브](archive/index.md)에 보존한다. 그 안의 미래형 지시는 현재 작업을 승인하거나 다시 실행하는 근거가 아니다.

## 2. 구현 상태와 다음 공백

0.1.45의 범위 한정 실제 실행과 이번 추가 재현을 함께 본다. 아래 미흡점은 [보완 검토](agent-workflow-refinement-review.md)에 조건·관찰·코드 소유 위치를 남겼다. 검사 수나 패키지 무결성을 일반 위임 신뢰도의 대용으로 쓰지 않는다.

| 영역 | 이미 확인한 토대 | 남은 공백/경계 |
| --- | --- | --- |
| 요청·조사·재개 | 같은 task/context, 미설정 조사, 안정 ID·근거·권한, 읽기 전용 조회와 실행 0회 | source-only 관찰의 runtime 미확인이 짧은 요약에서 빠질 수 있음. 선언한 inventory가 실제 전체 제품을 증명하지 않음 |
| Full-stack 검증 | 6셀 scope, prepare/execute/lookup, 실제 Chromium/API/Domain/SQLite·재시작 readback, FE 오류/BE PASS 반례 | 의미·구조 근거의 충분성은 독립 검토가 필요. 사업 성과나 모든 조건의 동작을 증명하지 않음 |
| 피드백·예방 | 원인별 분기, 실제 원래 기준 RED/GREEN·정상 사례, 새 기준/adapter 재확인과 후속 소비 | 철회된 동의의 metadata 재승인, 모호한 agree, 기준 변경 후 예외 승인 유지가 재현됨 |
| UI/검증 guide | 공유 owner·consumer·의도된 예외 연결, 실제 공유 UI 수정과 다음 요청 재사용, 프로젝트 runner 유지보수 | guide 연결 상태가 시각·사용성 품질의 판정은 아님. 예외 기준 revision과 새 consumer 인수가 필요 |
| 검사 가치 | 실제 detector 통합, 고유 방어 유지, 요구 일부 폐기 분기 | API/호출자 유지·업무 규칙만 폐기하는 정상 경우가 제거 목록 강제에 막힘 |
| 패키지·host | 19 Skills/246파일의 0.1.45 동결 패키지, 자연어 package 사용·fresh context·직접 조회 | native 새 버전 발견/context/보호된 수락, 장기 무인 효과·동시 다중 writer는 미검증/미지원 |

원래 R0–R4 Full 387개와 최종 영향 회귀 11개 통과는 해당 사례의 근거다. 이번 추가 재현에서 발견한 공백을 소급 통과한 것으로 취급하지 않는다. 이전 0.1.43 review/findings 승계 수리는 유지하며 다시 신규 구현 대상으로 올리지 않는다.

## 3. 하나의 업무 진입점과 선택적 Playbook

공통 책임은 아래 세 개로 나누되 Skill 세 개라는 파일 수를 완료 조건으로 삼지 않는다. 기존 진입점으로 책임과 발견 경로를 충족하면 재사용하고, 부족한 공통 판단만 얇은 Skill로 구현한다. 프로젝트별 연결점도 기존 AGENTS/guide로 충분하면 별도 Skill을 만들지 않는다. 이 선택은 §11과 실제 업무 수용 결과로 확인한다.

| 구성요소 | 소유할 책임 | 경계 |
| --- | --- | --- |
| `agent-workflow` | 의도 → 업무 절차 → 능력·영향 검증 선택, 결과 취합 | 제품 정답·명령 parser·모든 작업의 강제 lifecycle을 소유하지 않음 |
| `setup-project-verification` | 전체 기능·요구·환경·테스트·UI 조사와 Feature Map 완성, 실행 연결과 공백 표시 | 큰 프로젝트는 최초 setup 안에서 분할/재개/통합. 첫 실제 flow는 실행 확인이며 전체 지도 대체 불가. Harness 설치 강제 금지 |
| `maintain-project-verification` | Feature·검증·UI 기준의 의미 있는 drift, 누락·중복 점검과 범위 내 수리 | Harness 배포·retention·cohort 무결성과 구분 |
| 프로젝트 `verify-product` | root, Feature 기준, 명령·adapter·근거·정리 경로 안내 | 다른 runner에 unittest parser를 억지 적용하지 않음 |
| 프로젝트 `ui-system` | 기존 UI guide, token, component, 대표 화면·상태 검증 연결 | token 값·규칙의 수동 이중 기록 금지 |
| 조건부 Verification Agent | 고정 요구·diff·대상에 대한 독립 검토와 실제 검증 | 제품·정답·assertion 임의 수정 금지. 파일 생성만으로 독립성 주장 금지 |

내부 Playbook은 여섯 가지다. 각각 독립 Skill을 추가하지 않는다.

| 업무 | 요청 예 | 수행 순서·기존 능력 |
| --- | --- | --- |
| 초기 연결 | “이 프로젝트의 검증 체계를 마련해줘” | 전체 범위 조사 → 필요한 영역 분할 → 전체 지도 통합 → 실행 연결과 첫 실제 flow → 미검증 범위 표시 |
| 구현 | “이 기능 구현해줘” | 기대 결과 → 영향 Feature → 구현 → 검증 → 기준 갱신. 기존 실행 흐름 활용 |
| 검증·조회 | “무엇을 검증했는지 보여줘” | 계획/결과 → 근거·유효 범위 확인. 조회만으로 재실행하지 않음 |
| 통합 유지보수 | “개발 체계를 점검·개선해줘” | 제품 maintain + 관련 Harness maintain + 관련 UI 검토 → 발견 통합 → 범위 내 수리·재검증 |
| 피드백·재발 방지 | “의도대로 동작하지 않아. 고쳐줘” | 기대 동작 → diagnose → 원인 수정 → 가드레일 → 원래 실패·정상 반례 |
| UI 기준 개선 | “UI를 통일하고 기준을 개선해줘” | ui-system → 필요한 기존 UI 능력 → 실제 화면·상태 → 공유 구현·기준 갱신 |

여러 절차가 필요한 요청은 관련 참조만 선택해 읽고 조사·근거를 공유한다. 같은 검증은 유효성이 유지되는 범위에서 한 번 실행한다. 공통 문서·설정·인터페이스 수정은 한 책임자가 순차 수행한다. Harness PASS가 제품 BLOCKED를 가리지 않도록 영역별 판정을 유지한다.

작은 명확한 작업은 직접 완료할 수 있고 Router가 gate가 되어서는 안 된다. 분석 요청은 read-only, 수정 요청은 해당 범위에서 수리한다. 긴 작업·여러 위험 경계는 기존 Work Packet 기준을 적용하고 별도 업무 관리 엔진을 만들지 않는다.

## 4. 검증 관점과 Full-stack 책임

**비즈니스 모델과 아키텍처는 검토 관점, FE·BE·Domain은 책임 영역, E2E는 연결 확인 방법**이다. 사용자 요구와 업무 규칙이 정답이며 현재 구현 자체를 정답으로 삼지 않는다.

| 책임 영역 | 비즈니스 모델 관점 | 아키텍처 관점 | 근거 |
| --- | --- | --- | --- |
| FE | 작업 완료, 입력·오류·저장 상태, 기대 값과 실제 결과 | 상태 소유권, 비동기·중복 상태, component/effect 경계 | 실제 조작·reload/readback, 상태·keyboard·관련 화면 |
| BE | 권한·계정 분리, 저장 규칙, 실패 시 데이터 보존 | parse/validation, API contract, transaction, adapter·실패 책임 | API/handler 결과, persistence·rollback, 계정 경계 |
| Domain | 금액 계산, 상태 전이, 불변 이력 등 invariant | typed model, 규칙 소유 모듈, 순수 로직·의존 관계 | 결정적 behavior·계약·필요한 edge case |
| Cross-layer | 사용자 결과가 제품 전체에서 일치 | UI → API → Domain → 저장 → 재조회 연결 | 실제 앱·API·DB/readback 대조, 필요한 print/PDF |

사업 성과 가설(사용자 가치·전환·수익)과 소프트웨어 업무 규칙(가격·권한·상태 전이)을 구분한다. 전자는 적절한 사용자/운영 관찰이 필요하며 단위 테스트 PASS로 입증하지 않는다. 보안·성능·접근성·데이터 무결성은 관련 셀과 흐름의 속성으로 다루며 셀을 무조건 늘리지 않는다.

아키텍처는 실제 caller·상태/효과 owner·의존 방향·계약·실패 경로를 본다. 코드 구조 설명만으로 PASS를 만들지 않는다. 금지 의존, 중복 상태/호출, API 계약처럼 결정적으로 검사할 수 있는 성질은 기존 test/lint에 연결하고, 설계 선택의 적절성은 근거 있는 의미 검토로 남긴다. 같은 실행이 여러 셀을 뒷받침할 수 있지만 각 주장을 실제로 입증하는지 확인한다.

매 변경마다 모든 칸의 테스트나 Agent를 요구하지 않는다. 변경 로직·직접 호출자·상태·공유 자원·계약에서 영향 Feature를 선정한다. 아키텍처 검토는 touched boundary에 집중한다. 불명확한 영향은 조사하며 무조건 Full이나 생략으로 처리하지 않는다.

## 5. Feature Map·검증 실행·결과 조회

프로젝트 Feature Map의 최소 정보는 `ID/이름, 사용자 행동, 기대 결과, business invariant, FE, BE/API, Domain, 데이터 side effect, 실제 검증 방법`이다. 기존 구조를 재사용하고 assertion·특정 실행의 PASS를 영구 지도에 복제하지 않는다. 관련 없는 층에는 해당 없음과 이유를 둔다.

최초 init은 모든 기능을 대상으로 한다. 요구/화면/API/CLI/job/역할/flag/데이터/기존 테스트를 교차 조사하고, 모든 Feature에 요구 출처·책임·흐름·검증 연결 또는 미연결 상태를 둔다. 큰 지도는 업무 영역별 작성 뒤 영역 간 의존/흐름을 통합하며 전체 조사와 최소 의미가 완성되기 전에는 PARTIAL이다. 지도 완성과 전 기능 테스트 실행 PASS는 구분한다. [전체 init·분할·완료 기준](agent-workflow-completion-design.md)을 따른다.

map/guide는 기준과 방법, 프로젝트 설정은 argv와 실행 연결, `.work/`는 특정 실행 근거를 소유한다. 기존 `.harness/project.yaml`의 명령·영향 선택과 필요한 `extensions`를 우선 검토하되 비-Harness 프로젝트에 설치를 강제하지 않는다. Markdown·JSON·YAML을 사람이 중복 관리하지 않는다.

조회는 처음에 CLI/파일 요약으로 충분하다. 공통 조정 도구가 필요하면 capture·프로젝트 adapter를 호출하는 최소 계층만 둔다. 새 파일명·옵션은 실제 소비자에 맞춰 구현 시 결정한다. dashboard·MCP·모든 runner용 parser는 선행 조건이 아니다.

| 결과에 연결할 정보 | 의미 |
| --- | --- |
| Feature·check·주장·기대 결과 | 어떤 사용자 결과를 확인하는가 |
| 관점·책임 영역·선택/제외 이유 | 무엇을 검증하고 무엇은 영향이 없는가 |
| 실행 상태 | 계획, 실행됨, 미실행, skip, `not_required` 구분 |
| 판정 | PASS / ISSUES / BLOCKED와 미확인 범위 |
| 명령·cwd·source/runtime·fixture | 어느 코드·서버·데이터에서 실행했는가 |
| run ID·native exit·case/skip/error·raw evidence | 요약을 확인할 실제 근거 |
| 구현 commit/diff와 검증 연결 | 어떤 변경으로 어떤 문제가 해결됐는가 |

PASS는 선택한 필수 기준을 실제 확인한 범위에 한정한다. ISSUES는 기대와 다른 실제 행동, BLOCKED는 필수 관찰 불가·미해결 정답·환경 제한이다. `not_required`는 제외이며 PASS가 아니다. 0건·필수 전부 skip·다른 대상·stale 결과·shell 후속 성공은 성공 근거가 아니다.

짧은 조회도 `요청 범위 → 기대 출처/revision → 선택한 검사/관찰 방식 → 실제 결과·근거 → 미확인/제외 이유 → 현재 재사용·다음 행동`을 보여준다. source 조사 완료, 제품 runtime 관찰, 선언한 지도 범위, host 수락 수준을 하나의 PASS로 합치지 않는다. 요청 내 미관찰은 열린 항목으로, 요청 밖 runtime은 미실행/범위 밖으로 표시한다. source-only 요청을 완료하기 위해 브라우저 실행을 강제하지 않는다. 기존 조사 부가 필드의 runtime 미확인이 hook 요약에서 빠지는 문제는 후속 보완 대상이다.

현재 capture는 untracked 내용, dependency, fixture, served source, Agent 신원이나 editable evidence 진위를 인증하지 않는다. 중요한 항목은 프로젝트 실행 경로에서 확인한다. 과거 결과 조회는 원래 판정과 현재 재사용 가능성을 구분하고 자료가 없으면 주장을 확대하지 않는다.

## 6. 피드백을 수정과 가드레일로 연결

먼저 요구 위반·요구 변경·의도된 차이·기준/도구 오류·환경 제약/미확인을 구분한다. 기존 요구 위반은 `불편/실패 → 기대 출처 → 재현 → 원인·상태/데이터 흐름 → owner 수리 → 가드레일 → 같은 기준 RED/GREEN·정상 반례 → 다음 관련 요청의 소비`로 수행한다. 요구 변경은 유효한 변경 근거와 새 기준·유지 계약을, tool 오류는 독립 관찰과 도구 owner 수리를 확인한다. 의도된 차이는 적절한 variant/예외로, 환경/미확인은 열린 상태로 남긴다. 설명 요청만으로 수리하거나 전역 규칙·개인 memory를 변경하지 않는다.

| 원인 | 우선 개선 위치 |
| --- | --- |
| 제품 코드·저장 오류 | 상태·데이터·effect를 소유하는 코드 |
| 잘못된 입력·불가능한 상태 | runtime validation, type/model, 필요한 상태 전이 제약 |
| 반복 UI 불일치 | 기존 token·shared component·상태 API |
| 검증의 결함 누락 | 실패를 관찰하는 사용자 flow·경계 검사·guide |
| 대상·report·exit 오판 | 실행 도구·프로젝트 adapter·환경 식별 |
| 지침 미발견·충돌·과잉 | Router·Playbook·기존 지침의 연결 또는 축소 |
| 설치·배포 drift | source/generated·설치 무결성·Harness |
| 환경·접근 제한 | BLOCKED와 가능한 fallback, 제한 보존 |

사용자 검수는 후보/주장 ID·동의한 처분·범위·요구/UI 기준 revision에 연결한다. “문제가 있다”는 동의와 “차이를 유지한다”는 동의를 구분한다. 설명/원인/owner 메모 수정은 이전 동의의 근거를 새 hash로 바꾸지 않는다. 기준 변경·철회는 재검토하고, 유효한 동일 결정은 후속 task에서 재사용한다. 이는 현재 feedback의 재현된 공백을 보완할 계약이며 새 승인 DB나 매번 사용자 확인 절차를 뜻하지 않는다.

가드레일은 원래 실패를 검출하고 가까운 정상 사용을 허용해야 한다. 동작 보존은 baseline/equivalent GREEN을 쓸 수 있다. 기대값·skip·visual baseline을 완화해 결함을 숨기지 않는다. 지침이 이미 있었다면 같은 문장 추가보다 적용되지 않은 원인을 고친다.

의무의 발생·유지·누락 차단은 환경, 해당 의미를 판단하여 실제 작성·수리하는 것은 Agent, 정형 실행·계산은 code/CLI/runtime이 맡는다. 이 원칙은 요청·구현·검토·검증/조회·피드백·UI·유지보수·설치·자원/재개·완료 전반에 적용한다. 책임/권한의 위치와 처리의 결정성은 별도 축이며 Skill 전체를 하나로 분류하지 않는다. 외부 결과가 변해도 정형 수집/timeout/판정을 LLM에 넘길 이유는 아니다. 지도 갱신은 이 구분의 한 예다. 우회 불가가 필요한 효과는 Agent가 임의로 바꾸지 못하는 권한·수락 경계가 맡으며 선택적 로컬 hook/wrapper나 수정 가능한 PASS 파일은 강제 통제가 아니다. 단계별 분류 기준과 실제 역할 표·최소 context·검증은 [공통 책임 분리 설계](agent-workflow-completion-design.md)에 둔다.

자가 개선은 관찰된 회귀·실패·drift·피드백에서 시작한다. 범위 안의 가역적 개선은 진행하고 제품 결정 변경·전역 변경·외부 비용 등의 경계는 기존 권한을 따른다. 자동 회고·규칙 축적·무한 재시도는 만들지 않는다.

## 7. 지속 갱신의 책임

| 책임자·계기 | 수행할 일 |
| --- | --- |
| 환경 / 요청·변경·실패·설치·재개·완료 경계 | 적용되는 의무와 상태를 발생·유지하고 누락이면 해당 수락/효과를 거절. 정형 처리는 직접 실행하고 의미 작업만 필요한 context와 함께 Agent에 전달 |
| setup / 최초 연결 | 모든 기능의 map/guide/UI 조사, 필요 시 분할·재개·통합, 실행 연결과 미검증 범위 구분 |
| 고도화 수행자 / 기능·코드·UI·검증 추가·수정·삭제 | 영향 Feature·계약·구현/검증 연결을 같은 변경에서 반드시 갱신. 공통 변경은 소비 Feature까지 대조 |
| 검증자 / 완료 검토 | 요구·동작·근거와 지도 누락·기준 유효성 대조 |
| product maintain / 요청된 점검·회귀·drift | 누락 기능·죽은 명령·계층 공백·중복 검사 조사, 실제 실행·수리 |
| UI 작업자 / 관련 변경·반복 불일치 | 디자인 의도·대표 화면·상태 검토, 필요한 token/component·guide 개선 |
| Harness maintain / 관련 무결성 문제 | mapping·배포·retention·cohort 점검 |

UI 기준은 design principles, color/typography/spacing/radius/elevation, layout/component conventions, loading/empty/error, responsive·accessibility, Do/Don't·reference·visual 검증을 필요한 깊이로 연결한다. 의도는 guide, 실제 값·동작은 코드가 소유한다. 한 화면의 의도된 예외를 전역 규칙으로 승격하지 않는다. 관련 desktop/mobile·interaction을 실제 확인한다.

UI guide를 만들 때 현재 화면을 정답으로 복사하지 않는다. 공유 component의 두 소비 화면에서 같은 의미의 정상/오류·keyboard·관련 viewport를 확인하고, 새 context의 다음 화면 요청이 그 guide/owner를 재사용하는지 인수한다. 의도된 destructive/일반 action 차이를 결함으로 수리하지 않는다. UI 예외도 기준 변경과 연결해 재검토한다.

제품 버그·오래된 guide·실행 도구 오류를 구분한다. 제품 위반을 guide 변경으로 숨기지 않는다. 영구 문서는 현재 사용법과 lasting 결정, 상세 로그·fixture·screenshot은 기존 `.work` 보존 정책에 둔다.

행동 보존 리팩터링도 영향 Feature의 구현/검증 참조·검토 기준을 확인하고 달라진 부분을 갱신한다. 단순 timestamp나 자유 문구 `영향 없음`으로 기능 고도화의 의무를 대체하지 않는다. 제품 영향 없는 오탈자/작업 기록은 근거에 따라 내용 불변을 허용하며 매번 전수 조사/Full을 요구하지 않는다.

## 8. 검증을 유지·통합·제거하는 기준

`무슨 실패를 잡는가 → 같은 실패를 잡는 다른 근거가 있는가 → 축소/삭제 후에도 검출되는가`로 판단한다. 비용은 측정했을 때만 수치로 말한다.

- 우선 유지: 실제 regression, 핵심 invariant, 권한·계정·데이터 손상 방지, 경계 계약, 주요 flow, cheap deterministic 검사.
- 정리 후보: 구현 세부 고정, 검출 중복, brittle mock, 비용 대비 독자적 검출 부족, enforcement로 대체된 검사.
- 중복 통합: 남기는 검사/구조가 같은 의미의 실패와 가까운 정상 사용을 보존한다는 근거.
- 요구 폐기: 유효한 요구 변경, 제거/변경/유지되는 진입점·호출자, 남은 계약·소비자 영향, 활성 연결 정리와 이력. 규칙만 폐기하면 API는 남을 수 있으며 없는 대체 검사를 강제하지 않는다.
- 구조적 예방 이동: 실제 거부·정상 허용과 해당 우회/호출 경로를 확인한다. type/constraint가 있다는 선언만으로 detector를 제거하지 않는다.
- flaky/도구 오류: 제품 실패와 분리해 관찰 수단을 수리한다. 재시도 중 한 번의 PASS나 skip으로 공백을 숨기지 않는다.
- 검출 이력이 없거나 오래됐다는 이유만으로 고유 예방 검사를 삭제하지 않는다.
- 소비자 schema·manifest·배포 계약은 문자열 검사처럼 보여도 필요하다. 문구 검사로 Agent 품질을 증명하는 주장과 구분한다.

전수 정리나 mutation framework부터 만들지 않는다. 한 개의 근거 있는 통합·축소로 충분하다. 후보 발견과 삭제 완료를 구분한다.

## 9. PStack·10/3~4 후보·Plugin 채택 범위

PStack 기준은 `23e4138daa01c42d4969f7a5465f82704e64f798`이다. [고정 조사](pstack-analysis.md)와 필요한 원문을 사용하며 최신 inventory·host 지원을 뜻하지 않는다.

| 요소 | 현재 결정 |
| --- | --- |
| Mode/Router·Playbook | 단일 agent-workflow, 필요한 절차 선택. 강제 mode·다단계 handoff 제외 |
| create/maintain verification | Feature 기준·실제 앱 대조·Launch/Doctor/Drive/Evidence/Cleanup를 두 공통 검증 Skill과 프로젝트에 반영 |
| behavior·domain·boundary·구조적 교훈 | 기존 원칙과 코드·type·lint·component·runtime에 반영. 원칙별 Skill 증식 제외 |
| 고정 평가·독립 검토 | 효과를 주장할 과업에서 정상·결함·반례 대조. 항상 전체 fan-out 제외 |
| orch·기록 | revision 연결 참고. 문자열 저장을 실행·독립성 증명으로 취급하지 않음 |
| setup-project-verification 후보 | 첫 구현은 환경·첫 검증 연결로 축소 재도입했으며 후속 U1에서 전체 지도 init으로 확대. 과거 helper 사본·전체 파일 복원 금지 |
| ui-refine 후보 | UI Playbook·기존 UI 능력·프로젝트 ui-system에 흡수 |
| improve-workflow 후보 | 원인 분류·피드백·maintain에 흡수 |
| resume-work 후보 | 기존 재개에 상태·권한·evidence 유효성 확인 흡수 |
| clear-writing 후보 | 핵심 위임에서 제외. 실제 문장 편집에 필요할 때 사용 |

donor는 `b40396a63b1031b8a3958d376fb3cc46499a9191`이다. 당시 배포 계열과 달랐으므로 본문·지식만 선별해 현재 source에 반영한다. 전체 우월성은 미입증이다. 이미 수행한 카탈로그·launcher·capture 작업을 반복하지 않는다.

Plugin은 검증된 공통 Router·Playbook·Skill·capture 등의 **생성 패키징·버전·설치 수단**이다. 제품 정답·UI token·Feature Map·fixture·adapter는 프로젝트에 둔다. CLI/CI를 유지하고 canonical authoring에서 산출해 수작업 사본을 늘리지 않는다.

다음 세션은 업무 흐름과 실제 행동이 우선이며 공개 Plugin 전환은 선행 조건이 아니다. 필요한 임시 host 검증에서 설치·discovery·실행·업데이트·중복과 모델의 선택·이행을 구분한다. agent·hook·plugin 형식은 구현 시 현재 host와 공식 문서를 확인한다. 일반 설치·전역 설정·원본 제품 통합·push/publish는 별도 권한 범위다.

## 10. 다음 개선의 순서와 인수

[최신 검토의 구체적 반례](agent-workflow-refinement-review.md)를 먼저 해결한다. 이는 새 구현의 제안이며, 완료된 R0–R4나 U1–U7 전체를 다시 수행하라는 지시가 아니다.

| 순서 | 가장 작은 개선 | 완료 판단 |
| --- | --- | --- |
| 1 | 기존 feedback 결정의 대상·처분·기준 revision과 hash 승계 수리 | 철회→설명 수정 뒤에도 OPEN; 문제 동의≠예외 승인; 관련 기준 변경 시 재검토; 유효 결정은 후속 요청에서 재사용 |
| 2 | 기존 requirement retirement에서 규칙 폐기와 진입점 폐기 구분 | API 유지·상한 규칙 폐기를 정상 허용; 남은 소비자·활성 보호·근거 부족은 계속 차단 |
| 3 | 기존 investigation/CLI/hook 요약의 관찰 방식·미확인 표시 | source-only 완료를 허용하면서 runtime 미확인을 보존; 원문과 요약의 범위 일치; 조회 실행 0회 |
| 4 | 작은 관련 업무 연속 인수 | 피드백→공유 owner 수리→UI/검증 guide 갱신→새 context 관련 요청; 정상 variant·무관한 변경·낡은 근거 반례와 실제 재사용 |

많은 task의 운영은 기존 task/context/results의 읽기 전용 묶음 요약부터 검토한다. task별 writer를 하나로 유지하고 공유 source/설정의 통합 owner를 지정한다. 같은 base의 독립 task 둘 사이에서 공통 owner가 바뀌는 사례로 최종 통합 상태와 낡은 결과 차단을 확인한다. 의존 범위의 완전한 증명 없이 전체 Git 무효화를 느슨하게 하거나 새 scheduler/상태 DB를 만들지 않는다.

검증은 변경한 결정적 분기의 focused RED/GREEN과 영향 회귀를 우선하고, 관련 동작이 바뀐 최종 후보에 자연어 인수를 제한한다. 같은 요구·source·fixture·host/모델 조건에서 거짓 완료·결함 누락·정상 과업 오탐·개입·재작업·중복 실행·시간을 기록한다. 측정되지 않은 비용이나 임의의 신뢰도 백분율을 만들지 않는다. 효과가 없으면 규칙/절차를 축소하며, 안전·권한 경계를 없애 점수를 높이지 않는다.

보고는 `가능해진 사용자 업무 → 구현 위치/commit → 정상·실패·반례의 실제 관찰 → raw evidence → 후속 소비 → 남은 한계`를 연결한다. 소스, 설치, 제품 동작, Agent 행동, host 수락을 구분한다. 문서·schema·패키지 생성만으로 완료를 주장하지 않는다. 소수 사례의 성공은 장기 무인 운영의 신뢰성 증명이 아니다.

## 근거와 권한

- 실제 제품·Agent·Plugin 관찰: [Labeler 결과](labeler-verification-pilot.md).
- 외부 조사·고정 source: [PStack](pstack-analysis.md).
- 이전 설계·배포 비교·완료 프롬프트: [아카이브](archive/index.md).
- 현재 명령·소유권: [docs index](../index.md), [Feature Map](../feature-map.md), [Testing](../testing.md), [resource map](../../authoring/resource-map.json).
- 작업 권한은 현재 요청과 그 범위에 유효한 기존 승인을 따른다. 과거 실행 프롬프트·설계의 승인 문장을 새 구현·설치·원격·운영·보호 브랜치 통합의 권한으로 재사용하지 않는다.

## 11. 요구사항 검토로 구체화한 실행 연결

2026-10-05 [R01–R16 검토](agent-coding-requirements-review.md)는 수정 전 `53865b0`의 설계 검토다. 당시 책임은 `c7c064a`에서 source/generated·직접 조회 CLI로 구현했고 후속 수정과 독립 시험에서 T1–T6을 수행했다. 아래 setup/갱신 책임은 후속 전체-init 합의에 맞춰 확대했다. 당시의 미구현 판단을 현재 전체-init 기능의 부재로 해석하지 않는다. 실제 충족 상태와 환경 BLOCKED는 [구현 결과](agent-workflow-implementation-results.md), 현재 재현된 공백과 다음 개선 순서는 [최신 보완 검토](agent-workflow-refinement-review.md)와 §10이 소유한다. 일반적 효율·장기 안정성은 입증하지 않았다.

### 발견, 조합, 실패 처리

주 Agent가 요청의 조회/조사/수정 의도, 허용 범위, 대상 root·base/diff, 요구의 출처, 영향 Feature를 한 번 정리한다. 설치된 진입점의 description과 프로젝트 AGENTS/index의 짧은 연결에서 필요한 절차를 찾는다. 다음 구현의 임시 프로젝트에는 이 발견 경로를 실제 연결한다. 사용자가 Skill 이름·호출 순서를 말하거나 평가자가 매 단계 호출을 지시해야만 동작하면 단일 요청 위임 수용에 실패한 것이다. 전역 지침을 바꾸거나 모든 요청에 Router를 강제하지 않는다.

| 책임 | 입력 → 행동 → 다음 소비자 | 중단·실패 경계 |
| --- | --- | --- |
| 주 Agent / 업무 선택 | 자연어 요청·현재 대상·기존 기준 → 필요한 절차/책임/영향 검사 선택 → 하나의 작업 요약과 결과 조회 | 의도 불명확·권한 부족은 의존 작업만 보류. 조회에서는 기존 근거를 읽고 재실행/수리하지 않음 |
| setup / 최초 검증 연결 | 전체 기능과 기존 map/guide/명령/UI → 필요 시 영역 분할 → 전체 지도 통합과 실행 연결/공백 표시 → 변경자·검증자가 재사용 | 미조사 영역·미분류 후보·중요한 요구 충돌은 init PARTIAL/BLOCKED. 첫 flow와 전체 지도 완료를 구분 |
| product maintain / 요청·회귀·drift | 영향 diff·요구·현재 map/guide·실패 근거 → 누락/오래된 연결/검사 가치 조사 → 해당 소유자 수리·재검증 | 제품 결함은 diagnose/제품 소유자에게, 실행 도구 오류는 adapter/capture 소유자에게. audit-only는 발견 보고로 종료 |
| Harness maintain / 실제 mapping·cohort·retention 영향 | 기존 프로젝트 설정·관련 무결성 근거 → 기존 runtime의 해당 점검 → 별도 영역 판정 | 미설치 프로젝트는 해당 없음. 설치나 retention 삭제를 제품 유지보수의 부수 작업으로 수행하지 않음 |
| UI 작업자 / 화면 변경·반복 불일치 | 기존 의도·reference·token/component·영향 상태 → 기존 UI 능력으로 수정·실제 관찰 → 공유 구현과 관련 guide 갱신 | 의도된 예외를 보존. 정상 animation/관찰 오류는 도구를 고치며 UI 기준을 완화하지 않음 |

조사·검사 선택·원본 실행은 같은 대상과 유효 조건에서 공유하고, 한 실행을 여러 Feature가 참조할 수 있다. 공유 사실은 하나의 작업 기록/기존 Harness evidence에 두고 Skill마다 복사하지 않는다. 공통 파일 수정은 주 Agent가 소유한다. 통합 결과는 제품·Harness·UI의 PASS/ISSUES/BLOCKED를 각각 남긴다. 동일 이름의 check라도 대상·기준·조건이 다르면 같은 실행으로 합치지 않는다.

독립 검증이 필요한 경우 주 Agent는 사용자 기준, 해당 base/diff, 실제 실행 대상, 원본 evidence와 쓰기 범위를 검증자에게 전달한다. ISSUES는 재현과 소유자를 붙여 수정 담당자에게 돌려보내고, 새 diff가 무효화한 근거만 재검증한다. BLOCKED는 필요한 관찰·원인·가능한 fallback·재개 조건을 남기고 독립 작업을 계속한다. 같은 원인/근거만 반복되면 가설이나 수단을 바꾸며 무한 재시도하지 않는다. 주 Agent가 raw와 diff를 확인해 최종 판정한다. verifier 파일이나 구현자 PASS 전달은 이 절차를 대신하지 못한다.

### 변경 영향, 모델, 기준 갱신

| 변경·계기 | 선정할 관찰과 기준 갱신 시점 |
| --- | --- |
| Feature 최초 연결 | setup이 전체 기능을 요구/제품 문서/실제 진입점으로 조사하고 최소 의미를 채운 지도를 완성. 분할 작업은 통합 전 PARTIAL. 검사 미연결 기능도 지도에 포함하며 첫 flow로 실행 경로 확인 |
| 모든 고도화·Feature 추가·수정·삭제 | 변경자가 구현 전 기대 결과/invariant·영향을 확정하고, 같은 기능 단위 diff/commit에서 영향 map·guide·활성 selector를 대조하고 실제 변경된 참조·기준을 갱신. 의미·참조 불변이면 그 근거로 기존 내용을 유지. 삭제는 실제 호출/사용 여부를 확인하고 활성 연결만 제거하며 과거 결과는 보존 |
| FE 입력·직렬화·저장·재표시 또는 계층 간 계약 변경 | 관련 UI → API → domain/persistence → 새 조회를 실행. 층별 PASS만으로 대체하지 않음. DB 직접 관찰은 readback으로 확인 못 하는 원자성/중복/이력 규칙에 선택 |
| Domain 계산·상태 전이 변경 | 요구 기반 정상·경계·실패의 결정적 검사. 외부 표현/호출 계약도 바뀌면 해당 adapter와 사용자 flow를 추가 |
| 권한·transaction·외부 실패 변경 | 허용/거절 응답, 실패 뒤 데이터 보존·rollback/readback과 관련 사용자 상태. 실제 계정/외부 서비스 권한이 없으면 그 범위는 BLOCKED |
| UI 표현·공통 component 변경 | 영향 화면·desktop/mobile·keyboard 및 loading/empty/error 등 관련 상태. 저장 경로가 무관하면 제외 이유를 남김. 반복 문제는 가능한 기존 token/component/lint에서 예방하고 후속 요청에서 재사용 |
| 아키텍처만 변경 | touched interface·caller·상태/효과/의존 소유권과 baseline/equivalent GREEN. 행동 영향이 없으면 별도 제품 flow를 억지 추가하지 않음 |
| 완료 검토·요청된 유지보수·escaped regression | 검증자가 요구·diff·실제 관찰과 지도/guide의 누락·죽은 명령·삭제 잔존·계층 공백을 비교. 원인이 제품인지 기준/도구인지 분류해 해당 소유 위치만 수리. 매 작업 전수 조사는 하지 않음 |

아키텍처 판단은 `external boundary → parsing/validation → typed domain model → pure business logic → persistence/external adapter`를 사용한다. FE는 입력/표시/상호작용, BE는 권한/외부 계약/transaction, Domain은 계산/업무 상태/invariant를 소유하는지 실제 caller와 데이터 흐름에서 확인한다. controller·route·UI에 공유 업무 규칙이 흩어졌다면 올바른 기존 소유 위치를 우선한다. 상태 전이 복잡성에는 state machine/reducer, 상호 배타 데이터에는 typed model/discriminated union, 확장 목록에는 registry, 수명주기에는 command/event, 규칙 분산에는 domain module을 검토하되 관찰한 문제 없이 패턴이나 폴더를 추가하지 않는다. 이는 이전 설계의 유효한 책임 원칙을 복구한 것이며 전면 재설계 지시가 아니다.

### 계획·실행·조회 사이의 최소 연결

계획의 Feature/check와 기대 결과는 요구/기준의 출처·revision을 참조한다. 선택/제외 이유와 필수 여부를 실행 전에 정하고, 실제 결과는 그 항목에서 capture의 run ID·명령/cwd·코드 상태·raw 위치 및 native assertion/관찰 위치로 연결한다. 한 실행의 raw는 한 번 보존하고 요약은 그 참조를 소비한다. 실행기는 사실을 캡처하고 프로젝트 adapter/검증자는 업무 의미를 판단한다. 사람이 본 시각 관찰은 관찰자·대상·판단 근거를 표시하며 기계 assertion인 것처럼 쓰지 않는다.

조회는 `당시 실행 상태/관찰/판정`과 `현재 재사용 가능 / stale / 확인 불가`를 분리한다. 필요한 source·기준·명령·dependency·fixture·served build/runtime 조건의 식별값/참조가 없거나 달라지면 현재 PASS로 재사용하지 않는다. 모든 환경을 인증하는 새 시스템은 만들지 않는다. raw가 만료·누락되면 역사적 요약은 읽을 수 있지만 원본 재확인은 불가하다고 표시한다. `.work` 과거 record를 조회 시 수정하거나 새 실행으로 덮어쓰지 않는다.

집계는 필수 관찰이 하나라도 미실행/skip/0건/불명확하면 전체 PASS가 될 수 없다. 확인된 ISSUES와 BLOCKED를 함께 보존한다. `not_required`에는 영향 제외 이유를 붙이고 성공 수에 더하지 않는다. 현재 unittest adapter의 `ISSUES`는 native command 실패라는 check 범위 판정이므로 이를 제품 결함으로 바로 바꾸지 않는다. consumer가 raw에서 assertion 위반과 환경/도구 실패를 구분하며 원인 불명은 제품 판정 BLOCKED로 둔다. 기존 capture/adapter를 대체하지 않고 실제 소비자에 필요한 작은 결과 연결만 구현한다.

### PStack 역할과 배포의 최소 배치

Mode/Router는 의도 선택, Playbook은 조건부 순서, Skill은 재사용 판단, Principle은 기존 기준과 구조적 예방, 실행 도구는 명령·raw 캡처, 프로젝트 설정은 root/argv/selector/예외/보존을 소유한다. PStack Automation은 외부 이벤트·주기 실행을 붙이는 별도 계기다. 이번에는 사용자 요청·변경·실패가 충분하므로 Benny/cron/Slack/webhook를 채택하지 않는다. 반복 수요와 권한·비용 근거가 생기면 기존 절차의 입력으로 연결하며 다른 제품 정답을 만들지 않는다. Plugin은 이 능력의 생성 패키징·설치만 맡는다.

세 공통 Skill의 경계는 업무 조정, 전체 최초 지도와 검증 연결, 기존 경로 유지로 유지한다. 기존 Harness 유지보수는 제품 의미를 소유하지 않아 대체재가 아니며, diagnose는 초기 지도/지속 drift 점검의 대체재가 아니다. setup/maintain이 공유하는 조사·결과 규칙은 한 참조로 유지하고 공통 조정은 기존 AGENTS/Skill 발견 경로와 함께 검증한다. 프로젝트 `verify-product`/`ui-system`은 기존 진입점으로 발견·실행이 충분하면 재사용한다. 추가 Skill 채택은 실제 부족한 책임으로 판단하며 개수에 맞춰 늘리거나 줄이지 않는다.
