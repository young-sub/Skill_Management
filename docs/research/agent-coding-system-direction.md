# Agent 위임 설계 기준

이 문서가 현재 설계의 단일 기준이다. 0.1.87까지의 기준·근거는 [이전 판](archive/agent-coding-system-direction-through-0.1.87.md)과
[아카이브](archive/index.md)에, 버전별 실행 기록은 [docs/index.md](../index.md)에 있다.

## 목적과 판정 기준

사용자가 FE·BE·업무 로직에 걸친 작업을 범위 안에서 더 많이 위임하고, 무엇이 어떻게 검증됐는지
분명히 확인하게 한다. 플러그인은 **켰을 때 결과가 측정 가능하게 좋아져야** 존재 이유가 있다.

판정은 `evals/delegation-v1/`의 고정 held-out 과제에서 플러그인 OFF와 비교한다
([testing](../testing.md#delegation-effect-evaluation)).

| 지표 | 의미 |
| --- | --- |
| 검증된 성공 | 숨긴 수락 테스트와 기존 회귀 검사가 모두 통과 |
| 거짓 완료 | 완료를 주장했지만 숨긴 테스트나 회귀가 실패 (중단·timeout 제외) |
| probe 검출률 | Agent가 남긴 테스트가 인공 결함을 잡는 비율 |
| 비용 | 토큰, 비용, 시간. 검증된 성공 1건당 토큰으로 비교 |

같은 조건 비교 없이 일반 개선을 주장하지 않는다. 0.1.61·0.1.62·0.1.78의 OFF/ON 비교는 해결률이
같고 토큰·시간만 늘었다([Luna](luna-benchmark-execution.md), [0.1.78](luna-0.1.78-benchmark-results.md)).

## 설계 원칙

1. **결과를 바꾸는 장치만 기본 경로에 둔다.** 모델이 이미 하는 일(읽기·수정·테스트)은 다시 지시하지
   않고, 기록에서 반복해 빠뜨린 행동만 다룬다.
2. **자산은 제품 저장소에 실행 가능한 형태로 남긴다.** 테스트, lint·아키텍처 규칙, Feature Map,
   UI token, probe 등록부는 다음 세션·다른 Agent·플러그인 OFF에서도 작동한다. `.work` 상태는 보조다.
3. **매 턴 주입은 0에 가깝게.** 상세는 필요할 때 읽는다.
4. **측정하고 남긴다.** 평가 기준을 넘지 못한 장치는 사용 여부를 확인한 뒤 제거한다.

## 구조

### 상시 (최소)

- 자동 호출 Skill은 `agent-workflow`, `diagnose`, `recall`, `setup-project-verification`,
  `fixing-accessibility` 다섯 개다. 나머지 17개는 명시 호출 전용(Claude `disable-model-invocation`,
  Codex `allow_implicit_invocation: false`)이고, `agent-workflow`가 필요할 때 형제 Skill의 `SKILL.md`를
  읽어 쓴다([inventory](../architecture/skill-inventory.md)).
- 프롬프트 hook은 선택된 task가 없으면 Git도 runtime도 실행하지 않는다. 요청 유형이 맞을 때만 한 줄
  route를 남긴다. 따옴표 문구 편집과 고치라는 요청이 없는 질문에는 route를 주지 않는다.
- Stop guard는 마지막 편집 뒤 실행이 없을 때 한 번 막는다. 막을 때만 컨텍스트를 쓴다.

### 위임 작업의 핵심 장치 (`agent-workflow`, `diagnose`, 플레이북)

| 장치 | 막는 실패 (기록) |
| --- | --- |
| L1 수락 기준 먼저: 요구사항에서 기대값을 정하고, 현재 코드에서 의도한 이유로 실패하는지 확인 | 자기 테스트 통과·공식 실패 (0.1.78 Carbon 6/6) |
| L2 `probe_check.py prove`: 새 테스트는 소스 변경 없이 실패해야 함. 규칙은 probe로 등록 | 테스트 PASS인데 결함 통과 (Labeler 4/11, yeondoo 3/8) |
| L3 영향받는 기존 검사를 최종 편집 뒤 실행 | 기존 `PublicAPI-test.js` 미실행 |
| L4 같은 규칙을 쓰는 모든 경로 확인, 반박된 가설의 변경 되돌리기 | settle-order 우회 누락 (0.1.85) |
| L5 결과 카드: 요청→동작, 영향 Feature/계층, 최종 편집 뒤 검사, 증명, 미확인, 사용자 결정 | 무엇을 검증했는지 알 수 없음 |

pstack(MIT, Lauren Tan, 0.15.25 `101b274`)의 test-behavior·tdd·fix-root-causes·attack-the-premise·
blast-radius·build-the-lever·orchestrate 원칙을 위 장치와 swarm 지시서에 반영했다
([비교 기록](pstack-practical-comparison.md)).

### 제품 저장소 자산

`.harness/probes.json`의 probe 하나는 규칙 하나의 인공 결함(파일·find·replace·검사 명령, Feature, 관점
business/architecture/ui, 계층)이다. `probe_check.py probes`는 격리 worktree에서 각 probe를 적용해
Feature × 관점 × 계층의 killed/total을 보여 준다. 이 한 등록부가 다음을 잇는다.

- 검증 가시성: PASS 개수 대신 결함 검출 수
- 피드백·가드레일: 불만의 원래 결함과 우회 경로를 probe로 등록해 재발을 잡는다
- UI 기준: token 하드코딩·간격 변형을 lint·시각 검사가 잡아야 한다
- 검사 정리: 고유하게 잡는 probe가 없는 검사는 통합·제거 후보, 아무도 못 잡은 probe는 공백

Feature Map(규칙 → 검사 → 계층 책임자)과 UI 가이드·token은 프로젝트가 소유한다. 결과는 `audit --report`
와 probe 행렬로 본다.

## 책임과 권한 경계

| 소유자 | 책임 |
| --- | --- |
| Agent | 요청·영향·원인·시각 결과의 의미 판단, 검사 선택과 근거 읽기 |
| 공통 runtime | 기존 task·조회·capture·현재성, probe 실행. 제출한 상태는 행동 증거가 아니다 |
| 프로젝트 | 업무 규칙, Feature Map, UI token/component, 실행 가이드, runner·assertion, probe 등록부 |
| 지원 host | 플러그인 식별·Skill 발견·hook 전달. 설치·신뢰는 host 권한 경계 |

설치본 갱신, 전역 설정, 보호 branch 통합, push/publish, 유료 실행은 이 문서로 승인되지 않는다.
fixture·package·실제 제품·native host·사업 성과는 서로 다른 증거다.

## 현재 상태

0.1.88의 구현·측정 결과는 [0.1.88 기록](lean-delegation-0.1.88.md)이 소유한다. 판정 기준을 넘기 전에는
플러그인이 위임 결과를 개선한다고 보고하지 않는다.
