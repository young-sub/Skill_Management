# 개인 Agent Harness V2 고도화 계획

## 1. 목표

Harness V2의 목적은 다음 개발 사이클을 반복 가능하게 만드는 것이다.

```text
아이디어 탐색
→ 계획 구체화
→ 구현 계획 작성
→ 인간과 설계 합의
→ Codex Goal Mode 자율 실행
→ 구현·테스트·진단·고도화·검증
→ 완료 검토
→ 계획 문서 아카이브
```

운영 원칙은 다음과 같다.

1. 구현 전에는 중요한 결정과 검증 방향을 사람과 합의한다.
2. 합의가 끝나지 않으면 구현을 시작하지 않는다.
3. 구현이 시작된 이후에는 원칙적으로 질문하지 않는다.
4. Agent는 승인된 범위 안에서 구현·테스트·진단·리팩터링·문서화를 자율적으로 수행한다.
5. 계획 문서는 작업 중 Agent의 실행 계약으로 사용하고 완료 후 아카이브한다.
6. 장기 유지 문서는 사람에게 먼저 이해되는 형태로 작성한다.
7. 테스트는 사전에 합의된 위험과 테스트 경계 안에서만 늘릴 수 있다.
8. Codex Goal Mode를 장시간 자율 실행의 공식 엔진으로 사용한다.

---

# 2. 목표 Architecture

## 2.1 Harness 저장소

Harness 자체는 별도 Git 저장소에서 관리한다.

```text
personal-agent-harness/
├─ instructions/
│  └─ GLOBAL.md
│
├─ skills/
│  ├─ bootstrap-project/
│  ├─ explore-idea/
│  ├─ design-goal/
│  ├─ execute-goal/
│  ├─ diagnose/
│  ├─ close-goal/
│  └─ maintain-harness/
│
├─ references/
│  ├─ testing-policy.md
│  ├─ documentation-policy.md
│  ├─ review-policy.md
│  ├─ goal-execution-policy.md
│  └─ human-readability-policy.md
│
├─ templates/
│  ├─ project/
│  │  ├─ AGENTS.md
│  │  ├─ TESTING.md
│  │  └─ harness.yaml
│  └─ work/
│     ├─ SPEC.md
│     ├─ GOAL.md
│     ├─ IMPLEMENTATION.md
│     └─ RESULT.md
│
├─ scripts/
│  ├─ install.ps1
│  ├─ sync-instructions.ps1
│  ├─ verify-install.ps1
│  ├─ run-goal.ps1
│  ├─ render-review.ps1
│  └─ maintain-project.ps1
│
├─ manifest.yaml
└─ README.md
```

이 저장소가 다음 항목의 유일한 Source of Truth가 된다.

* Global Instruction
* 직접 만든 Skill
* Skill 설치 상태
* 프로젝트 Bootstrap Template
* Goal 문서 Template
* 테스트·문서 정책
* 설치·동기화·점검 Script

`~/.agents/skills`와 `~/.claude/skills`는 설치 대상일 뿐 직접 수정하지 않는다.

---

# 3. Instruction 체계

## 3.1 Global `AGENTS.md`와 `CLAUDE.md`

두 파일은 완전히 동일하게 유지한다.

```text
personal-agent-harness/instructions/GLOBAL.md
        ↓ install.ps1
~/.codex/AGENTS.md
~/.claude/CLAUDE.md
```

설치 후 두 파일의 Hash를 비교한다.

Global Instruction에는 프로젝트와 무관한 항목만 둔다.

* 기본 개발 사이클
* Design Gate
* 구현 중 질문 제한
* Hard Stop 조건
* Codex Goal Mode 실행 원칙
* 테스트 및 문서 생성 원칙
* 사람 가독성 원칙
* 위험 작업 승인
* 완료 조건
* Skill routing

다음은 포함하지 않는다.

* 특정 프로젝트 경로
* 특정 Branch 이름
* 프로젝트별 테스트 명령
* Worktree 경로
* 특정 Issue Tracker
* 현재 작업 상태
* 특정 Domain 용어

## 3.2 Local `AGENTS.md`와 `CLAUDE.md`

신규 프로젝트에는 두 파일을 모두 만들고 항상 동일하게 유지한다.

```text
project/
├─ AGENTS.md
├─ CLAUDE.md
├─ TESTING.md
└─ .harness/
   └─ project.yaml
```

Local Instruction의 역할은 Repository Routing이다.

1. 프로젝트 목적
2. 주요 Entry point
3. Source of Truth
4. 설치·실행·검증 명령
5. Architecture 및 데이터 제약
6. 테스트 Tier와 Verification Budget
7. 작업 문서 위치
8. Codex Goal 실행 방식
9. 프로젝트별 Hard Stop
10. Definition of Done

Local Instruction에는 Global 정책을 다시 복사하지 않는다.

## 3.3 동기화

`AGENTS.md`를 Local 권위 원본으로 삼고 `CLAUDE.md`를 자동 복사한다.

다음 시점에 Hash 검증을 수행한다.

* Bootstrap 완료
* Goal 실행 전
* Goal 완료 후
* Harness 정기 점검
* 팀 프로젝트에서는 CI

두 파일이 다르면 Goal Mode 실행을 시작하지 않는다.

---

# 4. 작업 문서 체계

## 4.1 디렉터리

```text
project/
├─ .work/
│  ├─ active/
│  ├─ archive/
│  └─ trash/
│
├─ docs/
│  ├─ architecture/
│  ├─ adr/
│  ├─ domain/
│  ├─ contracts/
│  └─ runbooks/
│
├─ AGENTS.md
├─ CLAUDE.md
└─ TESTING.md
```

`.work/`는 Git에서 제외한다.

* `.work/active`: 현재 작업
* `.work/archive`: 완료 작업
* `.work/trash`: 삭제 대기 작업

Tracked 문서는 `.work/`의 문서를 링크하거나 Source of Truth로 인용하지 않는다.

현재 감사에서 확인된 가장 중요한 문서 문제는 Tracked ADR·Logic 문서가 Gitignored Plan을 참조하여 다른 환경에서 근거를 재현할 수 없다는 점이다. 신규 체계에서는 이 연결을 금지한다.

## 4.2 작은 작업

작은 기능이나 버그 수정은 단일 문서로 관리한다.

```text
.work/active/W-20260719-001/
├─ SPEC.md
└─ artifacts/
   ├─ design-review.html
   └─ completion-review.html
```

`SPEC.md` 구성:

1. 문제
2. 목표
3. 포함 범위
4. 제외 범위
5. 사용자 행동
6. 주요 결정
7. 구현 방향
8. 테스트 위험과 Seam
9. Verification Budget
10. 문서 변경 계획
11. 자율 실행 범위
12. Hard Stop
13. 완료 조건
14. 구현 결과

## 4.3 중대형 작업

여러 구현 단위가 필요하면 Master Goal과 하위 구현 문서를 사용한다.

```text
.work/active/W-20260719-002/
├─ GOAL.md
├─ plans/
│  ├─ 01-foundation.md
│  ├─ 02-core-behavior.md
│  ├─ 03-integration.md
│  └─ 04-verification.md
├─ RESULT.md
└─ artifacts/
   ├─ design-review.html
   └─ completion-review.html
```

`GOAL.md`에는 다음만 둔다.

* 최종 결과
* 전체 Scope
* 구현 문서 목록
* 문서 실행 순서
* 의존관계
* 전체 Acceptance criteria
* 전체 검증 명령
* Verification Budget
* Hard Stop
* 최종 완료 조건

각 구현 문서에는 다음을 둔다.

* 이 문서가 완성해야 할 동작
* 선행 문서
* 포함·제외 범위
* 구현 방향
* 테스트할 위험
* 테스트 Seam
* 부분 완료 조건
* 예상 영향 영역

하위 문서는 Layer별 작업이 아니라 검증 가능한 수직 Slice로 나눈다.

---

# 5. Design Gate

## 5.1 구현 전 조사

`design-goal`은 질문하기 전에 다음을 조사한다.

* 기존 코드
* 기존 Architecture
* Public interface
* Schema와 데이터 상태
* 관련 테스트
* 기존 Domain 용어
* 기존 ADR
* 실행 및 배포 환경
* 유사 기능
* 오류 처리
* 운영·보안 제약

파일이나 코드에서 확인할 수 있는 사실은 사용자에게 묻지 않는다.

## 5.2 일괄 인터뷰

질문은 다음 묶음으로 한 번에 제시한다.

1. 사용자 행동 및 Scope
2. 데이터·상태·재실행
3. Interface 및 호환성
4. 실패·보안·운영
5. 테스트·검증·완료 조건
6. 구현 방향 및 Architecture

각 항목은 다음 형식을 사용한다.

```text
결정:
기존 응답 Schema를 유지할 것인가?

권장안:
기존 Schema를 유지하고 신규 필드만 선택적으로 추가한다.

이유:
기존 호출자의 호환성을 유지할 수 있다.

대안:
A. 기존 Schema 유지
B. Schema 일괄 변경
C. Versioned interface 추가

영향:
B와 C는 호출자 Migration이 필요하다.
```

사용자는 다음처럼 한 번에 응답할 수 있어야 한다.

```text
전체 권장안 승인.
3번은 B안.
5번의 Live 검증은 이번 범위에서 제외.
```

필요한 경우 한 차례 보정 인터뷰를 수행할 수 있으나, 질문을 구현 중으로 넘기지 않는다.

## 5.3 Design Review Pack

설계 검토는 CLI 출력이 아니라 정적 HTML로 제공한다.

```text
.work/active/<work-id>/artifacts/design-review.html
```

화면에는 다음을 표시한다.

* 문제와 목표
* 포함·제외 범위
* 결정 항목과 권장안
* As-Is / To-Be
* Component 및 Data flow
* 구현 문서와 의존관계
* 테스트 위험·Seam·예산
* 문서 변경 계획
* Agent 자율 결정 범위
* Hard Stop
* 완료 조건

Markdown이 Source of Truth이고 HTML은 사람이 검토하기 위한 파생 산출물이다.

---

# 6. Codex Goal Mode 실행

감사 결과 Codex 설정에는 Goal 기능이 활성화돼 있다. 기존 Work Packet의 `run`을 유지하는 대신 Goal Mode를 Harness의 공식 장시간 실행 엔진으로 사용한다.

## 6.1 `execute-goal`의 책임

`execute-goal`은 다음을 수행한다.

1. `AGENTS.md`와 `CLAUDE.md` 동기화 확인
2. 승인된 `SPEC.md` 또는 `GOAL.md` 확인
3. 하위 구현 문서의 의존관계 검증
4. Codex Goal Mode용 실행 지시 생성
5. Goal Mode 시작
6. 계획 문서 순서에 따라 구현
7. 관련 테스트 반복
8. 실패 시 자동 진단·수정
9. 제한된 고도화
10. 전체 검증
11. 문서 정합화
12. `RESULT.md` 작성

Goal Mode 호출 방식은 Codex CLI 세부 명령에 직접 결합하지 않는다.

```text
execute-goal Skill
        ↓
scripts/run-goal.ps1
        ↓
현재 Codex Goal Mode 호출 방식
```

향후 Codex CLI가 변경되더라도 `run-goal.ps1`만 수정한다.

## 6.2 Goal Mode 실행 지시

기본 실행 지시는 다음 의미를 가져야 한다.

```text
GOAL.md와 여기서 참조하는 구현 문서를 의존 순서대로 수행한다.

각 구현 단위에서 승인된 테스트 Seam을 기준으로 테스트와 구현을 반복한다.
실패하면 원인을 진단하고 수정한 뒤 계속 진행한다.

승인된 범위 안에서 필요한 리팩터링, 오류 처리 보완,
문서 갱신 및 관련 Regression test를 자율적으로 수행한다.

구현 중 일반적인 세부 결정은 질문하지 않고 기존 규칙과
보수적인 기본값을 사용하여 결정한 뒤 RESULT.md에 기록한다.

모든 Acceptance criteria와 완료 조건을 만족할 때까지 계속한다.
Hard Stop 조건이 발생한 경우에만 실행을 중단하고 BLOCKED.md를 작성한다.
```

## 6.3 구현 상태

각 계획 문서는 최소 Metadata를 가진다.

```yaml
---
id: 02-core-behavior
status: pending
blocked_by:
  - 01-foundation
---
```

상태는 다음으로 제한한다.

```text
pending
in_progress
completed
blocked
skipped
```

Goal Mode는 문서를 시작할 때 `in_progress`, 완료 시 `completed`로 갱신한다.

별도의 복잡한 상태 데이터베이스는 만들지 않는다.

## 6.4 Worktree

Worktree는 Slice마다 만들지 않는다.

```text
1 Goal = 1 Branch = 최대 1 Worktree
```

Goal 완료 후에는 다음을 수행한다.

* Dirty 여부 확인
* Result와 변경 내용 확인
* 필요한 Handoff 생성
* Worktree 제거
* Git worktree prune
* Goal 문서 Archive 이동

현재처럼 여러 Slice가 각각 Worktree를 만들면 등록되지 않은 잔존 디렉터리와 오래된 Instruction 사본이 누적될 수 있다. 감사에서는 54개 디렉터리 중 44개가 미등록 상태였다.

---

# 7. 구현 중 자율성과 Hard Stop

## 7.1 Agent가 자율 결정

다음은 중단 없이 자율적으로 처리한다.

* 함수·클래스 내부 구조
* 기존 Convention에 따른 파일 위치
* Local naming
* 승인된 Seam 내 테스트 케이스
* Fixture 구성
* 오류 메시지 세부 표현
* 관련 Regression test
* 작은 범위의 중복 제거
* 변경 영역의 이름 개선
* 승인 범위 내 성능 개선
* 기존 Durable 문서 수정
* 계획에 포함된 신규 문서 생성

## 7.2 자율 결정 후 기록

다음은 구현을 계속하되 `RESULT.md`에 기록한다.

* 여러 구현안 중 되돌리기 쉬운 Local 선택
* 외부 행동은 같지만 내부 구조가 다른 선택
* 기존 Convention이 없어 보수적 기본값을 선택한 경우
* 승인된 설계를 구체화한 세부 Interface
* 예상보다 작은 범위의 추가 리팩터링

## 7.3 Hard Stop

다음 경우에만 Goal 실행을 중단한다.

1. 승인된 요구사항끼리 모순
2. Public behavior 또는 Business rule 변경 필요
3. 승인되지 않은 Public API·Schema 변경 필요
4. 데이터 손실 또는 Migration 위험
5. 새로운 Credential·비용·외부 서비스 필요
6. 보안·개인정보 위험 발생
7. 승인 범위를 크게 넘는 Architecture 변경 필요
8. 승인된 테스트 Seam으로 핵심 기능을 검증할 수 없음
9. 필수 실행 환경 또는 권한 부재
10. 기술적으로 유효한 구현 경로가 없음

Hard Stop 시 질문만 출력하지 않고 다음 파일을 만든다.

```text
BLOCKED.md
```

내용:

* 중단 지점
* 완료된 작업
* 막힌 이유
* 확인한 증거
* 권장 결정
* 가능한 대안
* 각 대안의 영향
* 재개 방법

---

# 8. Skill 재구성

기존 Matt Pocock Skill을 Wrapper로 감싸지 않는다.

해당 Skill에서 검증된 원칙만 참고하고 Runtime dependency는 제거한다.

## 8.1 최종 Skill

### 1. `bootstrap-project`

신규 Repository를 분석하고 다음을 생성한다.

* `AGENTS.md`
* `CLAUDE.md`
* `TESTING.md`
* `.harness/project.yaml`
* `.work/` 구조
* 최소 Durable 문서 구조
* 표준 명령
* 검증 예산

### 2. `explore-idea`

구현 전 아이디어를 검토한다.

* 문제의 실재성
* 사용자 가치
* 대안
* 제약
* 구현 난이도
* 작은 MVP
* 필요한 Prototype

영구 문서는 기본적으로 만들지 않는다.

### 3. `design-goal`

Repository 조사, 일괄 인터뷰, 계획 문서와 Review Pack 작성을 담당한다.

### 4. `execute-goal`

승인된 문서를 Codex Goal Mode로 구현·테스트·진단·고도화·검증한다.

### 5. `diagnose`

독립적인 버그나 성능 문제에 사용한다.

```text
재현
→ 최소화
→ 가설
→ 계측
→ Root cause
→ 수정
→ Regression test
→ 재검증
```

### 6. `close-goal`

* Spec 적합성 검토
* 코드 품질 검토
* 테스트 유지비 검토
* 문서 가독성 검토
* Durable 문서 승격
* Completion Review 생성
* Archive 이동
* Worktree 정리

### 7. `maintain-harness`

* Skill Drift 확인
* Instruction 동기화 확인
* Archive 정리
* Worktree 잔존물 확인
* 깨진 문서 링크 확인
* 테스트 실행시간 추세 확인
* 오래된 문서·테스트 후보 분석
* 설치 상태 검증

## 8.2 별도 Skill로 만들지 않을 것

다음은 별도 Skill이 아니라 공통 Reference로 둔다.

* TDD
* 테스트 작성 원칙
* Architecture review
* 문서 작성 원칙
* 사람 가독성 Review
* Completion report 형식

별도 Skill 수가 과도해지면 어떤 Skill을 호출해야 하는지 결정하는 비용이 다시 증가한다.

## 8.3 기존 Skill 정리

기존 Skill은 다음 세 그룹으로 나눈다.

### 교체

* `grill-me`
* `grill-with-docs`
* `to-prd`
* `to-issues`
* `triage`
* `setup-matt-pocock-skills`
* `work-packet`
* 기존 `project-agent-bootstrap`
* 기존 `tdd`
* 기존 `improve-codebase-architecture`
* 기존 `handoff`

### 재작성

* `diagnose`

### 유지

업무 Workflow와 직접 충돌하지 않는 전문 Skill:

* `finance-research`
* `frontend-design`
* Artifact 관련 Skill
* Browser·Document·Spreadsheet·Presentation Plugin
* OpenAI System Skill

기존 Skill은 즉시 삭제하지 않고 `legacy-skills/`에 보존한 뒤 새 Harness Pilot이 끝나면 Global catalog에서 제거한다.

---

# 9. Skill 설치 및 Drift 방지

## 9.1 Manifest

```yaml
version: 2.0.0

skills:
  - id: bootstrap-project
    version: 1.0.0
    install_to:
      - agents
      - claude

  - id: design-goal
    version: 1.0.0
    install_to:
      - agents
      - claude
```

## 9.2 설치

```text
personal-agent-harness/skills
        ↓ install.ps1
~/.agents/skills
~/.claude/skills
```

설치 결과는 Hash manifest로 검증한다.

금지 사항:

* 설치된 Skill 직접 수정
* 한 Tool 경로만 수정
* 외부 Skill 위에 Wrapper 추가
* 출처 불명 파일 복사
* Helper 없이 문서만 존재하는 Skill 배포

감사에서는 개인 Skill 24개가 두 경로에 별도 실파일로 복제되어 있었고, 8개는 출처·버전이 확인되지 않았다. 새 Harness는 Source 저장소와 설치 Manifest를 명확히 분리해야 한다.

---

# 10. 테스트 체계

## 10.1 사전 합의 대상

설계 단계에서는 테스트 함수나 파일을 하나씩 승인하지 않는다.

다음 Test Envelope를 승인한다.

| 항목    | 내용                               |
| ----- | -------------------------------- |
| 위험    | 어떤 실패를 막는가                       |
| 행동    | 외부에서 무엇을 관찰하는가                   |
| Seam  | 어느 Public boundary에서 테스트하는가      |
| Tier  | Fast / Integration / Live / Eval |
| 완료 기준 | 무엇을 통과해야 하는가                     |
| 비용    | 예상 실행시간·외부 호출                    |
| 범위    | 이번 Goal에 포함되는가                   |

승인 후 Agent는 Test Envelope 안에서 테스트를 자율적으로 추가한다.

## 10.2 Test Tier

### Fast

* 순수 Domain logic
* Parser·Schema
* Public function·class behavior
* 작은 Regression

### Integration

* DB
* File
* Process
* 내부 Component 연계
* Local service

### Live

* 실제 외부 API
* Credential
* 운영과 유사한 시스템
* 비용 또는 Side effect

### Eval

* LLM·VLM 품질
* Dataset 기반 정확도
* 비결정론적 결과
* 품질·성능 비교

현재 체계의 Code test와 Model eval 분리는 잘 구성된 강점이므로 유지한다.

## 10.3 Verification Budget

프로젝트별 `.harness/project.yaml`에 기록한다.

```yaml
verification:
  targeted_max_seconds: 30
  feature_max_seconds: 120
  fast_suite_max_seconds: 300
  full_suite_runs_per_goal: 1
  integration_default: impacted
  live_default: false
  eval_default: false
```

기본 실행 원칙:

1. 구현 Loop에서는 Targeted test만 실행
2. Slice 완료 시 Feature test 실행
3. Goal 완료 직전 Fast suite 전체 1회
4. Integration은 영향 영역만 실행
5. Live와 Eval은 사전 승인된 경우만 실행
6. Full suite를 매 Slice마다 실행하지 않음

## 10.4 테스트 생성 제한

다음은 Design Gate에서 명시되지 않았다면 자동 생성하지 않는다.

* Snapshot test
* 대형 Golden file
* 새로운 Test framework
* Architecture source-shape guard
* 성능 Threshold
* 실제 외부 API test
* 대규모 Fixture
* 전체 Module Mock
* Coverage 수치만 높이기 위한 테스트

## 10.5 테스트 파일 Naming

작업 번호나 Goal 단계를 테스트 파일명에 사용하지 않는다.

금지 예:

```text
test_feature_wp3.py
test_feature_s4.py
test_hard2.py
```

권장:

```text
test_claim_review_contract.py
test_voucher_amount_reconciliation.py
test_eval_manifest_loading.py
```

테스트는 작업 이력이 아니라 장기적으로 보호하는 Behavior에 따라 배치한다.

## 10.6 완료 단계 유지비 Review

`close-goal`은 다음을 검사한다.

* 새 테스트가 승인된 위험과 연결되는가
* 같은 Failure mode를 다른 테스트가 중복 검증하는가
* 내부 구현에 결합됐는가
* Fixture가 과도한가
* 전체 실행시간이 증가했는가
* Source-shape test가 실제 Architecture contract인가
* 삭제하거나 통합할 기존 테스트가 있는가

자동 삭제하지 않고, 변경한 범위에서 명백한 중복만 정리한다.

---

# 11. 문서 체계

## 11.1 Durable 문서

다음은 장기 Source of Truth다.

* `README.md`
* `AGENTS.md`
* `CLAUDE.md`
* `TESTING.md`
* Architecture
* ADR
* Domain glossary
* API·Schema contract
* Runbook

## 11.2 Work 문서

다음은 구현을 위한 Local 문서다.

* `SPEC.md`
* `GOAL.md`
* 구현 Plan
* `RESULT.md`
* Review HTML
* `BLOCKED.md`

Work 문서는 완료 후 Archive로 이동한다.

## 11.3 문서 생성 Trigger

| 상황                   | 행동                    |
| -------------------- | --------------------- |
| 단순 내부 수정             | 기존 문서만 필요 시 수정        |
| Component 경계 변경      | Architecture 수정       |
| Public API·Schema 변경 | Contract 수정           |
| 되돌리기 어려운 Trade-off   | ADR 생성                |
| 실제 Domain 용어 확정      | Glossary 수정           |
| 운영 절차 변경             | Runbook 수정            |
| 임시 조사                | Work 문서 또는 `.scratch` |
| 코드에서 바로 확인 가능        | 별도 문서 생성 안 함          |

파일 생성마다 사용자에게 묻지 않는다. Design Gate에서 문서 변경 계획을 한 번 승인받고 그 범위 안에서 자율 실행한다.

## 11.4 사람 가독성

Durable 문서는 Human-first로 작성한다.

금지:

* Agent만 이해하는 축약어
* 합의되지 않은 신조어
* Work ID 기반 용어
* 코드 내부 명칭을 Domain 용어처럼 사용
* 이전 대화를 알아야 이해되는 설명
* 개인 PC 경로
* Archive Plan 참조
* 불필요한 파일·함수 나열

새로운 Canonical 용어는 다음 중 하나를 만족해야 한다.

* 실제 사용자나 업무 담당자가 사용
* 코드 여러 영역에서 반복되는 안정적 개념
* 기존 용어로 명확히 표현할 수 없음
* Design Gate에서 사람과 합의

`close-goal`은 독립된 사람 독자의 관점에서 문서를 재검토한다.

---

# 12. Archive 및 삭제

## 12.1 완료 시

1. `RESULT.md` 작성
2. 장기 유지할 결정·구조를 Durable 문서로 승격
3. Durable 문서가 Work 문서를 참조하지 않는지 검사
4. Work 폴더를 `archive/YYYY-MM/`로 이동
5. 완료일과 보존기한 기록
6. Worktree 정리

## 12.2 보존기간

기본값:

* 개인 프로젝트: 90일
* 팀 프로젝트: 180일
* 명시적 보존: 무기한

## 12.3 두 단계 삭제

```text
archive
→ 보존기한 경과
→ trash
→ 30일 경과
→ 삭제
```

`maintain-harness`는 다음 조건을 모두 만족한 문서만 이동·삭제한다.

* Active 상태 아님
* 다른 Work 문서가 참조하지 않음
* Durable 문서가 참조하지 않음
* 중요한 결정이 Durable 문서로 승격됨
* 미완료 Follow-up 없음
* `retain: true`가 아님

삭제 내역은 간단한 Maintenance log에 남긴다.

---

# 13. 완료 Review

## 13.1 Completion Review Pack

```text
.work/active/<work-id>/artifacts/completion-review.html
```

포함 내용:

* 목표 대비 완료 결과
* 구현 문서별 상태
* 계획과 실제 구현 차이
* 주요 Architecture 변경
* 사용자 Behavior별 결과
* 테스트 결과와 실행시간
* 추가·수정·삭제한 테스트
* 실행하지 않은 Live·Eval
* 생성·수정한 Durable 문서
* 자동으로 결정한 구현 사항
* 잔여 위험
* 리뷰 우선 파일
* Merge·배포 전 확인 사항

## 13.2 Review 축

### Spec

* 승인한 요구를 모두 구현했는가
* 빠진 요구가 있는가
* 범위 밖 기능을 추가했는가

### Standards

* Repository 규칙을 지켰는가
* 오류 처리와 Naming이 적절한가
* 불필요한 복잡성이 생겼는가

### Maintainability

* 테스트 실행시간이 과도하게 늘었는가
* 같은 Behavior를 중복 검증하는가
* 문서가 Agent 중심으로 변질됐는가
* 새로운 용어가 사람에게 설명 가능한가
* 장기 유지 문서가 불필요하게 늘었는가

High finding이 남아 있으면 완료로 처리하지 않는다.

---

# 14. 팀 프로젝트 대응

Local Plan을 유지하되 팀 공유 산출물을 별도로 생성한다.

`close-goal`은 다음 Handoff를 만든다.

```text
HANDOFF.md
```

내용:

* 문제와 해결
* 중요한 설계 결정
* 변경된 Behavior
* 검증 결과
* 미검증 사항
* 주요 코드 위치
* 리뷰 포인트
* 잔여 위험

프로젝트 설정에 따라 출력 위치를 바꾼다.

```yaml
handoff:
  target: local
```

가능한 값:

```text
local
pr
both
```

Issue·PR 발행은 Harness 핵심 Workflow가 아니라 선택 Adapter다.

---

# 15. 실제 구축 순서

## Phase 1. Harness Source of Truth 구축

### 구현

* 신규 `personal-agent-harness` 저장소 생성
* `manifest.yaml` 작성
* Global Instruction 원본 작성
* `install.ps1`
* `sync-instructions.ps1`
* `verify-install.ps1`

### 완료 조건

* Global Codex·Claude Instruction 동일
* Skill 설치 경로가 Manifest에서 결정
* 설치본 직접 수정 여부를 Hash로 탐지
* 기존 Skill과 충돌하지 않는 신규 이름 사용

---

## Phase 2. 신규 프로젝트 Bootstrap

### 구현

* `bootstrap-project`
* Local `AGENTS.md`·`CLAUDE.md` Template
* `TESTING.md`
* `.harness/project.yaml`
* `.work` 구조
* Repository 조사 및 표준 명령 검증

### 완료 조건

* 신규 Repository에서 Bootstrap 1회로 기본 Harness 생성
* 두 Instruction 파일 동일
* 존재하지 않는 명령을 문서에 기록하지 않음
* 불필요한 문서 폴더를 미리 생성하지 않음

---

## Phase 3. Design Gate와 Review Pack

### 구현

* `explore-idea`
* `design-goal`
* 단일 `SPEC.md` Template
* Master `GOAL.md`와 다중 Plan Template
* Decision Pack
* `design-review.html` 생성기

### 완료 조건

* Repository 사실은 자동 조사
* 결정만 사용자에게 질문
* 질문은 구현 전에 일괄 수행
* 사용자가 한 번에 승인·수정 가능
* 승인되지 않은 Goal은 실행 불가

---

## Phase 4. Codex Goal Mode 실행

### 구현

* `execute-goal`
* `run-goal.ps1`
* 단일·다중 Plan 실행
* 상태 갱신
* Hard Stop과 `BLOCKED.md`
* `RESULT.md`
* Goal 단위 Worktree 관리

### 완료 조건

* 승인 후 구현·테스트·진단·검증이 중간 질문 없이 진행
* 다중 Plan을 의존 순서대로 처리
* 실패를 자동 진단하고 재시도
* Full suite 반복 실행 금지
* Hard Stop 외에는 실행 중단 없음

---

## Phase 5. Close·문서·테스트 통제

### 구현

* `close-goal`
* Completion Review
* Spec / Standards / Maintainability Review
* Durable 문서 승격
* Archive 이동
* 테스트 실행시간·증가량 기록

### 완료 조건

* Tracked 문서가 Local Work 문서를 참조하지 않음
* Agent-only 용어 검토
* 테스트가 위험과 Seam에 매핑
* 계획 대비 결과가 사람이 이해 가능한 형태로 제공
* Worktree가 Goal 종료 후 정리됨

---

## Phase 6. Maintenance

### 구현

* `maintain-harness`
* Instruction·Skill Drift 검사
* Archive → Trash → Delete
* Worktree 잔존물 검사
* Broken link 검사
* 테스트 실행시간 추세
* 오래된 문서·테스트 후보 보고

### 완료 조건

* Active·Archive 상태가 자동 판정 가능
* 오래된 Work 문서가 정기 정리됨
* AGENTS·CLAUDE Drift 0
* 설치된 Skill과 Manifest 불일치 0
* 미등록 Worktree 잔존물 탐지

---

## Phase 7. Legacy 제거

Pilot Goal을 최소 3~5회 수행한 후 기존 Workflow Skill을 Global catalog에서 제거한다.

먼저 제거할 대상:

* Work Packet
* Setup Matt Pocock Skills
* To PRD
* To Issues
* Triage
* 기존 Project bootstrap
* 기존 Grill 계열
* 기존 Handoff

기존 파일은 일정 기간 Legacy archive에 보존한다.

전문 Skill과 System·Plugin Skill은 유지한다.

---

# 16. Pilot 방법

기존 Voucher Agent 프로젝트에 바로 적용하지 않는다.

신규 프로젝트 한 곳에서 다음 세 유형을 시험한다.

1. 작은 버그 수정
2. 일반 기능 개발
3. 여러 구현 문서가 필요한 중대형 기능

각 Goal에서 다음을 측정한다.

* 설계 질문 횟수
* Design Gate 이후 추가 질문 횟수
* Goal Mode 중단 횟수
* 구현 완료율
* Targeted test 시간
* 전체 검증 시간
* 구현시간 대비 검증시간
* 생성된 테스트 수
* 생성된 Durable 문서 수
* Archive 이동 성공 여부
* 사람이 결과를 이해하는 데 필요한 시간

초기 성공 기준:

* Design Gate 이후 불필요한 질문 0
* Hard Stop 외 Goal 중단 0
* `AGENTS.md`와 `CLAUDE.md` Drift 0
* Durable 문서의 Local Plan 참조 0
* 완료된 Work가 Active에 남는 사례 0
* Goal당 Worktree 잔존 0
* Full suite 실행은 원칙적으로 1회
* 테스트 실행시간이 설정된 Budget 안에 있음

---

# 17. 최종 운영 형태

```text
사용자
  ↓
explore-idea                 선택
  ↓
design-goal
  ├─ Repository 조사
  ├─ 일괄 인터뷰
  ├─ SPEC 또는 GOAL 작성
  └─ Design Review HTML
  ↓
인간 Design Gate
  ↓
execute-goal
  └─ Codex Goal Mode
       ├─ 다중 Plan 순차 실행
       ├─ TDD
       ├─ 자동 진단
       ├─ 제한적 고도화
       ├─ 테스트
       ├─ 문서화
       └─ 전체 검증
  ↓
close-goal
  ├─ Spec Review
  ├─ Standards Review
  ├─ Maintainability Review
  ├─ Completion Review HTML
  ├─ Durable 문서 승격
  └─ Archive·Worktree 정리
  ↓
maintain-harness             정기
```

# 18. 최종 판단

기존 Harness에서 유지할 강점은 다음이다.

* 구현 전 요구사항 정리
* Local Plan 기반 실행
* TDD와 Diagnose
* Architecture와 ADR
* Test와 Eval 분리
* Codex 장시간 자율 실행

제거할 구조는 다음이다.

* 외부 Skill과 Wrapper의 다단계 의존
* Issue·PR 중심의 불필요한 Workflow
* Tool별 Skill 수동 복사
* Worktree마다 누적되는 Instruction snapshot
* 작업 번호 중심 테스트 파일
* Durable 문서에서 Local Plan 참조
* 제한 없는 테스트·문서 추가
* 종료 기준 없는 고도화
* CLI 텍스트만을 이용한 사람 검토

V2의 핵심 단위는 Work Packet이나 Issue가 아니라 다음 세 가지다.

```text
Design Contract
Goal Execution
Human-readable Completion
```

구현 문서는 사람과 Agent가 합의한 계약이고, Codex Goal Mode는 해당 계약을 끝까지 실행하는 엔진이며, Completion Review는 사람이 결과를 빠르게 이해하고 검토하기 위한 산출물이다.
