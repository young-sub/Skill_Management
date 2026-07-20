---
title: "WP-20260720-005: Verification And Evidence Hardening"
status: confirmed
labels:
  - test/eval
  - diagnostics
  - docs
created_at: 2026-07-20
---

# WP-20260720-005: Verification And Evidence Hardening

## Korean Summary (non-normative)

### 목적

현재 Harness V2의 distribution, pilot, install evidence가 실제 검증 범위보다 강하게 해석되지 않도록 validator의 탐지 범위를 넓히고 모든 evidence를 정확한 Git revision에 결박한다.

### 핵심 구현 사항

self-containment 검사를 절대경로·URI·cross-skill·reparse 경계까지 강화하고, pilot 기본 실행을 tracked 문서 무변경 방식으로 전환한다. install/update evidence에는 commit/tree/tool identity를 기록하며 remote GitHub update는 별도 승인 전까지 계속 `not_verified`로 유지한다.

> This Korean summary is for review speed only. If it conflicts with the English canonical sections, linked source-of-truth docs, or repository rules, the English canonical sections and source-of-truth docs prevail.

## Metadata

- Source: independent review follow-up recommendations
- Tracker: `local_markdown`
- Durable tracker: this file
- Intake mode: `docs_grill_preflight`
- Intent confidence: high
- Status: `confirmed`
- Dependency: independent of WP-003 implementation; brownfield acceptance fixtures should reuse its scenarios when available

## Background

현재 로컬 검증은 unit tests, resource sync, distribution validation, three pilots를 통과한다. 그러나 검토에서 다음 evidence-quality gap이 확인됐다.

- self-containment validator는 제한된 text extension의 `../` 참조를 중심으로 검사한다.
- absolute path, `file:` URI, repository-root reference, cross-skill dependency, reparse escape를 포괄적으로 증명하지 않는다.
- pilot runner는 실행 시간 측정값을 tracked report/artifact에 다시 기록해 단순 검증이 dirty worktree를 만든다.
- local install evidence는 성공 내용을 기록하지만 exact Git commit/tree identity가 없어 현재 HEAD와 직접 결박되지 않는다.
- remote GitHub-backed native update는 의도적으로 `not_verified`이며 별도 external approval이 필요하다.
- 일부 archived Work Packet capsule은 역사적 phase 값과 최종 close 결과가 같은 문서에 있어 현재 상태로 오독될 수 있다.

## Purpose

검증 결과의 핵심 속성을 다음과 같이 강화한다.

1. validator가 주장하는 범위와 실제 탐지 범위가 일치한다.
2. read-only verification은 기본적으로 tracked files를 변경하지 않는다.
3. evidence는 exact revision, tree, toolchain, command, output artifact와 결박된다.
4. local-source evidence와 remote-source evidence를 혼동하지 않는다.
5. historical records는 snapshot과 final status를 명확히 구분한다.

## Current State

- public catalog와 inventory는 18 public/12 legacy로 일치한다.
- resource map과 generated hash drift 검사는 구현돼 있다.
- distribution validator는 legacy discoverability와 일부 relative escape를 차단한다.
- pilots는 실제 subprocess checks를 수행하지만 tracked output에 nondeterministic duration을 기록한다.
- release candidate metadata는 remote GitHub update를 정직하게 `not_verified`로 표시한다.
- external smoke rerun은 explicit approval이 필요한 별도 gate다.

## Ideal Direction

```text
verification command
  -> immutable execution context
  -> temp/raw evidence
  -> deterministic normalized summary
  -> revision-bound evidence manifest
  -> optional explicit baseline update
```

검증 command는 기본적으로 observer여야 한다. tracked baseline/report 갱신은 `--update-baseline` 같은 별도 명령과 의도적 review를 필요로 한다.

## Goal

Distribution self-containment, pilot reproducibility, install evidence provenance를 하나의 verification-trust capability로 강화한다.

## Non-goals

- 이번 WP에서 live GitHub Release/tag 생성
- 승인 없이 network install/update 수행
- 모든 programming language의 semantic import resolver 구현
- arbitrary binary content 분석
- archived evidence의 역사적 수치 재작성
- WP-003/004 brownfield bootstrap 구현

## Source Of Truth

- Distribution validator: `scripts/validate-distribution.ps1`
- Validator tests: `tests/distribution/test_validate_distribution.py`
- Pilot runner: `scripts/run-v2-pilots.py`
- Pilot tests: `tests/release/test_v2_pilots.py`
- Install smoke: `scripts/test-install.ps1`
- Release metadata: `distribution/release-candidate.json`
- Evidence: `distribution/evidence/`

## Implementation Logic

### Self-containment rule model

검사는 단일 regex가 아니라 rule ID 기반 finding을 출력한다.

| Rule ID | Finding |
|---|---|
| `SC_RELATIVE_ESCAPE` | Skill root 밖으로 나가는 relative reference |
| `SC_ABSOLUTE_PATH` | machine-specific absolute path |
| `SC_FILE_URI` | `file:` URI dependency |
| `SC_REPO_ROOT_REFERENCE` | install tree에 포함되지 않는 repo-root resource 참조 |
| `SC_CROSS_SKILL_REFERENCE` | 다른 Skill directory에 대한 runtime dependency |
| `SC_MISSING_RESOURCE` | declared/referenced local resource 부재 |
| `SC_REPARSE_ESCAPE` | symlink/junction/reparse resolution이 Skill root 밖을 가리킴 |

각 finding에는 skill, source path, locator, normalized target, severity, evidence를 포함한다. Source text는 untrusted input이며 실행하지 않는다.

Textual detector는 Markdown link, common path token, JSON/YAML string에 대한 conservative detection을 사용한다. False positive 가능성이 있는 rule은 명시적 allowlist file과 reason을 요구하며, inline ignore comment로 validator를 우회하지 않는다.

Manifest closure 검사는 `authoring/resource-map.json` 및 public resource manifest가 선언한 source/target을 실제 tree와 비교한다. installed Skill이 필요로 하는 resource가 catalog package tree 안에 존재하는지 complete-tree 관점으로 확인한다.

### Pilot execution modes

Pilot runner를 두 모드로 분리한다.

```text
python scripts/run-v2-pilots.py
  -> temp directory에 raw 결과 생성
  -> deterministic summary를 stdout 또는 temp report로 반환
  -> tracked docs mutation 0

python scripts/run-v2-pilots.py --update-baseline
  -> explicit baseline update
  -> normalized durations 또는 duration 제외
  -> changed paths와 revision을 출력
```

Default mode 전후에 tracked file hash snapshot을 비교해 zero mutation을 테스트한다. Runtime duration은 pass/fail evidence에는 남길 수 있지만 committed baseline identity에는 포함하지 않거나 stable bucket/summary로 정규화한다.

### Revision-bound evidence manifest

Install/pilot evidence 공통 필드:

```text
schema_version
generated_at
repository
git_commit
git_tree
git_dirty
branch
command
cwd
tool_versions
source_type
source_package
providers
public_skill_count
catalog_sha256
resource_manifest_sha256
result
unverified_checks
```

`git_dirty: true`인 evidence는 dirty path list와 관련성을 기록하며 release-candidate proof로 자동 승격하지 않는다. release metadata가 참조하는 evidence의 commit/tree가 현재 candidate와 다르면 validator가 `stale_evidence`를 보고한다.

### Local and remote evidence separation

- `local_source_install_refresh`: repository-local package tree install/refresh proof
- `remote_github_update`: published GitHub source의 native update proof

한 evidence가 다른 evidence를 대체하지 않는다. Remote check는 승인 전까지 `not_verified`를 유지한다. 실행하려면 exact source ref, network approval, isolated provider homes, cleanup/recovery policy를 별도로 확인한다.

### Archive clarity

완료된 Work Packet에서 phase capsule이 역사적 snapshot이면 `snapshot_at`과 `superseded_by_close_report`를 표시한다. 최종 status는 문서 상단과 Close Report에서 일치시킨다. 과거 검증 수치와 decision history는 변경하지 않는다.

## Vertical Slices

### Slice 1: Self-containment validator expansion

- Rule ID finding model
- absolute/file URI/root/cross-skill/missing/reparse fixtures
- manifest closure and allowlist contract

### Slice 2: Read-only deterministic pilots

- default temp output
- explicit `--update-baseline`
- tracked zero-mutation sentinel
- nondeterministic duration normalization

### Slice 3: Revision-bound install and pilot evidence

- common provenance fields
- stale evidence detection
- local vs remote evidence separation
- dirty-tree behavior

### Slice 4: Durable-record clarity

- historical capsule marker
- final status consistency checks
- repository-doc regression tests

## Acceptance Criteria

- 모든 새 self-containment adversarial fixture가 기존 validator에서 RED이고 구현 후 fail-closed한다.
- legitimate in-skill relative resource는 허용된다.
- default pilot 실행 전후 `git status --porcelain`과 tracked hashes가 동일하다.
- `--update-baseline`만 tracked pilot artifacts를 변경한다.
- evidence manifest가 exact `git_commit`과 `git_tree`를 포함한다.
- release candidate와 evidence revision이 다르면 validation이 실패한다.
- local-source proof가 remote update proof로 표시되지 않는다.
- remote GitHub update는 실제 승인된 check가 통과하기 전까지 `not_verified`다.
- historical Work Packet 검증 수치는 보존되고 snapshot/final state만 명료해진다.

## Verification Plan

```powershell
python -m unittest tests.distribution.test_validate_distribution
python -m unittest tests.release.test_v2_pilots
python -m unittest tests.release.test_install_update
python -m unittest tests.distribution.test_repository_docs
python -m unittest discover -s tests -p "test_*.py"
powershell -NoProfile -File scripts/sync-skill-resources.ps1 -Check
powershell -NoProfile -File scripts/validate-distribution.ps1
git diff --check
```

Pilot read-only acceptance는 command 전후 tracked hash와 `git status --porcelain`을 비교한다.

외부 검증은 구현 완료와 local checks 통과 후에도 자동 실행하지 않는다. 별도 승인 시에만:

```powershell
powershell -NoProfile -File scripts/test-install.ps1 -VerifyUpdate
```

## Architecture Review Target

- validator rule coverage vs claim wording
- false-positive allowlist governance
- pilot baseline ownership and determinism
- evidence schema versioning and revision identity
- local/remote source distinction
- historical document immutability

## Risks And Approval Boundaries

- path scanners must not execute repository content.
- reparse inspection failure is not clean evidence; report unverified or fail closed according to rule severity.
- external install/update remains approval-gated.
- remote release/tag/push is out of scope.
- allowlist growth requires evidence, owner, and expiration/review reason.

## Proposed Shared Doc Updates

- `docs/architecture/skill-inventory.md`: validator guarantee wording update after implementation
- `README.md`: default pilot read-only behavior and evidence provenance
- `distribution/release-candidate.json`: evidence revision requirements
- archived Work Packets: append-only snapshot/final-state clarification

## Implementation Confirmation Brief

- Purpose: make release and validation claims revision-bound and reproducible.
- Core target: stronger self-containment rules, read-only pilots, provenance-rich evidence.
- Observable change: stale or incomplete evidence fails validation; ordinary pilots leave a clean tree.
- Will not change: no automatic network smoke or live release.
- Verification signal: adversarial validator fixtures, zero-mutation pilot test, stale-revision test.

## Confirmation Status

- Status: `confirmed`
- Evidence: user invoked `/goal` for sequential implementation of WP-003, WP-004, and WP-005 on 2026-07-20.

## Phase Handoff Capsule

- updated_at: 2026-07-20
- source_ref: this Work Packet
- updated_by: Codex main session
- phase: init
- scope: validator, pilot, and evidence trust hardening
- current gate: implementation confirmation
- accepted decisions: read-only pilots by default; revision-bound evidence; remote remains separately gated
- open decisions: none identified; user confirmation remains
- files read: distribution validator/tests, pilot/release evidence pointers, tracker/workflow config
- files changed: this isolated Work Packet
- tracker/PR/doc mutations: local Work Packet only
- tracker_channel: none
- git_publish_state: local_only
- tracker_publish_state: local_pending
- published_body_ref:
- verification evidence: documentation checks pending
- delegated evidence: prior independent multi-agent review
- risks: false positives from broader path detection
- next mode: ready after confirmation
- next stop condition: scope adjustment or confirmation withheld

## Close Report Skeleton

- Outcome:
- Validator rules added:
- Pilot determinism evidence:
- Revision-bound evidence:
- External checks run/unrun:
- Docs updated:
- Remaining risks:
