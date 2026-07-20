# Personal Agent Harness V2 구현 계획

## 문서 상태

| 항목 | 값 |
| --- | --- |
| 상태 | 구현 준비 완료 초안 |
| 작성일 | 2026-07-19 |
| 대상 저장소 | `young-sub/Skill_Management` |
| 상위 기획 | `skill_recreate_plan.md` |
| 다음 단계 | 이 문서를 구현 계약으로 사용해 V2 구축 시작 |

이 문서는 `skill_recreate_plan.md`의 방향을 현재 저장소에 실제로 적용하기 위한 구현 문서다. 다음 세션은 다시 제품 방향을 탐색하는 대신, 이 문서의 결정과 순서에 따라 저장소를 재구성하고 검증한다.

---

## 1. 목적

현재 저장소를 개인용 Agent Harness의 유일한 Source of Truth로 전환한다. 최종적으로 다음 경험을 제공해야 한다.

1. 사용자는 하나의 설치 명령을 실행한다.
2. Installer에서 설치할 Skill과 대상 Agent Provider를 선택한다.
3. 프로젝트마다 `setup-agent-harness`를 한 번 실행해 Repository 규칙과 검증 환경을 설정한다.
4. `design-goal`이 코드와 문서를 조사하고 구현 계약을 작성한다.
5. 사용자가 계약을 승인하고 직접 Codex `/goal`을 선언한다.
6. 활성 Goal 안에서 `execute-codex-goal`이 승인된 계약을 구현·테스트·진단·검증한다.
7. `close-goal`이 결과를 검토하고 사람이 읽을 수 있는 Completion Review를 만든다.
8. `maintain-agent-harness`가 설치 Drift, 오래된 작업 문서, Worktree 잔존물 등을 점검한다.

V2는 Issue나 PR을 필수 실행 단위로 삼지 않는다. 핵심 단위는 다음 세 가지다.

```text
Design Contract
Goal Execution
Human-readable Completion
```

---

## 2. 배경

현재 저장소에는 Agent-driven development를 위한 여러 Skill이 개별적으로 축적되어 있다. 각각은 유용한 원칙을 포함하지만 전체 개발 생명주기에서는 다음 문제가 발생한다.

- 아이디어 탐색, 인터뷰, PRD, Issue, 구현, 진단, Review가 서로 다른 Workflow를 전제로 한다.
- `work-packet`, Matt Pocock 계열 Skill, Project Bootstrap이 서로의 문서와 설정을 요구한다.
- Issue/PR 발행과 실제 구현 계약이 강하게 결합되어 개인 프로젝트에도 불필요한 절차가 생긴다.
- Codex Goal Mode가 실행 엔진임에도 기존 Skill은 Goal 실행을 중심으로 설계되어 있지 않다.
- Codex와 Claude용 Skill이 각각 복사되어 Source와 설치본의 경계가 불명확하다.
- 설치된 파일이 직접 수정되면 원본과의 Drift를 안정적으로 탐지하기 어렵다.
- 작업 번호와 임시 Plan이 테스트명이나 Durable 문서로 누출될 수 있다.
- 완료 후 Work 문서, Worktree, Instruction snapshot이 남을 수 있다.

V2는 기존 Skill을 Wrapper로 다시 감싸지 않는다. 기존 Skill에서 검증된 원칙만 추출하고, 하나의 짧고 명시적인 개발 흐름으로 재구성한다.

---

## 3. 현재 저장소 현황

### 3.1 확인된 사실

- Git remote는 `git@github.com:young-sub/Skill_Management.git`이다.
- 기본 작업 branch는 현재 `main`이다. 실제 보호 branch 여부는 구현 시 remote 설정으로 다시 확인한다.
- `skills/`에는 25개 Skill 디렉터리가 존재했다.
- tracked 파일은 `skills/` 119개, `back-up/` 239개다.
- `skills/`와 `back-up/`을 합쳐 동일 SHA-256을 가진 파일 그룹이 117개 존재한다.
- Root `AGENTS.md`는 98줄, `CLAUDE.md`는 99줄이며 내용과 Hash가 일치하지 않는다.
- Root `README.md`에는 저장소 제목 외의 설치·운영 설명이 없다.
- PowerShell installer, 설치 Manifest, Drift verifier가 아직 없다.
- 현재 설치된 `codex-cli 0.144.6`은 `goals` feature를 stable로 노출한다.
- `/goal`은 사람이 Codex 안에서 선언하는 기능이다. Harness가 CLI wrapper로 대신 선언하지 않는다.
- 현재 Worktree에는 `skills/caveman/SKILL.md`, `skills/codex-delegation/SKILL.md` 삭제 변경과 untracked `skill_recreate_plan.md`가 있다. 이 변경은 구현 세션에서 임의로 되돌리지 않는다.

### 3.2 현재 강점

- `diagnose`에는 재현 가능한 feedback loop를 우선하는 진단 원칙이 있다.
- `tdd`에는 Red-Green-Refactor와 public behavior 중심 검증 원칙이 있다.
- `project-agent-bootstrap`에는 Repository evidence 기반 설정 원칙이 있다.
- `work-packet`에는 구현 계약, verification evidence, close report의 유용한 형식이 있다.
- `grill-with-docs`에는 Domain language와 ADR을 기준으로 결정을 명확히 하는 방식이 있다.
- Code test와 Model Eval을 구분하는 관점이 이미 존재한다.

이 원칙은 유지하되 기존 Skill을 Runtime dependency로 호출하지 않는다.

---

## 4. 리팩터링 범위

리팩터링 대상은 현재 저장소의 모든 Skill이 아니다. Agent-driven software development의 생명주기를 소유하거나 그 생명주기에 강하게 결합된 Skill만 대상으로 한다.

### 4.1 교체 또는 흡수 대상

| 기존 Skill | 처리 | V2 대응 |
| --- | --- | --- |
| `project-agent-bootstrap` | 교체 | `setup-agent-harness` |
| `setup-matt-pocock-skills` | 흡수 후 제거 | `setup-agent-harness` |
| `grill-me` | Workflow 기능 흡수 | `explore-idea`, `design-goal` |
| `grill-with-docs` | Workflow 기능 흡수 | `design-goal` |
| `to-prd` | 제거 | `design-goal`의 Contract 작성 |
| `to-issues` | 제거 | `design-goal`의 수직 Slice 작성 |
| `triage` | Core에서 제거 | 선택적 Tracker Adapter로만 재도입 가능 |
| `work-packet` | 교체 | Design Contract와 Goal Execution |
| `tdd` | 공통 정책으로 흡수 | Test Envelope와 실행 Reference |
| `improve-codebase-architecture` | Core Workflow 부분 흡수 | Design/Close architecture pass |
| `handoff` | Close 산출물로 흡수 | `close-goal`의 `HANDOFF.md` |
| `diagnose` | 재작성 | V2 `diagnose` |
| `codex-delegation` | 제거 또는 Archive | Codex Goal Mode 직접 사용 |

### 4.2 호환성만 검토할 지원 Skill

다음 Skill은 Core Workflow를 소유하지 않으므로 원칙적으로 재작성하지 않는다. 다만 V2가 이들을 선택적으로 호출할 때 문서 위치나 상태 모델이 충돌하지 않는지는 검증한다.

- `multi-agent-review`
- `prototype`
- `webapp-testing`
- `zoom-out`

호환성 수정은 path, trigger, obsolete dependency 제거에 한정한다. V2 구현을 이유로 기능 자체를 재설계하지 않는다.

### 4.3 명시적 제외 대상

다음은 전문 Domain, Artifact 생성, 학습 또는 Skill 관리 기능이다. Agent-driven development Core 리팩터링 범위에서 제외하며 내용도 변경하지 않는다.

- `finance-research`
- `frontend-design`
- `web-artifacts-builder`
- `theme-factory`
- `teach`
- `find-skills`
- `write-a-skill`
- `caveman`

이 목록의 Skill은 새 installer에서 선택 가능한 상태로 유지할 수 있지만 Harness Core profile에는 포함하지 않는다.

---

## 5. 이상적인 운영 방향

### 5.1 사람과 Agent의 책임 분리

사람이 책임지는 항목:

- 구현할 Goal 선택
- Design Contract의 중요한 결정 승인
- `/goal` 선언, 일시정지, 재개 또는 취소
- Credential, 비용, 외부 서비스, 파괴적 작업 승인
- Completion Review 확인과 Merge 판단

Agent가 책임지는 항목:

- 질문 전 Repository 조사
- 승인된 범위 내 세부 구현 결정
- Test Envelope 안의 테스트 설계
- 구현, 진단, 작은 리팩터링, 문서 정합화
- 상태 및 Verification evidence 기록
- Hard Stop 발생 시 증거가 포함된 `BLOCKED.md` 작성

### 5.2 사용자 호출 Skill과 Agent 호출 Skill 분리

사용자가 호출하는 Orchestration Skill:

- `setup-agent-harness`
- `explore-idea`
- `design-goal`
- `maintain-agent-harness`

Goal 또는 Agent가 호출하는 Discipline Skill:

- `execute-codex-goal`
- `diagnose`
- `close-goal`

사용자 호출 Skill은 다른 사용자 호출 Skill을 자동으로 연쇄 실행하지 않는다. `design-goal`이 끝나면 Goal payload를 제공하고 멈춘다. 이후 사용자가 `/goal`을 선언해야 한다.

### 5.3 문서 경계

- `.work/`는 실행 계약과 임시 증거를 저장하며 Gitignored다.
- `docs/`는 장기 유지할 Architecture, ADR, Domain, Contract, Runbook만 저장한다.
- Tracked 문서는 `.work/` 파일을 Source of Truth로 링크하거나 인용하지 않는다.
- 완료 시 중요한 결정만 Durable 문서로 승격한다.
- HTML Review Pack은 Markdown 계약에서 생성되는 파생 산출물이다.

---

## 6. 목표 Repository 구조

```text
Skill_Management/
├─ skills/
│  ├─ setup-agent-harness/
│  │  ├─ SKILL.md
│  │  ├─ scripts/
│  │  ├─ references/
│  │  └─ assets/
│  ├─ explore-idea/
│  ├─ design-goal/
│  ├─ execute-codex-goal/
│  ├─ diagnose/
│  ├─ close-goal/
│  ├─ maintain-agent-harness/
│  └─ <범위 밖 기존 전문 Skill>/
├─ authoring/
│  ├─ references/
│  │  ├─ testing-policy.md
│  │  ├─ documentation-policy.md
│  │  ├─ review-policy.md
│  │  ├─ goal-execution-policy.md
│  │  └─ human-readability-policy.md
│  └─ templates/
│     ├─ project/
│     ├─ work/
│     └─ review/
├─ scripts/
│  ├─ sync-skill-resources.ps1
│  ├─ validate-distribution.ps1
│  └─ test-install.ps1
├─ tests/
│  ├─ distribution/
│  ├─ skills/
│  └─ fixtures/
├─ legacy-skills/
├─ docs/
│  ├─ architecture/
│  ├─ adr/
│  └─ runbooks/
├─ AGENTS.md
├─ CLAUDE.md
├─ README.md
└─ LICENSE
```

`authoring/`은 공통 정책의 권위 원본이다. 하지만 `npx skills`로 설치되는 개별 Skill은 자기완결적이어야 하므로 설치 후 `../../authoring`을 참조하면 안 된다. `sync-skill-resources.ps1`가 각 Skill에 필요한 Reference와 Template만 복제하고 생성된 파일에 Source hash를 기록한다.

---

## 7. Skill별 구체 구현

### 7.1 `setup-agent-harness`

목적: Repository evidence를 조사해 프로젝트를 V2 실행이 가능한 상태로 만든다.

구현 순서:

1. Root 및 nested instruction, README, build files, CI, test command, architecture 문서를 조사한다.
2. 프로젝트를 `NEW_UNCONFIGURED`, `EXISTING_PARTIAL`, `EXISTING_OVERGROWN`, `DRIFT_REPAIR` 중 하나로 분류한다.
3. 생성·수정할 파일과 발견한 명령을 사용자에게 한 번에 제시한다.
4. 승인 후 다음 최소 파일을 생성한다.

```text
AGENTS.md
CLAUDE.md
TESTING.md
.harness/project.yaml
.work/active/
.work/archive/
.work/trash/
```

5. `AGENTS.md`를 Local 권위 원본으로 사용하고 `CLAUDE.md`를 byte-identical하게 동기화한다.
6. `.work/`를 `.gitignore`에 추가한다.
7. 실제로 성공한 명령만 `TESTING.md`와 `project.yaml`에 기록한다.
8. Global Instruction 설치가 필요한 경우 provider별 대상과 diff를 먼저 보여주고 별도 승인을 받는다.

`project.yaml` 최소 Schema:

```yaml
version: 2
project:
  name: example
  classification: existing_partial

instructions:
  authoritative: AGENTS.md
  mirrors:
    - CLAUDE.md

work:
  root: .work
  retention_days: 90
  trash_grace_days: 30

verification:
  targeted_max_seconds: 30
  feature_max_seconds: 120
  fast_suite_max_seconds: 300
  full_suite_runs_per_goal: 1
  integration_default: impacted
  live_default: false
  eval_default: false

handoff:
  target: local
```

완료 조건:

- 두 Instruction 파일 Hash가 동일하다.
- 기록된 검증 명령이 실제로 실행 가능하다.
- 존재하지 않는 문서 구조를 불필요하게 생성하지 않는다.
- 기존 사용자 문서와 dirty change를 덮어쓰지 않는다.

### 7.2 `explore-idea`

목적: 구현 계약을 만들기 전에 문제의 실재성, 가치, 대안과 작은 MVP를 검토한다.

규칙:

- 기본적으로 파일을 생성하지 않는다.
- Repository 조사가 필요한 아이디어라면 read-only 탐색만 한다.
- 결론은 문제, 사용자 가치, 대안, 제약, MVP, Prototype 필요 여부로 정리한다.
- 사용자가 구현을 결정하면 `design-goal`이 다음 단계라고 안내하고 멈춘다.
- `design-goal`을 자동 실행하지 않는다.

### 7.3 `design-goal`

목적: Repository evidence와 사용자 결정을 결합해 승인 가능한 구현 계약을 만든다.

절차:

1. 기존 코드, public interface, schema, tests, ADR, domain language, runtime, security 제약을 조사한다.
2. 코드에서 확인 가능한 내용은 질문하지 않는다.
3. 남은 결정은 다음 묶음으로 한 번에 제시한다.
   - 사용자 행동과 Scope
   - 데이터, 상태와 재실행
   - Interface와 호환성
   - 실패, 보안과 운영
   - 테스트, 검증과 완료 조건
   - Architecture 방향
4. 작은 작업은 `SPEC.md`, 중대형 작업은 `GOAL.md`와 `plans/*.md`를 만든다.
5. 각 Plan은 Layer가 아니라 독립 검증 가능한 수직 Slice로 나눈다.
6. `design-review.html`을 생성한다.
7. 사용자의 승인 응답을 받은 뒤 승인 Metadata와 계약 Hash를 기록한다.
8. 마지막 출력으로 Goal declaration payload를 제공하고 멈춘다.

승인 Metadata 예시:

```yaml
approval:
  status: approved
  approved_at: 2026-07-19T18:00:00+09:00
  approved_by: human
  contract_hash: sha256:<canonical-contract-hash>
```

Hash는 승인 Metadata 자체와 실행 중 상태 필드를 제외한 계약 내용을 canonicalize한 뒤 계산한다. 구현 결과나 상태 변경 때문에 승인 Hash가 달라지면 안 된다.

Goal declaration payload 예시:

```text
Use $execute-codex-goal.

Work ID: W-20260719-001
Contract: .work/active/W-20260719-001/GOAL.md
Approved contract hash: sha256:...
Execute every approved slice in dependency order.
Stop only for the contract's Hard Stop conditions.
```

### 7.4 `execute-codex-goal`

목적: 사람이 선언한 활성 Codex Goal 안에서만 승인된 구현 계약을 실행한다.

이 Skill은 `/goal`을 생성하거나 시작하지 않는다. `run-goal.ps1`도 만들지 않는다.

Preflight:

1. Host가 Goal 상태 도구를 제공하면 활성 Goal을 조회한다.
2. 활성 Goal이 없으면 구현하지 않고 Goal declaration payload를 다시 제공한다.
3. Goal objective의 Work ID, Contract path, contract hash가 문서와 일치하는지 확인한다.
4. `AGENTS.md`와 `CLAUDE.md` Hash를 확인한다.
5. 승인 상태와 Plan dependency DAG를 검증한다.
6. Git branch, worktree, dirty baseline을 기록한다. 기존 dirty change는 보존한다.

실행 Loop:

1. dependency가 충족된 첫 `pending` Plan을 선택한다.
2. 상태를 `in_progress`로 원자적으로 변경한다.
3. 승인된 Test Envelope에 맞는 failing test 또는 eval을 먼저 만든다.
4. 최소 구현으로 통과시킨다.
5. 관련 regression, type, lint, documentation check를 수행한다.
6. 실패하면 `diagnose` 원칙으로 원인을 확인하고 수정한다.
7. 부분 완료 조건을 만족하면 Plan을 `completed`로 변경한다.
8. 다음 Plan으로 이동한다.
9. 전체 Acceptance criteria를 검증한다.
10. `close-goal` 절차를 수행한다.
11. High finding이 없고 완료 조건이 충족된 경우에만 Goal을 complete 처리한다.

Hard Stop이면 구현을 멈추고 `BLOCKED.md`에 다음을 기록한다.

- 중단 지점
- 완료된 Plan
- 확인한 증거
- 막힌 이유
- 권장 결정
- 가능한 대안과 영향
- 재개 방법

### 7.5 `diagnose`

기존 Skill을 간결하게 재작성하되 다음 feedback loop는 유지한다.

```text
재현 → 최소화 → 가설 → 계측 → Root cause → 수정 → Regression test → 재검증
```

변경 사항:

- 기존 Work Packet, tracker, Matt Pocock 설정 의존을 제거한다.
- 프로젝트의 `TESTING.md`, `.harness/project.yaml`, Durable docs만 읽는다.
- 승인된 Test Envelope 밖의 Live test나 대형 fixture를 자동 추가하지 않는다.
- 진단 결과는 실행 중인 Work의 `RESULT.md` 또는 독립 버그 작업의 `SPEC.md`에 기록한다.

### 7.6 `close-goal`

목적: 구현 완료 주장을 검증하고 사람이 빠르게 판단할 수 있는 결과를 만든다.

Review 축:

- Spec: 승인된 요구를 빠짐없이 구현했는가.
- Standards: Repository 규칙, 오류 처리, naming을 지켰는가.
- Maintainability: 복잡성, 중복 테스트, 문서 증가가 합리적인가.
- Architecture: 변경된 boundary가 명확하고 테스트 가능한가.
- Diagnostics: 운영자에게 필요한 상태와 실패 정보가 제공되는가.

산출물:

```text
RESULT.md
artifacts/completion-review.html
HANDOFF.md               # handoff.target이 local 또는 both일 때
```

Close Gate:

- High finding이 남아 있으면 완료하지 않는다.
- Tracked 문서가 `.work/`를 참조하면 완료하지 않는다.
- 실행하지 않은 Live/Eval은 실패로 위장하지 않고 미검증으로 기록한다.
- 중요한 결정과 구조만 Durable 문서로 승격한다.
- Work 문서를 `archive/YYYY-MM/`로 이동한다.
- Worktree 정리는 사용자 설정과 안전 검증 후 수행한다.

### 7.7 `maintain-agent-harness`

기본 동작은 report-only다. 삭제나 설치본 교체에는 명시적 승인 또는 `-Apply`가 필요하다.

점검 항목:

- 설치된 Skill과 배포 Source의 Hash Drift
- `AGENTS.md`와 `CLAUDE.md` Drift
- Active, Archive, Trash 상태
- 보존기한이 지난 Work 문서
- Durable 문서에서 `.work/`를 향하는 링크
- 등록되지 않은 Worktree와 잔존 디렉터리
- Test 실행시간 Budget 초과 추세
- 오래되거나 중복된 테스트 후보
- 배포된 Skill의 누락된 resource와 깨진 상대 경로

---

## 8. 설치 및 인터넷 배포

### 8.1 기본 배포 방식

V2 초기 배포는 별도 전용 installer를 만들지 않고 Agent Skills ecosystem의 `skills` CLI를 사용한다.

대화형 설치:

```powershell
npx skills@latest add young-sub/Skill_Management
```

사용자는 대화형 UI에서 다음을 고른다.

- 설치할 Skill
- 대상 Agent Provider: Codex, Claude Code 등
- Project 또는 Global scope
- Symlink 또는 Copy 방식

자동 설치 예시:

```powershell
npx skills@latest add young-sub/Skill_Management `
  -g `
  -a codex `
  -a claude-code `
  --skill setup-agent-harness `
  --skill explore-idea `
  --skill design-goal `
  --skill execute-codex-goal `
  --skill diagnose `
  --skill close-goal `
  --skill maintain-agent-harness `
  -y
```

### 8.2 배포 요구사항

- 각 배포 Skill은 자체 `SKILL.md`와 필요한 resource를 모두 포함한다.
- Skill 밖 상대 경로를 참조하지 않는다.
- 각 `SKILL.md` frontmatter는 `name`, `description`만 사용한다.
- Skill folder와 `name`은 일치한다.
- 공개 branch에는 installer가 발견하면 안 되는 Legacy `SKILL.md`를 두지 않는다.
- Release는 Semantic Version tag와 GitHub Release로 식별한다.
- `README.md`에는 interactive, non-interactive, update, uninstall, project setup 절차를 기록한다.

### 8.3 Legacy 보존

리팩터링 대상 기존 Skill은 즉시 삭제하지 않는다.

1. V2 대응 관계와 원본 commit을 기록한다.
2. `legacy-skills/`로 이동한다.
3. `SKILL.md`를 installer가 인식하지 않는 이름으로 변경하거나 압축 archive로 보존한다.
4. Pilot 동안 기존 설치본은 유지할 수 있지만 신규 설치 catalog에는 노출하지 않는다.
5. Pilot 성공 후 기존 전역 설치본 제거 절차를 별도 승인받는다.

전문 Skill과 호환 지원 Skill은 `skills/`에 계속 남긴다.

---

## 9. 구현 Work Packets

### WP-01: Distribution과 저장소 경계

구현:

- 리팩터링 대상과 제외 대상의 inventory 문서화
- `skills/`, `authoring/`, `legacy-skills/` 경계 생성
- Skill resource 동기화 및 배포 검증 script 작성
- Root `README.md` 설치 문서 작성
- Root `AGENTS.md`와 `CLAUDE.md`를 이 저장소의 Local Router로 축소·동기화

검증:

- 모든 공개 Skill frontmatter 검증
- 공개 Skill에서 repo 밖 상대 경로 0개
- `npx skills add . --list`가 예상 Skill만 표시
- 임시 경로에 Codex와 Claude Code target 설치 성공

### WP-02: Project Bootstrap

구현:

- `setup-agent-harness`
- Project instruction, `TESTING.md`, `project.yaml` template
- instruction hash와 실제 명령 검증 helper
- 신규, 부분 설정, drift fixture

검증:

- 세 종류 fixture에서 dry-run과 apply 결과 검증
- 기존 파일 충돌 시 덮어쓰지 않고 diff 제공
- 존재하지 않는 command 기록 0개

### WP-03: Design Contract

구현:

- `explore-idea`
- `design-goal`
- `SPEC.md`, `GOAL.md`, Plan, `RESULT.md`, `BLOCKED.md` template
- 계약 Schema, canonical hash, dependency DAG validator
- 정적 Design Review renderer

검증:

- 작은 작업과 중대형 작업 fixture 생성
- 승인 전 실행 불가
- 승인 후 계약 변경 탐지
- DAG cycle과 없는 dependency 탐지
- HTML escaping과 필수 section 검증

### WP-04: Codex Goal Execution

구현:

- `execute-codex-goal`
- Goal 상태 확인, Plan 선택, 상태 전이, evidence 기록 절차
- `diagnose` 재작성
- Hard Stop과 `BLOCKED.md`

검증:

- 활성 Goal이 없으면 source 수정 0개
- Work ID 또는 Hash 불일치 시 source 수정 0개
- Fake Goal state와 fixture plans로 순차 실행 검증
- 실패 후 diagnose와 재시도 검증
- Hard Stop 발생 시 blocked 상태와 문서 생성 검증

### WP-05: Close와 Maintenance

구현:

- `close-goal`
- Completion Review renderer
- Durable 문서 link 검사
- Archive와 retention 처리
- `maintain-agent-harness`

검증:

- High finding이 있으면 complete 불가
- `.work/`를 참조하는 tracked 문서 탐지
- Archive → Trash는 report-only 기본값
- Worktree 잔존물과 instruction drift 탐지

### WP-06: Public Release와 Pilot

구현:

- GitHub Actions 배포 검증
- `v2.0.0` release candidate
- 설치·업데이트 smoke test
- 세 종류 Pilot Goal 수행

Pilot 유형:

1. 작은 버그 수정
2. 일반 기능 개발
3. 여러 Plan이 필요한 중대형 기능

성공 후:

- Legacy workflow Skill을 Global catalog에서 제거
- 필요하면 skills.sh catalog 노출과 native provider plugin을 별도 Work Packet으로 검토

---

## 10. 테스트 및 검증 전략

### 10.1 Distribution 검증

- Skill directory와 name 일치
- YAML frontmatter 유효성
- 필요한 resource 존재
- cross-skill 상대 경로 금지
- 생성된 resource와 authoring source Hash 일치
- Legacy Skill 미노출
- Codex와 Claude Code 설치 위치 smoke test

### 10.2 Contract 검증

- 필수 section과 Metadata
- 승인 상태 전이
- canonical contract hash 안정성
- Work ID 중복 방지
- dependency topological sort와 cycle 탐지
- 허용된 Plan status만 사용

### 10.3 Runtime 검증

- Goal 미활성 상태에서는 구현 거부
- 승인 전 또는 Hash Drift 상태에서는 구현 거부
- 기존 dirty change 보존
- Targeted → Feature → Fast suite 순서 준수
- Live와 Eval 기본 비활성
- Hard Stop 외 불필요한 질문 0회
- Full suite는 원칙적으로 Goal당 1회

### 10.4 Review와 Maintenance 검증

- Markdown과 HTML 내용 일치
- 외부 입력 HTML escape
- Durable 문서의 Work link 0개
- Archive 상태 및 보존기한 판정
- 삭제는 별도 Apply와 승인 없이는 실행되지 않음

---

## 11. 주요 위험과 대응

| 위험 | 대응 |
| --- | --- |
| `npx skills`가 공통 root resource를 설치하지 않음 | 각 Skill을 자기완결적으로 패키징하고 generated resource Hash 검증 |
| Legacy Skill도 installer가 발견함 | Legacy의 `SKILL.md`를 비활성 이름으로 보존하고 list test 추가 |
| 승인 후 상태 갱신으로 contract hash가 변함 | 승인 대상 필드와 runtime 상태 필드를 분리해 canonicalize |
| Goal Mode 밖에서 execute Skill이 실행됨 | Goal state preflight 실패 시 source mutation 금지 |
| 기존 dirty change를 Agent 변경으로 오인 | 실행 시작 시 baseline을 기록하고 변경 소유권을 분리 |
| Global Instruction 설치가 사용자 설정을 덮어씀 | setup에서 diff를 제공하고 별도 명시적 승인 요구 |
| HTML Review가 untrusted text를 실행함 | script 없는 정적 HTML과 escaping 사용 |
| Archive 자동 삭제가 복구 불가능한 손실을 만듦 | report-only 기본값, archive → trash → 승인된 delete |
| Provider마다 Skill discovery가 다름 | CI에서 Codex와 Claude Code target 설치 smoke test |
| V2가 전문 Skill까지 불필요하게 변경함 | Scope inventory와 excluded-path 검사를 Review gate에 포함 |

---

## 12. 전체 완료 조건

V2 구축은 다음 조건을 모두 만족해야 완료다.

- `npx skills@latest add young-sub/Skill_Management`에서 Skill과 Agent Provider를 선택해 설치할 수 있다.
- 사용자가 Skill 파일을 직접 복사하지 않아도 된다.
- Core Skill 7개가 설치 후 자기완결적으로 동작한다.
- `setup-agent-harness`가 실제 Repository evidence로 프로젝트를 설정한다.
- `design-goal`이 승인 가능한 Contract와 Goal declaration payload를 만든다.
- 사용자가 직접 선언한 Codex `/goal` 안에서 `execute-codex-goal`이 동작한다.
- 활성 Goal이나 유효한 승인이 없으면 구현을 시작하지 않는다.
- Hard Stop 외에는 승인된 범위의 세부 질문으로 Goal을 중단하지 않는다.
- Completion Review가 계획, 결과, 검증, 미검증, 잔여 위험을 사람이 이해할 수 있게 표시한다.
- `AGENTS.md`와 `CLAUDE.md` Drift가 없다.
- Durable 문서의 `.work/` 참조가 없다.
- 완료된 Work와 Worktree 잔존물이 없다.
- 전문 Skill은 기능 변경 없이 유지된다.
- 세 종류 Pilot이 성공하고 측정 결과가 기록된다.

---

## 13. 다음 세션 시작 절차

다음 구현 세션은 아래 순서로 시작한다.

1. `git status`, 현재 diff, 삭제된 Skill 두 개의 의도를 확인하되 임의로 복원하지 않는다.
2. `skill_recreate_plan.md`와 이 문서를 읽고 상충하는 부분은 이 문서의 최신 결정을 우선한다.
3. `npx skills`의 현재 local source 설치와 `--list` 동작을 read-only 또는 임시 경로에서 검증한다.
4. 현재 Skill inventory를 교체, 호환 검토, 제외 세 그룹으로 기계적으로 검증한다.
5. WP-01의 변경 파일 목록과 삭제·이동 대상을 제시한다.
6. Legacy 이동과 Root instruction 변경은 사용자 승인 후 수행한다.
7. 배포 검증 test를 먼저 실패시키고 WP-01 구현을 시작한다.
8. WP-01 완료 후 관련 문서와 verification evidence를 동기화한다.

다음 세션의 첫 구현 범위는 WP-01로 제한한다. Goal execution Skill을 먼저 작성하지 않는다. 설치 단위와 resource 경계가 확정되지 않으면 이후 모든 Skill 구조를 다시 변경해야 하기 때문이다.

---

## 14. 확정된 결정과 미결정 사항

### 확정된 결정

- 현재 repo를 Personal Agent Harness Source 저장소로 사용한다.
- Goal은 사람이 `/goal`로 선언한다.
- Harness는 Goal 선언 wrapper를 만들지 않는다.
- `execute-codex-goal`은 활성 Goal 안에서만 실행한다.
- 설치는 `npx skills` 기반 provider 선택형 설치를 우선한다.
- 리팩터링 범위는 Agent-driven development Core Workflow로 한정한다.
- Finance, Frontend, Artifact 등 전문 Skill은 Core 리팩터링에서 제외한다.
- Issue와 PR은 선택 Adapter이며 Core Workflow의 필수 조건이 아니다.
- Legacy는 Pilot 전에 삭제하지 않는다.

### 구현 중 확정할 사항

- GitHub repository 이름을 `Skill_Management`로 유지할지 `personal-agent-harness`로 변경할지
- 공개 License
- skills.sh catalog 등록 절차와 필요성
- Native Codex 또는 Claude plugin을 V2.1 범위로 만들지
- Global Instruction을 setup Skill이 설치할지, 별도 opt-in command로 분리할지
- Legacy 보존 형식을 rename, archive directory, release tag 중 무엇으로 할지

위 항목은 WP-01에서 조사하고 권장안을 제시한다. Remote rename, 공개 배포, License 변경, Global home 수정, Legacy 삭제는 사용자 승인 없이 수행하지 않는다.
