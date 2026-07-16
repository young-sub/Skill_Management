# Mode: ready

Finalize an existing Work Packet seed or tracker issue for implementation only after intent alignment, shared-doc reconciliation, and scope confirmation are recorded.

`ready` is serialized per Work Packet and should run in the orchestration lane. Do not run two `ready` operations in parallel when they may touch the same shared doc, tracker index, roadmap, implementation plan, public interface, or verification policy.


## Required reads

- Always read: this file, the `Phase handoff capsule` if present, the Work Packet seed or tracker issue metadata/needed sections, and these sections via `scripts/read-reference-section.py`: `Context budget and search hygiene`, `Issue-first contract with deferred shared-doc reconciliation`, `Metadata-first Tracker I/O`, `Right-sized Grill Routing`, `Full grill threshold`, `Implementation confirmation gate`, `Tracker and durable record policy`, and `Verification evidence`.
- Read if needed: nearest nested `AGENTS.md`, referenced source-of-truth docs that decide a readiness gate, and `Delegated Matt Pocock skill routing` via `scripts/read-reference-section.py`.
- Templates: `templates/implementation-confirmation.md` and `templates/issue-body.md`.
## Process

1. Read the Work Packet seed or tracker issue with metadata-first reads and only needed sections, plus the Required reads above. Do not read `REFERENCE.md` end-to-end; load only the listed sections and referenced docs that decide a readiness gate. Prepare long issue bodies through body files when possible; do not retain full body text after preparation.
2. Validate that Context Intake Notes or an equivalent context-budget and delegation plan exists. If it is missing, add it before marking the packet `ready-for-agent`; if broad exploration is still needed, stop or delegate rather than filling gaps with raw main-thread search.
3. Re-read nearest nested `AGENTS.md` for all likely touched paths.
4. Confirm the packet is one PR-sized business capability or root-cause fix.
5. Re-check `grill_route`, `grill_route_reason`, and the full grill threshold. If full-grill triggers are materially present and not satisfied, stop in `full_grill_with_docs`, present the Decision Map, and ask the next unanswered fixed-format question. If full grill was skipped for internal process or skill-maintenance work, require the capsule to prove the change is mechanical, local, branch-free, and does not affect workflow gates, context-budget policy, tracker I/O, verification delegation, durable records, or close/done behavior.
6. If the packet contains roadmap, PRD, vertical slices, acceptance criteria, Implementation Contract, or Implementation Confirmation Brief sections produced while direct full-grill questions were still open, treat those sections as tentative and do not validate or publish them until grill closure is recorded.
7. Ensure an Implementation Contract exists and is self-contained for this packet scope.
8. Inspect Scoped Overrides. If a shared doc conflicts with the packet and no scoped override exists, stop before marking ready.
9. Inspect Proposed Shared Doc Updates and classify each item as `ready`, `before-run`, `close`, `next`, or `do-not-apply`.
10. Apply only shared-doc updates required for correct implementation, and only in the serialized orchestration lane. Defer roadmap, queue, archive, completion-status, and speculative updates to `close` or `next`.
11. If multiple packets propose conflicting edits to the same shared doc, domain term, public interface, or verification command, stop and reconcile before marking any affected packet `ready-for-agent`.
12. Ensure an Implementation Confirmation Brief exists and states purpose, core implementation target, observable changes, non-goals, assumptions/risks, verification signal, grill decision, scoped overrides, and shared-doc update timing.
13. Require explicit user confirmation, equivalent source confirmation, or `--confirmed`. If missing, set status to `needs-confirmation` and ask the single confirmation question.
14. Delegate to `to-tickets` to validate the vertical slice breakdown. In `local_markdown` mode it writes only to the configured gitignored `docs/plans/<owner>/<feature>/tickets.md` surface and performs no remote tracker operation.
15. Decide whether child issue fan-out is needed, but publish child issues only in `issue` mode when the packet is too large for one PR, needs parallel ownership, or the repo explicitly wants issue fan-out.
16. Ensure acceptance criteria are observable.
17. Ensure verification commands are explicit and repo-supported.
18. Ensure the Codex goal outline is self-contained enough for `/goal`.
19. Ensure durable knowledge is not left only in `.scratch/`. If GitHub Issues are configured, prepare the parent issue body for `issue` mode as a body file or publishable payload and retain only metadata plus `published_body_ref`. If local markdown is explicitly configured, make the local tracker packet self-contained.
20. Mark `ready-for-agent` only when no blocking product, architecture, tracker, verification, full-grill, confirmation, or shared-doc reconciliation decisions remain.
21. Update the `Phase handoff capsule` with readiness decision, `published_body_ref`, `grill_route`, `grill_route_reason`, accepted/deferred shared-doc updates, verification plan, next mode, and next stop condition.

## Output only

1. Work Packet seed path or tracker issue ref
2. Readiness status
3. Confirmation status
4. Shared-doc reconciliation status
5. Scoped overrides accepted or rejected
6. Missing blockers, if any
7. Slice list
8. Codex goal summary
9. Issue/PR durable-record summary
