# 0.1.69 업무 흐름 개선 결과

2026-10-17 실행 기록이다. [현재 설계](agent-coding-system-direction.md)를 대체하지 않는다. 출발점은 현장에서 확인한 clean `main@ea7e11d828d00fb05065a7c88f509cac013bea05` / 0.1.68이다. 구현은 전용 branch `wp-20261017-workflow-improvement`의 `df3a23c861470dc2b5389d92a561c6ede1db9e6b`에 있다. 실제 소비 후 예방 연결을 먼저 점검하도록 공통 가이드를 보완한 커밋은 `4cbc320`이며 런타임 변경은 없다. 최종 로컬 통합/정리 관찰은 아래 evidence root의 `delivery.json`에 남긴다.

## 실제 달라진 업무

작은 요청에서 전체 프로젝트의 미선언 여섯 셀과 변경하지 않은 미매핑 파일 때문에 생기던 완료 차단을 재현하고 제거했다. 미선언 범위는 여전히 미확인이며, 명시한 요구·필수 검사·이번에 바꾼 미매핑 경로는 계속 차단한다. 현재 요청의 다음 행동과 프로젝트 잔여를 분리해 전달한다. 등록된 UI system이 있는데 중복 Feature UI 선언을 요구하던 경로도 고쳤다.

구조·타입/제약 예방은 실제 원인 소유자, 원래 실패, 우회 경로, 가까운 정상 사용을 기존 실행 캡처와 의미 검토로 연결할 수 있다. 자동 검사 예방의 고정 기준 RED/GREEN 경로는 유지했다. 동일 코드의 stage/commit만으로 증거가 무효화되던 문제를 고쳤고, 실제 소스·기준·근거 변화는 재검토를 요구한다. 이 검토는 Agent 판단이며 편집 가능한 로컬 파일을 실행 인증이나 보호 host 수락으로 승격하지 않는다.

기존 `agent-workflow` 진입점에서 선택된 Feature와 소비하는 UI 기준을 우선 발견하고, 생략된 항목에는 상세 경로를 남긴다. 실제 격리 제품에서 공유 포커스 기준 변경 후 새 문맥의 후속 작업이 같은 기준과 runner를 발견했고, 직원 PIN 해제 뒤 제목으로 키보드 포커스가 이동하지 않는 실제 결함을 찾았다. 무도움 native 발견이나 일반적인 Agent 생산성 향상으로 해석하지 않는다.

## 여섯 목표와 근거

| 목표 | 구현·관찰 | 남은 경계 |
| --- | --- | --- |
| 1. 무엇을 왜 검증했는지 이해 | 현재 요청/프로젝트 잔여, 필수 검사/현재 재사용 상태, 이유와 다음 행동을 구분한다. 고정 패키지 조회는 제품 명령 0회, 상태·기존 근거 불변이었다. | 결과의 의미를 사용자가 이해했는지 사용자 평가를 수행하지 않았다. |
| 2. 업무 규칙·아키텍처와 관련 계층 | 범위는 영향 지도이며 공통 여섯 검사 양식이 아니다. 연결 fixture에서 UI 입력 → API → Domain → SQLite → 서비스 재시작 후 조회를 확인했다. UI payload만 잘못된 대조군은 Domain 단독 검사 통과에도 연결 검사가 실패했다. | fixture는 실제 제품의 모든 업무 규칙·사업 가치·사업 성과를 증명하지 않는다. |
| 3. 원인 소유자와 재발 예방 | 실제 플러그인 과잉 차단을 baseline에서 재현하고 runtime와 hook의 공통 소유자를 수리했다. 구조 예방 연결, 같은 bytes 커밋, 다음 요청 재사용을 확인했다. 원인 코드를 되돌리면 OPEN과 실제 실패로 돌아왔다. | 임의 캡처의 의미적 진실성은 자동 인증하지 않는다. 현재 요청의 미실행 필수 검사를 과거 예방으로 대체하지 않는다. |
| 4. UI 가이드와 코드 재사용 | 격리 제품의 공유 포커스 구현을 변경하고, 잘못된 PageHeading 문서 참조를 실제 h1 소유자로 고쳤다. 새 문맥이 Feature Map → guide → 공유 코드/기존 browser runner를 발견해 후속 결함을 재현·수리했다. | 진입점 경로를 제공했다. native 발견·hook 전달, 사용자 시각 승인, 다른 제품에서의 일반 재사용은 미검증이다. |
| 5. 실행 기반 검증 가이드 | 기존 runner/parser를 사용했다. 브라우저와 연결 소비 가이드를 실제 실행해 절대 output 경로와 cleanup/보존 절차를 보완했다. fixture의 서비스·브라우저 종료, scratch DB 정리, raw/artifact 해시를 확인했다. | 기존 직접 제품 브라우저 raw와 TaskStore 연결 캡처는 다른 증거다. 제품 전체 TaskStore 완료로 보고하지 않는다. |
| 6. 유효 검사 유지와 절차 축소 | 현행 설계 하나와 짧은 실행 지시서로 통합했다. 반복 Skill 설명과 폐기된 여섯 셀 강제 완료 요구를 줄였다. 알려진 필수 미실행·오래된 근거·상태 충돌·중복 효과·실제 변경 누락 보호는 유지했다. | 추가 실행 검사 삭제는 동등 결함 검출/정상 허용 근거가 부족해 하지 않았다. 비용·개입·재작업 감소의 일반 수치는 측정하지 않았다. |

## 문서·지침 정리와 소유권

현재 설계/실행 지시서/index/testing을 현행 안내로 정리했다. 과거 next-session·중복 설계/검토 여섯 문서와 기존 혼합 문서의 보존본은 [아카이브](archive/index.md)로 연결했다. 고유 결정과 기존 인바운드 링크를 보존했고 raw evidence·사용자 작업 기록은 삭제하지 않았다. 현재 문서의 반복 실행 지시를 아카이브 기록으로 바꾸었으며 문서 수 감소를 효과 지표로 사용하지 않는다.

`authoring` canonical을 수정하고 resource-map 생성 사본을 갱신했다. TaskStore, 공개 API, 절대 state, 캡처 원자성, 읽기 전용 조회 등 [0.1.68 해결 사항](core-hardening-results.md)을 새로 구현하지 않았다. 새 Router·대형 DB·dashboard·범용 runner/parser·의존성은 추가하지 않았다. pstack은 고정 리비전의 소유권·예방·실행 기반 갱신 방향만 참고했고 원문 코드를 재배포하지 않았다.

## 실행 근거와 실패 기록

이 절의 경로는 모두 저장소의 `.work/workflow-improvement-20261017/` 아래이며 이번 실행이다. 과거 기록은 비교 출발점으로만 사용했다.

| 실행 | 결과와 해석 | 보존 위치 |
| --- | --- | --- |
| 범위/예방 초기 재현과 집중 회귀 | 과잉 차단을 RED로 관찰한 뒤 GREEN. 중간 119개 회귀 통과 이후 review에서 실제 호출부 누락을 더 발견해 수정했다. | `scope-{red,green}.json`, `prevention-{red,green}.json`, `workflow-focused-02.json` |
| 독립 검토 후 실제 호출부 회귀 | host 주입 inventory와 일반 local hook을 구분하고, source roots 밖의 새 변경을 검출했다. 과거 해결된 feedback이 현재 구조 수리를 막는 조건도 수정했다. | `review-gaps-*.json`, `caller-gaps-{red,green}.json` |
| Full | `CONNECTED_PRODUCT_REQUIRED=1 python -m unittest discover -s tests -p "test_*.py"`: 481 tests OK, 1022.306초. 실행 전후 source snapshot 일치. | `full-final.json` |
| Full 이후 좁은 보정 | 동일 bytes stage/commit이 구조 예방을 재개방하던 문제를 수정했다. stage/commit 허용, 새 source 변경 차단 및 기존 자동 예방 회귀 3개 통과. Full 결과를 이 후속 diff의 Full로 표시하지 않는다. | `commit-reuse-{red,prototype,green}.json` (prototype은 제품 증거 아님) |
| 리소스/배포 | `sync-skill-resources.ps1 -Check`, `validate-distribution.ps1`, `git diff --check` 통과. clean commit에서 0.1.69 패키지 생성. | `resource-final.json`, `distribution-final.json`, `frozen-package-verification.json` |
| 고정 패키지 연결 fixture | 정상 14/14, UI defect 대조군 9/14로 결함 검출. 양쪽 Domain 단독 exit 0. 조회 재실행 0, 소스 변경은 STALE. 서비스·브라우저·scratch DB 정리. | `runs/final-connected/report.json` |
| 고정 패키지 실제 플러그인 소스 소비 | baseline 과잉 차단 RED → 두 원인 소유자 수리 GREEN → feedback RESOLVED → 읽기 전용 조회 → 동일 bytes commit 유지 → 후속 요청 재사용 → 원인 되돌림 OPEN/실패. 다른 저장소 의무 미실행으로 task는 PARTIAL. | `runs/final-structural-02/report.json` |
| 실제 격리 제품 첫 업무 | 새 공유 포커스 기준에 기존 3px가 실패; 공유 구현/기존 assertion/가이드 수리 뒤 browser 7 suites PASS, 키보드/포인터 134 screenshots, source/served snapshot 및 cleanup 확인. 격리 제품 commit `dbdd7d7`. | `product-initial-result.md`, `product/.work/tasks/33cad3e6-9a7c-40c6-b831-e24f3e9649d6/` |
| 실제 격리 제품 새 문맥 소비 | 직원 PIN 진입의 포커스 handoff 누락을 독립 재현하고 기존 App의 effect 의존성 소유자를 수리했다. 최종 frozen capture exit 0, source 전후 동일, browser 7 suites PASS, 136 artifacts 해시·cleanup 확인. 구조 예방 feedback RESOLVED와 전체 task PARTIAL을 분리했다. | `product-followup-result.md`, `product-root-review.json`, `product/.work/staff-keyboard-feedback-20261017/` |
| 소비 후 지침 보완 | 구조 예방의 config/guardrail link와 owner를 실행 전에 audit하고 최종 source/criteria/config 고정 후 캡처하도록 순서를 명확히 했다. 카탈로그/자체 포함 10 tests, 리소스 drift, 배포 검사 통과. | `guide-consumption-regression.json`, `guide-resource-check.json`, `guide-distribution-check.json` |

초기 Full은 최종 호출부 누락 발견 후 소유한 테스트 프로세스만 중단했으므로 PASS가 아니다 (`full-01-disposition.json`). sandbox에서 기존 두 timeout/process cleanup 검사가 실패했고 동일 검사를 process-tree 접근 권한으로 재실행해 통과했다 (`full-environment-{diagnosis,authorized}.json`). 최종 Full은 그 권한 경계에서 수행했다. 진단 scratch 일부를 `environment-failure-artifacts/`에 보존했고 기존 Temp를 일괄 삭제하지 않았다.

첫 frozen 구조 소비는 helper가 runtime만 복사하고 결합된 hook 수리를 누락해 실제 hook 검사가 실패했다. helper만 바로잡아 같은 고정 패키지로 다시 실행했다. 실패 `runs/final-structural/`, 당시 helper snapshot과 성공 `final-structural-02`를 함께 보존했다. 후보 connected의 상대 output 경로 문제는 절대 경로 지침으로 수정하고 정확한 소유 산출물만 보존 위치로 옮겼다 (`candidate-connected-relocation.json`). 실패·도움·재시도를 성공 분모에서 숨기지 않는다.

새 문맥 소비에는 격리 제품과 Skill 진입점 경로 및 자연어 요청을 제공했고 정답 패치·token명·CLI 순서는 제공하지 않았다. 실제 가이드/코드/runner 발견과 결함 수리는 독립 수행했지만, 초기 OPEN에서 멈추지 말고 기존 예방 경로까지 마무리하라는 후속 지시를 받았다. 두 잘못된 CLI 경로, 지원하지 않는 feedback 옵션, 누락된 구조 예방 필드를 바로잡는 과정과 직접 browser GREEN 뒤 두 차례 캡처 실행을 보존했다. 늦은 config 보완이 첫 캡처를 stale로 만든 비용은 실제 발생했다. 공통 가이드의 preflight 순서 보완이 다음 새 문맥에서 그 비용을 없애는지까지는 아직 관찰하지 않았다.

제품 수리는 격리 branch의 `bb99fbb`에 커밋했다. 같은 bytes 커밋 후에도 feedback는 RESOLVED였고 새 UI 요청 `26d47b77-8b91-44bd-b966-554809d3b85d`가 그 원인/예방/binding을 상속했다. 조회는 `read_only=true`, 제품 명령 0회였다. 새 요청 자체는 PENDING으로 남으므로 과거 수리가 다음 업무 전체를 자동 완료하지 않는다. 첫 업무와 이 후속 업무 모두 제품 원본에 통합하지 않았다.

worktree의 Full/연결 검사 산출물 68개는 `worktree-retained/`에 byte 그대로 복사하고 `worktree-evidence-retention.json`에 원래 경로와 hash를 남겼다. 원시 보고서의 절대 경로를 다시 쓰지 않았다. 작업 worktree 제거 후에도 이 매핑으로 근거를 찾을 수 있다.

## 패키지와 재개 경계

소비에 사용한 고정 패키지: `.work/workflow-improvement-20261017/frozen-0.1.69/`. clean source `df3a23c861470dc2b5389d92a561c6ede1db9e6b`, tree `c3b2225bff9064a7a9ebeeb4bbba02dafde3ba32`. 19 skills, 253 files. `package-files.json` SHA-256 `b9198713d5bbc8bbc39991571cfa821998d4fd5c3f29051cbd7332f97e38de5b`; 소비 후 payload 전체 hash/파일 집합을 확인했다. 후보 패키지는 별도 과거 dirty snapshot이며 고정 패키지를 대신하지 않는다.

최종 전달 패키지는 지침 보완을 포함한 별도 불변 디렉터리 `frozen-0.1.69-final/`로 빌드한다. `build-origin.json`이 clean source commit을, `package-files.json`이 payload를 고정한다. `final-package-verification.json`에서 소비 패키지와의 차이가 지침 사본·manifest·build origin에 한정되는지와 모든 실행 코드의 byte 일치를 확인한다. 이전 패키지의 실제 제품 실행을 새 패키지의 재실행으로 표시하지 않는다. 같은 코드의 제품 명령을 다시 실행하지 않고 최종 패키지의 읽기 전용 소비와 근거 불변을 확인한다.

미검증: native Skill 발견·hook 전달·보호 host 수락, hosted CI, 사용자 UI 승인, 일반적인 업무 효율·비용 효과. 필요한 실제 host/session과 별도 권한이 준비되면 동일 고정 패키지로 해당 경계만 확인한다. 설치·전역 설정·다른 제품 원본·자격증명·push/publish/deploy/유료 실행은 변경하거나 실행하지 않았다.

모델 비교 벤치마크는 채택 결정을 바꾸지 않아 수행하지 않았다. 새 문맥 실험의 실제 model/reasoning/usage/cost는 수집되지 않아 unknown이다. 제품 업무는 격리 복사본에만 반영했고 제품 원본 통합이나 전체 제품/플러그인 완성을 주장하지 않는다. 다음 개선은 [실행 지시서](plugin-continuous-improvement-next-session.md)의 실제 미확인 경계와 새 재현에서 선택한다.
