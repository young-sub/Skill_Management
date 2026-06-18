# Mode: publish

Publish pending local Issue/PR records to the configured tracker, in one explicit human-triggered
batch. This is the ONLY mode that performs live tracker writes (`gh`, `mcp_pat`, or `connector`).
It is deliberately outside `auto`: `auto` produces local `local_pending` records and stops; the owner
runs `publish` when ready to push code and create/update Issues and PRs together.

`publish` can batch several Work Packets at once. Already-published records are isolated into an
archive surface so a later batch never re-publishes them.

## Prerequisites

- One or more local records carry `tracker_publish_state: local_pending` (Issue or PR body files).
- Implementation and verification for each record are complete, or the record is an Issue-only
  publish with no code dependency.
- Explicit human authorization to publish. `publish` is never auto-approved by `auto`.

## Required reads

- Precondition (before any tracker action): resolve the access path via the `Access path resolution` reference section — read the env profile, match the git remote, detect the orchestrator, decide the tracker channel. STOP if the profile is absent.
- Always read: this file, the `Phase handoff capsule` if present, the pending local Issue/PR body files, `git status --short`, `git diff --stat` or changed filenames, and these sections via `scripts/read-reference-section.py`: `Access path resolution`, `Metadata-first Tracker I/O`, `Durable Body Ownership`, `Tracker and durable record policy`, `Branch naming policy`, `Final active-branch refresh policy`, and `Verification evidence`.
- Read if needed: `Bounded auto approval policy` via `scripts/read-reference-section.py` only to confirm what `publish` is NOT covered by, and `Korean reporting and summary policy`.
- Templates: `templates/issue-body.md`, `templates/pr-body.md`. Full raw bodies are read from the local files; do not re-read `REFERENCE.md` end-to-end (escalation, not default).

## Process

1. Collect every record with `tracker_publish_state: local_pending` in scope. Confirm with the owner which packets to include in this batch; do not publish records the owner did not authorize.
2. Resolve the tracker channel once per repo from the `Access path resolution` reference section. The channel is `gh`, `mcp_pat`, `connector`, `handoff`, or `none`. Never probe the network to decide it.
3. Track two independent axes per record in the capsule: `git_publish_state` (`local_only` -> `committed` -> `branch_pushed`) and `tracker_publish_state` (`local_pending` -> `issue_published`/`pr_published`, or `handoff_pending`). They are not a single linear sequence: code push can succeed while tracker publish stays pending, and vice versa.
4. Code channel first (always available over SSH): push the implementation branch for each packet that has a diff, and set `git_publish_state: branch_pushed`. Push to the implementation branch only — never to a protected branch (see `close`/`next` for base reflection rules).
5. Tracker channel by resolved value:
   - `gh`: create/update the Issue and PR from each local body file using `gh` with explicit `--repo`; apply sandbox escalation per the profile. Retain only URL/number/state/refs and `published_body_ref`.
   - `mcp_pat`: create/update via the GitHub MCP server using the repo `.mcp.json` PAT.
   - `connector`: create/update via the Codex git connector.
   - `handoff`: do not attempt a live call. Emit the exact title, body file, labels, and the exact command (for example a `gh` invocation) for the owner or the connector-capable tool to run out of band. Set `tracker_publish_state: handoff_pending` and keep the local body file in the active surface.
   - `none`: leave the record as a durable local document; there is no remote to publish to.
6. Order within a packet: publish the parent Issue first, then the PR, so the PR can link the Issue. Link with `Related to #N`/`Part of #N` unless the PR fully resolves the Issue and targets the resolved base branch, in which case a closing keyword is allowed.
7. On partial failure, record exactly which axis/record succeeded. If the branch pushed but the Issue create failed, keep `git_publish_state: branch_pushed` and `tracker_publish_state: local_pending`, emit the exact retry command, and stop that record without rolling back the push. Do not loop retries.
8. On success for a record, move its local Issue/PR body file from the active surface into the archive surface (the repo's configured archive path, for example `docs/archive/work-packets/`, or `.scratch/work-packets/archive/` when only local drafts exist). Set the record's `tracker_publish_state` to `issue_published`/`pr_published` and store `published_body_ref`. Archiving isolates completed records so the next batch never re-publishes them.
9. Never re-publish a record whose body file already lives in the archive surface or that already has a `published_body_ref`. Treat an archived record as immutable history.
10. Include the Korean non-normative summary and English canonical sections on published Issues/PRs per the `Korean reporting and summary policy`.
11. Update the `Phase handoff capsule` per record with channel, both publish-state axes, `published_body_ref`, archive destination, and next stop condition. Do not refetch full Issue/PR bodies only to confirm a mutation.

## Output only

1. Records published, by Issue/PR URL or number
2. Records handed off (`handoff_pending`) with exact command
3. Records archived (moved out of the active surface)
4. `git_publish_state` and `tracker_publish_state` per record
5. Partial-failure records with retry command, if any
6. Next command (`close`, or `publish` again for remaining pending records)
