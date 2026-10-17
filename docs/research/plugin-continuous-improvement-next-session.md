# 현재 플러그인 개선 실행 지시서

## 2026-10-17 후속 구현 범위와 진행 계획

출발점은 재확인한 clean `main@0d546c8`, 테스트 설치 0.1.73이다. 이번 실행은 Claude Code 검증을 사용자 결정으로 제외하며 지원 코드는 유지한다. 기존 인증 home, 신뢰 설정, candidate-marketplace, 격리 제품의 미커밋 변경과 raw evidence를 보존한다.

하나의 계획으로 추적한 결과: (1) 최소 재현은 완료했으나 native Node pipe EPERM으로 전체 실행은 미완료, (2) 공개 feedback/task 결합·오래된 근거 재개방·새 Codex 요청의 계승·무실행 조회는 확인, (3) focus 관찰기 교정과 UTF-8 파일 stdin 전달은 실제 사용에서 한정된 예방 확인, (4) 시작 메뉴 내레이터로 두 오류 음성·키보드 복구를 사용자 확인, (5) 격리 Labeler 동시 수정 손실을 수리하고 화면→API→Domain→D1→새 조회 확인, (6) 공유 캡처의 label-only 재실행 요구를 제거하고 실패·도움·정상 허용을 평가했다. 0.1.75를 테스트 지역에만 설치해 새 native 요청이 소비한 bytes를 고정한다. 세부 직접 근거·한계는 결과 문서 한 곳에서 유지한다. 별도 장부·dashboard·범용 실행기는 만들지 않는다.

구현 branch는 `wp-20261017-native-followthrough`이며 검증된 변경은 로컬 main에 통합한다. 새 worktree는 만들지 않았다. 이번 raw는 기존 지속 폴더의 `followthrough/` 하위에 보존한다. 최신 결과와 사용자 음성 확인의 task 연결은 [native 결과](native-plugin-use-results.md)에 반영한다.

최신 재개 기준은 [0.1.75 후속 구현 결과](native-plugin-use-results.md#followthrough-implementation--0175)다. 동일 테스트 home의 로그인·hook 전달과 자연어 요청의 가이드 발견·후속 재사용은 관찰했다. 다시 설치하거나 로그인하지 않는다. native sandbox의 subprocess `EPERM`과 부모 호스트 개입을 무도움 완료로 바꾸지 않는다. 사용자는 한 프로세스의 elevated 비교만 승인했으며 계정/ACL/setup 변경은 승인하지 않았다. 최초 비교 CLI는 permission profile 인자가 없어 실행 전 실패했고, 이후 기존 preflight에서 같은 home의 setup marker와 sandbox user 파일 부재를 확인했다. 적합한 profile과 기존 준비된 권한 경계가 확인되거나 필요한 설정 변경을 구체화해 별도 승인받아야 다음 비교가 가능하다. native 전체 완료는 그 뒤 동일 runner의 테스트·브라우저·빌드·정리까지 실제 수행한 경우에만 판단한다. 0.1.73 조회 축소 및 이번 0.1.75 근거 재사용 수리는 새 반례 없이 재구현하지 않는다.

[현재 설계](agent-coding-system-direction.md)의 여섯 목표를 하나의 업무 흐름으로 구현·검증한다. 계획·문서·스키마·테스트에서 끝내지 않는다. 이 문서는 과거 작업을 다시 실행하는 목록이 아니다.

1. 실제 branch/commit/dirty/worktree, AGENTS, docs/index, project.yaml, 환경 예외, resource-map을 확인한다. `ea7e11d / 0.1.68`은 과거 출발점이며 현재 사실로 가정하지 않는다.
2. [후속 실제 소비](workflow-followup-results.md), [0.1.69 개선 결과](workflow-improvement-results.md), [hardening 결과](core-hardening-results.md)와 코드를 대조한다. TaskStore/공개 API/필수 검사/캡처/절대 state/읽기 전용 조회, 범위별 완료·구조 예방·UI 발견의 해결된 부분을 재구현하지 않는다. [이전 기록](agent-workflow-implementation-results.md)과 `.work` raw는 과거 근거로 보존한다.
3. 한 계획에서 여섯 목표의 구현·검증·잔여를 추적한다. 옛 지시와 중복 기준은 고유 결정·참조를 통합하고 기록은 [아카이브](archive/index.md)로 연결한다. 사용자 기록과 raw를 삭제하지 않는다.
4. 작은 업무 → 원인 소유자 수리/예방 → 후속 기준 발견·재사용을 실제 실행한다. 무관한 전체 지도/여섯 셀/등록 검사 형식이 막으면 기존 책임 경계에서 고친다. 실제 결함·우회 차단과 정상 허용 근거는 유지한다.
5. 코드 수정 → 집중 회귀 → 격리 소비 → 고정 패키지 순서로 진행한다. canonical 변경 후 생성 리소스를 갱신하고 [필수 검사](../testing.md)를 수행한다. Full·새 문맥·벤치마크는 필요한 불확실성을 해결할 때만 사용한다.
6. 검증 가이드를 실제 실행하고 소유 자원 정리 후 근거 보존을 확인한다. 실패·도움·미실행·비용 unknown을 보존한다. 과거 PASS와 이번 결과, fixture/package/product/native-host를 구분한다.
7. 승인 범위에서 기능 단위 커밋, main/사용자 상태 재확인, 로컬 통합을 진행한다. 이번 worktree만 증거 보존 후 정리한다. 이 문서는 push/publish/deploy/유료 실행/설치·전역·신뢰 설정 변경을 승인하지 않는다.

보고할 내용: 실제 개선 업무와 줄인 절차, 여섯 목표의 되는 것/미확인, 실제 실행과 한계, branch/commit/main/package/evidence, 미완료의 재개 조건. 개별 수리를 전체 완성으로 부르지 않는다. 미래 작업은 최신 결과에 남은 실제 재현과 미확인에서 선택한다.

Native 재개는 [현재 호스트 사용 결과](native-plugin-use-results.md)를 먼저 읽는다. Codex·Claude Code는 제품 사용 환경이므로 발견·호출·hook 전달을 실제 호스트에서 확인한다. 보호 driver 준비를 선행 조건으로 요구하지 않는다. 이미 확인한 발견·패키지 호환성을 반복 구현하지 말고, 현재 세션 설치 상태와 모델의 실제 업무 소비 등 남은 경계를 구분한다. 기존 전역 설치/신뢰 설정 변경과 유료 외부 호출은 여전히 별도 승인 범위다.

격리 직원 화면 요청 `26d47b77-8b91-44bd-b966-554809d3b85d`는 0.1.70 후속 실행 당시 현재 요청 action 0 / `READY_FOR_REVIEW`를 확인했다. 프로젝트 전체 잔여를 이 요청의 미완료로 다시 지시하지 않는다. 이후 변경으로 근거가 오래됐다면 해당 변경의 새 task에서 판단한다. 재개 대상과 경계는 [후속 실제 소비의 현재 결과](workflow-followup-results.md)를 먼저 확인한다. 기존 Full·전체 제품 검사를 자동 반복하거나 이 문서만으로 설치·유료 실행을 시작하지 않는다. 이미 해결된 과잉 차단·구조 예방·구조 예방 근거의 같은 bytes 커밋 재사용은 새 재현이 있을 때만 다시 연다. Native 실행의 source revision/diff 변경은 여전히 STALE로 보수 판정한다. 이 경계를 구조 예방 재사용과 혼동하지 않는다.

다음 선택은 [pstack 실전 비교](pstack-practical-comparison.md)의 잔여를 따른다. direct plan의 미추적 source 변경 누락은 0.1.71에서 수리했으므로 새 반례 없이 반복 구현하지 않는다. 같은 bytes 커밋 재사용은 Git 의존 명령의 반례를 먼저 고려한다. 다음 실제 관련 요청에서 UI/검증 기준의 무도움 발견·소비 또는 실제 FE/API/Domain 연결 변경을 검증하되, 요청 없는 제품 기능이나 벤치마크를 새로 만들지 않는다.
