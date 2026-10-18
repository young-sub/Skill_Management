# 4A: 작업 플레이북·설명·회상·설계 검토

2026-10-18. clean `wp-20261018-stage0-compatibility`의
`c31699909c776ef0e3af4f49d81f995863287098`에서 시작했다.
기대 결과와 실패 판정은 `.work/stage4a-20261018/plan.md`, 원본 관찰과
실패·재시도는 같은 디렉터리에 보존한다. 별도 `20261018-plugin-readiness`
계약은 선택·수정·완료하지 않는다.

## 구현

- `authoring/playbooks/`의 feature, bug-fix, refactoring이 각각 완료/실패,
  재현/원인 수리/회귀, 기준선/호출·오류·부수 효과 보존을 소유한다.
  workflow와 검증 setup/maintain에 같은 원본을 생성한다.
- `agent-workflow`는 요청과 필요한 절차를 연결한다. CLI/task 선택과
  실행·조회·캡처·Windows 입력은 기존 참조가 소유하며 작은 수정에는
  task·계약·설계 문서·전체 단계·고정 위임을 요구하지 않는다.
- `zoom-out`은 현재 호출/소유권의 how와 기록된 제약/결정의 why 중 필요한
  관점을 선택한다. 소스 추적과 실행, 확인된 이유·추론·미확인을 구분한다.
- 독립 `recall`은 충분한 인계를 다시 검색하지 않고 현재 Git/task/실행과
  대조한다. 회상은 읽기 전용이며 실제 재개만 기존 실행으로 연결한다.
  오래된 PASS·다른 작업 승인·미확인 launch를 현재 성공이나 재실행 권한으로
  옮기지 않는다. 기억 DB·자동 메모리 쓰기는 없다.
- `multi-agent-review`는 가정의 반례와 확인 방법을 판단에 반영하고,
  `prototype`은 선택을 바꿀 불확실성에서만 동일 조건 후보를 실행한다.
  `architect`가 필요할 때 선택하며 채택안의 구현·영향별 회귀까지 확인한다.
  별도 how/why/interrogate/arena 스킬이나 Router·runner는 추가하지 않는다.

catalog는 21개다. Feature는 `agent-workflow`, `work-recall`,
`exploration-learning`, `independent-review`, `architecture-design`이다.
공통 runtime/API/schema는 변경하지 않았다.

## 검증 범위

소비 과제는 기존 connected-product의 격리 복사와 source catalog를 제공한다.
정답 패치나 플레이북 경로를 지정하지 않는다. 제공된 catalog 내 발견은
native-host의 무도움 발견과 다르다. fixture의 합성 기록은 실제 운영 이력이나
사용자의 새 승인이 아니다. 사용량·비용과 일반적인 준수율은 unknown이다.

## 실제 소비

| 요청 / 선택한 기준 | 관찰과 근거 (`.work/stage4a-20261018/` 기준) |
| --- | --- |
| 짧은 기능 요청 / 완료·실패와 기존 API 보존 | `tasks/report.md`: catalog에서 agent-workflow와 feature 플레이북을 읽고 health에 service를 추가. 기존 runner 18/18, 초기 count 0과 재시작 후 count 2에서 전체 health 계약을 확인 |
| bool 버그 요청 / 먼저 재현 가능성 확인 | 처음 fixture는 이미 bool을 거부했다. 제품 로직을 바꾸거나 RED를 만들지 않고 Domain 4개와 실제 API 422·미저장 회귀 19/19를 확인. 이는 버그 수리 성공이 아닌 결함 부재 사례 |
| 별도 제어 결함 / 실제 버그 수리 | 부모가 bool guard를 제거한 별도 fixture에 같은 짧은 요청을 제공. `bug/report.md`: API true→201·SQLite 1 재현 후 Domain owner 수리. bool/음수 422·미저장, 2/0 저장·새 조회 `[2,0]`, Domain 3개와 기존 브라우저/재시작 runner 16/16 |
| 짧은 저장 책임 분리 / 동작 보존 | refactoring 플레이북과 architect를 선택, storage.py로 SQLite 책임을 이동하고 직접 save/read/count·bool 거부 검사 추가. 기존 runner 전후 19/19, 임시 port를 제외한 11개 관찰 일치, Domain/storage 5개 통과 |
| 작은 제목 수정 / 직접 확인 | 같은 소비자가 docs/index.md 제목만 수정하고 읽기/diff로 확인. 이 단계에 새 task·계약·설계 문서·제품 명령 없음. 새 문맥의 독립 tiny 실험으로 확대하지 않음 |
| 회상 / 읽기 전용과 현재성 | `recall/report.md`, `read-only-inspection.json`: 현재 dirty 사용자 주석, 미구현 health, 원본 없는 과거 PASS, receipt 없는 unknown export를 구분. 제품 명령 0, 프로젝트 21개 파일의 경로·bytes 동일 |
| 실제 재개 / 다음 행동 실행과 중복 방지 | 명시적 후속 요청 후 app.py의 health 한 필드만 변경. `recall/resume-evidence.json`: 실제 GET 1회, HTTP 200 및 필드 5개 확인, 서비스 시작/정지 각 1회, POST/export 재전송 0. 사용자 주석·handoff·pending bytes 보존 |
| raw는 있으나 현재 재사용 불가 / 기록 부재 | `stale/report.md`: 실제 Inventory 관찰을 복사한 raw와 현재 dirty InventoryNext 코드의 차이·다른 실행 identity를 구분. 이전 관찰을 인정하되 현재 acceptance로 사용하지 않고 task 기록 부재를 유지. 재검색·제품 명령 0, 20개 파일 bytes 동일 |
| 설계 반례·후보 실행 / 동일 조건과 판단 반영 | `design/comparison.md`, `experiment.json`: 같은 seed 41·정상/잘못된 입력·두 번째 INSERT 거절에서 항목별 commit은 `[41,6]`, 전체 transaction은 `[41]`. 원자성 요구로 후자를 채택하고 batch API 구현 |
| 채택안 구현 / 실제 회귀 | `design/implementation-regression.json`: 기존 runner 확장 22/22, Domain 2개, 단건 브라우저·batch 1/20 경계·거절·rollback·재시작 조회, skip/error/cleanup error 0. `design-oracle/results.json`: 별도 API/SQLite/재시작 관찰 32/32 |

기능·리팩터링 소비자는 feature/bug-fix/refactoring을 실제로 읽었다.
설계 소비자는 architect와 prototype을 선택했지만 multi-agent-review는 선택하지
않았다. 이 미사용을 검토 스킬 발견 성공으로 세지 않는다. 회상 소비의 중간
보고서에는 recall만 있었고, 종료 전 스스로 zoom-out도 읽어 기록을 보강했다.
주 세션이 중간 파일을 먼저 읽은 시점과 최종 보고서를 구분한다.

별도 짧은 설명/검토 요청의 새 문맥은 catalog에서 zoom-out과 architect를
선택했다(`explain-review.md`). 실제 UI→API→Domain→SQLite 호출과 기록된
SQLite 이유를 찾고, HTTP 버전의 과거 의도는 미확인으로 남겼다. 소스 검토를
실행 관찰로 표현하지 않았고 제품 명령 0, 회상 fixture 21개 파일 bytes 동일이다.
추가 위임 금지를 multi-agent-review 사용 금지로 해석해 그 스킬은 읽지 않았다.
이 발견 실패를 근거로 description과 진입 문구에 단독 반례 검토를 명시했다.
다른 스킬·runtime을 추가하지 않고 같은 소유자의 발견 조건을 수리했다.

설명 수정 뒤의 별도 소비는 multi-agent-review를 선택했지만, SQL row commit을
부모 Harness의 Git Item commit으로 잘못 해석했다(`review-retry.md`). 이는
**발견은 했으나 적용 대상이 틀린 실패**이며 요청된 검토의 성공이 아니다.
부모 research 검색 결과 일부도 노출돼 blind 사례가 아니다. 같은 스킬에
사용자가 지정한 프로젝트와 실제 진입점을 먼저 확정하도록 보강했다.
정확한 fixture/API 경로를 알려준 후속은 도움받은 교정 소비로 분리한다.
이 실패에서 잘못 지목한 core_harness.py는 수정하지 않았다.
`review-corrected.md`는 수정된 multi-agent-review를 읽고 두 번째 INSERT 거절
반례와 실제 전체-loop transaction·바깥 예외 처리 경계를 대조했다. 소스 검토만
수행하고 runtime PASS는 주장하지 않았다. 이 판단은 이미 관찰한 동일 조건
실험·구현 22/22·독립 32/32와 일치한다. 무도움 재발 방지까지 입증한 것은 아니다.

회상은 충분한 handoff로 대조했으며 다른 대화 원문을 찾지 않았다. 다만 상위
메모리 지침에 따른 registry 키워드 조회와 부모 저장소 지침 읽기는 있었으므로
전체 파일 접근이 handoff만으로 제한됐다고 주장하지 않는다. runtime 동작과
기록된 SQLite 이유, 기록 없는 HTTP 버전 의도를 구분했다. 재개 시 HTTP/1.0
응답이 실제 관찰됐어도 그 과거 선택 이유가 확인된 것은 아니다.

기존 stage4 검사기는 이번 기준선에서 32개 중 15개 실패했다. batch가 없는
상태를 성공으로 처리하지 않는다. 후보 실행 전 새 fixture의 저장 실패 계약에
맞춰 batch HTTP 기대값만 422에서 500으로 바꾸고 rollback/기존 단건 기준은
유지했다(`oracle-note.json`). 기준선 실패와 후보 성공은 별도 실행이며 이전
stage4 PASS를 재사용한 결과가 아니다.

## 회귀·배포와 보존

초기 catalog·자가완결성·생성·배포·문서·cohort 50개(`resources.json`),
작은 작업·조회 무실행·dirty 현재성·완료 재개·unknown launch 재전송 금지
6개(`lightweight.json`), 체크아웃 밖 패키지 통합 1개(`package.json`)가 통과했다.
참조 이동의 후속 링크 수정 후 최종 resource/package 37개(`resources-final.json`),
원본/생성 drift와 배포 검증(`drift-final.json`, `distribution-final.json`)도 통과했다.
검토 발견 문구 수정 뒤 resource/package 37개(`review-resources.json`),
문서·cohort 14개(`docs-cohort-final.json`)도 통과했다. 마지막 대상 범위 문구와
EOF 공백 정리 뒤 최종 drift·배포·패키지·diff를 다시 확인했다
(`commit-drift.json`, `commit-distribution.json`, `package-final.json`,
`commit-diff.json`). 명령/검사 로직이 같은 기존 실행은 별도의 고유 성공으로
더하지 않는다.
recall 및 변경된 5개 스킬의 frontmatter도 기존 작성 도구로 확인했다.
공통 runtime 변경이 없어 Full은 선택하지 않았다. 같은 조건의 중복 실행을
고유 성공 건수로 합산하지 않는다.

보존 검사 `preservation-result.json`은 기존 active Goals·project-verification·
0~4단계 근거·전역 원본 717개 파일의 경로와 bytes가 동일함을 확인한다.
각 fixture의 사용자 메모도 유지됐다. 이는 명시한 범위이며 전역 cache나 모든
과거 `.work`의 전수 감사는 아니다. plugin-readiness 계약은 그대로 남는다.

## 실패·재시도와 한계

초기 넓은 파일 목록은 오래된 host pipe에서 접근 거절을 만났고, 일부 독립
스킬을 authoring 아래에서 찾은 읽기 경로는 없었다. 원본 map에 따라 바로잡았다.
Git index 쓰기는 sandbox에서 거절된 뒤 기존 커밋 권한으로 등록했다.
PowerShell 인용/UTF-8 JSON 읽기와 port URL의 단순 비교 오류는 제품 실패와
구분하고 같은 원자료의 올바른 파싱·비교로 해결했다. 기존 unittest의 반환값
DeprecationWarning은 유지했다.
최초 diff 검사에서 참조 EOF의 추가 빈 줄 4곳을 찾아 원본에서 제거하고
생성본을 동기화했다. 로드맵 문장 치환 한 번은 불일치 assert로 무변경 종료 후
정확한 원문으로 수정했다.

제어 bool 결함의 첫 재현은 저장 오류를 실제 관찰했지만 검사기의 SQLite
connection이 닫히지 않아 임시 DB 정리가 실패했다. 해당 핸들을 닫도록 관측기를
고친 재현과 수리 후 확인을 별도로 남기며 첫 시도를 깨끗한 실행으로 세지 않는다.

설계 실험 첫 명령은 잘못된 script 경로로 실행 전에 실패했다. 성공한 첫
실험 JSON은 인코딩 정리 중 잘렸고 복구 전에 원래 bytes를 별도 보존하지 못했다.
첫 관찰은 도구 대화에 남으며 현재 experiment.json은 같은 기준의 재실행이다.
이를 최초 raw가 온전히 보존된 것으로 보고하지 않는다. 구현 회귀 JSON과
부모 독립 검사 근거는 별도로 보존했다.

in-app browser의 기존 `skip_until_manual_reenable` 예외(세션 policy metadata
부재)는 유지했다. 해제 위치는 Codex CLI `/plugins`의 Browser 선택이며 이번에는
해제하지 않고 격리 fixture의 기존 Playwright runner를 사용했다.
설치본·전역 설정·유료 평가·push·배포·protected branch 통합·5단계 평가·6단계
swarm은 실행하지 않았다. 운영 제품·native-host 무도움 발견·일반 효과는 미확인이다.
