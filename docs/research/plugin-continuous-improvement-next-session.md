# 다음 세션: 플러그인 지속 고도화 실행 요청

작성일: 2026-10-12. 상태: **다음 세션용 요청 준비. 아래 후속 구현은 아직 실행하지 않았다.**

현재 목표와 완료 기준은 [설계 §13](agent-coding-system-direction.md#continuous-plugin-improvement)이 소유한다. [§12](agent-coding-system-direction.md#plugin-maturity-yeondoo-link)의 실제 제품 평가·책임 경계도 유지한다. 사용자가 이 문서의 실행 블록을 명시적으로 적용하면 아래 구현·로컬 통합 범위를 승인한 요청으로 진행한다. 문서를 읽는 것만으로 실행하지 않는다.

직전 [0.1.48 실행 결과](agent-workflow-implementation-results.md#yeondoo-plugin-improvement-2026-10-12)와 [실행된 이전 요청](plugin-improvement-next-session.md)은 현재 기능과 과거 인수의 근거다. 완료된 범위를 신규 구현으로 반복하지 않는다. 아래 commit은 인계 시점의 관측값이며 다음 세션에서 다시 확인한다.

## 복사해서 실행할 프롬프트

```text
작업 저장소: C:/Users/YS/Desktop/python/Skill_Management
실제 평가 프로젝트: C:/Users/YS/Desktop/python/yeondoo-link
현재 설계: docs/research/agent-coding-system-direction.md의 §12·§13
참고 분석: docs/research/pstack-analysis.md
실행 요청: docs/research/plugin-continuous-improvement-next-session.md

이 문서의 “복사해서 실행할 프롬프트” 전체를 이번 실행 요청으로 적용한다.
아래 로컬 수정·검증·커밋·플러그인 main 병합·소유 작업 공간 정리 범위를 승인한다.
짧은 계획을 제시한 뒤 실제 구현을 계속해줘. 목적은 플러그인 고도화다.
다음 네 작업만 처리하고 끝내지 말고, 아래 여섯 관점의 남은 공백을 실제 근거로
확인·수리·소비하며 지속적으로 고도화해줘. 화면·문서·테스트 추가만으로 완료하지 마.

목표와 인수
1. 많은 task의 위임과 검증 조회:
   자연어 요청에서 현재 task/Feature/기준/owner/검사를 발견하고, 명시적으로 선택한
   task 묶음의 당시 결과·현재 유효성·NOT_RUN·STALE·UNKNOWN/BLOCKED·raw 생략/없음과
   다음 행동을 구분해 설명할 수 있어야 한다. 실행/조회/재개의 차이를 유지한다.
   공유 owner 변경, 독립 작업의 통합, 중단·다른 Agent의 인수에서 최신 근거를 확인한다.
   예상 사용 규모를 실제 업무와 후보 수로 정하고, 그 규모의 실행·조회 비용을 측정한다.
   한 task writer와 공유 source 통합 owner를 유지한다. 새 큐/DB/coordinator부터 만들지 마.
2. 비즈니스 모델·업무 규칙과 코드 아키텍처 × FE·BE/API·Domain:
   관점별 기대 주장·출처·소유자·적용 판단·실제 근거를 연결한다. 기존 6셀은 확인 질문의
   지도이며 검사 수가 아니다. 없는 계층은 근거 있는 N/A, 미결정은 열린 상태로 둔다.
   저장/경계 영향은 입력→API→규칙 owner→저장→새 조회의 실제 값·ID·부작용을 추적한다.
   상태/effect/의존/호출 계약·실패 복구도 확인한다. 기능 PASS를 전환·수익·사업 가설의
   입증으로 바꾸지 말고, 그런 주장은 자료/실험이 없으면 미검증으로 남긴다.
3. 자가 개선·불편·피드백과 실질 가드레일:
   기대 출처→재현→동작/데이터 흐름→최초 위반→원인 owner 수리→예방→실패/정상/우회
   검증→다음 관련 요청의 소비까지 수행한다. 요구 위반/변경/의도된 차이/관측기 오류/
   환경 제약을 구분한다. runtime validation·type/model·상태 제약·shared component·
   기존 lint/행동 검사 중 실제 원인을 막는 최소 수단을 쓴다. 지침을 늘리는 것으로 끝내지 마.
4. UIUX 가이드의 생성·지속 개선:
   기존 guide와 token/component owner를 재사용한다. guide는 의도·정보 위계·상태·
   variant/예외·반응형·접근성을, 코드는 실제 값·행동을 소유한다. 관련 실제 화면을
   관찰하고 독립 새 문맥의 다른 소비 화면이 재사용하는지 확인한다. 사용자 미검토 UI는 draft다.
5. 실행 가능한 테스트/검증 가이드의 생성·지속 개선:
   기존 명령·registry·adapter로 Launch→Doctor→Drive→Evidence→Cleanup을 연결한다.
   argv/cwd·전제조건·served source/build·fixture/runtime·assertion·exit·raw producer/
   위치·소유 자원 정리와 정리 후 근거 보존을 확인한다. 죽은 가이드/명령과 제품 결함은
   각 owner에서 고친다. 새 작업자에게 정답 명령 순서를 주입하지 않고 소비를 확인한다.
6. 실효성 있는 검증·가드레일만 유지·고도화:
   무엇을 검출하는지와 비용을 확인한다. 중복 통합은 같은 결함/정상 허용 보존,
   요구 폐기는 권한·기준·유지 계약, 구조적 예방 이전은 거부·우회·정상 경로,
   flaky는 관측기 수리·남은 공백으로 판단한다. 삭제 후보가 입증되지 않으면 유지한다.
   고정 검사 수, 오래됐다는 이유의 삭제, 기대값/skip/baseline 완화로 완료하지 마.

권한과 보존
- 플러그인 source/tests/필요한 fixture/schema/reference/generated/docs, 새 전용 branch/
  worktree, 완결 기능 단위 커밋, 검증된 구현의 로컬 main 병합, 이번에 만든 플러그인
  작업 트리/브랜치 정리를 승인한다. 보호 main에 대한 이번 요청의 로컬 통합 승인이다.
- 연두링크는 실제 repo의 별도 개발 브랜치에서 필요한 연결·수리·로컬 커밋을 수행하고
  보존한다. 기존 두 평가 브랜치와 worktree를 지우거나 덮어쓰지 마. 후속 소비 기준을
  정하고 필요하면 그 기준에서 새 브랜치를 만든다. 제품 main 병합·branch 삭제는 하지 마.
- 사용자 변경·기존 작업 상태·연두라벨 원본·기존 설치 Skill/Plugin·인증·전역 설정을 보존한다.
  push/publish/deploy, 설치본 갱신, CODEX_HOME/권한/전역 설정 변경, 비가역 migration,
  외부 비용은 승인하지 않는다. .dev.vars/비밀/원본 DB를 읽어 출력·복사하지 마.
  Azure 재개·유료 provider 호출도 하지 마. 필요하면 구체적인 준비 결과 후 별도 승인으로 둔다.
- 경로 쓰기/실행 제한은 해당 로컬 작업의 정상 승인 절차를 사용하고 권한을 바꿔 우회하지 마.
  이미 승인된 범위는 재확인하지 말고 진행한다. 명시적 manual-disable은 fallback을 사용한다.
- 독립 새 문맥 평가와 필요에 따른 분리된 Agent 검토/위임을 승인한다. 고정 Agent 수는 없다.
  공통 코드·설정·기준은 한 owner가 통합하고, 평가 Agent에게 정답 패치·Skill 순서·채점표·
  감독자 분석을 주입하지 마. 실제 외부 Skill/도구·모델·수동 개입은 별도 기록한다.

현재 상태 재확인
- 적용 AGENTS와 환경 예외, docs/index.md, .harness/project.yaml, docs/testing.md,
  docs/feature-map.md, authoring/resource-map.json, docs/agents/workflow.md를 읽는다.
  설계 §12·§13, 0.1.48 실행 결과, 필요한 refinement/completion 문서를 대조한다.
- 인계 시 플러그인 main은 696f6c6, 구현 efbd5b8, 버전 0.1.48이었다.
  연두링크 main은 220c945; evaluation/plugin-ui-20261012는 bd03682,
  evaluation/plugin-ui-candidate-20261012는 e1b8a09였다. 두 UI는 draft다.
  branch/HEAD/dirty/untracked/worktree/remote 관계를 다시 확인하고 기준을 기록한다.
  플러그인은 fetch로 원격을 확인하되 local 선행 커밋을 보존한다. reset/force/push하지 마.
  제품 remote tracking과 최신 원격 확인을 구분하고 fetch 실패를 성공으로 기록하지 마.
- 기존 .work의 패키지·raw·캡처는 임시 보존 정책을 따른다. 없으면 영향 인수만 재현하고
  없는 근거를 성공으로 채우지 마. 과거 로그를 현재 근거로 재결합하지 마.
- 0.1.48은 미결정 scope의 다음 행동과 동일 hook의 inventory/audit 공유를 이미 구현했다.
  D1–D3/G1–G6/R0–R4/A–C, 기존 task/raw/stale/UI 재사용·quote 폐기를 다시 만들지 마.
  이전 Full은 404 중 402 통과+2 오류였고 두 항목은 별도 재검증했다. Full PASS로 바꾸지 마.
  PStack 문서는 고정 리비전 참고 분석이다. 최신 구현/효과로 주장하거나 절차를 일괄 복제하지 마.

첫 구현 순서
A. 중첩 Git/worktree inventory 오류를 실제 수리한다.
   authoring/scripts/core_harness.py의 static_inventory는 inventory 파일의 parent 후보에
   root 밖 Git 조상까지 포함하고 relative_to(root)에서 실패할 수 있다. 지난 실행은
   소유 worktree를 외부 Temp로 옮겨 피했을 뿐 이 코드는 고치지 않았다.
   현재 재현·호출자 확인 후 focused RED, root 내부 조사 범위를 보존하는 최소 공통 수정,
   같은 실패/일반 repo/실제 하위 repo/영향 setup·maintain·cutover GREEN을 확인한다.
   이미 다른 변경으로 해결됐으면 현재 근거로 확인하고 중복 수정하지 마.
B. 연두링크에서 실제 task·기준·실행·raw·현재 재사용 연결을 완성한다.
   지난 후속은 guide/code 재사용이며 machine task map 연결은 CLI fixture에서만 검증했다.
   기존 README/화면 설계/App/styles/session와 기존 browser/native checks를 정상 입력으로
   사용한다. setup을 시작하면 합의한 전체 제품 기능을 조사·분할·통합하되 미조사 영역은
   PARTIAL로 남긴다. 대표 상담 흐름 하나의 실행을 전체 지도/제품 완료로 표시하지 마.
   기존 map/guide를 재사용하고 필요한 설정·최소 adapter만 둔다. 메모리 상담·장바구니,
   직원 UI PIN 잠금인 현재 MVP에 없는 API/DB/인증을 만들지 마. 없는 층은 이유 있는 N/A다.
   실제 정상/관련 실패·복구→prepare/execute→raw→lookup/reuse를 확인하고,
   공유 owner 변경 후 과거 PASS/current STALE와 필요한 재검증을 제품 task에서 확인한다.
   lookup/task resume의 파일 hash 불변과 실행 0회를 직접 측정한다.
C. 예상 운영 규모에서 hook 후보 발견 비용을 측정하고 필요하면 줄인다.
   task_candidates는 표시 제한 전 후보 레코드를 읽는다. 같은 호출 계산 공유 이후에도
   후보 수·파일 읽기/hash·bundle 평가·elapsed·payload를 계측한다. 실제 병목이면
   선택 task 우선·제한된 후보 미리보기·명시적 상세 조회로 최소 수리한다.
   미조사/생략/모호함을 표시하고 추정 선택하지 마. 다음 호출은 변경을 다시 관찰해야 한다.
   Feature 의존 완전성·누락 변경 검출을 먼저 입증하기 전 전체 Git/bundle stale 방어를 유지한다.
D. 현재 패키지의 native 발견·Skill 호출·hook 자동 전달·호스트 수락을 별도 확인한다.
   직접 CLI 성공과 구분하고 기존 허용 host에서 가능한 경로만 사용한다. BLOCKED면 정확한
   endpoint/권한/미관찰 범위와 재개 조건을 남긴다. 설치·인증·전역 설정 변경으로 우회하지 마.
   이미 구현된 host 기능을 새 기능으로 만들지 말고 현재 소비에서 재현된 결함만 수리한다.

지속 고도화 실행 방식
- 위 A–D 뒤에도 목표별 실제 근거와 남은 공백을 대조하고 다음 유용한 구현을 계속한다.
  다음 항목을 제안하거나 PASS 표를 작성한 것으로 끝내지 마. 같은 조건으로 효과가 없으면
  범위를 줄이고, 정상 업무를 막거나 비용만 늘리는 절차/제약을 근거에 따라 회수한다.
- 매 회차는 현재 근거 확인→한정된 기대/실패 선정→기준과 baseline 패키지 고정→
  focused RED 또는 행동 보존 baseline GREEN→원인 owner 최소 수리→영향 회귀/실제 흐름→
  독립 관련 작업 소비→효과 판정→완결 커밋/로컬 통합으로 진행한다.
  범위가 큰 조정에는 기존 contract를 쓰고 작은 수정에 새 계약·장부를 강제하지 마.
- 개입·거짓 완료·놓친 결함·정상 요청 차단·재작업·중복 실행·시간을 기존 .work에 기록한다.
  제품 실행과 전체 도구 호출, 처리와 환경/사용자 대기를 구분한다. 누락 계측과 조건 차이를
  밝히고 작은 fixture의 속도나 외부 Skill의 도움을 일반 플러그인 우월성으로 주장하지 마.
- 새 문맥에서 자연어 요청→발견→변경/검증→조회→다음 관련 작업까지 연결한다.
  실제 동작을 바꾼 최종 패키지에 영향 인수를 하고, 동일 근거의 반복 실행을 피한다.
  연두링크에 없는 실제 저장/API 경계는 기존 connected-product 예제 등 독립 경계에서
  확인하고 제품 증거와 분리한다. 의미 판단·UI 승인·사업 성과를 hash로 인증하지 마.
- 목표가 충족됐다는 판단은 §13의 여섯 관점별 현재 통합 source·실제 경로·실패/정상·
  후속 소비 근거와 지원 규모/조건으로 내린다. 필요한 근거가 없으면 PARTIAL/BLOCKED다.
  다음 세션으로 나누더라도 첫 네 작업/문서/테스트만 완료하고 전체 목표 완료라고 하지 마.
- 실행 한계나 외부 승인이 필요한 부분만 정확히 인계하고 독립적인 승인된 구현은 계속한다.
  무기한 대기·같은 실패 재시도·효과 없는 규칙 축적을 하지 않는다. 새 세션에는 기존 설계/
  실행 결과와 다음 미완료 항목/재개 조건을 갱신해 같은 목표를 이어갈 수 있게 한다.

검증·패키지·전달
- canonical source를 수정하고 mapped generated 리소스는 기존 sync로 재생성한다.
  영향 docs/feature-map·기준/guide/selector와 현재 기술 사실을 같은 기능 단위로 맞춘다.
  실패 raw·실험·캡처는 .work, lasting 사용법·결정은 기존 durable docs에 둔다.
- 영향에 맞는 workflow/refinement/hook·execution/viewer·연결 제품·Harness·docs 검사를
  선택한다. 실제 cross-cutting/정책 필요 때 Full을 실행하고 환경 오류/skip을 PASS로 숨기지 마.
  powershell -NoProfile -File scripts/sync-skill-resources.ps1 -Check
  powershell -NoProfile -File scripts/validate-distribution.ps1
  git diff --check
  필요 시 python -m unittest discover -s tests -p "test_*.py"
- 새 경로에 패키지를 빌드하고 source commit/version/전체 파일 hash를 고정한다.
  실제 CLI와 새 문맥 소비 전후 무결성을 확인한다. 기존 패키지를 덮어쓰지 마.
- 완결 단위 커밋, main 이동/dirty 재확인, 필요한 통합 검증 후 플러그인 로컬 main에 병합한다.
  필요한 패키지·증거를 먼저 보존하고 정확히 이번에 만든 플러그인 worktree/branch만 정리한다.
  제품 개발 브랜치·커밋·검토 상태와 기존 사용자 작업은 보존한다. 어느 repo도 push하지 마.
- 최종 보고는 실제 사용자 업무/공통 수정→source/commit→실패·정상·반례→raw→독립 후속
  소비→측정 효과/한계와 여섯 관점의 완료/미완료를 연결한다. 제품 수리·adapter·host·플러그인을
  구분하고, 제거/통합/유지한 검사와 이유, branch/package/증거/정리, 다음 미완료 구현을 남긴다.
```

## 실행 범위와 남은 승인

이 요청은 로컬 구현과 실제 인수를 반복하는 범위다. 정기 실행·cron·외부 작업자 서비스나 설치본 갱신을 자동 승인하지 않는다. 사용자의 UI 시안 검토, 사업 성과 자료, 호스트 접근·설치 변경이 필요하면 그 근거/권한은 별도다. 필요한 범위가 막혀 있으면 전체 목표 완료 대신 미완료와 재개 조건을 남긴다.
