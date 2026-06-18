# Mode: init

Create the smallest useful Work Packet ideation draft for the requested goal, but do not synthesize PRD, roadmap, vertical slices, Implementation Contract, or Implementation Confirmation Brief before required intent alignment is complete. When the chosen intake mode is `full_grill_with_docs`, grill alignment is the work product until the blocking decisions are closed.

`init` is branchless and parallel-safe by default. Multiple sessions may run `init` from the current orchestration branch without extra user setup when each session writes only to an isolated planning surface.


## Required reads

- Owner/profile precondition (blocking, runs first): ensure the env profile exists before ideation. If `agent-env.<slug>.md` is missing, run the Owner gate below to create it. This is the one place that may create the profile; every other mode STOPs when it is absent.
- Always read: this file, `templates/agent-env.template.md` (only when the profile must be created), `templates/grill-decision-map.md`, and these sections via `scripts/read-reference-section.py`: `Access path resolution`, `Context budget and search hygiene`, `Workspace and lane policy`, `Issue-first contract with deferred shared-doc reconciliation`, `Right-sized Grill Routing`, and `Tracker and durable record policy`.
- Read if needed by the selected intake path with `scripts/read-reference-section.py`: `Intake modes`, `Full grill threshold`, `Grill conduct and fixed question format`, `Implementation confirmation gate`, and `Delegated Matt Pocock skill routing`.
- Templates after alignment closure only: `templates/local-work-packet.md`, `templates/issue-body.md`, and `templates/implementation-confirmation.md`.
- Do not read `REFERENCE.md` end-to-end or load PR/close templates during unresolved grill/preflight alignment.
## Parallel-safe write policy

Allowed during `init`:

- read shared docs and repo evidence;
- create or update one isolated GitHub issue draft/body target;
- create one unique local Work Packet seed draft file;
- write user-visible draft output when file write safety is unclear;
- record Implementation Contract, Scoped Overrides, and Proposed Shared Doc Updates inside the isolated draft only after required grill/preflight decisions are closed or auto-closed;
- for `full_grill_with_docs` with open blocking decisions, write only a minimal decision scaffold if a file is needed: evidence inspected, Decision Map, auto-closed decisions, question log, status, and next question.

Not allowed during `init` unless the session is explicitly serialized in the orchestration lane:

- source-code edits;
- implementation branch or worktree creation;
- direct edits to `AGENTS.md`, `docs/agents/*`, implementation plans, roadmap/index docs, CONTEXT docs, ADRs, verification docs, tracker config docs, or other shared source-of-truth docs.

If no tracker/local path is configured and ideation should still proceed, create a unique seed draft under `.scratch/work-packets/` or output a draft without writing. Use an ID like `wp-<yyyymmddhhmmss>-<slug>`; if a collision is possible, append a short random or content hash suffix.

## Owner gate

Run this before ideation when `agent-env.<slug>.md` does not exist. It is a blocking precondition:
downstream modes STOP without a profile, so `init` must produce one.

1. Ask the owner once for a display name. Ask only this; do not bundle it with grill questions.
2. Derive a slug: lowercase, keep `a-z0-9` only, drop spaces and non-alphanumerics. Example:
   `Jane Doe` -> `janedoe`; the owner may shorten it (e.g. `jane`). Confirm the slug. The slug
   is used only for the gitignored filename `agent-env.<slug>.md` and for branch prefixes — never as
   a display name.
3. Clone `templates/agent-env.template.md` to `agent-env.<slug>.md` at the repo root.
4. Fill it from evidence: run `git remote -v`, compute `remote_match` (SSH alias token, or HTTPS
   `host/org`), set `expected_remote_match`, and add a per-repo block. Detect the integration branch
   with `git symbolic-ref --quiet refs/remotes/origin/HEAD`; if unset, leave `integration_branch`
   for the owner to set. Pre-fill `protected_branches: [main]` and the tracker-channel binding for
   the current `(remote_match, orchestrator)` using the `Access path resolution` reference section.
5. Ask the owner to confirm the tracker-channel binding and protected branches. Do not invent a
   channel: if the correct channel is unknown, record `handoff` and note the open setup question.
6. Confirm `agent-env.*.md` is gitignored at the repo root before writing anything sensitive. The
   profile is local-only and must never be committed.

After the profile exists and the binding is confirmed, continue with ideation.

## Process

Grill language rule: in `init`, write every direct user-facing grill question block in Korean (`ko-KR`) for `full_grill_with_docs`, `docs_grill_preflight`, and `targeted_grill`. The Decision Map may also be Korean; keep canonical section names and repo terms in English only when that improves clarity.

1. Run the Owner gate first when `agent-env.<slug>.md` is missing, then start from the Cold Start Context Budget in `SKILL.md`, then read only this mode file and the Required reads above. Do not read `REFERENCE.md` end-to-end. Read `templates/local-work-packet.md`, `templates/issue-body.md`, and `templates/implementation-confirmation.md` only after every direct grill/preflight question has an explicit user answer, evidence-backed closure, or recorded removal from the Decision Map.
2. Before repo exploration, write short Context Intake Notes: `Known from prompt`, `Must verify from repo`, `Do not read yet`, `Delegation candidates`, direct reads used, searches used, and whether subagent delegation is available.
3. Inspect `git status --short` to detect whether shared-file writes would be unsafe. Dirty state does not block isolated `init`, but it forbids shared-doc edits.
4. Resolve `active-goal` from the repo's active implementation plan, usually `docs/implementation-plan.md`, when requested.
5. If repo-local workflow/tracker/domain config is missing or drifted, continue with ideation-only draft when safe. Mark it `draft` or `needs-confirmation`, record missing config, and recommend `$project-agent-bootstrap` before `ready`/implementation if the missing config affects correctness.
6. If the input is a raw issue/backlog item, delegate to `triage` or perform minimal triage.
7. If the input is a bug, failing verification, flaky behavior, or performance problem, choose `diagnose_first` and establish the feedback loop before planning the fix.
8. Choose the lightest safe intake mode from `REFERENCE.md`, applying `Right-sized Grill Routing` with a full-grill bias before selecting a lighter mode. For non-trivial internal process, skill-maintenance, tracker hygiene, context-budget, verification delegation, mode-routing, durable-record, or close/done-policy work, default to `full_grill_with_docs` unless evidence proves the change is mechanical, local, and branch-free. Use `targeted_grill` only for a few already-known blockers, `docs_grill_preflight` for evidence-first light checks, and `full_grill_with_docs` when the decision tree itself must be walked.
9. If the full grill threshold is met, choose `full_grill_with_docs`, delegate to `grill-with-docs`, present the Decision Map from `REFERENCE.md`, ask one fixed-format question at a time, and stop. Strengthen full grill with the Full Grill Decision Tree Protocol, but keep the user-facing output to the Decision Map/status plus the next fixed-format question. Do not synthesize a roadmap, PRD summary, vertical slices, acceptance criteria, Implementation Contract, Codex goal, or Implementation Confirmation Brief while direct grill questions remain unanswered. If an isolated local file is useful, fill only a decision scaffold using `templates/grill-decision-map.md`, not a proposed implementation plan.
10. If a lighter domain check is enough, choose `docs_grill_preflight`: inspect code/docs first, auto-close evidence-backed terminology decisions, present or record the mini Decision Map, and ask only the highest-impact remaining fixed-format question. Escalate to `full_grill_with_docs` when evidence opens dependent product/domain branches.
11. For `targeted_grill`, present a compact Decision Map for the already-known blockers, then ask at most 3 blocking questions one at a time. Use the fixed question format when the question is product/domain/user-outcome oriented.
12. For `prototype_first`, delegate to `prototype`; capture what the prototype answers and where the durable answer must be recorded.
13. For `architecture_first`, perform bounded architecture discovery or delegate to `improve-codebase-architecture`; do not turn it into a broad refactor.
14. Continue past this point only after the selected intake path has closed all blocking decisions, or after repo evidence auto-closes them. If `full_grill_with_docs` still has a direct question pending, stop before this point and output only the Decision Map/status plus that question.
15. If enough context exists, use `to-prd` semantics to synthesize a PRD summary after alignment.
16. Create or update exactly one isolated local Work Packet seed draft using `templates/local-work-packet.md` or prepare one issue body draft using `templates/issue-body.md`. For unresolved `full_grill_with_docs`, this draft must remain a minimal decision scaffold and must not pre-fill roadmap, PRD, vertical-slice, acceptance, or confirmation sections as if decisions were closed. If GitHub Issues are configured, record that the seed is not durable until `issue` publishes or updates the parent issue.
17. Record an Implementation Contract, Scoped Overrides when needed, and Proposed Shared Doc Updates instead of editing shared docs.
18. Create an Implementation Confirmation Brief using `templates/implementation-confirmation.md` only after grill/preflight decisions are closed enough to state purpose, core target, observable changes, non-goals, assumptions, risks, and verification signal.
19. If explicit confirmation is missing and `--confirmed` was not supplied, set status to `needs-confirmation` and ask the single confirmation question from `REFERENCE.md`. Do not ask the confirmation question in the same response as an unanswered grill question.
20. If confirmation is present, record the evidence and allow `ready` to proceed.
21. Create or update the `Phase handoff capsule` in the draft or tracker surface with decisions, open gates, `grill_route`, `grill_route_reason`, full-grill triggers present or ruled out, files read, tracker/doc mutations, next mode, and next stop condition.

## Output only

1. Work Packet seed path, issue draft target, or user-visible draft marker
2. Whether `init` used isolated parallel-safe writes
3. Intake mode
4. Decision Map status, if grill/preflight was used
5. Full grill/preflight decision and reason
6. Implementation Contract summary, or `deferred: grill questions still open`
7. Proposed Shared Doc Updates summary
8. Implementation Confirmation Brief, or `deferred: grill questions still open`
9. Confirmation status
10. One fixed-format grill, confirmation, or blocking question, if any
11. Ready/not-ready status
12. One-sentence next step
