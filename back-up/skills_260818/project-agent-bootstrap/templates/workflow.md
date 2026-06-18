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
```

`$work-packet auto <goal-or-active-goal>` may run phases sequentially only while all gates pass.

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

## Codex `/goal` Contract

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

Use closing keywords only when the PR/MR fully resolves the issue and targets the default branch. Otherwise use `Related to` or `Part of`.

If `gh`/`glab` is unavailable, output the exact command, title, labels, and body instead of claiming the issue or PR/MR was created.

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
- inability to create/update issues or PRs and no configured local fallback;
- PR merge/close, issue close, or user review required.

## Branch and PR/MR Convention

- Default branch: <branch>
- Implementation branch if no repo convention exists: `wp-<work-packet-id>-<slug>` or `issue-<issue-number>-<slug>`
- Do not introduce `/` in branch-name examples unless the repo already requires slash-separated branch names.
- Draft PR/MR policy: <policy>
- `--no-auto-pr` policy: stop with exact command/body after local implementation and verification.

## Verification Evidence

Each completion report should include commands run, result, relevant output summary, checks not run, unverified assumptions, and remaining risks.

## Archive Hygiene

Keep active plans separate from stale proposals and completed plans. Archive completed/stale plans with decision history and verification evidence. Update indexes and source-of-truth pointers when docs move.

## Subagents and Worktrees

Default to one orchestrating agent. Use subagents/worktrees only when work is separable, interfaces and acceptance criteria are clear, verification responsibility is explicit, and merge risk is low.

Do not parallelize over shared interfaces, migrations, lockfiles, `AGENTS.md`, source-of-truth docs, secrets, tightly coupled edits, or unresolved decisions.

## Diagnostics and Operability

Only include repo-specific diagnostics policy when runtime or operator-facing behavior is in scope. Prefer structured events, high-signal logs, snapshots/reports, and fallback diagnostics export paths when relevant.
