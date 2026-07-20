---
title: "WP-20260720-003: Brownfield Discovery And Reconciliation"
status: completed
labels:
  - architecture
  - feature
  - test/eval
created_at: 2026-07-20
---

# WP-20260720-003: Brownfield Discovery And Reconciliation

## Korean Summary (non-normative)

### 목적

기존 프로젝트에 Agent Harness를 적용하기 전에, 이미 존재하는 테스트·문서·CI·instruction surface와 Git 경로 정책을 읽기 전용으로 조사하고 사람이 검토할 수 있는 migration proposal을 만든다.

### 핵심 구현 사항

현재의 단순 분류와 전체 파일 충돌 보고를 `Brownfield Inventory -> Authority Resolution -> Router Proposal -> TESTING Merge Proposal -> Path Policy` 흐름으로 확장한다. 이 Work Packet은 대상 프로젝트를 변경하지 않으며, 실제 적용은 WP-20260720-004가 담당한다.

> This Korean summary is for review speed only. If it conflicts with the English canonical sections, linked source-of-truth docs, or repository rules, the English canonical sections and source-of-truth docs prevail.

## Metadata

- Source: 2026-07-20 independent multi-agent implementation review
- Tracker: `local_markdown`
- Durable tracker: this file
- Intake mode: `docs_grill_preflight`
- Intent confidence: high
- Status: `completed`
- Parallel-safe init: yes
- Isolated write surface: this Work Packet only
- Dependency: none
- Enables: `WP-20260720-004`

## Background

Harness V2의 `setup-agent-harness`는 신규 저장소와 단순 partial repository에 대해 다음을 안정적으로 제공한다.

- `NEW_UNCONFIGURED`, `EXISTING_PARTIAL`, `EXISTING_OVERGROWN`, `DRIFT_REPAIR` 분류
- deterministic dry-run과 conflict diff
- 기존 파일 conflict 시 무변경 중단
- 승인된 clean apply
- `AGENTS.md`/`CLAUDE.md` mirror, `TESTING.md`, `.harness/project.yaml`, `.work/` 생성

그러나 현재 helper의 분류는 주로 파일 존재, AGENTS line count, instruction hash를 사용한다. 기존 CI, test manifest, documentation hierarchy, Git tracking/ignore state를 의미적으로 inventory하지 않는다. 따라서 `EXISTING_PARTIAL`은 migration readiness가 아니라 단순히 “일부 표식이 존재한다”는 뜻에 가깝다.

## Purpose

Brownfield repository에 대한 모든 mutation 앞에 신뢰할 수 있는 read-only reconciliation contract를 둔다.

이 contract는 다음 질문에 evidence pointer와 confidence를 붙여 답해야 한다.

1. 기존 source of truth는 어디에 있는가?
2. 실제 verification command는 어디에서 정의되고 사용되는가?
3. 어떤 문서를 새로 만들 필요 없이 router가 가리켜야 하는가?
4. 기존 `TESTING.md`에서 무엇을 보존하고 무엇을 제안해야 하는가?
5. 각 Harness 경로는 tracked, local-only, unknown 중 무엇이어야 하는가?
6. 현재 Git ignore/tracking 상태가 의도한 경로 정책과 충돌하는가?

## Current State

- `classify()`는 제한된 marker와 instruction/config drift를 검사한다.
- verification command는 caller가 `--verify-command-json`으로 전달하며 자동 discovery 결과가 아니다.
- 기존 `AGENTS.md` 또는 `CLAUDE.md` 하나를 authoritative bytes로 선택해 두 파일에 동일하게 제안한다.
- `TESTING.md`는 고정 template과 다르면 whole-file conflict다.
- plan action vocabulary는 `create`, `append`, `create_directory`, `conflict` 수준이다.
- `git ls-files`, `git check-ignore`, nested repository/submodule boundary를 사용하는 path classification이 없다.
- `.harness/project.yaml`은 생성하지만 `.harness/`를 tracked 대상으로 선언하거나 ignore 충돌을 차단하지 않는다.

## Ideal Direction

`setup-agent-harness`는 greenfield generator와 brownfield reconciler를 명확히 구분한다.

```text
greenfield plan
  -> deterministic desired files
  -> existing conflict-safe apply

brownfield reconcile
  -> evidence inventory
  -> authority candidates
  -> proposed routers and merge hunks
  -> path policy matrix
  -> reviewable immutable PlanArtifact
  -> no repository mutation
```

Brownfield mode의 기본 결과는 “적용”이 아니라 “검토 가능한 proposal”이다. confidence가 낮거나 authority가 충돌하면 추측하지 않고 `human_decision_required`를 출력한다.

## Goal

`python scripts/bootstrap_project.py reconcile --root <repository-root>`가 기존 프로젝트를 변경하지 않고 deterministic JSON report를 stdout으로 생성하도록 한다. 선택적인 `--report <path>`는 사용자가 명시한 경로에 동일 내용을 기록한다.

## Non-goals

- 임의 Markdown prose의 semantic merge
- arbitrary YAML schema의 범용 round-trip 편집
- 발견한 command의 자동 실행
- Git index mutation 또는 `git add`
- `.gitignore` 변경
- 기존 source-of-truth 문서 이동·삭제·이름 변경
- submodule 또는 nested repository 내부의 자동 migration
- tracker, provider global configuration, secret/env 파일 변경

## Source Of Truth

- Completed V2 record: `docs/archive/plans/harness_v2_implementation_plan.md`
- Current bootstrap contract: `skills/setup-agent-harness/SKILL.md`
- Canonical helper: `authoring/scripts/bootstrap_project.py`
- Generated copy: `skills/setup-agent-harness/scripts/bootstrap_project.py`
- Project templates: `authoring/templates/project/`
- Existing tests: `tests/harness/test_setup_agent_harness.py`

## Proposed Architecture

### Domain types

```text
DiscoveryEvidence
  path
  evidence_kind
  detector
  locator
  confidence
  notes

AuthorityCandidate
  authority_kind
  path
  precedence_basis
  confidence
  conflicts

PathPolicyEntry
  path
  desired_state: tracked | local-only | unknown
  current_state: tracked | untracked | ignored | absent | outside-boundary
  ignore_source
  evidence
  proposed_action
  approval_required

ReconciliationProposal
  router_proposals
  testing_merge_proposal
  path_policy
  blocking_decisions
  warnings

PlanArtifact
  schema_version
  mode
  repository_identity
  discovery_fingerprint
  inputs
  proposal
```

JSON은 canonical key ordering을 사용하고 timestamp를 identity hash에서 제외해 동일 repository state에서 동일 fingerprint를 만든다.

### Detector model

각 detector는 standard-library 기반의 read-only function이며 `(root) -> list[DiscoveryEvidence]` 계약을 갖는다. detector 실패는 전체 discovery를 숨기지 않고 structured warning으로 기록한다.

초기 detector 집합:

- Instructions: root/nested `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, Cursor/Gemini compatibility surfaces
- Verification docs: `TESTING.md`, `CONTRIBUTING.md`, README verification sections, runbooks
- Build/test manifests: `pyproject.toml`, `package.json`, `Makefile`, `Cargo.toml`, `go.mod`, solution/project files
- CI: `.github/workflows/`, GitLab CI, Azure Pipelines, other repo-evidenced CI entrypoints
- Architecture/domain: `CONTEXT.md`, `docs/architecture*`, `docs/adr/`, `docs/agents/domain.md`
- Commands: manifest scripts and conservative CI `run` entries, including exact source pointer; never execute them
- Git boundaries: repository root, submodules, nested `.git`, symlink/junction/reparse components

Unknown formats remain evidence records with `confidence: low`; they are never parsed as executable instructions.

### Authority resolution

Authority selection uses explicit precedence evidence, not filename preference alone.

1. Existing repo instruction explicitly naming a canonical document
2. CI or build manifest actively invoking a verification command
3. Dedicated current documentation such as `TESTING.md` or architecture index
4. README/CONTRIBUTING guidance
5. Convention-only candidate

Conflicting authorities remain multiple candidates and create a blocking decision. The reconciler must not silently select one.

### Router proposal

Router generation follows these rules.

- Preserve existing domain, architecture, testing, and workflow documents byte-for-byte.
- Propose a root `AGENTS.md` containing repository-specific pointers and commands only.
- Generate nested router proposals only when a subtree has materially different commands or constraints.
- Keep `CLAUDE.md` byte-identical to the proposed root router when the repository adopts the Harness mirror invariant.
- Show `preserved`, `referenced`, `new-router-line`, and `unresolved` items separately.
- Do not inline or copy the body of existing source-of-truth documents.

### TESTING merge proposal

The reconciler does not produce a blindly rewritten `TESTING.md`. It returns sections:

```text
preserved_sections
detected_commands
command_evidence
proposed_additions
conflicting_commands
human_decisions_required
unified_diff_preview
```

Commands detected in CI/manifests are candidates, not verified commands. A later apply may record them as `discovered` but must not label them `passed` until execution succeeds.

### Path policy

The default desired policy is:

| Path | Desired state | Rule |
|---|---|---|
| `AGENTS.md` | tracked | repository instruction router |
| `CLAUDE.md` | tracked | provider compatibility mirror when adopted |
| `TESTING.md` or existing verification source | tracked | durable verification contract |
| `.harness/project.yaml` | tracked | machine-readable Harness configuration |
| `.harness/` temporary state | prohibited | runtime state belongs under `.work/` |
| `.work/**` | local-only | ephemeral active/archive/trash/transaction state |
| `agent-env.*.md` | local-only | local tracker-channel profile |

Git state is resolved through Git plumbing and ignore source evidence. Exact string matching against `.gitignore` is insufficient.

## Vertical Slices

### Slice 1: Brownfield evidence inventory

- Add detector interfaces and repository-boundary checks.
- Emit source-of-truth, command, CI, docs, and path evidence.
- Add realistic Python, Node, mixed CI, nested-instruction, and conflicting-doc fixtures.

### Slice 2: Authority and router proposals

- Rank candidates with evidence.
- Generate thin root/nested router proposals without duplicating existing docs.
- Block ambiguous authority selection.

### Slice 3: TESTING reconciliation

- Preserve existing bytes and parse only explicitly supported headings/command forms.
- Produce merge hunks and unresolved conflicts.
- Distinguish `discovered`, `verified-passed`, and `rejected` command states.

### Slice 4: Git path policy report

- Classify desired/current states using Git plumbing.
- Detect ignore negation, global excludes, tracked-but-ignored paths, submodules, nested repositories, and `.harness/` conflicts.
- Produce an immutable `PlanArtifact` for WP-004 consumption.

## Acceptance Criteria

- `reconcile` makes zero target-repository mutations when writing only to stdout.
- Repeated runs against identical bytes and Git state produce the same discovery fingerprint.
- Existing source-of-truth documents are referenced, not copied into new docs.
- Existing `TESTING.md` prose is byte-preserved in the proposal inputs.
- Every proposed test command includes a source pointer and confidence.
- Conflicting commands or authorities are reported as blocking decisions.
- Every Harness-owned path has desired/current state and evidence.
- Ignored `.harness/project.yaml` is a High blocking finding.
- `.work/` is proposed as local-only but `.gitignore` is never changed.
- Nested repositories and submodules are reported and excluded from automatic migration.
- Existing greenfield `plan`, `apply`, and `validate` behavior remains backward-compatible.

## Verification Plan

TDD starts with failing brownfield fixtures, followed by:

```powershell
python -m unittest tests.harness.test_setup_agent_harness
python -m unittest discover -s tests -p "test_*.py"
powershell -NoProfile -File scripts/sync-skill-resources.ps1 -Check
powershell -NoProfile -File scripts/validate-distribution.ps1
git diff --check
```

Add a mutation sentinel test that snapshots every file before and after `reconcile` and proves equality.

## Architecture Review Target

- Detector isolation and failure behavior
- Deterministic PlanArtifact schema
- Git boundary handling
- Router ownership vs existing source-of-truth ownership
- Conservative parsing and untrusted-repository-content handling
- Backward compatibility of existing greenfield CLI

## Risks And Approval Boundaries

- Repository content is untrusted input; discovery never executes it.
- Symlink, junction, reparse, nested repo, or root escape produces a blocking finding.
- Writing `--report` requires an explicit path and containment check.
- No external/network command is required.
- Any proposed global Git ignore or provider configuration change is out of scope.

## Proposed Shared Doc Updates

- `skills/setup-agent-harness/SKILL.md`: document greenfield vs brownfield modes at close.
- `docs/architecture/skill-inventory.md`: record the brownfield capability after implementation.
- `README.md`: add reconciliation-first usage after implementation.

## Implementation Confirmation Brief

- Purpose: make brownfield readiness evidence-backed and reviewable before mutation.
- Core target: read-only discovery and reconciliation PlanArtifact.
- Observable change: `reconcile` reports authorities, router/TESTING proposals, path policy, and blockers.
- Will not change: existing greenfield apply behavior and any target repo files.
- Verification signal: deterministic zero-mutation fixtures and full repository checks.

## Scoped Overrides

- Implementation branch: the user explicitly directed implementation on `develop` on 2026-07-20. This overrides the default Work Packet implementation-branch policy for WP-003 through WP-005; `main` remains protected and no publish action is authorized.

## Confirmation Status

- Status: `confirmed`
- Evidence: user invoked `/goal` for sequential implementation of WP-003, WP-004, and WP-005, then explicitly selected `develop` as the implementation branch on 2026-07-20.

## Phase Handoff Capsule

- updated_at: 2026-07-20
- source_ref: this Work Packet
- updated_by: Codex main session
- phase: close
- scope: read-only brownfield discovery and reconciliation
- current gate: completed; WP-004 dependency released
- accepted decisions: existing docs are referenced; `.harness/` tracked; `.work/` local-only; no mutation in this WP
- open decisions: none identified
- files read: bootstrap helper/skill/tests, completed V2 plan, tracker/workflow config
- files changed: canonical/generated bootstrap helper, brownfield tests, setup skill contract, README, architecture inventory, resource manifests, this Work Packet
- tracker/PR/doc mutations: local Work Packet only
- tracker_channel: none
- git_publish_state: local_only
- tracker_publish_state: local_pending
- published_body_ref:
- verification evidence: final focused brownfield suite 10/10 passed; final repository suite 122/122 passed; resource sync, distribution, and diff checks passed
- delegated evidence: `/root/wp003_baseline_verifier` executed RED/GREEN; independent reviewer `/root/wp003_independent_review` found CRLF, Git fail-open, authority, and tracked-ignore gaps, verified their remediation, and returned PASS with no remaining High/Medium findings
- risks: conservative detection may require human resolution for uncommon toolchains
- next mode: goal close
- next stop condition: final evidence or repository verification failure

## Close Report

- Final status: completed
- Outcome: completed. `reconcile` emits a deterministic, read-only, digest-bound PlanArtifact.
- Implemented slices: evidence inventory; authority and thin router proposals; byte-preserving TESTING merge proposal; Git-backed path policy and repository boundaries; apply-ready immutable mutation contract.
- Verification evidence: 10/10 final focused tests and 122/122 final repository tests passed; resource drift, distribution, and diff checks passed.
- Independent review: PASS after remediation of byte preservation, Git-unavailable and tracked-ignore fail-closed behavior, prohibited path inspection, rank-2 CI authority, unknown evidence retention, and ambiguous-router suppression.
- Architecture review: detectors are isolated functions, repository content is never executed, nested/reparse boundaries are excluded, canonical authoring remains the single source copied into the public Skill.
- Docs updated: `skills/setup-agent-harness/SKILL.md`, `README.md`, `docs/architecture/skill-inventory.md`.
- Remaining risks: conservative command detection intentionally creates human decisions for ambiguous multi-command repositories.
- Follow-up: WP-004 may proceed against schema version 1 and exact `plan_sha256`.
