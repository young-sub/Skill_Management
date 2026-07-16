# Agent Workflow

## Control Plane

- Root instructions: `AGENTS.md`
- Tracker config: `docs/agents/issue-tracker.md`
- Triage vocabulary: `docs/agents/triage-labels.md`
- Domain and ownership: `docs/agents/domain.md`

## Work Packet Flow

Use `init -> ready -> issue -> run -> pr -> close -> next` for non-trivial skill capability work.
In this repository, `issue` and `pr` are local-document phases; the tracker channel is `none` and
`publish` is not required. `auto` must still honor every approval and verification gate.

`run` may use a Codex Goal as its implementation backend, but the local Work Packet remains the
durable owner of scope, decisions, verification evidence, and close state.

## Intake And Delegation

- Use the lightest safe intake mode, with docs-aware alignment for changes to workflow, routing,
  verification, durable records, or skill behavior.
- Matt Pocock provenance, ownership, replacement names, and verification are governed by
  tracked `UPSTREAMS.md`; personal implementation detail remains under ignored `docs/plans/`.
- Planning skills must honor tracker mode: `to-spec` and `to-tickets` write durable artifacts under
  `docs/plans/<owner-slug>/<feature-slug>/` when mode is `local_markdown`; they must not
  require or attempt GitHub Issue/PR operations.
- The entire `docs/plans/` tree is agent-local and gitignored for parallel work.
  Before close or cross-clone handoff, mirror settled shared scope and evidence into affected
  tracked source-of-truth docs, ADRs, or a PR body when one exists.
- If a delegated skill is unavailable, state its intended use and use the smallest evidence-backed
  fallback; do not claim delegation occurred.

## Agent Implementation Contract

Each `run` contract records the objective, Work Packet path, source-of-truth documents, decisions,
non-goals, 2-5 vertical slices, TDD strategy, verification loop, architecture review target,
documentation updates, stop conditions, and final evidence format.

## Auto And Approval Gates

Stop for unresolved product or ADR decisions, destructive or security-sensitive operations,
secrets, external/costly operations, unrelated dirty changes, tracker migration, protected-branch
writes, or verification failure without a credible next diagnostic step. `main` is protected.

## Verification Evidence

Record exact commands, pass/fail results, relevant output summary, checks not run, unverified
assumptions, and remaining risks in the Work Packet. Complete a scoped architecture review of
touched skill contracts, references, invocation policy, routing, audits, and diagnostics.

## Archive Hygiene

Keep agent-local Work Packets, specs, tickets, issues, and notes under
`docs/plans/<owner-slug>/<feature-slug>/`. The directory stays gitignored after close; mirror only
settled shared decisions and verification evidence into tracked source-of-truth docs.
