# Public Skill Inventory

The public catalog contains 22 Skills. `swarm` owns parallel implementation,
resume reconciliation and integrated evidence; `multi-agent-review` owns independent challenge. `architect` owns software design decisions;
`design-goal` owns work contracts. The mapped change-impact reference is shared by
architecture, workflow, verification and review, without requiring a contract or
design document for small edits. Human corrections and successful procedure
reuse extend `agent-workflow` and `diagnose`, with a mapped shared reference and
procedure template. No separate `reflect` or authoring Skill is distributed;
independent new procedures use an available host authoring tool only when needed.

Invocation policy (0.1.96): only `agent-workflow` is model-invocable. The other 21
declare `disable-model-invocation: true` (Claude Code) and
`policy.allow_implicit_invocation: false` in `agents/openai.yaml` (Codex), so their
descriptions stay out of the session context. Users invoke them directly, and
`agent-workflow` names each one in its capability table and reads the sibling
directory's `SKILL.md` when the need arises. That reference is a soft dependency by
name, not a path link: when the sibling is not installed, `agent-workflow` continues
alone, so each Skill remains independently installable.
`probe_check.py` ships beside the capture tool in `agent-workflow`,
`setup-project-verification`, `maintain-project-verification` and `diagnose`, and at
the plugin root.

The six Skills that bundle the verification viewer also bundle its capture tool
and evidence reader. They execute without a plugin installation, a project copy of
the capture script, or `--run-check`. The override remains available for explicit
customization. Hook delivery is a plugin capability, not a standalone Skill promise.
Harness cohort installation requirements below remain distinct from this runtime
self-containment guarantee.

Public Harness Skills are `setup-agent-harness`, `explore-idea`, `design-goal`, `execute-codex-goal`, `diagnose`, `close-goal`, and `maintain-agent-harness`. Setup, Design, Execute, Close, Maintain, and Diagnose are installed as one manifest-bound cohort. Missing, extra, or hash-drifted resources fail before mutation.

The independently self-contained public Skills are `swarm`, `architect`, `agent-workflow`, `setup-project-verification`, `maintain-project-verification`, `finance-research`, `fixing-accessibility`, `hwp-form-fill`, `impeccable`, `multi-agent-review`, `prototype`, `recall`, `teach`, `vercel-react-best-practices`, and `zoom-out`. The three workflow/verification responsibilities and their shared references are canonical under `authoring/` and generated through the resource map. Their use of other capabilities is conditional; they do not require a Harness cohort in every consumer project. Impeccable retains its independent entrypoint source and receives the mapped canonical repair/reuse reference for shared UI-standard requests. `authoring/public-resource-manifest.json` and the copy bundled in `maintain-agent-harness` define distribution integrity. `write-a-skill` is intentionally absent from this repository distribution; existing user installations are outside this removal.
