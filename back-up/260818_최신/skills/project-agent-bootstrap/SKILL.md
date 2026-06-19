---
name: "project-agent-bootstrap"
description: "Bootstrap or reconcile a repo-local agent control plane from repository evidence: concise AGENTS.md surfaces, Work Packet-compatible docs/agents config, tracker/domain/triage settings, durable-record policy, verification commands, audit support, and setup report. Use when a repo is new, unconfigured, legacy, overgrown, drifted, multi-surface, or not ready for Work Packet execution."
argument-hint: "[repo-path] [--dry-run] [--repair-drift] [--report-only]"
---

# Project Agent Bootstrap

Use this skill to configure the **project environment/control plane** for agent-driven development. Do not treat it as a local `AGENTS.md` generator. Local `AGENTS.md` files are only one concise instruction surface among several control-plane artifacts.

Output a minimal, evidence-backed repo control plane:

- root `AGENTS.md` as the repo-specific operating index;
- nested `AGENTS.md` only for materially different package/path deltas;
- `docs/agents/workflow.md`, `issue-tracker.md`, `triage-labels.md`, and `domain.md` for Work Packet-compatible config;
- a durable local Work Packet tracker surface and a separate published-records archive (for example `docs/work-packets/` for `local_pending` Issue/PR records and `docs/archive/work-packets/` for published ones), with `.scratch/` reserved for ephemeral drafts only;
- a gitignored agent env profile convention: ensure `/agent-env.*.md` is in `.gitignore` and document that `$work-packet init` creates `agent-env.<slug>.md` and that tracker-channel routing lives in `issue-tracker.md`;
- setup report with evidence, verification, changes, risks, and unverified assumptions.

Read `REFERENCE.md` and `templates/` for details. Do not inline long policies into `SKILL.md` or local `AGENTS.md`.

## Non-goals and stop gates

Do not implement product changes, run Codex goal mode, run grill/interview workflows, migrate trackers, create/rename/delete remote labels, rewrite history, delete files, touch secrets/env files, run destructive commands, close issues/PRs, or deploy without explicit approval.

Stop and report the smallest safe fallback if evidence is insufficient, tracker migration is required, unrelated dirty changes would mix with setup edits, a delegated skill or CLI has no safe fallback, or more than 3 blocking setup decisions remain.

## Procedure

### 1. Read-only discovery

Inspect before editing. Read the smallest sufficient repo evidence:

- existing root/nested `AGENTS.md`, line counts, legacy agent docs, prompts, wrappers, skills, and prior bootstrap artifacts;
- README, build files, lockfiles, CI, scripts, package managers, entrypoints, and verification commands;
- architecture, domain, runbook, `CONTEXT`, ADR, verification, implementation-plan, source-of-truth, active-plan, and archive docs;
- tracker evidence: remotes, issue/PR/MR templates, labels, milestones, local Work Packets, `.scratch/`, active plans, and backlog docs;
- git status, default branch, branch/PR/MR conventions, open PRs/MRs, worktrees, and `gh`/`glab` availability;
- generated/read-only paths, migrations, secrets/env policy, external services, deployments, diagnostics, and operator-facing surfaces.

Output a concise findings summary before edits. Use evidence-backed defaults; ask at most 3 blocking setup questions.

### 2. Classify

Assign one base classification and any modifiers.

Base: `NEW_UNCONFIGURED`, `EXISTING_PARTIAL`, `EXISTING_OVERGROWN`, or `DRIFT_REPAIR`.

Modifiers: `MULTI_SURFACE`, `TRACKER_DRIFT`, `DOC_DRIFT`, `LEGACY_AGENT_DOCS`, `TOOLING_GAP`, `OPERABILITY_SURFACE`.

### 3. Select the minimal control plane

Required for Work Packet compatibility:

- `AGENTS.md`
- `docs/agents/workflow.md`
- `docs/agents/issue-tracker.md`
- `docs/agents/triage-labels.md`
- `docs/agents/domain.md`

Conditional: nested `AGENTS.md`, a durable local Work Packet tracker path (e.g. `docs/work-packets/`), a published-records archive (e.g. `docs/archive/work-packets/`), `.scratch/` for ephemeral drafts, ADRs, verification docs, implementation-plan docs, and source-of-truth indexes only when repo evidence requires them. Do not point durable `local_pending` records at `.scratch/`; that is ephemeral only.

Do not create broad documentation sets. Prefer thin config docs plus pointers to existing source-of-truth docs.

### 4. Reconcile instruction surfaces

Use `templates/AGENTS.md` and `templates/nested-AGENTS.md`.

Rules:

- keep every `AGENTS.md` under 100 lines;
- treat global `AGENTS.md` as authoritative and do not repeat generic safety, planning, TDD, documentation, approval, or done rules;
- include only repo-specific facts supported by evidence;
- move long architecture maps, task plans, wrappers, templates, migrations, and roadmap detail into normal docs;
- record missing or uncertain facts in the setup report, not as guesses in `AGENTS.md`.

Keep legacy agent docs only as concise compatibility pointers unless a specific tool requires distinct content.

### 5. Reconcile docs/agents config

Use templates for `workflow.md`, `issue-tracker.md`, `triage-labels.md`, and `domain.md`.

Capture Work Packet flow (including the `publish` step, which runs outside `auto` and batches/archives Issue/PR records), intake modes, delegated skill routing, architecture triggers, agent implementation execution contract (tool-neutral, for example Codex `/goal`), issue/PR/MR conventions, Korean Summary policy, auto gates, tracker-channel routing and access-path resolution (gh/mcp_pat/connector/handoff via the env profile, not network probing), the gitignored env profile convention, tracker mode, durable records with the active/archive split and `local_pending`/`handoff_pending` states, labels/states, domain/source-of-truth pointers, base/integration-branch and protected-branch policy, branch/PR conventions, archive hygiene, and verification evidence format.

When no repo branch convention exists, recommend slash-free branch names such as `wp-<work-packet-id>-<slug>` or `issue-<issue-number>-<slug>`. Do not introduce `/` in branch-name examples unless repo evidence already requires that convention. Record the base/integration branch explicitly (resolved from `git symbolic-ref refs/remotes/origin/HEAD` or the env profile, never assumed to be `main`) and the protected branches that require explicit human action before any merge/push.

Gate diagnostics, subagent, worktree, migration, deployment, and external-service sections by repo evidence.

### 6. Validate Work Packet compatibility

Verify that required control-plane files exist or missing items are justified; `AGENTS.md` files are discoverable and under 100 lines; tracker mode, tracker-channel routing and the env profile convention, durable-record policy with the active vs archive vs `.scratch/` roles distinguished, the `publish` step being outside `auto`, base/integration-branch and protected-branch policy, Korean Summary policy, verification evidence format, delegated-skill fallback, auto/approval gates, and active/archive doc alignment are explicit.

Run `scripts/audit-agent-bootstrap.py <repo-path>` when available and relevant, then include output or a summary in the setup report.

### 7. Report

Use `templates/setup-report.md`.

Report files created/changed, existing instructions preserved or moved, classification and modifiers, selected control plane, nested coverage, tracker mode, durable-record locations, branch/PR convention, delegated skill and CLI availability, verification commands found, audit results, risks, and unverified assumptions.

Bootstrap is complete only when the project environment has a concise repo operating index, Work Packet-compatible `docs/agents` config, explicit tracker/durable-record policy, explicit verification evidence policy, no conflicting instruction surfaces, no invented facts, and a setup report.
