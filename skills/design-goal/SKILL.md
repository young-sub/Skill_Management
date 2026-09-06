---
name: design-goal
description: Create or revise a Harness Item contract when explicitly requested or persistent coordination is needed across review boundaries or material risk. Explore unresolved product decisions before creating a contract; use direct development for small, clear changes.
---
<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/skills/design-goal/SKILL.md -->
<!-- Source-SHA256: f49ef2e2548bce299f3e1badb1ea91c7aa8a0390be267e98b98add854bd90832 -->


# Design Goal

Use [the runtime](scripts/core_harness.py) to create work; consult [the contract schema](schemas/contract.schema.json) for field details. A host Goal is optional tracking and is created only when requested.

1. Inspect the affected behavior, callers, tests, and current constraints. Resolve internal choices from convention; ask only about decisions that change scope, observable behavior, permission, or recovery risk. Do not repeat an answered interview.
2. Build observable Items matching meaningful review boundaries with concrete steps and Done criteria. Add tests or other checks only when they provide distinct evidence; an Item with no product behavior may leave `tests` empty when its Done evidence is sufficient. Never add a check just to fill a field. Declare each Item's `decision` and `material_risks` explicitly, even when resolved/empty. At `design-create` input only, irrelevant `terms`, `depends_on`, and `non_goals` may be omitted; the runtime fills empty lists and defaults omitted `priority` to `core`. Saved contracts remain fully canonical. Include real dependencies and optional priority when they exist.
3. Validate Item/Done/dependency coverage and any checks that actually add evidence. Unresolved required decisions block authorization; present a draft and its open questions without calling `design-create` when a decision is still open. Only a resolved, authorized contract is persisted in runtime state. Ordinary work is default-authorized; a veto remains in force. Structured material risks require explicit user authorization, which may already exist in this conversation. Reuse matching authorization through `--intent explicit_approve`; a CLI flag or digest does not establish permission by itself.
4. Once required decisions are resolved and the contract has passed the coverage check, invoke `design-create` to reserve `.work/goals/active/<work-id>` atomically and write `contract.json`. Omit the work ID for a generated identity; an explicit ID conflicts instead of overwriting. Never pre-create the work root or write its authority files independently.

Summarize the work path, observable Items, and material open decisions. If implementation is authorized, continue through `execute-codex-goal` without another approval step. A design-only request ends with the design.
