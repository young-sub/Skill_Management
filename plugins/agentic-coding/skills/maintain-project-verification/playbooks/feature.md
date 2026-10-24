<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/playbooks/feature.md -->
<!-- Source-SHA256: 9823602f79c70e134aa3954b13f4d5ab35d232694f47079cfc071f42052714ef -->

# Feature

Use when the request adds or changes observable behavior. A tiny descriptive edit
stays direct; this is a decision aid, not a required plan, task or contract.

1. Derive completion and meaningful failure criteria from the request and existing
   requirements before editing; write them as checks whose expected values come
   from the requirement, not from running the new code. Confirm they fail on the
   current code for the intended reason. Find the current owner and affected callers.
2. Implement the smallest complete change, including affected inputs, outputs,
   tests, config and docs. Use existing tools and validation at trust boundaries.
   Every entry point that creates or changes the same data obeys the same rule.
3. If the new checks were not seen failing before the change, prove they fail without
   it (`probe_check.py prove --skip-current`). After the final edit, run them once with
   the existing checks that exercise the changed modules. For changed
   layer connections follow input through API, Domain, storage and fresh read;
   rejected writes must preserve data.

Completion evidence is actual normal/failure observations tied to the changed
behavior, not a successful command or PASS label alone. Select impact and assess
evidence currentness using [project verification](../references/project-verification.md).
If blocked, separate implementation from unavailable observations, name the cause
and next action, and continue independent authorized work. Do not build a runner
or force full-project setup to fill an unrelated gap.
