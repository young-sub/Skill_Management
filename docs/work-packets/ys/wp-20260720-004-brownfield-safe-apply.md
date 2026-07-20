---
title: "WP-20260720-004: Brownfield Approved Safe Apply"
status: in-progress
labels:
  - architecture
  - feature
  - approval-required
created_at: 2026-07-20
---

# WP-20260720-004: Brownfield Approved Safe Apply

## Korean Summary (non-normative)

### 목적

사람이 검토한 brownfield reconciliation plan과 실제 apply를 동일한 artifact digest로 결박하고, 도중 상태 변경이나 일부 파일만 적용되는 실패를 차단한다.

### 핵심 구현 사항

WP-20260720-003의 immutable PlanArtifact를 입력으로 받아 precondition을 다시 검증하고, 경로별 승인을 확인한 뒤 recoverable transaction으로 변경한다. `.harness/`는 tracked 대상으로 강제하고 local-only allowlist에 승인된 경로만 `.gitignore`에 반영한다.

> This Korean summary is for review speed only. If it conflicts with the English canonical sections, linked source-of-truth docs, or repository rules, the English canonical sections and source-of-truth docs prevail.

## Metadata

- Source: WP-20260720-003 output contract
- Tracker: `local_markdown`
- Durable tracker: this file
- Intake mode: `architecture_first`
- Intent confidence: high for direction, blocked on upstream schema
- Status: `in-progress`
- Dependency: WP-20260720-003 must close with a stable PlanArtifact schema
- Enables: unattended apply only for fully approved, conflict-free plans

## Background

현재 bootstrap은 사용자가 dry-run을 본 뒤 `apply --approve`를 실행하도록 안내하지만, 승인한 plan 파일이나 digest를 받지 않는다. apply는 repository를 다시 검사하고 새 plan을 계산한다. plan과 apply 사이에 repository state가 변하면 사용자가 본 내용과 실제 적용 내용이 달라질 수 있다.

또한 desired files와 `.gitignore`, directory를 순서대로 기록한다. write 중간에 process crash, permission failure, disk error가 발생하면 일부만 적용될 수 있다. 이는 clean greenfield에서는 드물지만 다양한 기존 상태를 가진 brownfield에서는 중요한 failure mode다.

## Purpose

Apply의 승인 대상, 입력 상태, mutation set, recovery behavior를 하나의 explicit contract로 만든다.

완료 후에는 다음 문장이 참이어야 한다.

> The exact reviewed plan, and only that plan, was applied to the exact repository state it described; otherwise no durable partial state remains or recovery is required before further use.

## Current State

- `--approve`는 boolean이며 특정 plan을 식별하지 않는다.
- preliminary plan과 verification 후 plan을 apply 시점에 재생성한다.
- input file hash, Git state, ignore source가 approval artifact에 고정되지 않는다.
- multi-file writes는 transaction journal이나 rollback 없이 순차 수행된다.
- `.gitignore`는 `.work/` exact line을 append한다.
- `.harness/project.yaml`이 ignored인지 차단하지 않는다.
- local-only 승인 단위가 없고 apply 전체만 승인한다.

## Ideal Direction

```text
WP-003 reconcile
  -> PlanArtifact + digest
  -> human review
  -> explicit plan/path approvals
  -> precondition revalidation
  -> transaction prepare
  -> staged writes
  -> commit or rollback/recover
  -> post-apply validation
  -> ApplyReport bound to the same digest
```

Greenfield의 기존 간단한 workflow는 유지하되 brownfield apply는 반드시 serialized PlanArtifact를 사용한다.

## Goal

다음과 같은 명시적 apply contract를 제공한다.

```text
python scripts/bootstrap_project.py apply-plan \
  --root <repository-root> \
  --plan <plan.json> \
  --approve-plan-sha256 <digest> \
  --approve-local-only .work/ \
  --approve-local-only agent-env.*.md
```

승인하지 않은 local-only path, changed precondition, unresolved conflict, ignored tracked path가 하나라도 있으면 mutation 전에 중단한다.

## Non-goals

- arbitrary conflict 자동 해결
- Git commit, staging, push 또는 branch 생성
- provider global configuration 변경
- global Git excludes 변경
- submodule/nested repository migration
- semantic merge가 불확실한 Markdown/YAML 자동 편집
- true cross-filesystem atomicity 보장
- destructive deletion 또는 legacy document 제거

## Source Of Truth

- Upstream PlanArtifact: `docs/work-packets/ys/wp-20260720-003-brownfield-discovery-reconciliation.md`
- Canonical bootstrap helper: `authoring/scripts/bootstrap_project.py`
- Public skill contract: `skills/setup-agent-harness/SKILL.md`
- Project configuration schema: `authoring/templates/project/project.yaml`

## PlanArtifact Apply Contract

필수 필드:

```text
schema_version
mode: brownfield-reconcile
plan_id
plan_sha256
repository_identity
repository_root_fingerprint
created_from_git_head
inputs[]
  path
  existence
  content_sha256
  git_state
  ignore_source
mutations[]
  path
  operation
  before_sha256
  after_sha256
  desired_state
  approval_class
blocking_decisions[]
warnings[]
```

`plan_sha256`는 timestamp, display formatting, report output path를 제외한 canonical JSON bytes로 계산한다.

## Approval Model

승인은 세 층으로 분리한다.

1. **Plan approval**: `--approve-plan-sha256`가 exact plan digest와 일치해야 한다.
2. **Path-class approval**: local-only mutation은 allowlist entry별 승인이 필요하다.
3. **Risk approval**: conflict resolution, deletion, global configuration은 이 WP에서 지원하지 않고 stop한다.

지원되는 초기 local-only allowlist는 `.work/`와 이미 repo policy에 선언된 `agent-env.*.md`뿐이다. repository-specific 추가 경로는 PlanArtifact에 근거와 함께 표시하되 새로운 명시적 approval argument 없이는 변경하지 않는다.

## Tracked And Local-only Rules

| Desired state | Apply behavior |
|---|---|
| tracked | ignore되지 않아야 하며 apply report에 `must_be_committed`로 기록한다. 자동 `git add`는 하지 않는다. |
| local-only | 승인된 allowlist와 일치해야 하며 해당 ignore rule만 최소 변경한다. |
| unknown | apply 차단 |
| prohibited | apply 차단 |

`.harness/project.yaml`은 반드시 `tracked`다. global/local ignore 때문에 무시되면 자동 negation을 추가하지 않고 stop하여 ignore source와 해결 command proposal을 출력한다.

`.gitignore` 편집은 전체 파일 재작성 대신 expected before hash를 확인한 뒤 승인된 exact rule만 추가한다. 기존 ordering, comments, negations, encoding, newline을 보존한다.

## Transaction And Recovery Logic

Python standard library만 사용하며 “완전한 다중 파일 atomic write”라고 과장하지 않는다. 목표는 recoverable transaction이다.

### Prepare

- exact plan digest 검증
- repository identity/root containment 검증
- 모든 input existence/hash/Git state/ignore source 재검증
- write target symlink/junction/reparse 검증
- unresolved blocker가 0인지 확인
- transaction ID 생성
- before image와 intended after hash를 journal에 기록

### Stage

- 승인된 `.work/bootstrap-transactions/<transaction-id>/`에 staging과 journal 저장
- 같은 filesystem에서 temp file을 생성하고 flush/fsync 가능한 범위까지 수행
- 모든 staged bytes의 hash를 PlanArtifact와 비교
- 이 단계까지 target file은 변경하지 않음

### Commit

- 각 target을 `os.replace`로 교체
- 각 교체 후 journal state를 갱신
- directory creation과 `.gitignore` 최소 변경도 explicit operation으로 기록
- 실패 시 즉시 rollback을 시도하고 status를 `rolled_back` 또는 `recovery_required`로 기록

### Recover

```text
python scripts/bootstrap_project.py recover-apply \
  --root <repository-root> \
  --transaction <id> \
  --approve-recovery
```

- journal과 current hashes로 complete/rollback 가능성을 판정
- ambiguity가 있으면 파일을 추측해 덮어쓰지 않고 stop
- recovery가 끝나기 전에는 새 apply를 차단

### Finalize

- post-apply `validate`
- desired/current path policy 재검사
- `.harness/project.yaml`이 not ignored인지 확인
- tracked 대상 중 untracked/modified 파일을 `must_be_committed`로 보고
- transaction staging 정리는 report-only retention policy를 따른다
- ApplyReport에 plan digest, operation 결과, uncommitted tracked paths, verification 결과를 기록

## Idempotency

동일 plan을 이미 성공 적용한 상태에서 다시 실행하면:

- mutation count 0
- status `already_applied`
- `.gitignore` duplicate rule 0
- 새로운 transaction state를 남기지 않음

부분 적용이나 input drift가 발견되면 `already_applied`로 간주하지 않는다.

## Vertical Slices

### Slice 1: Exact-plan approval and preconditions

- Canonical plan digest와 input precondition 검증
- plan/apply mismatch와 TOCTOU regression fixtures
- unresolved/unknown path fail-closed behavior

### Slice 2: Path-scoped approval and Git policy

- tracked/local-only enforcement
- approved allowlist만 `.gitignore` 최소 수정
- `.harness/` ignored, negation, global excludes, tracked-but-ignored fixtures

### Slice 3: Recoverable transaction

- prepare/stage/commit journal
- write 단계별 injected failure
- rollback/recovery state machine
- symlink/junction/reparse containment 재검사

### Slice 4: Post-apply validation and idempotency

- ApplyReport
- `must_be_committed` tracked output
- second-run no-op
- incomplete transaction blocks new apply

## Acceptance Criteria

- 승인 digest와 plan bytes가 다르면 zero mutation이다.
- plan 이후 input file, Git state, ignore source 중 하나라도 바뀌면 zero mutation이다.
- 승인되지 않은 local-only rule은 추가되지 않는다.
- `.harness/project.yaml`이 ignored이면 apply가 중단된다.
- `.harness/`는 tracked desired state로 report되고 자동 `git add`하지 않는다.
- `.gitignore`의 기존 comments, negations, encoding, newline이 보존된다.
- 각 write 경계에 fault를 주입해 prior state 복구 또는 explicit `recovery_required`를 증명한다.
- incomplete transaction이 있으면 다음 apply가 중단된다.
- 동일 plan의 두 번째 apply는 no-op이다.
- greenfield CLI regression tests가 그대로 통과한다.

## Verification Plan

TDD fault-injection tests를 우선 작성한다.

```powershell
python -m unittest tests.harness.test_setup_agent_harness
python -m unittest discover -s tests -p "test_*.py"
powershell -NoProfile -File scripts/sync-skill-resources.ps1 -Check
powershell -NoProfile -File scripts/validate-distribution.ps1
git diff --check
```

Windows에서는 symlink/junction permission 차이를 고려해 가능한 reparse test와 platform skip 이유를 명시한다. skip을 pass로 보고하지 않는다.

## Architecture Review Target

- PlanArtifact compatibility/versioning
- approval identity and precondition completeness
- transaction state machine and recovery ambiguity
- Git ignore semantics and repository boundaries
- Windows/POSIX replacement behavior
- no automatic staging/commit boundary
- backward compatibility with greenfield apply

## Risks And Approval Boundaries

- Apply는 repository mutation이므로 exact plan confirmation 후에만 실행한다.
- deletion, global config, secrets, external service, Git index mutation은 지원하지 않는다.
- filesystem crash 중 recovery가 불가능한 경우를 숨기지 않고 `recovery_required`로 남긴다.
- WP-003 schema가 안정되기 전에는 구현을 시작하지 않는다.
- greenfield path까지 transaction engine으로 즉시 통합하지 말고 brownfield path에서 검증 후 별도 결정한다.

## Proposed Shared Doc Updates

- `skills/setup-agent-harness/SKILL.md`: `apply-plan`, exact digest approval, recovery workflow 추가
- `authoring/templates/project/AGENTS.md`: `.harness/` tracked와 `.work/` local-only 정책 명시
- `README.md`: greenfield/brownfield apply 경계와 approval 예시 추가

## Implementation Confirmation Brief

- Purpose: ensure reviewed plan identity and recoverable mutation.
- Core target: digest-bound, preconditioned, path-approved apply state machine.
- Observable change: stale or unapproved plans fail before mutation; partial failures become recoverable.
- Will not change: no automatic Git staging/commit, deletion, global config, or conflict guessing.
- Verification signal: TOCTOU, fault-injection, Git ignore, and idempotency tests.

## Scoped Overrides

- Implementation branch: the user explicitly directed implementation on `develop` on 2026-07-20. `main` remains protected and no publish action is authorized.

## Confirmation Status

- Status: `confirmed`
- Evidence: WP-003 closed with PlanArtifact schema version 1 and exact `plan_sha256`; the user confirmed sequential WP-003 through WP-005 implementation via `/goal`.

## Phase Handoff Capsule

- updated_at: 2026-07-20
- source_ref: this Work Packet
- updated_by: Codex main session
- phase: run
- scope: approved brownfield apply and recovery
- current gate: WP-004 TDD implementation
- accepted decisions: exact plan digest; path-scoped local-only approval; `.harness/` tracked; no auto git add
- open decisions: none; recovery journals remain under approved `.work/bootstrap-transactions/`
- files read: bootstrap helper/skill/tests, tracker/workflow config
- files changed: this isolated Work Packet
- tracker/PR/doc mutations: local Work Packet only
- tracker_channel: none
- git_publish_state: local_only
- tracker_publish_state: local_pending
- published_body_ref:
- verification evidence: documentation checks pending
- delegated evidence: prior independent multi-agent review
- risks: transaction recovery and cross-platform filesystem semantics
- next mode: close after implementation and verification
- next stop condition: transaction or precondition acceptance evidence incomplete

## Close Report Skeleton

- Outcome:
- Applied PlanArtifact schema version:
- Fault-injection evidence:
- Git path-policy evidence:
- Recovery/idempotency evidence:
- Docs updated:
- Remaining risks:
