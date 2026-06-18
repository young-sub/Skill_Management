# Issue Tracker Config

This file defines the durable tracking surface for Work Packet and agent-driven implementation.

## Tracker Mode

- Mode: <github | gitlab | local_markdown | existing>
- Canonical tracker: <URL/path/name>
- Migration policy: do not migrate trackers silently; require approval or follow <tracked migration doc>.

## Tracker Channel and Access Path

The Work Packet skill body works on local documents; live Issue/PR query/publish happens only in the
`publish` step. How that publish reaches the tracker is the **tracker channel**, resolved as a skill
policy (not a tool-sandbox behavior) and applied equally to a Claude or Codex orchestrator.

- Env profile: `agent-env.<slug>.md` (gitignored at repo root, created by `$work-packet init`). It
  binds each repo (matched by SSH alias or HTTPS host/org from `git remote -v`) to a tracker channel
  per orchestrator tool. The channel is declared, never discovered by probing the network.
- Channels: `gh` (CLI with `--repo`), `mcp_pat` (GitHub MCP server with a static PAT), `connector`
  (Codex git connector), `handoff` (no direct channel: emit exact payload + command, set
  `handoff_pending`), `none` (local-only).
- Code channel (git push/pull over SSH) is always available and is NOT governed here.
- This repo's channel binding: <remote_match -> channel(s), or "see agent-env profile">.

## Durable Records

- Active local Work Packet tracker: <durable tracked path, e.g. docs/work-packets/<owner-slug>/> - holds
  `local_pending` Issue/PR records before `publish`, namespaced per owner so collaborators never touch
  the same file. The durable tracker until published. Not `.scratch/`, not one shared file.
- Published archive: <tracked path, e.g. docs/archive/work-packets/<owner-slug>/> - `publish` moves published
  Issue/PR body files here so a later batch never re-publishes them; archived records are immutable.
- Completed design/planning archive: <e.g. docs/archive/> - move completed/superseded PRD, implementation
  plan, and design docs here at close; keep active plans out.
- Shared index/roadmap (e.g. docs/index.md): minimize merge conflicts - prefer a derived/regenerable index,
  else append-only one entry per line by immutable key, edited only in the orchestration lane.
- Work Packet planning/spec: <active local path / issue/PR once published / tracked docs>
- PR/MR review knowledge: <PR/MR body or tracker>
- Decisions: <ADRs/docs/issue/PR>
- Close reports: <issue/PR/tracked docs>
- Architecture/domain updates: <docs/ADRs>
- `.scratch/`: ephemeral drafts and operating state only; never the durable record.

Publish state is tracked on two independent axes: `git_publish_state` (code channel) and
`tracker_publish_state` (`local_pending` -> `issue_published`/`pr_published`, or `handoff_pending`).
If the active path is gitignored, mirror durable summaries into tracked docs or the PR/MR body once available.

## GitHub / GitLab Behavior

- Issue titles: English.
- PR/MR titles: English.
- Canonical body sections: English.
- Korean summary: required for GitHub/GitLab issues and PRs/MRs created or updated by Work Packet.
- Closing keywords: use only when the PR/MR fully resolves the issue and targets the resolved base branch (never auto-merge into a protected branch).
- Channel fallback: when the resolved channel is `handoff` or unreachable, output exact command, title, labels, and body, set `handoff_pending`, and do not claim creation. Never retry a live call in a loop.

## Korean Summary Template

```md
## Korean Summary (non-normative)

- ...

> This Korean summary is for review speed only. If it conflicts with the English canonical sections, linked source-of-truth docs, or repository rules, the English canonical sections and source-of-truth docs prevail.
```

## Issue Body Sections

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
Agent implementation stopping condition (tool-neutral, e.g. Codex /goal)
```

## PR/MR Body Sections

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

## Local Markdown Work Packets

- Active path (durable, `local_pending` records, per owner): <e.g. docs/work-packets/<owner-slug>/, or not used>
- Published archive path (per owner): <e.g. docs/archive/work-packets/<owner-slug>/, or not used>
- Tracked by git: <yes/no>
- Required frontmatter:

```yaml
title:
status:
labels:
created_at:
```

- Default initial label: `needs-triage`, unless source tracker has a stronger state.
- `status: draft`: blocking decisions remain.
- `status: ready-for-agent`: no blocking decisions remain and verification plan is explicit.
