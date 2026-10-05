# Harness Architecture

## Control plane

`.harness/project.yaml` is JSON-compatible YAML. Its internal schema version is retained for machine compatibility. The file owns mapped roots, command descriptors, source-to-test candidates, Full warning triggers, document boundaries, retention, Git policy, and baseline debt. Unknown normative fields are rejected; provider extensions belong under `extensions`.

Older project files may contain redundant cohort and component-version declarations. The runtime recognizes only the exact known legacy shapes, normalizes them in memory without overwriting the file, and emits a digest-bound transaction for an approved migration. Unknown or mixed declarations fail closed.

## Work contract and authorization

`contract.json` is the canonical, language-independent Item contract. Every Item has stable identity, a concrete changed outcome, ordered behavior steps, observable verification, and stable Done criteria. Contracts contain the Items needed for meaningful review boundaries, with no fixed upper count. `design-create` accepts omitted descriptive `terms`, `depends_on`, and `non_goals` as empty lists and omitted `priority` as `core`; it expands only its input copy before validation. Decision state and material risk declarations remain explicit, including resolved/empty values. Saved contracts and `authorize` remain strict; no existing authorization payload is silently normalized.

Ordinary contracts are default-authorized from their canonical payload. Structured material risks describe actual effects, such as changing access controls or exposing private data, rather than any task mentioning security. User instructions establish permission; the runtime records it and checks consistency. A low-risk amendment changes descriptive title/outcome/steps/terms and preserves valid existing explicit authorization. Structural/material Item revisions use `amend --intent explicit_approve` with matching user permission; the flag records that permission, not a requirement to ask again. Veto and stable Item identity remain protected. Invalid or drifted authorization cannot be reused.

Use `amend --root <repo>` to persist a revision: the runtime checks the saved contract, updates it and the active manifest digest in one recoverable transaction, and preserves the original Git/dirty baseline. Designed but unstarted work retains its design-only state. Without `--root`, `amend` only returns a transformed contract for compatibility. `result.json` owns submitted evidence; validators do not execute or authenticate checks. Reassess evidence affected by the revision while reusing unaffected outcomes. Empty planned tests are allowed when observable Done evidence already establishes the outcome. The final chat response is the human-facing Design or Result summary.

## Runtime and state

Result evaluation rejects non-object `full` and Item `delta` values as incomplete evidence. Close leaves the work active without writing result artifacts when this validation fails.

The runtime selects dependency-ready core Items before optional Items and records only Git-reported staged/unstaged/deleted/non-ignored untracked baseline entries. Impact decisions record changed logic, affected behaviors, scope, and reason. Path rules yield candidates; local/capability scope selects exact tests, cross-cutting scope or an explicit request requires Full, and unknown scope blocks as `unresolved_logic_impact`. Close recomputes cumulative paths from the captured source commit. Independent Item worktrees use deterministic paths under the repository-owned, ignored `/.worktree/` directory; callers cannot place them outside the project. A commit contains the smallest complete functional unit that works from that commit alone; coupled Items sharing runtime, schema, documentation, or generated resources stay together. Planned test and Done IDs must match retained evidence one-to-one. A host Goal may track continuation but is not execution authority. Low-risk user changes become `approved_amendment`; material or high-risk deltas need focused approval. Legacy active work that already contains `review/design.html` remains valid only when the retained bytes match its stored digest; the runtime neither converts nor deletes it.

```text
.work/goals/active/<id>
  -> completed/YYYY-MM/<id>
  -> trash/YYYY-MM-DD/<id>
  -> deleted (exact-target approval only)
```

Manifest dates, not filesystem timestamps, drive retention. Transaction journals make broad setup and migration changes recoverable. `legacy-unclassified` is outside automatic retention.

## Environment exceptions

Configured `extensions.workflow` connects the existing project Feature Map, source patterns, criteria and command IDs to [project obligations](../../authoring/references/workflow-obligations.md). Normal Harness start captures its baseline in `work.json` and returns a compact reference; `project_workflow.py --work-id` reads that baseline and retains reviews in `workflow.json`. Resume preserves the baseline. Source/criteria/command changes reopen consumers; missing links and evidence remain PARTIAL. Current configured semantic reviews can be reused without repeating the whole survey. Harness maintain audits configured obligations and close directly checks its per-work state before lifecycle completion, even without an optional workflow begin. Older work retains configured-state checks. This remains editable local consistency: `READY_FOR_REVIEW` is not protected acceptance, and the explicit accept operation reports BLOCKED without a host-owned verifier boundary.

The cohort installer preserves replaced trees at its returned `preserved_previous` path, including user customizations. An already matching installation returns `reused: true` without rewriting it. Failed restoration retains both staging and backup recovery paths instead of deleting remaining previous bytes. This is recoverability for observed exceptions; process-crash recovery and hostile-process isolation require separate host evidence.

`.harness/environment-exceptions.json` is an ignored, repository-local machine exception document. If absent, the runtime does nothing. If present, schema version 1 requires each unique entry to contain non-empty `capability`, `status`, `reason`, `fallback`, `disable`, and `retry`; supported failure statuses are `verification_unavailable` and `execution_blocked`. A `skip_until_manual_reenable` entry prevents another invocation and selects the fallback. The resulting evidence carries the unavailable capability name, intent, reason, fallback, disable method, and remaining unverified scope for `result.json` and final chat. Environment failures never become approval blocks.

## Distribution

`agent-workflow` selects task procedures; `setup-project-verification` connects the first product flow; `maintain-project-verification` repairs product-map, command and UI drift. Their shared references are generated from one canonical source into each self-contained Skill. Existing Harness runtime retains mapping/cohort/retention ownership, while projects own requirements, runner adapters and UI implementation. Combining these capabilities does not turn a Harness integrity PASS into a product PASS or require a contract for ordinary development.

The existing Impeccable entrypoint also loads the canonical repair/reuse reference when the request includes shared UI standards or subsequent-screen reuse. This bounded reverse route matters when a natural UI request selects the UI capability first: the shared implementation, existing guide and active Feature command must travel together. Ordinary visual refinement does not trigger project setup or unrelated maintenance.

`authoring/` is canonical. `scripts/sync-skill-resources.ps1` generates self-contained public resources and the manifest. Each installed Skill exposes only its owned commands. When a known command is invoked through the wrong Skill, that entrypoint reports the requested command, owning sibling Skill, and exact sibling script path; there is no shared launcher. The installed cohort is accepted only when its complete observed tree exactly matches the required manifest resource set and hashes; Skill prose is not a compatibility signal. The bundled manifest must retain valid metadata and the same Harness resource entries, but unrelated Skill additions, removals, or hash changes do not invalidate the cohort. Full distribution validation still covers all public resources. Installation stages and verifies the whole cohort before atomically replacing its owned Skill roots.
