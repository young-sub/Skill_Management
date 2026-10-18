<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/playbooks/feature.md -->
<!-- Source-SHA256: 90feb13a1eefb3e8463a56cdfe0a95aec5761f1fec493ff43fd4bda86e92c85d -->

# Feature

Use when the request adds or changes observable behavior. A tiny descriptive edit
stays direct; this is a decision aid, not a required plan, task or contract.

1. Derive completion and meaningful failure criteria from the request and existing
   requirements before editing. Find the current owner and affected callers.
2. Implement the smallest complete change, including affected inputs, outputs,
   tests, config and docs. Use existing tools and validation at trust boundaries.
3. Observe the requested result and relevant rejection/state effects with existing
   checks. For changed layer connections follow input through API, Domain, storage
   and fresh read; rejected writes must preserve data.

Completion evidence is actual normal/failure observations tied to the changed
behavior, not a successful command or PASS label alone. Select impact and assess
evidence currentness using [project verification](../references/project-verification.md).
If blocked, separate implementation from unavailable observations, name the cause
and next action, and continue independent authorized work. Do not build a runner
or force full-project setup to fill an unrelated gap.
