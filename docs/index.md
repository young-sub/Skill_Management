# Agent Documentation Index

Load ignored repository-local `.harness/environment-exceptions.json` once per task when present; refresh after relevant environment changes. `skip_until_manual_reenable` selects the recorded fallback without retrying the unavailable capability.

- [System](system.md) — end-to-end Core-First Harness flow and state ownership.
- [Harness architecture](architecture/harness.md) — project, contract, execution, environment, retention, and distribution boundaries.
- [Testing](testing.md) — source-to-test impact rules and local/CI verification selectors.
- [Feature Map](feature-map.md) — repository user functions, invariants, side effects, and directly executable checks.
- [Agent workflow](agents/workflow.md) — repository delivery, Git, approval, and close workflow.
- [Global guidance](agents/global-guidance.md) — maintained global instructions, authorized target selection, and mandatory revision backups.
- [Domain](agents/domain.md) — repository responsibilities and source-of-truth map.
- [Tracker integration](agents/issue-tracker.md) — optional local/GitHub tracker channel policy.
- [Triage labels](agents/triage-labels.md) — current issue vocabulary.
- [Skill inventory](architecture/skill-inventory.md) — public distribution inventory.
- [Agent Coding direction](research/agent-coding-system-direction.md) — October 5 decisions and discussion history: one workflow entry, full-stack verification, feedback guardrails, Feature/UI maintenance, and evidence-based pruning; agreed capabilities are distinguished from implemented behavior.
- [Agent workflow completion design](research/agent-workflow-completion-design.md) — system-wide responsibility/authority and deterministic/semantic processing criteria across all capabilities, full Feature init, environmental enforcement, task benefit, and U1–U7; current acceptance design; implementation and remaining host limits are reported separately.
- [Next implementation prompt](research/agent-workflow-next-session.md) — execution scope applying the common separation criteria to the whole workflow and delivering U1–U7 in functional units; Feature Map is one example, not the implementation scope.
- [Agent Coding requirements review](research/agent-coding-requirements-review.md) — R01–R16 audit of the pre-implementation design, raw-evidence limits, minimal corrections, and concrete acceptance tasks; this review did not execute the implementation prompt.
- [Agent workflow implementation results](research/agent-workflow-implementation-results.md) — current implementation, isolated task evidence, host limits and requirement acceptance status.
- [Executed implementation prompt](research/agent-coding-next-session.md) — retained scope of the first implementation and T1–T6 pilot; current follow-up work is owned by the completion design, and actual outcomes/limits by the implementation results.
- [Labeler pilot results](research/labeler-verification-pilot.md) — actual browser/API/D1/print evidence, defect controls, delegated repair, minimal improvements, Skill responsibility and temporary Plugin host checks.
- [pstack research](research/pstack-analysis.md) — pinned upstream inventory and critical analysis; research evidence rather than repository execution policy.
- [Agent Coding archive](research/archive/index.md) — superseded October 4 design and completed foundation/Labeler prompt; historical evidence, not active execution instructions.
- [v2.0.0 release record](releases/v2.0.0.md) — durable historical release evidence; not current workflow authority.
- [v2 pilot evidence](pilots/harness-v2-pilots.md) — durable evidence owned by the v2.0.0 release record; not the current Review contract.
