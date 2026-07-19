# Agent Workflow

## Control Plane

- Root instructions: `AGENTS.md` with `CLAUDE.md` kept byte-identical for provider compatibility.
- Tracker config: `docs/agents/issue-tracker.md`.
- Triage vocabulary: `docs/agents/triage-labels.md`.
- Domain and source-of-truth pointers: `docs/agents/domain.md`.

## Work Packet Flow

Use `init -> ready -> issue -> run -> pr -> close -> next` for non-trivial capability work. `auto` may execute local phases but never publishes. `publish` is a separate human-triggered action that batches pending Issue/PR records and archives published records.

The current V2 effort starts with WP-01 from `harness_v2_implementation_plan.md`. Its implementation contract is the active plan plus a local Work Packet record. Use 2-5 vertical slices, TDD for behavior, and exact verification evidence.

## Intake And Delegation

- Use `skip_interview` when the active plan already fixes scope and acceptance criteria.
- Use `diagnose_first` for unexplained failures and `architecture_first` only when a repository boundary blocks safe implementation.
- Available delegated methods include `triage`, `diagnose`, `grill-with-docs`, `to-prd`, `to-issues`, `tdd`, `prototype`, `improve-codebase-architecture`, `zoom-out`, and `handoff`.
- If a delegated method is unavailable, perform the smallest local equivalent and report the fallback.

## Implementation Contract

Each run records the objective, Work Packet reference, source-of-truth docs, decisions, out-of-scope items, slice order, TDD strategy, verification loop, diagnostics expectations, architecture review target, documentation updates, stop conditions, and final report format.

## Branch And Review

- Base/integration branch: `main`, resolved from `refs/remotes/origin/HEAD`.
- Protected branches: `main`; never auto-push or auto-merge into it.
- Default implementation branch: `wp-<id>-<slug>`.
- Issue and PR titles and canonical sections are English. Include a short non-normative Korean summary.
- Use closing keywords only when the change fully resolves its issue against the resolved base branch.

## Gates And Evidence

Stop for destructive actions, secrets, live/costly operations, remote publication, migrations, unresolved architecture decisions, or verification failure without a credible next diagnostic step. Completion evidence includes commands run, results, relevant output, checks not run, assumptions, and remaining risks.

## Archive Hygiene

Active local records live under `docs/work-packets/<owner>/`; published records move to `docs/archive/work-packets/<owner>/`. `.scratch/` and `.work/` are ephemeral and never durable. Completed implementation and design plans move under `docs/archive/` only at close.
