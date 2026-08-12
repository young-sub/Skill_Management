<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/references/goal-execution-policy.md -->
<!-- Source-SHA256: 1cb056a14b0685c7ac7660a241433e0af07c98fd190733fdb4d81c7a242bb119 -->

# Goal Execution Policy

- An approved canonical Item contract is execution authority; a host Goal is optional and approval, recovery, and distribution hashes remain internal integrity data.
- Capture the current branch and commit and preserve the dirty baseline. Create branches only when repository policy or the human requires them.
- A commit unit is the smallest complete functional unit that works when checked out by itself, including required source, tests, docs, schemas, and generated resources. Commit every such unit after its mapped verification passes. Group coupled Items into one commit; split only independently working units. Never create an intentionally broken intermediate commit.
- Implement dependency-ready core Items before optional work. Use RED/GREEN for behavior changes and Impacted verification for completion.
- Record an unambiguous low-risk user change as `approved_amendment`; request focused approval only for material or high-risk deltas.
- Stop for destructive, security/privacy, secret, irreversible, costly external, publish/push, or genuinely blocked boundaries.
