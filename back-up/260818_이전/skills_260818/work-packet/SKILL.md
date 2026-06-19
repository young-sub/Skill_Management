---
name: "work-packet"
description: "Use when orchestrating issue-first, PR-sized Work Packet workflows: init, ready, issue, run, pr, close, next, or auto. Handles tracker records, verification evidence, PR handoff, close reports, and next-work selection; do not use for ordinary code edits unless the user asks for Work Packet execution."
---

# Work Packet

Use this skill as the repo-local orchestration layer for PR-sized agent-driven implementation. It coordinates repo evidence, intent alignment, Work Packet tracking, delegated Matt Pocock engineering skills, Codex `/goal` execution, PR handling, close reporting, and next-work selection.

Do not ask the user to paste long wrapper prompts. Read the matching mode file, route to delegated skills when useful, and ask only blocking or confirmation questions.

## Default Flow

Use `init -> intent alignment -> confirmation -> ready -> issue -> run -> pr -> close -> next`; `auto` runs the same phases sequentially with gates.

## Direct Fix Lane

For trivial docs-only changes, one-line maintenance, or narrow root-cause fixes with no policy-sensitive surface, do not invoke full Work Packet flow. State why no Work Packet was used, run focused verification, and report remaining risk.

Use a Work Packet when the change affects a non-trivial capability, source-of-truth docs, public API, architecture boundary, persistence, security/privacy, permissions, model/tool lifecycle, workflow gates, verification policy, migrations, external operations, or close/done criteria.

## Cold Start Context Budget

- First determine the requested command or mode from the user message. Do not read every mode file.
- During orientation, use at most 5 direct file reads and 2 searches before a retained summary. Mandatory safety reads required by the active mode are exempt, but summarize them instead of retaining raw dumps.
- Before repo exploration, record: `Known from prompt`, `Must verify from repo`, `Do not read yet`, and `Delegation candidates`.
- Use `rg -l`, `rg --files`, or path-scoped searches first. Avoid repo-wide line searches until paths are narrowed.
- Exclude archive, generated, vendored, build, cache, data, fixture, and reference directories unless the active mode or repo evidence makes them directly relevant.
- If more context is needed, summarize retained facts in 500 words or less, then delegate bounded read-only exploration when available or continue with scoped reads only.
- In `auto`, do not pre-read downstream mode files. Load each phase only when the previous gate passes, and update the phase handoff capsule at every phase boundary.

## Phase Handoff Capsule

Before reading tracker bodies, PR bodies, large docs, raw diffs, or raw logs, read the current `Phase handoff capsule` if present, then metadata/stat/name-only views, then only sections or hunks needed for the current gate.

The canonical capsule lives in the Work Packet or durable tracker issue. Adjacent `.scratch` capsule files are convenience caches only. The capsule is an index, not a conclusion: raw source, exact verification evidence, tracker/PR state, and source-of-truth docs win on conflict. If a capsule claim affects architecture, API, security, persistence, verification sufficiency, or close, inspect raw evidence directly and update the capsule.

Each capsule includes `updated_at`, `source_ref`, `updated_by`, `phase`, `scope`, `current gate`, `accepted decisions`, `open decisions`, `files read`, `files changed`, `tracker/PR/doc mutations`, `published_body_ref`, `grill_route`, `grill_route_reason`, `verification evidence`, `delegated evidence`, `risks`, `next mode`, and `next stop condition`.

## Context I/O Invariant

Default to `metadata-first, body-once, capsule-only` retention. Prefer metadata/stat/name-only views before body reads; publish long tracker or PR bodies from body files when the host supports it; retain only URL/number/state/ref plus capsule fields after publishing. Repeated full Issue/PR body reads, raw logs, or duplicated close reports are escalation.

## Required First Step

1. Read only the matching file under `modes/`: `init`, `ready`, `issue`, `run`, `pr`, `close`, `next`, or `auto`.
2. Read listed reference sections with `scripts/read-reference-section.py <anchor>`. Do not read `REFERENCE.md` end-to-end during cold start.
3. Read only the templates listed by that mode and only when their preconditions are met.
4. Read repo-local context only until the current gate can be decided. Referenced docs are read only when already-read evidence cannot decide that gate.
5. If repo control-plane docs are missing or drifted, `init` may draft an isolated seed, but substantial `ready`, `run`, or `auto` must stop for bootstrap or explicit scoped fallback.

## Model Routing

Quality comes first. When a frontier/high-quality model such as `gpt-5.5` is available and cost or latency is not a material constraint, default subagents to that model and tune reasoning by role instead of downgrading model class. Use `medium` reasoning for bounded research, `high` for challengers, triage, and code-review-like work, and reserve `xhigh` for the hardest long-running, architecture, security, or final-review judgments where it is expected to improve quality.

Use fast/small models only for bounded, checkable support tasks. A downgrade needs a task-shape reason such as mechanical source/file checking, grep/file location, read-only docs/code capsules, test/lint/type command execution, failure log compression, mechanical checklist comparison, duplicate compression, or PR/close draft formatting after the main agent decides the substantive content. Do not downgrade merely because the task seems probably easy.

Before delegation, apply a subagent ROI gate. Use subagents only when lenses are separable, each handoff can stay compact, the main agent can verify material claims by spot-checking instead of redoing the whole task, and coordination/context cost is lower than a main-only pass. If the gate fails, continue main-only or run a compressed single-agent multi-lens review. A longer handoff is acceptable only when it remains tightly scoped, pointer-rich, and easier to verify than the raw evidence.

Use main/high-quality for scope, acceptance criteria, architecture, public API, persistence, security, lifecycle, evidence sufficiency, final diff review, final verification interpretation, and close/merge/done judgment. Read-only challengers may inspect high-risk or tightly coupled areas, but mutating work in those areas stays with the main/high-quality path.

Do not use fast/small implementation unless the write scope is explicit, semantically disjoint, narrow, already specified, and later reviewed by the main/high-quality model. Fast/small implementation must not own shared interfaces, schemas, migrations, lockfiles, `AGENTS.md`, `docs/agents/*`, source-of-truth docs, security-sensitive code, or unresolved domain decisions. Delegated handoffs must include `Model class`, `Reasoning effort`, `Allowed model use`, `Forbidden decisions`, exact evidence pointers, commands run, checks not run, uncertainty, and escalation triggers; if the host cannot choose model class, record the intended class without pretending enforcement exists.
## Global Invariants

- `init` is branchless ideation by default. Multiple sessions may run parallel-safe init from the current orchestration branch if each writes only an isolated issue draft or unique Work Packet seed draft.
- Do not edit source code in `init`, `ready`, `issue`, or `pr` modes.
- Do not create or switch implementation branches in `init`, `ready`, or `issue`.
- Do not run Codex goal mode in `init`, `ready`, `issue`, or `pr` modes.
- `pr` mode may update only PR metadata, body, labels, review state, and tracker surfaces. Source, tests, docs, commits, and branch content remain owned by `run`.
- When GitHub Issues are configured, a local seed is never the durable tracker after `issue` is required; `run` must stop without a parent issue.
- Bounded auto approval never overrides platform/tool approval prompts, sandbox escalation requirements, connector permission failures, or security/destructive/live/costly operation approvals.
- Shared source-of-truth docs are read-only during `init` unless the session is explicitly serialized.
- Do not invent repo facts. Use repo evidence or state uncertainty.
- Ask one question at a time. In `grill-with-docs`, present a Decision Map first and then use the fixed question format from `REFERENCE.md`.
- When `full_grill_with_docs` has unanswered direct questions, stop with only the Decision Map/status and the next fixed-format question.
- Treat `.scratch/` as local operating state unless the repo explicitly tracks it.
- Keep durable planning and review knowledge in the configured tracker, PR body, tracked docs, ADRs, or implementation plan.
- Use branch-name examples without `/`; prefer `wp-<work-packet-id>-<slug>` or `issue-<issue-number>-<slug>` unless repo evidence requires another convention.
- In Codex sandboxed environments, request the required sandbox escalation before mutating Git, GitHub, or tracker state, including commit, push, branch update, PR create/update, issue publish/update/close, merge, or release actions. Bounded auto approval does not replace sandbox/tool approval.
- Do not claim completion without exact verification evidence.
- Report user-facing results in Korean while preserving technical/professional terms, commands, identifiers, file paths, section names, and GitHub/PR/Issue terms in English.
- Keep outputs concise and action-oriented.

## Completion and Failure

A Work Packet is complete only when intended behavior or root cause is addressed, verification evidence is recorded, durable docs/tracker state are updated, remaining risks are reported, and close/next cleanup has run or has been explicitly skipped with a reason.

If the skill cannot proceed, state the mode, missing evidence or failed delegated skill, smallest safe fallback, and whether the failure is blocking.
