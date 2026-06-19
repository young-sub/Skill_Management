# Project Agent Bootstrap Setup Report

## Summary

- Repo: <name/path>
- Date: <YYYY-MM-DD>
- Base classification: <classification>
- Modifiers: <modifiers>
- Mode: <normal | dry-run | repair-drift | audit-only>

## Files Created Or Changed

| Path | Action | Reason |
|---|---|---|
| <path> | <created/updated/moved/preserved> | <reason> |

## Existing Instructions

- Preserved: <items>
- Moved out of AGENTS.md: <items and destination>
- Left as compatibility pointers: <items>
- Not changed because approval is required: <items>

## Control Plane

- Root `AGENTS.md`: <status, line count>
- Nested `AGENTS.md`: <status/paths/not needed>
- `docs/agents/workflow.md`: <status>
- `docs/agents/issue-tracker.md`: <status>
- `docs/agents/domain.md`: <status>
- `docs/agents/triage-labels.md`: <status or not used>
- Active local Work Packet tracker (e.g. `docs/work-packets/`): <status or not used>
- Published archive (e.g. `docs/archive/work-packets/`): <status or not used>
- `.scratch/` (ephemeral only): <status or not used>
- `/agent-env.*.md` gitignored: <yes/no>
- Tracker-channel routing documented: <yes/no>

## Work Packet Compatibility

| Requirement | Before | After | Notes |
|---|---|---|---|
| Root AGENTS under 100 lines | <status> | <status> | <notes> |
| Required docs/agents config | <status> | <status> | <notes> |
| Tracker mode defined | <status> | <status> | <notes> |
| Tracker-channel + env profile | <status> | <status> | <notes> |
| Active/archive durable split | <status> | <status> | <notes> |
| Publish outside auto | <status> | <status> | <notes> |
| Base/protected-branch policy | <status> | <status> | <notes> |
| Durable record policy | <status> | <status> | <notes> |
| Korean Summary policy | <status> | <status> | <notes> |
| CLI fallback policy | <status> | <status> | <notes> |
| Verification evidence format | <status> | <status> | <notes> |
| Auto/approval gates | <status> | <status> | <notes> |

## Tracker And Durable Records

- Tracker mode: <github | gitlab | local_markdown | existing | unresolved>
- Canonical tracker/path: <value>
- Durable records: <issue/PR/tracked docs/ADRs/implementation plan>
- Tracker migration needed: <yes/no>
- CLI availability: `gh` <status>, `glab` <status>

## Commands And Verification

| Purpose | Command | Evidence | Run during bootstrap? |
|---|---|---|---|
| install | `<command>` | <source> | <yes/no> |
| build | `<command>` | <source> | <yes/no> |
| test | `<command>` | <source> | <yes/no> |
| typecheck | `<command>` | <source> | <yes/no> |
| lint/format | `<command>` | <source> | <yes/no> |
| run locally | `<command>` | <source> | <yes/no> |

## Branch / PR Convention

- Default branch: <branch>
- Implementation branch convention: <convention>
- Draft PR/MR policy: <policy>
- `--no-auto-pr` behavior: <policy>

## Delegated Skills

| Skill/method | Available? | Configured docs | Fallback |
|---|---|---|---|
| setup-matt-pocock-skills | <status> | <paths> | <fallback> |
| triage | <status> | <paths> | <fallback> |
| diagnose | <status> | <paths> | <fallback> |
| grill-with-docs | <status> | <paths> | <fallback> |
| to-prd | <status> | <paths> | <fallback> |
| to-issues | <status> | <paths> | <fallback> |
| tdd | <status> | <paths> | <fallback> |
| prototype | <status> | <paths> | <fallback> |
| improve-codebase-architecture | <status> | <paths> | <fallback> |
| zoom-out | <status> | <paths> | <fallback> |
| handoff | <status> | <paths> | <fallback> |

## Subagent / Worktree Recommendation

- Subagents: <recommended now | later | not recommended>
- Worktrees: <recommended now | later | not recommended>
- Reason: <evidence>

## Audit Results

- Audit helper run: <yes/no>
- Summary: <output summary>

## Remaining Risks And Unverified Assumptions

- <risk or assumption>

## Next Action

- <recommended next command or setup action>
