# Agent Coding 업무 위임·검증·지속 개선 체계

결정일: 2026-10-05. PStack 조사, 10/3~4 후보 Skill, 독립 Labeler 파일럿 및 이후 사용자 논의의 **현재 설계 결론**이다. 새 업무 진입점과 유지보수 능력의 구현 완료를 뜻하지 않는다. 현재 실행·권한·Git 정책은 [Agent workflow](../agents/workflow.md), 구현된 검증 도구는 [Testing](../testing.md)을 따른다. 다음 구현은 [실행 프롬프트](agent-coding-next-session.md)로 시작한다.

## 1. 목표와 논의 과정

목표는 Agent에게 많은 업무를 위임하면서 **무엇을 검증했고, 어떤 결과를 신뢰할 수 있으며, 발견한 불편이 어떻게 재발 방지로 이어졌는지** 확인하는 것이다. `Confidence / Verification Cost`는 실제 결함 검출력과 실행·유지 비용을 함께 판단하는 기준이다. 테스트 수·coverage·Skill 수를 목표로 삼지 않는다.

| 논의 단계 | 확인·판단 | 현재 결론에 미친 영향 |
| --- | --- | --- |
| PStack 조사 | Mode/Router가 요청을 Playbook에 연결하고 필요한 Skill·Principle을 선택한다. 검증 경로 구축·유지, 고정 평가 기준과 구조적 예방이 유용하다 | 능력 집합 위에 업무 조합과 완료 판단을 둔다. 전체 구조를 복제하지 않는다 |
| 10/3~4 후보 검토 | 환경 식별, 실제 사용자 행동, 원인별 개선, 안전한 재개 등의 지식은 유용하지만 후보 전체의 Agent 품질 우월성은 미입증이다 | 후보 전체 병합 대신 책임별 축소 도입·흡수 |
| 기반 구현·Labeler 파일럿 | 실제 앱·API·D1·PDF 검증과 통제 결함 대조가 가능했다. BE 검사는 놓친 FE 가격 전달 오류를 브라우저가 검출했다 | 사용자 기능과 계층을 연결한 검증, 실행 근거와 판정 분리가 필요 |
| 초기 최소화 판단 | 직접 명령을 우선하고 새 Router·독립 Skill 도입을 보류했다 | 실제 실행 토대는 유지한다. 당시 파일럿 범위의 결정이다 |
| 이후 사용자 요구 | 관련 Skill을 한 번에 조합하고 검증 조회·피드백·UI 기준·검증 유지보수를 하나의 업무로 수행해야 한다 | 얇은 `agent-workflow`와 두 공통 검증 Skill을 도입한다. 이전 Router 전면 보류 결론을 대체한다 |

우선 기능은 (1) 위임 업무의 검증 가시성, (2) 비즈니스 모델·아키텍처 및 FE/BE/Domain 검증, (3) 피드백과 자가 개선, (4) UI/UX 기준 고도화, (5) 검증 기준 고도화, (6) 원인 추적·실질적 가드레일·불필요한 검증 제거다.

이전 설계와 수행 완료 프롬프트는 [아카이브](archive/index.md)에 보존한다. 그 안의 미래형 지시는 현재 작업을 승인하거나 다시 실행하는 근거가 아니다.

## 2. 구현 상태

| 상태 | 구성요소 | 확인 범위 |
| --- | --- | --- |
| 구현됨 | 기존 Harness Skill, `diagnose`, UI 능력, `multi-agent-review`, source/generated 배포 체계 | 작업·재현·배포·보존 책임 재사용. 다른 제품의 의미를 자동 검증하지 않음 |
| 구현됨 | `scripts/run_check.py` | 유한 foreground 실행, native exit/timeout, 실행 ID·대상·Git 상태·raw output, 새 native JSON report 캡처. `behavior_verdict`는 null |
| 구현됨 | `scripts/verify_product.py`, 관리 저장소 Feature Map·selector | 이 저장소의 unittest 전용. 다른 프로젝트의 Vitest·브라우저용 범용 parser가 아님 |
| 파일럿 확인 | 독립 Labeler의 browser/API/D1/인쇄, 통제 결함·Agent 수리·독립 검증 | 고정 소스와 로컬 합성 fixture에 한정. [결과와 제한](labeler-verification-pilot.md) 참조 |
| 파일럿 확인 | 임시 Plugin 설치·fresh host discovery·cache 명령 실행·버전 변경 | 일반 설치 전환, 모델의 Skill 선택·이행, hook 품질은 미검증 |
| 합의됨·미구현 | `agent-workflow`, 축소된 `setup-project-verification`, `maintain-project-verification` | 다음 세션 구현 대상 |
| 합의됨·미구현 | 프로젝트 `verify-product`·`ui-system` 진입점, 조건부 verifier 역할, 업무별 결과 조회 | 실제 프로젝트의 기준·명령·evidence에 연결해 행동 검증 필요 |

문서 정리 시작 기준은 `wp-20261004-agent-coding-foundation`의 `c1e4b9e6ea22605c3458f2c859cf1fac49dde4c5`, dirty 없음이다. 다음 세션은 실제 checkout을 다시 확인하며 원격 main이나 과거 donor로 덮어쓰지 않는다.

## 3. 하나의 업무 진입점과 선택적 Playbook

공통 신규 Skill은 우선 세 개다. 프로젝트별 Skill은 정답을 복제하는 문서가 아니라 기존 기준·도구를 찾는 연결점이다.

| 구성요소 | 소유할 책임 | 경계 |
| --- | --- | --- |
| `agent-workflow` | 의도 → 업무 절차 → 능력·영향 검증 선택, 결과 취합 | 제품 정답·명령 parser·모든 작업의 강제 lifecycle을 소유하지 않음 |
| `setup-project-verification` | 기존 기능·요구·환경·테스트·UI 조사, 첫 실행 가능한 검증 경로와 기준 마련 | 기존 map/guide부터 갱신. Harness 설치 강제 금지 |
| `maintain-project-verification` | Feature·검증·UI 기준의 의미 있는 drift, 누락·중복 점검과 범위 내 수리 | Harness 배포·retention·cohort 무결성과 구분 |
| 프로젝트 `verify-product` | root, Feature 기준, 명령·adapter·근거·정리 경로 안내 | 다른 runner에 unittest parser를 억지 적용하지 않음 |
| 프로젝트 `ui-system` | 기존 UI guide, token, component, 대표 화면·상태 검증 연결 | token 값·규칙의 수동 이중 기록 금지 |
| 조건부 Verification Agent | 고정 요구·diff·대상에 대한 독립 검토와 실제 검증 | 제품·정답·assertion 임의 수정 금지. 파일 생성만으로 독립성 주장 금지 |

내부 Playbook은 여섯 가지다. 각각 독립 Skill을 추가하지 않는다.

| 업무 | 요청 예 | 수행 순서·기존 능력 |
| --- | --- | --- |
| 초기 연결 | “이 프로젝트의 검증 체계를 마련해줘” | 조사 → setup → 첫 실제 flow → 기준·명령 연결 |
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

매 변경마다 모든 칸의 테스트나 Agent를 요구하지 않는다. 변경 로직·직접 호출자·상태·공유 자원·계약에서 영향 Feature를 선정한다. 아키텍처 검토는 touched boundary에 집중한다. 불명확한 영향은 조사하며 무조건 Full이나 생략으로 처리하지 않는다.

## 5. Feature Map·검증 실행·결과 조회

프로젝트 Feature Map의 최소 정보는 `ID/이름, 사용자 행동, 기대 결과, business invariant, FE, BE/API, Domain, 데이터 side effect, 실제 검증 방법`이다. 기존 구조를 재사용하고 assertion·특정 실행의 PASS를 영구 지도에 복제하지 않는다. 관련 없는 층에는 해당 없음과 이유를 둔다.

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

현재 capture는 untracked 내용, dependency, fixture, served source, Agent 신원이나 editable evidence 진위를 인증하지 않는다. 중요한 항목은 프로젝트 실행 경로에서 확인한다. 과거 결과 조회는 원래 판정과 현재 재사용 가능성을 구분하고 자료가 없으면 주장을 확대하지 않는다.

## 6. 피드백을 수정과 가드레일로 연결

`불편/실패 → 기대 동작 → 재현 → 원인·상태/데이터 흐름 → 기존 소유자 수정 → 가드레일 → RED/GREEN·정상 반례 → 영향 기준 갱신`으로 수행한다. 설명 요청만으로 수리하거나 전역 규칙·개인 memory를 변경하지 않는다.

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

가드레일은 원래 실패를 검출하고 가까운 정상 사용을 허용해야 한다. 동작 보존은 baseline/equivalent GREEN을 쓸 수 있다. 기대값·skip·visual baseline을 완화해 결함을 숨기지 않는다. 지침이 이미 있었다면 같은 문장 추가보다 적용되지 않은 원인을 고친다.

자가 개선은 관찰된 회귀·실패·drift·피드백에서 시작한다. 범위 안의 가역적 개선은 진행하고 제품 결정 변경·전역 변경·외부 비용 등의 경계는 기존 권한을 따른다. 자동 회고·규칙 축적·무한 재시도는 만들지 않는다.

## 7. 지속 갱신의 책임

| 책임자·계기 | 수행할 일 |
| --- | --- |
| setup / 최초 연결 | 기존 map/guide/UI 조사, 핵심 flow·정상/실패 기준·명령 연결 |
| 기능 변경 수행자 / 추가·수정·삭제 | 영향 Feature·계약·검증 방법을 같은 변경에서 갱신 |
| 검증자 / 완료 검토 | 요구·동작·근거와 지도 누락·기준 유효성 대조 |
| product maintain / 요청된 점검·회귀·drift | 누락 기능·죽은 명령·계층 공백·중복 검사 조사, 실제 실행·수리 |
| UI 작업자 / 관련 변경·반복 불일치 | 디자인 의도·대표 화면·상태 검토, 필요한 token/component·guide 개선 |
| Harness maintain / 관련 무결성 문제 | mapping·배포·retention·cohort 점검 |

UI 기준은 design principles, color/typography/spacing/radius/elevation, layout/component conventions, loading/empty/error, responsive·accessibility, Do/Don't·reference·visual 검증을 필요한 깊이로 연결한다. 의도는 guide, 실제 값·동작은 코드가 소유한다. 한 화면의 의도된 예외를 전역 규칙으로 승격하지 않는다. 관련 desktop/mobile·interaction을 실제 확인한다.

제품 버그·오래된 guide·실행 도구 오류를 구분한다. 제품 위반을 guide 변경으로 숨기지 않는다. 영구 문서는 현재 사용법과 lasting 결정, 상세 로그·fixture·screenshot은 기존 `.work` 보존 정책에 둔다.

## 8. 검증을 유지·통합·제거하는 기준

`무슨 실패를 잡는가 → 같은 실패를 잡는 다른 근거가 있는가 → 축소/삭제 후에도 검출되는가`로 판단한다. 비용은 측정했을 때만 수치로 말한다.

- 우선 유지: 실제 regression, 핵심 invariant, 권한·계정·데이터 손상 방지, 경계 계약, 주요 flow, cheap deterministic 검사.
- 정리 후보: 구현 세부 고정, 검출 중복, brittle mock, 비용 대비 독자적 검출 부족, enforcement로 대체된 검사.
- 삭제 조건: 남기는 검사/구조가 같은 의미의 실패를 잡고 정상 반례도 통과한다는 근거. 검출 이력이 없거나 오래됐다는 이유만으로 예방 검사 삭제 금지.
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
| setup-project-verification 후보 | 환경·첫 검증 연결로 축소 재도입. 과거 helper 사본·전체 파일 복원 금지 |
| ui-refine 후보 | UI Playbook·기존 UI 능력·프로젝트 ui-system에 흡수 |
| improve-workflow 후보 | 원인 분류·피드백·maintain에 흡수 |
| resume-work 후보 | 기존 재개에 상태·권한·evidence 유효성 확인 흡수 |
| clear-writing 후보 | 핵심 위임에서 제외. 실제 문장 편집에 필요할 때 사용 |

donor는 `b40396a63b1031b8a3958d376fb3cc46499a9191`이다. 당시 배포 계열과 달랐으므로 본문·지식만 선별해 현재 source에 반영한다. 전체 우월성은 미입증이다. 이미 수행한 카탈로그·launcher·capture 작업을 반복하지 않는다.

Plugin은 검증된 공통 Router·Playbook·Skill·capture 등의 **생성 패키징·버전·설치 수단**이다. 제품 정답·UI token·Feature Map·fixture·adapter는 프로젝트에 둔다. CLI/CI를 유지하고 canonical authoring에서 산출해 수작업 사본을 늘리지 않는다.

다음 세션은 업무 흐름과 실제 행동이 우선이며 공개 Plugin 전환은 선행 조건이 아니다. 필요한 임시 host 검증에서 설치·discovery·실행·업데이트·중복과 모델의 선택·이행을 구분한다. agent·hook·plugin 형식은 구현 시 현재 host와 공식 문서를 확인한다. 일반 설치·전역 설정·원본 제품 통합·push/publish는 별도 권한 범위다.

## 10. 다음 구현의 완료 단위와 보고

1. 업무 선택·조회: 한 요청에서 절차를 선택하고 Feature별 계획·실제 결과·미검증 범위를 조회한다. 조회만 요청한 경우 재실행·수정하지 않는 반례 확인.
2. 프로젝트 연결: 독립 Labeler의 지도·native/browser·UI 기준을 새 진입점에서 재사용하고 요구·대상을 연결.
3. 피드백·가드레일: 의미 있는 실패를 재현하고 최소 수정·재발 방지를 같은 실패·정상 반례로 재검증.
4. 통합 유지보수·UI: 근거 있는 map/guide·UI drift를 수리하고 실제 기능·화면 확인. 조합해도 중복 실행·판정 은폐 방지.
5. 가치 평가·배포: 중복 검증 축소 또는 보존 판단, source/generated·임시 설치·실제 Agent 업무 수행을 구분해 검증.

문서·파일·schema·설치 메타데이터만으로 완료하지 않는다. 사용자 형태의 요청으로 선택·실행·취합·기준 개선이 이어지는지 확인한다. Agent 평가가 환경 때문에 막히면 native 검증은 계속하되 통합 위임 효과는 BLOCKED다. 소수 관찰로 안정적 품질·속도 우월성을 주장하지 않는다.

보고는 `가능해진 사용자 업무 → 구현 위치/commit → 실행 과업 → 정상·결함·반례 결과 → raw evidence → 제한`을 연결한다. 소스, 설치, 제품 동작, Agent 행동, 실환경 적용을 구분한다. 다음 세션 결과는 하나의 결과 문서로 연결하고 이 문서와 프롬프트의 상태를 갱신한다.

## 근거와 권한

- 실제 제품·Agent·Plugin 관찰: [Labeler 결과](labeler-verification-pilot.md).
- 외부 조사·고정 source: [PStack](pstack-analysis.md).
- 이전 설계·배포 비교·완료 프롬프트: [아카이브](archive/index.md).
- 현재 명령·소유권: [docs index](../index.md), [Feature Map](../feature-map.md), [Testing](../testing.md), [resource map](../../authoring/resource-map.json).
- 이번 작업은 결론·프롬프트·문서 정리만 구현한다. 원본 Labeler, 일반 설치, 실행 Skill·도구·전역 지침은 변경하지 않는다. 다음 세션 실행 요청은 관리 source·독립 시험의 구현·검증으로 해석하며 기존 승인·보안 경계를 보존한다.
