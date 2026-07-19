# Agent Workflow

This file holds workflow detail for the project agent operating environment. It should not duplicate global `AGENTS.md` rules or replace the Work Packet skill.

## Control Plane

- Root instructions: `AGENTS.md`
- Path-local instructions: nearest nested `AGENTS.md`, when present
- Tracker config: `docs/agents/issue-tracker.md`
- Triage vocabulary: `docs/agents/triage-labels.md` or <not used>
- Domain/source-of-truth pointers: `docs/agents/domain.md`

## Work Packet Flow

Use Work Packet for non-trivial capability work:

```text
$work-packet init <goal-or-active-goal>
$work-packet ready <work-packet-id>
$work-packet issue <work-packet-id>
$work-packet run <work-packet-id-or-issue-ref>
$work-packet pr <work-packet-id-or-issue-ref>
$work-packet close <work-packet-id-or-issue-ref>
$work-packet next <work-packet-id-or-issue-ref>
$work-packet publish            # human-triggered; OUTSIDE auto
```

The skill body works on local documents only. `issue`/`pr` produce `local_pending` records; the
tracker is touched only by `publish`, which is human-triggered, batches pending Issue/PR records, and
moves published ones to the archive. `$work-packet auto <goal-or-active-goal>` may run phases
sequentially only while all gates pass, but `auto` never publishes - run `publish` separately.

## Intake Modes

- `skip_interview`: narrow, reversible, evidence-backed work with clear acceptance criteria.
- `triage_first`: raw issue/backlog item or conflicting labels/state.
- `diagnose_first`: bug, failing test, flaky behavior, performance regression, or unexplained verification failure.
- `targeted_grill`: 1-3 blocking product/state/permission/failure/export decisions remain.
- `full_grill_with_docs`: domain language, product model, or cross-context meaning is unclear.
- `prototype_first`: throwaway code will answer uncertainty faster than discussion.
- `architecture_first`: architecture friction blocks safe implementation.

Ask at most 3 blocking questions unless the user requests a full interview. Auto-close implementation details that follow from repo convention.

## Delegated Skill Routing

| Situation | Delegated method | Availability | Fallback policy |
|---|---|---|---|
| Missing tracker/label/domain config | `setup-matt-pocock-skills` | <available/unavailable/unknown> | Do local equivalent and record fallback |
| Raw issue/backlog/conflicting labels | `triage` | <available/unavailable/unknown> | Minimal triage recommendation |
| Bug/failing verification/flaky/perf | `diagnose` | <available/unavailable/unknown> | Establish deterministic feedback loop |
| Domain/product ambiguity | `grill-with-docs` | <available/unavailable/unknown> | Ask only blocking domain/product questions |
| Requirements synthesis | `to-prd` | <available/unavailable/unknown> | Create concise PRD summary |
| Slice validation | `to-issues` | <available/unavailable/unknown> | Validate one PR-sized packet; avoid issue fan-out unless needed |
| Behavior implementation | `tdd` | <available/unavailable/unknown> | Failing test or documented verification per slice |
| Throwaway uncertainty resolution | `prototype` | <available/unavailable/unknown> | Capture durable decision |
| Boundary-blocking architecture | `improve-codebase-architecture` | <available/unavailable/unknown> | Bounded architecture discovery |
| System orientation | `zoom-out` | <available/unavailable/unknown> | Read-only orientation summary |
| Session transfer | `handoff` | <available/unavailable/unknown> | Compact handoff |

If a delegated skill is unavailable, state the skill, intended use, failure/unavailability, and fallback.

## Architecture Trigger Policy

Normal implementation is acceptable when the seam exists, the Work Packet fits 2-5 vertical slices, verification can prove behavior, and refactoring is local to touched modules.

Use `architecture_first` when runtime boundaries, persistence, context policy, provider/model interfaces, diagnostics, cross-domain contracts, or public interfaces are unclear or unstable; no credible public behavior test seam exists; repeated boundary friction exists; verification cost is rising; or a hard-to-reverse ADR is required.

Do not hide broad architecture rewrites inside feature implementation.

## Agent Implementation Contract (tool-neutral, e.g. Codex `/goal`)

`$work-packet run` should prepare a self-contained contract with:

- objective;
- Work Packet or issue reference;
- source-of-truth docs to read;
- decisions made;
- out of scope;
- vertical slice order;
- TDD strategy;
- verification loop;
- diagnostics expectations;
- scoped architecture review target;
- documentation updates;
- stop conditions;
- final report format.

## Issue and PR/MR Conventions

Titles should be English. Canonical body sections should be English.

Every GitHub/GitLab issue or PR/MR created or updated by Work Packet should include:

```md
## Korean Summary (non-normative)

- ...

> This Korean summary is for review speed only. If it conflicts with the English canonical sections, linked source-of-truth docs, or repository rules, the English canonical sections and source-of-truth docs prevail.
```

Use closing keywords only when the PR/MR fully resolves the issue and targets the resolved base branch (never auto-merge into a protected branch). Otherwise use `Related to` or `Part of`.

When the resolved tracker channel is `handoff` or unreachable, output the exact command, title, labels, and body, set `handoff_pending`, and do not claim the issue or PR/MR was created; do not retry a live call in a loop.

## Auto Gates

`auto` must stop on:

- more than 3 blocking decisions;
- no credible feedback loop for `diagnose_first`;
- human taste or ADR-level decision required for `architecture_first`;
- destructive operation, secret/credential handling, live provider call, external export, irreversible migration, costly operation, deployment, or security-sensitive change;
- tracker migration;
- unrelated dirty changes;
- delegated skill failure with no safe fallback;
- verification failure without a clear next diagnostic step;
- base/integration branch cannot be resolved (no `origin/HEAD` and no env-profile `integration_branch`);
- reflecting into a protected branch (auto must never auto-merge/auto-push there);
- PR merge/close, issue close, publish, or user review required.

`auto` does not publish: it stops with `local_pending` records and leaves `publish` to the owner.

## Branch and PR/MR Convention

- Default branch: <branch>
- Base/integration branch: <branch> - resolved from `git symbolic-ref refs/remotes/origin/HEAD` or the env-profile `integration_branch`; never assumed to be `main`.
- Protected branches: <list, e.g. main> - never auto-merge or auto-push into these; reflecting requires explicit human action. Work shuttles only between the implementation branch and the base.
- Implementation branch if no repo convention exists: `wp-<work-packet-id>-<slug>` or `issue-<issue-number>-<slug>`
- Do not introduce `/` in branch-name examples unless the repo already requires slash-separated branch names.
- Draft PR/MR policy: <policy>
- `--no-auto-pr` policy: stop with exact command/body after local implementation and verification.

## Verification Evidence

Each completion report should include commands run, result, relevant output summary, checks not run, unverified assumptions, and remaining risks.

## Archive Hygiene

Keep active plans separate from stale proposals and completed plans. When a design or planning doc (PRD, implementation plan, design notes, decision records) is completed or superseded by the implemented result, move it to `docs/archive/...` with decision history and verification evidence; do not leave completed design docs mixed with active plans. Published Work Packet records archive under `docs/archive/work-packets/<owner-slug>/`. Update indexes and source-of-truth pointers when docs move, in the serialized orchestration lane only, using the merge-safe index convention: prefer a derived/regenerable index, else append-only one entry per line by an immutable key, never reflowing the shared file.

## Subagents and Worktrees

Default to one orchestrating agent. Use subagents/worktrees only when work is separable, interfaces and acceptance criteria are clear, verification responsibility is explicit, and merge risk is low.

Do not parallelize over shared interfaces, migrations, lockfiles, `AGENTS.md`, source-of-truth docs, secrets, tightly coupled edits, or unresolved decisions.

## Diagnostics and Operability

Only include repo-specific diagnostics policy when runtime or operator-facing behavior is in scope. Prefer structured events, high-signal logs, snapshots/reports, and fallback diagnostics export paths when relevant.
