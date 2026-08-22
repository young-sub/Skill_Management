# Agent Workflow

Start from repository evidence and `.harness/project.yaml`. Capture the current branch and commit, preserve dirty files, and create the configured feature branch without assuming a default. Shared instructions, schemas, source-of-truth documents, generated resources, and common test interfaces remain sequential in the main session.

Use the Goal contract lifecycle only when the global Work Packet threshold is met or the user explicitly selects it. Within that workflow, capability work uses one to five canonical Items; use one when the change has only one meaningful review boundary. A valid ordinary contract is authorized by default; the user can veto it without performing approval ceremony. Host Goal tracking is optional. Implement dependency-ready core Items first, record logic impact from diff/direct callers/public behavior, and run exact checks; path mappings are candidates only.

A commit unit is the smallest complete functional unit that works when checked out by itself, including required source, tests, docs, schemas, and generated resources. Commit every such unit after its mapped verification passes. Group coupled Items into one commit; split only independently working units. Never create an intentionally broken intermediate commit.

Low-risk user deltas become `approved_amendment` and continue immediately. Request focused approval for material public contract, acceptance, multi-boundary architecture, destructive, security/privacy, secret, irreversible, costly external, push, or publish changes.

Close re-evaluates the cumulative Git change set, evaluates Items independently, updates only mapped durable truth, writes `result.json`, summarizes the outcome in final chat, and moves work to typed retained state. Re-resolve captured base movement and protection before integration. `main` is protected in this repository; leave a verified branch for human integration and never auto-push.
