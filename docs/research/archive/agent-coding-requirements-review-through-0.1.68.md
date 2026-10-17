> Historical record through 0.1.68; not current execution instructions. See [current design](../agent-coding-system-direction.md) and [current work](../plugin-continuous-improvement-next-session.md). Original bytes: Git ea7e11d.

# Agent Coding 요구사항 충족 검토와 구현 준비

후속 상태: 사용자의 별도 실행 승인으로 `c7c064a`에서 구현을 시작했다. 아래 표는 수정 전 설계 검토 기록으로 보존하며, 현재 R01–R16의 실제 구현·업무 수용·미검증 상태는 [구현 결과](../agent-workflow-implementation-results.md)가 소유한다.

추가 합의: 전체 기능의 최초 Feature Map, 분할·재개·통합, 모든 고도화의 필수 갱신, Agent 판단/환경 강제의 구분과 제약의 실익은 [완성 기준과 후속 구현](agent-workflow-completion-design-through-0.1.68.md)에 반영했다. 특히 R04/R12의 범위가 확대되었으므로 아래 역사적 검토나 T1의 첫 흐름 연결로 새 요구 충족을 주장하지 않는다.

검토일: 2026-10-05. 검토 기준은 사용자가 제시한 **R01–R16의 세부 요구**다. 수정 전 기준은 `wp-20261004-agent-coding-foundation`의 `53865b02d9563c8135b1ad51428c13be227c49fe`, dirty 없음이다. 다음 세션 구현 프롬프트를 실행하지 않았다. 소스·설정·설치·기존 fixture를 변경하거나 앱/모델 평가를 새로 실행하지 않고 문서, 기존 소스/테스트, Git 이력, 보존 raw를 읽었다. 이 문서는 사용자가 요청한 검토·준비 기록이며 일상 작업마다 같은 보고서를 만들라는 지침이 아니다.

## A. 결론

**수정 전 문서는 주요 요구를 폭넓게 담았지만 그대로 구현을 시작하기에는 실행 연결이 불충분했다.** 세 Skill 추가를 고정하면서 실제 발견·조합을 확인하는 조건은 약했고, Feature lifecycle 수용은 조건부였다. 결과 조회의 기준/실행 연결과 실패 후 재검증, 활성 설계의 구체적인 domain/boundary 원칙도 보완이 필요했다. 이는 체계 전체를 다시 만들 이유가 아니다.

이미 충분한 내용도 분명하다. 조회/수정 구분, 작은 작업의 직접 완료, 선택적 Full/계약/위임, 피드백 원인 분류와 구조적 예방, UI 기준과 코드 소유권, 검출력 보존 후 테스트 정리, 실제 Agent 평가가 막히면 전체 완료 금지는 기존 문서에 있다. 이들을 누락이라고 판정하거나 검사 삭제·고정 인원·새 관리 체계를 추가하지 않았다.

이번 문서 보완으로 [현재 설계 §11](agent-coding-system-direction-through-0.1.68.md#11-요구사항-검토로-구체화한-실행-연결)과 [다음 프롬프트](agent-coding-next-session-through-0.1.68.md)에 책임/계기/입력/행동/산출물/소비자/실패 처리 및 아래 T1–T6을 연결했다. **문서상 구현 준비는 완료했으나 구현·효과는 미입증**이다. 다음 실행 요청에서 이 기준을 사용하고, 실제 host/권한/자료를 확인한 뒤 허용된 구현을 진행한다. 이번 검토가 설치·운영 적용의 승인이나 성공을 뜻하지 않는다.

## B. 요구사항 추적표

아래 판정은 문서 보완 **이전** `53865b0` 기준이다. 줄 번호는 `git show 53865b0:<파일>`로 재현한다. 보완 뒤 상태를 원래 설계의 충족으로 소급하지 않는다.

- **D** = [docs/research/agent-coding-system-direction.md](agent-coding-system-direction-through-0.1.68.md)
- **N** = [docs/research/agent-coding-next-session.md](agent-coding-next-session-through-0.1.68.md)
- **L** = [docs/research/labeler-verification-pilot.md](../labeler-verification-pilot.md)
- **P** = [docs/research/pstack-analysis.md](../pstack-analysis.md)
- **A** = [docs/research/archive/agent-coding-system-direction.md](agent-coding-system-direction.md)
- **M** = [docs/feature-map.md](../../feature-map.md), **V** = [docs/testing.md](../../testing.md)

`충족`은 설계 반영의 판정이며 설치/실행/효과 입증과 다르다. 각 효과 칸은 기존 근거, 구현 예정, 근거 부족의 적용 범위를 구분한다. T1–T6은 이번에 구체화한 수용 과업이고 아직 실행하지 않았다.

| 요구 ID | 설계 판정 | 설계 근거(파일:줄) | 구현 프롬프트·수용 검증 연결 | 충족한 세부 / 누락·충돌·불명확 | 구현/효과 근거 상태 |
| --- | --- | --- | --- | --- | --- |
| R01 | 부분 충족 | D:21–45, A:79–94, L:22–36 | N:18–31 → T1/T4/T6 | 기존 Harness/diagnose/UI/배포·도구와 부족한 제품 의미 책임, 구현/파일럿/계획을 구분함. 다만 N:25/37의 세 공통·두 local Skill 생성 지시는 기존 연결로 충분한 경우의 재사용 판단을 제한함 | 기존 source/CLI·배포 구조 **현재 근거 있음**. 새 책임 조합 **구현 예정**, 전체 Agent 효율 **근거 부족** |
| R02 | 부분 충족 | D:9–19,143–164; P:29–55,75–98,119–132,175–202; L:102–112 | N:30–31/85 → T1/T3/T4 | Mode/Playbook/Skill·원칙, create/maintain·behavior·구조적 교훈, 5개 후보의 축소/흡수/제외와 donor 보존은 있음. Automation과 Project Configuration의 역할·입출력 및 이번 제외 이유가 활성 설계에서 덜 구체적. domain/boundary 세부가 아카이브에만 남음 | pinned 소스 분석·후보 역사 **현재 근거 있음**. 새 적용 **구현 예정**, 후보 전체 우월성·자동화 성과 **근거 부족** |
| R03 | 부분 충족 | D:35–61 | N:25–28/54/68–70/84 → T1/T4 | 요청→절차→능력→검증→취합, 선택 로딩/중복 방지/조회 구분은 있음. 실제 host 발견 경로와 호출 순서를 안내하지 않은 선택 증거, 두 유지보수 책임이 **모두 필요한** 정상 조합이 고정되지 않음 | 조정 책임 **구현 예정**. native CLI 실행은 근거가 있으나 단일 요청 자동 조합 효과 **근거 부족** |
| R04 | 부분 충족 | D:78–80,119–126; M:3–16; A:119–147 | N:35/68–69 → T1/T4 | 사용자 Feature 필드 전체와 요구/invariant, 최초·변경·검증·maintain 계기는 있음. 갱신 시점이 완전히 없는 것은 아님. 그러나 추가/변경/삭제의 diff·commit·활성 selector와 역사 결과 처리, 초기 미연결 범위가 불명확하고 수용이 “새 기능이 있다면”임 | 관리 4개 Feature·Labeler 3개 flow 지도 **현재 근거 있음**. 전체 기능 완전성/변경 lifecycle의 Agent 수행 **근거 부족**, 신규 유지보수 **구현 예정** |
| R05 | 부분 충족 | D:63–74; L:28–35,46–54 | N:36/57/63 → T2/T3/T5 | 제품 기대·계산/권한/상태/데이터와 책임/상태/효과/경계, FE/BE/Domain/E2E를 구분. 층별 PASS만으로 완료하지 않음. 어떤 변경이 연결 관찰을 필수로 만드는지, invariant→소유 경계→실제 검사 결과의 소비를 더 고정해야 함 | 가격 전달·금액 persistence 결함 검출 **현재 근거 있음**. 전 범위 구조/업무 검증 효과 **근거 부족**. 변경별 선택 연결 **구현 예정** |
| R06 | 부분 충족 | D:76–96; V:23–40; scripts/verify_product.py:61–96 | N:38–41/59 → T2 | 선택/제외·실행 상태·판정·명령/source/runtime/run/raw/diff와 stale 금지는 있음. 여러 층 결과의 실제 소비 방식, 기준 revision·조건 식별·원래 판정/현재 재사용 상태의 관계가 미정. 현재 CLI는 단일 unittest 재판정이며 업무 이력 조회가 아님. 최종 DB producer 연결도 부족 | capture·일부 binding **현재 근거 있음**. 통합 조회 **구현 예정**. DB provenance와 새 조회 행동 **근거 부족** |
| R07 | 충족 | D:7,86–96,113,134–139; L:56–71 | N:40/53–59/78–79 → T2/T3/T6 | behavior와 실제 관찰, exit/HTTP/screenshot/schema 단독 성공 금지, 정상·결함·오탐, 0/skip/wrong/stale/환경 실패, 가치 있는 unit/mock/schema 유지가 연결됨. 모든 기존 assertion의 효과를 입증했다는 뜻은 아님 | native/browser 정상·결함·실행 실패 대조 **현재 근거 있음**. 반복 안정성·전체 coverage 효과 **근거 부족**. 새 소비자 오판 방지는 **구현 예정** |
| R08 | 부분 충족 | D:46,59,89–96; L:73–79 | N:64–65 → T3 | 고정 인원 없이 필요 시 구현/검증 분리, 요구·diff·대상·raw 확인, main 책임과 agent 파일≠검증은 있음. ISSUES 반환→수정→새 diff의 근거 무효화/재검증, BLOCKED의 재개 조건이 운영 순서로 충분히 연결되지 않음 | 과거 역할 분리 제품 관찰 **현재 근거 있음**. model/tool trace 및 신원 인증 **근거 부족**. 새 책임 조합 **구현 예정** |
| R09 | 충족 | D:98–115,119–130 | N:61–75 → T3/T4/T5 | 피드백→기대→재현→원인→기존 소유자→구조/검사→재검증→기준 갱신, 제품/기준/도구/지침/설치/환경 분류, 자동 회고·규칙 축적·무한 loop 배제가 있음. 다음 과업이 변경된 자산을 소비한 증거는 아직 없음 | 기존 diagnose와 pilot 도구/관찰 수리 **현재 근거 있음**. 새 체계의 지속 재사용은 **구현 예정/근거 부족** |
| R10 | 충족 | D:100–115; authoring/skills/diagnose/SKILL.md:10–16 | N:53/61–65 → T3 | 상태/데이터/caller 추적, 공유 원인·소유 위치, 적합한 runtime/type/component/검사 예방, RED/GREEN·가까운 정상 반례, assertion/skip/baseline 완화 금지가 있음. 모든 결함에 새 guardrail을 강제하지 않음 | 가격 +1 제거와 원래 flow RED/GREEN **현재 근거 있음**. 합성 결함이며 원본 제품 개선이나 일반 효과는 **근거 부족** |
| R11 | 충족 | D:45,125–130; A:149–168 | N:37/72–75 → T1/T5 | design principles, color/typography/spacing/radius/elevation, layout/component, loading/empty/error, responsive/a11y, Do/Don't/reference/visual을 관리. guide 의도와 코드 값/동작을 분리하고 실제 화면/interaction·반복 공통 수리·후속 재사용을 요구. 특정 Button/Input/Table/Modal 소유 경로는 대상 조사에서 확정해야 함 | 기존 token/component·한정 화면 관찰 **현재 근거 있음**. 완전한 UI 상태 검증·지속 개선 효과 **근거 부족**, 후속 재사용 **구현 예정** |
| R12 | 부분 충족 | D:78–80,117–130; A:215–229 | N:28/35/67–70 → T1/T4 | 변경자/검증자/maintain 역할, 제품 의미와 Harness 무결성 구분, 버그 은폐 금지, 요청/회귀 기반 범위는 있음. map→영향→실행→누락/실패→수정의 입력·산출물과 추가/삭제/죽은 명령/계층 공백의 실제 과업 연결이 약함 | 프로젝트 guide/native/browser 경로 **현재 근거 있음**. 일반 유지보수·lifecycle 조합 **구현 예정**, 지속 효과 **근거 부족** |
| R13 | 충족 | D:132–141; L:114–120 | N:77–79 → T6 | 구현 고정/중복/brittle/저가치 후보를 구분하고 핵심 regression/invariant/경계/데이터/flow/cheap deterministic을 유지. 구조적 대체도 같은 실패와 정상 반례의 근거가 필요. 개수 감소와 무조건 삭제를 목표로 하지 않음 | 후보 조사와 보존 판단 **현재 근거 있음**. 삭제 후 효과는 실행하지 않아 **근거 부족**. 이는 강제 삭제를 추가할 이유가 아님 |
| R14 | 부분 충족 | D:39–46,69–74,151–164; A:250–267 | N:29/36–39/85 → T2/T3/T4 | Skill/도구/프로젝트/Plugin 책임, CLI/CI, canonical/generated 유지가 있음. 외부 입력→typed domain→pure logic→adapter 원칙과 복잡성별 모델 선택이 활성 문서에서 축약됨. 책임별 입력/출력/소비자도 구체화 필요 | 기존 shared schema/domain·Harness 배포 **현재 근거 있음**. 새 architecture 선택·연결 **구현 예정**, 일반적 개선 효과 **근거 부족** |
| R15 | 부분 충족 | D:166–176; N:23–41,51–101 | T1–T6 및 최종 완료표 | 실제 구현·정상/결함/반례·사용자 가능 업무와 source/설치/제품/Agent/운영 분리는 이미 필수. native만으로 전체 완료는 N:101이 금지함. 다만 파일 수 고정, 초기 setup/양쪽 조합/Feature 갱신의 조건부 수용, 임시 설치본을 쓰는 실제 Agent 경로가 남음 | 기반 source/native **현재 근거 있음**. 신규 체계 **구현 예정**, 통합 업무·속도/효율 효과 **근거 부족** |
| R16 | 충족 | D:9–33,145–164,178–184; archive/index.md:3–10; L:7–20,54,79,148 | N:19–20/43–49/86/90–96 → 모든 T의 범위 제한 | 결정 변화·아카이브·미구현 계획, 독립 Git/고정 source/합성 데이터, 원본·일반 설치·기존 자원 보존을 명시. 소스/관찰/추론/미검증도 구분. 이번 발견한 raw 추적 한계는 과거 결과에 주석으로 보완해야 함 | Git 이력·기존 raw **현재 근거 있음**. 원본 제품·운영·일반 설치·장기 재현 보장 **근거 부족**. 역사 기록을 새 성공으로 쓰지 않음 |

판정은 **부분 충족 10개, 충족 6개**다. 충족 6개도 통합 구현 효과를 입증한 것은 아니다. 요구 전체가 빠졌다고 보기보다 수용 연결과 일부 소유 책임이 약해진 상태다.

## 기존 능력과 후보 재사용의 판단 근거

현재 공개 배포는 Harness 7개와 독립 Skill 9개다. `authoring/resource-map.json:4–21`은 공통 runtime/정책/schema의 source→generated 소유권, `.harness/project.yaml`은 경로/명령/영향/보존/Git 정책, `.github/workflows/validate-distribution.yml`은 docs-only와 나머지 검사 경로를 소유한다. `maintain-agent-harness`의 runtime 점검은 mapping/cohort/retention이며 제품 요구의 정답을 검증하지 않는다. `diagnose`는 재현·원인·기존 소유자 수리에 충분하다. Impeccable의 `document/extract/doctor`와 접근성·React 능력은 UI 절차를 새로 복제할 이유를 줄인다.

관리 Feature Map의 네 행은 실제 사용자 기능을 설명하지만 모든 Harness·Agent 업무를 완전히 매핑하지 않는다. FE/BE 해당 없음은 이 저장소에 제품 UI/API가 없기 때문에 타당하다. 이를 Labeler full-stack 지도로 대체 사용하면 안 된다. Labeler의 세 Feature와 guide/adapter는 독립 pilot repo에 있으며 관리 저장소의 unittest adapter와 다른 소비자다.

| 10/3–10/4 후보 | 판단 | 근거와 새 책임의 최소 위치 |
| --- | --- | --- |
| setup-project-verification | 축소 도입 또는 기존 안내에 흡수 | 환경/source/server/fixture·첫 flow 연결은 pilot에서 실제 필요했음. 기존 Harness setup은 제어 설정이지 제품 의미 setup이 아님. T1에서 반복 판단이 필요한 부분만 공통 Skill, map/argv/oracle는 프로젝트에 둠 |
| ui-refine | 기존 UI 능력·UI 절차에 흡수 | Impeccable의 문서/추출/doctor와 프로젝트 token/component가 이미 있음. 긴급한 누락은 다른 이름의 UI Skill보다 source/runtime·interaction/readback 및 다음 요청의 재사용 경로임 |
| improve-workflow | diagnose·product maintain·피드백 절차에 흡수 | pilot의 오탐은 driver, report 공백은 capture, FE 결함 누락은 flow 연결에서 수정. 원인 소유 위치가 다른데 한 새 Skill이 전부 소유할 이유 없음 |
| resume-work | 기존 Harness/Git 재개에 흡수 | 현재 상태·dirty·권한·유효 evidence를 복구하는 기존 책임이 있음. 전체 재계획이나 전수 재검사보다 기존 단계와 조회를 구분함. 일반 resume A/B는 미입증 |
| clear-writing | 핵심 위임 범위에서 제외 | 이 pilot에 실제 문장 편집 과업이 없었고 UI마다 의무 호출할 근거 없음. 관련 편집 요청에서만 재평가 |

현재 HEAD에는 위 다섯 Skill 디렉터리가 없고 donor `b40396a63b1031b8a3958d376fb3cc46499a9191`에는 있다(`git ls-tree` 확인). 과거 구현과 현재 적용을 구분했다. 후보가 최신 배포 계열을 포함하지 않는다는 A:46–69의 역사 때문에 전체 donor 병합은 부적절하다. 과거 설치 확인·소수 실행과 모델 startup 이전에 중단된 평가를 후보 전체 우월성으로 취급하지 않는다.

PStack의 Mode/Router는 요청 분류, Playbook은 필요한 순서, Skill은 재사용 능력, Principle은 판단 기준, Automation은 외부 이벤트/주기의 시작 계기, Project Configuration은 대상·명령·도구·예산/권한 조건을 연결한다. 채택할 것은 이 책임 조합이다. 현재는 사용자 요청/변경/실패가 시작 계기이므로 Benny·Slack·cron·webhook는 제외한다. 프로젝트 설정은 기존 config와 guide로 충분하며 별도 중앙 설정을 만들지 않는다. `orch` 행이나 Principle 파일은 실행/독립 검증의 증거가 아니다. 고정 upstream 조사이며 최신 host 지원을 새로 확인한 결과도 아니다.

## 기존 raw evidence의 실제 범위

다음 경로는 모두 `.work/labeler-verification-pilot-5a80b570/` 아래다. 현재 읽을 수 있었던 기록의 검토이며 재실행 PASS가 아니다.

| 자료 | 이번에 직접 확인한 것 | 확인 못 한 것/판정 한계 |
| --- | --- | --- |
| `repo` | HEAD `ecd7db768aef3c17c0ffc9834759944cf013b0f0`, Git status clean | 원본 Labeler 최신 HEAD나 운영 환경과의 동등성 |
| `committed-browser.json`, `browser-committed/observed.json` | run `4d5f6b6d-351f-4c1b-a2d4-43b993e80b37`, native exit 0, 고정 clone HEAD, 28개 check와 UI/API 관찰 | 캡처의 `behavior_verdict`는 null. 모든 서버/backend/fixture 상태의 인증은 아님 |
| `committed-product/design/print.json`와 각 `.vitest.json` | 29/5/7 성공, native exit 0, capture report SHA-256과 raw 파일 일치 | 선택 Vitest assertions 범위. 독립 검증자나 제품 전체 PASS가 아님 |
| `browser-price-mutant/observed.json`, `domain-price-mutant.json` | UI `3201 != 3200` ISSUES, Domain 29 중 5 실패·native exit 1, 실제 raw report 해시 일치 | 의도한 결함에 대한 검출 신호. 원본 제품 버그 발견/장기 품질 측정이 아님 |
| `skip-native.json`, `zero-native.json`, wrong-target/unavailable capture | exit 0이지만 성공 0/pending 1, 0건, 다른 서버 doctor 실패/ECONNREFUSED의 exit 2 | 요약 verdict 카드만으로 판단하지 않음. 모든 실행 환경의 동일 동작은 미검증 |
| `committed-db-readback.json`, `db_readback.py:4,21` | committed browser와 상품/job ID·값 일치. 그러나 남은 script는 baseline-07을 읽어 다른 `db-readback.json`을 씀 | **최종 DB 결과의 생성 명령/run/source 연결을 찾지 못함.** 내용 일치를 같은 committed 실행의 완전한 DB provenance로 확대할 수 없음 |
| `agent-red/green`, `independent-browser`, native text/diff, `agent-implementation.json`, `independent-verdict.json` | 실제 RED/12개 GREEN/독립 관찰 12개 및 diff/출력이 남음 | 마지막 두 JSON은 요약 카드. 이번에 확인한 자료에는 새 Skill 자동 발견/선택을 입증할 raw model/tool transcript가 없음. 절차상 역할 분리와 기술적 격리를 구분 |
| plugin probe package·host/CLI 기록 | 과거 임시 설치/discovery/cache 실행·버전 시험 자료가 남음 | 이번 host 재시험을 하지 않았고 일반 설치/모델 선택/지침 이행/hook 효과로 확대하지 않음 |

DB 연결 공백은 새 앱/fixture 평가로 메우지 않았다. 기존 raw도 고치지 않았다. [파일럿 문서의 재확인 절](../labeler-verification-pilot.md#2026-10-05-요구사항-검토의-근거-재확인)에 제한을 붙였다. 원본 readback/API의 가치 전체를 부정하는 것이 아니라 producer 추적이 불완전한 지점을 한정한 판단이다. `.work` 자료의 만료 가능성과 manifest 기반 보존 등록 여부는 별개이며 임시 폴더가 영구 아카이브인 것처럼 쓰지 않는다.

## C. 중요한 간극과 가장 작은 보완

| 간극 | 사용자 업무에 미치는 영향 / 현재 문서가 불충분한 이유 | 가장 작은 보완 위치·방법 | 실제 과업과 정상/결함/반례 |
| --- | --- | --- | --- |
| G1. 발견·조합과 파일 수 | 이름/순서를 사용자가 다시 알려줘야 하거나 불필요한 3+2 파일을 만들 수 있음. N:68의 해당 없음으로 양쪽 조합 검증을 피할 수 있음 | D §3/11, N §2/C/6. 설치 description+프로젝트 index 연결, 공유 조사 한 번, 두 책임 동시 과업. 기존 안내가 충분하면 재사용 | T1/T4: 이름 없는 요청 정상 조합, 제품/Harness 각각 drift 검출, audit-only·비-Harness에서는 수리/설치 없음 |
| G2. Feature·guide lifecycle | 처음 만든 지도만 남고 추가/삭제·명령 변경에 낡아질 수 있음. N:69의 조건부 과업은 갱신을 입증하지 않음 | D §11 변경별 표, N §3/C. 변경 전 기준, 같은 기능 diff/commit 갱신, 완료 검증, 삭제 selector와 과거 결과 분리 | T4: 새 연결 누락·삭제 잔존·죽은 명령 탐지/수리, 실제 명령 확인, 역사 결과 보존·정상 지도 무수정 |
| G3. 비즈니스와 아키텍처의 관찰 | 계산 테스트와 화면 테스트가 따로 통과해도 전달/상태 소유 결함을 놓칠 수 있음. 아카이브의 구체적 boundary 원칙이 축약됨 | D §11에 기존 원칙만 복구. invariant→caller/소유 경계→검사/관찰 연결, 변경별 E2E 선택 | T2/T3: 정상 가격 저장, BE는 통과하는 FE +1, 잘못된 입력 거절·금지된 저장 없음. 무관한 UI 순수 표현에 저장 검사를 강제하지 않음 |
| G4. 결과 조회의 실제 소비 | Agent 요약만 보이거나 옛 기준/다른 DB 결과를 현재 성공으로 오인할 수 있음. 기존 CLI는 단일 unittest 재판정이고 최종 DB producer 연결도 부족 | D §11, V, N §3/A. 계획→run→raw assertion/관찰 참조, 기준/조건 식별, 역사 판정과 현재 재사용 분리. 새 범용 parser는 불필요 | T2: 현재 정상 결과·구현 diff 연결; raw 누락/기준 변경/다른 대상은 현재 PASS 금지; 조회는 실행·원본 수정 0 |
| G5. 독립 검토 후의 대응 | verifier ISSUES 이후 수정한 diff에 옛 PASS를 붙이거나 환경 막힘을 무한 재시도할 수 있음. 책임 분리는 있으나 후속 운영이 짧음 | D §11, N B. finding→소유자 수정→영향 근거 무효화/재검증, BLOCKED의 fallback·재개 조건·독립 작업 유지 | T3: 실제 다른 context가 요구/diff/raw를 읽음; 수정 후 관련 실행 갱신; assertion/권한 완화 금지·동일 원인 반복 중단 |
| G6. 최초 연결·후속 재사용의 행동 근거 | 파일과 guide를 만들었어도 실제 새 요청이 읽고 쓰는지 모를 수 있음. 기존 prompt는 이미 전체 완료 금지가 있으므로 그 규칙을 중복 추가할 필요는 없음 | N §5/6와 T1/T5. 임시 설치를 실제 쓰는 host/context 식별, 최초 연결과 후속 요청의 도구 trace. UI source 경로/의도된 예외 유지 | T1 첫 flow 성공/환경 BLOCKED; T5 공유 불일치 수리→두 번째 요청에서 재사용, 정상 예외 허용 |

다중 검토에서 나온 지적도 그대로 채택하지 않았다. 합성 결함 사용은 기존 N:63/L:79가 한계를 명시하므로 실제 제품 버그로 일반화하지 않는 한 유효하다. 검출력 근거가 없을 때 테스트를 보존하는 N:78은 R13에 맞다. N:101은 이미 Agent BLOCKED 시 전체 완료를 금지하므로 “native 검사만으로 완료를 허용한다”는 비판은 부정확하다.

## 수용 과업: 요구 → 설계 → 구현 → 관찰 → 맡길 수 있는 업무

다음 과업은 **첫 구현에서 수행할 수용 기준**이다. 기존 N의 A–E를 구체화한 것으로 별도 전체 benchmark를 추가하지 않는다. 한 과업이 여러 요구를 입증할 수 있으며 유효한 run/raw는 공유한다. 각 기준/필수 관찰/정상 반례는 구현 평가 전에 고정한다. 제품 없는 fixture 통과와 실제 Labeler 흐름은 구분한다.

| 과업 | 한 번의 사용자 요청과 입력 | 수행자·산출물·실제 관찰 | 결함/정상 반례와 완료 경계 | 가능해지는 업무 / 요구 |
| --- | --- | --- | --- | --- |
| T1 최초 연결·발견 | “이 프로젝트에서 상품 저장을 확인할 검증 경로를 마련해줘.” 새 독립 Labeler 작업 root, 기존 제품 기준/명령/UI, 임시 설치본. 기존 pilot 자료는 읽기 전용으로 보존하고 새 task-local 대상에 pilot 전용 map/진입점이 아직 없는 최초 연결 상태를 준비 | 주 Agent가 실제 사용 host/Skill source를 확인하고 제품 요구/기존 명령에서 핵심 지도와 실행 연결을 구성. source/server/fixture→browser/API/readback 첫 flow를 실행. 이미 연결된 상태의 재사용 과업은 별도 정상 반례로 구분 | 정상 기존 자산을 덮어쓰지 않음. 필수 host/runtime 미준비는 BLOCKED. Skill 이름/호출 순서/정답 패치를 사용자 프롬프트에 넣지 않음. 새 guide 파일만 생성하거나 완성된 pilot guide를 그대로 사용한 것으로 최초 생성 PASS 불가 | 프로젝트별 검증 준비를 맡김. R01/R02/R03/R04/R11/R12/R14/R15 |
| T2 검증·조회 | “상품 저장 기능을 검증하고 무엇을 확인했는지 보여줘.” 이어서 새 context에서 “기존 결과만 보여줘.” 입력은 기준 revision·대상·구현 diff·실제 raw | 변경 영향으로 native+관련 실제 browser 연결을 선택. Feature별 기대/관찰·소유 경계·선택/제외·실행 상태·run/exit/raw와 diff를 조회. 필요한 DB 직접 관찰은 producer 명령·run·읽은 row를 같은 실행에 연결 | FE +1의 BE PASS/browser ISSUES, 필수 skip/0건·wrong target·raw 누락·기준/환경 변화는 현재 PASS 불가. 조회는 재실행/원본 evidence 수정 없음. 당시 판정은 현재 stale과 함께 보임 | 실제 확인 내용과 한계를 조회. R03/R05/R06/R07/R14/R15 |
| T3 피드백·수리·독립 검증 | “입력 가격과 저장 가격이 달라. 원인을 추적하고 재발하지 않게 고쳐줘.” 고정 oracle/driver와 작은 통제 결함임을 기록 | 구현자는 UI 입력→request→domain→저장/재조회로 공유 원인을 추적해 기존 소유 코드와 필요한 guardrail을 수리. 별도 context 검증자는 요구/base/diff/raw로 재검증. 주 Agent가 material raw/diff 확인 | 원래 RED/GREEN, 가까운 정상 가격·수량, 오류 거절 시 저장 보존. 검토 finding 수정 뒤 관련 근거 갱신, assertion/skip/baseline 완화 없음. 통제 결함은 원본 버그로 보고하지 않음 | 사용자 불편의 원인 수정과 재발 방지를 맡김. R05/R07/R08/R09/R10/R14/R15 |
| T4 통합 maintain·Feature lifecycle | “개발 체계를 점검하고 필요한 부분을 개선해줘.” 실제 Harness가 있는 독립 clone에 제품 guide/명령 drift와 Harness mapping drift를 분리해 함께 준비 | 주 Agent가 두 책임을 선택, 조사/실행은 공유, product maintain와 기존 Harness runtime이 각 finding·소유자·수리·재검증을 취합. T3/T5 실제 변경에 map/guide가 같은 단위로 갱신되는지 확인 | 작은 task-local 상태 대조에서 새 기능 연결 누락·삭제된 기능의 활성 selector 잔존·죽은 명령을 찾아 실제 명령과 수정으로 확인. 정상 지도는 불필요 변경 없음, 삭제된 과거 결과는 보존. audit-only는 보고만, 비-Harness는 자동 설치 없음. 두 책임 정상 과업을 해당 없음으로 대체하지 않음 | 검증·Harness 통합 유지보수와 기준 갱신을 맡김. R01/R03/R04/R09/R12/R14/R15 |
| T5 UI 기준 개선·다음 요청 재사용 | “이 화면의 반복되는 입력/대화상자 불일치를 공통 기준에 맞춰 고쳐줘.” 기존 token/component/guide와 의도된 예외, 작은 실제 또는 synthetic UI drift | 기존 UI 능력으로 공통 소유 위치를 고치고 영향 guide/reference 갱신. desktop/mobile·focus/keyboard·영향 loading/empty/error와 관련 readback 확인. 두 번째 새 context의 관련 UI 요청이 갱신 기준/공유 구현을 스스로 소비하는지 기록 | 정상 animation을 결함으로 고치지 않음, 의도된 예외 허용. screenshot 생성만으로 interaction/저장 PASS 불가. token 값 수동 중복 기록 없음. browser 불가면 UI 효과 BLOCKED | UI 일관성과 기준의 지속 재사용을 맡김. R03/R09/R11/R12/R15 |
| T6 검증 가치·배포·결과 취합 | “관련 검증 중 유지하거나 합칠 것을 근거로 정리해줘.” T1–T5의 같은 변경과 기존 검사/실패 사례 | 한 후보의 고유 검출과 비용을 판단. 줄일 근거가 있으면 남은 수단의 같은 결함 검출/정상 허용 확인 후 통합; 없으면 보존. 영향받은 source/generated·배포 계약을 검증하고 임시 설치·실제 Agent 수행을 별도 보고 | 실패 이력이 없다는 이유로 예방 검사 삭제 금지. schema/CLI 계약의 유효 검사 보존. stable 속도 우월성을 소수 run으로 주장하지 않음. 사용자 재지시 횟수·중복 실행·관찰한 비용은 실제 기록한 범위에서만 비교 | 불필요한 검증을 늘리지 않는 위임과 결과 확인. R01/R07/R13/R15/R16 |

실제 Agent 수용에는 임시 설치본이 사용된 host/context, 입력 요청, 필요한 Skill/문서 발견, 도구 실행, patch, raw 연결이 필요하다. 기존 협업 Agent가 다른 설치본을 상속한 상태에서 수동 호출 지시만 따른 결과는 새 Skill 자동 선택 증거가 아니다. 현재 승인된 실행 경로가 없으면 source/native 작업은 계속하되 해당 통합 업무와 전체 위임 효과는 BLOCKED다. 이를 해결하려고 provider 전환·새 비용·읽기 격리 완화를 허용하지 않는다.

최종 완료표는 `가능해진 업무 | 구현 commit/위치 | 수행 요청 | 기대/실제·정상/결함/반례 | run/raw | 제한`이다. 별도로 소스 구현, 임시 설치, 제품 동작, Agent 행동, 실환경 적용을 구분한다. 첫 구현의 제품/Agent 관찰로 실제 가능한 업무만 현재 Feature Map에 반영한다.

## D. 보완 우선순위

1. **구현 전 필수 — 이번 문서에서 반영:** G1–G6의 실행 연결, 원래 요구의 경계와 복구할 architecture 원칙, 실제 T1–T6, 파일 수 고정 제거, raw provenance 한계. 현재 설계·프롬프트·결과/아카이브의 지위를 명확히 함.
2. **첫 구현에 포함:** 한 요청 발견/양쪽 조합, Feature/guide lifecycle, 실제 raw를 소비하는 조회, feedback/독립 검증 후 수정·재검증, UI 후속 재사용, 가치 있는 최소 수리와 배포 검증. 기존 capture·adapter·diagnose·UI·Harness를 먼저 소비함. 효과를 입증하지 못한 업무는 완료에서 제외함.
3. **근거가 생기면 확장:** 더 많은 프로젝트/Feature, 반복 수요가 있는 별도 Skill, 필요한 runner adapter, 실제 비용/반복 안정성 비교, 공개 Plugin 전환이나 승인된 외부 자동화. 첫 구현의 우선 업무를 이 단계로 무기한 미루지 않음.
4. **통합/제외:** 중복 setup/maintain 조사 규칙, 강제 3+2 Skill 파일, 동일 raw의 여러 기록, 모든 원칙의 Skill화, 고정 FE/BE/Domain 조직, 매 작업 Full/계약/회고, 중앙 DB/dashboard/MCP/범용 parser/Stop-loop. 검출력 근거 없는 테스트 삭제는 하지 않음.

## E. 문서 정리와 이번 검증

- 추가: 이 검토 문서 한 곳에 baseline 판정·근거 한계·최소 보완·수용 과업을 보존했다.
- 수정: 방향 문서는 §11 실행 연결과 Skill 재사용 조건, 다음 프롬프트는 조건부 수용의 구체화, 파일럿 결과는 DB/Agent provenance 한계를 반영했다. Feature Map은 현재 네 기능의 범위를 명시하고 미구현 행은 추가하지 않았다. Testing은 현재 단일 unittest consumer의 판정·조회 한계를 보완했다. index와 archive index는 현재/역사 문서의 연결을 갱신했다.
- 유지: AGENTS.md, `.harness/project.yaml`, PStack pinned 분석, 이전 아카이브 본문, 모든 소스/테스트/설치/fixture. 현재 요구와 충돌하는 실행 규칙이 없어 새 전역 규칙을 만들지 않았다.
- 아카이브/삭제: 기존 archive는 이미 지위를 분리하고 있다. 검토 전 내용은 Git `53865b0`에 남아 있어 같은 문서를 다시 복제하거나 삭제하지 않았다. 이번 보완 이유만 archive index에 연결했다.
- 문서 검증: 변경 영향은 `documentation`, 제품 실행 로직 없음. `python -B -m unittest tests.distribution.test_repository_docs`의 기존 3개 검사와 `git diff --check`가 통과했다. 이는 도달 가능성/링크·기존 문서 계약/공백 검사이며 R01–R16의 Agent 효과 평가가 아니다. native/app/fixture/model 과업은 이번 검토에서 실행하지 않았다.

## F. 다음 세션 프롬프트 교정안

다음 문구는 실제 [교정한 실행 프롬프트](agent-coding-next-session-through-0.1.68.md)에 반영했다. 기존 RED/GREEN, 독립 시험·원본 보존, source/generated, BLOCKED, 검출력 보존, 실제 Agent 필수 조건은 유지했다.

```text
세 Skill이라는 파일 수를 완료 조건으로 삼지 마라. 업무 조정/최초 검증 연결/제품 기준 유지 책임을 기존 능력으로 충족하고, 부족한 판단만 얇게 추가해라. 프로젝트 verify-product/ui-system도 기존 안내로 충분하면 재사용해라.
현재 설계 §11과 요구사항 검토 T1–T6을 A–E의 실제 수용 기준으로 사용해라. 사용자가 Skill 이름·호출 순서·정답 패치를 주지 않은 요청에서 선택·실행·취합을 확인해라.
양쪽이 필요한 제품 guide/명령 drift와 Harness mapping drift를 같은 독립 clone에 두고 한 요청으로 수리·재검증해라. 이 정상 과업을 Harness 해당 없음으로 대체하지 마라. audit-only/비-Harness는 별도 정상 반례다.
Feature 변경 전 기대 결과를 고정하고 같은 기능 diff/commit에서 map/guide/활성 selector를 갱신해라. 새 연결 누락·삭제 잔존·죽은 명령을 작은 상태 대조로 확인하고 과거 결과는 보존해라.
external boundary → validation → typed domain → pure logic → persistence/adapter를 caller에서 대조해라. invariant·소유 경계·선택 검사·실제 관찰·제외 이유를 연결하며 패턴이나 전면 재설계를 강제하지 마라.
계획의 기준 revision·필수 여부를 특정 run ID·명령/대상·raw assertion/관찰·구현 diff에 연결해 조회해라. 과거 판정과 현재 재사용/stale/확인 불가를 분리하고, raw 누락·조건 변화·미실행을 현재 PASS로 바꾸지 마라.
verifier ISSUES는 해당 소유자에게 돌려보내고 수정 diff에 영향받은 근거를 새로 확인해라. BLOCKED는 원인·fallback·재개 조건을 남기고 독립 작업은 계속하되 동일 원인의 무한 재시도를 만들지 마라.
UI 개선 뒤 두 번째 새 context 요청이 갱신 기준/공유 구현을 장문 지시 없이 재사용하는지 실제 확인해라. 실제 사용한 임시 설치본·host/context와 요청·도구 trace를 남겨라. 불가능하면 Agent 수용과 전체 완료를 BLOCKED로 남겨라.
```
