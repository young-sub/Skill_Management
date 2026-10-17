# Agent Coding 기반 구현 상태와 Labeler 검증 파일럿

> 아카이브: 수행 완료된 기반·파일럿 프롬프트입니다. 현재 구현 지시로 사용하지 않습니다. [현재 결론](../agent-coding-system-direction.md)과 [다음 세션 프롬프트](agent-coding-next-session-through-0.1.68.md)를 따릅니다. 변경 전 내용은 Git 이력에 보존됩니다.

2026-10-04에 기반 이식 프롬프트를 수행했다. 아래 완료 기록은 그 로컬 구현에 관한 것이다. 설계와 역사적 비교는 [수정 방향](agent-coding-system-direction.md), 현재 직접 명령은 [Testing](../../testing.md), 저장소 기능 지도는 [Feature Map](../../feature-map.md)에 있다. 완료된 기반을 다시 구현하지 않는다.

후속 목표인 **별도 복제한 Labeler의 제품 검증·Agent 위임과 근거 기반 최소 개선**을 2026-10-04~05에 수행했다. 실제 결과·재실행 방법·후보/Plugin 책임 판단·미검증 범위는 [파일럿 결과](../labeler-verification-pilot.md)에 통합했다. 아래 프롬프트는 수행한 범위와 완료 기준의 기록이며 완료된 기반/파일럿을 다시 생성하는 지시가 아니다. 일반 설치본·원본 제품 통합·공개 Plugin 배포는 완료 범위에 포함하지 않는다.

## 완료된 로컬 범위

- `git fetch origin main`으로 `e19134358141f901bb22c4af1aea17d7a9e2898c`를 재확인했다. 준비된 `wp-20261004-agent-coding-foundation`의 문서 base `1cc09ac6468573c1a020742f2f7540bdf92d4432` 위에서 기능 단위로 작업했다. 주 작업 폴더에서 진행했고 공통 .git 삭제나 다른 checkout의 reset을 수행하지 않았다.
- 최신 배포에서 `write-a-skill`만 제거했다. 공개 catalog·allowlist·inventory·manifest를 정렬하고 HWP와 기존 runtime을 보존했다. 일반 설치본 삭제는 수행하지 않았다.
- 후보 `b40396a`의 실행 캡처를 [독립 CLI](../../../scripts/run_check.py)로 선별 이식했다. 새 출력 부모 경로, 덮어쓰기 방지, native exit·timeout·Git 상태와 raw stdout/stderr를 기록한다. Feature/check와 고유 run ID를 추가했고 nonfinite timeout은 실행 전에 거절한다.
- [Repository adapter](../../../scripts/verify_product.py)는 Feature Map에서 프로젝트 명령 선택 → 캡처 → check 범위 판정을 연결한다. native 실패, 0건·skip·미실행, 다른 대상·run ID·argv/cwd, 실행 중 변경과 stale 결과를 PASS로 받아들이지 않는다. 원본 실행 record의 제품 판정은 null로 남는다.
- 후보 `9d2139f`의 Windows cmd/Git Bash 전송 fallback과 실패 진단만 이식했다. 기존 hash 거절·공유 version cache를 유지하고 loopback fixture와 임시 cache로 정상·실패 경로를 검사했다.
- 실제 cached Skills CLI로 임시 Codex/Claude 프로젝트에 16개 공개 Skill을 설치·갱신하고 resource 트리를 비교했다. 일반 설치·전역 설정·push/publish·protected main 통합은 수행하지 않았다.

## 채택·보류

| 후보 | 결정 | 이유 |
| --- | --- | --- |
| 실행 캡처 | 채택 | 직접 실행되는 repository 검증 adapter가 소비하며 native 정상/실패·timeout·기록 재사용 거절을 검증 가능 |
| Windows launcher | 필요한 부분 채택 | 전송 fallback 부재와 오류 은폐를 재현했고 native cmd/Git Bash fixture로 수정 효과 확인 |
| Agent eval supervisor와 file-change 계수 | 보류 | 이번 native 검증에 모델 평가 consumer가 없고 과거 CLI filesystem 격리 실패의 해결도 확인하지 않음 |
| 신규 5개 Skill, 다단계 router | 기반 구현에서는 일괄 도입 생략 | 당시에는 현재 Agent와 native 명령으로 완료 가능했음. 다섯 Skill의 개별 가치와 흡수 방식은 아래 파일럿에서 재평가하며 다단계 router를 기본 경로로 만들지 않음 |
| UI framework, MCP, 빈 plugin manifest | 보류 | 실제 제품 UI·외부 자원·설치 consumer가 아직 없음 |
| 테스트 대량 정리 | 보류 | 같은 의미의 결함 검출을 보존하며 삭제할 구체적 근거가 없음 |

## 검증과 한계

캡처·adapter 회귀 검사는 실제 Python/Git subprocess의 성공·결함·timeout·잘못된 대상·stale 대조를 사용한다. Windows launcher 검사는 컴파일한 fixture 엔진과 실패 curl, loopback HTTP를 사용하며 공개 release 다운로드 성공을 증명하지 않는다. 설치-script unit 검사의 mocked CLI와 실제 cached Skills CLI 설치 smoke는 별도 증거다. 임시 실행 자료는 `.work/agent-coding-foundation/` 및 기존 보존 정책 아래에 둔다.

샌드박스의 `taskkill /T`는 Access denied를 반환했다. 같은 소유 process/child와 무관한 process 대조는 허용된 native 도구 권한에서 검증했다. 제한 환경의 timeout 기록은 cleanup 실패·미완료를 그대로 남기고 BLOCKED로 판정한다. detached child까지 강제 정리하는 process sandbox는 제공하지 않는다.

`PASS`는 선택한 unittest assertions에 한정한다. 기록 정합성 검사는 editable evidence의 진위를 인증하지 않는다. untracked 내용·dependencies·fixture/runtime·server identity, Agent 품질·전체 skill 우월성, 외부 제품 UI/API/DB, 실제 plugin 설치/로딩/hook 동작은 미검증이다. 환경과 설치 root가 바뀌면 새 evidence가 필요하다.

## 후보 Skill에 대한 현재 판단

`b40396a`의 실제 본문을 다시 읽은 결과다. 아래는 채택 효과가 검증됐다는 결론이 아니라 파일럿에서 확인할 가설이다. 소스에 좋은 지침이 있는 것과 설치·로딩된 Agent가 지침대로 행동하는 것은 구분한다.

| 후보 | 재사용할 가치 | 비교할 대안·확인할 점 |
| --- | --- | --- |
| `setup-project-verification` | checkout/build/server/fixture 식별, 실제 사용자 행동과 저장 확인, native 실패 보존, 소유 자원 정리 | 공통 캡처 도구와 프로젝트 검증 guide에 먼저 흡수. 반복되는 환경 구성 판단이 독립 Skill을 정당화하는지 확인 |
| `ui-refine` | 기존 디자인 언어를 보존하는 좁은 UI 수정, 실제 화면·상호작용·read-back, 고정된 시각 비교 조건 | Impeccable·기존 FE 흐름과 겹치는 부분 통합. 작은 작업의 비용을 줄이면서 기준을 빠뜨리지 않는지 확인 |
| `improve-workflow` | 누락 규칙·미발견 규칙·충돌·실행 누락·잘못된 판정·설치 drift의 원인 분류 | 기존 유지보수 절차/Playbook으로 충분한지 비교. 실제 결함을 구조에서 고치고 반례에서 과잉 규칙을 만들지 않는지 확인 |
| `resume-work` | 상태 질문과 실행 요청 구분, dirty 상태·검증 유효성·미완료 작업 복구 | 기존 Git/Harness와 짧은 인계로 충분한지 비교. 불필요한 재계획·재검사와 중복 외부 실행을 줄이는지 확인 |
| `clear-writing` | UI 문구·기술 설명 편집 시 사실·조건·의미 보존 | 실제 문구 문제가 있을 때만 평가. UI 작업마다 별도 호출하거나 무관한 글쓰기 benchmark를 추가하지 않음 |

기존 skill 이름·폴더 수의 보존은 목표가 아니다. 각 능력을 도구, 프로젝트 기준, 기존 Skill, 짧은 Playbook, 독립 Skill 중 어디에 두는 것이 효과적인지 결정한다. `write-a-skill` 공개 배포 제거는 별도 기존 결정이며 이 재평가를 이유로 자동 복원하지 않는다.

## 다음 세션 실행 프롬프트

```text
관리 저장소: C:\Users\YS\Desktop\python\Skill_Management
제품 소스 저장소: C:\Users\YS\Desktop\python\labeler
시험 위치: 관리 저장소의 .work\labeler-verification-pilot-<이번 실행 식별자> 아래 독립 Git 저장소

목표는 Labeler의 테스트를 실행하는 데서 끝내는 것이 아니다. 별도 복제 환경에서 실제 사용자 흐름과 Agent 작업을 수행하고, 그 결과로 우리 Agent Coding 체계의 원인별 결함을 분석하고 필요한 최소 개선을 구현·검증해라. PStack과 10/3~4 후보의 유용한 능력을 재평가하여 Skill, custom agent, Playbook, 공통 도구, 프로젝트 기준, Plugin의 책임을 정해라. 근거 없는 대규모 개편은 설계 제안으로 구분한다.

반드시 해결할 문제:
- 많은 작업을 위임해도 결과를 신뢰하기 어렵다.
- 테스트를 수행해도 실제 결함을 잡지 못하는 형식적 검증이 있다.
- FE/UI마다 같은 지시를 반복하고 UI/UX 일관성이 깨진다.
- 프로젝트 변화가 검증 기준과 스타일가이드의 지속 개선으로 이어지지 않는다.
- 규칙·테스트·문서가 계속 쌓여 유지비가 커질 수 있다.

판단 기준은 사용자 behavior, business invariant, 실제 evidence와 반복 가능성, Confidence / Verification Cost다. 테스트 수·coverage·Skill 수를 목표로 삼지 마라. 이미 있는 규칙을 반복 작성하는 대신 왜 적용되지 않았는지 확인해라.

1. 현재 구현과 기준점을 확인해라.

- 관리 저장소의 AGENTS.md, docs/index.md, .harness/project.yaml, docs/feature-map.md, docs/testing.md와 docs/research/agent-coding-system-direction.md를 읽어라. PStack의 고정 원문과 평가는 docs/research/pstack-analysis.md를 사용하고 채택할 부분만 원문을 추가 확인해라.
- 마지막 확인 시 관리 저장소는 wp-20261004-agent-coding-foundation의 651f81e였다. 실행 캡처, repository unittest adapter, Feature Map과 Windows launcher 보완이 구현돼 있다. source HEAD·branch·dirty·remote 차이를 다시 확인하고 현재 기능을 원격 main이나 과거 후보로 덮어쓰지 마라. main이라는 로컬 branch의 존재를 가정하지 마라.
- Labeler는 마지막 확인 시 현재 checkout ab7aed6에 미추적 파일이 있고, 로컬 main은 1a10164ae7a3458e62b4accf8d52b20319f007e0였다. 원격 추적 main은 당시 로컬 main보다 뒤에 있었다. 제품 기준은 해당 저장소의 현재 로컬 main을 읽기 전용으로 재확인해 SHA를 고정한다. 변경됐다면 변경 내용과 새 기준을 기록한다. 현재 checkout이나 오래된 원격 추적 ref를 자동으로 기준 삼지 마라.
- 고정한 Labeler source의 AGENTS.md, docs/index.md, docs/label-signage-design.md, docs/product-architecture.md, docs/ui-ux-upgrade.md, package.json, test setup을 읽어라. 과거 카테고리 전용 설계를 현재 구현으로 오인하지 마라.
- capability exception을 확인하고 수동 비활성화된 도구를 재시도하지 마라. 현재 허용된 Playwright 등 실제 동작하는 대체 도구를 사용한다.

2. 원본과 분리된 재현 가능한 시험 환경을 만들어라.

- 원본 Labeler의 checkout·파일·Git refs·DB·일반 설치본은 변경하지 마라. 지정 source commit의 추적 소스를 archive/export한 뒤 새 경로에서 git init하여 독립 저장소를 만든다. 원본의 .git을 공유하는 worktree나 운영 저장소로 향하는 origin은 만들지 마라.
- repo·저장 데이터·process/port·설치 상태의 분리와 OS의 파일 접근 격리를 구분한다. 실제 보장 범위를 기록하고 사용자가 요구하지 않은 새 sandbox 조건 때문에 파일럿 전체를 차단하지 마라. 이미 적용되는 접근·보안 제한은 유지한다.
- 새 경로가 작업 소유 범위인지 확인하고, 이미 있는 폴더를 지우거나 덮어쓰지 마라. source SHA, 시험 repo baseline, 관리 도구 revision과 실행 환경을 남긴다.
- 원본 .dev.vars/.env/credentials, .wrangler의 DB/R2, node_modules, ignored 산출물과 미커밋 파일을 복사하지 마라. 비밀 파일은 경로로 제외하고 내용을 열거나 출력하지 마라. 새 의존성 환경은 lockfile을 기준으로 준비하고 mutable 저장소·cache를 원본과 공유하지 마라.
- 독립된 로컬 D1/R2, 작은 합성 데이터, 기존 테스트 fixture와 로컬 시험 세션을 사용한다. 실제 사용자 데이터나 인증 토큰을 가져오거나 새 인증 우회 코드를 제품에 추가하지 마라. 소셜 identity와 권한 모델은 그대로 둔다.
- 다른 앱과 충돌하지 않는 loopback 포트에서 실행하고, checkout/source/build·URL·실행 process·fixture를 연결해 확인한다. 200 응답만으로 올바른 앱이라고 판단하지 마라. 기존 사용자 서버를 종료하지 마라.
- 기존 npm pretest, test setup/teardown, migrations, build script의 실제 부작용부터 확인한다. 로컬 migration만 사용하며 실제 DeepL/결제/외부 상품 수집/원격 DB·배포는 이 파일럿에 포함하지 않는다.
- 앱·Worker·브라우저·로컬 저장소가 이어지는지 먼저 확인한다. 실패하면 제품 결함과 환경/도구 결함을 구분하고 원인에 따른 최소 수리만 한다. 환경이 준비되지 않았는데 mock 결과를 실제 앱 E2E로 보고하지 마라.

3. 사용자 기능과 검증·UI 기준을 최소 범위로 연결해라.

- 복제 제품에 사용자 관점 Feature Map을 두고 상품 저장, 디자인 저장·재열기, 통합 인쇄·재인쇄를 우선 연결한다. Feature ID·행동·기대 결과·business invariant·FE/BE/Domain·데이터 side effect·실제 검증 방법을 담는다. 기존 프로젝트 문서가 정답의 근거이며 현재 구현에서 기대 결과를 역으로 만들어 버그를 정당화하지 마라.
- 기존 테스트·selector·명령과 UI token/component를 재사용한다. 같은 사실의 여러 수동 원본이나 파일 목록 중심 지도를 만들지 마라. 필요한 신규 Feature와 검증만 보완한다.
- UI 기준은 기존 styles/token, DialogLayer·입력 등 공통 구현, 현재 디자인 문서·reference에서 추출한다. loading/empty/error, 키보드·focus·접근성, desktop/mobile, responsive와 시각 기준을 관련 화면에 연결한다. 새 UI framework나 전역 스타일을 먼저 만들지 마라.
- scripts/run_check.py는 공통 캡처에 재사용할 수 있다. 현재 scripts/verify_product.py는 이 관리 저장소의 unittest 전용이다. Labeler의 Vitest·브라우저·API 결과를 이 adapter에 억지로 맞추거나 가짜 unittest 성공 문자열을 출력하지 마라.
- 필요한 연결은 Labeler의 native runner 결과와 실제 관찰에 맞는 작은 adapter/명령으로 만든다. runner의 현재 지원 형식을 확인하고 선택된 case·실행/skip·오류·exit를 보존한다. 모든 runner용 parser나 새 테스트 framework는 만들지 마라.

4. 실제 앱에서 핵심 흐름을 검증해라.

A. 상품 등록·수정
- 브라우저 입력 → 저장 → 목록/상세 → 수정 → 새로고침/재조회까지 수행한다.
- 상품·가격·수량·단위 값이 FE, API, 로컬 DB에서 일치하는지 확인한다.
- 잘못된 입력과 불완전한 묶음 가격, 동시 수정 충돌, 다른 계정의 데이터 접근을 기존 검증과 연결한다. 거절 시 금지된 데이터 변화가 없어야 한다.

B. 디자인 저장·재열기
- 라이브러리에서 디자인을 열어 문구·스타일·크기를 바꾸고 저장한 뒤 다시 연다.
- 새 버전과 이전 버전의 보존, 필드/이미지/크기와 렌더링의 일치, 저장 실패 상태를 확인한다.
- desktop/mobile에서 관련 조작·focus·오류 표시·overflow를 확인한다. screenshot만으로 저장이나 조작 성공을 판단하지 마라. 의도된 시각 변경은 기준을 설명하고 기존 화면과 무조건 pixel 동일성을 요구하지 마라.

C. 통합 인쇄·재인쇄
- 상품과 인쇄물을 섞어 디자인·수량·순서를 정하고 A4 미리보기와 인쇄 경로를 실행한다.
- preview만으로 인쇄 기록이 생성되지 않는지, 확정 때 현재 내용·번역 revision·수량·치수 등을 다시 검사하는지 확인한다.
- 원문·디자인 변경 후에도 과거 인쇄 snapshot과 재인쇄 내용이 보존되는지 확인한다. 필요한 기존 legacy 호환 검사도 재사용한다.
- 실제 브라우저의 print 경로·print DOM·A4 PDF를 확인한다. window.print 호출 횟수만으로 인쇄 결과를 대신하지 마라. 물리 프린터의 출력 품질은 별도 미검증 범위다.

- Product는 요구와 결과, Domain은 계산/상태/규칙, BE는 API/권한/transaction/저장, FE는 사용자 행동/상태/시각, E2E는 그 연결로 나누어 본다. Architecture는 바뀐 책임·의존성·상태·외부 효과의 소유권을 확인한다. 모든 층마다 중복 suite나 별도 Agent를 만들 필요는 없다.
- tests/product.test.ts, tests/designs.test.ts, tests/commonPrinting.test.ts, tests/mixedPrintLayout.test.ts, tests/accountIsolation.test.ts, src/client/printReadiness.test.ts 등은 source 재확인 후 우선 재사용한다. 필요한 type/lint/build와 영향 검사를 선택하고, 기존 실패는 기준선으로 분리한다.

5. 검증 체계가 결함을 잡는지 대조해라.

- 먼저 정상/현재 baseline을 관찰한다. 원래 결함이 있다면 그 사실을 보존하고, 결함 주입과 섞지 마라. 판단 기준과 필요한 관찰을 대조 전에 고정한다.
- 시험 repo의 분리된 변경에서 작은 결함을 하나씩 넣는다. 예: 성공 표시 후 저장 누락, 가격·수량 계산 오류, 과거 snapshot이 최신 데이터를 따라 변함, 공통 UI 기준/상태 위반. 실제 코드와 관찰 경로가 있는 소수의 사례만 고른다.
- 같은 검증이 정상에서는 통과하고 결함에서는 해당 기대 결과의 위반을 검출하는지 확인한다. 단순 syntax error나 type error만 넣어 behavior 검출력을 입증했다고 하지 마라. 각 대조 후 오염을 해소하고 기준선이 복구됐는지 확인한다.
- 0건 실행, 필수 검사 전부 skip, 다른 checkout/build/server, stale evidence, 잘못된 run/Feature, DB/서버 준비 실패, native 실패가 후속 shell 성공으로 가려지는 경우를 PASS로 처리하지 않는지도 필요한 범위에서 확인한다. 기존에 검증된 helper 사례는 그대로 재사용하고 제품 연결의 새 위험만 추가한다.
- 기대 결과와 다른 실제 행동은 ISSUES, 필수 관찰 불가/잘못된 대상/미실행은 BLOCKED로 구분한다. 선택된 필수 기준을 충족한 범위만 PASS다. 선택적 not_required는 이유를 남기고 성공으로 세지 마라.
- 테스트가 실제 어떤 결함을 잡았는지, 놓쳤는지, 오탐인지와 비용을 남긴다. 검출을 피하려고 요구사항·assertion·skip·visual baseline을 바꾸지 마라.

6. Agent 위임과 개선 효과를 실제 작업에서 확인해라.

- 확인된 제품 결함이나 분리된 통제 결함 중 실제 의미가 있는 작은 수정 하나를 Agent에게 맡기고, 고정된 요구와 evidence로 검증한다. UI 변경에서는 기존 기준을 반복 설명하지 않아도 공통 구현·상태·저장 검증을 적용하는지 본다.
- 독립 검증이 유용한 작업은 구현과 검증의 context/역할을 분리한다. 검증자에게 요구·base/diff·실행 대상·원본 evidence를 주고, 구현자의 PASS나 주입 결함의 정답 위치만으로 판단하게 하지 마라. 검증 역할은 테스트와 결과 기록을 수행하고 제품·정답을 몰래 바꾸지 않는다. 주 Agent가 중요 판단을 확인한다.
- 별도 custom agent가 필요한지 판단할 때 입력, 출력, 허용된 쓰기, 적용할 위험 기준을 명시한다. FE/BE/Domain/Architecture는 검토 책임이며 고정 4인 조직이 아니다. 설정 파일을 만들었다는 사실만으로 독립 검증이 구현됐다고 하지 마라.
- 가능한 경우 현재 체계 A와 최소 개선 B를 같은 source/fixture/과업/환경/기준에서 비교한다. 실제 로딩된 skill·설정·도구 version/path가 다른지 확인한다. 일괄 도입 후 한 skill의 효과로 귀속하지 마라. 정상 대조와 가까운 반례로 과잉 적용도 확인한다.
- Agent 비교가 필요하면 새 session의 도구/쓰기/브라우저/정리까지 사전 점검한다. 과거 Windows CLI 0.160.0의 filesystem 격리 실패는 해결됐다고 가정하지 마라. 모델 과업 전 실패를 품질 실패나 동등성으로 세지 말고 원인 기반 수정·재점검 후 같은 장애를 반복하지 마라. 격리·권한을 느슨하게 해서 평가를 통과시키지 마라.
- 소수 파일럿의 관찰과 안정적인 품질/속도 우월성은 구분한다. 비교 환경이 막히면 native 제품 검증과 도구 개선을 계속하고 Agent 효과는 판단 불가로 남긴다.
- 작업 재개도 가치가 있으면 현재 시험 작업의 인계에서 확인한다. 사용자 dirty 변경 보존, 현재 상태 복구, 유효한 evidence 재사용, 불필요한 재계획/전체 재검사 방지가 기준이다. 허구의 외부 작업을 실제로 재실행하지 마라.

7. 테스트 결과를 체계의 근본 개선으로 연결해라.

- 각 중요 발견을 제품 결함 / 기대 기준 누락 / 실행·관찰 도구 결함 / 지침 미발견·충돌·과잉 / 설치·로딩 drift / 구조적 enforcement 부재 / 환경 한계로 분류한다. 하나의 현상을 여러 보고서에 중복 기록하지 마라.
- 발견마다 evidence, 영향을 받는 사용자 기능, 원인, 기존 체계가 막지 못한 이유, 가장 작은 수정 위치, 반례와 유지비를 연결한다. 지침은 이미 있는데 실행되지 않았다면 같은 문장을 더 추가하는 것으로 끝내지 마라.
- 반복 UI 문제는 token/shared component/상태 API, 경계 입력은 parsing/type/schema, 불가능한 상태는 적절한 domain model, 잘못된 의존성은 boundary/lint, 저장 문제는 transaction/constraint, 결과 오판은 실행 도구/판정 계약을 우선 검토한다. 작은 코드에 모든 구조를 강제하지 마라.
- Feature Map과 검증 guide의 갱신 책임을 기능 변경에 연결하고 실제 누락/오래된 명령을 찾아 수리한다. 제품 버그를 guide 변경으로 덮지 마라. 반복 UI 수정이 공유 기준과 구현에 반영돼 다음 작업에서 재사용되는지 확인한다.
- 유지보수는 변경·실제 회귀·확인된 drift에 반응하도록 설계한다. 매 작업 의무 회고, 규칙 자동 추가, 모든 Feature 정기 전수 실행부터 만들지 마라.
- 의미 없는 문구/구현 고정, brittle mock, 중복 검사의 정리 후보를 식별한다. 소비자 계약·cheap deterministic 검사·business invariant·데이터 보존·실제 regression 검사는 우선 보존한다. 삭제는 같은 의미 있는 결함 검출이 남는지 확인한 범위에서만 한다.

8. PStack과 10/3~4 후보를 선택적으로 재평가해라.

- PStack 조사 기준은 23e4138daa01c42d4969f7a5465f82704e64f798이다. 최신 구현이라고 가정하지 마라. create/maintain verification의 Launch/Doctor/Drive/Evidence/Cleanup, 사용자 Feature 기준, behavior 검증, domain 모델링, boundary discipline, 구조로 교훈 반영, 고정 평가 기준의 장점을 실제 파일럿에 대응시켜라.
- mode/router 계층, 모든 원칙의 Skill화, 고정 검토 인원/검사 개수, 매 변경의 전체 Feature fan-out, 상태 기록을 실행 증명으로 오인하는 방식을 복제하지 마라. orch의 verdict/evidence 문자열은 실제 실행과 독립 검증의 증명이 아니다.
- donor b40396a63b1031b8a3958d376fb3cc46499a9191의 다음 본문과 필요한 참조를 git show로 읽어라: setup-project-verification, ui-refine, improve-workflow, resume-work, clear-writing. 위치는 skills/<name>/SKILL.md다. 12a0ad1, bbc16df 및 과거 평가 기록은 필요한 변경 근거를 확인할 때 사용한다.
- 각 후보를 유지 / 축소해서 재도입 / 기존 Skill·문서에 흡수 / 실행 도구로 전환 / 보류·제외로 판단한다. 일괄 복원·일괄 폐기하지 마라. 이전 품질 평가가 완료되지 않았다는 한계를 유지한다.
- setup-project-verification은 runnable path 구축, ui-refine은 좁은 화면 수정, improve-workflow는 원인별 교정, resume-work는 상태·권한·evidence 복구, clear-writing은 의미 보존 문장 편집으로 평가한다. 이번 파일럿과 무관한 후보는 억지 benchmark를 만들지 말고 한계를 적는다.
- 현재 setup/design/execute/close/maintain/diagnose와 Impeccable, multi-agent-review의 역할 중복·빠진 책임·과도한 계약/라우팅·설치 결합도도 함께 검토한다. 글로벌 규칙, 실제 source, installed copy, session 로딩, 실제 행동을 구분한다.
- 중요한 공백마다 먼저 기존 소유자와 도구를 검토한다. 새 Skill은 반복되는 판단 능력이 독립적으로 필요할 때, custom agent는 분리된 검증 책임이 필요할 때, Playbook은 재사용할 작업 순서가 필요할 때 만든다. 결정적 제약은 가능한 한 코드·타입·lint·테스트·runtime에 둔다.

9. Plugin 전환을 구체적으로 판단해라.

- Plugin의 첫 실제 소비자는 이번 복제 Labeler다. 프로젝트는 Feature Map·업무 정답·UI 기준/코드·명령/fixture를 소유하고, 공통 도구는 실행·evidence, 선택적 Skill/Agent/Playbook은 판단과 절차, Plugin은 패키징·버전·설치/업데이트·선택적 host 연결을 소유하게 해라.
- 이식 가능한 capture와 프로젝트용 adapter를 분리하고 설치 경로와 실행 대상 root를 명확히 해라. plugin cache나 이 관리 저장소를 Labeler 대신 검사하는 오류를 막는다. 제품별 규칙을 공통 Plugin에 하드코딩하지 마라.
- 채택 권고에는 지금 묶을 기능, 계속 독립 CLI/Skill로 쓸 기능, 프로젝트에 남길 것, 새로 필요한 것, 제외할 것과 각각의 evidence를 명시한다. 단순 manifest 생성이나 skill 폴더 이동으로 목표가 달성됐다고 하지 마라.
- 실제 설치·호스트 연결의 이점이 확인되면 현재 공식 OpenAI 문서와 실제 host/CLI를 확인하고 최소 package를 준비해 임시 범위에서 검증한다. 직접 CLI, package 파일 집합·버전, 실제 설치, 새 session 로딩, 명령 실행, 중복 설치/업데이트·실패 처리를 각각 확인한다.
- authoring/resource-map 등 기존 source/generated 구조를 재사용한다. standalone skill이 다른 skill의 private 경로에 의존하지 않게 하고 동일 helper의 수작업 복사본을 늘리지 마라.
- hook의 trust 미부여·미지원·오류/timeout·중복 실행을 고려하고 직접 CLI/CI 경로를 유지한다. Stop hook으로 무한 반복을 만들거나 hook 자체를 제품 완료 보증으로 설명하지 마라. 외부 연결의 실제 필요 없이 MCP 서버·중앙 DB·대시보드를 만들지 마라.
- 임시 설치/로딩이 현재 환경에서 불가능하면 패키징 설계와 직접 CLI의 확인 범위를 분리하고 blocked 조건을 적는다. 설치 여부와 무관하게 제품·체계의 분석과 가능한 최소 개선은 끝내라.

10. 개선을 검증하고 지속 가능한 결과로 마무리해라.

- 재현 근거가 명확한 검증 도구·프로젝트 adapter·기준 소유권의 최소 개선은 복제 환경과 관리 저장소의 적절한 원인 위치에 구현·검증한다. 관리 저장소의 mapped source는 authoring에서 수정하고 생성·배포 검사를 따른다. 원본 Labeler 수정·병합은 하지 마라.
- broad architecture 전환, 미입증 신규 Skill/Agent/Plugin 일괄 도입은 구체적 설계와 채택 조건으로 남긴다. 기존 합의 범위의 작은 개선을 계획이나 제안만으로 끝내지 마라.
- 최종 결과에는 (a) source/시험/도구 revision과 재실행 방법, (b) Feature별 관찰과 raw evidence, (c) 정상·결함·오탐·blocked 대조, (d) 원인별 체계 결함과 구조적 교정, (e) 5개 후보 및 신규 Skill/Agent/Playbook/Plugin 채택표, (f) 실제 구현·검증한 변경과 남은 결정을 포함한다.
- 관찰 지표는 놓친 결함, 거짓 완료, 오탐, 사람의 반복 지시/재검수, 실행·유지 비용이다. 측정하지 않은 효과는 미측정으로 둔다. Agent 자기 점수나 테스트 개수로 품질 개선을 주장하지 마라.
- 상세 raw output·screenshot/PDF·fixture·실행 기록은 작업 소유 .work에 둔다. lasting 분석과 채택 근거는 관리 저장소의 기존 방향 문서 또는 하나의 파일럿 결과 문서에 통합하고 docs/index.md에서 연결한다. 동일 사실의 일지·회고·검증 guide를 여러 개 만들지 마라.
- verified functional unit 단위로 커밋한다. 제품 시험 변경과 관리 체계 개선의 commit/evidence를 구분하고, 완료 후 이 프롬프트의 상태도 갱신한다. 사용자 서버·dirty 파일·원본을 보존하고 소유 process·임시 데이터만 정리한다. 복제 repo와 재현 근거는 소비자가 끝나기 전에 삭제하지 마라.
- push/publish, 원본/보호 branch 통합, 일반 설치본·전역 설정 변경, 원격 자원·유료 provider 실행은 이 파일럿에 포함하지 않는다. 기존 명시 권한은 해당 범위에서 유지하고, 새 승인이 필요한 경우에는 준비 가능한 package·diff·임시 검증을 먼저 끝낸다.

완료는 테스트 실행 목록이 아니라, 실제 제품에서 확인된 근거로 어떤 체계를 유지·고치고 어떤 구성요소를 추가·흡수·삭제할지 결정하고 필요한 최소 개선의 효과까지 확인한 상태다. 미검증·blocked 부분은 정확히 남겨라.
```
