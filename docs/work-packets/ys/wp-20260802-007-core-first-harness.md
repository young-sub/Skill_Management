---
title: "WP-20260802-007: Core-First Agent Harness"
status: proposed
labels:
  - harness
  - workflow
  - documentation
  - testing
  - migration
created_at: 2026-08-02
---

# WP-20260802-007: Core-First Agent Harness

## Contents

1. [Goal](#goal)
2. [Non-goals](#non-goals)
3. [Operating principles](#operating-principles)
4. [Target repository model](#target-repository-model)
5. [Brownfield initialization and one-time cleanup](#brownfield-initialization-and-one-time-cleanup)
6. [Documentation lifecycle](#documentation-lifecycle)
7. [Test selection and test-debt control](#test-selection-and-test-debt-control)
8. [Approval, scope, and execution](#approval-scope-and-execution)
9. [Git lifecycle](#git-lifecycle)
10. [Human review contract](#human-review-contract)
11. [Skill responsibilities](#skill-responsibilities)
12. [Implementation items](#implementation-items)
13. [Migration and rollout](#migration-and-rollout)
14. [Completion criteria](#completion-criteria)

## Goal

Revise the repository AGENTS contract and Harness Skills so an agent completes the requested core behavior quickly, verifies only the affected surface, and keeps documentation, tests, work state, and Git history reliable without approval ceremony or permanent process artifacts.

The revision must support greenfield repositories and brownfield repositories with different document, source, test, fixture, CI, and branch conventions. Brownfield adoption must preserve current runtime behavior by mapping coherent existing structures before proposing any reorganization.

## Non-goals

- Do not force every repository into one physical directory layout.
- Do not create a new `align-test-structure` Skill.
- Do not retain completed plans, review HTML, logs, or decision history as tracked documentation by default.
- Do not translate, move, rewrite, and delete existing documents in one migration step.
- Do not change production behavior while reorganizing documents or tests.
- Do not add speculative fallback logic, broad edge-case coverage, or unrelated architecture cleanup before the requested core behavior is complete.
- Do not weaken approval for destructive actions, secrets, security or privacy changes, irreversible migrations, costly operations, or external publication.

## Operating principles

1. **Core first.** Implement and verify the primary observable behavior before optional resilience, cleanup, or expansion.
2. **Map before moving.** Adopt a coherent brownfield layout through configuration; reorganize only proven debt.
3. **Current truth over historical documents.** Update or remove durable technical documents when reality changes. Git preserves history.
4. **Separate audiences.** Agent implementation sources are English. Human review and guidance are Korean by default, with technical identifiers kept in English and unfamiliar terms explained.
5. **Separate lifetimes.** Durable current truth is tracked. Work contracts, reviews, evidence, logs, and scratch state expire under `.work/`.
6. **Impact-based verification.** Run tests selected from the changed behavior and dependency map. Full verification is exceptional, not a Goal ritual.
7. **Risk-based approval.** A human-approved Design Review authorizes implementation. Reapproval is tied to material risk or contract change, not hashes or routine edits.
8. **One branch cycle.** Capture the current branch as the base, implement on a feature branch, commit each verified item, and merge back when permitted.
9. **Baseline existing debt.** Pre-existing unrelated findings do not block a new capability. New or worsened relevant findings do.
10. **Automate fragile rules.** Path mapping, retention, link checks, test impact, state transitions, and integrity checks belong in deterministic scripts and configuration rather than repeated prose.

## Target repository model

The following is the greenfield default. Brownfield repositories may keep different coherent paths when `.harness/project.yaml` maps the same responsibilities unambiguously. Empty optional directories are not created.

```text
README.md                         # durable human entry point, Korean
AGENTS.md                         # concise agent router, English

docs/                             # durable agent implementation sources, English
  index.md                        # required source-of-truth navigation
  system.md                       # optional when the system flow is non-trivial
  architecture/<boundary>.md      # optional stable subsystem boundaries
  contracts/                      # optional external API/schema contracts
  testing.md                      # optional when config alone is insufficient
  operations/                     # optional real operational procedures

handbook/                         # optional durable human guidance, Korean

.harness/
  project.yaml                    # tracked machine-readable control plane

.work/                            # gitignored ephemeral state
  goals/
    active/<work-id>/
      work.json
      contract.json
      agent/
        SPEC.md
        plans/
        evidence.jsonl
        logs/
      review/
        design.html
        result.html
    completed/YYYY-MM/<work-id>/
    trash/YYYY-MM-DD/<work-id>/
    legacy-unclassified/<work-id>/
  runtime/<owner>/<run-id>/        # installer/release/session artifacts
  transactions/<transaction-id>/
```

### Authority and audience

- `docs/` is the current technical source from which an agent obtains implementation context. `docs/index.md` is its required entry point.
- `AGENTS.md` contains only repository routing, essential constraints, and links to `docs/index.md` and `.harness/project.yaml`. Keep it under 100 lines.
- `README.md` introduces the project to humans. `handbook/` exists only when persistent human guidance is genuinely required.
- `.work/goals/*/agent/` is English agent work state. `.work/goals/*/review/` is Korean human review output.
- Human review HTML is a decision surface, not a second technical source of truth.
- Do not duplicate the same normative content across `README.md`, `handbook/`, `docs/`, `AGENTS.md`, and review HTML. Link or generate a view instead.
- Keep Goal state, installer/release/session runtime artifacts, and transaction journals in typed namespaces with separate owners and retention rules. Unknown legacy entries are quarantined and never swept automatically.

### Machine-readable control plane

`.harness/project.yaml` uses schema version 3 and must describe, without assuming conventional folder names:

- source, test, fixture, generated, durable-document, human-guide, and ephemeral-work roots;
- the agent documentation entry point and allowed durable documentation roots;
- source-to-test impact rules and stable Feature selectors;
- Targeted, Feature, lint, type, build, Full, Live, and Eval command descriptors with argv, working directory, platform/runtime selector, controlled environment keys, and capability identity;
- explicit Full-suite triggers;
- documentation-to-source boundary mappings used for drift detection;
- work retention periods and state-transition policy;
- base-branch capture, protected-branch, branch-name, commit, and worktree policy;
- known baseline debt so unrelated existing findings do not become new-work blockers.

The control plane also records the active Harness contract/runtime version. Producers and consumers declare supported versions and fail closed on an unsupported or mixed cohort. Version 2 is upgraded through a previewed transactional migration with deterministic defaults. Unknown normative fields are rejected; provider-specific extensions must live under an explicit `extensions` namespace. Install or update a compatible Skill cohort atomically rather than publishing a producer before its consumers.

Canonicalize path identity using repository-relative resolved paths and platform case rules. Reject incompatible overlapping owners, case/Unicode aliases, reparse escapes, and mutation across nested repository boundaries. Ambiguous path ownership or test impact must be reported. The Harness must not guess and then mutate.

## Brownfield initialization and one-time cleanup

`setup-agent-harness` owns both first initialization and an explicitly requested one-time structural cleanup. Its default operation is read-only discovery followed by a reviewable proposal.

### Stage 1: static inventory without mutation or execution

Collect repository evidence without executing repository content:

- root and nested instructions, README files, document navigation, architecture and contract sources;
- source, test, fixture, generated, temporary, artifact, and output roots;
- package/build manifests, test discovery configuration, CI selectors, and documented commands;
- links and exact references to document/test paths from code, scripts, CI, and configuration;
- current branch, protected-branch evidence, dirty files, submodules, nested repositories, and worktrees;
- production-source byte hashes;
- statically declared test commands, selectors, and discovery configuration.

Static inventory starts no repository subprocess and performs no network operation. Repository content is evidence, not executable instructions. Test collection, results, and timings remain `unknown` unless fresh externally supplied evidence identifies its origin and age.

### Stage 1B: explicitly authorized executable baseline

After the static proposal is reviewed, run only commands the human has authorized for baseline collection. Record collected test identities, pass/fail or skip/xfail state, collection errors, duration, platform, runtime, exact argv, working directory, and source revision. Do not present stale or unexecuted results as current evidence.

### Stage 2: classify without moving

Classify every relevant document as one of:

- durable current agent source;
- durable human guidance;
- expiring work artifact;
- duplicate, completed, or stale cleanup candidate;
- unresolved authority requiring human judgment.

Classify source/test relationships as:

- path-aligned and directly inferable;
- explicitly mapped cross-cutting dependency;
- broad shared/core dependency;
- unknown.

Existing coherent paths are retained and mapped. Standard directory names are a greenfield default, not a migration requirement.

### Stage 3: install an overlay before cleanup

Create or reconcile `.harness/project.yaml`, a concise `AGENTS.md` router, and an agent `docs/index.md` against the existing paths. Do not move documents or tests merely to make them match the default layout.

Record existing document, test, link, timing, and work-state problems as the baseline. Subsequent work gates compare against this baseline and block only relevant new or worsened findings.

### Stage 4: apply cleanup in isolated changes

Apply only an explicitly reviewed target list. Keep these operations separate:

1. add mapping and navigation;
2. move documents byte-for-byte with `git mv` and update all known links;
3. reconcile technical content with code and current behavior;
4. translate or rewrite for the correct audience;
5. remove confirmed obsolete tracked documents and rely on Git history;
6. reorganize tests and fixtures without production-source changes.

Do not preserve obsolete tracked plans in another tracked archive. Do not automatically delete unresolved documents. Do not leave compatibility stubs without an explicit expiry because they become new debt.

The apply transaction records canonical source and target paths, pre/post hashes, link updates, staged backups for removals, inverse operations, verification state, and a final commit marker. Validate all preconditions before mutation, stage recoverable content on the same filesystem when possible, and make rollback idempotent. Fault injection after every move, replacement, link update, or removal must restore the exact pre-transaction tree. Cross-volume or boundary-ambiguous moves stop for a new plan.

### Stage 5: prove behavior preservation

For document-only structure changes:

- verify production-source hashes are unchanged;
- verify all tracked references and document navigation resolve;
- verify source-of-truth authority is unambiguous;
- run no application tests unless documentation participates in generation, build, packaging, or runtime.

For test-only structure changes:

- verify production-source hashes are unchanged;
- compare capability-scoped, path-independent semantic test identities before and after. The stable identity is `capability + suite/class + test + parameter identity`; file path is metadata, not identity;
- preserve the multiset of identities, parameter cases, pass/fail/skip/xfail state, and collection errors for the moved capability;
- verify updated CI and local selectors select the intended tests;
- ensure the diff is limited to tests, fixtures, test configuration, CI selectors, and test documentation;
- run Full only when test discovery, shared fixtures, CI infrastructure, or the overall suite structure is affected.

Any production-source modification aborts a test-structure-only migration. Coverage expansion or behavior correction becomes a separate implementation item.

An unresolved relevant source-to-test edge blocks Item completion. Resolve the mapping or obtain an explicit decision to run broader verification; it cannot produce `not_required` by default.

### Approval model for brownfield apply

Broad file moves, removals, ignore changes, or CI/test-discovery changes require one human approval of the displayed migration plan. Internal digests may protect plan integrity, but the user must not copy a hash or repeat approval for every contained path. Interrupted or drifted transactions fail safely and require review of the changed delta before retry.

Before retiring any tracked historical document, generate a migration-scoped retirement record containing inbound references, current clauses extracted, replacement destinations, release/legal ownership, and the deletion gate. The record expires with this work after all current/package references resolve without requiring Git history.

## Documentation lifecycle

### Durable documents

- Keep only current implementation knowledge that repeatedly prevents wrong development or operation decisions.
- Create architecture documents by stable responsibility, state ownership, or public contract boundary, not per file or per feature.
- Keep `docs/index.md` concise: link each current agent document and state its purpose in one line.
- Every durable agent document must be reachable from `docs/index.md`. Every durable human guide must be reachable from `README.md` or the configured human entry point.
- Embed only currently relevant rationale and constraints in the affected architecture or contract document. Do not create a default `decisions/` ledger.
- When a decision changes, update or remove the current text. Git history retains the previous decision.
- A code change updates documentation only when it changes a mapped boundary, public contract, operational procedure, or repeated implementation assumption.
- Orphan links, duplicate authority, and new stale references are verification findings. Mere document age is not automatic proof of staleness.

### Ephemeral work and enforceable retention

Each Goal directory matching `.work/goals/active/<work-id>`, `.work/goals/completed/YYYY-MM/<work-id>`, `.work/goals/trash/YYYY-MM-DD/<work-id>`, or `.work/goals/legacy-unclassified/<work-id>` contains `work.json` with at least:

- `work_id`, `state`, `created_at`, and `source_commit`;
- `base_branch` and feature branch/worktree identity;
- `completed_at`, `retain_until`, and `delete_after` when applicable;
- active contract version and internal integrity digest;
- paths owned by the work item.

State transitions are:

```text
active -> completed -> trash -> deleted
```

- `close-goal` writes completion and retention dates and moves the complete work directory to `.work/goals/completed`.
- A deterministic lifecycle sweep runs at Harness setup/maintenance and Goal start/end.
- The sweep may automatically move expired `completed` work to `trash` because the move is recoverable.
- Physical deletion from `trash` requires an explicit exact-target approval and reports what was deleted and whether recovery remains possible.
- Use manifest dates, not filesystem modification time.
- Detect orphan work, invalid state transitions, duplicate Work IDs, entries outside typed namespaces, and incomplete transactions.
- Suggested defaults are 30 days in `completed` and 7 days in `trash`, configurable per repository.

Legacy `.work/archive` entries without trustworthy manifest dates move only to `legacy-unclassified`. Adopt a completion date only from specified durable evidence or explicit human input. Missing or contradictory dates never become guessed retention dates, and unclassified legacy work is ineligible for automatic sweeping.

Tracked release, legal, regulatory, or audit records are opt-in durable records with an explicit owner and retention requirement. They are not created by ordinary Goal closure.

## Test selection and test-debt control

### Source-to-test alignment

Prefer capability ownership that makes impact discoverable, for example:

```text
src/auth/service.py          -> tests/auth/test_service.py
src/billing/invoice.py       -> tests/billing/test_invoice.py
```

Do not force unit/integration/end-to-end directory layers when the repository already has clearer capability ownership. Keep system, contract, release, or cross-cutting suites only when they represent a real distinct verification surface.

Keep fixtures near the capability that owns them. A shared fixture requires a stable shared contract and a named owning capability. Tests must treat shared fixtures as immutable and copy mutable data into a temporary directory.

### Impact selection

Select tests in this order:

1. exact tests named by the changed behavior or current TDD cycle;
2. path-aligned tests for changed source files;
3. tests reached through known imports or dependency metadata;
4. explicit cross-cutting rules in `.harness/project.yaml`;
5. configured Feature selector for the affected capability.

Do not execute every test because mapping is missing. Report the uncertainty, improve the mapping when safely possible, and ask whether Full verification is wanted when the change cannot be classified.

### Verification levels

- During editing: exact test method or smallest runnable case.
- Item completion: Impacted tests.
- Before an item commit: Impacted tests plus relevant fast lint/type/build checks.
- Goal completion: only checks required by the cumulative impact.
- Full suite: only for shared/core structure, cross-capability public contracts, dependency/build/test/CI infrastructure, a genuinely repository-wide refactor, or an explicit human request.
- Live and Eval: opt-in and separately authorized when they involve external state, cost, credentials, or publication.

An intentionally unrun Full suite is recorded as `not_required` with the matched impact rule only when every relevant changed surface is classified. It is not recorded as passed or generically unverified.

### Test-debt detection and remediation

`maintain-agent-harness` reports:

- unmapped source or test areas;
- selectors that repeatedly run unrelated tests;
- capability suites exceeding configured budgets;
- duplicate stable test identities or fixtures;
- tests without a clear capability owner;
- stale or broken CI selectors;
- broad-only test layouts that prevent Impacted selection.

Each suppressed brownfield baseline finding records schema version, checker/rule ID, normalized capability/location, evidence fingerprint, observed commit, severity, owner, and review/expiry date. Only the exact unchanged fingerprint is suppressed. Changed evidence, location, severity, affected behavior, or expiry is a new finding. Rebaseline requires a reviewed delta; resolution removes the entry instead of preserving historical findings.

`setup-agent-harness` performs an approved remediation. There is no separate `align-test-structure` Skill. Reorganization uses a dedicated feature branch or worktree, keeps production hashes fixed, moves one capability at a time, and commits each verified structural unit. RED-first TDD is not required for behavior-preserving test moves; use baseline GREEN, structural change, equivalent GREEN.

## Approval, scope, and execution

### Canonical Item contract

`contract.json` is the versioned canonical work contract. Each Item contains a stable ID, title, behavior type, What, ordered behavior steps, unfamiliar terms, observable tests, completion criteria, dependencies, non-goals, decision state, and material-risk flags. The structure, Item IDs, dependencies, test links, and completion criteria are language-independent fields; agent implementation notes are English.

Pending legacy SPEC/GOAL records may be converted once, before implementation starts. Conversion must preserve all requirements and non-goals, mark missing Item fields unresolved, and block approval until resolved. Do not convert in-progress, blocked, or crash-interrupted legacy work. Either let it close under its compatible legacy runtime before v3 activation or stop the cutover. Do not maintain two active runtimes after cutover.

Design and Result Reviews are deterministic locale projections of the same canonical Item payload and stable IDs. The approval record binds the contract version/digest, exact rendered Review digest, displayed Item IDs, approval utterance, actor, and time. A projection validator checks complete Item/test/done/dependency coverage and forbids added criteria. Korean explanatory text may clarify the canonical fields but cannot redefine them.

### Design approval

- The human's explicit approval of the Design Review authorizes implementation of the reviewed items.
- Store approval and an internal contract digest automatically. Do not require the human to paste Work ID, Goal path, or hash.
- Accept approval only for an unambiguous affirmative response to the currently displayed Review when no required decision remains unresolved.
- An active host Goal may provide tracking and continuation but is not a prerequisite for ordinary implementation.
- Any canonical or rendered approval-bundle mutation without matching human authority invalidates execution. The remedy is to show the material delta, not restart the entire ceremony.

### Mid-execution changes

- A new human instruction supersedes the affected earlier instruction.
- If it is unambiguous, remains within the Goal, and does not introduce a high-risk boundary, treat the instruction itself as approval of that exact delta. Record an `approved_amendment` event containing the source message identity, old/new contract digests, affected fields, actor, and time; regenerate the Review projection and continue without a second approval prompt.
- Any implementation change beyond the exact authorized delta invalidates execution and must be removed or reviewed.
- Request focused approval only when the change materially alters a public contract, acceptance criteria, non-goals, architecture across multiple boundaries, destructive behavior, security/privacy, secrets, external cost, or an irreversible migration.
- Do not require reapproval for implementation details that follow repository conventions.

### Scope discipline

- Define two to five reviewable implementation items for a normal Goal.
- Each item must deliver observable behavior and include its own test and completion criteria.
- Implement the primary happy path before optional fallback, resilience, optimization, or speculative edge handling.
- Add regression coverage for observed failures and risk-proportionate representative cases. Do not build a broad test matrix that displaces the core implementation.
- Do not make unrelated cleanup, generalized abstractions, compatibility layers, or future-proofing part of the current Goal.
- A Goal cannot be complete when its primary requested behavior is absent even if supporting tests and infrastructure pass.
- Optional improvements become explicit follow-up proposals and do not block acceptance unless they are required for safety or correctness.

## Git lifecycle

1. Record the current branch and commit as the work item's base. Do not assume `main` or the remote default branch.
2. Create a feature branch from that base using the repository's configured naming convention.
3. Use the current checkout for one isolated work item when safe. Use separate worktrees for independent parallel work or subagents.
4. Keep agents that edit shared interfaces, root instructions, source-of-truth documents, migrations, or lockfiles sequential under the main session.
5. Commit each independently verified implementation item. Include only files owned by the work item and never absorb the pre-existing dirty baseline.
6. Before merge, re-resolve the captured base ref, ancestry, protection, and repository policy. If the base advanced, integrate it using the repository-approved method, resolve conflicts, and rerun cumulative Impacted checks.
7. After cumulative verification and Result Review, merge the feature branch into the captured base when the base is not protected and the workflow authorizes local merge.
8. For a protected base, leave a verified branch and handoff for human merge. Never auto-push or auto-merge solely because a Goal completed.
9. Remove worktrees only after their commits are integrated or intentionally abandoned and their paths are verified.

## Human review contract

### Design Review

Render a scriptless, responsive Korean HTML decision surface from structured contract data. Do not render source Markdown as document sections.

Show at the top:

- one-sentence Goal;
- one-line scope and non-goal boundary;
- item count and any decision that still requires human input.

Show two to five stable Item cards in implementation order. Every card contains:

1. **What will be implemented**: the concrete capability or behavior;
2. **How it works**: the user/system flow in plain Korean;
3. **How it will be tested**: observable verification, not implementation trivia;
4. **Completion criteria**: explicit pass/fail conditions.

Explain any internally coined technical term inline on first use. Use a visual matched to the behavior:

- Tool/API: input -> processing -> output;
- UI: user action -> state change -> visible result;
- bug fix: failure -> root cause -> corrected behavior;
- migration: precondition -> transition -> verification -> rollback.

Show dependencies, constraints, risks, and questions only when they materially change a decision. Do not show raw Markdown, contract hashes, detailed logs, frontmatter, or an audit appendix. Status must use text and icon in addition to color.

### Result Review

Use the same Item IDs and order as Design Review. Show overall completion state and counts first. Each Item reports:

- actual implementation and observable behavior;
- relevant test results and commands at a reviewable level;
- completion-criteria status;
- planned versus actual difference and impact.

Collapse exact matches to `implemented as planned`. Material scope, acceptance, test, or public-contract differences require a visible approval state. Failed or required-but-unrun relevant tests prevent that Item from being complete. Do not add audit appendices or raw logs; link retained evidence only when investigation is needed.

Each Result Item reuses the Design behavior's visual grammar and shows the actual flow, state, corrected behavior, or migration outcome. Explain unfamiliar terms on first use in Result Review as well. A material delta must be visible in both the actual visual and the approval state; status text, icon, and color remain redundant accessibility signals.

## Skill responsibilities

### `setup-agent-harness`

- Own greenfield initialization, brownfield inventory, mapping-first reconciliation, and explicitly approved one-time structural cleanup.
- Preserve coherent existing layouts and install the control plane before suggesting moves.
- Separate document moves, content reconciliation, translation, deletion, and test reorganization.
- Protect production-source hashes during documentation/test-only cleanup.
- Apply broad changes transactionally with one reviewed-plan approval and safe recovery.

### `design-goal`

- Produce the smallest adequate contract with two to five behavior-oriented items.
- Generate the Korean card-based Design Review from structured fields.
- Treat explicit Design Review approval as execution authority.
- Keep hashes internal and support a small-change fast path.

### `execute-codex-goal`

- Allow execution from an approved contract without requiring an active host Goal.
- Capture base branch, create the feature branch, and use worktrees for independent parallel work.
- Implement core behavior first, run Impacted tests, and commit every verified item.
- Apply low-risk human amendments immediately and show only material deltas for renewed approval.
- Stop only at the defined high-risk or genuinely blocked boundaries.

### `close-goal`

- Judge completion item by item from intended behavior, relevant verification, and completion criteria.
- Require Full only when the configured cumulative impact requires it or the human requested it.
- Update only durable documents whose mapped current truth changed.
- Generate the Korean Result Review and transition the complete work tree to `.work/goals/completed` with retention dates.
- Prepare merge or protected-branch handoff without creating tracked plan archives.

### `maintain-agent-harness`

- Audit instruction/resource drift, document navigation and authority, source-document mapping, test-impact mapping and budgets, work retention, branches, and worktrees.
- Compare new findings with the recorded brownfield baseline.
- Default to report-only; allow a deterministic safe sweep from expired `completed` to recoverable `trash`.
- Never physically delete trash or rewrite production/test/document content without a separately reviewed action.

### `diagnose`

- Keep the root-cause loop bounded to the current failure and affected surface.
- Add the smallest regression proof and rerun only the relevant checks unless new evidence expands impact.

### Shared implementation resources

- Keep each `SKILL.md` concise and procedural.
- Put deterministic state, retention, rendering, mapping, migration, and integrity logic in shared authoring scripts that are generated into self-contained public Skills.
- Put detailed schemas and conditional guidance in directly linked references without duplicating SKILL content.
- Regenerate public Skill metadata and resource manifests after canonical authoring changes.

## Implementation items

### I-01: Prepare the versioned contract and dormant policy cohort

**What will be implemented**

Define the version 3 project/work/Item schemas and prepare revised global/project AGENTS templates, workflow references, documentation policy, testing policy, human-readability policy, and Goal execution policy as a non-active compatible cohort.

**How it works**

Global instructions define risk, audience, lifecycle, impact verification, and Git defaults. Repo-local AGENTS remains a short router to repository-specific paths and commands. The new cohort removes tracked Work Packet archives, mandatory Full-per-Goal, `main` as an assumed base, and user-visible hash approval, but an activation pointer remains on the legacy cohort until I-02 through I-04 are compatible.

**How it will be tested**

- Add schema tests for project v2-to-v3 preview, Item completeness, approval bundle identity, supported producer/consumer versions, and mixed-version fail-closed behavior.
- Add dormant policy contract tests for the new routing statements; do not activate negative legacy-rule assertions yet.
- Verify generated AGENTS/CLAUDE mirrors and public Skill resource synchronization.
- Verify repo-local AGENTS remains under 100 lines and contains no stale durable links.

**Completion criteria**

- Versioned schemas and a compatible Skill cohort exist without changing the active workflow.
- Generic and repo-specific rules have one owner and do not contradict each other.
- Unsupported or mixed producer/consumer versions fail before mutation.
- Distribution resource checks pass for the dormant affected resources.

### I-02: Implement mapping-first setup and debt-safe brownfield cleanup

**What will be implemented**

Extend `setup-agent-harness`, `.harness/project.yaml`, and maintenance discovery to migrate v2 configuration, map arbitrary coherent document/test layouts, establish audience and retention policy, baseline existing debt, and optionally reorganize documents or tests without changing production behavior.

**How it works**

The reconciler performs zero-execution static inventory first, classifies authority and ownership, writes a preview, and installs mappings before proposing moves. Approved baseline commands run separately. Cleanup operations are isolated by type and applied with a reversible transaction journal. Test-only cleanup is guarded by production hashes and capability-scoped before/after collection evidence. One approval covers the exact displayed migration plan; internal digests prevent drift without burdening the user.

**How it will be tested**

- Greenfield fixture with no docs or tests.
- Brownfield fixture with nonstandard but coherent paths that must remain in place.
- Static inventory fixture proving zero repository subprocess/network execution and `unknown` dynamic evidence.
- Version 2-to-3 configuration preview/apply and unsupported-version rejection.
- Conflicting document authorities and unknown test ownership that must remain unresolved without mutation.
- Windows/Linux canonical-path fixtures for overlaps, case aliases, reparse/symlink aliases, and nested repository boundaries.
- Document move fixture proving byte preservation and complete link updates.
- Test-only reorganization fixture proving unchanged production hashes, path-independent semantic test inventory, parameter/outcome state, and working local/CI selectors.
- Fault injection after every move/remove/link-update phase and exact-tree recovery tests.

**Completion criteria**

- Setup can adopt a coherent brownfield repository without moving files.
- Cleanup cannot modify production code in document/test-only modes.
- Existing debt is baselined and does not block unrelated future Goals.
- Ambiguity fails without guessed mutation.
- Baseline findings expire or reappear when their fingerprint, scope, severity, behavior, or review date changes.

### I-03: Replace Design and execution ceremony with item-driven delivery

**What will be implemented**

Replace Markdown-dump Design Review, explicit hash handoff, mandatory active Goal, and rigid amendment handling with the canonical Item schema, bound Korean projections, natural approval, internal integrity checks, core-first execution, impact verification, and per-item commits.

**How it works**

Design creates two to five canonical Items with What, How, Test, and Done fields and renders a Korean visual projection. Human approval binds the exact contract and projection automatically and is invalid while required decisions remain open. Execute selects the next core Item, changes behavior through an appropriate TDD or regression loop, runs Impacted checks, commits the verified Item, and accepts low-risk user changes as plan deltas without restarting approval.

**How it will be tested**

- HTML semantic tests for Item identity, required fields, Korean labels, inline term explanations, relevant flow visuals, accessibility status, and absence of raw contract dumps/hashes/audit appendices.
- Small-change execution without a host Goal.
- Natural approval without pasted hashes.
- Legacy pending SPEC/GOAL lossless conversion and unresolved-field blocking; active legacy work blocks v3 cutover rather than being partially converted.
- Internal drift detection that presents a delta.
- Mid-execution low-risk amendment that continues directly.
- Material public-contract or high-risk amendment that requests focused approval.
- Scope test proving optional work cannot displace an incomplete core Item.
- Git test proving one commit per completed Item without including dirty baseline files.

**Completion criteria**

- A reviewer can decide each Item from What, How, Test, and Done without reading the agent contract.
- Approved ordinary work starts without Goal/hash ceremony.
- User amendments follow risk-based delta approval.
- Every completed Item has relevant evidence and its own commit.
- Canonical Item and Korean Review coverage cannot diverge silently.

### I-04: Make close, retention, and maintenance proportional and enforceable

**What will be implemented**

Replace mandatory four-suite close gates and tracked archives with item-level completion, configured impact gates, aligned Korean Result Review, manifest-based work retention, baseline-aware maintenance, and recoverable lifecycle sweeps.

**How it works**

Close reads cumulative impact, requires only the relevant checks, updates mapped durable truth, renders Result cards with the same Item IDs and actual behavior visuals, and moves work to `.work/goals/completed`. Lifecycle sweeps use manifest dates to move expired work to `trash`; deletion remains exact-target approved. Maintenance reports new/worsened drift separately from existing baseline debt.

**How it will be tested**

- Independent change closes with Full marked `not_required` and a matched rule.
- Shared/core or test-infrastructure change requires Full.
- Failed or required-but-unrun Item tests block only the affected completion.
- Design/Result Item identity and planned-versus-actual delta tests.
- Result visual and first-use terminology tests.
- Retention state-machine, typed namespace, orphan work, duplicate ID, idempotency, interrupted move, and explicit-delete approval tests.
- Legacy archive with trustworthy, missing, and contradictory date evidence; unresolved records must remain unswept.
- Baseline-debt fixture proving unrelated old findings do not block closure while new regressions do.

**Completion criteria**

- Close never requires an irrelevant Full suite.
- Completed work leaves active state and receives deterministic retention dates.
- No ordinary Goal creates a tracked plan archive.
- Expired work is recoverably swept and never silently deleted.

### I-05: Migrate this repository and validate the complete workflow

**What will be implemented**

Atomically activate the compatible policy/runtime cohort, apply the new model to this repository, reconcile current active/completed documentation, replace hard-coded `main` workflow assumptions, align Harness tests by capability where useful, regenerate distributed resources, and validate representative greenfield and brownfield workflows.

**How it works**

The migration first proves I-01 through I-04 as a compatible dormant cohort and refuses cutover while legacy work is active, blocked, or transaction-incomplete. One activation change then switches the schema/runtime pointer, AGENTS/policies, generated Skill cohort, and negative contract tests together. Document cleanup, test organization, and current repository cleanup remain separate commits after activation. Confirmed obsolete completed Work Packets and historical implementation plans are removed from tracked current documentation only after their surviving current truth and inbound references are represented in `docs/`; uncertain release/legal evidence remains until classified. Existing pilot HTML is not treated as the new review contract.

**How it will be tested**

- Targeted tests for each changed capability throughout implementation.
- Feature tests for setup, design, execute, close, and maintain after their respective items.
- Full suite only at the point where shared policies, generated resources, test discovery, or the repository-wide workflow structure has changed.
- Resource drift, distribution validation, and `git diff --check` for affected distribution surfaces.
- Forward tests on: a tiny independent feature, a brownfield repository with mixed documentation, a large suite needing Impacted selection, a mid-execution amendment, and parallel independent branches/worktrees.
- Independent final review using the rendered human Design and Result surfaces rather than raw Markdown dumps.

**Completion criteria**

- This repository uses the same model it distributes.
- Current agent documentation is reachable from `docs/index.md`; human and agent work outputs are separated.
- Completed/stale tracked work records no longer remain active sources of truth.
- Relevant test selection works without routinely running the entire suite.
- Canonical authoring, generated Skills, tests, and distribution manifests are synchronized.
- The five representative workflows meet their Item-level acceptance criteria.
- Every intermediate commit either uses the complete legacy cohort or the complete v3 cohort; no mixed state can design, execute, or close work.
- This bootstrap Work Packet is removed in the final migration commit after its current truth, references, and verification gates are satisfied; it is not archived elsewhere.

## Migration and rollout

Implement in dependency order: I-01 -> I-02 -> I-03 -> I-04 -> I-05. I-01 through I-04 build and verify a dormant v3 cohort while the legacy cohort remains active. I-05 performs the single cutover only after schema, producer/consumer compatibility, migration, renderer, runtime, close, and maintenance checks pass together. Every commit must either keep the legacy pointer active or contain the complete v3 activation; mixed states must fail closed.

Use the current branch at implementation start as the base branch. Create a dedicated feature branch. Because canonical policies, generated Skill resources, and shared tests overlap, keep I-01 through I-04 sequential in the main worktree. Use isolated worktrees only for independent fixture exploration or forward tests that do not edit shared sources.

Do not use the current broken Review renderer as approval evidence for this migration. The present user instruction approving documentation of the final model authorizes creation and review of this Work Packet only. Actual implementation begins after the user approves this document and its independent review result. That approval authorizes I-01 through I-05; only later material deltas or high-risk operations require renewed approval.

At cutover, detect the complete legacy artifact graph: contracts, runtime state, dirty baselines, host Goal sidecars, evidence, resolved/unresolved block records, and transaction markers. Pending unstarted contracts may use the reviewed one-way converter. Any in-progress, blocked, or crash-interrupted legacy Goal prevents activation until it closes or the human approves a separately proven complete-state migration. Legacy installed Skills must be replaced as one compatible cohort.

Before integration, re-resolve the captured base branch, ancestry, and protection state. If the base changed, integrate it according to repository policy and rerun cumulative Impacted checks before Result approval or merge.

The implementation must use behavior tests for the new contract. Replace tests that assert raw Markdown inclusion, mandatory Full-per-Goal, mandatory active Goal/hash handoff, tracked archive creation, or fixed `main` assumptions. Do not preserve contradictory behavior for compatibility.

## Completion criteria

This Work Packet is ready for implementation only when an independent review confirms that it includes, without contradictory legacy requirements:

- visual, Item-based Korean Design and Result Reviews with plain-language term explanations;
- English agent sources and Korean human surfaces separated by audience and lifetime;
- `docs/index.md` as the agent documentation entry point;
- mapping-first greenfield/brownfield setup and behavior-preserving one-time cleanup;
- current-truth documentation with no default decision or completed-plan archive;
- enforceable `.work` retention and explicit physical deletion;
- source-to-test impact mapping, safe test-only reorganization, and conditional Full verification;
- no separate `align-test-structure` Skill;
- natural Design approval, internal-only hashes, optional host Goal, and low-friction user amendments;
- core-first scope discipline and proportional tests;
- current-branch base, feature branch, parallel worktrees, per-Item commits, and protected-branch handling;
- baseline-aware maintenance so unrelated existing debt does not block new work;
- Skill/resource generation and forward-test coverage for the changed workflow.
- versioned Item/project/work schemas, bilingual projection binding, and atomic policy/runtime activation;
- safe treatment of active legacy work, legacy archive dates, non-Goal `.work` writers, mapped-path collisions, and moving base branches;
- removal of this bootstrap Work Packet after the new durable truth is active and independently verified.

Any missing or contradictory item must be corrected in this document before implementation approval.
