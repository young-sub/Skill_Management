# Delegated coding evaluation v1

Eight Korean product requests for fresh, pinned Labeler and yeondoo-link clones. Judgment combines hidden acceptance tests, existing regressions, and probes against tests left by the agent. Reference patches are authoring controls, not candidate input.

Do not edit prompts after the first paid run. Retain the suite hashes, runner, plugin, model settings, source refs, dependency versions, and results. Never copy hidden files into a candidate clone until every session and probe has ended. Keep `hidden/`, `reference/`, validation logs, and solutions out of candidate prompts/workspaces. Never reuse authoring clones for paid sessions.

From the Skill_Management root, validate configuration without a paid session:

```powershell
python -B scripts/run_delegation_eval.py --scenarios evals/delegation-v1/scenarios.json --output C:/Users/YS/AppData/Local/Temp/claude/eval-authoring/dry-run-unused --condition off=off --condition plugin=plugin:plugins/agentic-coding --reps 1 --jobs 1 --timeout 300 --dry-run
```

For an authorized paid comparison, use a new output directory and remove `--dry-run`. Budgets are 1,800 seconds per single request and 2,700 seconds per sequence session; the runner applies the latter to **each** session. `--timeout 300` bounds judgment commands. The runner commits configured synthetic faults; authoring made no commits.

See `VALIDATION.md` for RED/GREEN/mutation evidence, runtimes, and limits. Authoring controls do not establish agent success or measured completion times. Hidden-free reference probes may pass; future candidate tests should catch those faults. Exact-text probes can miss alternative correct implementations, so inspect probe errors separately.

This sandbox rejects the runner's clone hardlinks. Authoring used `git clone --local --no-hardlinks` and the required dependency junctions. Use an account where the existing runner can clone. Read-only Vite host adaptations and scoped probe fallbacks are documented in `VALIDATION.md`; the runner, global settings, and source checkouts were not changed.
