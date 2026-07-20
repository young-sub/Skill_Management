---
name: design-goal
description: Build an approvable implementation contract from repository evidence and human decisions, including vertical-slice plans, a dependency DAG, and static Design Review. Use when implementation scope is understood and must be converted into SPEC.md, GOAL.md, and independently verifiable plans.
---

# Design Goal

## Preconditions

- Investigate code, public interfaces, schemas, tests, ADRs, domain language, runtime, security, and operations before asking questions answerable from the repository.
- Ask one grouped decision question only for unresolved product, state, interface, failure, security, verification, completion, or architecture choices.
- Never implement the proposed behavior during this workflow.

## Contract workflow

1. Choose a unique Work ID under the configured work root.
2. For a small change, instantiate `templates/work/SPEC.md`. For medium work, instantiate `GOAL.md` and one or more `templates/work/PLAN.md` files under `plans/`.
3. Keep every Plan a vertical, independently verifiable slice. Record dependencies as a JSON-array literal in `depends_on`.
4. Run `python scripts/contract_engine.py validate --root <contract-root> --work-root <work-root>`.
5. Render `design-review.html` with `python scripts/render_design_review.py --root <contract-root> --output <contract-root>/design-review.html` and present the human-readable contract for approval.
6. After an explicit human approval response, run `python scripts/contract_engine.py approve --root <contract-root> --work-root <work-root> --approved-at <ISO-8601> --approved-by human`. Approval rechecks Work ID uniqueness in that work root; never reuse an earlier validation result.
7. Re-run validation with `--require-approved`. Any contract hash drift requires new approval.

The parser supports only the generated limited frontmatter and required `##` sections. Approval metadata, Plan runtime status, Results, Blocked reports, and Evidence section content are excluded from the canonical hash. Contract decisions, approval requirements, Plan identity, and dependencies are included.

## Final output and stop

Return this Goal declaration payload with the actual values:

```text
Use $execute-codex-goal.

Work ID: <WORK_ID>
Contract: <GOAL.md path>
Approved contract hash: sha256:<canonical-contract-hash>
Execute every approved slice in dependency order.
Stop only for the contract's Hard Stop conditions.
```

Do not invoke `execute-codex-goal`, create a Codex Goal, or begin implementation. Provide the Goal declaration payload and stop.
