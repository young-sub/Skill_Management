# Mode: next

Choose the next Work Packet seed after a completed implementation.

This mode replaces old pasted post-implementation router prompts. `next` is orchestration-lane work only and must not run in parallel for the same repo.


## Required reads

- Precondition (before any tracker action): resolve the access path via the `Access path resolution` reference section — read the env profile, match the git remote, detect the orchestrator, decide the tracker channel. STOP if the profile is absent.
- Always read: this file, the `Phase handoff capsule` if present, completed close report, linked issue/PR metadata/needed sections, and these sections via `scripts/read-reference-section.py`: `Access path resolution`, `Context budget and search hygiene`, `Metadata-first Tracker I/O`, `Document layout and merge safety`, `Base reflection and protected-branch policy`, and `Final active-branch refresh policy`.
- Read if needed: unresolved Proposed Shared Doc Updates, recent commits, ADRs, CONTEXT docs, or roadmap/index docs that decide candidate ordering.
- Templates: none by default.
## Process

1. Read order: `Phase handoff capsule`; `git status --short`; close capsule or completed close report; linked issue/PR metadata; ready-issue metadata; current roadmap/status pointers only when needed; only unresolved Proposed Shared Doc Updates needed for candidate ordering; listed reference sections via `scripts/read-reference-section.py`.
2. Inspect recent commits, tests, docs changed, implementation plan, roadmap, AGENTS, CONTEXT docs, or ADRs only when the close report and active status pointers cannot decide the next bottleneck. Full docs or full `REFERENCE.md` reads are escalation, not default.
3. Identify what business or operational capability became possible.
4. Reflect this turn's implementation onto the resolved base/integration branch per the `Base reflection and protected-branch policy`. Work shuttles only between the implementation branch and the base. If the base is protected (for example base equals the default branch), do NOT auto-merge or auto-push into it: report the implementation branch, the intended base, the exact reflection command, and hand off for explicit human action. Never reflect into `main` or any protected branch autonomously.
5. Reconcile deferred roadmap, queue, implementation-plan, and index updates from completed Work Packets serially, in the orchestration lane only, per the `Document layout and merge safety` reference section: regenerate a derived index when possible, else append one stably-ordered entry per line without reflowing the shared file. Never edit shared indexes from parallel `init`/`run`.
6. Identify the current highest-value bottleneck. Prefer metadata-only `ready-for-agent` issue inspection first. If no ready issue exists, inspect only metadata for open `needs-info` issues and recommend the candidate most directly connected to the just-completed flow by linked issue/PR, parent/dependency, title keywords, or recent tracker adjacency. Treat a `needs-info` candidate as a next intake/ready target, not as runnable implementation work. Stop with `no ready issue found` only when neither ready issues nor a narrowly related `needs-info` candidate can be identified without broad doc scanning.
7. Propose at most 3 next Work Packet candidates.
8. Do not interview, implement, or write a full Codex goal prompt.
9. For each candidate, state likely intake mode and which Matt skills would be used.
10. Run final active-branch refresh from the reference section as the last step.
11. Update the `Phase handoff capsule` or durable tracker with selected next candidate, skipped candidates, refresh result, and next stop condition without refetching full Issue/PR bodies only for status confirmation.

## Output only

1. Completed capability summary
2. Base reflection status: reflected into base, or handed off (base protected), or skipped
3. Shared-doc/roadmap reconciliation status
4. Highest-value remaining bottleneck
5. Up to 3 candidate Work Packets
6. Recommended candidate
7. Recommended intake mode
8. Active-branch refresh status, if run or skipped
9. Suggested next command
