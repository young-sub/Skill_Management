# Global Guidance Ownership

The latest global contract always lives in the dedicated [authoring/global/](../../authoring/global/AGENTS.md) folder. Update this repository copy in the same revision as the actual global targets. Its LF checkout policy preserves equality with the installed source. It is separate from the repository router and is not a generated public Skill resource. Every revision also retains the previous global bytes in the separate backup subtree.

## Update Procedure

1. Resolve the actual target from `CODEX_HOME` and inspect `AGENTS.override.md` before choosing a file. A default `~/.codex/AGENTS.md` and an account-specific global may coexist; inspect each intended target rather than assuming both are active.
2. Before changing a global file, create a unique `back-up/global-agents/<date-time>/` directory and copy its exact bytes there. Use separate filenames for distinct targets, such as `AGENTS.md` and `account-AGENTS.md`; record source paths, byte lengths, and SHA256 hashes in `sources.json`.
3. Verify each snapshot against its source and its Git blob. This backup subtree disables Git text conversion in `.gitattributes` so checkout preserves the captured bytes. Historical snapshots are immutable and are excluded from ordinary cleanup. If backup or verification fails, leave the global target unchanged.
4. Revise the maintained source, keep it under 100 lines, and review the behavioral differences with the repository routing and affected skills. Existing user authorization for that revision covers its named global targets; backup does not grant broader configuration permission.
5. Recheck each target against its captured hash immediately before replacement. Stop on unexpected concurrent changes. Write the reviewed source only to the authorized targets and verify exact byte equality afterward.
6. Commit the maintained source, new snapshots, and affected guidance together. A later revision repeats the backup process even when Git already contains the source. Start a new agent session to verify instruction discovery; an existing session may retain its originally loaded instructions.

Snapshot files are restoration evidence, not active instructions. Restoring a historical revision also starts by backing up the current target. Do not edit installed Skills, provider settings, credentials, or other global files as part of this procedure.

## Current Operating Boundaries

Small work uses direct implementation and appropriate verification. Non-trivial work has one concise plan; a contract is reserved for multiple review boundaries, material risk, unresolved product decisions, or an explicit request. Existing approvals carry forward within scope. The configured model floor is GPT-5.6 Sol, with GPT-6 Astra also allowed; subagents inherit the current model by default.

Actual execution evidence remains necessary. Contract/result validation checks structure and consistency; it does not independently establish user permission or execute the reported product checks. Performance improvements from instruction changes require task-based evaluation rather than line counts or validator pass counts.
