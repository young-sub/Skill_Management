---
name: update-matt-skills
description: Review a new Matt Pocock skills release and safely reconcile it into this repository. Use when the user asks to check, update, sync, or adopt upstream Matt skills, compare the local catalog with a release, or refresh UPSTREAMS.md.
disable-model-invocation: true
---

# Update Matt Skills

Update from a pinned release through evidence and semantic reconciliation. Do not implement a blind
sync program and do not treat the upstream default branch as a release.

## Workflow

1. Read `UPSTREAMS.md`, `AGENTS.md`, the active Work Packet when present, and the current active
   skill catalog. Preserve user changes and local ownership boundaries.
2. Inspect the official upstream release, release notes/changelog, manifest/catalog, license, tag,
   and commit SHA. Use primary sources. Record the reviewed version and date.
3. Compare every upstream candidate with the active local catalog. For each candidate record:
   distinct role, referenced resources/dependencies, name or trigger collision, invocation policy,
   mutation/external-operation risk, and ownership classification.
4. Apply ownership rules from `UPSTREAMS.md`:
   - `upstream-derived`: update from the pinned release and retain only required host metadata;
   - `local-adapted`: reconcile upstream behavior with every documented protected local contract;
   - `local-owned`: do not overwrite; update routing references only when required.
5. Apply renames atomically: add the new directory, migrate active references and routes, remove the
   old active directory, then verify no active alias remains. Historical/provenance text may retain
   old names when clearly marked.
6. For user-invoked orchestrators, keep Claude and Codex explicit-only metadata aligned. Never
   weaken security, approval, tracker, protected-branch, or local-document policies merely to match
   upstream.
7. Run static checks and representative routing smoke tests before advancing the baseline. Verify
   folder/frontmatter names, duplicate names, linked resources, delegated reference closure,
   invocation metadata, ownership coverage, legacy-name removal, and local planning behavior.
8. Update `UPSTREAMS.md` only after checks pass. Record the new tag/SHA, ownership decisions,
   atomic replacements, retained adaptations, rejected/deferred candidates, and verification.

## Human Gate

Stop and wait for the user when an update would overwrite a `local-owned` skill, discard an
undocumented local behavior, change an external-operation/approval boundary, introduce an ambiguous
name or role collision, require credentials or destructive action, or leave a hard-to-reverse
architecture/product decision unresolved. Do not mark the update complete while the gate is open.

## Report

Report `added`, `updated`, `replaced`, `retained-local`, `rejected/deferred`, exact verification
commands and results, unverified items, remaining risks, and any required human decision.
