# Work Packet Reference

This file holds policy that applies across modes. `SKILL.md` is intentionally short; mode-specific execution details live under `modes/`.

## Context budget and search hygiene

Use this section before broad repo or document exploration.

Default initial orientation budget:

- Direct file reads: at most 5 files before a retained summary.
- Searches: at most 2 orientation searches before a retained summary.
- Main-thread retained summary: 500 words or less before expanding scope.
- Raw full command output, full repo search dumps, long logs, full test output, and complete file dumps should stay out of the main thread.

Budget scope:

- These limits govern initial orientation. Mandatory safety reads required by a mode, repo `AGENTS.md`, tracker policy, approval policy, or active source-of-truth conflict may exceed the numeric budget, but must be summarized and tied to the gate they decide.
- If a required decision cannot be made inside the budget, first write a retained working summary, then delegate bounded read-only exploration when subagents are available.
- Subagents compress context and gather evidence. They do not authorize writes, approvals, merges, issue closure, branch changes, destructive actions, live provider calls, or external exports.
- For test execution, CI log review, or other verification commands, use `Verification delegation policy`; test runners may write caches, coverage, or temp files and are not plain read-only exploration.
- If no subagent mechanism is available, record the missing delegation path and continue only with bounded path-scoped reads. Stop rather than broad-searching in the main thread when a gate still cannot be decided.
- When a repo route would normally read root context, architecture, development
  policy, or active plans, skip only documents that cannot affect the current
  gate. Record each skipped source-of-truth path and why skipping was safe in
  the phase handoff capsule.
- Read raw source-of-truth context before making any claim that depends on root
  terminology, contract anchors, source authority, architecture/API/security/
  persistence, or verification sufficiency.

Search hygiene:

- Prefer `rg --files`, `rg -l`, or path-scoped searches for orientation.
- Do not run repo-wide `rg -n <pattern> .` during orientation. Use line-number searches only after narrowing to relevant paths or directories.
- Exclude archive, generated, vendored, build, cache, data, fixture, and reference directories unless the current gate directly needs them.
- Read referenced docs only when the current gate cannot be decided from already-read evidence. Stop after the first source that answers the gate.
- Keep file lists, command output, and source excerpts short; retain decisions, file paths, line references, uncertainty, and next-read recommendations instead of raw dumps.

## Phase handoff capsule

The phase handoff capsule is the first read path before tracker bodies, PR bodies, large docs, raw diffs, or raw logs. Read the capsule if present, then metadata/stat/name-only views, then exact sections or hunks needed for the current gate.

Canonical location: the Work Packet or durable tracker issue under `Phase handoff capsule`. Adjacent `.scratch` files may cache the same facts temporarily, but review-relevant facts must be mirrored into the PR body, close report, tracked docs, or durable tracker surface when they affect review, closure, or future work.

Authority: the capsule is an index, not a conclusion. Raw source, exact verification evidence, tracker state, PR state, and source-of-truth docs win on conflict. If a claim affects architecture, API, security, persistence, verification sufficiency, or close, inspect raw evidence directly.

Required fields: `updated_at`, `source_ref`, `updated_by`, `phase`, `scope`, `current gate`, `accepted decisions`, `open decisions`, `files read`, `files changed`, `tracker/PR/doc mutations`, `published_body_ref`, `grill_route`, `grill_route_reason`, `verification evidence`, `delegated evidence`, `risks`, `next mode`, and `next stop condition`.

`published_body_ref` records durable URL plus updated timestamp or version when available. Local body files and log paths are cache pointers only; they are not durable evidence unless the repo explicitly tracks or uploads them.

`grill_route` records `skipped`, `docs_grill_preflight`, `targeted_grill`, or `full_grill_with_docs`; `grill_route_reason` names triggers present, triggers ruled out, and remaining questions.

## Access path resolution

Resolve the tracker channel before ANY tracker-touching action (`issue`, `run`, `pr`, `close`,
`next`, `publish`). This is a skill policy, not a tool-sandbox behavior, and it applies equally to a
Claude orchestrator and a Codex orchestrator. The goal is to remove runtime guessing about which
GitHub path applies to which repo: the channel is **declared in the env profile and matched against
the actual git remote**, never discovered by trying a live call and seeing whether it fails.

Two channels, only one of which this skill gates:

- **Code channel** (git push/pull/fetch over SSH): available for every repo and orchestrator. NOT
  gated by this skill. Do not remove or special-case it.
- **Tracker channel** (GitHub Issue/PR query + create/update): the only governed surface. Routed
  per `(repo, orchestrator tool)` by the env profile.

Resolution steps at mode entry:

1. Read the env profile (`agent-env.<slug>.md`). If absent in a non-`init` mode, STOP and tell the
   owner to run `init`. `init` creates it.
2. Read the git remote with `git remote -v` and compute `remote_match`:
   - SSH `git@<alias>:<org>/<repo>` -> the `<alias>` token before the colon.
   - HTTPS `https://<host>/<org>/<repo>` -> `<host>/<org>`.
   - Any other remote form, or no matching binding row -> STOP and ask the owner to add a binding.
3. If the matched binding's `expected_remote_match` differs from the live remote, STOP (drift): do
   not trust either side silently.
4. Detect the current orchestrator tool (Claude or Codex) and read the matching channel column:
   `gh`, `mcp_pat`, `connector`, `handoff`, or `none`.
5. Carry the resolved channel in the phase capsule. Never probe the network to decide the channel.

Channel handling:

- `gh`: `gh` CLI with explicit `--repo <org>/<repo>`; apply sandbox escalation per the profile.
- `mcp_pat`: GitHub MCP server with a static PAT from that repo's `.mcp.json` (Claude orchestrator on
  an external account where `gh` login is unreliable).
- `connector`: Codex git connector (Codex orchestrator on an external account).
- `handoff`: no direct channel for this `(repo, orchestrator)`; produce the exact payload + command
  and hand off. Record `tracker_publish_state: handoff_pending` in the capsule so later turns do not
  re-attempt and loop.
- `none`: tracker disabled; manage Issue/PR purely as local documents.

A `handoff` or unreachable tracker never blocks the code channel: pushing the branch and producing a
publish payload can both succeed while tracker publish stays pending.

## Metadata-first Tracker I/O

Use this section before tracker-heavy `ready`, `issue`, `pr`, `close`, or `next` work.

- Prefer metadata/stat/name-only reads before body reads: issue or PR number, URL, title, state, labels, draft state, head/base refs, head SHA, merge state, and updated time.
- Prefer short-output `gh` commands for GitHub create, update, comment, label, close, and PR operations when MCP connector mutations would return full Issue or PR bodies. Use body files for long Issue/PR bodies when the host supports them.
- For reads, request JSON fields that exclude `body` and `comments` unless the current gate requires those sections.
- If a connector must be used and returns a full body, immediately compress it into the phase capsule and do not fetch the same body again.
- Never fetch a full Issue or PR body only to confirm URL, state, label, head branch, base branch, merge state, or close status.
- If no short-output path is available, treat the connector call as a context-cost escalation and state that in the phase capsule.

Retain these fields by default: `issue: number, url, state, labels, title`; `pr: number, url, state, draft, head_ref, base_ref, head_sha, merge_status`; `published_body_ref: durable_url, body_version_or_updated_at, local_cache_path optional`.

## Durable Body Ownership

Use owner surfaces to avoid duplicating long records. Link secondary surfaces to the owner instead of copying full bodies.

| Surface | Owns | Does not own |
|---|---|---|
| Parent Issue | Pre-run Work Packet spec, acceptance criteria, confirmation, scoped overrides, proposed shared-doc updates, verification plan | Final verification transcript, full close report, PR review evidence |
| PR body | Implemented slices, changed files summary, final verification capsule, architecture review, docs updated, remaining risks | Full pre-run issue body, unrelated roadmap history |
| Issue close comment | Closure capsule: PR URL, outcome, verification summary plus durable evidence pointer, remaining risk, next pointer | Duplicate full PR body or close report |
| Tracked docs/ADRs | Durable architecture, domain, source-of-truth, and policy decisions | Tracker operation transcripts |
| Active local Work Packet record (`local_pending`) | Personal working tracker in the configured path; when that path is gitignored, shared decisions and verification must be mirrored to a tracked owner surface before close or cross-clone handoff | Final published URL/state once published |
| Archive surface (published records) | Immutable copies of Issue/PR body files already published in `publish`, isolated so a later batch never re-publishes them | Active editing; archived records are history, not a working surface |
| Local body/log files | Temporary body/log cache and short-term reproducibility aid | Durable review evidence unless tracked or uploaded |

## Right-sized Grill Routing

Use the lightest mode that is safe, but bias toward `full_grill_with_docs` for non-trivial Work Packet, skill, process, tracker, verification, delegation, context-budget, orchestration, or close/done-policy changes. These changes alter how future agents work, so a wrong rule can spread through issues, PRs, docs, tests, and operator behavior.

- Use `full_grill_with_docs` by default when a Work Packet changes agent workflow gates, skill behavior, context-budget policy, mode routing, tracker I/O, verification delegation, durable body ownership, close/next behavior, done criteria, or audit policy.
- Use `docs_grill_preflight` only when repo evidence is likely to close the question and any remaining user check is light, local, and cannot open dependent workflow or policy branches.
- Use `targeted_grill` only when the remaining unknowns are already named, three or fewer, and cannot change lifecycle, routing, durable records, verification policy, or source-of-truth docs beyond the local packet.
- When unsure between `docs_grill_preflight`, `targeted_grill`, and `full_grill_with_docs` for non-trivial process or skill-maintenance work, choose `full_grill_with_docs`.
- Record `grill_route`, `grill_route_reason`, full-grill triggers present, full-grill triggers ruled out, and open questions in the phase capsule.

## Model routing policy

Quality preservation outranks fast/small model use. Use fast/small models only when a task is bounded, checkable, and does not require high-quality judgment. When uncertain, use main/high-quality.

Fast/small may handle grep or file location, read-only docs/code capsules, test/lint/type command execution, failure log compression, mechanical checklist comparison, and PR/close draft formatting after the main/high-quality model has decided the substantive content.

Main/high-quality owns scope and acceptance criteria, architecture, public API, persistence, security, lifecycle, evidence sufficiency, final diff review, final verification interpretation, and close/merge/done judgment.

Never use fast/small models for implementation unless the write scope is explicit and semantically disjoint, behavior is narrow and already specified, invariants and forbidden dependencies are named, and the main/high-quality model reviews imports, contracts, tests, and final diff.

Delegated handoffs must record `Model class`, `Allowed model use`, and `Forbidden decisions`. If the host cannot choose model class, record the intended model class and boundaries without claiming enforcement.
## Workspace and lane policy

Use three lanes:

- **Orchestration lane**: normally the current orchestration checkout and branch. Use the repo default branch only when the user, repo policy, or active mode explicitly names it. Use this lane for `init`, `ready`, `issue`, `close`, `next`, review, and source-of-truth reconciliation.
- **Implementation lane**: an implementation branch or dedicated worktree. Use it for `run` and implementation-owned `pr` updates.
- **Read-only parallel lane**: separate sessions may inspect, draft, and perform docs-aware grill work, but must not mutate shared repo files.

`init` is branchless ideation by default. It must not create implementation branches or worktrees. Starting several `init` sessions from the current orchestration branch is allowed without extra user setup only when each session writes to an isolated planning surface.

Parallel-safe `init` write surfaces:

- one GitHub issue draft or one issue body target;
- one unique local Work Packet seed draft file;
- user-visible draft output when write safety is unclear.

Shared source-of-truth docs are read-only during parallel `init`, including `AGENTS.md`, `docs/agents/*`, implementation plans, roadmap/index docs, CONTEXT docs, ADRs, verification docs, and tracker config docs.

## Issue-first contract with deferred shared-doc reconciliation

Do not split shared docs only to enable parallel planning. Keep shared docs as source-of-truth documents, but avoid writing them during `init`.

Every non-trivial `init` draft should contain an **Implementation Contract** for this Work Packet only after required grill/preflight decisions are closed or auto-closed. For `full_grill_with_docs` with unanswered direct questions, the `init` artifact is a decision scaffold only; defer the Implementation Contract, roadmap, PRD summary, vertical slices, acceptance criteria, and Implementation Confirmation Brief until alignment is complete. A direct question is unanswered until the user answers it, repo evidence auto-closes it, or it is removed from the Decision Map with a recorded reason. A recommended answer is not closure. After `ready`, the configured durable tracker is authoritative for implementation scope: the parent GitHub Issue when GitHub Issues are configured, or the local Work Packet only when local markdown is explicitly configured. An `init` seed is not the durable tracker once issue publishing is required.

When the Work Packet implies updates to shared docs, record them under **Proposed Shared Doc Updates** instead of editing the shared docs during `init`.

Use **Scoped Overrides** only when the Work Packet must temporarily override a stale or incomplete shared doc for this packet's scope. A scoped override must name the shared doc, existing statement, packet-specific override, scope, expiry, and required reconciliation.

Shared-doc update timing:

| Delta type | Default timing |
|---|---|
| Domain term required before implementation | `ready` or before `run` |
| Verification command or policy required before implementation | `ready` |
| Architecture boundary or ADR-level decision | `ready`, or separate architecture Work Packet |
| Roadmap, queue, priority, or backlog order | `next` |
| Implemented behavior, verified domain decision, docs evidence | `close` |
| Speculative idea | keep in issue or seed draft; do not apply |

Ready reconcile gate:

- Inspect all Proposed Shared Doc Updates before marking `ready-for-agent`.
- If multiple open Work Packets propose conflicting changes to the same shared doc, term, public interface, or verification policy, stop and reconcile in the orchestration lane.
- If a blocking shared-doc delta is not applied, the Work Packet must include a scoped override sufficient for implementation.
- `run` must stop if shared docs conflict with the Work Packet and no scoped override exists.

## Delegated Matt Pocock skill routing

Use these skills as delegated methods, not ceremony.

| Situation | Delegate skill | Where it fits |
|---|---|---|
| Repo lacks issue tracker, triage-label, or domain-doc config | `setup-matt-pocock-skills` or `$project-agent-bootstrap` | Before substantial implementation; `init` may still draft ideation locally |
| Raw idea, bug report, unclassified backlog, conflicting labels | `triage` | Before `init`, or inside `init` |
| Bug, broken behavior, failing verification, flaky test, performance regression | `diagnosing-bugs` | `init` as `diagnose_first`, or `run` when failures appear |
| Existing codebase feature touches domain language, user-facing behavior, workflow semantics, state, lifecycle, persistence, export/import, submission, permissions, or multi-context behavior | `grill-with-docs` | `init` as `docs_grill_preflight` or `full_grill_with_docs` |
| General non-code brainstorming | `grill-me` | Outside this repo implementation flow |
| Enough context exists to synthesize requirements after alignment and confirmation | `to-spec` | `init` after decisions are closed or auto-closed |
| Spec/plan must become vertical implementation units | `to-tickets` | `ready`, to validate slices |
| Behavior implementation | `tdd` | `run`, one vertical slice at a time |
| Product/state/UI/logic uncertainty is best answered by throwaway code | `prototype` | `init` or `ready`; capture the durable decision |
| Codebase boundary blocks implementation | `improve-codebase-architecture` | `init` as `architecture_first`, or end of `run` as scoped review |
| Unfamiliar code area needs orientation | `zoom-out` | Optional exploration before `ready` or architecture review |
| Session must transfer context | `handoff` | After `close` or when work cannot continue safely |

If a delegated skill is unavailable, do the smallest equivalent local version, state that the skill was unavailable, and record the fallback.

## Intake modes

Choose the lightest safe intake mode, but do not under-regulate agent coding. Prefer intent alignment over fast implementation when the work could encode product, domain, or workflow semantics.

- `skip_interview`: narrow, reversible, already-confirmed goal with clear acceptance criteria and no meaningful product/domain/user-visible semantic change.
- `triage_first`: raw source item whose category, state, owner, or actionability is unclear.
- `diagnose_first`: bug, failing verification, flaky behavior, performance regression, or unexplained failure. Build or identify a deterministic feedback loop before planning the fix.
- `targeted_grill`: use when the scope is otherwise clear and 1-3 known blocking decisions remain. Questions should close a specific product, state, permission, export, failure, or hard-to-reverse choice; do not broaden into unrelated discovery.
- `docs_grill_preflight`: use when the plan is mostly clear but repo docs/code need a light terminology, edge-case, or source-of-truth check before implementation. Inspect evidence first, auto-close repo-answerable decisions, and ask only the highest-impact remaining question.
- `full_grill_with_docs`: use when the agent must walk the product/domain decision tree before implementation because the wrong abstraction, lifecycle, roadmap, state model, public contract, or workflow meaning could spread through code, docs, issues, tests, or user-facing behavior.
- `prototype_first`: a throwaway prototype would answer the question faster than discussion.
- `architecture_first`: architecture friction blocks safe implementation.

## Full grill threshold

`full_grill_with_docs` means full decision-tree alignment, not a longer version of `targeted_grill`. It is the normal guardrail for non-trivial agent coding when intent, domain language, or workflow confidence is not high enough.

Use this selection rubric before choosing a grill mode:

- Choose `targeted_grill` when the unknowns are already named, few, and local to the requested Work Packet.
- Choose `docs_grill_preflight` when repo evidence is likely to answer most uncertainty and only a light user check may remain.
- Choose `full_grill_with_docs` when the shape of the decision tree itself is uncertain, when answers can open dependent branches, or when the wrong choice would create durable product/domain language.
- For internal process, skill-maintenance, tracker hygiene, verification-log policy, context-budget, delegation, mode-routing, durable-record, or close/done-policy changes, apply `Right-sized Grill Routing` with a full-grill bias; use a lighter grill mode only when the change is narrow, mechanical, and cannot open dependent workflow or policy branches.

Choose `full_grill_with_docs` when any trigger applies:

- The Work Packet introduces or renames a product/domain concept that will appear in code, docs, UI, issue titles, data model, API, or tests.
- The Work Packet creates or reorders a roadmap, phase plan, architecture strategy, cross-domain expansion plan, trace/eval ownership model, observability boundary, or domain proving order.
- The Work Packet changes agent workflow gates, skill behavior, context-budget policy, mode routing, tracker I/O, verification delegation, durable body ownership, close/next behavior, done criteria, or audit policy.
- Existing terms are overloaded, inconsistent, or conflict across docs, code, UI, packages, or prior issues.
- The change adds or changes state, lifecycle, permission, policy, persistence, export/import, submission, handoff, failure behavior, or user-facing workflow meaning.
- The implementation would create a new abstraction, boundary, durable data shape, public interface, or ADR-level decision.
- The observable behavior is clear but the purpose, non-goals, or success criteria are not explicit.
- The acceptance criteria depend on interpreting fuzzy terms such as manage, sync, preset, configuration, template, state, mode, workflow, export, submit, validate, or integration.
- More than one meaningful product/domain question remains after code/docs inspection, or one remaining question has dependent branches that could change scope, terminology, lifecycle, verification, or docs.
- The implementation seems easy but a wrong choice would be hard to reverse, visible to users, or likely to spread through the codebase.
- Intent confidence is below `0.85` for product/domain/user-facing work, or below `0.75` for purely internal work.
- The agent cannot explain the purpose, core implementation target, observable changes, non-goals, and verification signal in a short confirmation brief.

Do not use `full_grill_with_docs` for routine bugs with a deterministic repro, mechanical dependency updates, typo/copy-only changes, narrow test updates, or implementation-only refactors with no behavior, domain, workflow, public-interface, or persistence impact.

Existing docs can auto-close specific decisions, but they do not downgrade a full-grill request into `docs_grill_preflight` while direct product/domain questions remain or while dependent branches are still unknown. When unsure between `docs_grill_preflight` and `full_grill_with_docs`, choose `full_grill_with_docs` for non-trivial product/domain feature work and for non-trivial internal process or skill-maintenance work. Use a lighter mode only when evidence proves the change is mechanical, local, and branch-free. Agent coding should be regulated by intent clarity, not by implementation confidence.

## Grill conduct and fixed question format

`grill-with-docs` is for alignment, terminology, edge cases, and decision closure. It must not implement.

Before asking any direct grill/preflight question, present a compact **Decision Map**; in other words, present a compact Decision Map before every direct grill/preflight question. This applies to `targeted_grill`, `docs_grill_preflight`, and `full_grill_with_docs`; the difference is depth, not whether the map exists. Decision Map may be written in Korean when the user-facing grill is Korean, while canonical repo terms may remain in English when clearer:

```md
## Decision Map

| Category / 카테고리 | Why it matters / 왜 중요한가 | Estimated questions / 예상 질문 수 | Direct questions / 직접 질문 |
|---|---|---:|---|
| <category or Korean category> | <short business/product reason in Korean or English> | <min-max> | <question labels> |

- Total estimated questions / 전체 예상 질문: <x-y>
- Questions to ask directly now / 지금 직접 물을 질문: <count>
- Decisions likely auto-closed from repo evidence / repo 근거로 자동 종료할 결정: <count>
```

Decision Map fields:

- **Category / 카테고리**: decision category that must be closed before implementation.
- **Why it matters / 왜 중요한가**: short business/product reason, not implementation trivia.
- **Estimated questions / 예상 질문 수**: category-level expected question count.
- **Direct questions / 직접 질문**: questions that truly require the user; repo-answerable questions must be auto-closed from docs/code evidence.
- For `targeted_grill`, present a compact Decision Map with only the known blockers; do not expand into unrelated discovery.
- For `docs_grill_preflight`, present a mini Decision Map that separates repo-auto-closed decisions from the remaining user question.
- For `full_grill_with_docs`, present the normal Decision Map and keep deeper branch tracking internal unless the user needs a status update.

### Full Grill Decision Tree Protocol

Use this protocol only for `full_grill_with_docs`. Keep the user-facing output readable: show the Decision Map/status and one question, not an internal process dump.

- Build decision branches for terminology, actor or user outcome, workflow/lifecycle/state, abstraction or data shape, permissions/failure/persistence, verification/eval, and docs/ADR impact when relevant.
- Track each branch internally as `open`, `auto-closed`, `closed`, or `skipped-with-reason`; a recommended answer is not closure.
- Ask the next dependency-unblocking question, not merely the easiest or broadest question.
- Use concrete scenario probes when a branch is fuzzy; auto-close the probe only when repo evidence answers it.
- Finish full grill only when all relevant branches are closed, auto-closed, or explicitly skipped, and the purpose, non-goals, observable changes, verification signal, and docs/ADR impact are clear enough for confirmation.

Ask exactly one question at a time using this fixed format. Do not change the `진행` line shape:

During `init`, write every direct user-facing grill question block in Korean (`ko-KR`) regardless of the surrounding canonical section language. This applies to `full_grill_with_docs`, `docs_grill_preflight`, and `targeted_grill`: the Decision Map, question title, question intent, and recommended answer may be Korean; Decision Map labels may keep repo terminology when that is clearer.

```md
진행: [카테고리 n/m, 전체 예상 x~y개 중 z번째]

## Q. [질문]
질문 의도:
- <이 질문이 닫는 비즈니스 결정과 추천 답변을 고르는 기준을 한 문장으로 설명한다. Decision Map의 Why it matters를 반복하지 않는다.>

추천 답변:
- <권장 답변을 먼저 쓰고, repo evidence, product intent, reversibility, verification 기준의 짧은 이유를 필요한 만큼만 덧붙인다.>
```

Rules:

- First inspect relevant code/docs. Do not ask the user to restate facts that the repo can answer.
- Ask one question at a time and keep the sequence within the Decision Map unless new evidence changes the map.
- Keep questions product/domain/user-outcome focused, not internal implementation trivia.
- Keep the question block compact: one decision point, one recommended answer, no explanation of every alternative.
- Prefer recommended answers that reduce scope ambiguity, avoid hard-to-reverse abstraction mistakes, and preserve verification clarity.
- If the response asks a direct grill question, it must not also include implementation-planning sections such as roadmap, PRD summary, vertical slices, acceptance criteria, Implementation Contract, Codex goal, or Implementation Confirmation Brief.
- Stop `targeted_grill` when the named blockers are closed; stop `docs_grill_preflight` when repo evidence and any single remaining check leave no blocking ambiguity; stop `full_grill_with_docs` only when the relevant decision branches are closed or explicitly skipped.
- Record closed decisions, auto-closed decisions, scoped overrides, and docs/ADR update targets durably.

## Implementation confirmation gate

Before a non-trivial Work Packet can become `ready-for-agent`, publish an Implementation Confirmation Brief and record explicit scope confirmation.

This applies even when the implementation looks clear. Confirmation verifies that the agent is about to build the right thing; it is not approval for destructive or security-sensitive actions.

Use `templates/implementation-confirmation.md`. The brief must state:

- purpose;
- core implementation target;
- observable or user-facing changes;
- what will not change;
- key assumptions and risks;
- verification signal;
- whether `docs_grill_preflight` or `full_grill_with_docs` was used or skipped and why;
- any scoped overrides and proposed shared-doc updates that affect implementation.

Ask exactly one confirmation question after the brief. The preferred question is:

```text
Confirm this Work Packet as the implementation target? Reply yes/proceed, or name the one core change to adjust before implementation.
```

Confirmation is satisfied only by one of these:

- the user explicitly confirms in the current session;
- the source issue, PRD, or implementation plan already contains equivalent confirmation for the same scope;
- the user passes `--confirmed`, which confirms only this Work Packet scope.

`--confirmed` does not bypass required `full_grill_with_docs` when the full grill threshold is met. It also does not approve risky actions, tracker migration, secret handling, destructive operations, irreversible migrations, live provider calls, or costly external operations.

If confirmation is missing, keep the Work Packet in `needs-confirmation` and do not run `issue`, `run`, or `pr` as implementation-ready phases.

## Architecture trigger policy

Use normal implementation with a scoped architecture review when the existing seam/interface/module can support the change, the Work Packet fits 2-5 vertical behavior slices, verification can prove behavior without broad boundary changes, and refactoring is limited to touched modules, interfaces, seams, adapters, tests, diagnostics, and docs.

Use `architecture_first` before implementation when runtime boundaries, persistence, context policy, provider/model interfaces, diagnostics, or cross-domain contracts are unclear; no credible public behavior test seam exists; the same boundary caused repeated friction; domain/runtime responsibilities are mixed; public interfaces likely need redesign; verification cost is rising because responsibilities are mixed; or the work requires a hard-to-reverse ADR.

Do not hide broad architecture rewrites inside feature implementation.

## Tracker and durable record policy

The configured tracker is defined by `docs/agents/issue-tracker.md` and root/local `AGENTS.md`. Do not infer local markdown tracking only because `.scratch/` exists.

When GitHub Issues are configured:

- `init`: may create a local Work Packet seed draft or issue body draft for parallel-safe ideation.
- `ready`: finalizes the Implementation Contract, confirmation evidence, slice plan, and issue body, but does not make a local seed the durable tracker.
- `issue`: must create or update one parent GitHub Issue before `run` starts.
- `run`, `pr`, and `close`: must cite the parent issue, with `.scratch/` used only for local drafts, intermediate notes, smoke outputs, and temporary close reports.
- If GitHub access is unavailable, output the exact issue title, body, labels, and command/API payload, then stop before `run` unless the repo explicitly configures a local-only fallback.
- On the first GitHub create/update failure caused by unavailable auth, network, or permission, emit the exact payload and stop. Do not retry repeatedly or fall back to local durable tracking unless that fallback is explicitly configured.

Preferred durable structure when GitHub Issues are configured:

- Parent Issue: pre-run Work Packet spec, PRD summary, slices, acceptance criteria, decisions, user confirmation, implementation contract, scoped overrides, proposed shared-doc updates, verification plan, approval boundaries, and Codex goal stopping condition.
- PR: implemented diff, linked issue, changed slices, exact verification capsule, review discussion, architecture review result, docs updated, remaining risks, merge or non-merge decision, and close summary.
- Issue close comment: short closure capsule with PR URL, outcome, verification summary plus durable PR/archive/capsule pointer, remaining risk, and next pointer; do not duplicate the full PR body or close report by default.
- Tracked docs/ADRs: durable architecture, domain, and source-of-truth updates.
- `.scratch/`: local drafts, intermediate notes, smoke outputs, temporary body/log caches, and temporary close reports only.

When local markdown tracking is explicitly configured or the repo is not yet configured:

- Create one unique Work Packet draft under the configured local path.
- The configured path may be a gitignored personal plan tree such as
  `docs/plans/<owner-slug>/<feature-slug>/`; when so configured, keep Work Packet, spec, tickets,
  child issues, and notes inside that tree so parallel agents never share mutable planning files.
- If no local path is configured and `init` is only ideation, use `.scratch/work-packets/` as a safe local fallback with a unique file name.
- If that path is gitignored, mirror settled shared decisions and verification evidence into tracked
  source-of-truth docs or a PR body before close or cross-clone handoff. The ignored plan remains
  local operating state and must not be the only cross-clone record.
- Do not silently migrate trackers. Ask or follow the repo migration doc.

## Document layout and merge safety

Use one consistent repository document layout so personal records, shared source-of-truth, and agent
control-plane docs stay separated, and so collaboration does not cause merge conflicts. Adapt to repo
evidence; never assume a path exists without checking.

Canonical layout:

- `docs/agents/` - agent control-plane / reference docs (`workflow.md`, `issue-tracker.md`,
  `triage-labels.md`, `domain.md`, setup report). Shared-mutable; edited only in the orchestration lane.
- Configured local-markdown plan root (for example
  `docs/plans/<owner-slug>/<feature-slug>/`) - agent-local Work Packet, spec, tickets, child issues,
  and notes. It may be gitignored when repo policy prioritizes conflict-free parallel planning.
- `docs/work-packets/<owner-slug>/` - tracked `local_pending` Issue/PR body files only when a remote
  tracker publish workflow requires them.
- `docs/archive/work-packets/<owner-slug>/` - published/completed Work Packet records moved here by
  `publish`; append-only and immutable.
- `docs/archive/` - completed or superseded design and planning docs (PRD, implementation plan,
  design notes, decision records) moved here when their work is done, preserving decision history and
  verification evidence; append-only and immutable. Active plans stay out of the archive.
- `docs/adr/`, `docs/architecture*`, `docs/implementation-plan.md` - overall architecture and
  source-of-truth docs.
- other `docs/*` - remaining project docs.
- `.scratch/` - ephemeral drafts and operating state only; never the configured plan root.

Merge-safety rules for SHARED documents (index/navigation/roadmap/queue/status such as
`docs/index.md`):

- Keep personal records in per-owner subdirectories, never in one shared file, so concurrent work
  produces no conflicts.
- Prefer a shared index that is DERIVED/regenerable from the per-record files over a hand-maintained
  list; regenerate rather than hand-merge when possible.
- When an index must be hand-maintained, make it append-only with one entry per line, stably ordered
  by an immutable key (e.g. issue number). Each owner appends only their own line(s); do not reflow,
  reorder, or rewrite the whole file.
- Edit shared indexes only in the serialized orchestration lane, never from parallel `init` or `run`;
  defer roadmap/queue/index updates to `close`/`next` in that lane.
- If two owners must change the same shared doc, term, interface, or index region, stop and reconcile
  serially before either proceeds.

## Korean reporting and summary policy

User-facing result reports from this skill should be Korean. Keep technical/professional terms in English when that is the clearer canonical form, including Work Packet, Implementation Contract, Scoped Overrides, Proposed Shared Doc Updates, verification evidence, architecture review, PR, Issue, command names, file paths, code identifiers, labels, API/library/model names, and section names.

Issue and PR titles should be English. Issue and PR bodies should use English canonical sections. Every GitHub Issue and PR created or updated by this skill must include a Korean summary at the top for review speed. Local Work Packet drafts may include it when useful. The Korean summary is non-normative.

Shape the Korean summary as a variable-length compact, executive-readable Korean brief with subheadings, not a translated duplicate of the canonical sections. Put the business/review decision first: explain what operational, review, audit, customer, or follow-up decision becomes easier, then describe only the implementation impact needed to understand that judgment.

Use `### 목적` for the business or review flow being improved. This section should be understandable to company leadership without reading code identifiers. Use `### 핵심 구현 사항` for impact, core change or result, and any necessary scope boundary or risk. For PR bodies, add `### 핵심 구현 결과` under `### 핵심 구현 사항`: leave it empty or as `TBD: 구현 완료 후 작성` when creating an initial or draft PR, then fill it during the implementation-complete PR update with what was actually changed and what reviewers should confirm. Default to the shortest complete brief; small changes may need only a few sentences, while complex work may use more, but avoid filler and avoid explaining every implementation detail.

Technical identifiers, file names, event names, schema names, and command names may appear only when they materially help understanding. Put business meaning before technical identifiers, and explain unavoidable technical terms on first mention in plain Korean, for example `approval trace(승인 이력을 추적하는 기록)` or `runtime permission(실제 실행 가능 여부)`. Do not lead a sentence with a chain of identifiers, and avoid dense identifier-heavy sentences.

Do not use bullet lists, numbered labels such as `변경사항 1`, or standalone `검토`/`리스크` summary rows. Do not include verification command lists or standalone verification status in the Korean summary; keep exact verification evidence in the canonical Verification section. The summary must not introduce facts, scope, acceptance criteria, verification claims, or risk decisions that are absent from the English canonical sections or source-of-truth docs.

Use `templates/korean-summary.md`.

## Branch naming policy

Use repo evidence first. If no convention exists, use slash-free examples:

```text
wp-<work-packet-id>-<slug>
issue-<issue-number>-<slug>
```

Do not introduce `/` in branch-name examples unless repo evidence already requires that convention.

Owner slug normalization (collaboration): the owner slug from the env profile is lowercase
alphanumeric only (`a-z0-9`), with spaces and non-alphanumerics removed. Use the slug, never the
display name, in any branch prefix or folder name, to avoid case, space, or non-ASCII breakage. When
the repo already uses owner-less branches such as `issue-<issue-number>-<slug>`, keep that convention
and do not force an owner prefix; add an owner prefix like `<owner-slug>-issue-<issue-number>-<slug>`
(slash-free) only when collaborators share branch namespace and the repo has no other disambiguator.

## Implementation worktree policy

Parallel implementation is conditional, not the default. It is allowed only when:

- each implementation lane owns exactly one `ready-for-agent` Work Packet;
- file overlap is low;
- no shared interface, schema, migration, lockfile, `AGENTS.md`, `docs/agents/*`, source-of-truth doc, or unresolved domain decision is touched;
- verification can run independently;
- PR order does not matter.

`run` is the first mode that may create or switch implementation branches or worktrees.

## Base reflection and protected-branch policy

Work shuttles only between the implementation branch and the resolved base/integration branch. Never
auto-merge, auto-rebase, or auto-push the implementation into a protected branch.

- Resolve the base branch as in `run`: `git symbolic-ref --quiet refs/remotes/origin/HEAD` when it is
  set and reachable; else the env profile `integration_branch`; else STOP and ask. Do not assume the
  default branch or `main` merely because it exists.
- Determine protected branches from the env profile `protected_branches` (default `[main, master]`).
- If the resolved base is itself protected (common when base equals the default branch), `next` and
  `close` MUST NOT auto-merge, auto-rebase, or auto-push the implementation into it. Hand off instead:
  report the implementation branch, the intended base, the exact reflection command, and stop.
  Reflecting into a protected branch requires explicit human permission or a human action.
- If the resolved base is NOT protected, reflecting the implementation into the base may proceed only
  when the owner authorizes it and verification evidence exists. Even then, never touch a protected
  branch.
- Never merge, rebase, or pull a protected or default branch INTO the active implementation branch as
  cleanup. The active branch only takes fast-forward updates from its own upstream.

## Final active-branch refresh policy

Run a final local branch refresh at the end of `close` when `close` is the terminal command, and at the end of `next` when `next` is run manually or as the final phase of `auto`.

Branch target:

- By default, refresh the branch that is current in the implementation repo when the refresh starts.
- Match that local branch to its configured upstream remote branch.
- Do not infer the repo default branch or `main` as the refresh target merely because it exists.
- Use a repo-configured default branch, `main`, or any other named branch only when the user, repo policy, or active mode explicitly names that target.
- If the current branch or its upstream cannot be proven, skip refresh and report the reason.

Refresh steps:

1. Inspect `git status --short`.
2. Inspect the current branch and its upstream before any pull.
3. Do not switch branches unless an explicit target was provided and unresolved dirty changes, uncommitted implementation changes, or unpushed commits will not be hidden or lost.
4. Stay on the current branch by default.
5. Pull latest changes from the current branch's upstream with fast-forward only, normally `git pull --ff-only`.
6. Do not merge, rebase, or pull the repo default branch into the active branch as cleanup.
7. Report the local branch, upstream branch, and whether pull succeeded, failed, or was skipped.

Do not delete local or remote branches as part of this cleanup unless repo policy explicitly requires it.

## Bounded auto approval policy

Invoking `$work-packet auto` with tool permissions set to auto is treated as bounded approval for routine, skill-scoped LOCAL and code-channel git operations needed to complete the local-document Work Packet flow. It is not an approval to publish.

This bounded approval is workflow intent only. It never overrides platform or tool approval prompts, sandbox/credential escalation requirements, connector permission failures, destructive-operation approval, secret or credential handling, live provider calls, force-push, branch deletion, repository deletion, irreversible migrations, external data export beyond issue/PR/tracker updates, or costly/security-sensitive operations.

Satisfy the resolved tracker channel's own requirements before any tracker write, independent of which tool is the orchestrator; for example, request sandbox escalation in Codex sandboxed environments, or use the PAT-backed `mcp_pat` channel. This applies to PR create/update, issue publish/update/close, merge, and release actions, which happen in `publish`, not in `auto`.

Under `auto`, bounded approval covers only, when scoped to the active Work Packet:

- creating, switching to, and committing on the implementation branch;
- preparing local `local_pending` Issue/PR body files;
- final active-branch refresh after `next`.

Under `auto`, bounded approval does NOT cover tracker publish, push to a protected branch, PR merge, or issue closure. Those are deferred to the human-triggered `publish` mode and to explicit human action.

`publish` is never blanket-auto-approved: the owner authorizes each batch. When the owner runs `publish`, the in-scope tracker writes it may perform are:

- creating or updating the parent issue;
- applying or updating tracker labels/statuses configured for this flow;
- creating, switching to, committing on, and pushing the implementation branch;
- creating or updating a draft or normal PR;
- answering tool prompts such as `Approval needed to export/create PR:` as approved when the PR body, title, target, and linked Work Packet are in scope and the owner authorized the batch;
- marking the PR ready for review when verification evidence exists and repo policy permits it.

Merging a PR and closing the linked issue are NOT auto-approved. Reflecting into the base, default, or any protected branch always requires explicit human permission or a human action per the `Base reflection and protected-branch policy`. The conditions below are necessary but not sufficient; even when they all hold, the skill never performs the merge into a protected branch on its own.

Auto-merge conditions:

- The PR was created or updated for the active Work Packet.
- The user did not pass `--no-auto-merge`.
- Repo policy does not prohibit merge.
- The target branch is not protected, or the owner has explicitly authorized the merge.
- Required verification evidence is recorded.
- Required CI checks are passing, or the repo explicitly has no CI requirement.
- Required branch-protection reviews, merge queue requirements, or repository policy gates are satisfied.
- The PR is not draft.
- No approval-sensitive non-GitHub gate remains.
- No unresolved risks require human review.

This bounded approval does not apply to work outside this skill's scope and does not approve destructive operations, secret or credential handling, irreversible migrations, live provider calls, external data export beyond issue/PR/tracker updates, costly external operations, security-sensitive changes, tracker migration, repository deletion, branch deletion, force-push, or history rewrite.

`--no-auto-pr` overrides all PR creation/update behavior in `publish`. `--no-auto-merge` allows PR creation/update but prevents merge and issue closure.

## Verification delegation policy

Use this policy whenever `run` needs test, lint, type, build, CI log review, or repeated verification output. When subagents are available, delegate command execution by default and keep raw output out of the main session.

- The main agent owns test intent, command selection, RED/GREEN acceptance, acceptance criteria, final interpretation, and the done claim.
- Delegated verification may run only exact repo-declared local commands supplied by the main agent, or inspect exact logs/artifacts supplied by the main agent. Use it by default for focused or broad tests, lint/type/build checks, noisy failure compression, bounded flaky/slow triage, and CI log review when subagents are available.
- Delegated verification is side-effect-constrained, not read-only. Normal test-run cache, coverage, and temp artifacts are allowed, but the subagent must not edit source, tests, docs, snapshots/goldens, fixtures, lockfiles, tracker surfaces, branch/PR/issue state, or run branch changes, commits, merges, destructive commands, dependency installs, migrations, live/network/provider/export/secret-handling operations, or approval/escalation requests.
- Before delegation, record the expected signal: slice/test intent, cwd or worktree, branch/ref, command, relevant env gates, expected RED/GREEN/other result, rerun budget, and stop condition. The subagent must not broaden commands unless explicitly asked. Redirect raw output to a log artifact when noisy output is expected, and retain only the verification capsule in the main session.
- The main agent should run verification locally only when no subagent mechanism is available, the command is a tiny smoke check whose full output is already bounded, the subagent lacks required local access, or ambiguous evidence must be rerun for final interpretation. Record the reason when main runs tests directly.
- A delegated RED is valid only when a new or changed test fails through the expected behavior/assertion. Collection, import, environment, fixture setup, syntax, or unrelated failures are blockers, not RED evidence.
- If delegated evidence is ambiguous, rerun the focused command locally or inspect enough raw output to decide. Unexpected failures, flaky behavior, slow tests, or performance regressions should route to `diagnosing-bugs` after bounded evidence capture, not repeated unbounded reruns.
- Return a verification capsule instead of raw logs: `agent`, `scope`, `cwd`, `branch/ref`, `git status`, `command`, `relevant env gates`, `exit code`, `duration`, `expected result`, `actual summary`, `pass/fail/skip counts when known`, `changed fixtures or generated artifacts`, `known noisy diagnostic note`, `notable diagnostics`, `expected/unexpected`, `failure signature`, `file:line`, `artifacts/log path`, `checks not run`, `main-agent interpretation`, `confidence`, `recommended next action`, `uncertainty`, and `rerun trigger`.

## Verification evidence

Every implementation or close report must include a capsule, not raw logs by default:

- exact commands run;
- result summary;
- delegated verification provenance when used, including `run by`, cwd/worktree, branch/ref, relevant env gates, exit code, expected/actual result, pass/fail/skip counts when known, changed fixtures or generated artifacts, notable diagnostics, failure signature or artifact/log path, rerun trigger, and the main agent's interpretation;
- checks not run and why;
- known risks;
- docs/tracker updates performed;
- unverified assumptions.
