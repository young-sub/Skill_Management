# 5단계: 효과 평가와 정리

2026-10-18. clean `wp-20261018-stage0-compatibility`의
`298743d313ede68404a2eb9a9d7bbc82278fc0dc`에서 시작했다. 별도
`20261018-plugin-readiness` 계약은 선택·수정·완료하지 않았다.
기준과 원본 출력은 `.work/stage5-20261018/`에 보존한다.

## 고정한 비교와 판정

`plan.md`, `pins.json`에 실행 전 요청·기대 결과·실패 조건·평가기 해시를
고정했다. 4A의 batch 저장 검토 과제, 제품 복사본, 기존 `independent_check.py`,
`run_check.py`, connected-product runner와 lookup/resume 회귀를 재사용했다.
새 runner·평가기·상태 DB·계약은 없다. 유료 모델/API 평가는 실행하지 않았다.

주 비교는 같은 프로젝트 bytes·요청·전체 catalog·위임 금지 조건에서
`multi-agent-review`의 description만 4A 초기 문구로 되돌린 대조군과 현재
HEAD를 비교한다. 본문과 나머지 capability는 같다. 대조군은 과거 전체 버전이
아닌 description 하나의 대조이며, source 경로와 개행 표현 차이는 남는다.
모델/추론은 세션 상속이며 실제 응답 ID는 수집하지 못했다. 표본은 조건별 1회다.
따라서 일반 성공률·속도·비용의 인과 효과나 전체 0~4A A/B benchmark가 아니다.

합격은 검토 스킬을 실제 읽고 지정한 제품의 entrypoint에 반례를 적용하며,
소스 검토와 실행을 구분하고 파일·권한을 보존하는 것이다. 스킬 미사용,
부모 Harness를 제품으로 오인, 결함 누락, 잘못된 완료, 불필요한 차단·위임,
무단 쓰기는 별도로 실패 판정한다. 검토 내용이 맞아도 미사용을 지우지 않는다.

## 실제 소비와 수리

| 실행 | 실제 관찰 | 판정 |
| --- | --- | --- |
| 현재 HEAD, 짧은 batch 요청 | `baseline-report.md`: catalog의 multi-agent-review를 읽고 두 번째 INSERT 거절에 따른 부분 저장 반례를 찾음. 현재 전체-loop transaction과 Git Item commit을 구분. 제품 명령 0 | 추가 교정 없는 catalog 내 발견·대상 적용 성공. native-host 발견은 아님 |
| 4A 초기 description 대조군, 같은 요청 | `description-control-report.md`: architect·agent-workflow·별도 ponytail-review를 읽었으나 multi-agent-review는 읽지 않음. SQLite 반례와 현재 구현 판단 자체는 맞음 | 검토 내용 유효, 목표 스킬 발견 실패. 결함 누락·잘못된 완료로 중복 계산하지 않음 |
| 더 짧은 commit 요청의 첫 후속 | `followup-report.md`: 목표 스킬과 제품을 찾았지만 첫 파일 읽기에 baseline-report.md를 포함 | 오염된 실패 시도. 무도움 후속 성공에서 제외; 이후 부모 메시지는 오염 기록·종료 지시이며 교정 성공으로 세지 않음 |
| 입력 격리 수리 후 후속 | `isolated-retry-report.md`: 이전 답은 읽지 않고 목표 스킬도 선택했지만, 질문을 Git Item 준비로 해석해 Git 이력·Item 상태·실행 report를 요구 | 대상 오인과 불필요한 추가 자료 요구 재현. 입력 격리 성공과 검토 실패를 분리 |
| 대상 바인딩 수리 뒤 같은 조건 재검토 | `scope-repair-report.md`: multi-agent-review를 읽고 제품 callsite에서 SQLite 의미를 선택. 두 번째 INSERT 거절 반례·현재 전체 transaction·Git 정책의 별도 범위를 설명 | 추가 교정 없이 대상 적용 성공. Git/Item 추가 자료 요구·제품 실행·잘못된 runtime 완료 0 |
| 명시적 Git 정책의 정상 후속 | `git-policy-review.md`: 같은 소비자가 명시적인 Git commit_per_item 질문을 받고 완전한 기능 단위·결합 변경과 독립 Item을 구분 | SQLite 검토로 강제 전환하지 않음. 특정 diff의 분할 안전성은 미확인. 새 독립 발견 표본은 아님 |

4A의 기존 도움받은 `review-corrected.md`는 이번 성공에 합산하지 않는다.
현재 HEAD의 첫 소비는 그 보고서나 답·스킬 지시를 전달받지 않았다. 대조군의
미사용은 description이 위임 요청 중심이어서 단독 반례 검토 발견을 놓치는
기존 원인과 일치한다. 4A의 description 수리는 유지한다. 그러나 더 짧은 입력의
깨끗한 후속은 대상 바인딩 수리가 충분하지 않음을 드러냈다.

`multi-agent-review`는 이름 있는 프로젝트를 읽으라는 기존 문구만으로는
그 프로젝트의 `.harness` 작업 정책을 제품 의미보다 우선했다. 해당 소유자의
바인딩 문단을 수정해 제품 callsite의 입력/저장 transaction과 Git/Item 전달을
구분하고, `.harness`가 있다는 이유로 후자를 선택하지 않게 했다. Git/Item 자료
부재는 소스 기반 제품 설계 검토를 막지 않는다. 남는 모호성은 명시하되 검토
대상을 조용히 바꾸지 않는다. 공통 runtime은 수정하지 않았다.
수리 전후 자료의 17개 제품 파일·요청·catalog description·근거 범위는 동일하다.
차이는 검토 본문과 manifest 및 Temp 복사 경로다. 각 1회에서 대상 오인/불필요한
자료 요구가 관찰된 1건에서 0건으로 바뀌었으나, 모델 ID/추론 미수집과 표본 한계로
일반 개선율을 계산하지 않는다. 정상적인 명시적 Git 질문도 별도 후속에서 허용했다.

이번에 새로 관찰한 문제는 **새 대화만으로 공유 workspace의 이전 답 노출이
막히지 않는 것**이다. 기존 평가 준비 소유자인
`authoring/references/feedback-and-success.md`의 5번 절차를 수정했다.
이전 소비자 보고서·평가기 답을 발견 범위 밖에 두고, 깨끗한 과제/자료 복사와
명시적 근거 범위를 사용하며, 우발적 노출은 오염으로 남기고 새 문맥에서
재시도하도록 했다. agent-workflow·diagnose 생성 참조와 manifest를 동기화했다.
이것은 접근 통제를 구현한 sandbox가 아니라 평가 준비 절차의 수리다.
실제 후속은 그 절차로 준비했으며 범위 제한 도움도 결과에서 숨기지 않는다.

Feature는 `agent-workflow`, `feedback-repair`, 문서 정합성의
`independent-review`다. Feature Map의 위임 전용 설명, 로드맵 첫머리의
4A 미구현 표기를 수리하고 현재 설계·index·testing을 연결했다.
catalog는 기존 21개를 유지한다. 새 스킬·공통 runtime/API/schema 변경은 없다.

## 같은 조건의 검출력과 정상 허용

| 기존 검사 | 이번 실행과 의미 |
| --- | --- |
| batch 독립 평가기 | `normal-batch-capture.json`: 32/32. `fault-batch-capture.json`: 행마다 commit만 주입한 복사본은 30/32로 실패. `storage rollback`, `storage rollback fresh GET`에서 이전에 저장된 첫 행을 검출. 정상/입력 거절/단건 계약·재시작 조회 유지, 소유 서버 종료 확인 |
| 연결 제품 | `connected.json`: required Chromium 회귀 3개 통과, skip 없음. 정상 저장·재시작·새 조회와 FE payload +1의 5개 실패, 의도된 UI 차이 허용과 focus 결함 검출을 유지 |
| 경량 작업·조회·재개 | `lightweight.json`: 기존 6개 통과. 작은 작업에 전체 셀 선언을 요구하지 않으며 조회 무실행, 미추적 입력 현재성, 완료 checkpoint 재사용과 unknown launch 재전송 금지를 확인 |

결함 주입 실행은 실패한 제품 결과 그대로 남긴다. 검사기가 결함을 검출했다는
사실과 제품 성공을 구분한다. 정상/결함 대조는 plugin 지침 변경의 모델 효과가
아니며 같은 검출 장치를 유지할 근거다. 독립 평가기의 재시작 검사는 직전 DB와
새 GET의 일치를 보므로 rollback 검사와 같은 의미라고 간주해 삭제하지 않는다.

삭제·통합은 하지 않았다. API rollback, FE 전송 결함, UI focus, 무실행 조회와
unknown 효과 보호는 서로 다른 실패를 검출한다. 같은 결함 검출과 가까운 정상
허용을 보존하면서 없앨 수 있는 중복 후보를 이번 범위에서 찾지 못했다.

## 효과 판단과 경계

채택: 기존 4A 발견 수리와 경량 경로를 유지한다. 수정: 재현된 대상 오인을 검토
소유자에서, 평가 입력 오염을 기존 재사용 절차에서 수리하고 안내 drift를 정리한다.
보류: native-host 무도움 발견, 운영 제품, 일반 비용/개입/재작업 감소,
검사 삭제 및 6단계 swarm. 설치본과 전역 설정은 변경하지 않았다.

현재 HEAD 1회와 description 대조 1회 모두 제품 결함 누락·잘못된 runtime 완료·
불필요한 차단·사용자 추가 입력·제품 중복 실행은 관찰되지 않았다. 차이는 목표
스킬 선택 1회 대 미선택 1회이며 검토 품질 개선으로 확대하지 않는다. 후속 오염
1회, 격리 후 대상 오인 1회와 그로 인한 재작업·재시도는 분모에 남긴다. 부모의 실험 준비·범위 제한과
사용자 개입을 구분하며, 수집하지 않은 모델 시간·사용량·비용은 unknown이다.
로컬 검사 시간은 capture에 있지만 모델 작업 비용을 대신하지 않는다.

최초 두 capture 호출은 `--cwd` 누락으로 제품 실행 전에 실패했다. 수정한 호출은
새 제품 실행이며 중복 성공으로 세지 않는다. JSON 요약의 기본 CP949 읽기 실패는
UTF-8 bytes 파싱으로 고쳤고 제품 검사는 재실행하지 않았다. CIM 프로세스 상세
조회는 거절됐으며 이름/ID 목록만 확인했다. 기존 프로세스는 종료하지 않았다.
기존 unittest 반환값 DeprecationWarning은 raw에 남겼다.

초기 리소스/패키지 37개, 입력 격리 수정 뒤 문서·cohort 포함 51개가 통과했다.
대상 바인딩 수정 뒤 `scope-resources.json`의 catalog·자가완결성·생성·배포·
체크아웃 밖 패키지 검사 37개와 `scope-drift.json`, `scope-distribution.json`이
통과했다. 소스가 바뀌어 재실행한 검사는 새로운 고유 성공으로 합산하지 않는다.
최종 문서는 `docs-final.json`, staged diff는 `diff-final.json`으로 확인한다. 실행 로직 교차 변경이
없어 Full은 선택하지 않았고, 문구 일치만 검사하는 새 테스트는 만들지 않았다.

`preservation-result.json`은 active Goals·project-verification·0~4A 근거·
전역 원본 1,126개 파일의 경로·bytes 불변을 확인했다. 네 제품 복사의 소스 17개씩은
동일하다. baseline의 domain.pyc 1개는 부모의 독립 평가기 실행에서 생성됐으며,
이를 소비자의 무쓰기 증거에서 숨기지 않는다. 격리 실패/수리 소비의 각 291개
입력 자료도 불변이고 보고서만 추가됐다. `final-preservation.json`은 명시적 Git
후속 뒤에도 입력과 첫 검토 보고서가 불변임을 확인한다. 모든 과거 `.work`나 전역 cache의 전수
감사는 아니다. in-app browser의 기존 manual-disable 예외는 유지하고 기존
Playwright runner를 사용했다. 설치·전역 변경·push·배포·protected branch 통합·
6단계 swarm은 실행하지 않았다.
