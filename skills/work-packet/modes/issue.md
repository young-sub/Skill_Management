# Mode: issue

Finalize the durable issue record for a ready Work Packet as a local body file, pending batch
publish. This mode manages the issue as a local document and does NOT call `gh`, the connector, or
any tracker channel. Actual GitHub Issue creation/update happens later in `publish` mode, which can
batch several packets at once. Until then the local Work Packet doc is the durable tracker and the
record carries `tracker_publish_state: local_pending`.

## Prerequisites

- Work Packet is `ready-for-agent`.
- Implementation Contract is recorded.
- Implementation Confirmation Brief is recorded.
- User confirmation is recorded or validly supplied with `--confirmed`.
- No blocking full-grill, product, architecture, tracker, verification, or shared-doc reconciliation decisions remain.
- Tracker policy is known, or a safe explicit fallback is provided.


## Required reads

- Precondition (before any tracker action): resolve the access path via the `Access path resolution` reference section — read the env profile, match the git remote, detect the orchestrator, decide the tracker channel. STOP if the profile is absent.
- Always read: this file, the `Phase handoff capsule` if present, the ready Work Packet or tracker issue sections needed for publishing, and these sections via `scripts/read-reference-section.py`: `Access path resolution`, `Metadata-first Tracker I/O`, `Tracker and durable record policy`, `Document layout and merge safety`, `Korean reporting and summary policy`, `Implementation confirmation gate`, and `Context budget and search hygiene`.
- Read if needed: `docs/agents/issue-tracker.md`, root/local `AGENTS.md`, GitHub issue templates or label evidence, and `Bounded auto approval policy` via `scripts/read-reference-section.py` when running under `auto`.
- Template: `templates/issue-body.md`.
## Parallel rules

GitHub issue creation may be parallel only when each session creates or updates a different issue and does not mutate shared label/project/milestone configuration.

Local markdown issue creation may be parallel only when local markdown is explicitly configured and each session writes a unique packet file. Shared tracker indexes, `AGENTS.md`, `docs/agents/*`, roadmap docs, implementation plans, and source-of-truth docs are serialized.

## Process

1. Read the Required reads above, tracker config, `templates/issue-body.md`, and the confirmation brief with metadata-first reads and section-only body access. Do not read `REFERENCE.md` end-to-end.
2. Determine the configured tracker from `docs/agents/issue-tracker.md` and root/local `AGENTS.md`; do not infer local markdown tracking only because `.scratch/` exists.
3. Note the resolved tracker channel from the access-path precondition, but do not act on it here. `issue` mode never calls `gh`, the connector, or `mcp_pat`; all live tracker writes are deferred to `publish`.
4. Finalize exactly one parent body at the path configured by `docs/agents/issue-tracker.md`. For
   `local_markdown`, use its owner/feature-namespaced plan directory (for example
   `docs/plans/<owner-slug>/<feature-slug>/work-packet.md`) and honor its gitignore policy. For a
   remote tracker pending publish, use the configured tracked `local_pending` body-file surface.
   Record the local ref and do not create or update a remote issue here.
5. When GitHub Issues are the configured tracker, the parent issue becomes the durable tracker only after `publish` runs. Before that, the local Work Packet doc is durable and `run` proceeds from its local ref; do not stop merely because no remote issue exists yet.
6. Keep the body publishable: exact title, labels, and a body file ready for batch `publish`, so the later live call is mechanical.
7. Do not satisfy `issue` mode by writing only to `.scratch/` when GitHub Issues are configured; use the durable local Work Packet path so the `local_pending` record survives review.
8. If local markdown tracking is explicitly configured, create or update the local Work Packet in
   that configured path. When the plan tree is gitignored, mirror settled shared decisions and
   verification evidence to tracked source-of-truth docs before close or cross-clone handoff.
9. Prepare child issue bodies as separate `local_pending` records only when the Work Packet is too large for one PR, requires parallel ownership, or the user/repo asks for issue fan-out.
10. Apply the repo's mapped `ready-for-agent` state only when confirmation, acceptance criteria, verification plan, and shared-doc reconciliation are complete.
11. Include Korean non-normative summary and English canonical sections. Follow the `Korean reporting and summary policy` reference section and `templates/korean-summary.md`; for issues, emphasize the workflow bottleneck, expected review decision, and unresolved assumptions only as needed.
12. Ensure the issue body includes Implementation Contract, Scoped Overrides, Proposed Shared Doc Updates, and `Phase handoff capsule` so implementation can proceed without relying on hidden local state.
13. Update the `Phase handoff capsule` with the local body-file ref, `tracker_publish_state: local_pending`, `published_body_ref` left empty until publish, next mode, and next stop condition.

## Issue body must include

Use `templates/issue-body.md`.

## Output only

1. Local issue body-file path and `tracker_publish_state: local_pending`
2. Title/labels prepared
3. Confirmation status
4. Shared-doc reconciliation status
5. Child issue bodies prepared, if any
6. Next command (`run`, or `publish` when batching pending records)
