# Mode: auto

Run the manual phases sequentially only while each gate passes. `auto` is intended for practical Codex auto-permission use, but it still regulates agent coding through full-grill, shared-doc reconciliation, and confirmation gates.

Do not run more than one `auto` sequence in the same checkout. Parallel `auto` is allowed only when each sequence owns a separate ready issue, each uses a separate implementation worktree, and `close`/`next` are deferred or serialized in the orchestration lane.


## Required reads

- Precondition (before any tracker action): resolve the access path via the `Access path resolution` reference section — read the env profile, match the git remote, detect the orchestrator, decide the tracker channel. STOP if the profile is absent. `auto` does not publish (see the publish exclusion below), but it must still resolve the channel for any read it performs.
- Always read: this file and these sections via `scripts/read-reference-section.py`: `Access path resolution`, `Context budget and search hygiene`, `Metadata-first Tracker I/O`, `Right-sized Grill Routing`, `Tracker and durable record policy`, `Bounded auto approval policy`, and `Verification evidence`.
- Read if the phase reaches the gate with `scripts/read-reference-section.py`: `Full grill threshold`, `Grill conduct and fixed question format`, `Implementation confirmation gate`, `Issue-first contract with deferred shared-doc reconciliation`, `Implementation worktree policy`, and `Final active-branch refresh policy`.
- Templates: load only the current phase templates. Do not preload downstream phase templates.
- Do not read downstream mode files until the previous phase gate has passed.

## Lazy phase loading and handoff

At every `auto` phase boundary, write or update a phase handoff capsule with: completed phase, current evidence, decisions, unresolved gates, files read, tracker/doc mutations, `published_body_ref`, `grill_route`, `grill_route_reason`, verification evidence, delegated evidence, risks, next mode, and next stop condition. The capsule keeps lazy loading from losing state; it is an index, not a conclusion, and not a substitute for durable tracker or PR records.

## Default sequence

```text
init -> intent alignment -> shared-doc reconcile -> confirmation -> ready -> issue -> run -> pr -> close -> next -> final active-branch refresh
```

If `--draft-pr-first` is present:

In this sequence, `draft PR` and `update PR` are `pr`-mode review-surface actions only. Source, tests, docs, commits, and branch content remain owned by `run`.

```text
init -> intent alignment -> shared-doc reconcile -> confirmation -> ready -> issue -> draft PR -> run -> update PR -> close -> next -> final active-branch refresh
```

If `--no-auto-pr` is present:

```text
init -> intent alignment -> shared-doc reconcile -> confirmation -> ready -> issue -> run -> stop with PR command/body
```

## Parallel init behavior

During the `init` phase, `auto` may create only an isolated draft or issue body target. It must not edit shared docs during `init`. If the repo is not configured enough for durable issue publishing, `auto` may complete ideation and stop before `ready` with the draft path and missing config. If GitHub Issues are configured, `auto` must not proceed to `run` from a local seed alone.

## Full-grill and confirmation behavior

Auto mode must not treat implementation clarity as intent clarity.

- Apply `Right-sized Grill Routing` with a full-grill bias before selecting a lighter mode. For non-trivial internal process, skill-maintenance, tracker hygiene, context-budget, verification delegation, mode-routing, durable-record, or close/done-policy work, use `full_grill_with_docs` unless evidence proves the change is mechanical, local, and branch-free. If the full grill threshold from `REFERENCE.md` is met, stop in `full_grill_with_docs`, present the Decision Map, and ask the first fixed-format question unless the full grill has already been completed for the same scope.
- While direct full-grill questions remain unanswered, output only the Decision Map/status and the next fixed-format question. Do not synthesize roadmap, PRD, vertical slices, acceptance criteria, Implementation Contract, Codex goal, or Implementation Confirmation Brief.
- If `docs_grill_preflight` is enough, inspect repo docs/code and auto-close evidence-backed terminology decisions; stop only if a meaningful product/domain question remains.
- If the Implementation Confirmation Brief is missing, create it.
- If scope confirmation is missing, stop before `ready` and ask the single confirmation question.
- `--confirmed` only satisfies the confirmation gate for this exact scope. It does not bypass required `full_grill_with_docs`.

## Shared-doc reconciliation behavior

- Continue past `init` only when Proposed Shared Doc Updates are classified.
- Stop at `ready` if a blocking shared-doc update requires serial reconciliation.
- Stop at `ready` if a shared doc conflicts with the Work Packet and no Scoped Override exists.
- Do not directly edit shared docs from a parallel `init` context.
- Apply confirmed shared-doc updates only in the orchestration lane at their configured timing.

## Publish exclusion and bounded approval

`auto` never performs live tracker writes. It produces local `local_pending` Issue/PR records and
stops short of publishing. Live Issue/PR create/update — and any prompt such as:

```text
Approval needed to export/create PR:
```

belongs to the explicit, human-triggered `publish` mode, not to `auto`. The owner runs `publish`
separately to push code and create/update Issues and PRs in a batch.

`auto`'s bounded approval therefore covers only local work and the code channel it owns: creating or
switching the implementation branch and committing locally. It does NOT approve tracker publish,
push to a protected branch, merge, or issue closure. Read `Bounded auto approval policy` with
`scripts/read-reference-section.py` for the full boundary.

## `--no-auto-pr` behavior

`auto` already defers all Issue/PR creation to `publish`, so within `auto` no PR is ever created
regardless of this flag. `--no-auto-pr` carries forward to the later `publish` step:

- In `auto`: produce the local `local_pending` PR body and stop short of publishing, as always.
- Carried into `publish`: do not create or update a PR; do not close linked issues; output the exact `gh pr create` command, PR title, PR body or body-file path, linked issue reference, verification evidence capsule, and unresolved risks for the owner to run.
- Do not mark the Work Packet closed unless the repo explicitly allows local-only closure.

## Auto gates that must stop the sequence

- Full grill is required but not completed for the current scope.
- More than 3 blocking decisions remain after the Decision Map.
- Scope confirmation is missing and `--confirmed` was not supplied.
- Blocking shared-doc reconciliation is required.
- A shared doc conflicts with the Work Packet and no Scoped Override exists.
- `diagnose_first` cannot build a credible feedback loop.
- `architecture_first` requires human taste or ADR-level decision.
- Approval-sensitive non-GitHub action is required: destructive operation, credential/secret handling, live provider call, external data export beyond issue/PR/tracker updates, irreversible migration, costly external operation, or security-sensitive change.
- Tracker migration would be required.
- Dirty unrelated changes would mix with the branch or PR.
- A delegated skill fails and no safe fallback exists.
- Verification fails without a clear next diagnostic step.
- The configured parent issue cannot be created or updated before `run`; a local fallback is allowed only when local markdown tracking is explicitly configured.
- Auto-merge conditions fail when a merge would otherwise be attempted.
- User review is explicitly required by the repo or source Work Packet.
- Another `auto` sequence is active in the same checkout.

## Final cleanup

When the sequence reaches `close` or `next`, continue only while metadata plus the phase capsule are sufficient. If a full Issue/PR body would be needed only for reassurance, stop with the exact next mode command instead. When the sequence reaches `next`, run final active-branch refresh from the reference section after candidate selection. This refresh stays on the current branch by default, pulls from its configured upstream with fast-forward only, and reports if skipped.

## Output only

1. Completed phases
2. Current phase/status
3. Full-grill/preflight decision
4. Confirmation status
5. Shared-doc reconciliation status
6. Created issue/PR paths or URLs
7. Verification evidence, if any
8. Merge/issue-close result, if attempted
9. Active-branch refresh status, if run or skipped
10. Stop reason, if stopped
11. Next command or approval needed
