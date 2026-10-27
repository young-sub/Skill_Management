# Paired review loop

Decides whether an independent verifier, followed by a fix pass, improves delegated
outcomes beyond what the same model achieves when simply asked to re-verify its own work.
Only if it does is the device worth building into the plugin. Criteria below are committed
before the first paid session.

## Why

The offline falsification ([record](../../docs/research/independent-path-check-offline.md))
showed a fresh verifier finds the missing path in every partial implementation, and that
some of its "false alarms" on references were real defects the v2 hidden checks miss. It
did not show that the implementer then fixes them, or that independence matters more than
spending the same model's effort on a second look. Plugin ON versus OFF cannot separate
those, so this comparison uses no plugin at all.

## Design

Suite: `evals/delegation-v3/scenarios.json` (v2 prompts byte-identical; three scenarios gain
one hidden check for a defect the v2 checks missed). 12 scenarios × 2 reps = 24 cells.

Each cell runs **one** plugin-OFF implementation (same as v2), snapshots the working tree,
then three branches from that snapshot in the same workspace:

| Branch | Follow-up after the implementation |
| --- | --- |
| `off` | none |
| `self` | resume the implementer (`--resume <id> --fork-session`) with [self.md](prompts/self.md): re-verify on every path with new entry-point tests, fix violations |
| `indep` | a fresh session with [verifier.md](prompts/verifier.md) (request + diff only) writes failing tests; if it reports `incomplete`, resume the implementer with [fix.md](prompts/fix.md) and the report |

`self.md` and `verifier.md` carry the same verification rules, so `self` versus `indep`
isolates independence. Every session disables `agentic-coding`. The verifier's product edits
are undone; its new test files stay for the fix pass. Hidden files exist only while judging;
ignored files judging creates are removed before the next branch. If the implementer left
Claude project memory, it is parked during the verifier session. Each branch keeps
`final.diff` and its tree, so later hidden checks can rescore it.

## Pre-registered criteria

Over pairs where all three branches are valid (no session or judging error):

- **D1, independence:** `self → indep` gained minus lost verified successes ≥ 3.
- **D2, no harm:** `off → indep` lost ≤ 1.
- **Interpretation guard:** gains are split into the three augmented scenarios
  (`rule-all-paths`, `b-sequence-category-branch-copy`, `a-import-offer-sequence`) and the
  other nine. Those three hidden checks were derived from defects this verifier prompt found,
  so if every `self → indep` gain falls in them, the result counts as unconfirmed and a
  held-out set is required before any plugin work.

Decision:

| Result | Next step |
| --- | --- |
| D1 and D2, gains not confined | Build the device in the plugin; then compare plugin ON against `off` and `indep` |
| D1 and D2, gains confined | Author held-out checks first; no plugin work |
| D1 fails, `off → self` gained − lost ≥ 3 | Re-verification helps without independence; at most a one-line instruction, no device |
| otherwise | Shrink the plugin; stop paid evaluation of review devices |

Reported, not decided on: v2-only success, false completion, admitted incomplete, verifier
verdicts, cost and extra cost per gained success, wall time.

## Commands

```powershell
python -B evals/review-loop/tools/run.py --scenarios evals/delegation-v3/scenarios.json --output .work/review-loop/<dir> --reps 2 --jobs 2 --deps-root C:/e/deps --dry-run
python -B evals/review-loop/tools/run.py --scenarios evals/delegation-v3/scenarios.json --output .work/review-loop/<dir> --reps 2 --jobs 2 --deps-root C:/e/deps --max-cost 120
```

Rerunning the same output skips cells with a `cell.json`; paid cells are never replayed.
Launching stops once recorded cost exceeds `--max-cost` (default $120).
`tests.distribution.test_review_loop` checks the runner with a fake executable.

## Status

Not run. The user judged independent verification better in most cases and had it built
into the plugin without this comparison (2026-10-27, 0.1.91). The runner and criteria stay
for a later measurement.
