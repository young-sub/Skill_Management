---
name: setup-project-verification
description: Map all project functions and connect verification using existing requirements, commands and UI assets. Use for initial mapping or missing execution paths; resume completed partitions and preserve explicit verification gaps.
---
<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/skills/setup-project-verification/SKILL.md -->
<!-- Source-SHA256: 7f9bb30fa5659afe67248f4ee082bd28f42f224da0c31f4fbe297cb088531218 -->


# Setup Project Verification

Read [shared verification responsibilities](references/project-verification.md). Inspect existing project guidance, requirements, package/native commands, callers, fixtures and UI sources before adding anything. Distinguish first connection from reuse; identify exactly which pilot/project connections are absent. Preserve underlying product requirements.

1. Reconcile all functions in the agreed project/revision boundary against requirements, UI/routes, API/CLI, jobs, roles, flags and tests. Partition large maps by user flow with stable IDs. Each Feature links requirements, outcomes/invariants, variants, FE/API/Domain owners, state/data effects, existing guarantees, checks and gaps. Reuse the map/command registry. Use [workflow obligations](references/workflow-obligations.md) for resumable progress and omission detection. Unresolved candidates keep initialization PARTIAL; a first runnable flow confirms execution linkage, not complete mapping. Features without automatic checks remain in the map. Read `mapping_status` separately from overall task status; explicitly retain product-quality/data gaps as `product_findings` without treating their repair as map setup work. Unclassified or missing map content remains a mapping finding.
2. Inspect setup/teardown, pretest/migration and command forwarding for side effects. Identify source/dirty diff, dependencies, synthetic fixture, owned process/build/URL and cleanup. Honor manual capability disables and use the recorded fallback. Do not copy credentials, original DBs or uncommitted files into experiments.
3. Connect Launch → Doctor → Drive → Evidence → Cleanup through existing commands. HTTP 200 is readiness only: bind served source/build and launch/process evidence to the checkout. Do not stop an unknown server to obtain its port.
4. Run the actual path, including affected persistence/reload and relevant failure/normal cases. Propagate the native exit immediately, inspect discovered case/skip/error counts, and distinguish command failure from product assertion failure. Reuse the project's existing capture CLI when available, passing its explicit path from project guidance; otherwise retain the native command/output and target identity directly. Capture records execution and leaves product judgment to the project's adapter/observer.
5. Leave the shortest repeatable command and project discovery link with fixture/output/cleanup boundaries. Reuse existing AGENTS/index/guide as the project verify-product and ui-system entrypoints. Add a local Skill only for demonstrated repeated branching that those paths cannot express. Do not force Harness installation.

Use the same failing criterion after a repair and a nearby valid case; equivalent baseline GREEN is appropriate for preserved behavior. Preserve raw failures. If execution is unavailable, record the missing observation, cause, fallback and resume condition, and continue independent connections. Finish only the named verified scope; metadata and generated files do not establish the first actual flow.
