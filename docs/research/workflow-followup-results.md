# 0.1.70 후속 소비와 중복 검사 통합

[현재 설계](agent-coding-system-direction.md)의 다음 세 경계를 순서대로 확인한다: 기존 요청의 실제 완료, 새 문맥의 관련 업무 재사용, native host 발견·hook·보호 수락. 이 기록은 [이전 개선 실행](workflow-improvement-results.md)과 별도이며 과거 결과를 이번 실행으로 세지 않는다.

## 출발점과 보존

시작 시 저장소는 clean `main@9350b21b27fa2810d7cb7d172393b3e26d7ae180`, 버전 0.1.69였다. 전용 branch `wp-20261017-sequential-consumption`에서 기록을 갱신한다. 실제 제품 소비는 기존 격리 `product`의 clean `bb99fbb`에서 시작했다. 원본 제품·설치본·전역 설정은 변경하지 않는다.

이번 근거는 저장소 `.work/workflow-next-20261017/`, 실제 제품과 기존 실패 근거는 `.work/workflow-improvement-20261017/product/`에 보존한다. 소비 패키지는 이전에 고정한 `frozen-0.1.69-final/`이며 Python bytecode 생성을 끈다. 이전 package CLI/fixture/native 미검증의 경계는 그대로 유지한다.

## 1. 기존 직원 화면 요청

정확한 task `26d47b77-8b91-44bd-b966-554809d3b85d`를 재개했다. 직원 PIN/포커스가 현재 요청이고, 다른 제품 기능의 전체 잔여는 별도다. 최초 등록 실행은 native 56개를 통과했지만 browser의 catalog-import가 실패했다. 직원 흐름 통과만으로 요청을 완료하지 않았다.

실제 업로드 파일은 존재했지만 274자 Windows 경로를 전달하면 Chromium `File.text()`가 `NotFoundError`를 냈다. 같은 bytes를 Playwright 파일 payload로 전달한 작은 진단은 성공했다. 이를 제품 파서 결함과 구분하고 격리 제품의 기존 runner에서 파일 bytes를 읽어 suite에 전달하도록 고쳤다. 정상·잘못된 백업 파일 모두 같은 경로를 사용하며 missing file은 오류로 남는다. standalone suite 호출은 유지했다. 새 runner나 의존성은 없다.

제품 커밋 `f76f1e8`은 runner, catalog suite 호출부, 짧은/긴 경로·정상/잘못된 내용·누락 파일 회귀, 검증 가이드를 함께 포함한다. 실제 실패 캡처와 byte-path 진단이 행동 RED이며, 새 helper를 아직 export하지 않아 발생한 초기 테스트 import 오류는 행동 RED로 세지 않는다.

수정 후 등록 실행은 native 57개, reporter 9개와 기존 browser 7개 suite를 통과했다. 실제 source/served root 일치, 실행 전후 source 불변, 소유 browser 2개 종료·server 종료·cleanup 오류 없음도 확인했다. 직원 제목의 키보드 포커스, 포인터 사용, 320px PIN gate와 import modal의 현재 캡처를 직접 검토했다. 실제 UI 승인이나 서버 인증 증거는 아니다.

7개 Feature/check 소비자가 실제 명령 4개를 실행했다. native 공유 실행은 재사용됐지만 같은 전체 browser suite가 두 check 이름으로 두 번 실행됐다. 이는 다음 유지보수 업무의 실제 재현이다. source commit 전에 prepare한 1회는 실행하지 않고 폐기했으며, 그 준비 비용과 최초 실패를 보존한다.

주요 근거: `stage1-execute.json`(실패), `upload-failure-diagnosis.json`, `file-upload-probe.cjs`, `upload-focused-green.json`, `stage1-execute-fixed.json`, `stage1-command-inventory.json`. 현재 제품 raw는 해당 task의 `runs/62a9915b-cf48-4981-aaa4-a6faef30afdc/` 아래에 있다.

4개 관련 기능의 실제 호출/상태/데이터 소유자, 계약·의존성·실패 경계와 필요한 화면을 검토했다. 검토는 기존 실행에 결합했고 제품 명령을 다시 실행하지 않았다. 기존 포커스 예방도 원래 실패를 역사적 근거로 유지하면서 이번 keyboard/pointer 캡처에 연결했다. `READY_FOR_REVIEW`, 현재 요청 action 0, feedback `RESOLVED`가 되었고 전체 프로젝트는 8개 잔여와 `PARTIAL`을 유지한다. 이는 사용자 검토 준비이며 제품 전체 승인과 다르다.

첫 feedback 갱신 때 조회 결과 전체를 제출해 읽기 전용 binding 필드 보호에 거부됐다. 상태는 변경되지 않았으며 `id/feature/prevention_review`만 제출해 갱신했다. 이 Agent 입력 실수와 재시도도 `stage1-prevention-refresh{,-02}.json`에 보존했다. 보호를 약화하거나 제품 검사를 다시 실행하지 않았다.

## 진행 상태

절대 `--state`로 수행한 최종 조회는 `read_only=true`, 제품 명령 0회이며 task·기존 근거 460개 파일의 bytes를 유지했다 (`stage1-final-lookup.json`, `stage1-readonly-verification.json`). 소비 패키지도 253개 파일 집합과 manifest/payload hash가 모두 그대로였다 (`package-before-fresh-consumption.json`).

## 2. 새 문맥의 검증 유지보수

새 문맥 Agent에는 자연어 불편, 격리 제품, 기존 패키지 진입점과 보존 경계만 전달했다. Agent가 같은 일곱 browser suite를 두 check 이름으로 호출하는 등록 중복을 찾았다. 제품 `3a8563b7a5d185a1ee00dfeefe25eb4e50760ccd`는 기존 공유 check에 CatalogImport를 연결하고, 실제 runner 전체의 dependency/fixture를 일치시켰다. 12개 CatalogImport assertion은 그대로다. 두 check가 같은 파일에 쓰면서 조건은 다른 경우 기존 prepare가 차단했고, 조건을 실제 실행에 맞춰 고쳤다.

커밋 전 등록 실행은 native 58개, reporter 9개, browser 일곱 suite를 통과했다. 실제 명령은 네 개에서 세 개, 전체 browser 실행은 두 번에서 한 번으로 줄었다. 잘못된 백업 거부, 유효 파일 복구, 취소, 정상 적용, 저장 실패 시 기존 목록 보존을 계속 확인했다. 현재 source/served source와 cleanup도 확인했다. 신규 회귀는 공유 등록과 고유 assertion을 함께 보호하며, 다른 lifecycle의 별도 check는 허용한다. Guide와 Feature Map은 이 owner를 연결한다. 구조 예방 feedback은 실제 capture에 결속해 RESOLVED가 됐다.

공통 플러그인은 과거 baseline에 prevention 라벨이 없다는 이유로 이 통합을 `prior_detection_scope_unknown`으로 차단했다. 이미 있는 이름으로 합치는 작업은 순수 이름 변경 `rebind`에도 해당하지 않았다. 부모 Agent가 이 경계를 확인한 뒤 공통 수리를 맡았으므로 전체 완료를 무도움 성공으로 계산하지 않는다.

0.1.70은 기존 검사 유지보수 경계에 `consolidate / duplicate_execution` 증명을 추가한다. Git의 원본 등록 명령·assertion과 실제 입력, 기존 coverage/prevention, 현재 task에 결속된 공유 실행을 비교한다. Report 출력 경로만 다른 같은 runner가 대상이며, 추가 입력 연결과 metadata 변경을 허용한다. 원본 변조, 필수 검사 누락, 입력 누락/변경, 미실행·오래된 target은 차단한다. 과거 라벨을 새로 꾸미거나 일반적인 서로 다른 검사 간 동등성을 추정하지 않는다. 새 runner/parser/state store는 없다.

커밋 후 native 결과는 source revision/diff/status 차이로 STALE이 됐다. 동일 bytes의 구조 예방 재사용과 native 실행 현재성은 별도다. Agent는 이를 성공으로 덮어쓰지 않았다. Synthetic 후속 task `7c195b0c-3471-4321-b5b9-2a913fe92dd8`는 공유 검사·기준·예방 owner를 발견했고 조회에서 제품 명령 0회를 확인했다. 새 사용자 업무의 무도움 실행 성공은 아니다. 자세한 실패·재시도·도움·unknown 비용은 해당 task의 `discovery-result.md`와 `stage2-assistance.json`에 남았다.

## 3. Native host 경계

현재 native CLI는 `0.160.0`이며 plugin 관리 명령의 help를 확인했다. 기본 sandbox에서는 active home의 plugin/config와 account 파일 존재 확인이 Access Denied였고, 승인된 읽기 전용 조회에서는 setup marker/account 파일 존재를 확인했다. 자격증명 내용은 읽지 않았다. Active home에서 `agentic-coding` 활성화 항목이나 예상 cache layout의 해당 manifest를 발견하지 못했다. Help나 준비 파일 존재는 native 발견·hook 전달·보호 수락의 증거가 아니다.

실제 발견·hook·보호 수락은 미검증이다. 재개에는 최종 패키지 검토 후 격리 지원 home의 설치/활성화·hook 신뢰 변경 승인, 새 문맥의 실제 요청, 별도 보호 host policy/driver가 필요하다. 현재 승인은 설치·전역/신뢰 변경·유료 호출을 금지하므로 실행하지 않았다. [공식 plugin 문서](https://developers.openai.com/plugins/build/plugins)도 설치/활성화와 hook 신뢰를 구분한다. 로컬 제품 업무의 공통 차단으로 사용하지 않는다. 현재 관찰은 `stage3-host-preflight.json`에 있다.

## 검증과 효과의 범위

Focused workflow/runtime 검사 118개는 실패 없이 완료됐지만, 같은 명령에 잘못 적은 존재하지 않는 `test_workflow_effects` 때문에 invocation 전체는 exit 1이었다. 이를 PASS로 바꾸지 않았다. 실제 effect/필수 실행/조회/hook 회귀는 올바른 모듈로 58개 통과했다. 최종 통합/순수 이름 변경/변조 경계 4개와 package/update/resource/docs/public API/release 44개도 통과했다. 소스 변경이 이어진 중간 실행을 고정 소스 판정으로 부르지 않는다. 이 변경은 workflow 검사 보존 capability에 한정하므로 Full·모델 벤치마크를 반복하지 않았다.

| 목표 | 이번에 확인한 것 | 남은 경계 |
| --- | --- | --- |
| 위임·가시성 | 기존 요청 완료와 프로젝트 잔여 분리, 커밋 뒤 STALE 노출, 조회 0 실행 | 장기 무도움 위임·native 전달 |
| 규칙·아키텍처 | 실제 import 정상/오류/저장 보존, 호출·상태·책임 검토 | 이 제품 흐름은 FE/local Domain이며 서버 API/사업 성과 증거는 없음 |
| 피드백·예방 | runner 경로 오류 수리, 중복 등록 구조 통합, 정상 예외·고유 assertion 보호 | 새 원인별 판단과 실제 사용자 수락 |
| UI 재사용 | 기존 화면 기준·공유 owner 발견, 직원/가져오기 실제 화면과 키보드 관찰 | 이전 UI 기준 변경의 새 무도움 소비를 이번 실행으로 다시 주장하지 않음 |
| 실행 가이드 | 실제 실패를 기존 runner·가이드에 반영, 후속 발견 | Synthetic 후속 조회는 새 업무 실행 성공이 아님 |
| 검사·절차 | 동일 browser 실행 2→1, 고유 검출 유지, 과거 라벨 없는 통합의 불필요한 차단 수정 | Native source identity는 커밋 시 보수적으로 STALE; 일반 비용 절감은 미측정 |

## 최종 실제 소비

Candidate 0.1.70의 공개 packaged CLI로 원래 task `aa296108-331a-4bc8-8ff4-71978c53f74a`를 최종 제품 커밋에서 준비·실행했다. Run `30e0dcd2-ec97-41b5-b9db-47ede5c27236`은 native 58개, reporter 9개, browser 일곱 suite를 통과했다. 다섯 Feature/check binding이 실제 세 명령을 공유하며 browser 실행은 한 번이다. 두 소유 browser와 server 종료, cleanup errors 없음, source 보존을 확인했다.

동일한 원본 plan과 현재 공유 bundle을 review CLI에 연결해 `catalog-import-browser` retirement는 `PRESERVED`, 현재 요청은 `READY_FOR_REVIEW` / action 0이 됐다. 다른 아홉 Feature 잔여는 `PARTIAL`로 남는다. Review CLI의 exit 2는 이 프로젝트 전체 PARTIAL이며 오류나 검사 실패가 아니다. `stage2-candidate-{prepare,execute}.json`, `stage2-consolidation-review.json`, `stage2-final-command-inventory.json`에 실제 명령·판정·raw 위치가 있다. Resource drift, 배포 검증, 갱신 문서 검사도 통과했다.

고정 `frozen-0.1.70/`은 clean `722fee88917df69ddbd512c27869f9cb745bc64b`에서 만들었다. 19 Skill / 253 파일, manifest SHA-256은 `803afb3648f529a16f9486a96c2bae2a58462d4ab17c6b4f25f656aab73db645`다. 기존 package 검증 함수로 파일 집합과 모든 hash를 확인했다. 실제 소비한 candidate와는 build origin/manifest만 다르고 실행 payload는 동일하다.

고정 package의 절대 state 조회도 현재 요청 `READY_FOR_REVIEW`, action 0, 현재 검사 재사용과 프로젝트 잔여 분리를 유지했다. 제품 명령은 0회였고 task/raw/package 1,066개 파일의 bytes를 보존했다 (`frozen-current-lookup.json`, `frozen-readonly-verification.json`, `frozen-package-identity.json`). Package CLI 검증을 native host 수락으로 승격하지 않는다. 로컬 통합/생성 worktree 정리의 최종 식별자는 `.work/workflow-next-20261017/delivery.json`에 보존한다. 기존 raw와 실패한 시도는 삭제하지 않는다.
