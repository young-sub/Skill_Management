<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/playbooks/feature.md -->
<!-- Source-SHA256: 5e74eaf4208fd242dede73d6d37103945cb983d155a6356523add678016287ce -->

# Feature

Use when the request adds or changes observable behavior. A tiny descriptive edit
stays direct; this is a decision aid, not a required plan, task or contract.

1. Derive completion and meaningful failure criteria from the request and existing
   requirements before editing; write them as checks whose expected values come
   from the requirement, not from running the new code. Confirm they fail on the
   current code for the intended reason. Find the current owner and affected callers.
2. Implement the smallest complete change, including affected inputs, outputs,
   tests, config and docs. Use existing tools and validation at trust boundaries.
   When enforcing a rule on stored data, find every writer: run `LSP findReferences`
   on the writing function (text search if no `LSP` tool), and text-search table/column writes too
   (SQL INSERT/UPDATE, ORM calls, import/restore jobs). Cover each writer with a check.
3. When a new test's ability to catch the defect is in doubt, optionally use
   `probe_check.py prove --skip-current`. After the final edit, run them once with
   the existing checks that exercise the changed modules. For changed
   layer connections follow input through API, Domain, storage and fresh read;
   rejected writes must preserve data.

Completion evidence is actual normal/failure observations tied to the changed
behavior, not a successful command or PASS label alone. Select impact and assess
evidence currentness using [project verification](../references/project-verification.md).
If blocked, separate implementation from unavailable observations, name the cause
and next action, and continue independent authorized work. Do not build a runner
or force full-project setup to fill an unrelated gap.
