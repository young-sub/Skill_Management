# 실행된 요청: R0–R4 구현·검증과 로컬 main 통합

갱신일: 2026-10-09. 이 실행 블록은 이번 세션에서 수행됐다. 실제 결과와 지원 한계는 [구현 결과](agent-workflow-implementation-results.md#r0r4-implementation-2026-10-09)가 소유한다. 아래 블록은 수행 범위를 보존한 기록이며 다시 실행할 미완료 목록이 아니다. 이 문서는 0.1.44 검토 이후의 실행 프롬프트였다. 사용자가 이 프롬프트를 다음 세션의 요청으로 전달하면 아래 구현·로컬 Git 통합 범위를 승인한 것이다. 문서를 우연히 읽은 것만으로 실행 권한이 생기지는 않는다.

기존 G1–G6의 범위 한정 구현·시험은 [구현 결과](agent-workflow-implementation-results.md)에 있다. 이전 실행 프롬프트는 Git `95c4f9e:docs/research/agent-workflow-next-session.md`에서 확인할 수 있으며 다시 수행할 미완료 목록이 아니다. 현재 범위는 [보완 검토](agent-workflow-refinement-review.md)와 [R0–R4 완료 기준](agent-workflow-completion-design.md#review-driven-refinement)을 따른다.

아래는 사용자가 실행 요청으로 전달한 전체 블록이다.

```text
agentic-coding 플러그인의 최신 고도화 보완안을 실제로 구현·검증하고,
완료한 변경을 Skill_Management 로컬 main에 병합해줘.
짧은 계획 후 실제 구현을 진행하고, 계획·문서·스키마·시험 자료만으로 끝내지 마.

저장소: C:\Users\YS\Desktop\python\Skill_Management
연두라벨 참고 대상: C:\Users\YS\Desktop\python\labeler

이 요청은 Skill_Management의 source/tests/docs/저장소 generated 리소스 수정,
격리된 로컬 시험·새 로컬 패키지 생성, 기능 단위 커밋, 최신 main 반영,
검증된 작업의 로컬 main 병합과 이번에 만든 작업 공간 정리를 승인한다.
저장소의 main 보호 정책에 대한 이번 작업의 명시적 로컬 통합 승인이다.
push/publish/deploy, 기존 설치 Skill/Plugin·전역 설정·인증·권한 변경은 승인하지 않는다.
플러그인 고도화가 대상이며 연두라벨 제품 UI 후보를 수정하는 요청이 아니다.

1. 최신 Git 기준과 보존
- AGENTS.md, docs/index.md, .harness/project.yaml, docs/agents/workflow.md와
  적용 경로의 nested AGENTS.md, 환경 capability 예외를 먼저 읽어라.
- 현재 branch/HEAD/staged/unstaged/untracked, local main, upstream/remote,
  worktree 목록과 main 포함 관계를 확인하고 dirty baseline을 보존하라.
- git fetch origin으로 실제 원격을 확인하고, main 작업 공간에서
  git pull --ff-only origin main으로 동기화하라. upstream 이름이 다르면 실제 설정을 따르라.
  작성 당시 local main은 0.1.44 구현을 포함한 95c4f9e에서 문서 보완이 추가되는 상태였고,
  origin/main보다 92커밋 앞서 있었다. 이 값은 참고이며 현재 상태를 다시 확인하라.
- 로컬이 앞서 있으면 그 커밋을 보존한다. 양쪽이 갈라졌다면 서로의 변경을 검토해
  필요한 병합·충돌 해결을 하며 hard reset/force push/사용자 변경 덮어쓰기는 하지 마라.
  fetch/pull이 환경 때문에 실패하면 오류와 원격 최신성 미확인을 기록하고,
  확인 가능한 로컬 작업은 진행하되 동기화 성공으로 보고하지 마라.
- 뒤처진 기존 작업 브랜치에서 구현하지 말고 최신 로컬 main에서 고유한 새 branch/worktree를 만든다.
  원본 저장소 하위에 중첩하지 않는 허용된 작업 소유 경로(TEMP 또는 별도 worktree 부모)를 우선하라.
  이번 인계의 router/config 검사는 중첩 worktree에서 상위 저장소 경로 처리 오류가 났고,
  독립 TEMP 경로로 이동한 동일 내용에서는 통과했다. 기존 worktree나 .work를 재사용·삭제하지 마라.
- 여러 Agent가 같은 task 기록·공통 파일에 동시에 쓰지 않게 하라.
  태스크별 기록을 분리하고 공통 source/state 통합 작성자는 한 명으로 둬라.

2. 최신 설계와 이미 구현된 기능
다음 문서의 최신 구간과 관련 코드·호출자·테스트를 읽어라.
- docs/research/agent-coding-system-direction.md
- docs/research/agent-workflow-refinement-review.md
- docs/research/agent-workflow-completion-design.md#review-driven-refinement
- docs/research/agent-workflow-implementation-results.md의 최신 결과와 한계
- docs/research/pstack-analysis.md (고정 소스 비교이며 실행 정책 아님)
- docs/testing.md, docs/feature-map.md, docs/plugins.md, authoring/resource-map.json

0.1.44에는 task/context, 요청 연결, 6셀 범위, prepare/execute/lookup/resume,
feedback·RED/GREEN/정상 사례, ui_systems, maintain/check_retirements가 이미 있다.
0.1.43에서 수리한 review/findings 승계 결함을 미구현으로 다시 다루지 마라.
현재 동작을 확인하고, 유지할 기능과 재현한 공백·이번 구현을 짧은 작업 계획에 구분하라.
기존 G1–G6를 통째로 다시 수행하거나 W1–W7을 일곱 신규 시스템으로 만들지 마라.

3. R0 — 기준과 최소 수용 사례 고정
- 기존 독립 시험 프로젝트·실제 runner를 재사용해 API-only와 실제 Web+저장 경로,
  workflow 미설정 조사 과업을 다룰 최소 조건을 준비하라.
- 요구 출처·기대 결과·source/fixture/명령/runtime 조건을 기록하고
  현재 버전과 후보의 비교 기준을 먼저 고정하라. 정답 패치를 평가 Agent에게 주지 마라.
- business/architecture는 관점, FE·BE/API·Domain은 책임 영역이다. 6셀을 유지하고
  필요한 셀만 검증하되 비적용 이유·미판단·미연결·미확인을 숨기지 마라.
- 중요한 저장 흐름은 실제 입력→API→Domain→저장→fresh read의 ID와 값을 대조하라.
  합성 API 화면, 실제 API/DB, 정적 아키텍처 근거를 구분하고 셀별 PASS로 연결 성공을 대신하지 마라.
- 요구 문서와 코드/테스트가 충돌하는 사례, 정당한 요구 변경,
  FE 전달 오류지만 BE/Domain PASS인 사례와 FE 없는 정상 과업을 포함하라.
- 이미 충족한 항목은 실제 근거로 유지하고 부족한 동작만 구현하라.

4. R1 — 수정 없는 조사 → 조회 → 재개 연결 구현
- 정식 workflow가 미설정인 프로젝트에서도 진단 요청·허용/금지 범위·source 기준·
  조사 목록·증거 위치·미확인·다음 행동을 보존하고 이어갈 수 있게 하라.
- 기존 task가 있으면 연결하고, 없으면 .work의 최소 진단 기록을 사용하라.
  정식 검증 설정을 자동 생성하거나 실행 workflow/두 번째 task 장부를 복제하지 마라.
- 전체 조사 요청은 route/menu/API/CLI/job/role/flag 등 해당 프로젝트의 전체 진입점 분모를 유지한다.
  작은 요청은 영향 Feature/공유 owner/직접 소비자만 다루며 전체 setup을 선행 강제하지 않는다.
- UI는 적용 가능한 화면·viewport·하위 상태를 안정적인 ID로 구분하고 직접 관찰 근거를 연결한다.
  존재하지 않는 모든 조합을 생성하지 말고, 대표 캡처 하나로 미관찰 상태를 확인 완료 처리하지 마라.
- 관찰 사실/원인 추정, 제품/플러그인/도구/환경/Agent 판단 문제를 구분하라.
- lookup과 읽기 전용 resume는 기존 근거를 읽으며 테스트·브라우저·서버를 다시 실행하지 않는다.
  새 미관찰 범위의 조사는 별도 실행으로 구분하고 모호한 task를 최신 시각으로 추측하지 마라.
- 사용자가 검수할 수 있도록 위치·접근 경로·조건·기대/관찰·비교 근거·미확인을 보여라.
  HTML이 필요하면 기존 기록/결과의 얇은 파생 표현으로 만들고 결과 DB/dashboard를 새로 만들지 마라.
- 완료 근거: 미설정 상태에서 진단 생성→중단→새 context 조회/재개,
  원본 코드/설정/데이터 불변, 동일 ID·미확인 보존, 조회 시 실행 0회,
  일부 조사만으로 전체 완료가 되지 않는 반례.

5. R2 — 사용자 검수·피드백의 올바른 분기와 후속 소비
- 기존 diagnose/feedback/review/prevention/ui_systems를 사용해 다음을 구분하라.
  a) 기존 요구 위반: 원래 기준의 실패 검출→소유자 수리→같은 기준 통과·정상 반례.
  b) 요구 변경/새 선호: 요청 권한·근거와 기준 revision 갱신→새 요구와 유지 계약 검증.
  c) 의도된 차이: 공통 variant 또는 범위/사유/근거/재검토 조건이 있는 예외.
  d) 기준/도구 오류: 독립 근거로 확인 후 기준/runner/adapter 소유 위치 수리·실제 재확인.
  e) 환경 제약/원인 미확인: 실패·조건·재개 범위를 남기고 해결로 승격하지 않음.
- 후보 ID와 근거에 사용자 동의/의도된 차이/보류·의견을 연결하라.
  검수 동의만으로 원인을 확정하거나 기존 수정 권한을 확대하지 마라.
- 예방은 validation/type/schema/transaction/DB constraint/단일 상태 owner/
  공유 component/token/실제 회귀 검사 중 원인에 맞는 최소 수단을 사용한다.
  같은 지침을 추가하거나 가드레일을 등록했다는 사실만으로 완료하지 마라.
- UI guide는 의도·용어·variant·상태·반응형·접근성·예외와 코드 참조를 소유한다.
  실제 값·동작은 코드가 소유한다. 가이드 없는 경우도 다루되 현재 구현을 무조건 정답으로 추출하지 마라.
- 검증 가이드는 실제 명령·기준·fixture·Launch/Doctor/Drive/Evidence/Cleanup을 연결하고
  기능·도구·환경의 실제 변화가 있을 때 영향 부분을 갱신한다. 문서만으로 제품 결함을 덮지 마라.
- 상세 feedback/retirement 자동 근거 결합의 prepared native-JSON 제한을 확인하라.
  필요한 실제 runner는 기존 프로젝트 adapter로 연결하고 재현된 공통 계약 공백만 확장한다.
  결과 형식이 다른 것을 임의 PASS JSON이나 새 범용 parser로 감추지 마라.
- 완료 근거: 위 분류가 뒤섞이지 않고, 수리/기준 변경/예외가 해당 owner와 근거에 연결되며,
  새 관련 요청에서 기준·예방 검사가 실제 소비된다. 무관한 변경에 불필요한 Full을 강제하지 않는다.
  수동 Domain 검사가 있다는 이유만으로 selector 결함이라고 단정하지 마라.

6. R3 — 검사 유지·통합·폐기 사유 보완
- 기존 maintain/check_decisions/check_retirements를 재사용한다.
  새로운 pruning framework나 검사 점수 시스템을 만들지 마라.
- 중복 통합은 남는 검사/구조가 해당 보호 책임·알려진 실패·경계·정상 사례를 보존해야 한다.
- 요구/기능 폐기는 유효한 변경 근거, 제거된 진입점·호출자, 남은 요구/소비자 영향,
  active 연결 정리와 이력 보존으로 판단한다. 폐기한 요구에 대체 검사를 억지로 만들지 마라.
  Feature 전체 폐기의 기존 reconciliation과 살아 있는 Feature 내 요구 일부 폐기를 구분하라.
- 타입/DB 제약 등으로 예방을 옮기면 실제 거부·정상 허용과 우회/호출 경로를 확인하라.
- flaky/낡은 runner를 skip 또는 재시도 중 한 번의 PASS로 숨기지 마라.
  비용·검사 수·오래 실패하지 않았다는 이유만으로 고유 방어를 제거하지 마라.
- 코드 검토에서 발견한 '요구 일부 폐기 시 불필요한 대체 증명 차단'은 확정 버그가 아니다.
  focused 사례로 재현한 뒤 필요한 사유 분기만 고치고, 정상 경계는 보존하라.
- 완료 근거: 입증된 중복은 정리, 폐기된 요구는 정당하게 제거,
  다른 실패를 잡는 검사는 유지, 근거 부족은 열린 상태, 실제 비용만 보고.

7. R4 — 실제 위임 수용·패키지·지원 범위
- CI는 영향받는 결정적 회귀·상태/ID/참조·잘못된 완료·재개·조회 불변성을 검사한다.
  자연어 업무 평가는 관련 동작 변경과 최종 후보에 제한하고 작은 수정마다 모두 실행하지 마라.
- 자연어 과업은 Skill 이름/CLI 순서/정답 패치 없이 수행하게 하고,
  실제 개입·재시도·재작업·잘못된 완료·정상 작업 오탐·중복 실행·경과 시간을 기록하라.
  사용량/비용을 제공받지 못하면 추정값을 실측처럼 쓰지 마라.
- 지원 host에서는 실제 발견/진입/context 전달/후속 요청을 확인하라.
  패키지 직접 호출, Agent의 패키지 사용, native 설치 호스트 호출, 보호된 수락을 구분한다.
  기존 설치·전역/인증 변경 없이는 불가능한 부분은 정확한 오류와 조건을 남기고 나머지 작업을 계속하라.
- 별도 범용 doctor부터 만들지 말고 선택한 능력의 사전 조건·오류 안내를 기존 경로에 보완하라.
- 현재는 task 기록 하나당 writer 한 명이다. atomic replace를 동시 갱신 보장으로 표현하지 마라.
  같은 기록 동시 쓰기 기능은 이번 범위에서 새로 만들지 않으며 위임에서 단일 writer를 유지한다.
- 이미 유효한 조회와 검증을 반복하지 마라. 전체 Git 무효화는 입력 의존 범위 증명 없이 완화하지 않는다.
  기준·지도 수정과 최종 검증 순서를 정리해 동일 행동의 불필요한 재측정부터 줄여라.
- canonical과 mapped generated를 동기화하고 관련 회귀·resource drift·distribution·git diff --check를 수행하라.
  Full은 실제 cross-cutting 영향이나 명시적 필요에 맞춰 선택한다.
- 배포 소스 변경에 맞는 버전 정책으로 새 로컬 패키지를 만들고 source commit/버전/해시를 고정하라.
  기존 0.1.44와 새 결과를 구분하고 기존 패키지·설치본을 덮어쓰지 마라.

8. 연두라벨과 기존 시험 자료의 경계
- 원본 연두라벨 코드·스타일·문서·Git refs·데이터·운영 서비스는 변경하지 마라.
  실제 실행이 필요하면 새 격리 소스와 합성 데이터만 사용하고 소유 자원만 종료한다.
- 기존 UI 후보는 사용자 검수 전이다. 동의/의도된 차이/보류 결과를 꾸며 넣거나 제품을 수리하지 마라.
- 과거 UI 결과·스크린샷은 조회/재개/검수 연결의 입력으로 재사용할 수 있으나
  새 버전의 최초 조사 능력이나 개선 효과를 증명한 것으로 계산하지 마라.
- 새 기능의 제품 인수가 필요하면 범용 구현·독립 과업 검증·패키지 고정 후 수행한다.
  연두라벨 전용 정답·지도·adapter를 미리 주입해 범용 성공으로 보고하지 마라.
- 보존된 선택 자료(없어도 durable 설계와 현재 코드로 진행 가능):
  .work/ui-consistency-trial-20261009/{plugin-trial.md,trial-state.json,review.html}
  .work/plugin-maturity-review-20261009/{assessment.html,refinement.html}
  .work/generic-completion-delivery-20261009/implementation-results.md
  이 자료는 원본 저장소 아래에 있으며 새 worktree로 기존 DB/인증/.work 전체를 복사하지 마라.

9. 문서·커밋·main 통합과 최종 전달
- 영향 Feature/검증 연결·현재 guide와 docs/research/agent-workflow-implementation-results.md를 갱신하라.
  새 결과를 최신 구간에 기록하고 과거 실행 결과·환경 한계를 성공으로 덮어쓰지 마라.
- source/tests/docs/generated를 검증된 기능 단위로 커밋한다.
  지침 문구 검사나 PASS 스키마만으로 Agent 업무의 구현 완료를 주장하지 마라.
- 병합 직전 origin과 local main의 이동·dirty 상태를 재확인하고 최신 main을 작업 브랜치에 반영하라.
  충돌은 main의 최신 내용과 이번 변경 의도를 모두 보존해 해결하고 영향받는 검사를 재검증하라.
- 검증된 변경을 로컬 main에 병합하라. main 보호 정책 파일을 수정해서 우회하지 마라.
  이번 요청이 명시적 로컬 병합 권한이므로 같은 허가를 다시 묻지 마라.
  사용자 변경을 보존할 안전한 통합이 불가능하면 완료했다고 주장하지 말고 정확한 차단점과
  검증된 branch/commit을 남겨라. 실패한 기능을 완료로 포장해 병합하지 마라.
- 필요한 실행 증거를 원본 저장소의 작업 소유 .work에 보존한 뒤
  이번에 만든 worktree/branch만 정리하라. 삭제 전 절대경로·소유권·병합 여부·dirty를 확인하라.
  다른 작업 공간/branch/.work를 삭제하지 마라. 최종 주 작업 공간은 가능한 clean main으로 남겨라.
- 최종 보고: R0–R4별 구현/기존 충족/미완료, 실제 사용자 업무와 정상·실패·반례,
  코드와 근거 경로, 개입·재실행·비용 범위, 패키지 버전/해시, 시작·최종·main 커밋,
  원격 동기화/로컬 병합 결과와 남은 한계. HTML 경로는 절대경로로 제공하라.
- push·배포·기존 설치 업데이트는 하지 마라.
```
