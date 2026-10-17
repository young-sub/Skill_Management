> Historical record through 0.1.68; not current execution instructions. See [current design](../agent-coding-system-direction.md) and [current work](../plugin-continuous-improvement-next-session.md). Original bytes: Git ea7e11d.

# 다음 세션: 연두링크 실제 사용을 통한 플러그인 고도화

작성일: 2026-10-12. 상태: **사용자가 이번 실행 요청으로 적용한 범위다. 0.1.48 공통 수리와 실제 저장소 평가·독립 후속 재사용 결과는 [실행 기록](../agent-workflow-implementation-results.md#yeondoo-plugin-improvement-2026-10-12)에 남긴다.**

이 문서의 블록은 수행된 0.1.48 요청을 보존한다. 이후 실제 구현에는 [지속 고도화 다음 세션 프롬프트](plugin-continuous-improvement-next-session-through-0.1.68.md)를 적용한다. 새 목표와 완료 기준은 [설계 §13](agent-coding-system-direction-through-0.1.68.md#continuous-plugin-improvement)에 있으며 이 과거 블록을 다시 실행하는 요청은 아니다.

현재 판단·부족한 점·책임 분리·평가 기준은 [설계 문서 §12](agent-coding-system-direction-through-0.1.68.md#plugin-maturity-yeondoo-link)가 소유한다. 이 문서는 다음 세션에서 실행할 요청이다. 문서를 읽은 것만으로 실행하지 않으며, 사용자가 아래 블록이나 이 문서를 명시적으로 실행 요청으로 전달했을 때 적용한다. 과거 `agent-workflow-next-session.md`와 `agent-coding-next-session.md`의 완료된 실행 블록은 다시 수행하지 않는다.

아래 프롬프트의 실행 전 기준은 플러그인 0.1.47 / `d8068eb`, 마지막 실행 코드 `eb76c6a`, 연두링크 `220c945`였다. 이번 실행에서 실제 플러그인 기준은 clean main `1d7462e`, 연두링크는 clean main `220c945`로 재확인했다. 완료된 공통 수리와 평가를 이 보존된 블록만 보고 반복하지 않는다. 현재 source·commit·패키지·검증 범위와 남은 UI/호스트 판단은 실행 기록에서 확인한다.

## 복사해서 실행할 프롬프트

```text
연두링크의 실제 UI 작업을 평가 과제로 사용해 agentic-coding 플러그인을 고도화해줘.
핵심 목적은 연두링크 개선 자체가 아니라, 자연어 요청에서 관련 Feature·기준·코드·
가이드·검증을 발견하고 실제 작업과 다음 관련 작업까지 재사용하는 플러그인의 완성도다.
연두링크 화면만 바꾸거나 문서·계획·스키마·테스트 추가만으로 끝내지 마.

플러그인 저장소: C:/Users/YS/Desktop/python/Skill_Management
실제 평가 프로젝트: C:/Users/YS/Desktop/python/yeondoo-link
현재 합의: docs/research/agent-coding-system-direction.md의 §12
실행 요청: docs/research/plugin-improvement-next-session.md

권한과 보존
- Skill_Management의 source/tests/필요한 fixtures·schemas·references/generated/docs 수정,
  새 전용 branch/worktree, 기능 단위 로컬 커밋, 필요한 검토 문서의 로컬 main 반영,
  검증된 구현의 로컬 main 병합과 이번에 만든 플러그인 작업 공간 정리를 승인한다.
  이는 저장소 main 보호 정책에 대한 이번 작업의 명시적 로컬 통합 승인이다.
- 연두링크는 실제 저장소의 별도 새 브랜치에서 개발하고 로컬 커밋한다.
  필요하면 그 저장소에 속한 worktree를 사용한다. 변경 브랜치와 결과는 보존하고
  연두링크 main에 병합하거나 브랜치를 삭제하지 않는다.
- 기존 사용자 변경·기존 branch/worktree·연두라벨 원본·기존 설치본·인증·전역 설정을 보존한다.
  push/publish/deploy, 기존 설치 Skill/Plugin 갱신, CODEX_HOME·권한·전역 설정 변경은 하지 마.
  .dev.vars나 자격증명을 읽어 출력·복사하지 말고 Azure 재개·유료 provider 호출도 하지 마.
- 샌드박스에서 연두링크 쓰기가 막히면 해당 로컬 작업에 필요한 정상 승인 절차를 사용한다.
  권한 설정을 바꿔 우회하지 말고, 불가능하면 정확한 BLOCKED 범위와 이유를 남긴다.
  가능한 공통 플러그인 구현은 계속한다. 이미 승인한 범위의 허락을 다시 묻지 마.

1. 현재 상태와 실행 범위 확인
- 양쪽 저장소의 적용 AGENTS.md와 환경 예외를 읽고 branch/HEAD, dirty·untracked,
  worktree, 원격과 local/remote main 관계를 기록한다. 과거 commit/version을 현재로 가정하지 마.
- Skill_Management는 fetch로 원격을 확인하고 로컬 선행 커밋을 보존하며 안전하게 동기화한다.
  reset/force로 덮어쓰지 마. fetch 실패는 최신 원격 확인 성공으로 기록하지 마.
  현재 로컬 main에서 새 전용 worktree/branch를 만들고, 필요한 별도 검토 커밋은 내용과
  main 포함 여부를 확인한 뒤 필요한 것만 반영한다.
- 연두링크도 실제 기준을 확인하고 기존 변경을 건드리지 않는 새 브랜치를 만든다.
  실제 repo의 main은 변경하지 않는다. 추가 비교용 격리가 필요하면 소유권과 출처를 기록한다.
- 플러그인의 docs/index.md, .harness/project.yaml, docs/testing.md, docs/feature-map.md,
  authoring/resource-map.json, docs/agents/workflow.md, 위 현재 설계와 구현 결과를 읽는다.
  refinement/completion 문서는 현재 결함과 완료 범위를 확인할 때만 필요한 부분을 읽는다.
  pstack-analysis는 고정 리비전 참고 자료이지 최신 실행 명령이나 새 기능 목록이 아니다.
- 짧게 기존 기능·현재 재현 공백·영향받는 호출자/Skill/CLI/hook·최소 수정·인수를 제시하고 진행한다.
  G1–G6/R0–R4/A–C/D1–D3와 기존 T5·quote 규칙 폐기를 새 기능처럼 다시 만들지 마.

2. 수정 전 비교 기준 고정
- 현재 소스에서 기존 방식으로 새 로컬 baseline 패키지를 만들거나 이미 존재하는 패키지의
  소스·버전·파일 hash를 검증해 사용한다. 버전 정책을 확인하고 기존 패키지를 덮어쓰지 마.
- 연두링크 source base, 과제, 실제 사용자 판단, 평가 기준, host/model·외부 Skill·도구·
  브라우저/runtime 조건을 먼저 기록한다. 기존 테스트·문서·스크립트를 재사용한다.
- 평가 대상에게 정답 패치·Skill 이름·CLI 순서·채점표·감독자 분석을 주지 마.
  프로젝트의 기존 AGENTS/README/일반 안내와 해당 패키지의 정상 발견 경로는 허용한다.
  가능한 독립 새 문맥을 사용한다. 같은 대화의 역할극은 독립 평가가 아니다.
- 연두링크 UI 요청은 다음을 출발점으로 삼고, 합의한 변경은 모든 비교에 동일하게 반영한다:
  “연두링크는 외국인 관광객을 대상으로 하는 웹사이트이고 아직 MVP 수준이라 UI가 일관적이지 않다.
   먼저 제품에 맞는 콘셉트를 잡고, 대표 화면에 적용해서 다음 화면도 같은 기준을 쓰게 해줘.
   기존 기능과 데이터 처리는 유지해줘.”
- baseline 실행과 초기 발견부터 기록한다. 나중에 수집을 시작해 누락한 시간·개입이 있다면 밝힌다.
  숙련된 감독자가 수동으로 연결해 준 부분은 플러그인의 자동 성공으로 계산하지 마.

3. 연두링크에서 실제 흐름 사용
- README, docs/화면_설계.md, 현재 src/App.tsx·styles.css·session.ts와 관련 호출자,
  기존 브랜드/캐릭터 및 browser 검사로 현재 제품 조건을 확인한다.
- 현재 MVP는 매장 공유 기기 한 대의 상담·상품 탐색 도구이며 상담 서버가 없다.
  초기 두 기기·실시간 기획을 현재 구현으로 취급하지 마. 없는 API/DB를 평가를 위해 새로 만들지 마.
- 공유 기기와 개인 휴대폰 중 우선 사용 장면, 시각 방향 등 아직 확정되지 않은 중요한 결정만
  사용자에게 묻는다. 일반 “좋아”를 특정 시안의 실제 검토로 기록하지 마.
  사용자 판단을 기다리는 동안 독립적인 공통 코드 수리는 계속한다.
- 시작·상품 탐색·상담 질문·직원 화면의 필요한 viewport와 상태를 실제로 관찰한다.
  먼저 대표 화면의 콘셉트와 구현을 만들고, 가이드·token/component·Feature 연결을 함께 남긴다.
  사용자 승인 전 후보는 draft로 표시한다. 모든 화면을 같은 밀도·배치로 만들지 마.
- 고객 언어 우선/한국어 보조, 상품 사진·확인된 사실, 장바구니와 비교 후보의 구분,
  가격·재고 미확인, 직원 UI 잠금, 상담 종료 시 초기화 등 기존 계약을 보존한다.
- 스타일 값·공통 동작은 코드가 소유하고 가이드는 의도·정보 위계·상태·반응형·접근성·
  variant/예외를 소유하게 한다. 기존 지도/문서를 재사용하고 중복 지도를 만들지 마.
  원본의 비밀·실데이터·인증 정보를 평가 입력이나 패키지에 포함하지 마.

4. 실패를 분류하고 공통 플러그인 구현 수리
- 사용 중 발생한 발견 실패·문맥 누락·잘못된 절차 선택·중복 구현·검증 누락·잘못된 완료를 기록하고
  원인이 플러그인/제품/runner·adapter/프로젝트 연결/호스트 중 어디에 있는지 구분한다.
- 우선 현재 재현을 확인할 공통 공백:
  a. READY_FOR_REVIEW + 활성 6셀 UNDECIDED + coverage PARTIAL + 빈 next_actions 조합.
     누락된 적용 판단과 다음 행동을 보여주되 현재 유효한 검사 결과를 보존한다.
     source-only·작은 수정·이유 있는 N/A는 정상 허용하고 6개 검사를 강제하지 마.
  b. 같은 hook 안의 중복 inspect/inventory와 후보 발견 비용.
     수정 전 읽기·hash·bundle 평가·시간을 측정하고 같은 호출의 계산 공유부터 최소 수정한다.
     긴 payload에서도 정확한 task·범위·Feature/기준·근거 상태·다음 행동·상세 참조를 보존한다.
     모호한 task를 추정 선택하지 마. 미조사·생략 상태도 표시한다.
- 이미 고쳐진 항목은 현재 실행으로 확인하고 중복 구현하지 마. 새로운 비단순 분기는
  focused RED 후 공유 소유 코드에서 고치고 실패/정상/관련 경계의 GREEN을 확인한다.
- 의도·관련성·원인·UI 의미·검사 가치는 Agent가 판단한다. 결정론적 코드는 명시된 ID·연결·
  상태 전이·실행·raw·변경/stale·정확한 조회와 집계를 소유한다. 프로젝트가 실제 assertion을 소유한다.
  파일/hash·LLM 제출을 의미적 정답·실제 사용자 승인·신원 증명으로 취급하지 마.
- 가드레일은 원인 소유 코드, 구조·타입/제약·기존 검사·공유 component에 우선 둔다.
  연두링크 전용 규칙을 공통 플러그인에 하드코딩하지 마. 새 승인 DB·조사 장부·일반 workflow engine·
  대형 dashboard·고정 agent 수·매번 전체 setup을 만들지 마.
- 공유 지도 변경의 무효화 범위를 줄이려면 Feature 의존성 완전성과 누락 변경 검출을 먼저 증명한다.
  그렇지 않으면 전체 Git/bundle stale 방어를 유지하고 비용을 명시한다.

5. 수정 후 비교와 독립 후속 재사용
- 같은 제품 base·요청·콘셉트 결정·전제조건에서 수정 패키지를 사용해 비교한다.
  제품 코드와 가이드가 개선된 상태만 후보에게 주면서 플러그인 자체 개선이라고 주장하지 마.
  분리할 수 없는 효과와 host/model/도구 차이는 한계로 남긴다.
- 첫 구현을 보지 않은 독립 Agent에게 예를 들어 “상담 질문 화면도 현재 연두링크 UI 기준에 맞춰
  정리해줘. 기존 질문과 선택 동작은 유지해줘”라고 요청한다. 과거 대화·정답 순서를 주입하지 마.
  선택한 대표 화면에 따라 겹치지 않는 후속 소비 화면을 정한다.
- 실제로 가이드·공유 owner·예방·활성 검사를 발견했는지, 정상/의도된 variant/오류 복구가 유지되는지
  주 Agent가 diff·캡처·raw·실행 수를 직접 확인한다. Agent의 성공 주장만 믿지 마.
- 제한된 task 묶음에서 현재 유효/NOT_RUN/과거 PASS지만 STALE, 요약 생략과 raw 관측,
  raw 없음/만료, 환경·runner 문제와 제품 결함을 구분해서 설명한다.
  lookup/task resume 전후 파일 hash와 실제 검사 실행 수로 읽기 전용·실행 0회를 확인한다.
- 같은 base의 독립 task가 공유 owner 변경 후 기존 근거를 어떻게 재검토하는지 확인한다.
  기존 유효한 인수를 재사용하고, 새 변경이나 소비 실패가 없는 범위는 반복하지 마.
  같은 task 레코드에 동시에 쓰지 말고 공유 소스·설정은 한 owner가 통합한다.
- 독립 실행이 불가능하면 실제 CLI/패키지와 가능한 구현 검증은 끝내고 자연어 평가는 미검증/BLOCKED로 남긴다.
  사용자가 보지 않은 UI 후보를 승인된 것으로 기록하지 마.

6. 검증 가치와 효과 판정
- 6셀은 검증 질문의 지도다. 관련 사용자 경로와 업무 규칙·아키텍처를 검증하고,
  없는 계층은 근거 있는 N/A로 둔다. 작은 UI 수정에 무관한 전체 제품 검사를 강제하지 마.
  실제 데이터 경계가 바뀌면 입력→소유 로직→저장→새 조회의 값·식별자를 추적한다.
- UI 기능 검사와 시각·사용성 검토, 사업 가치·전환·수익 가설을 구분한다.
  코드 PASS를 디자인 승인이나 사업 성과 증명으로 보고하지 마.
- 중복 검사는 남는 검사의 같은 결함 검출·정상 허용, 요구 폐기는 권한·기준·소스·유지 계약,
  type/constraint 이동은 금지·우회·정상, flaky는 관측기 수리·남은 공백으로 판단한다.
  rule-only 폐기에 entrypoint/caller 삭제나 폐기 규칙의 replacement test를 강요하지 마.
  불필요함이 입증되지 않으면 유지하고 이유를 설명한다.
- 잘못된 완료·놓친 결함·사용자 개입·정상 요청 차단·재작업·중복 실행·소요 시간을 기록한다.
  제품 실행과 도구 호출, 실제 처리와 대기 시간을 구분하고 힌트·오류·재시도를 숨기지 마.
  효과가 없으면 없다고 보고하고 비용만 늘리는 제약을 줄인다.

7. 패키지 검증·로컬 통합·보고
- authoring/resource-map.json의 canonical source를 수정하고 mapped generated Skill을 기존 스크립트로 재생성한다.
  관련 source/tests/fixtures/schema/reference/generated/docs를 기능 단위로 함께 반영한다.
  docs/feature-map.md와 현재 기술 문서를 실제 변경에 맞추고, raw·평가 로그는 .work/에 둔다.
- 실제 영향과 저장소 정책에 따라 workflow/refinement/hook, verification execution/viewer,
  연결 제품 및 repository docs 검사를 선택한다. 기존 연두링크 검사도 영향 범위에 맞춰 실행한다.
  powershell -NoProfile -File scripts/sync-skill-resources.ps1 -Check
  powershell -NoProfile -File scripts/validate-distribution.ps1
  git diff --check
  cross-cutting 영향이나 정책상 필요하면 python -m unittest discover -s tests -p "test_*.py".
  같은 검사를 횟수 채우기로 반복하지 마. 환경 실패/skip/미실행을 PASS로 기록하지 마.
- 기존 빌드 방식으로 새 패키지를 만들고 버전·소스 커밋·파일 내용/hash를 연결한다.
  실제 패키지 CLI 소비 전후 무결성을 확인한다. native 설치본 발견/호출·hook 자동 전달·
  보호 호스트 수락은 직접 CLI와 별도 검증이며 설치·인증·전역 설정을 변경해 우회하지 마.
- 완결 단위마다 커밋하고 Skill_Management main 이동 여부를 확인한다.
  이동했다면 최신 통합 상태에서 필요한 검증 후 로컬 main에 병합한다.
  필요한 증거·패키지를 먼저 보존하고 정확한 경로·소유권을 확인한 이번 플러그인 worktree/branch만 정리한다.
  연두링크 개발 브랜치·커밋과 검토에 필요한 작업 상태는 보존한다. 어느 저장소도 push하지 마.
- 최종 보고는 플러그인 공통 수정과 연두링크 평가용 변경을 분리한다.
  RED→GREEN, 수정 전후/새 문맥 결과, 검증 유지·통합·제거 이유, 남은 미구현/미검증/BLOCKED,
  두 저장소 branch/commit·원격 확인 범위·패키지·증거·정리 결과와 필요한 사용자 판단을 적는다.
  연두링크 화면이 좋아졌거나 문서·테스트가 늘었다는 사실만으로 플러그인 고도화 완료를 선언하지 마.
```

## 이 프롬프트가 완료를 뜻하지 않는 범위

전체 UI 시안 승인, 연두링크 전체 화면 통일, 전체 프로젝트 지도 조사, 현재 설치본 자동 발견, 보호 호스트 수락, 장기 무인 운영, 일반 품질·비용 우월성은 각각 실제 근거가 필요하다. 범위를 넓히는 대신 수행한 것과 남은 것을 구분한다. 평가 프로젝트의 브랜치는 다음 검토를 위해 남기며 플러그인 작업 공간 정리에 포함하지 않는다.
