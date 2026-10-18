---
name: diagnose
description: Investigate implementation or verification failures and human direction corrections, distinguish root causes from environment limits or intentional exceptions, and fix the responsible owner when authorized. A Harness contract is optional.
---

# Diagnose

Use existing repository checks and diagnostics. Consult [execution policy](references/goal-execution-policy.md) when the failure belongs to an active Harness contract.

For a human correction, use [feedback and success reuse](references/feedback-and-success.md) to separate expected behavior, missing guidance and missed discovery from a one-off exception. Then use [repair and reuse](references/repair-and-reuse.md) for the existing feedback/prevention evidence contract. Repair the first clear correction at its cause owner; prefer structure, type/constraint, an appropriate regression, then minimal documentation. Observe the original failure, alternate bypass and nearby normal use before claiming prevention, and consume it in a related follow-up. Do not duplicate an existing rule that was simply not discovered.

A read-only investigation does not require project workflow setup. When useful,
use the available agent-workflow task's diagnostic record to retain the request,
allowed/forbidden actions, source identity, entrypoint/state IDs, observations and
unknowns. Update existing work instead of creating another ledger. Lookup and
task resume read retained evidence; fresh investigation/execution is a separate
action. Distinguish observation from hypothesis and product/plugin/tool/environment
or Agent judgment ownership. Full surveys retain their denominator; a small
request stays with affected owners and consumers.

Classify feedback before repair: existing requirement violation, authorized
requirement change, intentional variant/exception, independently justified
oracle/tool error, environment limit or unknown cause. User agreement does not
prove a cause or authorize more changes. Keep deferred reviews and unknown causes
open; retain candidate IDs and evidence. Reuse the available feedback record's
reason-specific completion and subsequent-consumption checks.

Environment failures also need repair evidence: distinguish required target from
host/backend/container identity, preserve the failed command and cleanup output,
bind attempts to project-owned capability actions, then recheck the same target.
Use the existing environment feedback contract to retain failure history and
current availability. Lookup never diagnoses, repairs or clears a manual disable.

1. Reproduce the reported input/entry point and failing output with the smallest relevant check. Confirm the current checkout, runtime, and endpoint when using existing logs or a running server.
2. Trace the failing behavior through its callers and state owner. Form a falsifiable hypothesis; instrument only what distinguishes likely causes. Separate code failure, missing evidence, and environment failure.
3. If a retry produces the same evidence, change the hypothesis or check instead of repeating it. Honor loaded manual-disable records. Escalate scope only when the observed cause crosses the current boundary.
4. For an authorized fix, add the smallest regression proof when it prevents recurrence, observe RED when that evidence is useful, fix the shared root cause, and observe GREEN. Reuse existing evidence when it already proves the behavior; do not add a test solely to document a one-off diagnosis. A diagnosis-only request ends with evidence and the proposed fix. No contract creation is required for a small repair.
5. Recheck affected public behavior and relevant sibling callers. Expand verification only for newly affected logic or an explicit request; unrelated baseline debt is not a completion gate.

For active contract work, append only new failure/cause/fix/check evidence to `.work/goals/active/<work-id>/agent/evidence.jsonl`; otherwise a concise task record or chat is enough. Reuse permission for covered live checks; obtain missing authorization only for real external effects, cost, or sensitive changes. Report unresolved causes without inventing certainty.
