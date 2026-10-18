# 6단계: 병렬 위임과 통합 검증

2026-10-18. clean `wp-20261018-stage0-compatibility`의
`557905d094420498928d3ddff78dc7d4eb131aa1`에서 시작했다.
`20261018-plugin-readiness`는 선택·수정·완료하지 않는다.
실행 전 기준, 입력 해시, 원본 출력은 `.work/stage6-20261018/`에 보존한다.

## 구현과 소유권

독립 `swarm`은 목적·파일 소유권·선행 의존성·완료/실패 기준·요구 증거·
검토/통합 책임을 가진 구현 분담을 맡는다. `multi-agent-review`는 독립 반론과
판단 검토를 계속 맡는다. 공통 파일과 task 상태는 한 명만 쓰며, 실행 handle과
현재 artifact를 대조한 뒤 완료 checkpoint는 재사용하고 미확인 launch는
재전송하지 않는다. Agent 보고서 다음에 통합 diff와 실제 동작을 확인한다.

원본은 `authoring/skills/swarm/SKILL.md`, 생성본은 `skills/swarm/SKILL.md`다.
기존 resource map, manifest, catalog(22개), `agent-workflow` 진입점, portable
guide, Feature Map과 프로젝트 소유권을 연결했다. Feature는
`parallel-implementation`, 관련 진입점은 `agent-workflow`와 `work-recall`이다.
새 Router·범용 runner·DB·계약·공통 runtime 변경은 없다.

## 고정한 비교 조건

`plan.md`는 소비자 실행 전에 요청·실패 판정·비교 조건을 고정한다.
기존 4A 재고 fixture의 API와 storage 모듈에 일괄 저장을 구현한다.
`storage.save_items(database, values)` 인터페이스, 1~20개 strict integer,
입력 오류 422, 저장 실패 500, 전체 transaction, 기존 단건 동작 보존을
두 조건에 똑같이 제공했다. 쓰기 범위는 API·storage와 각 테스트 4개 파일이다.
공유 UI·Domain·사용자 파일은 보존한다.

각 소비자는 부모 대화 없이 다른 Temp 프로젝트와 전체 capability catalog를
받았다. 입력 288개 중 차이는 catalog의 절대 경로뿐이며 격리 Git commit ID는 다르다. 이전 소비자 보고서·
정답 patch·독립 평가기는 소비자 근거 범위 밖에 뒀다. 이것은 실험 입력 격리이며
접근 제어 sandbox가 아니다. Catalog 제공과 근거 범위 제한은 명시적 실험 도움이다.
스킬 이름이나 해결책은 요청에 주지 않았다. 순차 조건은 추가 Agent를 금지하고,
병렬 조건은 독립 구현의 실제 위임을 요청했다.

각 조건 1회이며 실제 응답 모델 ID·추론·모델 시간·사용량·비용은 unknown이다.
세션 설정을 상속했으며 별도 유료 모델/API 평가는 하지 않았다. 속도·비용·일반
결함 감소의 인과 효과를 주장하지 않는다. 로컬 검사 시간은 모델 비용이 아니다.

## 실제 결과

| 조건 | 관찰 | 실패·재작업과 한계 |
| --- | --- | --- |
| 순차 | `agent-workflow`와 feature/영향/검증 참조를 선택. Agent 추가 없이 API·storage 구현. 최종 단위검사 13개, 브라우저 19개, 별도 실제 프로세스 재시작 후 batch 조회 통과 | 첫 12개 단위검사에서 SQLite 연결 미종료로 정리 오류 2개. 테스트 연결을 닫아 수정하고 12개 통과 후 경계 검사를 더해 13개 통과. Temp patch 접근 거절과 JSON 요약 읽기 오류 보존 |
| 병렬 | catalog에서 `agent-workflow`와 `swarm`을 읽음. `/root/parallel_consumer/storage_batch`가 storage/전용 테스트를 맡고 주 소비자가 API/전용 테스트를 동시에 구현. 통합 단위검사 12개, 브라우저 19개, 실제 batch 프로세스 재시작 조회 통과 | worker의 4개 검사 중 정리 오류 1개와 통합 검사 정리 오류 1개를 각 테스트 소유자에서 수정. patch/전송 실패와 재시도 보존. 전역 MEMORY 검색이라는 근거 범위 일탈이 있어 엄격한 격리 발견 성공에서 제외 |

병렬 결과의 원본 보고서는 Agent가 API 구현과 storage 작업의 실제 중첩,
독점 파일 소유권, main 통합 검토를 기록한다. 부모는 그 보고서의 PASS만 받지 않고
최종 diff와 독립 HTTP·SQLite 평가를 확인했다. 두 입력 모두 원래 파일 중
`app.py`, `storage.py`만 바뀌었고 사용자 파일과 나머지 286개 입력은 동일하다.
새 전용 테스트와 `.work` 실행 기록은 별도 추가 파일이다. `sequential-final/`,
`parallel-final/`에 최종 제품·보고서·보존된 로컬 근거를 복사했다.

두 결과물 모두 기존 4A 독립 평가기로 **32/32**를 통과했다. 정상 batch의 순서·ID,
잘못된 입력의 무쓰기, 두 번째 INSERT 강제 실패의 전체 롤백, 새 GET,
서비스 재시작 후 같은 DB 조회와 단건 호환성을 관찰했다.
각 최종 결과물의 복사본에만 행별 commit 결함을 넣으면 **30/32**로 실패한다.
동일하게 `storage rollback`, `storage rollback fresh GET`이 먼저 저장된 행을
검출했다. 네 실행 모두 소유 서버 종료를 확인했다. 결함 주입은 실패한 제품
실행으로 남기며 모델의 결함 발견 성공이나 정상 결과에 합산하지 않는다.

| 비교 항목 | 순차 | 병렬 |
| --- | --- | --- |
| 고정 평가기 범위의 잔존 결함 누락 / 잘못된 완료 | 0 / 0 | 0 / 0 |
| 추가 사용자 입력 | 0 | 0 |
| 실패한 테스트 실행과 수정 | 1회, 정리 오류 2개 | worker 1회 + 통합 1회, 정리 오류 각 1개 |
| 관찰된 파일/의미 충돌 | 0 | 0 |
| 관찰된 중복 효과 실행 | 0 | 0 |
| 대상 스킬 소비 | 순차 조건에서 swarm 미사용, 예정된 대조 | swarm 읽음; 근거 범위 일탈 별도 실패 |
| 모델 시간·사용량·비용 | unknown | unknown |

부모는 각 소비자에게 상태 조회와 현재 검사 뒤 보고서 마무리 메시지를 보냈다.
해결책·평가 정답은 전달하지 않았지만 이 조정도 도움 이력으로 남긴다.
단위검사 재시도·추가 경계 검사·다른 DB의 독립 검증을 중복 효과와 혼동하지
않는다. 이 표는 작은 한 과제의 관찰이며 병렬이 재작업이나 비용을 줄였다는
결론은 나오지 않았다. 병렬 소비자의 범위 일탈은 성공으로 지우지 않는다.

## 재개·후속 소비

깨끗한 별도 Temp 복사에 통합 코드·전체 catalog와 기존 task/context를
준비했다. 기존 `start → prepare → execute`를 사용하고 readiness 계약과
연결하지 않았다. 준비 중 캡처 도구의 `unittest_evidence.py`를 누락해 import가
실패했다. 실제 `--help` 재현으로 제품 시작 이전의 준비 오류임을 확인하고
누락된 기존 파일만 복사했다. 이전 started marker·누락된 capture 상태는
보존하고 새 plan/output에서 실행했다. 제품 runtime 수정은 없다.

새 실행은 기존 browser runner와 원본 assertion을 통과하고 실제 완료 checkpoint를
남겼다. 후속 소비자에게는 이 원본과 이전 started-without-checkpoint 실행을
함께 제공하되, 부모의 진단 답과 이전 소비자 보고서는 제공하지 않았다.
이는 알려진 자료를 재구성한 continuation 실험이며 실제 Agent crash 자체의
증거가 아니다. 실제 controller 중단·재개는 아래 기존 회귀로 구분한다.
복사 뒤 병렬 소비자가 API 테스트에 server-instance 재시작 관찰을 추가했다.
후속 입력의 실행 코드 두 파일은 최종 결과와 같지만 그 테스트 추가는 포함하지
않는다. 후속 checkpoint의 입력을 뒤늦게 덮어쓰지 않았다.

첫 후속은 `recall`만 읽어 **swarm 미사용**으로 남겼다. 실제 완료된 browser
checkpoint는 코드·raw 해시를 대조해 재사용했고 이전 unknown launch도
재전송하지 않았다. 그러나 인계에 batch 완료 증거를 주지 않아 소비자가
미검증 batch를 직접 검사했다. 첫 stdout 수집은 PowerShell stderr 처리로
불완전했고, 별도 재시도 12개와 batch OS-process 재시작 관찰이 통과했다.
기존 319개 입력·task·증거 파일은 그대로였다. 새로운 실행이 원래 checkpoint의
중복은 아니지만, 사전의 제품 명령 0회 기준에는 실패했다. 이를 성공으로
재분류하지 않는다. 준비 자료의 공백과 스킬 발견을 구분한다.

재개 발견 소유자인 `recall`에 위임된 소유권·통합을 대조할 때 사용 가능한
`swarm`으로 이어지는 연결만 추가했다. Swarm description/본문은 새 Agent를
띄우지 않는 main-only 재개도 포함한다고 명확히 했다. Runtime은 그대로다.
재시도 준비는 이미 실행된 batch 원본과 source 해시를 인계에 포함하고 현재
범위를 source/evidence 대조로 한정했다. 이전 소비자 보고서와 해석 결과는
근거 범위 밖으로 옮겨 보존했다. 실제 원본 실행 증거는 재개 자료로 남겼다.
스킬 연결과 제공 자료가 함께 달라졌으므로 결과를 문구 하나의 인과 효과로
주장하지 않는다. 새 문맥의 준비 도움을 받은 재시도로 별도 집계한다.

재시도는 catalog에서 `recall → swarm → agent-workflow`를 읽었다. 실제 source와
batch 원본 10개 해시를 대조하고 완료 browser bundle은 기존 CLI의 읽기 전용
조회로 PASS/REUSABLE을 확인했다. 이전 started-only bundle은 BLOCKED/UNKNOWN,
불완전한 테스트 stdout도 미확인으로 남겼다. **새 제품 검사·서비스 실행 0회**이며
328개 기존 입력·task·raw 파일의 bytes 변화도 0개다. PID/CIM 조회 거절은
미확인 한계로 기록하고 replay의 이유로 쓰지 않았다. 해당 fixture의 넓은
architecture review NOT_RUN과 task 전체 완료를 구분했다.

`followup-first-report.md`와 `followup-final/report.md`가 각각 미사용/추가 실행과
수리 후 소비를 보존한다. 이 재시도는 자료를 보완한 catalog 후속 소비 성공이며
native-host 무도움 발견, 첫 시도의 성공 또는 일반 효과로 승격하지 않는다.

## 회귀·배포와 보존

기존 완료 checkpoint·shared producer·unknown launch·known failure와 pending
검사·실제 controller 종료·task lookup/execute resume·독립 worktree commit/통합
회귀 **8개**가 이번 실행에서 통과했다. 이것은 runtime 보호의 증거이며
스킬 문구가 모든 모델의 중복 실행을 막는다는 증거는 아니다.

초기 catalog·자가완결성·sync·distribution·package·문서 41개 검사 중 package
1개가 새 파일의 Git 미등록으로 실패했다. 빌더의 기존 `git ls-files` 규칙을
확인했고, 일반 Git index 쓰기 권한 거절 뒤 허용된 권한으로 새 파일을 등록했다.
등록 전에 발생한 package 재시도 실패도 보존했다. 등록 후 package 검사는
통과했다. Skill validator, resource drift와 배포 구조 검증도 통과했다.
문서/portable guide 변경 뒤 해당 검사만 다시 확인하며 성공 수를 중복 합산하지 않는다.
Recall 보완을 포함한 최종 리소스/패키지 회귀는 `resources-after-recall.json`에서
41/41 통과했다. `drift-after-recall.json`, `distribution-after-recall.json`,
`swarm-validation-final.json`도 통과했다. 앞선 8개 runtime 회귀는 로직이
변하지 않아 재사용하며 결과를 새 실행으로 세지 않는다.
Recall 보완 뒤 동기화는 Windows user-mapped-section 쓰기 오류로 중단됐다.
기존 프로세스를 종료하거나 동기화 도구를 바꾸지 않고, 별도 Temp 원본/생성본에
기존 `-RepositoryRoot` 경로로 재생성했다. 실제 달라진 manifest만 가져오고
현재 트리의 drift 검사로 전체 일치를 확인한다. 실패·재시도 원본도 남겼다.

실행 로직·schema·공통 runtime 변경이 없어 Full은 선택하지 않았다.
새 단어/문장 일치 테스트를 만들지 않고 기존 catalog 기대 집합만 확장했다.
자가완결성과 패키지 실행은 모델 효과·설치본 갱신·native-host 성공과 별개다.

보존 기준 1,819개 파일은 기존 active Goals·project-verification·0~5단계(4A 포함)
증거와 전역 지침 원본이다. 최종 `preservation-final.json`에서 경로·bytes 변화는
0개이며 기존 독립 평가기 해시도 같다. 첫 후속 319개, 재시도 328개 기존 파일도 불변이다.
모든 과거 `.work`와 전역 설치본의 전수 감사를 의미하지 않는다.
기존 in-app browser manual-disable 예외는 유지하고 fixture의 Playwright를 사용했다.
설치·전역 설정·유료 API·push·배포·protected branch 통합은 하지 않았다.
