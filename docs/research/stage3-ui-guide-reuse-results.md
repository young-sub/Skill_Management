# 3단계: UI 기준과 실행 가이드의 후속 재사용

2026-10-18. 기준은 clean `wp-20261018-stage0-compatibility`의
`02a354d35f201a9093f747d4fcdcab84eb262caa`다. 실행 전 기대 결과·실패 기준은
`.work/stage3-20261018/plan.md`와 `execution/criteria.md`에 기록했다.
별도 `20261018-plugin-readiness` 계약은 이번 작업으로 선택하거나 완료하지 않는다.

## 구현 범위

기존 `agent-workflow`, 검증 setup/maintain, `impeccable`, 접근성 및 React 스킬의
발견 경로를 연결했다. 디자인 의도·상태·반응형·접근성은 프로젝트 가이드에서
실제 token/component/state 소유자로 연결하고 값과 동작은 코드에 남긴다.
비등록 프로젝트와 작은 수정은 기존 파일·명령을 직접 사용한다.

[공통 비교 절차](../../authoring/references/repair-and-reuse.md#ui-discovery-and-comparison)는
화면·뷰포트·테마·데이터·상태를 맞추고 요청된 차이와 보존할 동작을 실행 전에
정한다. 이미지와 상호작용을 함께 판단하며 baseline 갱신으로 결함을 숨기지 않는다.
[가이드 실행](../../authoring/references/project-verification.md#execute-and-repair-the-existing-guide)은
준비→행동→관찰→정리, 원인 소유자 수리, 같은 결함 검출·정상 허용과 후속 소비를
기존 runner와 가이드에 연결한다. 새 Skill·Router·범용 runner·상태 DB는 없다.

변경 Feature는 `agent-workflow`, `ui-standards`, fixture 검증을 소유한
`native-verification`이다. 원본/생성본과 manifest, 기존 source mapping,
Feature Map을 갱신한다. 공통 runtime/API/schema 변경은 없다.

## 실제 실행과 한계

이번 실행의 raw, 실패·재시도, 시각 관찰과 후속 소비는 `.work/stage3-20261018/`에
보존한다. 패키지 검사와 fixture/모델 소비는 별도로 판정한다.

| 관찰 | 원래 판정 → 수리 후 판정 | 근거 |
| --- | --- | --- |
| 공유 터치 영역 44→48px의 의도한 변경 | 정확히 44px를 요구해 13/14 실패 → 토큰과 최소 크기 기준에서 16/16 허용 | `execution/oracle-48-original/`, 아래 `style-variants/.../larger-token/` |
| 데스크톱 History의 초점 테두리 제거 | 모바일만 관찰해 14/14로 놓침 → 15/16, 공유 UI 검사에서 검출 | `execution/original-desktop-focus-blindspot/`, 아래 `style-variants/.../history-focus-defect/` |
| 정상 연결 실행 | 실제 가이드 명령으로 16/16, skip/error 0 | `.work/connected-product-artifacts/a4943df1-2301-43c0-a3dd-4c46b6a49b70/browser.json` |
| FE의 수량 +1 전송 결함 | API/Domain 정상만으로 통과하지 않음. 화면 검사가 실패하고 저장·새 조회에 3이 남음 | `.work/connected-product-artifacts/7586be5b-be3e-421a-bc46-23dd7a0e4268/` |

두 시각 변형은 `.work/connected-product-artifacts/style-variants/4d7daf2f-e3fd-45e8-8fe6-73571876ba51/`에
있다. 원본과 결함은 격리 복사이며 운영 제품의 실제 결함이라고 주장하지 않는다.
정상·의도된 변형·결함에 동일한 수리 후 관측기를 사용했다. 기존 14개 검사 ID를
유지하고 loading/empty와 read-error 관찰 2개를 추가했다. 44px라는 특정 값의
동일성은 정상 변형을 거절하는 오류였으며, 최소 크기·실제 토큰 충족·공유
탐색/초점·반응형 기준을 제거하지 않았다.

가이드의 준비 단계는 기존 런타임 파일 확인, 별도 SQLite와 로컬 서비스 준비다.
브라우저는 응답 해제를 제어하여 loading/empty·pending을 관찰하고, 합성 503으로
read-error를 확인한다. Tab 순서는 탐색 2개→수량→저장이고 Enter로 2를 저장한다.
-1은 422·미저장, 0은 201이며 SQLite와 화면의 `[2,0]`이 서비스 재시작 후에도
유지된다. 소유 서비스 2개가 stopped이고 cleanup 오류는 0, 임시 DB·port 파일은
제거됐다. 종료 코드는 이 Windows 실행에서 1이며 정상 요청의 HTTP 결과와 구분한다.

1280/390px의 두 화면과 초점 이미지를 직접 읽었다. 48px 변형의 높이·수직 위치
변화는 의도된 차이이고, 내용·계층·탐색·초점은 유지됐다. 결함 이미지에서는 같은
키보드 상태의 주황색 초점 테두리가 없어졌다. 스크린샷 존재나 픽셀 차이만으로
판정하지 않았으며 `visual-review.md`와 실제 측정을 함께 남겼다.

수리는 fixture의 driver·artifact 수집·assertion·가이드·회귀에 한정된다.
`shared.css`, `ui.js`, API/Domain/storage 제품 코드는 변경하지 않았다.
초기 확대 검사의 키보드 초기화 오류(15/16)와 첫 회귀의 두 가정 오류도 보존했다.
관측기는 각 화면에서 body로 순서를 초기화한 뒤 Tab을 입력한다. 회귀는 합성
503을 성공 history 조회로 해석하지 않고, `:focus-visible` 일치와 실제 outline을
구분한다. 이후 같은 결함 검출·정상 허용을 재확인했다.

## 새 문맥 후속 소비

새 소비자에게 이전 대화 없이 격리 프로젝트, 19개 전체 source capability catalog,
“History 화면의 내비게이션 터치 영역을 조금 넓혀줘. 기존 공통 스타일과 동작을
유지하고 실제 확인해줘”라는 요청만 제공했다. 토큰명·가이드명·실행 명령·정답
패치는 제공하지 않았다. 소비자는 `docs/index.md`→UI/acceptance 가이드→
`shared.css`/`AppNav`를 발견하고 source `agent-workflow`, `impeccable`,
`fixing-accessibility`를 읽었다. React/Next.js 코드가 없어 React 스킬은 제외했다.

원본 파일 비교에서 변경은 `shared.css`의 공통 `--control-size` 44→48px뿐이다.
페이지별 값 복제나 observer/assertion/API/Domain 변경은 없었다. 소비자가 발견한
가이드 명령을 변경 전·후 각각 실행해 16/16, skip/error 0, 두 뷰포트·두 화면의
탐색 링크 44→48px, 동일한 초점·탐색 스타일·키보드 순서, `[2,0]` 저장·재조회와
cleanup을 확인했다. 공통 토큰을 쓰는 입력창·저장 버튼도 4px 커진 영향은
보고서에 명시됐다. 주 세션도 raw/hash/diff와 전후 이미지를 직접 확인했다.

근거는 `followup/project/report.md`, `followup/parent-inspection.json`,
`followup/project/.work/connected-acceptance/history-nav-{before,after}-20261018/`다.
소비자의 Impeccable context는 기존 디자인을 유지하는 좁은 수정 경로를 안내했고
CSS detector는 `[]`였다. detector 결과는 실제 브라우저 검증과 별개다.
원본 출력은 해당 소비자의 도구 대화에 있고 보고서가 그 경로를 기록한다.

구분: 실행 가이드 수리자는 전체 과제·원인 분석을 받은 **도움받은 소비**다.
후속 소비자는 제공된 전체 catalog/격리 프로젝트 안에서 추가 힌트 없이 기준과
소유자를 발견했다. catalog와 작업 자체를 제공했으므로 **native-host의 무도움
Skill 발견**은 아니다. 처음 상위 Git 상태에서 branch/HEAD/dirty 경로 목록을
봤으며 diff나 과거 증거는 보지 않았다. 따라서 완전한 blind 실험이라고 하지 않는다.
사용자의 추가 개입은 없었지만 단일 사례이며 일반 성공률·비용 감소는 unknown이다.

후속 소비의 PowerShell JSON 읽기와 `rg` 옵션 해석 오류 각 1회는 보존했다.
동일 raw를 Python으로 읽고 검색 구분자 `--`로 수정했으며 브라우저 재실행을
만들지 않았다. Impeccable의 업데이트 안내에는 업데이트를 실행하지 않았다.
전역 상태 전수 감사는 하지 않아 부수적 cache 변화 없음까지 보증하지 않는다.

## 영향별 검사 결과

| 검사 | 이번 결과 |
| --- | --- |
| 공유 UI 소유자·예외 현재성·작은 작업·무실행 조회 | 8개 통과, `ui-regressions.json` |
| catalog·자가완결성·생성·배포 회귀 | 36개 통과, `resources.json` |
| 문서·cohort cutover | 14개 통과, `docs-cohort.json` |
| 독립 패키지 CLI·안내·리소스 소비 | 1개 통합 검사 통과, `package.json` |
| required Chromium 회귀 | 3개 통과, `execution/unittest-final.log`; 정상 2회·overwrite 거부·API/FE 결함·시각 변형 포함 |
| 원본/생성 drift·배포 검증 | 각각 종료 0, `drift.json`, `distribution.json` |

공통 runtime/API/schema와 테스트 발견 규칙은 바뀌지 않아 Full은 선택하지 않았다.
시각·상태 관측 로직은 fixture capability 범위이며 해당 실제 브라우저 회귀를
선택했다. 원본 확인의 터미널 인코딩 문제, 존재하지 않는 테스트 파일 1회 읽기,
적용 전 patch-context 거절 3회와 Git index의 sandbox 거절도 실행 이력에 남겼다.
Git 등록은 기존 커밋 권한으로 재시도해 성공했으며 패키지는 새 파일 등록 뒤 검사했다.

기존 active Goals·project-verification·0/1/2단계 증거와 전역 원본 395개 파일의
해시는 `preservation-before.json`/`preservation-after.json`에서 동일하다.
별도 readiness의 상태나 완료 조건을 이 결과로 갱신하지 않는다.

설치본·전역 설정, 유료 모델 평가, push·배포·protected branch 통합,
4단계 이후 구현은 제외한다. 운영 제품·native-host·일반적인 발견 성공률이나
비용 감소는 이 격리 사례로 입증하지 않는다.
