# Upstream Provenance And Ownership

## Matt Pocock Skills Baseline

- Repository: `https://github.com/mattpocock/skills`
- Reviewed release: `v1.1.0`
- Release commit: `d574778f94cf620fcc8ce741584093bc650a61d3`
- Reviewed on: 2026-07-15
- License: MIT, Copyright (c) 2026 Matt Pocock
- Evidence: release notes, `.claude-plugin/plugin.json`, release tree, and bundled skill files at
  the release commit.

Use the release tag as the reproducible import baseline. Main-branch changes after the tag are
research evidence only until a later update explicitly advances this file.

## Ownership Definitions

- `upstream-derived`: upstream is the content source; update from a pinned release with local
  invocation metadata added only when required by this repository's host support.
- `local-adapted`: upstream supplies the discipline, but a named local contract must be preserved
  through semantic reconciliation.
- `local-owned`: this repository owns the behavior; never overwrite it from Matt Pocock upstream.

## Active Local Skill Ownership

| Local skill | Ownership | v1.1.0 action / protected contract |
|---|---|---|
| `caveman` | local-owned | Retain; removed upstream and not part of this cleanup |
| `codex-delegation` | local-owned | Retain |
| `diagnosing-bugs` | upstream-derived | Replaces `diagnose`; use pinned release behavior |
| `finance-research` | local-owned | Retain |
| `find-skills` | local-owned | Retain |
| `frontend-design` | local-owned | Retain |
| `grill-me` | upstream-derived | Retain current active copy; not a target of this adoption packet |
| `grill-with-docs` | local-adapted | Adopt `grilling` and `domain-modeling` dependencies while preserving docs-aware local orchestration gates |
| `grilling` | upstream-derived | Adopt from pinned release |
| `domain-modeling` | upstream-derived | Adopt from pinned release |
| `codebase-design` | upstream-derived | Adopt from pinned release |
| `code-review` | upstream-derived | Adopt from pinned release |
| `handoff` | upstream-derived | Retain current active copy; not a target of this adoption packet |
| `improve-codebase-architecture` | local-adapted | Adopt `codebase-design` and `domain-modeling` as vocabulary sources |
| `multi-agent-review` | local-owned | Retain |
| `ask-matt` | upstream-derived | Adopt from pinned release; explicit-only |
| `implement` | upstream-derived | Adopt from pinned release; explicit-only and never nested automatically inside Work Packet |
| `project-agent-bootstrap` | local-owned | Update routing/config names only; never replace from upstream |
| `prototype` | upstream-derived | Update from pinned release |
| `research` | upstream-derived | Adopt from pinned release |
| `resolving-merge-conflicts` | upstream-derived | Adopt from pinned release tree |
| `setup-matt-pocock-skills` | local-adapted | Adopt current config vocabulary while preserving repo control-plane coexistence |
| `tdd` | upstream-derived | Update from pinned release and its current bundled resources |
| `teach` | upstream-derived | Retain current active copy; not a target of this adoption packet |
| `theme-factory` | local-owned | Retain |
| `to-tickets` | local-adapted | Replaces `to-issues`; preserve one-PR, 2-5 slice and wide-refactor contract |
| `to-spec` | local-adapted | Replaces `to-prd`; preserve ignored local-document tracker contract |
| `triage` | local-adapted | Adopt current claim-verification flow; gate external PR request behavior behind explicit config |
| `update-matt-skills` | local-owned | Review and reconcile pinned upstream releases; never blind-sync |
| `wayfinder` | upstream-derived | Adopt from pinned release; explicit-only |
| `webapp-testing` | local-owned | Retain |
| `web-artifacts-builder` | local-owned | Retain |
| `work-packet` | local-owned | Preserve end-to-end orchestration and Goal-as-run-backend boundary |
| `writing-great-skills` | upstream-derived | Replaces `write-a-skill`; explicit-only |
| `zoom-out` | local-owned | Retain; removed upstream and not part of this cleanup |

`back-up/` is historical and excluded from the active catalog.

## Atomic Replacements

| Remove active name | Install active name | Release evidence |
|---|---|---|
| `diagnose` | `diagnosing-bugs` | v1.0.0 breaking rename |
| `to-prd` | `to-spec` | v1.1.0 planning unification |
| `to-issues` | `to-tickets` | v1.1.0 planning unification |
| `write-a-skill` | `writing-great-skills` | v1.0.0 breaking replacement |

Long-lived active aliases are not allowed. Historical and provenance text may mention old names.

## Selected Additions

| Skill | Invocation at adoption | Role |
|---|---|---|
| `domain-modeling` | model-invoked | domain vocabulary and ADR discipline |
| `codebase-design` | model-invoked | deep-module, interface, seam, and adapter vocabulary |
| `code-review` | model-invoked / explicit delegation | Standards and Spec review |
| `grilling` | model-invoked | shared interview primitive |
| `research` | model-invoked | primary-source research artifact |
| `resolving-merge-conflicts` | model-invoked | merge/rebase conflict loop |
| `diagnosing-bugs` | model-invoked | hard bug and performance diagnosis |
| `to-spec` | explicit-only | settled-context specification |
| `to-tickets` | explicit-only | tracer-bullet slices and blocking edges |
| `implement` | explicit-only | standalone upstream execution flow; never nested automatically inside Work Packet/Goal |
| `wayfinder` | explicit-only | foggy effort too large for one session |
| `ask-matt` | explicit-only | standalone router; never auto-enter an active Work Packet |
| `writing-great-skills` | explicit-only | skill-authoring reference |

The v1.1.0 plugin manifest lists all selected additions except `resolving-merge-conflicts`; that
skill exists in the signed release tree and is intentionally selected by the local adoption plan.

## Local Adaptation Rules

1. Compare the pinned upstream directory with the active local directory before replacement.
2. Copy upstream-derived content with its referenced sibling resources and license provenance.
3. Reconcile local-adapted behavior semantically; record retained contracts in this file or the
   active Work Packet.
4. Never copy upstream files over local-owned skills.
5. Apply renames as add + reference migration + old-directory removal in one verified slice.
6. User-invoked orchestrators must carry Claude `disable-model-invocation: true` and Codex
   explicit-only invocation metadata when supported.
7. Advance the release/tag/SHA only after static checks and representative routing smoke tests pass.

## Rejected Or Deferred Release Content

- Deprecated, in-progress, personal, and unrelated misc skills are not active adoption targets.
- `caveman` and `zoom-out` remain local-owned despite upstream removal.
- Main-branch commits after `v1.1.0` are deferred to the next `$update-matt-skills` review.

## Adoption Verification

- `python -m unittest -v tests.test_audit_matt_skills` - 11 tests passed.
- `python scripts/audit_matt_skills.py` - passed names, resources, ownership, invocation,
  local-planning, legacy-reference, and Work Packet routing checks.
- `python skills/work-packet/scripts/audit-work-packet-skill.py` - passed.
- Pinned upstream-derived file hashes match `v1.1.0`, excluding local
  `agents/openai.yaml` host metadata.
- `git diff --check` - passed; line-ending conversion warnings only.
- `skill-creator/scripts/quick_validate.py` - not run because the current Python environment lacks
  PyYAML; equivalent frontmatter/name checks passed through `audit_matt_skills.py`.
