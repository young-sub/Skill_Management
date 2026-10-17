# Agent Documentation Index

Read applicable AGENTS and `.harness/project.yaml` first. Load ignored `.harness/environment-exceptions.json` once per task; honor `skip_until_manual_reenable` and its fallback.

- [Current design](research/agent-coding-system-direction.md): six outcomes, user flow, ownership and completion boundaries. This is the design authority.
- [Current execution instructions](research/plugin-continuous-improvement-next-session.md): improve from observed gaps, without reopening completed work.
- [System](system.md), [architecture](architecture/harness.md), [domain ownership](agents/domain.md): runtime and source boundaries.
- [Feature Map](feature-map.md): user functions, owners and executable checks.
- [Testing](testing.md): impact selection, current commands, execution and evidence rules.
- [Agent workflow](agents/workflow.md): repository delivery/Git policy; explicit session authorization remains authoritative.
- [Global guidance](agents/global-guidance.md): canonical global rules and revision backups.
- [Plugin packaging](plugins.md), [Skill inventory](architecture/skill-inventory.md): local package, distribution and host boundaries.
- [Tracker integration](agents/issue-tracker.md), [triage labels](agents/triage-labels.md): optional tracking.

## Results and historical evidence

These are scoped execution records, not current task lists or fresh PASS results.

- [0.1.68 hardening](research/core-hardening-results.md): required checks, TaskStore/public API, capture publication, package and isolated product evidence.
- [Implementation results](research/agent-workflow-implementation-results.md): preceding versions and their limits.
- [Luna benchmark execution](research/luna-benchmark-execution.md), [benchmark plan](research/agentic-harness-benchmark-plan.md): actual results versus unperformed boundaries.
- [Labeler pilot](research/labeler-verification-pilot.md), [pstack analysis](research/pstack-analysis.md): bounded product/research evidence.
- [Archive](research/archive/index.md): superseded design/review/next-session material and prior testing notes.
- [v2 release](releases/v2.0.0.md), [v2 pilot](pilots/harness-v2-pilots.md): historical release evidence.
