---
name: setup-agent-harness
description: Set up or repair repository Harness configuration when explicitly requested. Map existing ownership and commands before making the smallest useful configuration change.
---
<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/skills/setup-agent-harness/SKILL.md -->
<!-- Source-SHA256: 9b860ea4e126dfc147cd8817923cf3dfb842d1ac97d936d9e5b63778e1c47514 -->


# Setup Agent Harness

Use this Skill only for an explicit repository setup or Harness-repair request. Ordinary implementation work does not authorize Harness installation or revision.

Resolve this installed Skill directory as `<skill-root>` and run `<skill-root>/scripts/core_harness.py` ([runtime](scripts/core_harness.py)); do not assume the target repository contains that script. Consult the [project schema](schemas/project.schema.json), [documentation policy](references/documentation-policy.md), and templates only for the configuration being created or repaired.

1. Inspect instructions, manifests, CI, Git state, and the source/test/doc entry points needed to map the requested scope. Follow uncertain ownership boundaries selectively; do not recursively read every file. Static inspection cannot establish dynamic test success.
2. Preserve coherent paths and existing working configuration. Report mapping ambiguity before a dependent mutation. A repair changes the faulty mapping or capability; it does not restart full repository setup.
3. When present, load environment exceptions once and run only the relevant capability descriptors for a revision-bound baseline. Honor `skip_until_manual_reenable` and record fallback limits. Missing optional tools need not block unrelated configuration.
4. For initial setup, add `.harness/project.yaml`, a concise local router, and the configured documentation entry point (usually `docs/index.md`); preserve existing equivalents on repair. Ignore `/.work/`, `/.worktree/`, and `.harness/environment-exceptions.json`. Add architecture or verification docs only when they prevent recurring wrong decisions. Do not fabricate a documentation tree or move files to fit the template.
5. If cleanup is needed, prepare an exact plan and use its internal digest for application. Reuse authorization that already covers the displayed scope; obtain any missing approval for broad moves/removals or consequential CI/discovery changes. Routine setup configuration within the request does not need another approval ceremony.
6. Use the runtime transaction under `.work/transactions/` for cleanup/migration. Keep mapping, byte-preserving moves, reconciliation, and test reorganization separate when they need different verification. On failure, verify rollback to the captured state. Test-only moves preserve semantic identities and working selectors.

Report actual configuration changes, baseline results, and remaining mapping gaps. Repository setup does not authorize global provider or installed-Skill changes.
