# Issue Tracker Config

This file defines the durable tracking surface for Work Packet and agent-driven implementation.

## Tracker Mode

- Mode: <github | gitlab | local_markdown | existing>
- Canonical tracker: <URL/path/name>
- Migration policy: do not migrate trackers silently; require approval or follow <tracked migration doc>.

## Durable Records

- Work Packet planning/spec: <issue/PR/tracked docs/local path>
- PR/MR review knowledge: <PR/MR body or tracker>
- Decisions: <ADRs/docs/issue/PR>
- Close reports: <issue/PR/tracked docs>
- Architecture/domain updates: <docs/ADRs>
- `.scratch/`: local operating state only unless intentionally tracked.

If the local Work Packet path is gitignored, mirror durable summaries into tracked docs or the PR/MR body once available.

## GitHub / GitLab Behavior

- Issue titles: English.
- PR/MR titles: English.
- Canonical body sections: English.
- Korean summary: required for GitHub/GitLab issues and PRs/MRs created or updated by Work Packet.
- Closing keywords: use only when the PR/MR fully resolves the issue and targets the default branch.
- CLI fallback: if `gh`/`glab` is unavailable, output exact command, title, labels, and body; do not claim creation.

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
Codex goal stopping condition
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

- Path: <path or not used>
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
