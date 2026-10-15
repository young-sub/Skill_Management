# Agentic Coding Harness 벤치마크 검토와 다음 고도화 계획

검토일: 2026-10-15. 저장소 기준: clean local `main@fc04f7099ac8ce427892765cfd8d1406fdbd9ab7`, runtime **0.1.61**. 다음 세션은 실제 branch·HEAD·dirty baseline·worktree를 다시 확인한다.

이 문서는 사용자 제공 리서치, 이번 대화에서 확인한 공개 문서·평가 코드, 현재 플러그인 코드와 읽기 전용 환경 조사에 근거한다. **벤치마크 설치·oracle 실행·모델 평가와 아래 runtime 수정은 아직 수행하지 않았다.** 외부 자료는 당시 main/웹 문서의 관찰이며 commit을 고정한 실행 증거가 아니다. 실행 전 데이터 revision·평가기 commit·이미지 digest를 고정한다. 현재 구현과 과거 인수는 [방향 문서](agent-coding-system-direction.md#design-review-2026-10-15)와 [0.1.61 결과](agent-workflow-implementation-results.md#delegated-handoff-2026-10-15)를 따른다.

## 결정

순서는 **코드 수정 → 회귀·실제 소비 → 고정 패키지 → 벤치마크 평가**다. 공개 과제의 해결률과 플러그인 고유의 후속 인수·복구·가이드 재사용을 함께 평가한다. 모델 성능, 플러그인 효과, native host 지원, 사업 가치는 별도 주장이다.

기존 검사 ID/결과 경로 이관, unknown launch의 BLOCKED 표시, 요청/영향/프로젝트/미결정 범위 분류는 다시 구현하지 않는다. 제품에 남은 의미 검토·미검증 화면은 플러그인 기능 부재로 치환하지 않는다.

## 공개 벤치마크 검토

| 대상·직접 확인한 출처 | 확인 내용 | 채택 판단 |
| --- | --- | --- |
| [Harness Bench](https://github.com/Qihoo360/harness-bench) | 현재 안내는 300개 작업이며 Software Engineering 81개·Web Development 27개를 포함. 기본 general 274개와 multimodal 26개의 실행 경로가 구분됨 | 독립 평가·실패 분모·업무 단위 부분 점수·trace 방법론은 즉시 참고. 전체 실행은 후순위 |
| [SWE-bench Multimodal v2](https://www.swebench.com/multimodal) | 2026-09-01 공개 v2는 재현성을 기준으로 480개 과제를 유지하고 Docker·브라우저·JS grading을 보완 | 기존 FE 버그 수정의 첫 평가 후보. 통과를 디자인 품질·사용자 UI 승인으로 확대하지 않음 |
| [FeatureBench](https://github.com/LiberCoders/FeatureBench) | Fast는 GPU 불필요 100개. README는 데이터 v1.1과 Codex 등 실행 연결을 안내. 정답 패치 평가 경로 제공 | 기존 프로젝트 기능 구현 후보. gold patch의 평가 시간은 Agent 구현 시간이나 현재 PC 실행 시간과 다름 |
| [ABC-Bench](https://github.com/OpenMOSS/ABC-Bench) | 224개 과제·127개 저장소·92개 환경 구성 과제. 외부 HTTP 검증. 공개 실행 예시는 `terminal-bench` CLI와 Hugging Face 데이터 사용 | BE 구현·환경 준비·서비스 실행 평가 후보. HTTP 통과만으로 UI부터 저장까지의 full-stack 연결을 주장하지 않음 |
| [Multi-SWE-bench](https://github.com/multi-swe-bench/multi-swe-bench) | 7개 언어 1,632개 과제와 Flash 300개, Docker 기반 외부 패치 평가를 안내 | 초기 연결이 안정된 뒤 JS/TS 저장소 다양성을 늘릴 때 추가 |
| [ts-bench v2](https://github.com/laiso/ts-bench/blob/main/articles/ts-bench-v2-coding-agent-benchmark.md) | 공개 SWE-Lancer 198개 풀에서 시작한 5개 기본 과제, Expensify 기반 Docker·공식 평가기 연결. README의 기본 dataset은 v1이므로 v2를 명시해야 함 | 실제 CLI 연결 비용이 유리하면 FE 일부 대체 후보. 5개 결과를 일반 성능 순위로 해석하지 않음 |
| [Terminal-Bench](https://github.com/harbor-framework/terminal-bench) | 현재 README는 Harbor와 버전별 dataset을 안내하며 실행 환경에서 oracle 반복 검증을 요구 | 복합 도구·환경 복구 평가의 후속 후보. ABC의 기존 실행 경로와 동일하다고 가정하지 않음 |

SWE-bench Verified/Live/Pro와 두 Vibe Coding 벤치마크는 제공 자료의 추가 후보로 보존한다. 이번에는 해당 항목의 규모·공개 실행 범위·신뢰성 주장을 독립 확인하지 않았으므로 주력 선정 근거로 사용하지 않는다. 모든 벤치마크를 연결하는 통합 프레임워크를 먼저 만들지 않는다.

### 실제 평가 코드에서 확인한 주의점

- [FeatureBench Codex adapter](https://github.com/LiberCoders/FeatureBench/blob/main/featurebench/infer/agents/codex.py)는 버전 미지정 시 `latest`를 사용하고 컨테이너 내 실행에 `danger-full-access`를 설정한다. 모델 이름만 맞춰서는 조건이 고정되지 않는다. CLI 버전·실제 권한·컨테이너 경계를 기록하고 실행 설정을 검토한다. 이 코드를 현재 호스트에서 실행하지 않았다.
- [Harness Bench 평가 규칙](https://github.com/Qihoo360/harness-bench/blob/main/docs/EVALUATION_AND_SCORING.md)은 의미 있는 업무 결과를 묶어 채점하고 timeout·model/protocol 실패도 분모에 남긴다. 단순 assertion 수로 부분 점수를 부풀리거나 성공 실행만 평균내지 않는다.
- [평가기 계약](https://github.com/Qihoo360/harness-bench/blob/main/docs/TASK_AUTHORING_AND_ACCEPTANCE.md)은 숨겨진 evaluator와 정답을 Agent에서 분리하고, 후보가 작성한 검증 파일을 정답으로 삼지 않는다. 우리 플러그인의 PASS와 외부 판정을 대조할 때 적용한다.
- [Provider trace](https://github.com/Qihoo360/harness-bench/blob/main/docs/PROVIDER_TRACE.md)는 provider usage와 수집 완전성을 구분한다. 우리도 누락된 사용량을 0으로 계산하지 않고 reasoning token 등을 중복 합산하지 않는다. 새 proxy는 기존 trace로 부족함이 입증될 때만 검토한다.

## 현재 환경에서 확인한 사실과 개선 책임

Windows 호스트라는 사실과 대상 컨테이너 OS는 별개다. [Docker Desktop의 Windows 지원](https://docs.docker.com/desktop/setup/install/windows-install/)에는 Linux 컨테이너 실행 경로가 있다. endpoint 선택은 [Docker context](https://docs.docker.com/engine/manage-resources/contexts/)와 override를 확인해야 한다.

이번 대화의 읽기 전용 관찰:

- `docker context show`, `docker context ls`, `docker context inspect desktop-linux`: 활성 context는 `desktop-linux`, endpoint는 `npipe:////./pipe/dockerDesktopLinuxEngine`이었다. 조사자가 Linux 호스트라고 가정해 새로 선택한 경로가 아니다.
- `DOCKER_HOST`와 `DOCKER_CONTEXT` override는 모두 없었다.
- `docker version --format '{{json .}}'`: Windows client 28.1.1, Server null, 선택된 엔진 파이프 부재. 기본 sandbox와 권한 상승에서 같은 실패였다.
- `docker --context default version --format '{{json .}}'`: `docker_engine` 파이프도 없었다. 일반적인 관리자 권한 안내가 함께 출력됐지만 권한 상승에서도 파이프 부재는 같았다.
- `Get-Process -Name 'Docker Desktop','com.docker.backend','dockerd'`: 기본·권한 상승 조회에서 해당 프로세스가 나타나지 않았다.

확인된 상태는 **현재 엔진 endpoint를 사용할 수 없음**이다. Desktop 미기동은 유력한 설명이나 WSL/backend 고장까지 확정하지 않았다. 설치·context 변경·서비스 기동·전역 설정 변경은 수행하지 않았다. 다음 세션은 이 관찰을 현재 상태로 가정하지 말고 필요한 capability만 다시 확인한다.

앞선 설명의 부족한 점은 host/context/backend를 먼저 설명하지 않고 엔진 가동 필요로 요약한 것이다. 플러그인은 이런 실패를 단순 BLOCKED 문구로 끝내지 않고 **관찰 → 근거 있는 분류 → 실제 시도 → 재검사 → 후속 재사용**으로 연결해야 한다.

| 소유 위치 | 현재 확인한 공백·다음 변경 |
| --- | --- |
| `scripts/run_check.py` | Windows timeout cleanup의 `taskkill` exit만 남기고 stdout/stderr를 버림. 기존 capture에 cleanup 명령·출력·결과를 추가하여 본 검사 실패와 정리 실패를 구분 |
| `authoring/scripts/core_harness.py`의 capability descriptor/환경 예외 경로 | 기존 `run_dynamic_baseline`, `load_environment_exceptions`를 우선 재사용. 명령 부재·endpoint 부재·접근 거부·요구 OS/architecture 불일치·원인 불명을 근거와 함께 표현. Harness 미사용 프로젝트에 계약 설치를 강제하지 않음 |
| `authoring/scripts/project_workflow.py`와 기존 feedback/실행 근거 | `environment_limit`은 현재 OPEN으로 남고 `environment_resume_required`를 표시함. 실패 이력은 보존하면서 실제 복구 실행과 현재 차단 상태를 연결하는 최소 확장을 검토. 녹색 파일이나 동의만으로 해결 처리하지 않음 |
| 공통 Skill/참조 문서와 프로젝트 guide | 공통은 발견·진단·재시도·재검증 원칙, 프로젝트는 실제 도구별 명령·기대 결과·fallback을 소유. CLI가 미등록 복구 명령을 추측하지 않음 |

오류 문구 하나로 원인을 확정하거나 자동 승격하지 않는다. 권한 상승은 원인과 권한 범위가 맞는 명령에만 적용한다. 환경 변경 뒤에는 현재성을 다시 확인하고, 수동 비활성화는 자동 해제하지 않는다. `lookup/resume`은 raw를 읽을 뿐 진단·복구 명령을 실행하지 않는다. 환경 실패 기록의 복구가 제품 인수 PASS를 뜻하지도 않는다.

## 다음 세션의 작업 목록 — 순서 고정

| 순서 | 고도화 항목 | 종료 조건 |
| --- | --- | --- |
| 1 | **summary 축소** | 현재 요청의 인수 가능 범위·차단 이유·다음 행동을 우선 표시. 프로젝트 잔여·미결정·분모·생략 수·상세/raw 연결 보존 |
| 2 | **조회 비용 감소** | 같은 호출 내부의 중복 inspect/파일 읽기만 공유. full 결과 동등성·다음 호출 변경 감지·조회 무변경을 유지하고 반복 시간/편차로 효과 확인 |
| 3 | **환경 진단·복구 연결** | cleanup raw 보강, 실제 대상/요구 환경 확인, 원인·시도·복구 근거·현재 차단·다음 행동 연결. 기존 예외/feedback/capability 경로 재사용 |
| 4 | **후속 Agent 재사용 검증** | 새 문맥에서 환경 재실수 방지, 정확한 인수·중복 효과 방지, 변경된 스타일 기준·가드레일의 다른 업무 재사용 확인. 도움과 합성/실제 사례 구분 |
| 5 | **고정 패키지와 벤치마크 연결** | source/회귀/실제 소비 후 패키지 고정. 공식 평가기를 호출하는 얇은 연결로 task·모델·환경·patch·trace·외부 판정 기록. 정답/실패 대조 선행 |
| 6 | **소규모 A/B 평가** | 고정 OFF/ON과 필요한 이전판/수정판 비교. 해결률·거짓 완료·회귀·비용·인수 정확성 보고 후 미사용 과제로 확인 |

비자명한 수정은 focused RED → 최소 owner 수정 → GREEN → 정상/영향 회귀 → 실제 소비 순서다. 외부 TEMP worktree, state별 writer 하나, 필요한 독립 반례 검토를 사용한다. source·테스트·문서·생성 리소스를 함께 검증하고 고정 패키지 소비 후 로컬 main에 통합한다. 제품 후보·credentials·과거 raw를 보존한다.

환경 회귀에는 Windows/Linux-container 정상 조합, endpoint 부재와 실제 접근 거부의 구분, 복구된 환경의 옛 실패, context 변경 뒤 옛 성공, 수동 비활성화, cleanup 실패·중복 효과를 포함한다. 합성 재현은 실제 host 복구 성공으로 보고하지 않는다.

## 벤치마크 실행 계획

초기 탐색 평가 제안은 공개 과제 **8개**(Multimodal 3, FeatureBench Fast 3, ABC 2)와 연속 과제 **4개**다. 실행 가능한 task ID는 환경/평가기 확인 뒤 결과를 보기 전에 고정한다. 다음 네 연속 과제는 플러그인에 필요한 능력을 평가한다.

1. 여러 상태의 작업 인수: 현재 PASS와 의미 검토 잔여, STALE, BLOCKED, NOT_RUN, 프로젝트 잔여를 정확히 설명.
2. 일부 효과 수행 후 중단·재개: 새 Agent가 상태를 인수하고 외부 효과를 중복 실행하지 않음.
3. 공유 스타일 기준 변경 후 다른 업무: 새 guide/token/component 발견·적용과 이전 판단의 현재성 확인.
4. 실제 full-stack 피드백과 예방: 같은 ID/값의 UI→API→Domain→저장→새 조회, 원래 실패·정상·관련 우회, 다른 업무의 예방 재사용.

각 조건 3회면 12×2×3 = **72개 실행 단위**다. 연속 과제의 모든 turn·후속 Agent 비용을 포함하며, 72개를 서로 독립인 과제 수로 취급하지 않는다. 표본 수는 탐색 목적 제안이지 통계적 충분성 보증이 아니다. 처음부터 50×2×3 = 300회 실행하지 않는다. 소수 oracle 검증과 실행량 측정 뒤 필요한 모델 비용·총상한을 산출하고 기존 비용 권한을 확인한다.

### 공정한 비교와 평가기 검증

- 고정: task/data/evaluator revision, repository base, 이미지·dependency, 모델·추론 강도·CLI, 시간/토큰 예산, 도구·권한·네트워크, 초기 guide/근거. warm/cold 조건·실행 순서를 통제하고 순서를 교차한다.
- OFF/ON은 같은 자연어 요청과 원본 근거를 받는다. 이전 세션·전역 Skill·상대 조건의 산출물이 유입되지 않도록 분리. 연결/setup 비용과 제공한 도움을 기록한다.
- ON은 실제 플러그인 발견·Skill 사용·필요 hook 전달을 관찰한다. 단순 파일 복사나 설치 목록을 전체 활성화 증거로 쓰지 않는다. 활성화 실패를 숨기거나 실행 분모에서 임의 제거하지 않는다.
- 정답 패치·숨겨진 테스트는 Agent가 접근할 수 없는 평가 환경에 둔다. read-only mount도 읽기는 가능하므로 숨김의 대체가 아니다. Agent 종료 뒤 공식 평가기를 독립 실행한다.
- 정답/수정 없음/관련 결함이 남은 대조로 평가기 민감도를 확인하고 flaky와 환경 실패를 사전 기록한다. 평가기가 기대하지 않는 임의 테스트 완화로 통과시키지 않는다.
- timeout·모델·플러그인 실행 실패도 남긴다. genuine infrastructure failure는 별도 분류·동일 조건 재시도하며 원래 기록과 전체 시도 수를 보존한다. 가장 좋은 재시도만 `Resolved@1`로 선택하지 않는다.
- 개선에 사용한 과제는 개발셋이다. 미사용 task와 가능한 다른 저장소를 확인셋으로 남긴다. 공개 과제의 모델 학습 오염 가능성도 일반화 주장에 반영한다.

### 지표와 개선 판정

| 우선 | 지표 |
| --- | --- |
| 1 | 독립 평가기 해결률·회귀, 완료 선언과 외부 실패가 어긋난 비율, 요구된 실제 flow 충족 |
| 1 | 후속 인수의 상태/범위/다음 행동 정확성, 중복 효과, 환경 원인 오분류·같은 실패의 무의미한 반복 |
| 2 | 실패 포함 전체 비용/시간, 총비용 ÷ 성공 수, 입력·출력·캐시 토큰과 수집 누락, 사용자 개입 |
| 2 | summary 크기·조회 시간·중복 검사 수, 변경된 guide/guardrail의 실제 후속 재사용 |

서로 다른 벤치마크의 부분 점수를 하나로 합산하지 않는다. 작업별 대응 차이와 신뢰구간을 보고하고 반복·같은 저장소의 상관을 고려한다. 작은 표본의 시간 꼬리값이나 몇 건의 무실패로 일반 신뢰성을 주장하지 않는다. 구조/업무 의미는 고정 rubric의 독립 검토로 보완하되 테스트 정답을 대체하지 않는다. 품질·비용·사용자 개입 중 무엇이 개선됐는지 따로 결론 낸다.

## 미수행과 권한 경계

이번 문서화는 공개 자료·코드 검토와 이미 수행한 환경 조회의 보존이다. 구현·벤치마크·Docker 복구가 완료된 것은 아니다. 현재 0.1.61의 짧은 summary/조회 비용/환경 복구 연결은 다음 수정 범위다. native 모델 Skill 호출·실제 hook callback·보호 host 인수, 사업 가치·장기 무인 운영은 별도 미수행이다.

두 55-case 검사는 소비자/fixture 계약이 달라 유지한다. 실제 공동 선택·중복 실행과 결함 검출/정상 허용·반복 비용을 조사한 뒤에만 통합한다. 새 dashboard·DB·scheduler·범용 정답 판정기를 추가하지 않는다.

설치된 Skill/Plugin·전역 설정·provider 변경, 원격 push·배포·외부 비용·제품 main 병합은 기존 권한 경계를 유지한다. 필요한 외부 조건만 구체화하고 독립적인 코드 수리는 계속한다. 문서 변경의 Feature는 documentation이며 공개 runtime 기능 계약이 바뀌지 않아 feature-map 기능 행은 유지한다.
