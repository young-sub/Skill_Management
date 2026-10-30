---
name: diagnose
description: Investigate reported incorrect behavior (user or customer complaints, bugs, something that disappeared or looks wrong), implementation or verification failures and human direction corrections; distinguish root causes from environment limits or intentional exceptions, fix the responsible owner when authorized and block the original and alternate paths. A Harness contract is optional.
disable-model-invocation: true
---
<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/skills/diagnose/SKILL.md -->
<!-- Source-SHA256: a0ccacf557794323b3009b9a2df0425913eca2a2c1ca4b6bfc6a5c9d98a0abce -->


# Diagnose

Use existing repository checks and diagnostics. A read-only investigation needs no
project workflow setup, and a small repair no contract. For a failure inside an active Harness
contract, consult [execution policy](references/goal-execution-policy.md).

**Classify before repairing.** For a human correction, use
[feedback and success reuse](references/feedback-and-success.md) to separate expected
behavior, missing guidance and missed discovery from a one-off exception, and
[repair and reuse](references/repair-and-reuse.md) for the prevention evidence
contract. Repair the first clear correction at its cause owner, preferring structure,
type/constraint, an appropriate regression, then minimal documentation. Observe the
original failure, alternate bypass and nearby normal use before claiming prevention,
and consume it in a related follow-up. The cause is
one of: existing requirement violation, authorized requirement change, intentional
variant/exception, independently justified oracle/tool error, environment limit or
unknown. User agreement does not prove a cause or authorize more changes. Keep unknown
causes and deferred reviews open with their candidate IDs and evidence; do not
duplicate a rule that exists but was not discovered. Reuse the feedback record's
reason-specific completion and follow-up consumption checks.

**Records.** When useful, keep the request, allowed/forbidden actions, source identity,
entry/state IDs, observations and unknowns in the existing agent-workflow task's
diagnostic record. Lookup and task resume read retained evidence; fresh investigation
is a separate action. Name the owner: product, plugin, tool, environment or Agent
judgment. A full survey keeps its denominator; a small request stays with affected
owners and consumers.

**Environment failures** follow the `environment_limit` row of
[repair and reuse](references/repair-and-reuse.md#classify-the-feedback-before-choosing-a-repair):
keep the failed command, attempts and cleanup output and recheck the same target.
Lookup never diagnoses, repairs or clears a manual disable.

1. Reproduce the reported input/entry point and failing output with the smallest
   relevant check. Confirm the checkout, runtime and endpoint when using existing logs
   or a running server.
2. Trace the failing behavior through its callers and state owner. Form a falsifiable
   hypothesis and instrument only what distinguishes likely causes. Separate code
   failure, missing evidence and environment failure, and observation from hypothesis.
3. If a retry gives the same evidence, change the hypothesis or the check. After two
   failed fixes on one premise, write the premise down and test it. Revert edits for a
   refuted hypothesis; a guard is a fix only when that state can legitimately occur.
   Honor loaded manual-disable records. Widen scope only when the observed cause crosses the current boundary.
4. For an authorized fix, add the smallest regression proof when it prevents
   recurrence, observe RED when that evidence is useful, fix the shared root cause and
   observe GREEN. Reuse existing evidence that already proves the behavior; do not add a
   test solely to document a one-off diagnosis. A diagnosis-only request ends with
   evidence and the proposed fix.
5. Find every path to the same failure: `LSP findReferences` on the faulty function
   (text search if no `LSP` tool), plus text-search table/column writes (SQL INSERT/UPDATE,
   ORM calls, import/restore jobs). Cover each with the regression.
   Register the original fault as a probe in `.harness/probes.json` and run
   `python <this Skill's directory>/scripts/probe_check.py probes --root <project>`;
   every probe must be killed. Optionally use `probe_check.py prove --skip-current`
   when a new test's ability to catch the defect is in doubt.
6. In a connected project, record complaint, cause, repair, guardrail and bypass
   evidence in the existing feedback record so the next task inherits it; update
   existing work instead of creating another ledger. Unconnected: say no feedback
   record can be kept and offer `setup-project-verification` once.
7. Recheck affected public behavior and relevant sibling callers. Expand verification
   only for newly affected logic or an explicit request; unrelated baseline debt is not
   a completion gate.
8. After an authorized fix, run the [independent check](references/independent-check.md):
   a fresh verifier with only the complaint verbatim and the diff writes failing tests
   for paths you did not cover. Fix what they show and register each fixed violation as
   a probe beside the step-5 probes; a stricter reading than the complaint is the user's
   decision, recorded in `.harness/decisions.md` once answered.

Active contract work appends only new failure/cause/fix/check evidence to
`.work/goals/active/<work-id>/agent/evidence.jsonl`; otherwise a concise task record or
chat is enough. Reuse permission for covered live checks; ask only for real external
effects, cost or sensitive changes. Report unresolved causes without inventing certainty.
