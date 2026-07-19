# WP-20260719-002: Harness V2 Core Workflow And Release Candidate

## Status

- Phase: run preparation
- Branch: `wp-20260719-002-harness-v2-core-release`
- Base: `develop` at `f16598a`
- Tracker channel: `none` (local markdown is authoritative)
- Confirmation: supplied by the user in the active goal
- Git publish state: `local_only`
- Tracker publish state: `local_pending`

## Objective

Implement and verify WP-02 through WP-06 from `harness_v2_implementation_plan.md`: the seven self-contained Harness V2 Core Skills, their project/contract/runtime/review helpers, release validation, installation smoke coverage, and three recorded pilots.

## Source Of Truth And Decisions

- `harness_v2_implementation_plan.md` wins on conflict with `skill_recreate_plan.md`.
- `docs/architecture/skill-inventory.md` defines public, legacy, and future catalog ownership.
- Installed Skills must be self-contained. Shared authoring sources are copied into consuming Skill directories through `authoring/resource-map.json`; installed Skills never reference `authoring/` or another Skill at runtime.
- Python standard-library scripts provide deterministic filesystem, schema, hash, DAG, rendering, and maintenance behavior. `SKILL.md` files own agent orchestration and approval boundaries.
- Generated-file headers are extension-aware: Markdown uses HTML comments, Python uses comments, and JSON/YAML remain syntactically valid. WP-02 adds the regression test before mapping executable/template resources.
- `.work/` is ephemeral and gitignored. Fixtures use temporary directories; durable tests and pilot reports contain no links into `.work/`.
- Existing files and dirty changes are preserved. Destructive maintenance is report-only unless a future user explicitly requests apply.
- Public release means a verified `v2.0.0` release candidate in repository metadata and CI. Creating a live GitHub Release or tag remains out of scope unless explicitly authorized.

## Architecture

```text
authoring/
  references/                  canonical shared policies
  templates/                   canonical project/work/review templates
  scripts/                     deterministic canonical helpers
  resource-map.json            source-to-self-contained-skill copies

skills/<core-skill>/
  SKILL.md                     orchestration, gates, user-visible workflow
  references|assets|scripts/   generated or skill-owned runtime resources

tests/
  harness/                     WP-02..05 behavior and adversarial fixtures
  pilots/                      three end-to-end workflow simulations
  distribution/               catalog, packaging, CI/release/smoke contracts
```

Helpers exchange JSON on stdout and use non-zero exits for contract violations. Markdown files remain human-authoritative; JSON/YAML-like configuration is parsed only within the documented minimal schema. Renderers escape all untrusted text and do not execute it.

## Vertical Slices

### Slice 1 / WP-02: Project Bootstrap

Deliver:

- `setup-agent-harness` with evidence discovery, classification, dry-run plan, conflict diff, and explicit apply workflow.
- Project instruction, `TESTING.md`, and `.harness/project.yaml` templates.
- Helpers for byte-identical instruction hashes and validation of recorded commands.
- New, partial, overgrown, and drift fixtures. The three explicitly required acceptance fixtures remain new/partial/drift; overgrown covers the fourth classification defined by the workflow.

TDD acceptance:

- RED first for all three fixture classifications and dry-run/apply behavior.
- RED first for extension-aware generated-resource headers so copied scripts and configuration remain parseable.
- Existing conflicting files are not overwritten and a readable diff is returned.
- `AGENTS.md` and `CLAUDE.md` are byte-identical after an approved clean apply.
- `.work/` is gitignored and no nonexistent verification command is recorded.

Commit: `feat: add harness v2 project bootstrap`

### Slice 2 / WP-03: Design Contract

Deliver:

- `explore-idea` read-only workflow and `design-goal` contract workflow.
- `SPEC.md`, `GOAL.md`, Plan, `RESULT.md`, and `BLOCKED.md` templates.
- Contract validator, canonical hash, approval metadata, dependency DAG validator, and static Design Review renderer.

TDD acceptance:

- Small and multi-plan fixtures validate.
- Pending approval cannot execute; approved contract mutation causes hash drift.
- Missing dependency and dependency cycle are rejected; valid plans receive deterministic topological order.
- Required Markdown sections are enforced and renderer output HTML-escapes untrusted input.

Commit: `feat: add harness v2 design contracts`

### Slice 3 / WP-04: Codex Goal Execution

Deliver:

- `execute-codex-goal` preflight, next-plan selection, atomic state transition, evidence recording, and Hard Stop handling.
- Rewritten self-contained `diagnose` preserving the documented feedback loop.
- `BLOCKED.md` generation and retry evidence.

TDD acceptance:

- No active Goal, mismatched Work ID/path/hash, instruction drift, or unapproved contract produces zero source mutations.
- Fake Goal state executes eligible plans in dependency order.
- A reproduced failure enters diagnose, records root-cause/regression evidence, and can retry.
- Hard Stop records blocked state and every mandatory `BLOCKED.md` section.

Commit: `feat: add harness v2 goal execution`

### Slice 4 / WP-05: Close And Maintenance

Deliver:

- `close-goal`, Markdown result/handoff generation, and escaped static Completion Review HTML.
- Durable-link, finding-severity, archive/retention, and safe worktree checks.
- `maintain-agent-harness` report-only audit covering instruction/resource drift and stale work.

TDD acceptance:

- Any High finding blocks completion.
- Tracked documents referencing `.work/` block completion.
- Unrun Live/Eval checks are reported as unverified rather than failed.
- Archive-to-trash and worktree cleanup remain report-only by default.
- Instruction drift and residual worktree paths are detected.

Commit: `feat: add harness v2 close and maintenance`

### Slice 5 / WP-06: Release Candidate And Pilots

Deliver:

- Public catalog updated from `future_core_skills` to the seven active Core Skills.
- GitHub Actions distribution validation, local release-candidate metadata, and install/update smoke coverage.
- Recorded isolated pilots for a small bug fix, a normal feature, and a multi-plan medium feature.
- README/install documentation updated to current behavior.

TDD acceptance:

- Distribution checks prove 18 expected public Skills, zero discoverable legacy workflows, valid resources, and generated-resource hash alignment.
- Local fake-CLI tests cover install and update without network access.
- Explicitly approved real `npx skills` isolated install smoke is recorded separately.
- All three pilots exercise design approval, execution ordering, close gates, and durable result reporting.

Commit: `release: prepare harness v2.0.0 candidate`

## Verification Plan

Run focused tests at each RED and GREEN boundary, then after every slice:

```powershell
python -m unittest discover -s tests -p "test_*.py"
powershell -NoProfile -File scripts/sync-skill-resources.ps1 -Check
powershell -NoProfile -File scripts/validate-distribution.ps1
git diff --check
```

WP-06 additionally runs, only with explicit external-execution approval:

```powershell
powershell -NoProfile -File scripts/test-install.ps1
```

Verification records must capture command, runner, cwd, branch/ref, exit code, pass/fail/skip counts where available, notable diagnostics, and unrun checks.

## Delegation And Review

- The main session owns this contract, shared interfaces, source-of-truth docs, branch integration, final verification interpretation, and merge/push.
- Each implementation slice is delegated with exact write scope and mandatory RED/GREEN evidence. Agents must not change another slice's public interface without escalation.
- A separate read-only reviewer inspects the complete diff after WP-06. High findings are fixed and re-reviewed before merge.
- Final architecture pass covers touched module boundaries, self-containment, tests, diagnostics, and obsolete paths.

## Stop Conditions And Approval Boundaries

Stop for destructive deletion, secret/credential handling, live provider calls beyond the explicitly approved install smoke, irreversible migration, security-sensitive behavior, unresolved contract decisions, or verification failure without a credible diagnostic loop. Do not create a tag or GitHub Release. Do not merge or push until review and complete verification pass; the user's active goal explicitly authorizes merging this branch into `develop` and pushing `develop` after those gates pass.

## Phase Handoff Capsule

- updated_at: 2026-07-19T23:32:54+09:00
- source_ref: `harness_v2_implementation_plan.md`
- updated_by: main session
- phase: run preparation
- scope: WP-02 through WP-06
- current gate: delegated implementation
- accepted decisions: self-contained generated resources; Python stdlib helpers; local markdown tracker; five slice commits
- open decisions: none blocking
- files read: implementation plan, parent plan excerpts, inventory, workflow, README, authoring resource map, distribution catalog
- files changed: Work Packet; WP-02 bootstrap resources; WP-03 contract resources; WP-04 Goal runtime, `execute-codex-goal`, rewritten `diagnose`, runtime fixtures, and tests
- tracker/PR/doc mutations: local Work Packet created
- tracker_channel: none
- git_publish_state: local_only
- tracker_publish_state: local_pending
- published_body_ref: none
- grill_route: skip_interview
- grill_route_reason: the user supplied exact remaining WPs, branch/commit/review/merge workflow, and the active plan fixes acceptance criteria
- verification evidence: branch created from clean `develop` at `f16598a`; WP-02 passed 34/34 unittests and 4/4 resource checks; WP-03 passed 42/42 and 12/12; WP-04 passed 50/50 and 17/17; WP-05 integration passed 56/56 unittests and 24/24 resource checks; distribution validation and `git diff --check` pass
- delegated evidence: WP-02 RED `python -m unittest tests.distribution.test_sync_skill_resources.SyncSkillResourcesTests.test_uses_parseable_extension_aware_generated_headers tests.harness.test_setup_agent_harness` failed because generated Python had an HTML header (`SyntaxError`) and the bootstrap helper was absent; WP-03 initial RED `python -m unittest tests.harness.test_design_contract` failed 8/8 because the contract engine, renderer, and Skills were absent; the SPEC-only small-contract RED failed with exit 2 while the engine still required GOAL/plans; the GOAL+plans multi-contract RED failed with `missing_document:SPEC.md`; final focused GREEN passed 8/8; full suite passed 40/42 with only the WP-06 catalog transition missing; resource drift check passed; standalone distribution validation reported only `unexpected public skill: 'design-goal'` and `unexpected public skill: 'explore-idea'`; `git diff --check` passed
- delegated evidence WP-04: initial RED `python -m unittest tests.harness.test_goal_execution` failed all 7 tests because `goal_runtime.py`, `execute-codex-goal`, and `diagnose` were absent; the resolved Contract-path RED failed with `contract_path_mismatch` when the Goal objective correctly named `GOAL.md`; final focused GREEN passed 8/8 against the generated installed runtime; harness feature suite passed 22/22; fast suite passed 48/50 with only the deferred WP-06 catalog declarations for `diagnose` and `execute-codex-goal` failing; resource drift check verified 17 generated targets; standalone distribution validation reported only those same two unexpected public Skills; `git diff --check` and Python compilation passed
- delegated evidence WP-04 completion audit: SPEC-only RED failed because preflight returned an empty `plan_order` and `start` returned `no_dependency_ready_plan`; the generated runtime now exposes implicit Plan `SPEC`, treats missing `runtime-state.json` as read-only logical `pending`, and atomically creates or replaces that adjacent ephemeral file only for `start`, `complete`, or `block`; contract content and canonical hash remain unchanged; focused GREEN passed 10/10, harness feature suite passed 30/30, full suite passed 58/58, resource drift check verified 24 generated targets, and `git diff --check` passed
- delegated evidence WP-05: initial RED `python -m unittest tests.harness.test_close_and_maintenance` failed all 5 tests because `close_goal.py` and `maintain_harness.py` were absent; final focused GREEN passed 5/5, covering High and tracked `.work/` close gates, Live/Eval `unverified`, escaped scriptless Markdown/HTML parity, conditional handoff plus monthly archive, and report-only instruction/retention/worktree findings; full suite passed 53/55 with only the deferred WP-06 catalog declarations for `close-goal` and `maintain-agent-harness` failing; resource drift check verified 24 generated targets; standalone distribution validation reported only those same two unexpected public Skills; `git diff --check` and Python compilation passed
- delegated evidence WP-05 completion audit: `test_close_supports_small_spec_only_contract` RED failed with `GOAL.md` `FileNotFoundError`; minimal contract selection now requires exactly one of `GOAL.md` or `SPEC.md`, preserves GOAL `## Objective`, and derives SPEC outcome from `## Problem`, `## User Value`, or the first readable section; focused GREEN passed 6/6, full suite passed 56/56, resource sync/check verified 24 generated targets, and `git diff --check` passed
- delegated evidence WP-06: initial focused RED failed 4/4 because `distribution/release-candidate.json`, `.github/workflows/validate-distribution.yml`, `scripts/run-v2-pilots.py`, and install/update smoke support were absent; final local GREEN passed 63/63 unittests, resource drift verified 24 generated targets, distribution validation passed, all three deterministic repo-local helper simulation pilots passed and archived Completion Review artifacts, and `git diff --check` passed
- external verification WP-06 first run: approved `skills@1.5.19` local-source install completed for all 18 public Skills in both Codex and Claude Code targets, created project `skills-lock.json` entries with `sourceType=local`, and list discovery saw the installed Skills; native `skills update -p -y` then exited successfully while reporting no project Skills or updates and left deliberately stale copies unchanged, because upstream update filters to GitHub-backed hash entries; the wrapper fix was pending at the end of that run
- delegated WP-06 update regression: fake native update exit-0/no-op RED failed on the first stale `finance-research` Codex entrypoint; GREEN now detects stale hashes, reports native local update as unsupported/no-op, reruns the exact local `skills add <resolvedRoot> --skill '*' -a codex -a claude-code --copy -y` refresh, and verifies all 18 Skills across both targets; the existing native-update-success case still passes without fallback; focused release tests passed 6/6, full suite passed 64/64, resource drift verified 24 generated targets, distribution validation passed, and `git diff --check` passed
- external verification WP-06 corrected rerun: approved `skills@1.5.19` smoke exited 0 after installing all 18 public Skills into both Codex and Claude Code targets, detecting the native local update no-op, rerunning the local-source add refresh, and restoring hashes for all 36 provider entrypoints; final evidence included `Local source refresh passed for 18 public skills across codex and claude-code.` and `Install and update smoke test passed for 18 public skills across codex and claude-code.`
- risks: remote GitHub-backed update remains unverified and is post-release scope; live GitHub release is not authorized
- next mode: run
- next stop condition: independent review of the complete WP-02 through WP-06 implementation
