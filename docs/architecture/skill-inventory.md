# Public Skill Inventory

The public catalog contains 21 Skills. `architect` owns software design decisions;
`design-goal` owns work contracts. The mapped change-impact reference is shared by
architecture, workflow, verification and review, without requiring a contract or
design document for small edits. Human corrections and successful procedure
reuse extend `agent-workflow` and `diagnose`, with a mapped shared reference and
procedure template. No separate `reflect` or authoring Skill is distributed;
independent new procedures use an available host authoring tool only when needed.

Public Harness Skills are `setup-agent-harness`, `explore-idea`, `design-goal`, `execute-codex-goal`, `diagnose`, `close-goal`, and `maintain-agent-harness`. Setup, Design, Execute, Close, Maintain, and Diagnose are installed as one manifest-bound cohort. Missing, extra, or hash-drifted resources fail before mutation.

The independently self-contained public Skills are `architect`, `agent-workflow`, `setup-project-verification`, `maintain-project-verification`, `finance-research`, `fixing-accessibility`, `hwp-form-fill`, `impeccable`, `multi-agent-review`, `prototype`, `recall`, `teach`, `vercel-react-best-practices`, and `zoom-out`. The three workflow/verification responsibilities and their shared references are canonical under `authoring/` and generated through the resource map. Their use of other capabilities is conditional; they do not require a Harness cohort in every consumer project. Impeccable retains its independent entrypoint source and receives the mapped canonical repair/reuse reference for shared UI-standard requests. `authoring/public-resource-manifest.json` and the copy bundled in `maintain-agent-harness` define distribution integrity. `write-a-skill` is intentionally absent from this repository distribution; existing user installations are outside this removal.
