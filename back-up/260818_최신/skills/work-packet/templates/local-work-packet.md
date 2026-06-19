---
title:
status: draft
labels:
  - needs-triage
created_at:
---

# <title>

## Korean Summary (non-normative)

### 목적

<Write a concise Korean paragraph for review speed. Start with the business, review, audit, customer, or follow-up decision this Work Packet makes easier. Do not start with implementation identifiers.>

### 핵심 구현 사항

<Write a compact Korean paragraph that explains business impact, core implementation result, important scope boundary, and material risk only when needed. Explain unavoidable technical terms briefly on first use.>

> This Korean summary is for review speed only. If it conflicts with the English canonical sections, linked source-of-truth docs, or repository rules, the English canonical sections and source-of-truth docs prevail.

## Metadata

- Source:
- Tracker:
- Durable tracker after issue:
- Intake mode:
- Intent confidence:
- Status:
- Parallel-safe init: yes/no
- Isolated write surface:

## Phase handoff capsule

- updated_at:
- source_ref:
- updated_by:
- phase:
- scope:
- current gate:
- accepted decisions:
- open decisions:
- files read:
- files changed:
- tracker/PR/doc mutations:
- tracker_channel: <gh | mcp_pat | connector | handoff | none>
- git_publish_state: <local_only | committed | branch_pushed>
- tracker_publish_state: <local_pending | issue_published | pr_published | handoff_pending>
- published_body_ref: <durable url + version, empty until publish>
- verification evidence:
- delegated evidence:
- risks:
- next mode:
- next stop condition:

This capsule is an index, not a conclusion. Inspect raw evidence directly for architecture, API, security, persistence, verification sufficiency, or close claims.

## Context-budget and delegation plan

Ready gate: fill this before `ready-for-agent`; unresolved broad exploration must be delegated or recorded as a blocker.

- Known from prompt:
- Must verify from repo:
- Do not read yet:
- Direct reads used:
- Orientation searches used:
- Delegation candidates:
- Delegation used or unavailable:
- Retained working summary:

## Goal

## Non-goals

## Source of truth

## Implementation Contract

For unresolved `full_grill_with_docs`, leave this section as `DEFERRED: direct grill questions remain`. Use `templates/grill-decision-map.md` instead of filling implementation-planning sections.

After `ready`, this seed is authoritative only when local markdown is the configured tracker. If GitHub Issues are configured, `issue` must publish or update the parent issue; that GitHub Issue becomes the durable implementation contract, and this file remains supporting draft evidence.

- Purpose:
- Core implementation target:
- Observable changes:
- What will not change:
- Verification signal:

## Scoped Overrides

### <shared-doc-path-or-none>

- Existing statement:
- Packet-specific override:
- Scope:
- Expiry:
- Required reconciliation:

## Proposed Shared Doc Updates

### <path-or-none>

- Change type: <domain | architecture | verification | roadmap | archive | tracker | other>
- Reason:
- Proposed update:
- Apply timing: <ready | before-run | close | next | do-not-apply>
- Blocking for implementation: <yes | no>
- Conflict risk: <low | medium | high>

## Grill / intent alignment

- Full grill decision:
- Docs/code evidence inspected:
- Auto-closed terminology decisions:
- Blocking questions:

## Decision Map

Decision Map may be written in Korean for Korean grill sessions. Keep it compact for `targeted_grill`, use a mini map for `docs_grill_preflight`, and use the full map plus internal branch tracking for `full_grill_with_docs`.

| Category | Why it matters | Estimated questions | Direct questions |
|---|---|---:|---|
| <category> | <business/product reason> | <min-max> | <labels> |

- Total estimated questions:
- Questions to ask directly now:
- Decisions likely auto-closed from repo evidence:

## Grill question log

```md
Progress: [category n/m, question z of estimated x-y]

## Q. [question in Korean]
Question intent:
- <Explain in Korean which business/product decision this question resolves and why the recommended answer is reasonable. Do not repeat the Decision Map.>

Recommended answer:
- <State the recommended option first, then briefly explain repo evidence, product intent, reversibility, and verification basis.>
```

## Implementation Confirmation Brief

Use `templates/implementation-confirmation.md`.

## Confirmation status

- Status: needs-confirmation
- Evidence:

## Decisions made

## Auto-closed decisions

## PRD summary

For unresolved `full_grill_with_docs`: `DEFERRED: direct grill questions remain`.

## Vertical slices

For unresolved `full_grill_with_docs`: `DEFERRED: direct grill questions remain`.

1. <slice>
2. <slice>

## Acceptance criteria

## Verification plan

## Architecture review target

## Risks and approval boundaries

## Codex goal outline

## Issue body draft

## PR body draft

## Close report skeleton

## Durable record notes
