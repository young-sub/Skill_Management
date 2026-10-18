# 2단계: 인간의 교정과 성공 절차 재사용

2026-10-18. 시작점은 clean `wp-20261018-stage0-compatibility@5e8de29`이며
1단계 `0e12642` 위에 하나의 지침·배포 연결 단위를 구현했다. 별도 readiness
계약을 선택·수정·완료하지 않았다. 실행 전 판정은
`.work/stage2-20261018/plan.md`, 원본 소비·검사 근거는 같은 디렉터리에 있다.

## 구현과 소유권

- `agent-workflow`의 설명·라우팅에 인간의 방향 교정, 좋은 판단, 만족한 턴·결과물의
  절차 추출을 연결했다. 작은 진입점은 기존 스킬 안에 두고 `reflect`를 신설하지 않았다.
- `diagnose`는 첫 명확한 교정부터 기존 feedback/prevention으로 연결한다.
  원인 소유자의 구조→타입/제약→자동 검사→최소 문서와 원래 실패·우회·정상·후속
  소비를 사용한다. 기존 규칙을 놓쳤다면 발견·충돌 경로를 고친다.
- 공통 [교정·성공 재사용](../../authoring/references/feedback-and-success.md)은
  지속적 판단 교훈, 명시적인 재사용 요청, 단순 칭찬, 일회성 예외를 구분한다.
  [절차 템플릿](../../authoring/templates/reusable-procedure.md)은 호출·필수 입력·준비·도구·순서·결과·검증·실패·예외를 필요한 만큼 남긴다.
  기존 소유자를 먼저 수정하고 독립 절차에만 호스트의 기존 작성 도구를 사용한다.
- 원본과 생성본, manifest, 패키지 안내, Feature Map과 기존 Feature source 연결을
  갱신했다. 공개 catalog는 기존 19개 그대로다. 설치 cohort가 새 diagnose 리소스를
  거절하는 실제 cutover 실패를 확인해 `REQUIRED_COHORT_RESOURCES`에 세 경로를
  추가했다. 실행 로직/API/schema, 설치본,
  전역 지침·설정, 새로운 학습 DB·runner·계약 체계는 변경하지 않았다.

변경 Feature는 `agent-workflow`, `feedback-repair`와 설치 리소스 목록의 `harness-core`다.
runtime 변경은 재현된 패키지 거절의 허용 목록 세 항목뿐이며 호출·상태 전이·공개 API는
그대로다. 영향은 cohort 설치/검증에 한정돼 설치·격리 CLI·cutover를 선택했으며
`shared_runtime` 경고만으로 Full을 선택하지 않았다. 기존 `skill-creator`의
기존 스킬 우선·자가완결성·실제 소비 검증 절차를 사용했다. 새 스킬 생성이나 설치는 없다.

## 실제 소비와 판정

| 사례 | 실제 관찰 / 근거 | 범위 |
| --- | --- | --- |
| 첫 교정: true를 수량 1로 저장하지 말 것 | `correction-report.md`, `correction/.work/correction-before.json`에서 HTTP 201·SQLite 1을 재현. Domain의 bool 제외 후 `correction-after.json`에서 422·미저장, 0/2/7은 저장·재조회 유지 | 제공한 Skill 진입점의 도움받은 격리 소비. 원인 수리와 회귀는 fixture 내부에만 있음 |
| 다른 호출·정상 흐름 | 직접 Domain 회귀와 실제 Chromium 14/14, 저장·history·재시작 후 `[2,0]`, cleanup 오류 없음. 고정된 기존 독립 평가기는 `correction-verdict.json`에서 14/14 | API/Domain/SQLite/브라우저 fixture. 운영 제품 증거 아님 |
| 교정 후 새 문맥의 관련 요청 | `followup/followup-report.md`, `raw/run-20261018-quantity-values-retry1/results.json`: true/false 직접 호출 TypeError, API 422·새 조회 빈 저장소; 0/9는 201 후 `[0,9]`. 18개 관찰과 기존 Domain 3개 검사 통과, fixture 소스 변경 없음 | 수리된 소유자와 기존 프로젝트만 제공. 첫 검사기 시도의 mutable 기대값 오류와 수정 후 별도 DB 재실행을 모두 보존 |
| 성공한 설명 방식 추출 | `extraction/project/docs/`의 기존 인계 가이드를 보강하고 템플릿·index 연결. `extraction/report.md`에 기존 규칙·칭찬·이번만 예외·제작 이력 불명 사례의 판단과 수정 내용을 보존 | 만족은 명시적으로 합성 acceptance 조건. 실제 사용자의 새 승인이라고 주장하지 않음 |
| 원자료를 사용한 별도 문맥 소비 | 추출 소비자의 추가 소비는 제공된 14/14 요약을 인계하며 없는 raw를 미확인으로 표시 | 도움받은 원자료 소비. 새 입력 재현과 별도로 기록 |
| 다른 자료의 새 문맥 소비 | `reuse-project/handoff.md`: BLOCKED 0개, FAIL 4/5, PASS 5/5를 모두 보존. 거부 전후 행 수 2, 정상/새 조회 `[0,9]`, 원인별 재시도, 정확한 JSON 포인터, 미실행·비용 null·합성 자료 한계를 표시 | 이전 대화·패치 없이 짧은 요청, 프로젝트 index, 새 observations만 제공. 인계문 제작은 실제 실행, 입력의 제품 관찰은 합성 데이터 |

추출 소비자는 단순 칭찬에 별도 규칙을 추가하지 않았고, 영어 요청을 한 보고서의
예외로 남겼다. 기존 실패 보존 규칙은 새 규칙으로 복제하지 않고 index 발견을
수리했다. 제작 이력이 없는 결과물은 검증된 제작 절차로 추정하지 않았다.
새 입력 소비의 최종 산출물을 직접 읽어 실행 전 기준과 대조했다. 소비자는
가이드·템플릿·입력만 읽었고 제품 명령 0회였다. 한 사례의 성공으로 일반적인
준수율·재작업/비용 감소나 무도움 발견을 주장하지 않는다.

교정 소비자의 RED/GREEN unittest stdout은 별도 raw 파일이 아니라 도구 대화에
남아 있다. 원래 실패·수리 후 API JSON, 브라우저 raw, 주 세션의 독립 평가와 후속
소비의 검사 로그는 파일로 보존했다. 첫 소비자가 상위 Git status의 파일명 목록을
본 점도 완전한 blind 실험과 구분한다. 원인 패치나 평가기는 제공하지 않았다.
`ui.js`의 이상 표시는 터미널 인코딩이었고 실제 UTF-8·구문과 원본 bytes가 정상이라
수정하지 않았다.

## 선택적 pstack 참고

로컬 조사본 `pstack-review/installation.json`의 0.15.25 리비전
`101b274dd991f694e1f7024be2157e5f3adf07de`를 고정했다. correct, reflect,
reflect의 synthesizer, automate-me 네 파일의 SHA-256이 그 manifest와 일치한다
(`pstack-pin.json`). 이는 로컬 고정 조사본 확인이며 새 원격 검증은 아니다.
구조적 예방, 오래 유효하고 다음 결정을 바꾸는 교훈, 기존 스킬 우선과 짧은 재사용을
선택적으로 비교했다. 원문을 재배포하지 않았다. 원본은 Lauren Tan / MIT다.
두 번 실수해야 시작하는 조건, 고정 리뷰어·모델, 일률적 재승인·PR, 개인 mode,
대화 전수 수집·외부 backlog 등록은 가져오지 않았다.

## 검증과 보존

| 검사와 이유 | 이번 결과 / capture |
| --- | --- |
| feedback 구조·현재성·후속 계승, 정상 예외, 경량 진단·작업·재개 | 8개 통과, `focused-feedback.json` |
| 무실행 조회·미설정 작은 작업 | 2개 통과, `lookup-regressions.json` |
| 문서·설치 cohort·격리 CLI·cutover·기존 보존 | 44개 통과, `cohort-final.json` |
| catalog·자가완결성·생성·배포·패키지 실행·설치 CLI | 추적 파일 등록 후 44개 통과, `package-tracked.json` |
| 원본/생성 drift·배포 검사 | 각각 종료 0, `drift.json`, `distribution.json` |
| 기존 작성 도구의 frontmatter 검사 | agent-workflow/diagnose 모두 valid; 구조 검사이며 소비 증거와 별개 |

검사별 stdout/stderr·종료 상태를 확인했으며 package와 모델 소비를 분리한다.
배포 검증과 임시 디렉터리의 설치 테스트는 실제 설치본 갱신·배포가 아니다.
검사 중 문서만 후속 편집한 경우 실행 로직·기준 불변 범위에서 관찰을 재사용하며
전체 checkout 현재성이나 기존 readiness의 검증으로 승격하지 않는다.

실패·재시도도 보존했다. 처음 두 feedback 모듈 전체를 실행한 capture는 기본
300초 제한으로 timeout, cleanup의 taskkill은 access denied였다. 이후 소유
프로세스의 종료를 관찰한 뒤 직접 관련된 8개를 선택해 실행했다. 전체 모듈 실행은
완료/PASS가 아니며 부분 출력의 점 개수를 성공 건수로 집계하지 않는다.
초기 cutover는 새 리소스 세 경로의 허용 목록 누락으로 2개 실패했다.
목록 수정 후 동기화가 일시적 user-mapped file 잠금으로 중단됐고, 아직 이전 생성본을
사용한 격리 CLI 검사는 1개 실패했다. 해당 실행 종료 후 동기화를 재시도해 성공하고
cohort 회귀를 다시 통과했다. 처음 패키지는 Git 추적 파일만 묶기 때문에 새 리소스
안내 링크가 누락돼 실패했다. sandbox의 Git index 쓰기 거절 뒤에도 잘못 이어 실행한
동일 실패 1회도 `package-staged.json`에 남겼다. 허용된 Git staging 후 패키지가
새 파일을 포함하면서 통과했다. 이를 runner 결함으로 바꿔 고치지 않았다.

두 번의 patch-context 거절, UTF-8 문자열이 맞지 않아 치환되지 않은 무변경 편집,
읽기 전용 프로세스 CIM 조회의 access denied도 발생했다. 기존 DeprecationWarning은
raw에 남겼다. 후속 검사기의 최초 저장된 기대값 오류는 최종 근거에서 제외하지만
시도 분모에서는 유지한다. 이를 제품 결함이나 성공으로 집계하지 않는다.
기존 active Goals·project-verification·0/1단계 증거·전역 원본 235개 파일은
`preservation-before.json`/`preservation-after.json`에서 동일하다.

설치본·전역 설정 변경, 유료 모델 평가, push·배포·protected branch 통합,
3단계 이후 구현은 수행하지 않았다. in-app browser는 기존 manual disable을
유지했고 fixture의 기존 Playwright 경로를 사용했다. native-host·운영 제품·무도움
발견은 미실행이다. 사용량·비용은 수집하지 않아 unknown이다.
