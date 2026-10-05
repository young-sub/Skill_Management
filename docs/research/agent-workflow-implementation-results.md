# Agent workflow implementation and acceptance

Execution began 2026-10-05 on `wp-20261004-agent-coding-foundation` at `aa536876fb9f8922e0cade072469ddc9a51267df`, with a clean worktree. This implements the [execution prompt](agent-coding-next-session.md); the prior review-only restriction does not apply to this authorized implementation. Acceptance is in progress; this document does not declare the whole delegation system complete.

## Implementation and responsibility

- `authoring/skills/agent-workflow/SKILL.md` coordinates intent, selected procedures, relevant capabilities, evidence and unresolved work.
- `authoring/skills/setup-project-verification/SKILL.md` connects the first actual flow from existing product requirements and tools.
- `authoring/skills/maintain-project-verification/SKILL.md` owns product Feature/guide/command/UI drift, alongside the existing Harness mapping/cohort/retention owner when both are affected.
- Shared `authoring/references/project-verification.md` and `repair-and-reuse.md` are generated into self-contained Skill trees. Existing diagnose, UI capabilities, multi-agent review, capture and project adapters remain in use. Public catalog, inventory, Feature Map and active verification selector are updated together.

Source/generated distribution is distinct from temporary installation, product execution, actual Agent selection and operational application. No ordinary installation, global settings, original Labeler files/refs/DB, protected branch, push, deployment or remote migration is changed.

## Independent target and host

New evidence root: `.work/agent-workflow-pilot-20261005/`. These are temporary retained records; if removed, this document remains a historical summary, not reproducible raw evidence.

`export.json` identifies the independent `git archive` export from the previous isolated Labeler commit `ecd7db768aef3c17c0ffc9834759944cf013b0f0`. It contains 319 safe tracked files and no shared Git/origin, original database, dependencies or uncommitted files. `t1-fixture.json` records removal of only the new copy's previous pilot guide/routing/selectors, retaining original product requirements, native tests and drivers. Existing pilot/raw records remain unchanged.

Initial npm registry access failed with `EACCES` (owned `npm-cache/_logs/2026-10-05T03_01_55_340Z-debug-0.log`). A narrowly authorized `npm ci --cache ../npm-cache --no-audit --no-fund --fetch-retries=0` installed 331 packages from the lockfile. Local Skills CLI installation then verified 19 Skill trees for the temporary Codex/Claude project roots (`install-local.json`). No dependencies were copied from the original product.

`host-discovery/captures/03-app-server/` preserves fresh Codex 0.160.0 initialize and skills/list requests/responses. All three new Skills are enabled at the temporary project's `.agents/skills` paths. This is host discovery evidence only. The one empty task-local CODEX_HOME CLI model probe encountered Responses socket error 10013 and timed out after 60 seconds (`04-exec-startup-probe/`); CLI model behavior remains **BLOCKED**. No credential copy, provider/model change or sandbox bypass was used. Actual task evaluations use separate collaboration-host contexts, installed-resource reads and retained commands/raw outputs; that fallback is reported separately.

## Acceptance tasks

| Task | Actual short request and outcome | Evidence and limit |
| --- | --- | --- |
| T1 | First connection in progress | `t1-fixture.json`, `t1/`; initial connection is distinguished from existing-path reuse |
| T2 | Pending actual verification and read-only lookup | Native/backend alone cannot establish product flow PASS |
| T3 | Pending synthetic defect repair and independent verification | Original product is not the fault-injection target |
| T4 | Pending combined product/Harness maintenance and counterexamples | Both responsibilities must be exercised |
| T5 | Pending shared UI repair and fresh-context reuse | Screenshots alone will not prove interaction |
| T6 | Source/distribution/install checks completed so far; Agent/value assessment pending | `distribution-check.json`: 22 tests; `install-contract-check.json`: 18 tests; source/generated drift and distribution validation passed |

## Retained and excluded capabilities

The donor setup capability was narrowed to first connection. UI-refine is absorbed by the UI procedure and existing UI capabilities; improve-workflow by cause ownership/diagnose/product maintenance; resume-work by existing Git/Harness state recovery. Clear-writing has no acceptance task here and is excluded. No public Plugin/MCP/dashboard/central database, automatic full fan-out, cron or Stop-loop is introduced. Direct native CLI/CI paths remain available.

Existing capture regressions for zero/skip/stale/wrong-target/report handling remain useful. Backend/native assertions and the browser flow catch different failures; neither replaces the other. Static option/label/class checks are candidates for review, but no equivalent defect and valid-case evidence yet justifies deleting them. Test-count reduction, long-term reliability, cost or speed improvement are not claimed.

## Requirement status

R01–R16 are the acceptance criteria in the [requirements review](agent-coding-requirements-review.md). Final per-requirement implementation, observed behavior and remaining gaps will be updated after the task evaluations; source files and metadata are not evidence that those requirements are all fulfilled.
