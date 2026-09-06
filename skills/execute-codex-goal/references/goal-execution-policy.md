<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/references/goal-execution-policy.md -->
<!-- Source-SHA256: a4bb27abeb258019990ac4ed87d1845dcacd2840ee28f4013c2eb8738590432e -->

# Goal Execution Policy

- A canonical Item contract records authorized scope; actual user instructions establish permission. A host Goal is optional tracking. Approval, recovery, and distribution hashes are internal integrity data, not human approval evidence.
- Capture the current branch and commit and preserve the dirty baseline. Create branches only when repository policy or the human requires them.
- A commit unit is the smallest complete functional unit that works when checked out by itself, including required source, tests, docs, schemas, and generated resources. Commit every such unit after its mapped verification passes. Group coupled Items into one commit; split only independently working units. Never create an intentionally broken intermediate commit.
- Implement dependency-ready core Items before optional work. Use focused RED/GREEN for non-trivial behavior changes where feasible, explain concrete exceptions, and verify affected observable behavior.
- Record an unambiguous low-risk user delta as `approved_amendment`. This shortcut updates descriptive `title`, `what`, `steps`, or `terms`; it cannot clear a veto or change identity, decisions, acceptance tests/Done criteria, dependencies, non-goals, risk declarations, or priority. Structural/material revisions use the revised canonical contract and explicit authorization; reuse user permission already covering that exact revision instead of asking again. A mechanical structural edit within authorized scope does not itself require another human confirmation. A veto needs an explicit user reversal.
- Continue covered work through high-risk steps only with matching authorization. Ask about uncovered scope or risk after preparing a reviewable action. An environment failure is `verification_unavailable` or `execution_blocked`, not an approval block.
- Capture real command outcomes and relevant runtime evidence. Contract/result validators establish record consistency; they do not execute reported checks or attest to product correctness.
