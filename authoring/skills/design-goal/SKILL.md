---
name: design-goal
description: Design a Harness Item contract for explicitly requested planning, multiple review boundaries, material risk, or unresolved product decisions. Use ordinary development directly for small, clear changes.
---

# Design Goal

Use [the runtime](scripts/core_harness.py) to create work; consult [the contract schema](schemas/contract.schema.json) for field details. A host Goal is optional tracking and is created only when requested.

1. Inspect the affected behavior, callers, tests, and current constraints. Resolve internal choices from convention; ask only about decisions that change scope, observable behavior, permission, or recovery risk. Do not repeat an answered interview.
2. Build one to five observable Items with concrete steps, tests, and Done criteria. Declare each Item's `decision` and `material_risks` explicitly, even when resolved/empty. At `design-create` input only, irrelevant `terms`, `depends_on`, and `non_goals` may be omitted; the runtime fills empty lists and defaults omitted `priority` to `core`. Saved contracts remain fully canonical. Include real dependencies and optional priority when they exist.
3. Invoke `design-create` to reserve `.work/goals/active/<work-id>` atomically and write `contract.json`. Omit the work ID for a generated identity; an explicit ID conflicts instead of overwriting. Never pre-create the work root or write its authority files independently.
4. Validate Item/test/Done/dependency coverage. Unresolved required decisions block authorization. Ordinary work is default-authorized; a veto remains in force. Structured material risks require explicit user authorization, which may already exist in this conversation. Reuse matching authorization through `--intent explicit_approve`; a CLI flag or digest does not establish permission by itself.

Summarize the work path, observable Items, and material open decisions. If implementation is authorized, continue through `execute-codex-goal` without another approval step. A design-only request ends with the design.
