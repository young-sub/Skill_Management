> Historical record through 0.1.68; not current execution instructions. See [current design](../agent-coding-system-direction.md) and [current work](../plugin-continuous-improvement-next-session.md). Original bytes: Git ea7e11d.

# 다음 세션: Agent Coding 업무 위임 체계 구현·실제 검증

작성일: 2026-10-05. 상태: **명시적 실행 요청에 따라 source/generated 구현과 독립 제품·Agent 수용 검증을 수행한 실행 기준**. 실제 결과와 남은 BLOCKED 범위는 [구현 결과](../agent-workflow-implementation-results.md)에 연결한다. 아래는 [현재 결론](agent-coding-system-direction-through-0.1.68.md)과 [R01–R16 검토·수용 과업](agent-coding-requirements-review-through-0.1.68.md)을 구현하기 위해 사용한 프롬프트다. 기반 이식과 첫 Labeler 파일럿의 [결과](../labeler-verification-pilot.md)와 [이전 프롬프트](agent-coding-next-session.md)는 과거 근거이며 재실행 지시가 아니다.

## 실행에 사용한 프롬프트

아래 블록은 수행 범위의 기록으로 보존한다. 이후 사용자 합의의 전체 Feature init·매 고도화 갱신·환경 집행·위임 성과 기준과 U1–U7은 [완성 기준과 후속 구현](agent-workflow-completion-design-through-0.1.68.md)이 소유한다. 아래의 한 중요 흐름 연결만으로 최초 setup을 완료하는 범위는 새 전체-init 요구를 충족하지 않는다. 재개 시 현재 source/host와 새 단위의 인수 기준을 확인하며 과거 통제 결함을 일괄 재주입하지 않는다. 새 권한 없이 일반 설치·운영 적용으로 범위를 넓히지 않는다.

현재 새 구현은 [연두링크 사례 기반 플러그인 고도화 프롬프트](plugin-improvement-next-session-through-0.1.68.md)를 사용한다. [전체 역할 분리·고도화 프롬프트](agent-workflow-next-session-through-0.1.68.md)도 이미 수행된 범위의 기록이다. 아래 과거 실행 블록을 다시 실행하거나 현재 권한으로 해석하지 않는다.

```text
작업 저장소: C:\Users\YS\Desktop\python\Skill_Management
현재 설계: docs/research/agent-coding-system-direction.md
이전 실제 근거: docs/research/labeler-verification-pilot.md

현재 설계에 따라 Agent에게 업무를 위임하고 실제 검증·피드백·기준 고도화를 연결하는 최소 체계를 구현해라. Skill 파일을 생성하거나 테스트가 통과했다는 보고에서 끝내지 마라. 사용자 형태의 요청으로 새 체계를 실제 사용하고, 구현 내역과 테스트 근거를 연결해 어떤 업무를 맡길 수 있게 됐는지 보고해라.

1. 현재 상태와 권한을 확인해라.

- AGENTS.md, docs/index.md, .harness/project.yaml, docs/feature-map.md, docs/testing.md, docs/agents/workflow.md, 현재 설계 §11, 요구사항 검토의 T1–T6, 이전 파일럿 결과와 근거 재확인 한계를 읽어라. 편집 경로의 nested AGENTS.md와 capability exception을 확인해라.
- 문서 정리 시작 기준은 wp-20261004-agent-coding-foundation의 c1e4b9e6ea22605c3458f2c859cf1fac49dde4c5였다. 이후 문서 commit을 포함한 현재 branch/HEAD/dirty를 다시 기록해라. 현재 기반을 원격 main이나 donor로 덮어쓰거나 이미 완료한 capture/launcher/카탈로그 정리를 반복하지 마라.
- 관리 저장소 source·generated·관련 문서와 작업 소유 .work 아래 독립 시험 환경의 수정·로컬 검증·기능 단위 commit이 이번 실행 범위다. 일반 설치본·전역 설정·원본 Labeler의 파일/Git refs/DB·보호 branch를 변경하지 마라. push/publish·원격 migration·외부 메시지·실데이터 전송·새 유료 provider/자원·권한 완화는 포함하지 않는다.
- 짧은 실행 계획으로 구현·검증 순서를 제시하고 진행해라. 제품의 미해결 결정만 분리하고 설계 전체를 다시 승인받지 마라. 여러 위험 경계에 persistent coordination이 필요하면 기존 Work Packet을 사용하되 모든 작은 작업의 선행 조건으로 만들지 마라.

2. 하나의 업무 진입점과 두 검증 능력을 구현해라.

- agent-workflow의 업무 조정, setup-project-verification의 최초 연결, maintain-project-verification의 제품 기준 유지 책임을 구현한다. 기존 diagnose·실행 흐름·maintain-agent-harness·UI 능력·multi-agent-review로 충분한 부분은 재사용한다. 세 Skill이라는 파일 수를 목표로 하지 말고 기존 발견 경로로 부족한 책임만 추가해라. Skill 이름·호출 순서 없는 짧은 요청으로 진입점과 실제 선택이 연결되는지 T1/T4에서 확인해라.
- agent-workflow는 초기 연결/구현/검증·조회/통합 유지보수/피드백·재발 방지/UI 기준 개선의 내부 Playbook을 선택한다. Playbook마다 별도 Skill을 만들거나 매 요청에 모든 참조를 로드하지 마라. 같은 요청에 필요한 절차를 조합하고 공유 조사·근거는 재사용한다.
- 조회·설명·감사만 요청한 경우 쓰기·재실행을 하지 않는다. 수정이 요청된 경우 범위 내 수리까지 이어간다. 작고 명확한 작업은 direct development가 가능해야 한다. 전체 lifecycle·Full·항상 다중 Agent를 강제하지 마라.
- setup은 기존 map/guide/명령/UI 자산·환경을 조사하고 첫 실행 경로를 마련한다. T1의 새 task-local 대상에서는 기존 제품 기준을 유지한 채 pilot 전용 연결이 없는 상태에서 최초 생성·실행을 확인하고 이미 연결된 상태의 재사용과 구분한다. maintain은 제품 의미·실제 명령·Feature 누락·UI drift·검증 가치를 점검한다. Harness maintain의 mapping/cohort/retention 책임과 구분하되 필요한 요청에서는 함께 수행한다.
- authoring/resource-map.json과 public-resource-manifest, catalog, installer, inventory의 실제 소비자를 조사해 canonical source/generated 경로에 반영한다. 독립 Skill이 다른 Skill의 private helper를 암묵적으로 참조하지 않게 해라. 공통 helper는 한 source에서 생성하거나 실행 경로를 명시한다. 전역 AGENTS나 개인 memory는 수정하지 마라.
- donor b40396a63b1031b8a3958d376fb3cc46499a9191의 skills/<name>/SKILL.md와 필요한 참조를 git show로 읽는다. setup-project-verification의 환경 식별은 축소 도입하고 ui-refine은 UI 절차, improve-workflow는 원인별 개선, resume-work는 기존 재개에 흡수한다. clear-writing과 후보 전체 병합은 핵심 범위에서 제외한다.
- PStack의 고정 조사 docs/research/pstack-analysis.md를 사용한다. 필요한 원문만 확인하고 Mode→Playbook→필요 능력 선택, Feature 기반 검증, 구조로 교훈 반영을 가져온다. 모든 원칙의 Skill화·전체 fan-out·verdict 문자열을 실행 증명으로 취급하는 방식은 복제하지 마라.

3. 프로젝트 기준과 실행·결과 조회를 연결해라.

- 프로젝트 Feature Map은 ID/이름·사용자 행동·기대 결과·business invariant·FE·BE/API·Domain·데이터 side effect·검증 방법과 요구의 출처를 연결한다. 최초 setup이 범위를 표시하고, 변경자가 구현 전 기준을 확인하여 같은 기능 diff/commit에서 map/guide/활성 selector를 갱신하며, 완료 검증자가 누락·삭제 잔존·죽은 명령을 대조한다. maintain은 요청·회귀·drift가 계기다. 구현을 그대로 요구사항으로 승인하지 마라.
- 비즈니스 모델/아키텍처와 FE/BE/Domain 책임을 현재 설계 §11의 변경별 기준으로 선택한다. external boundary → parsing/validation → typed domain model → pure business logic → persistence/external adapter를 실제 caller와 대조하고 invariant·소유 경계·선택 검사·관찰·제외 이유를 연결한다. UI 입력/전송/저장/재표시나 계층 계약 변경에는 관련 실제 E2E를 수행한다. 상태/타입/registry/reducer/command-event/domain module은 관찰한 복잡성 원인에 맞을 때만 검토한다.
- 프로젝트 verify-product·ui-system 역할은 기존 AGENTS/index/guide·코드·명령·adapter에서 발견·실행할 수 있게 연결한다. 기존 안내로 부족한 반복 판단이 있을 때만 얇은 local Skill을 만든다. Harness 설치를 모든 프로젝트에 강제하거나 업무 정답·token을 공통 Skill에 복제하지 마라.
- 검증 계획과 실행 결과를 우선 CLI/파일 요약으로 조회하게 해라. Feature/check·요구/기준 revision·기대/실제·관점/영역·선택/제외·필수 여부·실행 상태·판정·명령/cwd/source/runtime·native exit/case/skip/error·구현 diff를 특정 run ID와 raw assertion/관찰 위치로 연결한다. capture는 실행 사실, 프로젝트 adapter/검증자는 제품 의미를 소유한다. check 범위 native 실패를 바로 제품 결함으로 분류하지 마라.
- scripts/run_check.py를 재사용한다. 현재 scripts/verify_product.py는 이 관리 저장소 unittest 전용이다. Labeler native JSON·browser 관찰을 그 parser에 억지 적용하거나 unittest-looking 성공 출력을 만들지 마라. 필요한 조정 도구는 실제 프로젝트 adapter와 capture를 연결하는 최소 형태로 구현한다. 모든 runner의 범용 parser·dashboard·MCP·중앙 DB는 만들지 마라.
- 계획·미실행·skip·not_required는 PASS와 구분한다. 필수 0건/전부 skip, 다른 대상/run/Feature, 오래된 근거, unavailable, native 실패가 후속 shell 성공에 가려지는 경우를 성공으로 처리하지 마라. 부분 PASS와 BLOCKED를 함께 보여라. 현재 capture가 인증하지 않는 fixture/server/untracked/Agent 신원은 별도 확인하고 한계를 남겨라.
- 결과 조회는 실제 raw evidence를 소비하고 원래 판정과 현재 재사용 가능/stale/확인 불가를 구분한다. 관련 source·기준·명령·dependency·fixture·served runtime 식별값/참조가 없거나 달라지면 현재 PASS로 재사용하지 마라. raw 누락/보존 만료를 숨기지 말고 미실행/skip/not_required를 성공 수에 더하지 마라. ISSUES와 BLOCKED가 함께 있으면 둘 다 보존한다. 같은 raw는 한 번 기록하고 Markdown·JSON·YAML에 수동 복제하지 마라.

4. 원본을 보존한 실제 제품 시험 환경을 준비해라.

- 첫 소비자는 독립 Labeler다. 이전 .work/labeler-verification-pilot-5a80b570/repo의 최종 commit ecd7db768aef3c17c0ffc9834759944cf013b0f0와 guide/driver/adapter가 존재하는지 확인한다. 기존 근거는 read-only 재사용하고 새로운 .work/agent-workflow-pilot-<run-id>에 tracked source를 export해 git init한 독립 repo를 마련한다. 원본 .git/worktree/origin을 공유하지 마라.
- 이전 clone이 없으면 원본 C:\Users\YS\Desktop\python\labeler의 고정 파일럿 source 1a10164ae7a3458e62b4accf8d52b20319f007e0를 읽기 전용으로 확인해 export한다. 없거나 기준을 바꿔야 하면 차이를 기록한다. 기존 사용자 폴더를 삭제·덮어쓰거나 원본 branch를 전환하지 마라. clone 부재가 source/runtime 한계이면 이를 분리해 관리 체계 구현은 계속한다.
- .dev.vars/.env/credentials, 미커밋 파일, 원본 DB/R2·node_modules·ignored 산출물을 복사·읽기·출력하지 마라. lockfile, 로컬 합성 fixture·D1/R2·독립 cache/profile/port를 사용한다. 실제 계정·인증 토큰을 가져오거나 제품에 인증 우회를 추가하지 마라.
- 프로젝트 AGENTS/문서·package script·pretest/migration의 부작용을 확인한다. 소유 loopback 서버의 source/build/process/URL과 저장소를 연결한다. HTTP 200만으로 대상 확인을 대신하지 마라. 기존 사용자 서버·브라우저는 종료하지 마라.
- 수동 비활성화된 in-app browser를 재시도하지 않고 기록된 Playwright fallback을 쓴다. 환경·파일 접근 격리·소유 자원 분리를 구분하고 실제 제한을 유지한다.

5. 구현과 실제 업무 검증을 병행해라.

- non-trivial 행동 변경은 가능한 경우 집중 실패/평가를 먼저 관찰하고 수정 후 동일 기준으로 확인한다. 동작 보존은 baseline/equivalent GREEN을 사용한다. 환경 실패를 기능 실패·성공·동등성으로 세지 마라.
- 아래 A–E를 요구사항 검토의 T1–T6으로 구체화해 실제 사용자 형태의 짧은 요청으로 수행한다. 임시 설치본과 프로젝트 발견 경로가 사용되는 새 context, 요청·host/Skill source·도구 호출·실제 diff·run/raw 참조를 남겨라. 평가 정답과 정상 반례는 먼저 고정하되 Agent에게 호출 순서나 정답 패치를 안내하지 않는다. 기존 협업 Agent가 임시 설치본을 읽지 않았다면 native/역할 분리 증거일 뿐 새 Skill 발견 증거가 아니다. 새 paid provider나 권한 완화 없이 불가능하면 해당 행동 수용은 BLOCKED다.

A. 검증 가시성과 업무 선택
- “상품 저장 기능을 검증하고 어떤 확인을 했는지 보여줘”로 관련 native/browser 경로를 선택·실행·취합하는지 확인한다. FE 입력 → API → 저장 → reload/readback을 대조한다. 관련 아키텍처 경계도 검토하고 근거 유형을 구분한다.
- 정상 구현은 선택 기준에서 PASS, FE 가격 전송 +1과 같은 분리된 통제 결함은 ISSUES여야 한다. 기존 BE 검사가 통과한 것과 FE/browser 결함 검출을 함께 보여야 한다. driver·oracle는 비교 중 고정한다.
- “기존 검증 결과만 보여줘”라는 정상 반례에서 재실행·제품 수정·불필요한 Skill fan-out이 없는지 확인한다. 현재 source가 달라졌으면 과거 결과의 유효 범위를 알린다.

B. 피드백·원인 수리·가드레일
- “입력한 가격과 저장 가격이 달라. 원인을 추적하고 재발하지 않게 고쳐줘” 등의 실제 의미가 있는 과업을 수행한다. 실제 결함이 없으면 독립 시험 branch의 작은 통제 결함으로 명시한다.
- 기대 결과 → 공용 경계·상태/데이터 흐름 → 원인 → 최소 수정 → 사용자 흐름/적절한 구조적 가드레일을 연결한다. 원래 실패 RED/GREEN, 가까운 정상 가격·수량/오류 거절 사례를 확인한다. synthetic 결함을 원본 제품 버그로 보고하지 마라.
- 큰 저장·이력/미묘한 FE 변경에는 구현자와 검증자의 역할·context를 분리해 실제 위임을 시험한다. bounded assignment, 고정 요구·base/diff·환경·원본 근거를 제공하고 제품·정답 수정은 검증자에게 허용하지 않는다. 필요한 소유 fixture/evidence 출력 권한과 실제 host 제한을 맞춘다. 주 Agent가 중요 주장을 확인한다.
- 독립 verifier 파일만 생성하고 완료하지 마라. 실제 context 분리·도구 실행을 확인한다. ISSUES는 근거와 소유자를 붙여 구현자에게 돌려보내고 새 diff에 영향받은 검사만 재실행한다. BLOCKED는 원인·fallback·재개 조건을 보존하고 독립 작업을 계속한다. 같은 근거의 반복은 가설/수단을 바꾸며 무한 loop를 만들지 않는다. 지원 agent 형식은 로컬 host/공식 문서를 확인하고 모델/provider 설정을 임의 변경하지 않는다.

C. 통합 유지보수와 Feature 갱신
- 독립 clone의 실제 Harness 설정과 제품 검증을 대상으로 guide/명령 drift와 Harness mapping drift가 함께 있는 T4 상태를 마련한다. “개발 체계를 점검하고 필요한 부분을 개선해줘”라는 한 요청에서 양쪽 책임을 선택·수리·재검증하는지 확인한다. 이 정상 조합 과업을 Harness 해당 없음으로 대체하지 마라. 별도 비-Harness 반례는 자동 설치·불필요한 fan-out 없이 끝내고 공유 조사/실행은 중복하지 않는다.
- 기대 기준을 낮추지 않고 누락 연결/명령을 수리해 실제 실행한다. T3/T5의 기능 변경에서 영향 map/guide를 같은 diff/commit에 갱신하거나 변경 불필요 이유를 근거로 남겨라. T4의 작은 상태 대조로 새 기능 연결 누락·삭제 기능의 활성 selector 잔존·죽은 명령을 탐지하고, 삭제된 기능의 과거 결과는 보존되는지 확인한다. audit-only 반례에서는 수리하지 않는다.
- 한 영역의 환경 실패/누락이 다른 영역의 PASS에 가려지지 않는지 확인한다. 자연어 선언이나 ledger row만으로 수행 여부를 판정하지 마라.

D. UI/UX 기준과 재사용
- 기존 token/component/guide를 조사해 ui-system으로 연결한다. 영향을 주는 작은 실제 화면 변경이나 분리된 UI 불일치로 업무 흐름을 시험한다. 제품에 문제가 없으면 정상 대조 또는 명시적인 synthetic drift를 사용한다.
- desktop/mobile, 관련 focus/keyboard, loading/empty/error 중 영향 상태, 저장 관련 readback을 실제 확인한다. screenshot 존재만으로 interaction·저장 성공을 주장하지 마라. 관찰 타이밍 오류를 UI 버그로 고치지 마라.
- 반복 불일치는 기존 공통 token/component·상태 API에서 고치고 guide의 해당 기준만 갱신한다. T5의 두 번째 새 context 요청에서 이전 장문 지시 없이 갱신된 기준/공유 구현을 발견·재사용하는지 실제 확인한다. Button/Input/Table/Modal 등 해당 공통 구성과 영향 상태의 source 경로·reference를 연결하고 값은 문서에 수동 복제하지 않는다. 의도된 예외는 정상 반례로 보존한다.

E. 유용한 검증 유지·중복 정리
- 변경 범위에서 중복/구현 고정/비용 높은 검사 후보를 검토한다. 축소·통합할 근거가 있으면 같은 실패 검출·정상 반례를 유지한 뒤 정리한다. 근거가 없으면 보존 이유를 보고하며 억지 삭제하지 않는다.
- 기존 capture의 0건/skip/stale/wrong-target/report 회귀 근거는 재사용하고 새 연결의 위험만 추가 검증한다. 구조적 enforcement가 생겼다는 이유로 사용자 오류·cross-layer 관찰까지 무조건 제거하지 마라.

6. 배포와 실제 Agent 사용을 구분해 검증해라.

- 변경 로직·소유 경로에 맞는 기존 Harness/배포 검사를 선택한다. source/generated가 바뀌면 resource drift·distribution·git diff --check를 수행하고 관련 문서 링크를 검사한다. 테스트가 끝나면 새 실패·변경·미해결 위험 없이 무조건 확대·반복하지 마라.
- 새 능력을 임시 project/CODEX_HOME에 설치해 파일 집합·버전·entrypoint와 fresh host 발견을 확인한다. 실제 사용 가능한 승인된 host/Agent 실행 경로를 먼저 확인하되 일반 설치본은 갱신하지 않는다. T1–T6의 실제 선택·실행·갱신 증거와 설치 메타데이터를 구분한다. host/model 실행이 막히면 원인을 보존하고 허용된 source/native 구현을 계속하되 위임 효과나 전체 완료를 주장하지 않는다.
- Plugin은 공통 생성 패키징·버전·설치 범위로 정리한다. 프로젝트 업무 정답·UI/map/adapter는 프로젝트에 둔다. 이번 업무 수용 기준을 끝내기 전에 공개 Plugin·MCP·hook·dashboard로 확대하지 않는다. 추가 임시 host 연결이 실제 필요하면 기존 probe를 재사용한다. 직접 CLI/CI를 보존한다.
- Windows CLI 격리·model startup 장애를 Skill 품질로 집계하거나 보안 제한을 낮춰 통과시키지 마라. 단일 주 Agent의 안내를 그대로 따른 실험과 새 context에서 독립적으로 능력을 선택한 실험을 구분해 보고한다.

7. 문서·commit·보고까지 끝내라.

- verified functional unit마다 필요한 source/tests/docs/generated를 함께 commit하고 dirty baseline·원본을 보존한다. 제품 시험 commit과 공통 체계 commit을 구분한다. 관리 저장소 Feature Map은 실제 가능해진 기능·실행 명령만 갱신한다. 미구현 계획을 현재 기능 row로 만들지 마라.
- 새 실행의 상세 근거·fixture·raw Agent 기록·screenshot/PDF는 소유 .work에 둔다. 지속적으로 참조할 결과는 docs/research/agent-workflow-implementation-results.md 하나에 정리하고 docs/index.md에서 연결한다. 이 방향 문서와 프롬프트의 구현 상태·다음 과제를 실제 결과에 맞춰 갱신한다.
- 최종 보고는 다음 표로 구현과 검증을 연결한다:
  가능해진 사용자 업무 | 구현 위치/commit | 실제 수행 요청 | 정상·결함·반례 결과 | raw evidence | 미검증 범위
- 별도로 소스 구현/임시 설치/제품 동작/Agent 행동/실환경 적용을 구분한다. 채택·흡수·제외한 구성요소, Plugin 전환 범위, 유지·제거한 검사와 근거를 명시한다. 파일 수·테스트 개수·coverage를 업무 위임 가능성의 증거로 제시하지 마라.
- 예를 들어 “어떤 검증을 했는지 조회 가능”, “사용자 피드백에서 원인 수리·회귀 방지까지 수행”, “Feature와 UI 기준의 drift를 실제 수리”가 어떤 과업과 결과로 확인됐는지 설명한다. 실패/차단된 기능은 그대로 보고하고 미래형 설명으로 완료 처리하지 않는다.
- 소유 process·브라우저만 종료하고 재현 근거·독립 repo는 기존 보존 정책에 따라 남긴다. 기존 사용자 자원이나 미커밋 파일은 정리하지 않는다.
```

## 완료 판단

필수 업무는 요구사항 검토 T1–T6의 최초 연결·선택/조회·피드백/가드레일·양쪽 통합 유지보수/Feature lifecycle·UI 기준 재사용·검증 가치 판단이다. A–E와 같은 과업/근거를 재사용하며 별도 대규모 benchmark를 만들지 않는다. 구현·실제 실행·결함 검출·정상 반례가 연결되어야 하고, 근거가 없어서 검사를 보존한 판단은 허용된다. 원본 제품 적용·일반 설치·공개 Plugin 전환은 범위 밖이다. Agent 환경 때문에 위임 검증이 막히면 native 능력과 BLOCKED인 통합 위임을 분리하고 전체 완료로 표시하지 않는다.
