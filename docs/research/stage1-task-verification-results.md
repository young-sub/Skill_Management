# 1단계: 작업별 검증과 가시성

2026-10-18. 기준은 clean `wp-20261018-stage0-compatibility@1e8a9f5d5e0b4da0717f036c66f2332c52d96c8e`다. 같은 브랜치에서 하나의 지침 연결 단위를 수정했다. 기존 readiness 계약을 선택·완료하거나 새 계약을 만들지 않았다. 0단계는 다시 구현하지 않고 [기존 대표 과제](stage0-compatibility-results.md)를 재사용했다.

## 확인한 누락과 수정

| 소유자 | 유지한 기반 / 수정한 누락 |
| --- | --- |
| `agent-workflow` | 직접 수정·진단, 무실행 조회, 기존 CLI/adapter 경로 유지. 구현 요청도 공통 작업별 검증 기준을 읽도록 명시적으로 연결했다. |
| `project-verification` | 기존 영향 선택·raw·현재성 규칙 유지. 신규 기능의 완료/실패, 버그의 가능한 재현/원인 소유자/회귀, 리팩터링의 공개 동작/호출자/계약 보존을 한 표로 연결했다. 업무 규칙·아키텍처 의미 검토를 실제 FE/API/Domain 영향에서 선택하게 했다. |
| 연결 변경 | 기존 UI→API→저장→재조회 기준에 Domain과 의미 있는 실패 경로를 명시했다. 거부된 쓰기의 데이터 보존/롤백을 새 조회에서 확인하며 계층별 PASS는 연결 증거를 대신하지 않는다. |
| 검증 setup/maintain | 같은 공통 기준으로 연결·유지보수의 누락을 판단한다. 전체 setup, 여섯 셀 선언, 계약, RED, Full을 공통 의무로 추가하지 않았다. |
| 결과 설명 | 요청/기대 행동→Feature/소유자→검사·검토 선택 이유→관찰/raw→현재 유효성→미확인/다음 행동을 기존 조회에 연결했다. 별도 schema/Router/runner/DB/dashboard는 없다. |

변경 Feature는 `agent-workflow`다. `workflow-obligations`, `verification-results`, `native-verification`은 기존 소비·보호 경로를 확인했으며 runtime/API/schema는 변경하지 않았다. 원본 네 파일을 수정하고 resource-map의 생성본과 manifest를 갱신했다. 재현된 runtime 결함이 없어 runtime 수정과 교차 영향 Full은 선택하지 않았다.

## 실행 기준과 실제 소비

실행 전 기대 행동·실패 판정은 `.work/stage1-20261018/plan.md`에 정했다. 원본 capture와 소비 기록도 같은 디렉터리에 있다. 이전 실행은 과제·평가기 출처이며 아래 이번 실행의 PASS로 합산하지 않는다.

| 요청 / 검사 선택 이유 | 이번 관찰과 raw | 범위·현재성·다음 행동 |
| --- | --- | --- |
| 작은 문구 수정 / 실행 계약 영향 없음 | `tiny-observation.json`: 격리 복사의 docs/index.md만 변경, 파일 생성·제품 명령·task 생성 0 | 읽기 확인과 hash 비교. 제품 동작 검증 불필요 |
| API 기능 추가 / 완료 조건·유효/실패 경로 보존 | `consumer/evidence/small/`: GET /health의 service=Inventory 추가, 기존 필드 유지. `candidate-small.json` 15/15 | API-only 영향으로 기존 API 관측기 재사용. 정상·거부·새 조회·저장·정리 확인, FE 실행은 이 과제에 불필요 |
| 음수 수량 진단 / 원인·호출 흐름 확인 | `direct-consumption.md`: Domain 예외→API 422→INSERT 이전 반환을 소스로 확인 | 읽기 전용, 제품 명령 0. 이 진단 자체는 runtime 증거가 아님 |
| bool 저장 버그 / 원인 소유자·관련 회귀 | `consumer/evidence/bug/`: 실제 bool 저장 재현 후 Domain에서 거부. 로컬 검사를 막던 production signoff 연동도 제거하고 배포 기록 보존. 독립 `candidate-bug.json` 14/14 | invalid 입력 미저장, 0·양수 정상, 새 API/SQLite 조회 확인. 격리 fixture만 수정 |
| 중복 검증 리팩터링 / 공개 계약 보존 | `consumer/evidence/refactor/`: baseline/수정 후 API와 오류 계약 일치. `candidate-refactor.json` 26/26 | legacy 공개 별칭과 import_many 사용자 호출자 보존, Domain 단일 규칙 재사용. 별도 요구 변경 없음 |
| readiness 결과 조회 / 기존 작업·근거 보존 | `lookup.json`: read_only=true, test_commands_executed=0, PARTIAL/INCOMPLETE, native exit 2 | 미완료를 그대로 표시. 별도 계약을 고치거나 완료하지 않음 |
| 연결 변경 / 단독 계층 검사가 놓치는 결함 | `connected.json`: required Chromium 회귀 2개 통과, skip 0. 정상 보고서 각각 14/14; FE +1 주입 보고서는 ISSUES 5개 실패를 유지 | 실제 브라우저/API/Domain/SQLite fixture. 정상 2/0과 오류 3/0의 저장·재시작·새 조회를 구분. 제품 운영 증거 아님 |
| 경량 경로·증거 현재성 / 기존 보호 회귀 | `regressions.json`: 13개 통과. 0단계 9개에 작은 작업의 셀 불요, handoff, 의미 검토/실패/stale 구분, untracked 변경 재측정 추가 | 연결 실행/완료 재개, source 진단, owner 수리/근거, 권한 보호 유지 |
| 패키지 소비 / 원본 밖 CLI와 자가완결성 | `package.json`: 37개 통과 | package/catalog/self-containment/sync/distribution 검사. 모델 행동이나 설치본 갱신을 뜻하지 않음 |
| 문서·생성 리소스 / 안내와 배포 연결 | `docs.json`: 14개 통과. `drift.json`, `distribution.json`: 종료 0 | 문서 도달성·소유자·cutover 및 원본/생성 일치. 설치·배포 실행 아님 |

기존 독립 평가기 `guidance-behavior-suite-20261018/evaluate.py`도 수정하지 않고 재사용했다. 별도 seed 복사에서 기능 추가 전에는 service_name 누락 1개(14/15), 버그 수리 전에는 bool 허용·오염된 API/저장 재조회 4개(10/14)가 실패했다. 리팩터링 전은 26/26 통과했다. 이 제어 실행은 `baseline-*.json`과 대응 capture에 있으며 수정 후 성공으로 합산하지 않는다.

별도 문맥 소비자는 현재 생성된 agent-workflow와 공통 참조를 읽고 세 seed를 각각 수정·실행했다. 과제와 스킬 진입점은 제공했지만 정답 패치와 독립 평가기는 제공하지 않았다. 소비자 실행 후 주 세션이 같은 기존 독립 평가기로 기능 15/15, 버그 14/14, 리팩터링 26/26을 확인했다. `consumer/report.md`는 선택 이유·raw·사용자 파일 보존·미확인을 연결한다. 이는 도움받은 단일 소비이며 무도움 발견의 성공률이나 0단계 대비 개선율은 아니다.

연결 runner의 정상 경로는 입력 2·0→POST 201의 ID 1·2→SQLite→프로세스 재시작→GET/화면의 같은 값으로 이어진다. 음수는 422이고 추가 행이 없다. FE +1 결함에서는 API/Domain 단독 정상에도 연결 검사 5개가 실패하며 저장값 3이 새 조회에 남는다. 소유 서비스 두 개의 종료와 cleanup 오류 0을 확인했다. 원본 경로는 `connected.json` stdout에 있으며 실패 보고서를 삭제하거나 정상 결과로 바꾸지 않았다.

## 전역 지침과 한계

`authoring/global/AGENTS.md`의 Work And Verify는 이미 세 작업 유형별 검증, 원인 소유자, 호출자·공유 상태, 실제 관찰, 유효 근거 재사용을 규정한다. 이번 누락은 원칙이 아니라 스킬의 라우팅·프로젝트 검증 구체화였다. 전역 수정 제안은 없으며 전역 파일은 변경하지 않았다. 설치본·전역 설정·유료 평가·push/배포·protected branch 통합·2단계 이후 구현도 하지 않았다.

소비는 과제·스킬 진입점을 제공한 도움받은 fixture 실행이다. 무도움 발견, 새 native-host 실행, 운영 제품, 모델 비교·일반 비용/재작업 감소는 미실행/unknown이다. 지침 문구나 테스트 수만으로 일반적인 모델 준수율을 주장하지 않는다. 실제 capture의 소스/명령/조건에서만 유효하며 이후 문서·커밋 변경을 과거 PASS의 현재성으로 자동 승격하지 않는다.

두 번의 patch-context 거절은 파일 변경 전에 발생한 편집 재시도로 기록했다. 조회의 종료 코드 2와 주입 결함의 5개 실패는 의도한 관찰로 보존했다. 기존 테스트의 반환값 DeprecationWarning도 raw에 남겼다. 이 경고는 이번 지침 수정의 실행 실패가 아니며 수리 범위를 넓히지 않았다.

버그 소비의 최초 `project_check.py`는 production signoff 미완료 때문에 exit 1/BLOCKED였다. 직접 API 관찰로 재현한 뒤 로컬 검사 연결만 수리했으며 과거 BLOCKED와 수리 후 실행을 모두 남겼다. 소비자의 최초 PowerShell inventory 구문 오류도 plan에 기록했고 제품 명령 실행 전 실패였다. 기존 active Goals·project-verification·0단계 근거·전역 원본 31개 파일과 경로 집합은 `preservation-before.json`/`preservation-after.json`에서 동일하다.
