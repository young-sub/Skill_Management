---
name: setup-agent-harness
description: Map and configure greenfield or brownfield repositories with the Core-First Agent Harness.
---
<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/skills/setup-agent-harness/SKILL.md -->
<!-- Source-SHA256: 5721fd6f4287f84ad9ed21c8804b9c9936973248502c290dfa1ba7d08587f31f -->


# Setup Agent Harness

Use this Skill only for an explicit repository setup or Harness-repair request. Ordinary implementation work does not authorize Harness installation or revision.

Resolve this installed Skill directory as `<skill-root>`. The runtime path is `<skill-root>/scripts/core_harness.py`; use [the runtime](scripts/core_harness.py), [the project schema](schemas/project.schema.json), [the documentation policy](references/documentation-policy.md), and the bundled templates as the contract. Do not assume the target repository contains that script.

1. Read root/nested instructions, manifests, CI selectors, documents, source, tests, fixtures, Git state, boundaries, and worktrees without executing repository content. Dynamic test evidence remains `unknown`.
2. Build a mapping-first proposal. Preserve coherent existing paths; report ambiguous authority, path ownership, nested repositories, aliases, or unknown test impact without mutation.
3. After the static proposal is valid, run only the capability descriptors needed to establish a useful revision-bound baseline. Ask when the command crosses a high-risk approval boundary.
4. Install `.harness/project.yaml`, a concise router, and `docs/index.md` before proposing moves. Ensure the repository ignore file owns `/.work/` and `/.worktree/` so ephemeral state and project-local worktrees never escape or enter tracked inventory. Record pre-existing debt only when it would otherwise block relevant work.
5. Apply only the displayed cleanup plan with its internal digest. Separate mapping, byte-preserving moves, content reconciliation, translation, removal, and test reorganization. The human approves the displayed plan once and never pastes a hash.
6. Journal the transaction under `.work/transactions/`; on a fault restore the exact pre-transaction tracked tree. Document/test-only changes must preserve production hashes. Test-only moves also preserve path-independent semantic identities and selectors.

Require focused approval for broad moves/removals, ignore or CI/discovery changes, destructive actions, or boundary-crossing migration. Never edit global provider configuration or installed Skills.
