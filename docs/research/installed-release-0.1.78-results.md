# Installed release 0.1.78 experiments

Date: 2026-10-18. Published baseline: `5ac76c6d5223aea824b712a6d24c0864b49175c3`
on `main`. Acceptance criteria were frozen before product execution. This is a
bounded installation and execution result, not completion of
`20261018-plugin-readiness` or a model benchmark.

## Actual installation

All installations used new project/home directories under the ignored
`.work/installed-trial-20261018/`. No installed-resource repair or replacement
from the development checkout was performed.

- `npx --yes skills@latest add git@github.com:young-sub/Skill_Management.git --skill '*' -a codex -a claude-code --copy -y`
  installed 22 Skills for each host. The resolved installer was Skills 1.7.2.
  All source resources matched (Git newline normalization allowed), with no
  missing, changed or extra files.
- The same remote command with `--skill agent-workflow -a codex` installed only
  that Skill in a separate project; its bundled capture was sufficient.
- Codex CLI 0.160.0 and Claude Code 2.1.186 registered the SSH Git marketplace
  and installed `agentic-coding@agentic-coding` into isolated native homes.
  Both caches contained version 0.1.78, 22 Skills, and 283/283 inventory files
  with exact hashes. Host-generated Python bytecode was retained separately.

## Observed behavior

| Experiment | Executed result |
| --- | --- |
| Browser -> API -> Domain -> SQLite -> restart -> fresh read | Five installed surfaces: both npx hosts, both native plugins, and the single Skill. Normal and repaired runs each passed 16/16 assertions; no skips/errors. Screenshots, trace hashes and owned service cleanup checked. |
| Deliberate frontend quantity payload defect | All five surfaces reported ISSUES with five failed assertions (11/16 passed), rather than false PASS. Restoring the original project source produced the independent repaired runs above. |
| Lookup and completed execution resume | Two calls per browser scenario, 30 total: zero test commands; evidence bytes preserved, including failed results. |
| Installed Harness lifecycle | Seven CLI cases per full installation, 28 total: passed. Includes setup/cleanup, execution and parallel worktree lifecycle. |
| Interruption and replay controls | Four cases per full installation, 16 total: killed controller, retained failure/pending work, unknown launched execution, and submitted PASS hiding a bad fact. All passed. |
| Task/context follow-up | Four installed workflows: prepare, execute without a capture override, semantic review, lookup, resume, audit, completed execution reuse, and stale input detection. Each executed its product command once. Plugin hook output was also invoked directly from its actual installed hook path. |
| Optional global instructions installer | Fresh SSH clone; isolated Codex/Claude homes. Seven CLI executions and two concurrency probes: preview, byte-preserving backup and unmanaged text, repeat apply, managed block replacement, override refusal, and concurrent-edit refusal passed. Eleven evidence rows include two supplemental observations, not eleven executions. |

The browser experiments used the repository's existing connected-product fixture
and its real Chromium runner, with the **installed** verification runtime. They
did not ask a model to discover a Skill, implement a new product, or judge success.
The interruption tests inject existing failure seams and point both viewer and
capture at the installed resources. Normal browser and task executions supplied
no `--run-check` or source-checkout runtime fallback.

## Retained failures and limits

Native marketplace SSH initially failed inside the restricted sandbox; those
attempts installed nothing and remain recorded. Authorized network retries
succeeded. The first task/context recorder could not serialize a subprocess
object, leaving its verdict unknown. The second attempt on all four surfaces
failed because the source-oriented test assumed the hook lived beside the
workflow script. The experiment was corrected to use the plugin's actual
`hooks/workflow_context.py`; standalone Skills have no plugin hook, so that
assertion is excluded there. Both earlier attempts remain, not relabeled PASS.

No product defect was reproduced; version 0.1.78 was therefore retained without
an artificial runtime patch or version bump. Real user homes/global settings were
not modified. Native model discovery, automatic host hook delivery, paid model/API
evaluation, all-Skill semantic quality, other operating systems, and general
performance/cost improvement remain unverified. Comparative time, usage and cost
are unknown. Source checkout regression checks are not native model acceptance.

## Evidence and ownership

Raw local records are retained under `.work/installed-trial-20261018/` according
to repository retention policy, rather than published with host-local paths:

- `acceptance.json`, `skills-inventory.json`, `skills-cli-version.json`.
- `hosts/evidence/`: failed/retried native commands, inventory hashes and installed
  CLI results; `npx-harness.json` covers the two standalone full installations.
- `products/<surface>/commands.jsonl`, `summary.json`, and each fixture's `.work/`:
  actual argv/exit/output, native JSON, browser artifacts, lookup/replay evidence.
- `<surface>-resume.json` and `<surface>-context-attempt3.json`; prior context
  attempts and their recorder scripts remain alongside them.
- `global/evidence/observations.jsonl`: actual clone, previews, backups,
  refusal/concurrency observations and isolated paths.

Features: `skill-install`, `plugin-package`, `verification-results`,
`workflow-obligations`, `work-preservation`. This task changes documentation only;
no executable logic changed. Existing installed experiments supply the behavior
evidence; documentation links, resource drift, distribution and diff checks guard
the delivered documentation.
