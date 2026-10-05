---
name: agent-workflow
description: Coordinate a coding task from a natural-language request through relevant project capabilities, actual verification, and results. Use for connecting project verification, verifying or viewing feature results, repairing user feedback, improving the development workflow, or reusing UI standards. Select only the needed procedures; ordinary small edits stay direct.
---
<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/skills/agent-workflow/SKILL.md -->
<!-- Source-SHA256: 3733e9b6f404846b6aa75499fd01122a92c83b9238d85be2748e6f782a04008e -->


# Agent Workflow

Read the project AGENTS/index, current checkout and dirty baseline, requirement sources, and applicable capability exceptions once. Identify the user's intent, authorized changes, affected Feature and expected outcome. Reuse that investigation and evidence across the selected capabilities. Do not require the user to name Skills or repeat their order.

| Request | Select the necessary work |
| --- | --- |
| Initial project verification | Available `setup-project-verification`; reconcile the complete function map, partition/resume large surveys, then connect actual checks. Map completeness and execution coverage are separate. |
| Implement a feature | Existing development workflow; requirements and touched callers first. If the affected Feature lacks a runnable verification connection, use the setup responsibility for that missing path, then implement, verify and update affected map/guide/active selectors in the same functional commit. Small work needs no contract. |
| Verify a feature | Project verification guide/adapter; select checks from changed behavior, run the real native and affected user flow, inspect raw outcomes. |
| Show existing results | Read existing plan, capture and raw observations only. Separate original judgment from current reuse. Do not run tests, repair files or start services. |
| Inspect/improve the development workflow | Available `maintain-project-verification` plus `maintain-agent-harness` when actual Harness mapping/cohort/retention is involved. Inspect shared facts once and retain both areas' findings. Audit-only stays read-only; authorized improvements include repair and recheck. |
| Feedback or recurrence | Available `diagnose`; trace expected behavior through callers, state and data to its owner, fix and prevent the concrete failure. |
| Improve UI consistency or standards | Discover project UI guide/token/component paths and use the relevant existing UI capability. Repair shared implementation and affected guidance, then verify actual states and subsequent reuse. |

Load [verification responsibilities](references/project-verification.md) for setup, verification, maintenance or feedback. For feedback/UI work also read [repair and reuse](references/repair-and-reuse.md). If a named capability is unavailable, perform its bounded responsibility using project commands; do not silently treat missing checks as passed or install a new framework.

For configured projects, [workflow obligations](references/workflow-obligations.md) provides the direct audit/resume CLI. Consume its affected references and perform the required semantic work. Local consistency and host-protected acceptance are distinct; the CLI reports the unsupported enforcement boundary explicitly.

For existing structured project evidence, the bundled [read-only viewer](scripts/verification_results.py) joins a project plan, capture, adapter assessment and raw observations. Read its [input and reuse contract](references/result-viewer.md); preserve the project's native report format and use its criterion/observation pointers. It never launches a recorded command. If the project has no compatible plan, inspect raw directly and report the missing binding; do not manufacture a successful plan or silently execute during lookup.

Keep a single concise plan for nontrivial work. Use the existing Harness contract only when coordination/risk or the user requires it. Never force Full, all playbooks, a fixed agent count or new setup on every request. Current user authorization remains authoritative; global installs, provider changes and publishing are separate effects.

For material persistence or subtle cross-layer changes, use available independent review with bounded context: requirements, base/diff, actual target, raw evidence, permitted fixture/output paths. Do not supply the desired patch/verdict or let the verifier change the product/oracle. Verify its material claims yourself. Return ISSUES with reproduction and owner to the implementer; recheck only evidence invalidated by the resulting diff. BLOCKED retains cause, fallback and resume condition while independent work continues.

Report Feature, criteria, selected/excluded checks, actual observations and remaining gaps. Preserve product, Harness and UI outcomes separately; ISSUES and BLOCKED can coexist. Source changes, generated distribution, temporary installation, product behavior, Agent behavior and real-environment application are different claims. Metadata, a verifier file or submitted PASS does not prove execution.
