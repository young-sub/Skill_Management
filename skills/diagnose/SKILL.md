---
name: diagnose
description: Diagnose an implementation or verification failure with a bounded root-cause loop and durable evidence.
---

# Diagnose

Use this bounded loop for a failure in the current approved work:

1. Reproduce the exact observable failure.
2. Minimize it to the smallest reliable case.
3. Hypothesize a falsifiable cause.
4. Instrument only the boundary needed to test that hypothesis.
5. Identify the Root cause from evidence.
6. Fix the root cause with the smallest contract-aligned change.
7. Add a Regression test that fails before the fix and passes after it.
8. Reverify the targeted check, then the approved broader checks.

Read only project `TESTING.md`, `.harness/project.yaml`, and relevant durable project documents. Do not expand into unrelated live systems or add Live/Eval coverage outside the approved Test Envelope. Record the minimized reproduction, hypotheses, observations, root cause, fix, regression, and Reverify results in the current work's `RESULT.md` or the adjacent structured evidence record.
