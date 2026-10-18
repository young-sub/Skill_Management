# 4단계: 설계 판단과 변경 영향

2026-10-18. 시작점은 clean `wp-20261018-stage0-compatibility`의
`be6f92a24b2c04175c53055181fbb15c47d33559`다. 같은 브랜치에서 하나의 결합된
스킬·공통 참조·배포 연결 단위를 구현했다. 실행 전 기준과 실제 근거는
`.work/stage4-20261018/plan.md`와 같은 디렉터리에 보존한다.
별도 `20261018-plugin-readiness` 계약을 선택·수정·완료하지 않았다.

## 구현과 책임

- `architect`는 기술 설계 판단을 담당한다. 실제 호출자·입출력 타입·상태와
  데이터 소유권·모듈 의존·오류/트랜잭션 경계를 조사하고 구현·회귀로 확인한다.
- `design-goal`은 Items·의존성·권한·완료 조건의 작업 계약을 관리한다.
  두 스킬은 서로의 필수 선행 조건이 아니며 작은 수정에 설계 문서나 계약을
  요구하지 않는다. 설계만 요청하면 읽기 전용이고 구현이 승인되면 계속한다.
- [공통 영향 분석](../../authoring/references/change-impact.md)은 `architect`,
  `agent-workflow`, 검증 setup/maintain, `multi-agent-review`에 같은 원본으로
  배포된다. 기존 구조·도구와 원인 소유자를 우선하며 새 추상화·의존성은 실제
  필요로 판단한다. 기존 오류 처리·경계 검증·저장 데이터 보존을 유지한다.
- catalog는 20개다. 원본/생성본·manifest·패키지 안내·Feature Map·source 연결을
  갱신했다. Feature는 `architecture-design`, `agent-workflow`, `work-design`,
  `independent-review`다. 공통 runtime/API/schema는 변경하지 않았다.

## 실제 소비

아래 결과는 격리 fixture 소비다. 패키지 검사는 별도이며 운영 제품·native-host
무도움 발견·모델 비교나 일반 비용 절감의 증거로 확대하지 않는다.

첫 소비자에게 새 `architect` 진입점과 기존 connected-product 복사, 일괄 저장
요구를 제공했다. 요구는 1~20개 수량을 모두 검증한 뒤 한 트랜잭션으로 저장하고,
하나라도 잘못되거나 저장 중 거절되면 어떤 행도 추가하지 않는 것이다.
정답 패치·독립 검사기는 제공하지 않았다. 이는 **도움받은 소비**다.

소비자는 `ui.js`의 단건 호출, API 입력/오류 변환, `domain.validate_quantity`의
타입·수량 규칙, SQLite 저장과 트랜잭션 소유자를 추적했다. 별도 서비스나 규칙을
만들지 않고 기존 `Handler.do_POST`에 batch 계약을 추가했다. Domain·UI·DB schema는
그대로며 실제 변경은 `app.py`, `test_domain.py`, acceptance/Feature 문서다.
설계 판단은 기존 작업 보고서에 남겼고 Harness 계약은 만들지 않았다.

| 검사 / 선택 이유 | 이번 관찰과 근거 |
| --- | --- |
| 미구현 기준선 / 새 기능 검출 | `baseline-oracle-retry/results.json`: 32개 중 15개 실패. batch 경로 부재를 정상으로 처리하지 않음 |
| 독립 API·저장·재시작 / 타입·원자성·호출 계약 | `candidate-oracle/results.json`: 32/32. `[0,2]` 저장, bool/음수/string/float/null·빈/초과 batch 거부, 중간 INSERT 거절 후 전체 rollback, 기존 단건 422 문구·0 저장·GET/재시작 유지 |
| 직접 Domain과 API 회귀 | `complex/project/.work/complex-batch-20261018/domain-final.log`: 4개 통과. 원래 Domain 기준 2개도 변경 전 통과 |
| 기존 UI 소비 / 변경된 공통 POST의 기존 호출자 | 같은 디렉터리 `ui-acceptance/browser.json`: 실제 Chromium 16/16, skip/error 0. 화면 입력→API→Domain→SQLite→재시작/화면 새 조회 `[2,0]`, 음수 미저장·키보드·상태·cleanup 확인 |
| 사용자 파일·변경 범위 | `complex/parent-inspection.json`: 위 4파일만 변경, Domain/UI bytes와 user-notes 보존 |
| 별도 문맥의 아주 작은 요청 | `tiny/inspection.json`: 제목을 바꾸라는 요청에서 `docs/index.md`만 변경. 생성/삭제 파일 0, capability 선택·제품 실행·설계 문서·계약·상태 생성 0 |

독립 검사기는 HTTP 응답과 SQLite 행을 직접 읽고 저장 오류를 trigger로 주입한다.
자체 성공 표시를 받아들이지 않으며 소비자에게 노출하지 않았다. 기준선 이후
최대값만 매개변수로 만들었고 기본값 20의 동일 판정으로 후보를 검사했다.
처음 기준선은 알 수 없는 POST 경로가 body를 읽지 않고 반환하는 동안 연결이
끊겨 19개 관찰 후 중단됐다. 첫 raw를 보존하고 관측기에서 transport-error를 실패
관찰로 기록하도록 보완했다. 재실행 32개와 후보 결과를 첫 시도 성공으로 합치지 않는다.

소비자 첫 회귀는 SQLite 테스트 연결을 닫지 않아 임시 DB 정리에서 실패했다.
제품 수리는 추가하지 않고 테스트의 connection lifetime을 `closing`으로 고친 뒤
4개를 재실행했다. 응답 shape assertion을 보강한 마지막 4개 실행도 별도 로그에
보존했다. 처음 실패 로그도 유지한다. 기존 browser runner는 변경하지 않았다.

## 짧은 요청의 새 문맥 소비

첫 후속 소비자는 이전 대화·정답 없이 전체 source catalog와 격리 프로젝트,
“수량 일괄 저장 상한을 50개로 늘려줘. 기존 검증·원자성과 단건 저장은 유지하고
실제 확인해줘”라는 요청을 받았다. 프로젝트 index→acceptance/Feature/소유 코드와
기존 검사 명령을 발견하고 API 한계·오류 문구, 관련 테스트·문서만 바꿨다.
Domain·UI·저장 경계와 사용자 파일은 유지됐다. 직접 API 회귀 4개와 기존 브라우저
16/16, 별도 부모 검사 `followup-oracle/results.json` 32/32가 통과했다.

이 소비자는 **architect와 새 change-impact 참조를 사용하지 않았다**. 기존
프로젝트 설계 기준을 적용한 경량 후속 소비이며 새 스킬 발견 성공으로 세지 않는다.
근거는 `followup/project/report.md`, `.work/quantity-batch-50-20261018/`,
`followup/parent-inspection-retry.json`이다. PowerShell JSON 읽기 오류는 같은 raw를
Python으로 읽어 해결했으며 제품 재실행은 없었다. 부모의 최초 파일 비교는 상위
`.work`까지 제외해 빈 집합을 만든 관측 오류였다. 프로젝트 상대 경로로 수정한
재검사에서 4파일 변경·보고서 1개 추가·삭제 0을 확인하고 최초 오류도 보존했다.

추가 문맥에는 “HTTP 처리에서 저장 책임을 분리해 직접 호출하는 작업에서도 같은
원자적 저장을 재사용할 수 있게 해줘. 기존 API·오류·데이터는 유지하고 실제
확인해줘”라는 짧은 요청과 전체 catalog/프로젝트만 제공했다. 특정 스킬·파일명·
정답·이전 대화는 제공하지 않았다. 이 소비자는 catalog에서 **architect와
change-impact를 발견·읽고 적용**했다. `storage.py`로 연결·초기화·원자적 저장을
옮기고 HTTP 파싱·Domain 검증·422 변환은 API에 유지했다. 기존 `app.connect`와
`app.initialize`는 import로 호환성을 남겼다. 저장 함수는 검증된 정수 목록을
받는 내부 persistence 경계이며 raw 외부 입력의 새 검증 계층으로 주장하지 않는다.

실제 기준선 4개 통과 후 후보 5개 통과에 직접 호출 정상 저장·중간 SQLite 거절의
롤백이 추가됐다. 브라우저 16/16과 부모 독립 API/저장/재시작 32/32도 통과했다.
기존 Domain·UI·runner·user-notes는 bytes가 같고 assertion은 새 저장 모듈의
dependency 참조만 추가했다. Feature/설정의 소유 경로도 갱신했다. 근거는
`boundary/project/report.md`, `.work/storage-boundary-20261018/`,
`boundary/parent-inspection.json`, `boundary-oracle/results.json`이다.

기준선 stdout/stderr 캡처에서 PowerShell wrapper가 오류처럼 표시되어 같은
4개 검사를 세 번 실행했다. 세 원본 출력을 보존하며 제품 실패나 고유 성공 12개로
집계하지 않는다. 직접 호출 근거와 기존 API 오류/저장 근거를 구분한다.
이것은 **제공된 catalog 안에서 추가 힌트 없는 발견·소비**의 한 사례다.
native-host가 스스로 스킬을 노출·선택한 무도움 발견이나 일반적인 준수율은 아니다.

## 검증과 경계

초기 catalog·자가완결성·생성·배포·문서·cohort 검사 50개, 작은 작업·읽기 전용
조회·완료 실행 재개 회귀 4개, 체크아웃 밖 패키지 통합 1개가 통과했다.
`architect` frontmatter 검증도 통과했다. 상세 출력은 `resources.json`,
`lightweight.json`, `package.json`, `skill-validation.json`에 있다.
최종 source 기준 `resources-final.json`은 catalog·자가완결성·생성·배포·패키지
37개, `docs-cohort-final.json`은 문서·cohort 14개 통과다. 앞선 실행과 더해
고유 성공 건수를 부풀리지 않는다. `drift.json`, `distribution.json`은 각각
종료 0이다. 후속 결과 서술은 raw와 대조하고 최종 diff 검사에 포함한다.

생성 도중 Windows user-mapped file 잠금으로 동기화 2회가 중단됐다. 잠긴
`skills/agent-workflow/SKILL.md`를 동일 bytes의 파일로 원자 교체한 뒤 기존
동기화가 성공했다. runtime 수리나 설치본 변경은 없다. 초기 Git index sandbox
거절 후 기존 커밋 권한으로 신규 파일을 등록했다. 읽기 단계의 존재하지 않는
파일 경로·UTF-8 출력/읽기 오류와 기존 host pipe 접근 거절도 실행 이력에 남겼다.
이들은 제품 성공 건수에 포함하지 않는다. 기존 unittest DeprecationWarning은 유지했다.

공통 runtime/API/schema와 검사 발견 로직이 바뀌지 않아 Full은 선택하지 않았다.
in-app browser의 기존 manual-disable 예외는 유지하고 격리 fixture의 기존
Playwright 경로를 사용했다. 설치본·전역 설정·유료 평가·push·배포·protected
branch 통합·5단계 이후 구현은 하지 않았다. native-host 무도움 발견과 운영 제품,
일반적 성공률·비용/재작업 개선은 미실행/unknown이다.

기존 active Goals·project-verification·0~3단계 근거·전역 원본의 531개 파일과
경로 집합은 `preservation-before.json`/`preservation-after.json`에서 동일하다.
이는 명시한 보존 범위이며 전역 cache나 모든 과거 `.work`의 전수 감사는 아니다.
