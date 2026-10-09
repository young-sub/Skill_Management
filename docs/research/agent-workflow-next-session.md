# 다음 세션: 범용 플러그인 완성 후 실제 제품 인수

갱신일: 2026-10-09. [방향 합의](agent-coding-system-direction.md)와 [완성 설계 §0의 G1–G6](agent-workflow-completion-design.md#generic-plugin-first)를 실행하는 프롬프트다. 기존 U1–U7의 책임·업무 기준은 유지한다. 과거 실행 지시의 Labeler 선행 연결·임시 설치·관리자 환경 구축을 재개하지 않는다. 이 문서 작성은 아래 기능의 구현 완료가 아니다.

문서 작성 시 확인한 최신 구현은 23e5d152038abf30765a019729c02bc05f640b5d, 소스 버전 0.1.42다. main과 설치본의 현재 상태는 다음 세션에서 다시 확인한다. [현재 구현 결과](agent-workflow-implementation-results.md#connected-actual-product-use-2026-10-07)와 §0의 알려진 결함을 출발점으로 사용하며 전체 과거 이력을 다시 조사하지 않는다.

아래 블록을 다음 세션의 사용자 요청으로 전달한다. 문서만 열었다는 이유로 실행 권한을 추정하지 않는다. 현재 사용자의 추가 범위·권한 지시가 우선한다.

```text
/goal 범용 agentic-coding 플러그인을 실제 사용자 업무가 완결되도록 고도화하고,
제품 독립 검증과 패키지 고정을 마친 뒤 연두라벨에서 실제 인수 시험을 수행하라.

저장소: C:\Users\YS\Desktop\python\Skill_Management
새 worktree 부모: C:\Users\YS\Desktop\python\Skill_Management-worktrees

먼저 다음 문서를 읽고 승인된 방향을 이어가라.
- AGENTS.md, docs/index.md, .harness/project.yaml
- docs/research/agent-coding-system-direction.md
- docs/research/agent-workflow-completion-design.md의 §0 및 관련 U1–U7
- docs/research/agent-workflow-implementation-results.md의 현재 구현·한계
- docs/plugins.md, authoring/resource-map.json
필요한 소유 코드·호출자·테스트를 확인하되 전체 이력 재조사로 시작하지 마라.

1. 범위와 작업 기준
- 목적은 범용 플러그인의 완성이다. 연두라벨은 이후 사용할 실제 제품 인수 대상이다.
- 범용 기능 완성 → 제품 독립 기능 검증 → 패키지 고정 → 연두라벨 인수 → 공통 결함 개선 순서를 지켜라.
- G1–G4 전에 연두라벨 전용 Skill/지도/adapter/정답 패치를 준비하거나
  연두라벨의 가격·인쇄·프레임워크를 공통 설계에 하드코딩하지 마라.
- 현재 branch/HEAD/staged/unstaged/untracked, main, worktree 목록, Git 보호 정책과
  적용되는 환경 예외를 확인하라. 원본 경로나 main이 최신 구현을 포함한다고 가정하지 마라.
- 알려진 구현 기준 23e5d152038abf30765a019729c02bc05f640b5d의 포함 관계와 현재 변경을 확인하고,
  최신 구현이 포함된 검증된 커밋에서 정책에 맞는 새 branch와 새 worktree를 만들어라.
- 기존 checkout/branch/dirty/.work를 보존하고 기존 경로를 재사용·삭제·덮어쓰지 마라.
  미커밋 파일·DB·인증 정보·과거 .work를 새 worktree로 복사하지 마라.
- 실제 기능 구현 요청이다. 짧은 계획 뒤 구현을 시작하고 문서·스키마·시험 자료만으로 끝내지 마라.

2. 기존 소유 위치와 역할
- authoring/scripts/project_workflow.py: 작업 연결, 상태, 의무, 피드백·검토·유지보수
- authoring/scripts/verification_results.py: 선택, prepare/execute, 결과 유효성·재사용·조회
- authoring/scripts/workflow_context.py: 읽기 전용 진입 맥락
- scripts/run_check.py, scripts/verify_product.py: 기존 capture와 저장소용 adapter
- authoring/skills/agent-workflow, setup-project-verification, maintain-project-verification
- 기존 diagnose/UI 능력, authoring/references의 workflow-obligations, project-verification,
  result-viewer, repair-and-reuse와 tests/distribution의 관련 시험
- Agent는 의미·범위·원인·설계·시각적 충분성·검사 가치를 판단하고 수정한다.
  CLI는 결정된 작업·선택·실행·수집·누락·유효성·재사용·조회를 일관되게 처리한다.
  프로젝트는 업무 정답·runner·환경·자원·UI 기준을, 플러그인은 발견·조합·패키징을 소유한다.
- 새 범용 runner/workflow 엔진/dashboard/중복 장부/절차별 Skill 묶음을 만들지 마라.
  작은 작업에 Harness 계약이나 설치를 강제하지 마라.

3. G1 — 공통 작업 상태와 후속 연결 수리
- begin()의 일반 후속 작업에서 유효 검토가 모두 사라지고 무관한 map_review가 다시 생기는 문제와
  미해결 product_findings가 현재 후속 조회에서 빠지는 문제를 focused RED로 확인하고 수리하라.
- 기준이 유효한 검토는 재사용하되 새 요청의 적용·범위 판단을 과거 scope_reviews로 대체하지 마라.
  미해결 문제는 검토 STALE 여부와 별개로 명시적 해결/처리까지 이어가라.
- 일반 작업에 요청 요약·기대 결과 참조를 연결하라. Harness 계약이 있으면 참조해 중복하지 마라.
- 복수 작업은 명시적 식별로 연결하고 모호하면 후보와 필요한 식별 정보를 보여라.
  최신 시각·정렬 순서로 선택하거나 제공되지 않은 호스트 session ID를 가정하지 마라.
- 전체 저장소 변경에 묶인 결과 재사용을 검토하라. 검사 의존 범위가 확인된 경우만 좁히고,
  명령·기준·런타임·의존성·fixture·공통 입력의 변경은 계속 무효화하라.
- lookup/task resume는 읽기 전용, 완료된 execute resume는 불필요한 재실행 없이 유지하라.

4. G2 — 범용 프로젝트 최초 연결 완성
- 처음 보는 프로젝트의 기존 문서·코드·명령·테스트에서 사용자 기능과 소유 경계를 조사하고 연결하라.
  UI/routes 외 API/CLI/jobs/roles/flags 등 합의한 범위의 누락을 확인하라.
- 큰 지도는 기존 작업 상태로 분할·재개·통합한다. 미조사/미분류/미연결을 남기고,
  등록된 파일만 빠짐없다는 사실을 전체 기능 발견의 증명으로 삼지 마라.
- 기존 runner/도구로 Launch → Doctor → Drive → Evidence → Cleanup을 연결하고 실제 실행하라.
  프로젝트가 자원 수명주기를 소유하고 공통 CLI는 기존 capture/선택/실행/수집/조회를 재사용한다.
- 필요한 최소 adapter는 해당 프로젝트에 둬라. 명령과 assertion을 다음 작업에서도 재사용하라.
- 실행 가능한 instance/source/새 데이터와 실제 사용자 동작·저장·fresh read를 연결하라.
  HTTP 200, stdout 성공 문자열, 자체 PASS 파일만으로 성공 처리하지 마라.
- 지원 가능한 실행·관찰 수단과 미지원 범위를 명시하라. 무설정 모든 스택 지원을 가정하지 마라.

5. G3 — 여섯 업무 흐름을 실제 수정과 후속 소비까지 완성
- 기능 구현: 요구·영향 → 구현 → 필요한 실제 검사 → 의미 검토 → 결과·공백 조회.
- 검증/조회: business/architecture × FE/BE/API/Domain의 적용·미판단·미연결·제외·실패·차단·STALE 구분.
  검사 PASS와 의미 검토 미완료가 함께 보일 수 있어야 한다. FE 없는 프로젝트는 이유 있게 제외한다.
- 피드백: 기대 동작 → 재현 → caller/state/data 흐름 → 근본 원인과 소유 코드 수정 → 적절한 예방책.
  원래 실패 RED/GREEN과 가까운 정상 사례를 확인하고 다음 관련 작업에서 예방책/검사를 실제 소비한다.
  타입·경계 검증·상태 구조·제약·공유 구현·검사 중 원인에 맞게 선택하라.
- UI: 기존 기준을 찾거나 의도·상태·반응형·접근성 기준을 작성하고 공유 token/component를 수정한다.
  영향 화면과 다음 화면 작업의 재사용을 확인한다. token 값을 이중 관리하지 마라.
  연결 정보의 존재, 수치 검사, 실제 시각적 일관성 판단을 구분하라.
- 검증 유지보수: 낡은 명령·누락된 경로·잘못된 관찰을 소유 위치에서 수리하고 실제 재실행·후속 사용을 확인한다.
- 검사 정리: 기존/대체 검사의 동일 결함 검출·정상 허용을 확인한 경우 통합/삭제한다.
  비용·횟수·coverage만으로 삭제하지 말고 고유 검출력이나 근거 부족이면 유지하고 이유를 남겨라.

6. G4 — 제품 독립 수용 시험과 패키지 고정
- 기존 connected_product 등 독립 시험 프로젝트를 우선 재사용한다. 실제 웹 Full-stack과 FE 없는
  CLI/API, 비-Harness, UI 기준 유무를 확인할 최소 차이를 둬라. 새 대형 시험 체계를 만들지 마라.
- 실제 assertion 실패와 환경/관찰 차단, skip/0건을 구분하고 정리 후에도 run ID·명령·대상·raw와
  필요한 screenshot/trace/report가 남는지 확인하라. 근거 파일 충돌·덮어쓰기도 방지하라.
- G1–G3를 후속 작업까지 검증하라. 유효 결과, 완료된 실행, 읽기 전용 조회를 불필요하게 반복하지 마라.
- canonical 수정에 대응하는 저장소 안 mapped generated 리소스를 재생성하고 영향 Feature Map/docs를 갱신하라.
  관련 회귀 검사, resource drift, distribution, git diff --check를 수행하라.
- 새 worktree의 새 출력 경로에 로컬 패키지를 만들고 소스 commit·버전·패키지 해시·지원 범위를 고정하라.
- 가능한 기존 호스트에서 패키지 위치·자연어 업무·권한만 제공해 실제 발견·선택·사용을 확인하라.
  Skill 이름·CLI 순서·정답 패치를 알려준 시험은 무개입 성공으로 보고하지 마라.
  직접 CLI 시험과 Agent 시험, 패키지 사용과 native 설치·발견을 구분하라.
- 기존 설치 갱신이나 전역 변경 없이는 사용할 수 없는 호스트 범위는 미검증으로 남겨라.
  그 범위를 숨기거나 보호 호스트 미지원 때문에 일반 기능 개발 전체를 중단하지 마라.
- G1–G4의 일반 사용자 기능이 미완료이면 수리하고, 연두라벨 선행 맞춤 작업으로 보충하지 마라.

7. G5 — 고정 패키지로 연두라벨 실제 제품 인수
- 대상 후보는 C:\Users\YS\Desktop\python\labeler다. 현재 checkout/main/worktree와 합의한 제품 범위를
  다시 확인하고 시험할 커밋을 명시하라. 경로 이름이나 과거 파일럿 기준을 최신 제품으로 가정하지 마라.
- 새 작업 소유 공간에 안전한 tracked 소스와 새 시험 데이터를 사용하라.
  기존 DB·인증·미커밋 파일·과거 .work·맞춤 시험 연결을 가져오지 마라.
  원본 제품 checkout/Git refs/운영 환경을 변경하지 말고 소유하지 않은 프로세스를 종료하지 마라.
- 고정 패키지에 프로젝트 위치·요청·허용 범위와 기존 제품 자료를 제공하라.
  최초 연결 기능이 기존 자원을 조사하고 필요한 지도·가이드·최소 adapter를 생성·실행하게 하라.
  사람이 사전 작성하거나 중간에 명령 순서를 알려줘야 진행되면 해당 공백/개입을 기록하라.
- 최초 연결 → 실제 기능 변경/검증 → 읽기 전용 조회 → 피드백 수리 → UI·검증 기준 개선 → 재개/후속 작업을
  대표 업무와 그 영향 범위에서 수행하라. 제품 전체 고도화나 운영 배포 사업으로 확장하지 마라.
- 합성 API 화면 검사와 실제 API/Domain/저장/fresh read 근거, PDF와 물리 인쇄, 로컬과 외부 공급자를 구분하라.

8. G6 — 원인 소유 위치의 개선과 재검증
- 제품 결함은 프로젝트 코드·예방책, 연결 결함은 프로젝트 명령·가이드·adapter,
  공통 결함은 플러그인 canonical 코드·기존 절차에서 고쳐라.
- 장기 예방책을 코드·공유 구현·등록 검사·현재 가이드에 남기고 임시 기록에만 의존하지 마라.
- 공통 수정은 원래 실패와 다른 프로젝트 정상 사례에서 확인하고 새 패키지로 구분하라.
  변경 전 고정 패키지의 시험 결과를 변경 후 성공으로 덮어쓰지 마라.
- 다음 관련 요청에서 개선을 실제 소비하는지 확인하라. 실패가 남으면 남은 범위로 보고하라.
  기준/assertion/skip/권한 경계를 완화해 점수를 높이지 마라.

9. 권한·검증·전달
- 허용: 새 worktree의 source/tests/docs/저장소 generated 수정, 새 독립 시험 공간과 새 로컬 패키지,
  범위 안의 실제 로컬 실행·수리, 검증된 기능 단위별 로컬 커밋.
- 기존 설치 Skill/Plugin cache·전역 설정·인증·원본/운영 DB·원격 환경은 변경하지 마라.
  push/publish/deploy, 관리자 sandbox 구축·권한 완화·반복 설치·광범위한 native Agent 평가는 하지 마라.
  보호 브랜치 추가 병합은 이 프롬프트만으로 수행하지 말고 해당 세션의 명시적 권한을 따르라.
- non-trivial 변경은 가능한 focused RED 후 GREEN·정상 반례를 확인하라.
  영향 회귀·필수 저장소 확인이 통과하면 새 이유 없이 검사를 반복·확대하지 마라.
- source/tests/docs/generated를 기능 단위로 함께 커밋하고 새 branch/worktree를 검토 가능하게 남겨라.
- docs/research/agent-workflow-implementation-results.md의 현재 결과와 영향 문서/지도/프롬프트 상태를 갱신하라.
  과거 결과와 이번 실행 결과를 분리하고 문서 작성이나 테스트 수를 업무 성공으로 삼지 마라.
- 최종 보고: G1–G6 및 여섯 업무의 완료/미완료, 사용자가 할 수 있는 일, 실제 명령·근거 위치,
  실행/Agent 판단/사람 개입, 재작업·잘못된 완료·불필요한 실행, 지원/미지원 범위,
  기준·최종 HEAD/커밋/worktree, 기존 사용자 변경·설치 보존 여부, 남은 우선순위 최대 3개.
- 설치 가능한 패키지와 안정적 업무 위임을 별도로 평가하라. 직접 CLI/일반 Agent/설치된 native host/
  보호 수락/실제 제품 인수를 구분하고 제한된 성공을 모든 프로젝트나 장기 효과로 일반화하지 마라.
- pstack 비교가 필요하면 docs/research/pstack-analysis.md의 0.15.6 / 23e4138daa01c42d4969f7a5465f82704e64f798
  고정 소스를 사용하라. 실제 동일 과제 비교 없이 우열을 주장하지 마라.
```
