# Project Agent Bootstrap Reference

This reference holds long policies that should not be copied into `SKILL.md` or local `AGENTS.md`.

## 1. Purpose

`project-agent-bootstrap` sets up the project environment for agent-driven development. It is not a local-`AGENTS.md` generator.

The environment is complete only when the repo exposes a compact, evidence-backed control plane for:

- repo-specific instructions;
- Work Packet orchestration;
- tracker and durable records;
- domain/source-of-truth pointers;
- triage/state mapping when used;
- verification commands and evidence reporting;
- branch/PR conventions;
- delegated skills, subagents, worktrees, and CLI fallback;
- setup report and unresolved assumptions.

## 2. Local AGENTS.md contract

Root `AGENTS.md` is a repo-specific operating index, not a full guide. It should normally contain only:

1. `Scope`
2. `Repo Map`
3. `Source Of Truth`
4. `Commands`
5. `Work Tracking`
6. `Agent / Skill Use`
7. `Repo Constraints`
8. `Verification And Done`

Do not include:

- generic global agent rules;
- long architecture descriptions;
- exhaustive file inventories;
- task-specific implementation plans;
- wrapper prompts;
- speculative or aspirational rules;
- unsupported commands;
- deterministic policy that belongs in CI, scripts, tests, hooks, or tooling.

A nested `AGENTS.md` is justified only when a subtree has different commands, constraints, verification, source-of-truth docs, generated files, or tracker conventions. It should contain deltas only.

## 3. Work Packet compatibility

Work Packet expects the repo to expose a small set of stable instruction surfaces:

- root `AGENTS.md`;
- nearest nested `AGENTS.md` for touched paths;
- `docs/agents/workflow.md`;
- `docs/agents/issue-tracker.md`;
- `docs/agents/triage-labels.md`, if labels/states are configured;
- `docs/agents/domain.md`;
- referenced architecture, context, ADR, verification, implementation-plan, runbook, and archive docs.

The bootstrap skill must create or reconcile those surfaces without duplicating the Work Packet skill itself.

## 4. Tracker and durable records

Define exactly one configured tracker mode:

- `github`: GitHub Issues/PRs are durable planning and review surfaces.
- `gitlab`: GitLab Issues/MRs are durable planning and review surfaces.
- `local_markdown`: repo-configured markdown files are the local tracker. The plan tree may be
  gitignored when repo policy prioritizes parallel personal planning, but then close/handoff must
  mirror settled shared decisions and verification evidence into tracked source-of-truth docs.
- `existing`: the repo already has another durable tracker; document how Work Packets map to it.

Durable knowledge must live in the configured tracker, PR/MR body, tracked docs, ADRs, or implementation plan. Distinguish these surfaces and namespace personal records per owner so collaboration does not cause merge conflicts:

- `docs/agents/` - agent control-plane/reference docs (shared-mutable, edited only in the orchestration lane);
- configured local plan root (for example `docs/plans/<owner-slug>/<feature-slug>/`) - personal
  Work Packet/spec/tickets/issues; may be gitignored by explicit repo policy;
- `docs/work-packets/<owner-slug>/` and `docs/archive/work-packets/<owner-slug>/` - tracked
  pending/published records only when a remote tracker publish workflow is configured;
- `docs/archive/` - completed or superseded design/planning docs (PRD, implementation plan, design notes, decision records), moved here when done; active plans stay out;
- `docs/adr/`, `docs/architecture*`, `docs/implementation-plan.md`, other `docs/*` - source-of-truth and other project docs;
- `.scratch/` - ephemeral drafts and operating state only; never durable.

For SHARED index/navigation/roadmap docs (e.g. `docs/index.md`), minimize merge conflicts: prefer a derived/regenerable index over a hand-maintained list; when hand-maintained, keep it append-only, one entry per line, stably ordered by an immutable key, with each owner appending only their own line(s) and never reflowing the whole file; edit it only in the serialized orchestration lane, never from parallel `init`/`run`. If the active path is gitignored, mirror durable summaries into tracked docs or the PR/MR body once one exists.

Tracker access is a declared **tracker channel**, not a try-and-fail behavior. The gitignored env profile `agent-env.<slug>.md` (created by `$work-packet init`) binds each repo - matched by SSH alias or HTTPS host/org from `git remote -v` - to a channel per orchestrator tool (Claude or Codex): `gh`, `mcp_pat`, `connector`, `handoff`, or `none`. The channel is resolved statically, never by probing the network. The code channel (git push/pull over SSH) is always available and is not governed by the tracker mode. Live Issue/PR writes happen only in the `publish` step, which is outside `auto`, batches pending records, and archives published ones. Track publish state on two axes: `git_publish_state` and `tracker_publish_state` (`local_pending` -> `issue_published`/`pr_published`, or `handoff_pending`). Ensure `/agent-env.*.md` is gitignored.

Never silently migrate tracker modes. Ask for approval or follow a tracked migration doc.

## 5. Issue and PR/MR surface policy

Issue/PR/MR titles should be English. Canonical sections should be English. GitHub/GitLab Issues and PRs/MRs created or updated by Work Packet should include a short Korean summary at the top for review speed:

```md
## Korean Summary (non-normative)

- ...

> This Korean summary is for review speed only. If it conflicts with the English canonical sections, linked source-of-truth docs, or repository rules, the English canonical sections and source-of-truth docs prevail.
```

Recommended issue sections:

```text
Korean Summary (non-normative)
Business outcome
Scope / out of scope
Source-of-truth docs
Decisions made
Vertical slices
Acceptance criteria
Verification plan
Architecture review target
Approval boundaries
Codex goal stopping condition
```

Recommended PR/MR sections:

```text
Korean Summary (non-normative)
Linked issue / Work Packet
Business outcome
Implemented slices
Scope / out of scope
Decisions made
Verification evidence
Architecture review result
Docs updated
Remaining risks
Close report placeholder or final report
```

## 6. Branch and PR/MR naming policy

Record the repo's existing branch convention when evidence exists. If no convention exists, recommend slash-free branch names such as:

- `wp-<work-packet-id>-<slug>` for local Work Packets;
- `issue-<issue-number>-<slug>` for issue-backed work.

Do not introduce `/` in generated branch-name examples or default branch recommendations unless the repo already has a working convention that explicitly requires slash-separated branch names.

Record the base/integration branch explicitly: resolve it from `git symbolic-ref refs/remotes/origin/HEAD` when set, else the env-profile `integration_branch`, else stop and ask. Never assume `main` or the default branch as the base merely because it exists. Record protected branches; the skill must never auto-merge or auto-push into them, and work shuttles only between the implementation branch and the base. Reflecting into a protected branch requires explicit human action.

Use closing keywords only when the PR/MR fully resolves the issue and targets the resolved base branch. Otherwise use `Related to` or `Part of`.

## 7. Local markdown Work Packet format

Required frontmatter:

```yaml
title:
status:
labels:
created_at:
```

Default rules:

- new packets start with `labels: [needs-triage]` unless the source tracker has a stronger state;
- use `status: draft` when blocking decisions remain;
- use `status: ready-for-agent` only when the packet can be implemented without extra human context;
- target one reviewable implementation PR with 2-5 vertical behavior slices.

Recommended body sections:

```text
# <title>

## Korean Summary (non-normative)
## Metadata
## Source
## Goal
## Non-goals
## Source of truth
## Intake mode
## Decisions made
## Auto-closed decisions
## Blocking questions
## PRD summary
## Vertical slices
## Acceptance criteria
## Verification plan
## Architecture review target
## Risks and approval boundaries
## Codex goal outline
## Issue body draft
## PR body draft
## Close report skeleton
## Durable record notes
```

## 8. Intake modes

Use the lightest safe intake mode:

- `skip_interview`: narrow, reversible, evidence-backed work with clear acceptance criteria.
- `triage_first`: raw backlog item or conflicting labels/state.
- `diagnose_first`: bug, flaky behavior, failing test, performance regression, or unexplained verification failure.
- `targeted_grill`: 1-3 blocking product/state/permission/failure/export decisions remain.
- `full_grill_with_docs`: domain language, product model, or cross-context meaning is unclear.
- `prototype_first`: throwaway code will answer a product/state/UI/logic question faster than discussion.
- `architecture_first`: architecture friction blocks safe implementation.

## 9. Architecture trigger policy

Normal implementation is acceptable when the seam exists, the change fits 2-5 vertical slices, verification can prove behavior, and refactoring is local to touched modules.

Use `architecture_first` when runtime boundaries, persistence, context policy, provider/model interfaces, diagnostics, or cross-domain contracts are unclear; no credible public behavior test seam exists; repeated boundary friction exists; runtime and domain responsibilities are mixed; public interfaces would likely be redesigned; verification cost is rising; or a hard-to-reverse ADR is required.

Do not hide broad architecture rewrites inside feature implementation.

## 10. Agent implementation contract support (tool-neutral, e.g. Codex `/goal`)

`docs/agents/workflow.md` should make it possible to create a self-contained implementation contract (for example a Codex `/goal`) with:

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

## 11. Auto and approval gates

Work Packet `auto` must stop on:

- more than 3 blocking decisions;
- no credible feedback loop for `diagnose_first`;
- human taste or ADR-level decision required for `architecture_first`;
- destructive operation, secret/credential handling, live provider call, external export, irreversible migration, costly operation, deployment, or security-sensitive change;
- tracker migration;
- unrelated dirty changes;
- delegated skill failure with no safe fallback;
- verification failure without a clear next diagnostic step;
- base/integration branch cannot be resolved (no `origin/HEAD` and no env-profile `integration_branch`);
- reflecting into a protected branch (auto must never auto-merge or auto-push there);
- PR merge/close, issue close, publish, or user review required.

`auto` never publishes: it stops with `local_pending` records and leaves the human-triggered `publish` step (and its archive step) to the owner.

## 12. Delegated Matt skill routing

Record availability and fallback policy for these methods when relevant:

| Situation | Delegated method | Fallback policy |
|---|---|---|
| Missing tracker/label/domain config | `setup-matt-pocock-skills` | Do local equivalent and record fallback |
| Raw issue/backlog/conflicting labels | `triage` | Minimal triage recommendation |
| Bug/failing verification/flaky/perf | `diagnosing-bugs` | Establish deterministic feedback loop |
| Domain/product ambiguity | `grill-with-docs` | Ask only blocking domain/product questions |
| Requirements synthesis | `to-spec` | Create a settled spec in the configured tracker surface |
| Slice validation | `to-tickets` | Validate one PR-sized packet; avoid issue fan-out unless needed |
| Behavior implementation | `tdd` | Failing test or documented verification per slice |
| Throwaway uncertainty resolution | `prototype` | Capture durable decision |
| Boundary-blocking architecture | `improve-codebase-architecture` | Bounded architecture discovery |
| System orientation | `zoom-out` | Read-only orientation summary |
| Session transfer | `handoff` | Compact handoff |

## 13. Legacy agent-doc interop

`AGENTS.md` and `docs/agents/*` should be canonical for this project setup. If older docs exist:

- preserve them if specific tools require them;
- convert them to concise pointers when safe;
- do not delete them without approval;
- do not maintain conflicting rules across `AGENTS.md`, `CLAUDE.md`, Copilot instructions, Cursor rules, `GEMINI.md`, prompt wrappers, or local skills.

## 14. Subagents and worktrees

Default to one orchestrating agent.

Use subagents/worktrees only when work is separable, interfaces and acceptance criteria are clear, verification responsibility is explicit, and merge risk is low.

Do not parallelize over shared interfaces, migrations, lockfiles, `AGENTS.md`, source-of-truth docs, secrets, tightly coupled edits, or unresolved decisions.

## 15. Verification evidence

Completion reports should include:

- commands run;
- result;
- relevant output summary;
- checks not run;
- unverified assumptions;
- remaining risks.

Do not claim completion without fresh evidence.

## 16. Archive hygiene

For a repo-approved gitignored personal plan tree, keep Work Packet/spec/ticket details local and mirror settled shared decisions plus verification evidence into tracked source-of-truth docs or a PR body before close or cross-clone handoff. Only remote-publish pending records move to the configured tracked archive after publication. Update shared indexes in the serialized orchestration lane using the merge-safe index convention.

## 17. Audit evidence

Use repository-supported read-only checks and record the exact commands. Do not require or invent a
bootstrap-specific helper program. At minimum verify `AGENTS.md` line counts, required
`docs/agents` files, `/agent-env.*.md` and any configured personal plan root are gitignored,
local-plan vs remote pending/archive vs `.scratch/` roles are distinct, ignored-plan mirror policy
is explicit, tracker-channel routing keeps `publish` outside `auto`, and base/protected-branch
policy is recorded.
- git dirty state;
- legacy agent docs;
- obvious wrapper prompt files;
- `.scratch/` presence;
- candidate verification commands.

The helper cannot replace evidence review. Treat its output as an audit input, not a source of truth.
