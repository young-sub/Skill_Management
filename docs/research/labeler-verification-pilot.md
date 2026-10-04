# Labeler 실제 검증 파일럿과 최소 개선

실행일: 2026-10-04~05 KST. [실행 프롬프트](agent-coding-next-session.md)를 수행한 결과다. 고정 소스의 실제 사용자 흐름, 통제 결함, Agent 위임을 확인하고 공통 캡처와 복제 프로젝트의 검증 연결을 구현했다. 원본 제품에 반영하거나 공개 배포한 결과는 아니다.

## 기준과 보존 범위

| 대상 | 고정 기준 / 결과 |
| --- | --- |
| 관리 저장소 | `wp-20261004-agent-coding-foundation`, 시작 `f68d3414ca11330faba5ee8a34e39b11db030376`, dirty 없음. 공통 개선 `264fef0` |
| 원본 Labeler | 시작 시 local main `1a10164ae7a3458e62b4accf8d52b20319f007e0`를 고정. checkout `ab7aed6a6c9c64ecc57aa6134f6088d60265b72c`, branch `wp-W-20260909-category-delete` |
| 독립 export | `.work/labeler-verification-pilot-5a80b570/repo`, baseline `1c417ade0e9a410551c64f3e52aceae781c43a89`, branch `pilot`, origin 없음 |
| 제품 시험 commit | 실행 기반 `830ca2c`, UI 통제 결함 `f92133a`, 독립 검증한 복원 `79e7b20`, 검증 연결 `ecd7db768aef3c17c0ffc9834759944cf013b0f0` |
| 실행 환경 | Windows, Node/npm lockfile 설치, Vitest 4.1.11, cached Playwright `1.64.0-alpha-1790635538000`, Chrome 152, Codex CLI 0.160.0 |
| donor / PStack | 후보 `b40396a63b1031b8a3958d376fb3cc46499a9191`; PStack `23e4138daa01c42d4969f7a5465f82704e64f798` |

315개 tracked 파일만 경로 제외 후 export하고 별도 `git init`했다. 원본 `.git`, 미커밋 파일, dependencies/cache, `.wrangler`, DB/R2, `.dev.vars`, `.env`, credentials를 가져오지 않았다. `.dev.vars.example`도 제외했다. 독립 lockfile 설치·npm cache·로컬 D1/R2·loopback `4371`·브라우저 profile·임시 CODEX_HOME을 사용했다. 기존 developer-preview의 로컬 세션 경로로 합성 계정을 만들었으며 제품 인증 우회 코드는 추가하지 않았다. OS 파일 읽기 격리를 제공한 실험은 아니다.

최종 원본 checkout/branch와 Git status의 미추적 `%SystemDrive%/`, `src/client/commonDesigns.test.ts`는 시작 상태와 같다. 미추적 내용의 bytes 비교는 하지 않았으며 이 작업에서 해당 파일을 읽거나 수정하지 않았다. 다만 원본 main은 작업 중 `e07dcd4faf7ce9a0d76a099d9f5fb0e4997d5794`로 진행됐다. 이 작업의 원본 Git 명령은 읽기 전용이었다. 독립 변경을 되돌리지 않았고 파일럿 기준 SHA도 바꾸지 않았다. 따라서 최신 main 전체의 검증으로 일반화할 수 없다. 일반 설치본·전역 설정·push/deploy·remote migration·유료 provider는 작업하지 않았다.

## 구조와 부족한 책임

현재 공개 배포는 기존 Harness 7개와 독립 Skill 9개다. setup/design/execute/close/maintain/diagnose는 계약·실행·증거 정합성·보존·배포 drift를 다루고, Impeccable은 UI 판단/실행, multi-agent-review는 분리된 검토를 지원한다. 공통 `run_check.py`와 관리 저장소의 unittest 전용 `verify_product.py`는 이미 있었다. 후보 5개는 donor 본문을 직접 읽었으며 현재 설치·session 로딩·품질 개선으로 간주하지 않았다.

Labeler에는 제품·설계·UI 문서, styles tokens, DialogLayer, 공통 입력, shared schema/domain, Worker/D1/R2, API/도메인/인쇄 테스트가 있었다. 아래 부족함은 이 구조를 대체할 이유가 아니다.

| 관점 | 관찰한 강점 | 실제 공백 / 책임 |
| --- | --- | --- |
| Product | 저장·버전·인쇄 snapshot 정답이 기존 문서와 public API 검사에 있음 | 사용자 Feature에서 FE/BE/Domain/데이터/검증을 연결한 실행 지도가 부족. 복제 guide에 3개 Feature를 연결 |
| Domain | 가격·묶음·버전·측정·layout invariant 검사가 실제 결함을 검출 | 테스트 수로 품질을 판단하지 않도록 알려진 결함/정상 대조를 기록 |
| BE | 충돌·validation·account isolation·immutable persistence 검사 | native PASS가 실제 FE 입력·운영 인증·provider 검증을 대신하지 못함 |
| FE | tokens, 44px controls, 공통 focus/Escape, responsive 규칙 | client selector는 renderer/API/workbook에 치우쳐 ProductForm·library/workspace·PrintManager의 실제 조작이 빠짐 |
| E2E | 앱/Worker/D1 및 실제 인쇄 경로가 로컬에서 작동 | 표준 browser 명령·source/server 확인·저장 readback 연결이 없었음. 작은 driver로 보완 |
| Architecture | 외부 입력 → shared validation → Worker → persistence 경계가 이미 있음 | 이번 가격 통제 결함은 전송/저장 경계의 위반. 새 state machine/domain framework를 만들 근거 없음 |
| 유지보수 | Harness mapping/distribution 검사는 있음 | 제품 의미·UI 정답의 갱신은 Feature 변경 소유자의 책임. Harness maintain가 그 의미를 자동 검증한다는 설명은 부정확 |

## 실제 흐름과 근거

원문 요구의 근거는 고정 소스의 `docs/label-signage-design.md`, `docs/product-architecture.md`, `docs/ui-ux-upgrade.md`다. 기존 동작을 요구사항으로 역추론하지 않았다. 복제 프로젝트의 `docs/verification-pilot.md`가 사용자 행동·기대 결과·invariant·FE/BE/Domain·데이터·실행 방법의 단일 연결 지도를 소유한다.

이하 경로는 모두 `.work/labeler-verification-pilot-5a80b570/` 아래다. raw 자료는 기존 임시 보존 정책을 따르며 이 문서가 지속 판단을 남긴다.

| Feature | 실제 관찰 | 근거 / 판정 범위 |
| --- | --- | --- |
| `product-save` | 브라우저 가격 3200·수량 2·box 입력 → 저장/API → reload → 3500 수정. stale 409·불완전 묶음 400 뒤 데이터 동일. 모바일 dialog containment·focus·Escape | `browser-committed/observed.json`, `product-mobile.png`; `committed-product.json` native 29 assertions; `committed-db-readback.json` D1 가격 3500/350000 minor·수량/단위 일치 |
| `design-reopen` | library 추천 디자인 → 이름/배경/폭 변경·저장 → 재열기·폭 110 새 버전 → 이전 버전 이름/설정 보존 → stale save 409. desktop/mobile overflow 관찰 | 같은 browser record와 `design-desktop.png`, `design-mobile.png`; `committed-design.json` 5 assertions; D1 두 template config와 API 일치 |
| `mixed-print` | 상품 2개 + 직접 안내 1개, 순서 변경, 실제 측정 prepare/confirm. preview는 job 없음, confirm에 1개 생성. 현재 상품 이름 변경 후 history snapshot 동일·옛 이름 재인쇄·새 job 없음 | browser record, `print-dom.html`, `a4.pdf`, `reprint.pdf`, `print-mobile.png`; `committed-print.json` 7 assertions; D1 snapshot과 browser/API 일치 |

최종 source `ecd7db7`의 browser 실행은 28개 관찰 assertion을 통과했다. `committed-browser.json`의 native exit 0, before/after Git 동일·clean, source map과 checkout 일치를 직접 확인했다. 캡처의 제품 판정은 여전히 null이다. 화면·API·D1·PDF는 서로 다른 관찰이며 HTTP 200 또는 인쇄 이벤트 하나로 성공을 대체하지 않았다.

Poppler로 A4 PDF 1페이지, `594.96 × 841.92 pt`를 확인하고 PNG로 렌더링해 3개 인쇄물의 순서·회전 배치·3500원·2박스·과거 이름을 눈으로 확인했다. Type 3 glyph bounding-box 경고는 남았고 관찰한 렌더는 읽을 수 있었다. baseline native 6개 파일 40 assertions와 별도 `legacy-native.json`의 commonPrintBackup/printing/printLayout 7 assertions도 통과했다. 후자는 과거 인쇄/백업·layout 호환 검증이며 실제 물리 프린터 출력이 아니다.

미검증 범위는 운영 소셜 로그인/실제 타 계정 browser session, 외부 번역·결제, 이미지 업로드 전 흐름, 모든 loading/error/empty state, 모든 viewport/accessibility 항목, 물리 프린터다. 다른 계정 차단·확정 중 source/translation 변경·잘못된 측정·과거 snapshot은 관련 기존 native 검사를 재사용했다. 상품 3500 수정 후 두 번째 UI reload와 Escape 이후 원래 focus 복귀는 이번 driver assertion에 없다. 저장 실패의 상세 UI 문구를 전수 검증한 것도 아니다.

## 정상·결함·오탐·BLOCKED 대조

| 대조 | 결과 | 원인과 가장 작은 교정 |
| --- | --- | --- |
| 정상 baseline | browser 28 / native 40 통과 | 실행 경로의 정상 대조. 원래 제품 결함을 발견했다는 주장은 하지 않음 |
| UI `priceKrw + 1` 통제 결함 | `browser-price-mutant/observed.json`: 3201 ≠ 3200, ISSUES. `native-price-mutant.json`의 product backend assertions는 통과 | backend 검사만으로 FE 저장을 승인하는 공백. product-save browser 경로를 연결 |
| 저장 `priceKrw * 100 → * 10` 통제 결함 | `domain-price-mutant.json`: native exit 1, 29 중 5 실패, ISSUES | 실제 금액/소수점 persistence invariant 검사 가치 확인. 기존 테스트 유지, 원본 bytes 복원 뒤 29 통과 |
| 모바일 geometry 오탐 | `browser-baseline-02`: 등장 애니메이션 중 dialog가 viewport 밖에 보임 | 관찰 시점 결함. animation 완료를 기다림; UI style 규칙/제품 코드를 바꾸지 않음 |
| driver 조작 실패 | baseline-03/04/05: 이미 열린 details를 닫음, 버전 선택으로 card 이름 변경, 추천 key 오인 | 실행 도구 결함. 상태 확인·현재 accessible name·고정 추천 ID 사용. 제품 버그로 집계하지 않음 |
| 길이가 긴 합성 문구 | baseline-06: overflow로 인쇄 비활성화 | 실제 안전 거절. 정상 인쇄 fixture를 짧게 바꾸되 거절 증거 보존. overflow 기준 완화하지 않음 |
| 0건 / 필수 전부 skip | `zero-native.json` native exit 1 / `skip-native.json` native exit 0, 둘 다 BLOCKED | exit 0만으로 PASS 불가. native JSON의 실제 assertions/skips를 읽음 |
| 다른 run/Feature, stale source | `native-controls.json`의 wrong-run/wrong-feature/stale-source 전부 BLOCKED | invocation/source 바인딩. Git commit도 재사용 무효화 |
| 잘못된 대상 / 서버 미준비 | `wrong-target-execution.json`, `unavailable-execution.json`: 실제 child exit 2, BLOCKED | source map doctor + 필수 관찰 불가 판정. outer shell 성공/HTTP 200에 기대지 않음 |
| 새 report 대신 기존 report, missing/malformed | 관리 capture regression에서 실행 전 거절 / error 기록·native exit 보존 | 공통 실행 도구에서 구조적으로 방지. editable 파일을 인증하는 기능은 아님 |

UI mutant와 Agent RED/GREEN은 동일한 frozen driver SHA-256 `eb1571346306e482ba4c51507dfc29ebd004701e8f9243028c5537553f2fa710`에서 비교했다. 뒤에 doctor/판정 metadata를 보완했으며 가격 기준을 바꾸지 않았다. 실험용 결함 두 개는 모두 해소했다. 최종 복제 `src/`는 export baseline과 diff가 없다.

## Agent 위임에서 확인한 것

기준 조사, 구현, 독립 검증의 질문·입력·쓰기·중단 조건을 분리했다. 구현 Agent는 복제 `src/client`만 수정할 수 있고 정답/driver/config 변경과 server 시작·종료·commit을 금지했다. RED 가격 불일치를 재현하고 `+1`만 제거했다. 검증 Agent는 구현자의 완료 보고를 정답으로 받지 않고 요구·mutant base·현재 diff·고정 driver를 받았다. 제품 수정 없이 새 browser context에서 12개 assertions와 product native 18개를 다시 통과했다. main Agent는 실제 diff, frozen hash, raw browser/API와 native 결과를 확인한 뒤 commit했다.

근거: `agent-red/observed.json`, `agent-green/observed.json`, `agent-implementation-native.json`, `independent-browser/observed.json`, `independent-native-product.txt`, `independent-source-diff.patch`, `independent-verdict.json`. 요약 카드의 PASS만을 실행 증명으로 쓰지 않는다.

이것은 실제 역할/context 분리의 한 사례다. 같은 filesystem을 공유하므로 악의적인 쓰기 방지나 verifier 신원 인증은 제공하지 않는다. 모델/Skill A/B의 안정적 품질·속도 우월성, 사람이 반복 지시한 양의 감소는 미측정이다. 설치된 후보 5개를 달리하여 비교한 실험도 아니다. 기존 Windows 모델 eval의 격리 문제를 해결했다고 주장하지 않는다. 별도 custom agent 파일은 만들지 않았다.

## 구현한 최소 개선

1. **공통 도구**: `run_check.py --json-report`는 새 native report를 같은 실행 record에 수집한다. 기존 경로 거절, JSON/path/hash/error 보존, native exit와 null verdict 유지. Vitest stdout이 별도 파일 위치만 알리는 실제 consumer 공백을 메웠다. 새 parser framework나 dependency는 없다.
2. **프로젝트 adapter**: 복제 `scripts/verify-native.py`는 명시된 target root, Feature selector, 새 report와 run ID, 정확한 test files, 실행/skip/count/native exit/source 상태를 해석한다. 0/skip/wrong/stale 대조에서 BLOCKED, 실제 assertion 위반에서 ISSUES. 관리 unittest adapter에 Vitest를 억지로 맞추지 않았다.
3. **프로젝트 기준과 실행**: 3개 Feature map, 영향 규칙, native/browser driver, discovery 링크/AGENTS routing, 실행·source doctor·관찰 실패 분류를 연결했다. 의미를 가진 흐름·저장·snapshot 검사만 추가했다. 기존 UI token/component를 별도로 복제한 전역 style guide는 만들지 않았다.
4. **기존 Agent 능력**: multi-agent-review의 bounded brief와 실제 독립 실행을 사용했다. PASS/ISSUES/BLOCKED는 evidence와 범위를 함께 기록한다. 모든 변경에 같은 Agent 인원을 강제하지 않는다.

관리 `native-verification` Feature의 RED는 새 report 옵션이 없는 기존 CLI의 실제 실패였다. 수정 후 capture/adapter 21 tests, 정책의 distribution 전체 68 tests 통과; 21은 68의 부분집합이다. 문서 변경의 repository-docs/cutover 12 tests도 통과했다. `sync-skill-resources.ps1 -Check`, `validate-distribution.ps1`, `git diff --check`도 통과했다. mapped authoring/skills는 바꾸지 않아 생성본 변경이 없다. 이 검사들은 캡처/배포의 증거이며 Labeler 제품 품질이나 모델 행동의 증거와 합산하지 않는다.

## 책임 배치와 후보 재평가

| 구성요소 | 결정 / 소유할 책임 | 제외하거나 아직 주장하지 않는 것 |
| --- | --- | --- |
| Project / Feature Map | 업무 정답·UI token/component·fixture·명령·영향 판단·제품별 adapter. `ui-system`은 현재 구현/기존 문서를 source of truth로 연결 | 공통 Plugin에 가격 규칙·화면 token·Labeler 명령을 하드코딩하지 않음 |
| Execution tool | 유한 foreground 실행, native exit/timeout, 새 report, invocation/source 일치, 0/skip 거절 | 제품 정답, editable evidence 진위, server/Agent 신원 보증 |
| 기존 Skill | diagnose는 재현/원인 수리; Impeccable는 관련 화면 판단; multi-agent-review는 필요한 독립 검토; Harness는 작업/배포/보존 | 모든 제품 변경을 계약으로 시작하거나 maintain가 제품 의미를 자동 소유하지 않음 |
| Playbook | 프로젝트 guide의 Launch → Doctor → Drive → Evidence → Cleanup과 변경 기반 갱신 순서를 재사용 | 별도 같은 문서나 의무 회고를 늘리지 않음 |
| custom agent | 위험한 저장/과거 데이터/미묘한 FE 변경에서 조건부 verifier brief를 사용 | 고정 FE/BE/Domain/Architecture 4인 조직, agent 파일만으로 독립성 완료 주장 |
| Router | 현재 Skill description/AGENTS의 짧은 발견 경로 유지 | 새 다단계 mode/router, 자연어 handoff가 직접 실행보다 앞서는 구조 |
| Plugin | 공통 능력과 tool의 version·설치·host discovery 연결 | 제품 기준 소유, 완료 보증, 자동 full fan-out, 현재 일반 설치본 갱신 |

| 10/3~4 후보 | 결정 | 파일럿 근거 / 남은 조건 |
| --- | --- | --- |
| setup-project-verification | **도구와 프로젝트 guide로 흡수** | source/server/fixture와 실제 저장 연결 공백을 실제로 메움. 반복되는 setup 판단이 다른 프로젝트에서도 독립 능력을 요구하면 짧게 재도입; 지금 전체 Skill 복원 불필요 |
| ui-refine | **기존 FE 능력·프로젝트 기준으로 흡수** | tokens/DialogLayer를 재사용하고 animation/상태/readback 관찰을 guide에 연결. UI redesign·일관성 개선의 장기 효과는 미측정; 별도 framework/Skill 생성 보류 |
| improve-workflow | **diagnose와 변경 기반 Playbook에 흡수** | 결함 누락은 Feature/browser 연결, 오탐은 driver, report 분리는 capture에서 고침. 같은 원칙 문장 추가보다 실제 소유자 수정 |
| resume-work | **기존 보존/인계 절차로 흡수** | fresh verifier가 dirty baseline·기준·현재 대상·유효 evidence를 복구. 일반 resume task 품질 A/B는 미측정; mandatory 재계획/전체 검사 제외 |
| clear-writing | **이번 도입 보류; 별도 편집 과업에서 재평가** | 실질적인 문장 편집 과업이 없었다. UI마다 의무 호출하거나 무관한 benchmark를 만들 근거 없음 |

새 `verify-product` Skill 대신 직접 native adapter와 browser 명령을 채택했다. `verification-maintainer`라는 새 Skill 대신 변경 소유자의 기존 map/guide 갱신 책임과 bounded review를 채택했다. 독립 Skill은 반복되는 판단이 기존 소유자/직접 명령만으로 해결되지 않는 증거가 생겼을 때 추가한다. `write-a-skill` 배포 제거는 유지한다.

PStack의 [create-verification 원문](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/create-verification-skill/SKILL.md)의 실행 가능한 lifecycle·실제 흐름, [maintain-verification 원문](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/maintain-verification-skill/SKILL.md)의 drift 교정은 이번 파일럿에 유용했다. 채택한 것은 능력과 책임이며 전체 디렉터리 계층이 아니다. 모든 Feature의 병렬 live 실행, 모든 원칙의 Skill화, 고정 검사 개수, orch의 verdict/evidence 문자열을 실제 실행/독립성으로 해석하는 방식은 제외한다. 기존 [PStack 분석](pstack-analysis.md)의 한계를 유지한다.

## 테스트 정리와 앞으로의 최소 흐름

삭제 후보는 `ProductForm.test.tsx`의 option HTML, `App.test.tsx`의 정적 문구, `CheckboxField.test.tsx`의 class/label, `DesignEditorPalette.test.ts`의 inventory 모양이다. 이번 실제 browser 연결만으로 이 검사들의 category choice·accessibility·compatibility 의미가 모두 대체됐다고 입증하지 않았다. **삭제하지 않았다.** 상품/디자인/인쇄/계정 경계·backup·legacy/layout/readiness 검사는 실제 invariant와 결함 검출 근거가 있어 유지한다.

기능 변경자는 해당 Feature의 기대 결과와 영향을 확인한다. 먼저 관련 native 경계를 실행하고, FE 저장/디자인/인쇄가 바뀌면 그 Feature의 실제 browser 흐름과 API/저장 readback을 실행한다. UI는 기존 token/component/reference와 관련 desktop/mobile·focus/state를 확인한다. 결과는 scope와 raw evidence를 붙인다. 위험/누락이 크면 bounded verifier를 추가한다. 발견한 회귀·오래된 명령·관찰 오류는 해당 map/check/component/tool 소유 위치 한 곳에서 고친다. 필요한 검사가 끝나면 완료하고, 모든 Feature 전수 실행/규칙 자동 축적/주기적 모델 평가를 추가하지 않는다.

관찰 지표는 FE 결함 누락 1건(backend만 사용했을 때) → 같은 결함 browser 검출, Domain 통제 결함 검출, skip exit-0 거짓 완료 거절, UI geometry 오탐과 driver 실패 교정이다. final browser 한 실행 캡처는 약 8초대였으나 안정적 median·전체 환경 구축/Agent/유지 비용·사람 반복 지시량은 측정하지 않았다. native count 증가를 품질 개선 지표로 삼지 않는다.

## Plugin 전환 범위와 실제 호스트 확인

[현재 공식 Plugin 구조](https://developers.openai.com/plugins/build/plugins)를 확인하고, 기존 source에서 임시 package를 구성했다. `plugin-probe/marketplace/plugins/labeler-native-probe/`에는 공통 capture, 프로젝트 native consumer의 시험용 사본, 기존 multi-agent-review, discovery용의 짧은 Labeler probe Skill이 있다. 마지막 두 제품 전용 요소는 호스트 연결 시험 재료이며 공통 공개 배포에 채택한 새 Skill이 아니다. package copy/hash를 확인했고 canonical source는 관리 scripts/기존 skills와 복제 프로젝트에 남는다.

Codex 0.160.0에서 task-local marketplace 등록 → 실제 plugin 설치 → fresh app-server `skills/list`에서 cache의 enabled Skill/pluginId 확인 → installed cache의 tool로 복제 target의 native 29/5/7 assertions 실행 → 중복 설치/cache 재사용 → `0.1.0 → 0.1.1` 새 cache version 설치를 확인했다. local marketplace upgrade는 Git marketplace가 아니므로 거절됐다. 추가 재현 run `20261004T151153Z-cb52dbf2`에는 실제 CLI returncode/stdout/stderr와 initialize 후 skills/list 요청·응답 원문, duplicate와 `0.1.1 → 0.1.2` 설치를 남겼다. 요약의 상수 PASS를 증거로 쓰지 않고 raw 응답과 native exit/JSON/hash를 확인했다. 사용한 임시 CODEX_HOME의 plugin/marketplace는 제거했고 package와 evidence는 보존했다. 일반 host 설치/설정은 갱신하지 않았다.

빈 manifest `{}`는 CLI install exit 0이지만 Skill discovery가 없었다. 이를 설치/로딩 완료로 세지 않았다. 지원되지 않는 marketplace root와 UTF-8 BOM도 거절됐다. Wrangler stderr의 사용자 AppData log EPERM은 native assertions가 실제 통과한 것과 구분해 기록했다. 모델 호출·Skill 선택/지침 이행·hook 실행·원격 Git marketplace update·유료 provider는 검증하지 않았다. host discovery가 곧 모델 행동 증거라는 주장은 하지 않는다.

채택할 첫 공통 Plugin 범위는 **단일 canonical capture CLI + 선택적인 기존 multi-agent-review와 그 리소스의 생성 패키징**이다. 프로젝트 adapter/Feature Map/UI 기준은 프로젝트에 남기고 `--root`/`--capture`를 명시한다. 직접 CLI/CI를 계속 지원한다. 현재 임시 package는 연결 가능성을 확인한 것이며 public catalog나 일반 설치본 전환을 완료한 것은 아니다. 공개 전환 시 기존 resource-map/distribution을 사용하는 생성 경로와 설치/업데이트 회귀를 갖추어 수작업 helper 사본을 늘리지 않아야 한다. 실제 모델 session의 발견·선택 행동은 별도 수용 기준이다.

새 MCP/중앙 DB/dashboard/router/자동 full-run/Stop-loop hook는 포함하지 않는다. Hook은 [공식 trust 경계](https://developers.openai.com/codex/hooks)를 따르고 미지원/미신뢰/오류/timeout/중복을 성공으로 세지 않아야 한다. 이번 package에는 hook가 없고 직접 명령을 사용했다.

## 재실행과 검증 범위

복제 `docs/verification-pilot.md`의 Launch/Doctor/Drive/Evidence/Cleanup을 따른다. 최초 lockfile 설치와 local migration은 그 명령을 사용하고 remote/deploy/catalog/provider script는 실행하지 않는다. cache/profile/log/config는 작업 소유 root에 둔다. 기존 서버/DB/출력을 덮어쓰지 않는다.

```powershell
$pilot = (Resolve-Path .work/labeler-verification-pilot-5a80b570).Path
$env:WRANGLER_LOG_PATH = "$pilot/wrangler-logs"
$env:WRANGLER_SEND_METRICS = 'false'
python "$pilot/repo/scripts/verify-native.py" --root "$pilot/repo" --capture scripts/run_check.py --feature product-save --output "$pilot/new-product.json"
# Owned localhost:4371 server must be launched first using the project's pilot config.
# From the clone; use a new artifact directory and task-local browser cache:
node scripts/verify-flows.mjs ../new-browser all
```

`identity.json`, `plan.md`, `native-controls.json`, committed native/browser records, `committed-db-readback.json`, PDF/PNG/DOM, Agent raw records, `plugin-probe/result.json`와 `plugin-probe/repro-runs/20261004T151153Z-cb52dbf2/`의 host/CLI raw 기록 및 `reproduce_plugin_probe.py`가 재현 근거다. JSON report/path/hash는 editable evidence의 consistency 검사이며 signed attestation이 아니다. 초기 실패 로그는 버리지 않았고 제품 결함과 실행 도구 실패를 구분했다. 소유 브라우저를 finally/고유 CLI session close로 닫고 소유 foreground 서버를 종료했다. source repo와 fixture/evidence는 삭제하지 않았다.
