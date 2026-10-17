# pstack 비교와 실전 개선 판단

현재 설계는 [단일 설계 기준](agent-coding-system-direction.md)을 따른다. 이 문서는 0.1.70의 남은 문제를 pstack과 비교한 판단 및 0.1.71의 한정된 실행 기록이다. 시작점은 clean `main@9a19027954a81977c96329f63e305de77bd89ca0`; 전용 branch는 `wp-20261017-pstack-practical`이다. 과거 소비 결과를 이번 성공으로 다시 세지 않는다.

## 비교 기준과 우선순위

pstack은 로컬 `pstack-review/.agents`의 0.15.25, 고정 리비전 `101b274dd991f694e1f7024be2157e5f3adf07de`를 읽었다. 비교한 원본은 `skills/architect/SKILL.md`, `skills/correct/SKILL.md`, `skills/create-verification-skill/SKILL.md`, `skills/maintain-verification-skill/SKILL.md`, `skills/poteto-mode/playbooks/shipping.md`다. `review-20261017/review.md`와 `final-verification.json`의 프로토타입·실행 결과는 과거 조사다. 원문 코드를 복사하지 않았다. 원본 저작권·라이선스는 Lauren Tan / MIT이며, 향후 원문을 옮기면 고정 리비전·현지 변경과 고지를 함께 보존한다. 앞선 [pstack 조사](pstack-analysis.md)는 다른 리비전의 기록이다.

| 사용자 목표 | pstack에서 참고할 점 | 현재 구현과 개선 포인트 | 이번 처리 / 남은 확인 |
| --- | --- | --- | --- |
| 위임한 검증을 이해하고 신뢰 | 실제 사용자 경로와 부작용을 관찰하고 증거를 보존 | 선택 이유·실제 실행·현재성·잔여를 연결하는 기존 runtime 유지. 모든 공개 조회 경로에서 동일하게 오래된 근거를 거절해야 함 | 최우선: direct plan 조회의 미추적 파일 변경 누락 수리. 대량 위임의 사용자 개입 감소는 미측정 |
| 업무 규칙과 아키텍처, FE/API/Domain | architect의 호출부 먼저 작성, 상태·데이터 소유권을 기준으로 설계 | 현재 영향 지도와 owner review는 존재. 사업 가치 가설과 실행 가능한 업무 규칙을 구분하고, 실제 제품의 연결 경로를 검증해야 함 | 이번은 장바구니 Domain/native 사례. 기존 full-stack fixture를 실제 제품 전체 증거로 승격하지 않음. 다음 연결 변경에서 입력→API→Domain→저장→새 조회를 정상·우회 경로로 확인 |
| 피드백과 근본 원인 예방 | correct의 구조→타입/제약→자동 검사→최소 문서 | 분류·owner·원래 실패/우회/정상 근거의 기존 흐름 유지. 문서 규칙을 추가하기 전에 공통 owner의 빠진 연결을 수정 | 제품 결함과 검증기 결함을 구분. 새 검사기나 상태 저장소 없이 기존 source snapshot을 direct 조회에도 연결 |
| UI 기준 지속 개선 | 처음 읽는 Agent가 실제 진입점·행동을 찾게 하는 가이드 작성 원칙 | UI guide→실제 token/component 연결은 기존 구현. pstack의 위 네 Skill만으로 디자인 시스템 자동 개선을 보장하지 않음 | 다음 관련 UI 요청에서 정답 token·패치·CLI 순서 없이 소비를 검증할 필요. 이번에는 새 UI 효과를 주장하지 않음 |
| 실행 가능한 검증 가이드 | create의 launch/doctor/drive/evidence/cleanup; maintain의 실행 기반 갱신과 제품/관측기 문제 분리 | 기존 runner/parser·Feature Map을 유지하고 실패에서 가이드를 보완 | 공개 CLI로 실제 제품 정상/결함/복원 조회를 비교. 초기 의존성 누락 실패도 보존. 새 범용 runner나 전수 실행 절차를 만들지 않음 |
| 효과 있는 검사만 유지 | 겹치는 실행을 합치되 사용자 경로와 실제 판정은 보존 | 동일 browser 2→1은 이전 0.1.70 결과. 이번 후보는 동일 bytes 커밋 후 재실행 감소 | Git 상태를 읽는 명령까지 자동 재사용하면 잘못된 성공이 가능. Git 영향·의존성·설정·기대 결과 불변 증명 없이 STALE 보호를 삭제하지 않음 |

한 계획으로 **공개 조회 반례 재현 → 공통 owner 수리 → 집중 회귀 → 격리 제품 소비 → 고정 패키지 → 로컬 통합**을 진행했다. 새로운 Router/DB/dashboard, 고정 다중 Agent, 모든 Feature 반복 전수 검사는 채택하지 않았다. pstack보다 성능이 좋다는 주장은 동일 조건 비교가 없어 하지 않는다.

## 재현과 수리

새 Domain 파일을 아직 Git에 추가하지 않은 상태에서 검사를 실행하고, 그 파일의 내용을 바꾸면 HEAD·tracked diff·status 문자열은 그대로일 수 있다. Bundle 조회는 기존 untracked digest를 다시 측정했지만, 개별 `--plan --record --assessment --current-context` 조회는 revision/diff/status만 확인했다. 실행 때 저장한 current-context를 재사용하면 오래된 PASS를 현재 PASS로 표시했다.

`verification_results._item_result`가 기존 source snapshot의 untracked digest를 직접 재측정·비교하도록 연결했다. 이전 형식에 없던 근거를 소급 생성하지 않는다. 파일 접근 거부/안전 경로 검사 실패는 현재 성공을 허용하지 않는다. 실행·캡처·TaskStore·공개 API 구조는 그대로다. Git metadata 변경에 따른 보수적인 무효화도 유지한다.

집중 회귀는 실제 명령의 입력 5→6 변경, 같은 Git status, 역사적 PASS와 현재 STALE 분리, 원래 bytes 복원 후 PASS, 조회의 제품 명령 0회와 raw 보존을 확인한다. 최초 테스트 작성의 bundle 자료형 오류는 행동 RED가 아니며, 이를 고친 뒤 기존 코드에서 잘못된 현재 PASS를 별도로 재현했다.

실행 근거는 저장소 `.work/pstack-practical-20261017/`에 보존한다. 최종 소비·검증·패키지 식별자는 이 문서의 아래 결과와 해당 디렉터리의 기록을 함께 확인한다.

## 이번 실제 소비와 판단

기존 격리 제품 `3a8563b7a5d185a1ee00dfeefe25eb4e50760ccd`를 새 `product/`에 복제했다. 원본 제품과 이전 소비 복사본은 수정하지 않았다. `src/session.ts`를 새 복사본의 Git index에서만 제외해, 실제 Domain 파일을 아직 등록하지 않은 개발 상태를 재현했다. 새 사용자 기능을 완성했다는 증거가 아니라 **기존 실제 제품에 대한 통제된 결함 실험**이다.

공개 0.1.70 패키지의 기존 prepare/execute와 등록 `local-native` 명령을 사용했다. 첫 실행은 복제본의 Vite 의존성 누락으로 57/58이었으며 `product-execute.*`, `product/.work/probe/`에 보존했다. 설치 없이 기존 의존성을 package 단위로 연결하고, 생성 캐시는 복제본의 일반 디렉터리에 두었다. 새 `probe-02` 실행은 기존 58개 모두 통과했다. 이후 음수 수량 거절 조건만 제거한 mutant에서는 실제 장바구니 규칙 검사 한 개가 실패했다. 기대값·assertion·검사 선택을 완화하지 않았다.

| 같은 보존 근거의 조회 | 정상 코드 | 실제 결함 삽입 | 원래 bytes 복원 |
| --- | --- | --- | --- |
| 0.1.70 개별 plan | PASS | **잘못된 현재 PASS** | PASS |
| 기존 bundle | PASS 실행 근거 | STALE / BLOCKED | 기존 기준 유지 |
| 수정된 package 개별 plan | PASS | STALE / BLOCKED; 역사적 PASS 유지 | PASS |

조회는 제품 명령을 0회 실행했고 원래 실행 근거 12개 파일의 경로·hash가 그대로였다. `consume.py`, `probe-02-baseline-resume-summary.json`, `probe-02-candidate-final-summary.json` 및 각 공개 CLI argv/stdout/stderr가 근거다. 최초 소비 스크립트의 Windows 기본 인코딩 오류도 보존했으며, UTF-8 읽기로 고친 재시도를 별도로 기록했다. 최초 79개 회귀와 35개 delivery 검사는 통과했다. 중복된 부분 source observer를 기존 snapshot으로 통일한 최종 코드에서도 79개 회귀, 최종 package/docs 4개, resource drift, distribution, diff 형식 검사가 통과했다. 변경이 현재성 관측 capability에 한정돼 Full은 반복하지 않았다. 최종 고정 패키지와 통합 식별자는 `delivery.json`에 보존한다.

커밋 재사용 후보는 별도 `git-sensitive-case/`에서 확인했다. 동일한 파일 bytes·명령·기대 리비전을 유지한 채 빈 커밋만 만들었을 때 실제 검사는 exit 0→1로 바뀌었다 (`git-sensitive-summary.json`, 두 capture). pstack shipping도 단순 SHA 무시가 아니라 patch/build 비교와 변경된 조건 재검증을 요구한다. 우리 runtime의 임의 명령에 파일 hash만으로 자동 재사용을 허용하지 않기로 했다. 안전한 제거 후보를 찾지 못했으므로 필수/오래된 근거 차단 검사는 삭제하지 않았다. 대신 빠진 확인을 유발한 부분 source 조회 구현을 제거하고 기존 `_git_snapshot`을 공유했다.

## 잔여와 재개 조건

- **다음 실제 연결 변경:** 기존 full-stack fixture와 별도로 실제 제품의 FE→API→Domain→저장→새 조회 및 우회/정상 경로를 확인한다. 이번 실제 제품 소비는 Domain/native이며 브라우저·서버 API는 이번에 검증하지 않았다.
- **다음 관련 UI/검증 업무:** guide/token/component/실행 명령을 스스로 발견해 사용하는 새 문맥 소비를 확인한다. 이번에는 Agent 발견을 시험하지 않았으므로 무도움 성공률이나 개입 감소를 주장하지 않는다.
- **검사 비용 감소:** Git와 실행 조건에 무관한 재사용 범위를 실제 runner에서 입증할 때만 추가한다. pstack 전면 이식이나 고정 다중 모델 절차는 현재 결정을 바꾸지 않아 수행하지 않는다.
- **Native host:** Codex·Claude Code가 실제 제품 사용 환경이다. 격리 설치/세션 로딩·Skill 발견/호출·hook 전달은 보호 host driver 없이도 각각 확인한다. 전역 설치와 hook 신뢰 변경은 별도 권한 경계이며, 보호 수락을 일반 사용 검증의 선행 조건으로 두지 않는다. 후속 현행 근거는 [native 사용 검증](native-plugin-use-results.md)에 있다.
- **벤치마크:** 이번 채택 판단에는 공개 CLI 반례와 실제 제품 결함 검출이 충분했다. 유료 모델 호출·SWE-bench·FeatureBench를 실행하지 않았고 pstack 대비 성공률·시간·비용은 미측정이다.
