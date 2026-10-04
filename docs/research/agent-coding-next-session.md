# 다음 세션: 최신 배포본 정리와 검증 도구 이식

아래 프롬프트는 사용자가 요청한 후속 구현용이다. [수정 방향과 전체 요구사항](agent-coding-system-direction.md)을 실행 범위와 완료 기준으로 압축했다. 구현 후에는 실제 채택·제외 결과에 맞춰 갱신하거나 역할이 끝난 부분을 제거한다. 일반 작업의 필수 절차로 사용하지 않는다.

## 복사해서 사용할 프롬프트

```text
저장소: C:\Users\YS\Desktop\python\Skill_Management

이전 검토를 반복하는 데 그치지 말고, 최신 배포본을 기준으로 정리한 뒤 필요한 도구 개선을 선별 이식해 검증하고 기능 단위로 커밋해줘. 목적은 스킬 간 라우팅에 의존하지 않고 프로젝트 검증 명령을 직접 실행할 수 있게 하여, 이후 플러그인으로 묶을 수 있는 토대를 만드는 것이다.

먼저 AGENTS.md, docs/index.md, .harness/project.yaml 및 다음 두 문서를 읽어라.
- docs/research/agent-coding-system-direction.md: 합의한 방향, 배포본 비교, Feature Map·UI·검증·유지보수·플러그인 요구사항
- docs/research/pstack-analysis.md: 고정된 upstream 소스의 연구 근거. 그대로 복제하는 설계가 아니다.

1. 최신 기준과 현재 작업 위치부터 확인해라.

- 준비된 branch는 wp-20261004-agent-coding-foundation이다. 문서화 시작 base는 e19134358141f901bb22c4af1aea17d7a9e2898c였다. 이는 2026-10-04에 fetch한 origin/main이며 2026-09-22 배포 계열이다.
- 이전 후보 branch wp-20260906-agent-guidance의 b40396a63b1031b8a3958d376fb3cc46499a9191은 이식 근거일 뿐 새 작업의 base가 아니다. 과거 A/B의 f4eca33 또는 54ff6be로 돌아가지 마라.
- git status, branch/HEAD, worktree list, origin URL을 확인하고 git fetch origin main으로 실제 최신 SHA를 확인해라. 기록된 SHA를 오늘도 최신이라고 가정하지 마라.
- fetch가 실패하면 최신 상태라고 선언하거나 확인되지 않은 base로 전환하지 마라. 기존 checkout과 변경을 보존하고 원인·마지막 확인 base를 구분해라. 최신 확인에 의존하지 않는 읽기·검토는 계속할 수 있다.
- 현재 branch가 최신 origin/main 위의 문서 준비본이면 그대로 진행한다. 원격이 이동했고 현재 branch에 이 문서 준비본만 있다면 실제 최신에서 새 작업 branch를 만든 뒤 문서화 commit만 옮겨라. 문서화 commit은 git log -- docs/research/agent-coding-system-direction.md로 식별하고 diff로 문서 범위인지 확인해라. dirty 파일·추가 commit·코드와 문서가 섞인 commit이 있다면 먼저 변경 소유권과 옮길 범위를 정하고, 기존 branch를 보존한 채 통합해라. 임의 reset·stash 삭제·혼합 commit의 일괄 이식은 하지 마라.
- 현재 폴더는 다른 linked worktree가 참조하는 공통 .git을 가진 주 작업 폴더다. 폴더/.git을 삭제하거나 다른 runner worktree의 main을 reset하지 마라. 이미 이전 후보 checkout을 버리고 최신 기반으로 전환했으므로 별도 worktree 생성은 실제 독립 작업이 필요할 때만 해라.
- source는 추적 파일과 지정 commit을 기준으로 다뤄라. 이전 .work, ignored fixture/cache, 설치본을 최신 source로 복사하지 마라. 남아 있는 작업 자료는 소유권과 보존 정책을 확인하기 전에는 삭제하지 마라.

2. 짧은 실행 계획을 세우고 배포본부터 정리해라.

- 현재 공개 catalog와 source/generated mapping을 확인해라. 이미 배포된 result/delta 방어, Harness cohort 범위, 불필요한 계약 유도 완화, CI·POSIX path·텍스트 hash 수정과 hwp-form-fill은 보존해라.
- 사용자가 의도적으로 제거했던 write-a-skill은 후보 commit 90437c6을 참고해 최신 catalog/manifest/inventory/test에 맞춰 좁게 다시 제거해라. 이미 제거됐다면 반복하지 말고, 이후 사용자가 변경한 의도가 있으면 그 최신 지시를 우선해라. 예전 catalog 전체를 가져오거나 HWP를 제거하지 마라. 전역 설치본 삭제와 repository 배포 목록 정리는 별개다.
- 새로운 다단계 router나 다섯 개 신규 skill의 일괄 도입부터 시작하지 마라. 작은 작업은 구현·검증까지 현재 Agent가 직접 진행하는 경로를 유지해라.
- authoring/resource-map.json에서 mapped source를 확인하고 canonical source만 수정한 뒤 생성해라. 독립 skill은 그 자체 source 경로를 사용해라. 후보 generated core나 manifest를 통째로 덮어쓰지 마라.

3. 후보 도구를 실제 필요와 검증 가능한 효과로 선별 이식해라.

후보 commit b40396a에서 git show 또는 범위 diff로 읽을 수 있다. branch 전체 merge나 일괄 cherry-pick을 하지 마라.

A. 실행 증거 캡처
- 원본: skills/setup-project-verification/scripts/run_check.py, tests/distribution/test_check_capture.py
- 필요한 효과: 첫 출력 경로 생성, argv/cwd/head/변경 상태·stdout/stderr·native exit·timeout 기록, 이전 evidence 덮어쓰기 방지, command 실패 전달.
- helper의 소유 위치는 현재 consumer 기준으로 가장 단순하게 정해라. setup-project-verification skill을 다시 만들어야 helper를 쓸 수 있는 구조는 피한다. 공통 배포가 필요해지면 기존 authoring/generated 방식으로 한 원본을 유지한다.
- 실제 native 정상/실패 command와 새 evidence 경로를 실행해라. exit 0을 제품 PASS로 바꾸지 말고 behavior 판정은 별도로 둬라. untracked 내용·fixture·dependency·server identity의 보증 한계를 유지해라.
- 판정은 실행기가 생성한 특정 기록을 참조하게 해라. 기존 run ID나 고유 output 경로를 재사용하고, 그 기록의 check/Feature·argv/cwd·관련 코드 상태·execution/exit와 판정의 연결을 consumer에서 확인해라. 연결되지 않은 성공, 다른 대상, 무효화된 오래된 결과는 PASS로 수용하지 않는 경로를 검증해라. 새 증거 DB나 모든 runner용 parser는 만들지 마라.
- stdout/stderr에 비밀을 기록하거나 장기 background server를 이 helper로 띄우지 마라. timeout 정리가 무엇을 실제로 종료했는지 구분해라.

B. Windows Impeccable launcher
- 원본: 9d2139f의 skills/impeccable/scripts/impeccable, impeccable.cmd, tests/distribution/test_impeccable_launcher.py
- 필요한 효과: 전송 fallback, 보이는 실패, hash 불일치 시 실행 거부, 공유 version cache 재사용.
- 최신 launcher와 먼저 비교하고 아직 필요한 부분만 이식해라. loopback fixture와 임시 cache에서 실제 경로를 검증해라. 일반 사용자 cache를 지우거나 mock 결과를 live release 다운로드 성공으로 보고하지 마라.

C. Agent 평가 실행기
- 원본: b40396a의 tests/behavior/run_agent_eval.py, tests/distribution/test_eval_process_cleanup.py
- 세션 소유 process cleanup, timeout, 실제 file-change 계수는 재사용 후보다. 이번 작업에서 소비자가 생기는 부분만 이식하고 불필요한 평가 framework는 도입하지 마라.
- 모델 없는 실제 process 검사와 Agent 품질 평가는 구분해라. 과거 Windows CLI 0.160.0의 split filesystem read 격리 실패는 해결됐다고 가정하지 마라.
- 28개 과업 0개 시작 기록은 판단 불가였다. 전체 품질 batch부터 재시작하지 마라. 별도 모델 평가가 실제 필요한 경우 권한·비용 범위와 현재 환경 지원을 먼저 확인하고, 지원 실패를 권한 완화로 우회하지 마라.

각 후보는 채택/보류/불필요와 이유를 간단히 남겨라. 실제 결함과 consumer가 없는 도구까지 모두 옮기는 것이 목표는 아니다.

4. Feature Map에서 직접 실행까지 최소 한 경로를 연결해라.

- Feature Map은 코드 목록이 아니라 사용자 기능의 지도다. ID·이름, 사용자 행동, 기대 결과, business invariant, 관련 FE/BE/Domain, 데이터 side effect, 실제 검증 방법을 연결해라.
- 이 저장소의 실제 기능 중 설치·갱신, native 검증 결과 확인, 변경 보존·재개 등 소수만 시작해라. FE/BE가 없는 기능에 가짜 UI/API/DB를 추가하지 마라. 미적용 층은 이유와 함께 해당 없음으로 둔다.
- 이 단계의 evidence 범위는 repository/harness다. 파일시스템 side effect와 외부 제품 DB 검증을 구분해라. canonical 지도 위치를 기존 index/AGENTS에 연결하고, 기능 변경자가 항목을 갱신하며 결과에는 Feature ID 또는 기능 영향 없음의 이유를 남기게 해라. 소비하는 ID/명령의 누락과 문서의 깨진 링크는 기존 검사와 최소 adapter에서 확인해라.
- Markdown 한 곳과 기존 docs/testing.md·프로젝트 명령을 우선 써라. 실제 자동 소비자가 필요할 때만 작은 구조화 형식을 만들고 수동 이중 원본을 만들지 마라.
- verify-product는 먼저 직접 쓸 수 있는 검증 능력/명령이다. 기존 runner와 실행 캡처를 연결하되 다른 skill 호출 성공을 전제로 하지 마라. 이미 충분한 native 명령에 새로운 범용 wrapper를 씌울 필요는 없다.
- path mapping은 후보이며 최종 선택은 바뀐 로직·caller·계약·Feature로 판단한다. 영향 불명확을 PASS나 무조건 Full로 바꾸지 마라.
- 실제 한 흐름에서 기준 → 선택한 command → raw evidence → 판정을 확인해라. 관련 실패 대조도 확인해서 command 실패·미실행·오래된 결과가 성공으로 처리되지 않는지 보여줘라. 검사하지 않는 상태를 검사했다고 주장하지 마라.
- 결과는 PASS/ISSUES/BLOCKED와 남은 범위로 보고한다. skipped/not_run/not_required와 PASS를 분리한다. 현재 source, 임시 설치, 실제 동작, Agent 행동, 실환경 적용 증거를 섞지 마라.

5. 플러그인으로 묶을 경계를 준비해라.

- 프로젝트: Feature Map, 업무 정답, UI token/component/기준, 실제 검증 command/fixture.
- 공통 도구: 유한한 실행과 evidence 캡처, 필요한 config 검사.
- 선택적 Skill: 판단이 필요한 설정·유지보수 절차만.
- Plugin adapter: 패키징·버전·설치·선택적 hook. 기존 CLI는 독립 실행 가능해야 한다.
- 실제 consumer와 native 실행을 먼저 확보한다. 빈 manifest·MCP 서버·대시보드·라우터를 만들어두는 것으로 완료하지 마라. 현재 host 지원과 실제 사용 목적이 확인돼 작게 검증할 수 있을 때만 최소 local package까지 만들고, 그렇지 않으면 검증된 CLI와 패키징 경계를 완료 결과로 남겨라.
- OpenAI plugin/hook 문법은 현재 공식 문서와 실제 host/CLI에서 확인해라. plugin 설치가 hook trust나 항상 실행됨을 뜻하지 않는다. hook 오류/timeout·미지원 동작을 PASS로 취급하지 않고 직접 command/기존 CI 경로를 유지해라.
- standalone/plugin 중복 설치·버전 충돌과 generated ownership을 고려해라. 사용자의 일반 설치, 전역 설정, 외부 publish는 별도 범위다.
- UI는 다음 실제 제품 적용에서 기존 DESIGN/Impeccable/token/component를 재사용한다. 지금 이 저장소에 사용하지 않는 UI framework나 모든 프로젝트용 style 값부터 만들지 마라.

6. 검증과 전달

- 형식적인 문구·테스트 수·coverage 확대를 목표로 하지 마라. 테스트 정리 후보는 direction 문서에 있다. 삭제는 같은 의미 있는 실패 검출이 남는다는 근거가 있을 때만 한다.
- 이식한 도구의 실제 behavior·실패 경로를 검증하고, source/generated/catalog가 바뀌면 해당 배포·설치 검사를 수행해라. Full은 실제 cross-cutting 영향이나 명시 요청일 때 수행한다.
- repository 문서 링크, resource drift, distribution, git diff --check 등 변경된 표면의 기존 필수 검사를 적용해라. PowerShell의 후속 성공으로 앞의 native 실패를 가리지 마라.
- 반복 문제는 문서 경고 추가보다 type/lint/shared component/DB constraint/test/runtime check처럼 원인 위치에서 예방해라. source/shape 검사는 그 계약만 증명한다고 보고해라.
- 변경과 검증을 complete functional unit 단위로 커밋해라. 계획이나 테스트 추가만으로 종료하지 말고 실제 명령을 사용할 수 있게 끝내라. 미해결 환경 문제가 있으면 독립적으로 진행 가능한 부분은 완료하고 정확한 미검증 범위를 남겨라.
- docs/index.md와 관련 durable 문서를 실제 구현 상태로 갱신해라. 이 후속 prompt도 구현된 내용·보류한 내용이 오해되지 않게 정리해라. 임시 실행 로그는 기존 .work 보존 정책을 따른다.
- push/publish, protected main 통합, 일반 설치본·전역 설정 변경, 원격 자원/유료 provider 실행은 이번 로컬 구현 완료에 포함하지 않는다. 기존 명시 권한이 있는 경우에는 그 범위를 재요청하지 말고 적용한다.

최종 보고는 핵심만: 최신 base와 commit, 채택·제외한 도구, 직접 실행할 command, 실제 검증 결과와 남은 범위, 다음 plugin 연결에 필요한 최소 작업.
```

## 후속 세션이 지켜야 할 완료 경계

이번에 준비한 것은 최신 배포본을 기준으로 한 문서 branch다. 후속 세션은 문서에서 끝나지 않고 실제 필요한 도구의 소비 경로와 실패 검증까지 완료한다. 반대로 실제 제품 프로젝트 검증이나 전체 skill 품질 우월성·plugin 전역 적용을 아직 수행하지 않았다면 완료 범위에 넣지 않는다.

상세 원본 확인 예시는 `git show b40396a:skills/setup-project-verification/scripts/run_check.py`다. 로컬 donor commit이 사라진 환경에서는 추측해서 복원하지 말고 해당 근거가 없다는 점을 밝히고 현재 배포 코드에서 필요한 최소 수정부터 판단한다.
