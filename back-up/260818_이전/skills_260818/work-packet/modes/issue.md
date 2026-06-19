# Mode: issue

Publish or update the durable issue surface for a ready Work Packet.

## Prerequisites

- Work Packet is `ready-for-agent`.
- Implementation Contract is recorded.
- Implementation Confirmation Brief is recorded.
- User confirmation is recorded or validly supplied with `--confirmed`.
- No blocking full-grill, product, architecture, tracker, verification, or shared-doc reconciliation decisions remain.
- Tracker policy is known, or a safe explicit fallback is provided.


## Required reads

- Always read: this file, the `Phase handoff capsule` if present, the ready Work Packet or tracker issue sections needed for publishing, and these sections via `scripts/read-reference-section.py`: `Metadata-first Tracker I/O`, `Tracker and durable record policy`, `Korean reporting and summary policy`, `Implementation confirmation gate`, and `Context budget and search hygiene`.
- Read if needed: `docs/agents/issue-tracker.md`, root/local `AGENTS.md`, GitHub issue templates or label evidence, and `Bounded auto approval policy` via `scripts/read-reference-section.py` when running under `auto`.
- Template: `templates/issue-body.md`.
## Parallel rules

GitHub issue creation may be parallel only when each session creates or updates a different issue and does not mutate shared label/project/milestone configuration.

Local markdown issue creation may be parallel only when local markdown is explicitly configured and each session writes a unique packet file. Shared tracker indexes, `AGENTS.md`, `docs/agents/*`, roadmap docs, implementation plans, and source-of-truth docs are serialized.

## Process

1. Read the Required reads above, tracker config, `templates/issue-body.md`, and the confirmation brief with metadata-first reads and section-only body access. Do not read `REFERENCE.md` end-to-end.
2. Determine the configured tracker from `docs/agents/issue-tracker.md` and root/local `AGENTS.md`; do not infer local markdown tracking only because `.scratch/` exists.
3. If GitHub Issues are configured, inspect remote, default branch, issue templates, label mapping, and available GitHub interfaces such as MCP tools, `gh`, or API access.
4. If GitHub Issues are configured, create or update exactly one parent issue from a body file or short-output path when possible, and record only its URL/number/state/labels as the durable tracker reference. Prefer `gh` over connector mutations when connector output would return a full body.
5. If GitHub Issues are configured but no GitHub interface is available, output the exact issue title, body, labels, and creation command/API payload, then stop before `run`.
6. On the first GitHub auth, network, connector, or permission failure, emit the exact payload and stop. Do not retry repeatedly or treat `.scratch/` as durable tracking unless local markdown tracking is explicitly configured.
7. Do not satisfy `issue` mode by writing only to `.scratch/` when GitHub Issues are configured.
8. If local markdown tracking is explicitly configured, create or update the local Work Packet and mirror durable planning to tracked docs when the local path is gitignored and review durability is required.
9. Publish child issues only when the Work Packet is too large for one PR, requires parallel ownership, or the user/repo asks for issue fan-out.
10. Apply the repo's mapped `ready-for-agent` state only when confirmation, acceptance criteria, verification plan, and shared-doc reconciliation are complete.
11. Include Korean non-normative summary and English canonical sections. Follow the `Korean reporting and summary policy` reference section and `templates/korean-summary.md`; for issues, emphasize the workflow bottleneck, expected review decision, and unresolved assumptions only as needed.
12. Ensure the issue body includes Implementation Contract, Scoped Overrides, Proposed Shared Doc Updates, and `Phase handoff capsule` so implementation can proceed without relying on hidden local state.
13. Update the `Phase handoff capsule` with durable tracker reference, `published_body_ref`, issue mutation metadata, next mode, and next stop condition. Do not refetch the full issue body only to confirm the mutation.

## Issue body must include

Use `templates/issue-body.md`.

## Output only

1. Issue URL/path or exact creation command
2. State/labels
3. Confirmation status
4. Shared-doc reconciliation status
5. Child issues created, if any
6. Next command
