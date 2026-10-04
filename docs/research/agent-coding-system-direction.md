# Agent Coding 체계의 수정 방향과 플러그인 확장 기반

검토일: 2026-10-04. 이 문서는 사용자가 요청한 종합 설계와 후속 작업 기준이다. 현재 구현의 설명, 과거 후보본의 관찰 결과, 앞으로 만들 기능을 구분한다. 일반 기능 개발마다 이 문서 전체를 읽거나 같은 보고서를 만들 필요는 없다. 현재 실행·권한 정책은 [Agent workflow](../agents/workflow.md), 검증 선택은 [Testing](../testing.md)을 따른다.

## 1. 결정 요약

**최신 배포 소스에서 다시 시작하고, 후보본에서 검증 가능한 도구 개선만 선별 이식한다.** 자연어로 스킬을 계속 전환하는 라우터를 핵심 경로에서 뺀다. 신뢰의 중심은 프로젝트의 사용자 기능, 기대 결과, 실제 실행 명령과 그 증거다.

최소 흐름은 `요구사항과 Feature Map → 변경 영향 판단 → 필요한 검증 실행 → 기대 결과와 evidence 비교 → 필요한 구조 개선`이다. Skill은 특정 능력을 제공하고, 플러그인은 그 능력과 실행 도구·프로젝트 설정을 설치하고 연결하는 수단으로 발전시킨다. 플러그인으로 포장했다는 사실 자체가 품질을 보장하지는 않는다.

| 결정 | 적용 방식 |
| --- | --- |
| 시작점 | 2026-10-04에 fetch한 `origin/main`의 `e19134358141f901bb22c4af1aea17d7a9e2898c` |
| 후보본 취급 | `b40396a63b1031b8a3958d376fb3cc46499a9191`은 도구·연구 근거를 꺼내는 이식 원본. 전체 병합하지 않음 |
| 라우팅 | 최소한의 발견용 설명과 명시적 호출만 유지. 다른 스킬을 거쳐야 구현·검증할 수 있는 연쇄 제거 |
| 검증 | 프로젝트에서 직접 실행 가능한 명령을 먼저 확보. Feature와 기준·실행 결과를 연결 |
| UI | 기존 DESIGN 문서·token·shared component를 재사용하고 반복 문제를 코드에서 방지 |
| 유지보수 | 변경·실제 회귀·확인된 drift에 반응. 모든 작업에 회고·새 규칙·새 테스트를 요구하지 않음 |
| 플러그인 | CLI와 프로젝트 설정의 책임이 명확해진 뒤 얇게 묶음. 처음부터 MCP 서버·대시보드·범용 router를 만들지 않음 |

2026-10-04 후속 구현에서 최신 기준을 재확인하고 카탈로그 정리, 실행 캡처, Windows 런처 보완과 repository/harness Feature 검증 경로를 구현했다. 실제 제품 적용과 플러그인 설치·로딩은 아직 수행하지 않았다. 현재 사용법은 [Testing](../testing.md), 기능 지도는 [Feature Map](../feature-map.md), 채택·보류와 후속 범위는 [실행 상태와 후속 프롬프트](agent-coding-next-session.md)에 있다. 아래 비교·평가 기록은 당시 기준의 연구 근거다.

## 2. 해결해야 하는 문제와 판단 기준

목표는 Agent에게 더 많은 일을 맡겨도 사람이 결과를 반복해서 전부 검수하지 않아도 되는 체계다. 테스트 수와 coverage 비율은 목표 지표로 삼지 않는다. `Confidence / Verification Cost`는 실제 결함 검출과 유지비를 함께 판단하기 위한 방향이며, 근거 없는 단일 점수로 계산하지 않는다.

| 현재 문제 | 필요한 변화 | 확인할 결과 |
| --- | --- | --- |
| 큰 작업의 완료 선언을 신뢰하기 어려움 | 기대 결과를 먼저 정하고 현재 코드·실행 대상에 묶인 evidence 확보 | 거짓 완료, 검증 누락, 사람의 재검수 감소 |
| 테스트가 형식적임 | 사용자 behavior·business invariant·경계 계약 검증 | 알려진 결함은 실패하고 정상 구현은 통과 |
| FE마다 같은 지시 반복, UI/UX 불일치 | 프로젝트 UI 기준과 공통 구현 재사용 | desktop/mobile·상태·상호작용 일관성 |
| 검증·스타일 기준이 제품과 함께 발전하지 않음 | 변경된 Feature, 재발 결함, 실제 화면 차이를 기준에 반영 | 다음 변경에서 같은 실수 방지 |
| 규칙·테스트·문서 누적 | 검출 가치·소비자·유지비를 기준으로 통합·삭제 | 의미 있는 회귀 검출을 유지하면서 비용 감소 |
| 스킬 라우팅이 실패하거나 불필요하게 작업을 확대 | 직접 작업과 직접 실행 명령을 기본 경로로 사용 | 다른 스킬 호출 없이 작은 일을 끝낼 수 있음 |

검증은 **제품·비즈니스 관점의 정답**과 **FE/BE/Domain 및 아키텍처 관점의 책임**을 함께 본다. 현재 코드에서 규칙을 추출하는 것만으로 정답을 확정하면 기존 버그를 요구사항으로 고정할 수 있다. 사용자 요구와 도메인 규칙을 먼저 확인한다.

## 3. 배포본과 후보본 비교

### 확인한 기준점

| 기준점 | 확인된 상태 | 의미 |
| --- | --- | --- |
| `f4eca3333684b2ebf68fae9d9852a1f6413c5328` | 2026-09-06 15:30 KST, 공개 skill 16개 | 두 계열의 공통 조상. 과거 A/B의 A. 최신 배포본은 아님 |
| `96076c1ddbaf274ef9989b32e3a4f1fb2e431126` | 2026-09-06 16:21 KST, 공통 조상 이후 8개 commit | 결과 검증·cohort 범위·계약 유도 조건·플랫폼 호환성 수정 포함 |
| `e19134358141f901bb22c4af1aea17d7a9e2898c` | 2026-09-22 20:58 KST, 공개 skill 17개 | 10/3 이전이면서 이번 확인 시점 최신 원격 main. HWP skill 추가 |
| `b40396a63b1031b8a3958d376fb3cc46499a9191` | 기존 작업 branch, 공개 skill 20개 | 공통 조상 이후 별도 10개 commit. 신규 5개, write-a-skill 제거, 도구 보완·평가 기록 |

`origin/main...b40396a`의 차이는 배포 계열 9개 / 후보 계열 10개 commit이다. 후보본은 최신 배포 소스 위에 변경을 얹은 상태가 아니다. 그대로 채택하거나 오래된 파일을 통째로 가져오면 이미 배포된 다음 수정을 되돌릴 수 있다.

- `a61b09c`: 잘못된 result/delta 형태 방어, Harness cohort 호환성 범위 축소, 미해결 제품 결정을 곧바로 계약 생성으로 연결하지 않도록 설명 수정.
- 이후 CI 수정: Ubuntu PowerShell 실행, UTF-8·TEMP/TMP 조건, POSIX 설치 상대경로, 텍스트 리소스 해시 정규화 범위 보완.
- `e191343`: `hwp-form-fill` 및 관련 카탈로그·manifest. 이 작업과 무관한 배포 기능이므로 보존한다.

`main`의 `e191343`에 연결된 [GitHub Actions 실행](https://github.com/young-sub/Skill_Management/actions/runs/35724728187)에서 Windows와 Ubuntu의 `Unit and contract tests`, `Generated resource drift` 단계 성공을 확인했다. 별도 `Distribution contract` 단계는 해당 실행에서 skipped였다. 이는 저장소 검사 이력이며 Agent의 실제 업무 품질을 보증하지 않는다.

### 설치와 행동 증거의 한계

2026-10-04에 `C:\Users\YS\.agents\skills` 아래 다음 3개 파일을 다시 읽고, CRLF를 LF로 정규화한 SHA-256을 각 commit의 `git show <SHA>:skills/<상대경로>`와 비교했다. 모두 `96076c1` 및 `e191343`의 해당 파일과 일치했고 `b40396a`와는 달랐다. 전체 설치 트리나 현재 session의 실제 로딩을 검증한 결과는 아니다.

| 설치 root 아래 상대경로 | 정규화한 SHA-256 |
| --- | --- |
| `design-goal/SKILL.md` | `b251562e30260a5cd09504e6ed7230e6a9e108b34b6ab84c713b435b3f00ebda` |
| `explore-idea/SKILL.md` | `56eac0d6db2aa7eddacbca9cc4b0a9d1dab08f90bc697c168abf853e6b070ed1` |
| `execute-codex-goal/scripts/core_harness.py` | `51bfc27058151ccb392f4f9e3b7aac1ff00e18e99439cec13976ae0290609225` |

후보본에는 실행 캡처 첫 출력 경로 생성, Windows Impeccable 다운로드 fallback, 평가 프로세스 정리 등 재사용할 도구 개선이 있다. 그러나 **후보 skill 전체의 품질 향상은 미입증**이다. 최근 전체 비교는 28개 품질 과업 중 0개가 시작됐다. Windows CLI 0.160.0이 요청된 파일 읽기 격리를 강제하지 못해 모델 과업 전에 중단됐으며, 이를 skill 품질 실패·성공·동등성으로 해석할 수 없다. 이전의 제한된 UI 실행과 단발 비교도 안정적인 효과를 입증하지 않는다.

과거 상세 기록은 보존한 후보 commit의 `docs/research/agentic-development-improvement.md`에서 읽을 수 있다. 이 문서가 그 기록의 설계 방향을 대체한다. 과거 제안을 현재 실행 지침으로 함께 복제하지 않는다.

### 현재 작업 위치

`C:\Users\YS\Desktop\python\Skill_Management`는 공통 `.git`을 가진 주 작업 폴더다. 폴더 삭제는 연결된 worktree에도 영향을 줄 수 있으므로 clean 상태를 확인한 뒤 최신 `origin/main`에서 `wp-20261004-agent-coding-foundation`을 만들고 전환했다. 기존 branch `wp-20260906-agent-guidance`와 그 commit은 이식 원본으로 남겨두었다. 연결된 `runner` worktree의 `main`은 변경하지 않았다.

배포 기준으로 되돌아오면서 tracked 카탈로그에는 역사적 `write-a-skill`이 다시 존재한다. 이를 재채택하기로 한 결정은 아니다. 후보본 `90437c6`의 의도적인 배포 제거를 다음 세션에 좁게 재적용하고 최신 HWP 등 무관한 기능은 보존한다. 일반 설치본은 이번 작업에서 갱신하지 않는다.

## 4. 현재 구조에서 재사용할 것과 새로 필요한 것

| 영역 | 이미 존재하는 것 | 필요한 보완 |
| --- | --- | --- |
| 소스·배포 | `authoring/resource-map.json`, canonical authoring, generated skills, 카탈로그·manifest, sync·설치 트리 검사 | 플러그인도 같은 원본에서 생성. 별도 수작업 원본을 늘리지 않음 |
| 작업 흐름 | direct development, 필요할 때 Harness 계약·execute·close·maintain | 작은 작업에 lifecycle 의무화 금지. skill 간 전환 없이 직접 완료 가능하게 함 |
| 규칙·문서 | Global/프로젝트 AGENTS, testing·execution policy, docs index | 중복 규칙 추가보다 기존 소유 문서 수정. 프로젝트별 도메인 정답 보완 |
| 영향 선택 | `.harness/project.yaml`, `select_impacted_checks()` | path candidate와 사용자 Feature의 연결. 변경된 실제 동작으로 최종 선택 |
| 결과 검사 | `evaluate_result()`, `complete`, `close`, evidence schema/provenance | 실행 여부·대상·실제 결과와 판정의 연결. 기록 정합성과 제품 검증 구분 |
| 실행 도구 | 기존 native test/CLI, `scripts/run_check.py`, repository용 `scripts/verify_product.py` | 종료 코드와 원본 기록·판정 연결을 유지. 외부 제품용 parser는 실제 소비자가 생길 때만 추가 |
| UI | Impeccable `document`·`extract`·`doctor`, accessibility·React 도구 | 실제 프로젝트의 token/component/DESIGN와 Feature 검증 연결 |
| 제품 검증 | 설치 CLI·transaction·schema·경계 테스트 | 사용자 Feature Map, 검증 기준, 실제 프로젝트의 FE/BE/Domain 실행 경로 |
| 유지보수 | Harness integrity·retention·환경 예외 | 제품 기능·검증·UI 기준의 drift를 좁게 검토하는 절차 |
| 행동 평가 | 후보본의 opt-in eval runner·fixture·프로세스 정리 검사 | 현재 지원되는 격리 환경, 고정된 기준과 정상/결함 대조. 먼저 환경 사전 점검 |

이 저장소는 제품 FE/BE 앱이 아니라 skill·실행 도구 배포 저장소다. 여기의 테스트만으로 다른 제품의 UI·API·DB를 검증했다고 주장할 수 없다. 실제 제품 적용은 별도 대상 프로젝트의 코드·기능·권한을 확인해야 한다.

## 5. 라우팅을 줄인 최소 구성

아래는 책임 구분이다. 폴더나 skill을 각각 새로 만들라는 요구가 아니다.

| 구성요소 | 최소 구현 형태 | 별도 Skill로 만들 조건 |
| --- | --- | --- |
| Workflow | AGENTS의 짧은 위치·명령 안내와 기존 작업 흐름 | 보통 추가 불필요 |
| Project Principles | 기존 testing/architecture 문서와 코드 경계 | 매번 다른 해석이 필요한 전문 절차가 있을 때만 |
| Feature Map | 사용자 기능 기준의 단일 문서 | 지도 자체는 프로젝트 데이터 |
| `ui-system` | DESIGN/기존 UI guide + token + shared component | 기존 UI 도구로 해결되지 않는 반복 작업만 얇게 안내 |
| `verify-product` | 프로젝트에서 직접 실행하는 명령 + guide | 검증 환경을 구성하는 판단이 반복될 때 제한된 진입점 |
| `verification-maintainer` | 변경·회귀에 반응하는 유지보수 절차/명령 | 여러 프로젝트에서 같은 유지보수 판단이 실제 반복될 때 |
| Playbooks | bug fix·UI·검증의 짧은 기존 절차/참조 | 자체 능력이 없는 절차마다 새 skill을 만들지 않음 |
| Plugin | 검증된 도구·선택적 skill·설정·호스트 adapter 묶음 | 실제 설치·업데이트·자동 실행 필요가 확인된 뒤 |

`setup → design → execute → verify → close`를 매 요청마다 skill handoff로 수행하지 않는다. 작은 작업은 현재 Agent가 구현하고 프로젝트 명령을 실행해 끝낸다. 규모·위험상 필요한 계약은 기존 runtime으로 관리하되 또 다른 라우터를 만들지 않는다. Skill 설명은 발견과 범위를 돕는 수준으로 유지한다.

최소 프로젝트 자산은 **Feature Map 한 곳, 기존 verification guide 한 곳, 기존 UI 기준과 구현, 실행 명령, 기존 임시 evidence 저장소**다. 초기에는 Markdown이면 충분하다. 자동 소비자가 필요해지면 그 부분만 구조화하고 사람이 YAML/JSON/Markdown을 각각 중복 유지하지 않는다. 대규모 schema나 core runtime 재작성은 선행 조건이 아니다.

## 6. Feature Map: 사용자에게 제공하는 기능의 지도

Feature Map은 테스트 케이스 목록이나 코드 파일 목록이 아니다. 어떤 사용자 결과를 보장해야 하는지 정하고 관련 코드와 검증 경로를 찾아가는 기준이다. Feature와 test/check는 다대다 관계를 허용한다. 같은 검증을 여러 Feature가 참조해도 한 변경에서 중복 실행할 필요는 없다.

| 필드 | 담을 내용 |
| --- | --- |
| ID와 이름 | 이름 변경에도 추적 가능한 식별자, 사용자 관점의 기능명 |
| 사용자 행동·시나리오 | 사용자/권한, 시작 조건, 핵심 행동 |
| 기대 결과 | 관찰 가능한 성공 결과와 실패 시 보존해야 하는 상태 |
| business invariant | 상태 전이, 계산, 권한·중복·데이터 규칙 중 중요한 것 |
| FE | 화면·interaction·상태·공통 component의 관련 진입점 |
| BE/API | endpoint·contract·authorization·서비스 경계 |
| Domain | 업무 규칙·계산·상태 전이의 소유 모듈 |
| 데이터 side effect | 생성·변경·삭제·외부 호출과 실패 시 금지할 변화 |
| 검증 방법 | 기존 test/실행 명령, 필요한 fixture·환경, 관찰할 evidence |

예시 `product.create / 상품 등록`은 다음 정도로 시작한다. 아래 세부 업무 규칙은 예시이며 실제 프로젝트 요구에서 확정한다.

- 시나리오: 상품 등록 권한이 있는 사용자가 폼을 작성하고 저장한다.
- 결과: 저장한 상품이 목록과 새로 조회한 상세에 나타난다. 잘못된 입력은 이유를 표시하고 저장하지 않는다.
- invariant: 상품 생성 규칙과 필수값을 만족한다. 중복 제출의 결과는 실제 제품의 중복·멱등 정책과 일치해야 한다.
- FE: 등록 화면, 입력 오류, 저장 중 상태, 완료 후 목록 갱신.
- BE/API: create와 read API, validation, authorization, persistence.
- Domain: 상품 생성 규칙과 중복 처리. DB: 필요한 상품 row와 관련 데이터만 원자적으로 생성.
- 검증: 실제 UI 입력 → 저장 → 목록 확인 → 새 조회 또는 reload로 저장 확인. API 실패·권한 거절·잘못된 입력에는 저장 부작용이 없는지 확인한다. DB 직접 검사는 rollback·중복 row처럼 read-back만으로 확인할 수 없는 중요한 규칙에 사용한다.

모든 test assertion을 지도에 복제하거나 최종 PASS를 영구적으로 적지 않는다. 지도에는 안정적인 기대 결과와 실행 경로를 두고, 특정 commit의 결과는 evidence에 둔다. 구현에서 기능 후보를 발견해도 곧바로 정답이나 신규 요구사항으로 승인하지 않는다. 삭제·미사용 기능도 호출자와 사용자 흐름을 확인한 뒤 제거한다.

canonical 지도 위치는 프로젝트의 기존 문서 index나 AGENTS에서 한 번 연결한다. 기능을 변경하는 사람이 해당 항목 갱신을 맡고, 검증자는 영향 Feature와 누락 여부를 확인한다. 검증 결과에는 Feature ID 또는 기능 영향이 없다는 이유를 연결한다. 자동 소비자가 있는 부분은 존재하지 않는 ID·실행 경로를 거부하고, 문서 링크는 기존 링크 검사로 확인한다. 삭제한 Feature의 실행 결과는 과거 기록으로 남길 수 있지만 활성 selector에서는 제외한다. 별도의 상시 관리 Agent가 있어야만 갱신되는 구조로 만들지 않는다.

초기 적용은 중요한 실제 흐름 몇 개로 제한한다. 이 저장소라면 `선택한 skill을 설치·갱신한다`, `작은 작업을 과도한 계약 없이 끝낸다`, `검증 결과를 실행 근거와 함께 확인한다`, `사용자 변경을 보존하며 재개한다`, `소유한 작업 자원만 정리한다`가 사용자 Feature 후보가 된다. 현재 `harness-core / distribution / documentation`은 기술 영역 selector이므로 이 지도를 대신하지 못한다.

변경 영향 판단은 `diff와 변경 로직 → 직접 호출자·계약·공유 자원 → Feature 후보 → 필요한 기준과 검사`로 진행한다. 경로 매핑은 후보만 제공한다. 지도에 없거나 영향이 불명확한 변경은 `unmapped / unresolved`로 드러내고 조사하며, 검증 생략이나 무조건 Full로 숨기지 않는다.

## 7. UI/UX Style System

적용 대상 제품 저장소의 실제 UI 구현을 기준으로 기존 DESIGN.md 또는 style guide를 정리한다. UI 기준·token·component 산출물은 그 제품 저장소가 소유하고, 이 배포 저장소는 재사용할 절차와 도구를 소유한다. 현재 Skill_Management 자체에는 제품 UI가 없으므로 이 단계의 화면 검증은 해당 없음이다. 다음 항목은 대상 제품에 필요한 깊이로 관리한다.

| 기준 | 관리 대상 | 우선할 enforcement |
| --- | --- | --- |
| 디자인 원칙 | 사용자·화면 목적, 정보 위계, 대표 화면, Do/Don't | 대표 화면과 component 사용 기준 |
| 시각 토대 | color, typography, spacing, radius, elevation | token과 theme, 직접 값 반복을 줄이는 lint |
| 구성 | layout, Button/Input/Table/Modal 등 convention | shared component와 layout primitive |
| 상태·상호작용 | loading, empty, error, disabled, validation, focus | component API·상태 모델·행동 검사 |
| 환경 | responsive, desktop/mobile, 키보드·접근성 | 반응형 규칙·접근성 primitive·실제 화면/interaction 검증 |
| 시각 검증 | reference 화면, 필요한 visual regression, 변경 의도 | 고정된 viewport/fixture와 검토 가능한 screenshot |

흐름은 `기존 기준 확인 → 구현 → 실제 화면과 사용자 flow 검증 → 반복 문제 확인 → token/component/기준 보완 → 다음 작업에 재사용`이다. 디자인 의도는 문서가, 실제 token 값과 component 동작은 코드가 소유한다. 문서에 같은 값을 손으로 이중 기록하지 않는다. 자동 추출·생성 결과에는 원본 위치를 연결한다.

해당 UI 변경 수행자가 기존 component·design 기준 소유 범위 안에서 갱신한다. 여러 화면에서 같은 불일치가 재현되거나 공통 component가 기준을 깨는 경우 공유 구현으로 고친다. 단일 화면의 의도된 예외를 전역 규칙으로 승격하지 않는다. 개선은 영향 화면·상태에서 다시 확인한다.

이미 있는 Impeccable의 `document`·`extract`·`doctor`를 먼저 검토한다. `doctor`의 commit 수 기반 drift 신호는 모순의 증거가 아니고, 코드 hook도 전체 화면 품질을 보증하지 않는다. 문서와 실제 token·component를 대조하고 브라우저에서 관련 화면을 확인한다. 단순히 `ui-refine`을 다시 설치하거나 새 `ui-system` skill을 추가하는 것만으로 지속적인 일관성이 생기지 않는다.

Visual 검사에서는 실행 중인 checkout·build·URL과 화면을 먼저 연결한다. 다른 worktree의 서버, 이전 build, 고정 screenshot을 현재 구현 evidence로 쓰지 않는다. 영향받은 화면·공유 component의 상태와 desktop/mobile을 선택해 본다. 저장 관련 UI면 reload/read-back까지 확인한다. 모든 페이지 snapshot이나 시각 baseline 자동 갱신을 기본으로 삼지 않는다.

## 8. Product Verification: 무엇을 어떤 층에서 확인할 것인가

Product/business requirement는 정답의 축이고, FE/BE/Domain은 그 정답을 확인할 책임 경계다. Architecture는 이 경계를 가로지르는 관점이며 E2E는 연결을 확인하는 방법이다. 작업마다 다섯 종류의 suite를 모두 만들거나 실행하라는 뜻이 아니다.

| 관점 | 핵심 질문 | 적절한 evidence와 현재 gap |
| --- | --- | --- |
| Product | 요구와 사용자 결과가 일치하는가? 핵심 invariant를 지키는가? | acceptance와 실제 결과의 비교. 현재 일반화된 Feature Map·제품 정답 연결이 없음 |
| Domain | 계산·validation·상태 전이·업무 규칙·edge case가 맞는가? | pure logic의 결정적 사례·필요한 property 검사. Harness 규칙 검사는 있으나 대상 제품의 업무 규칙 검증은 아님 |
| Backend | API contract, 권한, transaction, 저장, 실패 처리가 맞는가? | 실제 handler/API·저장소 계약·rollback/read-back. 배포 저장소 자체에는 일반 제품 BE가 없음 |
| Frontend | 사용자 flow·interaction·validation·loading/error/empty·visual이 맞는가? | 관련 화면의 브라우저 관찰·상태/접근성 검사. UI skill/fixture가 실제 제품 검증을 대체하지 않음 |
| Cross-layer | 중요한 flow가 앱 전체에서 이어지는가? | 실제 앱 UI/API/저장 연결. installed CLI E2E는 Harness 경계 증거이며 제품 UI/DB E2E와 별개 |
| Architecture | 책임·상태·효과·의존성 경계가 보존되는가? | touched interface/caller 검토, 필요한 계약·의존성 검사. 매 변경마다 별도 아키텍처 보고서 불필요 |

실제 검증에는 deterministic unit test도 포함된다. 브라우저가 항상 더 정확하거나 싸지는 않다. 중요한 실패를 가장 직접적이고 안정적으로 잡는 경계에서 검증하고, 연결 자체가 위험할 때 integration/E2E를 보탠다. 실제 runtime 검증이 더 싸더라도 반복 가능한 회귀 검출이 사라지는지 먼저 본다.

### 구현 후 기본 흐름

1. **기준 확인:** 요청과 Feature의 기대 결과·invariant를 먼저 정한다. 이미 있는 test/guide/명령을 찾고 기준이 불명확한 부분을 분리한다.
2. **범위 선택:** 실제 로직·caller·공유 component·API/DB 계약으로 영향 Feature를 판단한다. 선택/생략 이유는 기존 작업 기록에서 짧게 설명한다.
3. **실행 조건 확인:** checkout/head와 dirty 상태, 실행 명령, 필요한 fixture·권한, 서버/build/URL을 확인한다. 준비 실패를 검증 성공으로 취급하지 않는다.
4. **구현과 집중 검증:** 가능한 경우 중요한 실패를 먼저 관찰한다. 변경 후 작은 신뢰할 수 있는 검사부터 수행하고 연결 위험만 추가 확인한다. 이식처럼 동작 보존 작업은 baseline/equivalent GREEN을 사용할 수 있다.
5. **결과 대조:** native runner의 실제 test 이름·개수·skip·오류, 응답·저장·화면 결과를 기준과 비교한다. 요구된 검증이 0건이거나 전부 skip이면 PASS가 아니다.
6. **종료:** 현재 결과를 evidence와 연결하고 남은 범위를 명시한다. 새 실패·변경·미해결 위험이 없으면 검사를 반복 확대하지 않는다. 소유한 자원만 정리한다.
7. **좁은 유지보수:** 새 Feature, 깨진 검증 명령, 반복 문제만 해당 지도·guide·공통 구현에 반영한다.

### 증거와 판정의 계약

결과는 최소한 `Feature / 주장과 기대값 / 실제 관찰 / 실행 대상·명령 / evidence 위치 / 판정·미검증 범위`를 연결한다. 기본 evidence는 CLI output·exit code, API response, DB 상태, 로그, screenshot, 브라우저 행동이다. 비밀정보와 실제 개인 데이터는 기록에 넣지 않는다. 하나의 실행 결과를 여러 보고서에 복제하지 않는다.

다음 구현의 최소 계약은 판정에서 **실행기가 만든 특정 기록**을 참조하는 것이다. 기존 runner의 run ID나 새로 예약한 고유 output 경로를 사용하고, consumer는 파일 존재뿐 아니라 요청한 check/Feature·argv/cwd·관련 코드 상태·실행 상태와 결과가 그 기록에 연결되는지 확인한다. 누락·다른 대상·관련 변경으로 무효화된 과거 결과는 PASS로 받아들이지 않는다. 기존 근거 재사용은 관련 코드·기준·실행 조건이 유지됐다는 확인을 전제로 한다. 관찰 결과의 업무상 의미는 별도로 판단하며, 이 연결도 증거의 위조 방지나 독립 실행 환경을 보증하지 않는다.

| 판정 | 의미 |
| --- | --- |
| PASS | 선택된 필수 기준을 현재 대상에서 실행했고 관찰 결과가 일치. 확인하지 않은 범위까지 확장하지 않음 |
| ISSUES | 실제 관찰 결과가 요구·invariant·계약과 다름. 재현과 영향 연결 |
| BLOCKED | 필수 기준을 환경·접근·미해결 정답 때문에 확인할 수 없음. 원인·가능한 fallback·남은 범위 표시 |

`not_run`, `skipped`, `not_required`는 실행 상태이며 PASS와 분리한다. 결함과 blocked 범위가 함께 있으면 둘 다 남긴다. exit 0·HTTP 200·screenshot 존재는 필요한 근거의 일부일 뿐 제품 성공의 충분조건이 아니다.

현재 `evaluate_result()`와 close는 제출한 status·ID·기록 정합성을 확인한다. `scripts/evidence_provenance.py`와 `scripts/validate_evidence.py`도 revision·kind·shape 등을 검사하므로 호출자가 입력한 성공을 실제 실행 사실로 승격하지 않는다. 기존 역할은 유지하면서 실행 경로를 별도로 연결한다.

후보 `run_check.py`는 argv/cwd/head/tracked diff hash/상태·시간·stdout/stderr·exit를 기록하고 `behavior_verdict`를 비워둔다. untracked 내용, dependency, fixture, 서버 정체성은 보증하지 않는다. 프로젝트 검증이 그 정보를 필요로 할 때만 adapter가 보완한다. 모든 shell/runner를 해석하는 범용 로그 parser는 만들지 않는다.

필요한 회귀 방지는 현재 실패 근거에서 고른다. 예를 들어 native 실패를 PowerShell의 후속 성공이 가리지 않도록 exit를 즉시 전달하고, 출력 파일은 새 경로에 생성해 stale 결과 덮어쓰기를 막는다. 검증기 자체에는 실패 command·잘못된 대상·누락된 evidence 등 중요한 오판 경로에 대한 소수의 negative control을 둔다. 이것을 모든 기능에 거대한 메타 테스트를 추가하는 규칙으로 확대하지 않는다.

## 9. Verification Guide와 Feature Map의 유지보수

프로젝트의 기존 `docs/testing.md`, README 검증 절, DESIGN 문서를 우선 재사용한다. 유지보수 책임은 `변경된 기능의 기준과 실행 경로를 실제 코드·앱에 맞게 유지`하는 것이다. `maintain-agent-harness`의 배포 무결성·work retention 책임과 혼합하지 않는다.

| 계기 | 하는 일 | 남길 것 |
| --- | --- | --- |
| 기능 추가·변경·삭제 | 영향 Feature와 기대 결과·명령 대조 | 해당 항목 수정, 실제 사용하지 않는 연결 제거 |
| escaped regression | 놓친 기준/환경/검사 원인 확인 | 최소 회귀 검사 또는 type/lint/component 등 구조 수정 |
| 검증 실행 실패 | 환경 문제·제품 결함·오래된 방법 분리 | 실행 경로 수리 또는 BLOCKED 범위 |
| 반복 UI 불일치 | token/component/상태 구현과 기준 비교 | 공유 구현 개선, 필요한 대표 화면 갱신 |
| 요청된 점검·release 검토 | 누락 Feature, 죽은 명령, 중복·brittle 검사 확인 | 가치가 있는 수정·삭제만 |

변경량·경로·route 추가는 조사 후보를 찾는 신호다. 소스만으로 모든 사용자 기능의 완전성을 증명할 수 없다. 문서와 앱이 다르면 요구가 바뀐 것인지 제품이 잘못된 것인지 먼저 확인한다. 제품 결함을 가리려고 기대 결과를 현재 구현에 맞춰 낮추지 않는다.

처음부터 cron·자동 회고·매번 전체 Feature 순회·자동 삭제를 만들지 않는다. 주기 점검은 release cadence나 실제 누락 위험 때문에 가치가 있을 때만 설정한다. 오래됐다는 이유만으로 규칙을 지우지 않고, 위험도 낮고 검출력이 겹치는 규칙부터 정리한다. 영구 문서에는 결정과 사용법을, 실행 로그에는 특정 실행 결과를 둔다. 로그는 기존 `.work` retention과 소유권 정책을 따른다.

## 10. 기존 테스트의 정리 후보와 보존 기준

아래는 소스 검토로 발견한 **후보**다. 이번 문서화에서 테스트를 삭제하지 않았으며 각 테스트의 결함 검출 이력을 전수 측정하지 않았다.

| 위치 | 관찰 | 후속 판단 |
| --- | --- | --- |
| `tests/release/test_release_candidate.py`의 README/release 문구 검사 | 특정 승인 문장·역사적 heading 존재에 의존 | 소비자가 요구하는 계약만 남기고 의미가 같은 문장 편집을 막는 부분 축소 |
| 같은 파일의 workflow 문자열 검사 | Node 버전·CI command 문자열 존재로 실제 실행을 증명하지 못함 | 필요한 설정 계약과 실행 증거를 구분. 지원 플랫폼의 실제 CI 결과 활용 |
| `tests/harness/test_core_first_cutover.py`의 문구/횟수 검사 | AGENTS 문구, Full command 등장 횟수, 은퇴한 표현을 고정 | 유효한 entrypoint/설정 계약은 보존하고 표현만 고정하는 부분 검토 |
| `tests/distribution/test_powershell_hash_portability.py` | 함수명·내부 serializer 문자열 검사와 실제 SHA 비교가 섞임 | 실제 입력/output·cross-platform 결과를 우선. Python SHA와 실제 helper 비교는 보존 |
| forward workflow와 installed CLI E2E | 대표 시나리오가 겹치지만 내부 로직과 설치 경계가 다름 | installed CLI acceptance 유지. 내부 중복만 검출 경로 확인 후 축소 |
| catalog·frontmatter·generated marker 검사 | 일부는 문구처럼 보여도 실제 설치·도구 소비자의 계약 | 문자열 검사라는 이유만으로 삭제하지 않음 |

installed CLI E2E에서 사람이 구성한 `status: passed`, `evidence: observed`를 제출하는 것은 Harness가 기록을 처리하는지 검증하는 유효한 fixture다. 이를 Agent가 실제 앱을 구현·검증했다는 증거로 제시할 때 문제가 된다. schema 테스트, mock, 짧은 테스트를 모두 형식적이라고 분류해서는 안 된다.

삭제·생성 보류 후보는 implementation detail만 고정하거나 동일 실패를 중복 검출하는 검사, brittle mock, 높은 유지비에 비해 독자적 검출력이 없는 검사, 구조적 보장으로 대체된 검사다. 실제 regression 검출, core business invariant, module/boundary 계약, 데이터 손상 방지, 주요 사용자 flow, cheap deterministic 검사는 우선 보존한다. 결함을 잡은 이력이 없다는 이유만으로 중요한 예방 검사를 지우지 않는다.

정리 절차는 `무엇이 잘못되면 이 검사가 실패하는가 → 같은 실패를 잡는 다른 근거가 있는가 → 삭제/축소 후 그 검출력이 유지되는가`다. 필요한 경우 알려진 결함·작은 의도적 오류를 대조한다. 전체 mutation framework를 먼저 도입하지 않는다. test 개수 감소도 그 자체로 성과 지표가 아니다.

## 11. 아키텍처와 구조적 예방

기본 책임 흐름은 `external boundary → parsing/validation → typed domain model → pure business logic → persistence/external adapter`다. Controller·route·UI에 업무 규칙을 분산하지 않는다. 계산·상태 전이는 가능한 한 Domain에서 검증하고, authorization·transaction·외부 실패는 해당 boundary에서 확인한다.

조건이 복잡해지는 원인이 상태 전이면 state machine/reducer, 상호 배타적 데이터면 discriminated union/typed model, 확장 목록이면 registry, 명령·이벤트 수명주기면 command/event, 규칙 소유권이면 domain module을 검토한다. 작은 코드에 모든 패턴이나 새 폴더 계층을 강제하지 않는다. core 파일이 크다는 이유만으로 이번에 전면 분할하지 않는다.

| 반복 문제 | 우선할 구조적 수정 | 남아 있는 검증 |
| --- | --- | --- |
| 색·간격·버튼·상태 불일치 | token/shared component/layout API | 실제 화면·상태·접근성 |
| 불가능한 상태·중복 분기 | type/union/state transition 소유권 | 실제 업무 전이·edge case |
| 경계에서 잘못된 입력 | parse/validation schema, typed domain 변환 | 외부 입력·사용자 오류 처리. type만으로 runtime 입력 보장 불가 |
| 잘못된 의존성·업무 규칙 분산 | module boundary·필요한 dependency lint | touched 계약과 호출 흐름 |
| 중복 저장·부분 저장 | DB constraint/transaction/멱등 처리 | rollback·실패 응답·read-back |
| 검사가 실패했는데 성공으로 보고 | native exit 전파, 신규 evidence 경로, runner 상태 확인 | 실패 command와 미실행 대조 |
| 다른 서버·이전 build 검사 | 실행 대상 식별·프로젝트 launch/doctor 연결 | 현재 화면·데이터가 그 대상에서 나왔는지 확인 |
| 설치본 drift | 원본/설치 전체 상대 파일 집합·hash 검사 | 실제 entrypoint 실행과 host 로딩은 별도 |

같은 실패를 막는 enforcement가 생기면 중복 문장·체크리스트를 줄인다. 구조적 보장도 범위가 있다. DB unique constraint는 사용자에게 적절한 오류를 보여주는지까지 보장하지 않는다.

## 12. 독립 검증과 체계 자체의 평가

작고 되돌릴 수 있는 변경은 한 Agent와 직접 evidence로 충분하다. 큰 작업, 여러 경계, 데이터 손상 위험, 판단의 불확실성에 비례해 구현자와 검증자를 분리한다. FE·BE·Domain·Architecture는 검토할 책임이지 매 작업마다 4명의 Agent를 띄우는 규칙이 아니다.

검증자에게는 요구·Feature 기준, 실제 diff와 revision, 실행 명령·원본 결과를 제공한다. 구현자의 설명이나 자체 PASS만 전달하지 않는다. 필요하면 다른 session/context로 검증하지만 별도 Agent라는 사실만으로 환경·oracle까지 독립적이 되지는 않는다. 주 Agent가 중요 주장과 미검증 범위를 확인하고 최종 결과를 책임진다.

개선 효과는 같은 제품 과업과 고정 기준으로 비교한다. source·설치 트리·model·tool·환경·예산 차이를 기록하고, 정상 대조·알려진 결함·오탐 사례와 필요한 미공개 사례를 둔다. 품질 비교 도중 정답이나 기준을 수정해 점수를 높이지 않는다. 변동성이 결론에 영향을 주면 그때 반복한다. 작은 도구 수정에 전체 Agent benchmark를 의무화하지 않는다.

관찰할 지표는 escaped regression, 거짓 완료, 검출 누락·오탐, 사람의 검수 시간, 실행·유지보수 시간과 비용이다. 단순 PASS 비율·coverage·테스트 수·skill 수는 대리 목표로 삼지 않는다. 모델 이벤트 전 startup 실패는 품질 과업 분모와 분리한다. 현재 후보본 전체의 비교 결과는 판단 불가이며 최신 배포본을 이긴다는 주장은 하지 않는다.

## 13. PStack에서 채택할 것

자세한 원문 조사와 고정 source는 [PStack 분석](pstack-analysis.md)에 있다. 조사 기준은 `23e4138daa01c42d4969f7a5465f82704e64f798`, v0.15.6이다. 당시 일반 등록 skill 49개, Benny 정의 3개, playbook 23개, agent 정의 2개를 구분했다. 현재 최신 inventory라는 뜻은 아니다.

Mode/Router, Playbook, Skill, Principle, Automation/Configuration은 유용한 책임 구분이지만, 반드시 이 순서로 호출해야 하는 계층으로 받아들이지 않는다.

| 참고 요소 | 가져올 것 | 그대로 복제하지 않을 것 |
| --- | --- | --- |
| create-verification-skill | 사용자 Feature에서 시작, launch/doctor/drive/evidence/cleanup, 실제 한 flow를 끝까지 검증 | 프로젝트마다 거대한 독립 skill·동일 문서 생성 |
| maintain-verification-skill | 지도·명령·실제 앱 대조, 누락·삭제 기능 확인, 제품 결함과 guide drift 분리 | 모든 변경에 Feature별 Agent fan-out와 전체 flow 실행 |
| principles | behavior 검증, domain 모델링, boundary 책임, 불필요한 작업 최소화 | 원칙마다 skill을 만들고 기존 규칙과 중복 로딩 |
| playbooks | bug fix·investigation·performance·visual parity의 필요한 절차 | 모든 작업을 router와 다단계 handoff에 종속 |
| frozen benchmark·hillclimb | 기준을 구현과 분리하고 실제 결과로 효과 판단 | 측정 환경이 막혔는데 숫자·문구 검사로 성능 주장 |
| orch·shipping 기록 | revision과 검토 결과 연결 | verdict/evidence 문자열 저장을 실행·독립성 보증으로 간주 |

PStack의 `orch`는 기록한 verdict/evidence와 PR/SHA 연결을 다루지만 그 문자열 자체가 evidence 파일 존재, 실제 검사 실행, 독립 검증자를 입증하지 않는다. 우리 체계도 같은 한계를 반복하지 않도록 기록·실행·판정을 구분한다.

## 14. Skill에서 Plugin으로 발전하는 경계

플러그인의 가치는 같은 도구와 설정을 일관되게 설치·업데이트하고 host와 연결하는 데 있다. 검증 대상 제품의 의미와 정답은 프로젝트가 소유한다.

| 소유자 | 책임 |
| --- | --- |
| 프로젝트 | Feature Map, business invariant, UI 기준·코드, 실제 검증 명령·fixture |
| 공통 도구 | 유한한 command 실행·exit·evidence 캡처, 필요한 설정 검사 |
| 선택적 Skill | 환경 구성·검증 결과 해석·유지보수처럼 판단이 필요한 반복 작업 |
| Plugin adapter | 패키징·버전·설치·명령/선택적 hook 연결과 호환성 |
| 기존 CI/host | 실행 권한, 플랫폼별 자동화·검사 적용 |

구체적 패키지 경로는 실제 소비자가 생길 때 정한다. 현재 `authoring → generated skills → distribution checks`를 유지하고 plugin 산출물을 추가하는 방식이 우선이다. 공통 helper가 필요하면 canonical source 한 곳에서 생성한다. 독립 설치 skill이 다른 skill의 private 경로를 몰래 참조하게 만들지 않는다. MCP는 실제 외부 자원/지속 연결이 필요할 때 검토한다.

2026-10-04 확인한 [공식 plugin 문서](https://developers.openai.com/plugins/build/plugins)는 root `plugin.json`과 `skills/`, 선택적인 MCP·hooks를 설명하며 `.codex-plugin/plugin.json` 호환 형식도 지원한다. 세부 schema를 지금 자체 규격으로 고정하지 않고 구현 시 실제 Codex host/CLI의 지원을 재확인한다. 로컬 파일을 묶는 것, 설치된 package가 일치하는 것, 새 session에 로딩되는 것, 실제 기능이 실행되는 것은 별도 확인이다.

[공식 hook 문서](https://developers.openai.com/codex/hooks)에 따르면 비관리 hook은 해당 정의에 대한 trust가 필요하고 설치만으로 활성화되지 않는다. 일부 handler는 지원하지 않으며, callback 오류·timeout 등의 실패가 도구 실행을 막지 않는 경우도 있다. Stop hook의 추가 작업 유도도 제품 release gate와 같지 않다. 자동화의 기본은 직접 실행 가능한 검증 명령과 필요한 CI다. hook은 현재 host에서 지원과 실패 동작을 확인한 뒤 제한된 보조 연결로 사용한다. 무한 수정·재검증 loop를 만들지 않는다.

standalone skill과 plugin에 같은 기능이 함께 설치되면 중복 발견·버전 충돌을 확인한다. 설치 경로·소유자·버전을 명시하고 검증 없이 기존 설치를 지우거나 전역 설정을 바꾸지 않는다. plugin 전환에도 기존 독립 CLI/skill 소비자가 계속 쓸 수 있는지 확인한다.

## 15. 이식 순서와 완료 기준

| 단계 | 작업 | 완료 근거 |
| --- | --- | --- |
| 0. 방향 확정 | 최신 배포 기준으로 전환, 이 문서와 연구·후속 prompt 보존 | baseline·후보 SHA 구분, 문서 연결 검증 |
| 1. 배포본 정리 | 최신의 수정·HWP 보존, write-a-skill 제거 의도 좁게 재적용 | diff와 catalog/manifest·설치 경계 확인 |
| 2. 필요한 도구 이식 | 실행 캡처·Windows launcher·평가 소유 자원 정리 중 실제 소비자가 있는 변경 | native 정상/실패 대조와 해당 회귀 검사 |
| 3. 저장소 기능의 연결 검증 | Harness 사용자 Feature 몇 개와 기존 명령 연결, 필요한 경우 캡처 helper 사용 | 한 flow의 실제 관찰과 결함 대조, 잘못된 대상/미실행은 PASS 불가 |
| 4. 실제 프로젝트 적용 | 대상 프로젝트에서 UI 기준과 FE/BE/Domain/핵심 E2E 보완 | 실제 앱·저장·실패 상태 evidence, 기존 기준 재사용 |
| 5. Plugin 연결 | 검증된 CLI/설정을 얇게 패키징하고 현재 host에서 확인 | 설치·로딩·실행·충돌/실패 동작을 각각 확인 |

다음 세션의 중심은 1–3 단계에서 **최신 배포본 위에 필요한 도구를 이식해 직접 쓸 수 있는 토대**를 만드는 것이다. 다른 제품의 UI/API/DB 검증이나 전체 skill의 품질 비교, plugin의 일반 설치·배포까지 완료했다고 확대하지 않는다.

3단계에서도 사용자 관점의 Feature Map을 쓰되 evidence 범위를 `repository/harness`로 밝힌다. 파일 설치·work 기록 변경은 해당 기능의 파일시스템 side effect이며 외부 제품 DB 검증이 아니다. 관련 없는 FE·BE/API·DB 항목은 이유와 함께 해당 없음으로 표시한다. 4단계에서 대상 제품의 실제 항목을 채운다.

| 후보 원본 | 가져올 판단 대상 | 주의할 경계 |
| --- | --- | --- |
| `90437c6` | write-a-skill 공개 배포 제거 | 오래된 catalog 전체로 덮어쓰면 HWP가 사라짐 |
| `b40396a:skills/setup-project-verification/scripts/run_check.py`와 `tests/distribution/test_check_capture.py` | native 실행·첫 evidence 경로·실패 전달·timeout 기록 | setup-project-verification skill을 통째로 도입할 필요 없음. 대상/내용 보증 한계 유지 |
| `9d2139f`의 Impeccable launcher와 `test_impeccable_launcher.py` | Windows 전송 fallback·오류 노출·hash 거절·cache 재사용 | live 다운로드 성공으로 확대하지 않음. 임시 loopback fixture로 재검증 |
| `b40396a:tests/behavior/run_agent_eval.py`와 `test_eval_process_cleanup.py` | 세션 소유 프로세스 정리·timeout·실제 file-change 계수 | 평가 실행기가 실제 필요한 경우만. 현재 Windows 격리 실패 해결을 주장하지 않음 |
| 신규 5개 skill 및 기존 skill의 연결 문구 | 유용한 짧은 지식·전문 작업 범위 | 전체 설치를 기본으로 삼지 않음. 라우팅 설명·규칙 증식·미입증 품질 주장 보류 |

source→generated mapping, 최신 설치 경로/해시 수정, Harness result 방어를 보존한다. 최신과 후보의 manifest·generated core를 통째로 비교 복사하지 않는다. 도구 이식마다 실패 원인과 검증할 효과를 적고, 실제 consumer가 없으면 그 도구도 미룬다.

완료 보고에서는 소스 변경, 임시 설치 무결성, 실제 동작, Agent 행동 평가, 실환경 적용을 구분한다. 필요한 검사와 비용 대비 효과가 확인되기 전에는 규칙·skill·plugin 수를 늘리지 않는다. 이식 진행 후 이 문서의 구현 상태와 다음 세션 prompt를 갱신해 계획 문서가 현재 구현으로 오인되지 않게 한다.

## 16. 후속 구현에서 확정한 경계

`origin/main`을 다시 fetch하여 `e19134358141f901bb22c4af1aea17d7a9e2898c`가 유지됨을 확인했고, 준비된 `wp-20261004-agent-coding-foundation`에서 진행했다. 후보 브랜치를 병합하지 않았다. `write-a-skill`만 공개 배포에서 제거하고 HWP·최신 Harness runtime·cohort·hash/CI 수정은 보존했다. 일반 설치본은 변경하지 않았다.

실행 캡처는 `scripts/run_check.py`에 독립 CLI로 두었다. 새로운 Skill이나 generated core 변경 없이 repository adapter가 소비한다. `scripts/verify_product.py`는 단일 Markdown Feature Map과 기존 프로젝트 selectors를 읽고, 특정 실행의 run ID·Feature/check·argv/cwd·before/after/current Git 상태를 검사한다. 선택한 unittest의 유효한 성공 요약만 check 범위의 PASS로 해석하며 원본 `behavior_verdict`는 null이다. 0건, skip, 다른 대상, 미실행과 stale 상태는 PASS가 아니다. 편집 가능한 로컬 evidence의 진위, untracked 내용·dependency·fixture·server identity까지 인증하는 도구는 아니다.

Windows Impeccable은 아직 없던 전송 fallback·오류 노출만 이식했다. 기존 SHA-256 거절과 공유 version cache를 유지하고 cmd/Git Bash native fixture로 검증했다. 공개 release/TLS 다운로드 성공은 검증 범위 밖이다. Agent eval runner는 실제 모델 평가 consumer가 없어 보류했으며, 신규 5개 Skill·UI framework·범용 router·MCP도 추가하지 않았다. timeout의 Windows taskkill은 샌드박스에서 Access denied가 관찰됐고, 같은 native fixture는 허용된 도구 권한으로 실행해 소유 child 종료와 무관한 프로세스 보존을 확인했다. 제한된 환경의 cleanup 실패를 성공으로 바꾸지는 않는다.

플러그인 경계는 common capture CLI와 project-owned Feature Map/argv/업무 기준, repository-specific 판정 adapter로 나눈다. 공통 배포가 실제 필요해지면 현재 `authoring/resource-map.json` 방식으로 한 원본에서 산출한다. 플러그인에 프로젝트의 업무 기준을 복사하거나 다른 Skill의 private 경로를 참조하지 않는다. standalone CLI는 계속 직접 실행 가능해야 한다. 중복 설치·버전 충돌·generated 소유권을 package 설치/업데이트 검증에서 확인한다.

공식 [패키징 문서](https://developers.openai.com/plugins/build/plugins#bundled-mcp-servers-and-lifecycle-hooks)에서 root `plugin.json`의 OpenAI extension, `./` 상대 hook 경로와 기본 `hooks/hooks.json`, plugin root/data 환경변수를 재확인했다. [Hook trust 문서](https://learn.chatgpt.com/docs/hooks#review-and-trust-hooks)에 따르면 설치·활성화만으로 비관리 hook의 trust가 부여되지 않으며, 정의 변경 시 재검토가 필요하다. 로컬 `codex-cli 0.160.0`의 `plugin --help` 및 `plugin add --help`는 marketplace 기반 add/list/remove를 제공한다. 샌드박스에서는 CLI 임시 alias 경로의 접근 경고도 발생했다. 도움말 확인은 설치·로딩·hook 실행 검증이 아니다. 실제 프로젝트/host에서 설치 consumer를 확인하기 전에는 빈 local package를 만들지 않으며, hook 실패·timeout을 release gate로 의존하지 않고 직접 CLI/CI를 유지한다.

## 근거 탐색 경로

- 현재 구조: [docs index](../index.md), [Harness architecture](../architecture/harness.md), [공개 skill inventory](../architecture/skill-inventory.md), [프로젝트 설정](../../.harness/project.yaml).
- 실행과 영향 판단: [core_harness.py](../../authoring/scripts/core_harness.py)의 `select_impacted_checks`, `evaluate_result`; [testing policy](../../authoring/references/testing-policy.md).
- 설치·배포: [resource map](../../authoring/resource-map.json), [sync](../../scripts/sync-skill-resources.ps1), [test-install](../../scripts/test-install.ps1), [distribution validator](../../scripts/validate-distribution.ps1).
- PStack 원문과 source 고정 링크: [기존 조사](pstack-analysis.md). 이번 문서는 그 조사 및 선택된 소스 재검토를 활용했으며 전체 upstream을 새로 실험한 결과가 아니다.
- 이전 후보 세부 평가: `git show b40396a:docs/research/agentic-development-improvement.md`. 원본 실행 자료는 해당 기록에 기술된 `.work` 경로에 있을 때만 확인하며, 존재·재현성을 확인하지 않고 재사용하지 않는다.
