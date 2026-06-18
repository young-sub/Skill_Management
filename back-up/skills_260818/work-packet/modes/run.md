# Mode: run

Prepare and, when the environment supports it, start Codex `/goal` execution for a ready parent issue or explicitly configured local Work Packet.

This mode delegates implementation discipline to `tdd` and uses other Matt skills as needed. `run` is the first mode that may create or switch implementation branches or worktrees.


## Required reads

- Always read: this file, the `Phase handoff capsule` if present, parent issue or configured local Work Packet sections needed for the run gate, root/local/nested `AGENTS.md` for likely touched paths, and these sections via `scripts/read-reference-section.py`: `Context budget and search hygiene`, `Metadata-first Tracker I/O`, `Tracker and durable record policy`, `Implementation worktree policy`, `Branch naming policy`, `Verification delegation policy`, and `Verification evidence`.
- Read if needed with `scripts/read-reference-section.py`: `Delegated Matt Pocock skill routing` and `Issue-first contract with deferred shared-doc reconciliation`; read source-of-truth docs only when they decide a blocking implementation gate.
- Template: `templates/codex-goal.md`.
## Process

1. Read order: `Phase handoff capsule`; tracker/Work Packet metadata and only Implementation Contract, Scoped Overrides, Proposed Shared Doc Updates, grill route evidence, and verification-plan sections; `git status --short`; likely-path `AGENTS.md`; listed reference sections via `scripts/read-reference-section.py`; source-of-truth docs only when they decide an implementation gate. Do not read `REFERENCE.md` end-to-end.
2. Confirm the tracker item is `ready-for-agent`, the full grill threshold has been satisfied or ruled out with `grill_route` and `grill_route_reason`, shared-doc reconciliation is complete, and the Implementation Confirmation Brief is recorded. If GitHub Issues are configured, a parent issue URL/number is required; a local seed path alone is insufficient.
3. Stop if user confirmation is missing, unless the source issue/PRD/plan contains equivalent confirmation or `--confirmed` was supplied for this exact scope.
4. Stop if shared docs conflict with the Work Packet and no explicit Scoped Override exists.
5. Stop if any Proposed Shared Doc Update marked blocking for implementation remains unresolved and is not covered by a Scoped Override.
6. Inspect `git status --short`, current branch, default branch, existing worktrees, and open PRs.
7. If expected touched scope exceeds 5 files, more than 2 source areas, or requires broad logs/reference comparison, delegate bounded read-only exploration when available and keep only the distilled findings in the main session. Use `Verification delegation policy` for test, lint, type, build, or log-heavy verification; delegate exact command execution by default when subagents are available, because test commands are side-effect-constrained rather than read-only. Fast/small execution is evidence only; the main agent owns RED/GREEN acceptance, sufficiency, and slice completion. If delegation is unavailable or the main agent runs a verification command directly, record the reason.
8. Do not continue if unrelated dirty changes would mix with implementation.
9. Confirm or create the implementation branch before starting Codex `/goal`: use the repo branch convention when defined; otherwise use `wp-<work-packet-id>-<slug>` or `issue-<issue-number>-<slug>`.
10. If started on `main`, create or switch to an implementation branch or create/use a dedicated implementation worktree before source edits. Do not leave source-code changes on `main`.
11. If an appropriate branch exists, switch to it. Otherwise create a new branch from the repo-approved base branch.
12. Parallel `run` requires a separate worktree and one `ready-for-agent` Work Packet per worktree. Stop if the packets would touch shared interfaces, schema, migrations, lockfiles, `AGENTS.md`, `docs/agents/*`, source-of-truth docs, or unresolved domain decisions.
13. If branch/worktree creation or switching is blocked by dirty state, missing base branch, stale worktree, or ambiguous existing PR, stop and report the smallest safe next action.
14. If `--draft-pr-first` is present, create a draft PR before implementation only when a live review/CI surface is valuable and the repo permits it.
15. If `--no-auto-pr` is present, do not create or update a PR automatically after implementation. Implement locally, verify, then output the exact PR command and body for user approval.
16. Construct a Codex `/goal` contract using `templates/codex-goal.md`, including the confirmed purpose, observable changes, scoped overrides, and shared-doc update obligations.
17. Implement with `tdd` one vertical slice at a time:
    - before RED, the main agent records the behavior/test intent, focused command, expected failure signal, and delegates verification execution by default when subagents are available;
    - delegate command execution or log compression only under `Verification delegation policy`; the main agent still owns RED/GREEN acceptance and slice completion;
    - one behavior-focused failing test or documented verification per slice;
    - RED is accepted only when the new or changed test fails through the expected behavior/assertion, not collection, import, environment, fixture setup, syntax, or unrelated failure;
    - minimal code to pass;
    - GREEN uses the same focused command when possible, then the relevant broader repo checks, normally executed by a verification subagent with capsule-only results;
    - no broad refactor while tests are red;
    - commit or report slice completion according to repo convention.
18. If unexpected verification failures, flaky behavior, slow tests, noisy output, or performance regressions occur, capture bounded evidence, redirect raw logs to an artifact when practical, retain only the verification capsule in the main session, stop unbounded reruns, and delegate to `diagnose` before changing more code.
19. Near the end, use `improve-codebase-architecture` semantics only for a scoped review of touched modules, interfaces, seams, adapters, tests, diagnostics, and docs.
20. Update affected docs and final evidence according to the Proposed Shared Doc Updates timing.
21. Do not claim completion without exact verification evidence.
22. Update the `Phase handoff capsule` with files changed, verification evidence, delegated evidence, risks, next mode, and next stop condition.

## Output only

1. `/goal` contract or started goal summary
2. Confirmation status
3. Shared-doc reconciliation status
4. Expected slice order
5. Required verification commands
6. PR behavior: auto PR, draft PR first, or no-auto-pr
7. Stop condition
8. Final report format
