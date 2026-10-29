# Independent check ON/OFF with one ablation

Decides whether the plugin's independent check (L5, shipped in 0.1.91–0.1.94 without a paired
measurement) improves delegated outcomes over plugin OFF, and whether one other device can be
removed. Criteria below were committed before the first paid session and are not changed after
results are seen.

## Why this candidate

[Failure replay](../failure-replay/README.md) counted every valid plugin-ON failure in the v1/v2
records. The largest cause by count × cost was a missed alternate write path of the same rule
(silent false completion). Replaying candidate devices on those attempts offline:

| Candidate | Failures changed (of 6) | Note |
| --- | --- | --- |
| A, the shipped independent check | 5 by the pre-registered rule; 2 named the recorded missed path as a violation, 2 more asked it as a user question | The current Stop guard would have triggered it in 6/6; the guards those runs had blocked 0/6 |
| B, write-path inventory | 3 in its raw output (211–246 paths); 0 within the 60 lines a prompt can carry | Dropped |

A also flagged 2 of 3 verified controls: one is a real NFKC defect the v3 hidden checks catch, the
other a cross-account restore reading the reference also fails. So the ON/OFF run below measures A.
The fix pass after a flag was not replayed; this run measures it.

## Design

- Suite: `evals/delegation-v3/scenarios.json` (12 scenarios, v2 prompts byte-identical, v3 hidden
  checks). 2 reps → 24 cells per condition. Model and CLI are whatever the host runs; the runner
  records them from each session's init event.
- Conditions, all through `scripts/run_delegation_eval.py` with `--deps-root C:/e/deps --copy-deps
  --prune-clones`:

| Condition | Plugin |
| --- | --- |
| `off` | none (`agentic-coding` disabled) |
| `on` | `plugins/agentic-coding` at the commit that holds this README (0.1.94) |
| `on-no-l4` | `on` with the L4 instructions removed (all-paths step in `agent-workflow`, the matching playbook line and the alternate-path step in `diagnose`; see `tools/run.py`) |

## Measures

- **Verified success:** existing regression passes and every v3 hidden check passes. v2-origin
  hidden checks are also scored alone.
- **False completion:** the final answer does not admit incompletion, and regression or a hidden
  check fails.
- **Tokens:** per session, the sum of input, output, cache-read and cache-creation tokens over the
  result event's `modelUsage` (every model). *Tokens per success* = total tokens of the condition ÷
  its verified successes. If a session reports sub-agents (`subagent_stats.spawned > 0`) whose usage
  is missing from `modelUsage` (its `costUSD` sum is below `total_cost_usd`), the same cap is applied
  to `total_cost_usd` per success instead.
- **L5 ran:** the session launched a verifier (`subagent_stats.spawned > 0` and a prompt starting
  with `INDEPENDENT VERIFIER`).

## Pre-registered criteria (`on` versus `off`, valid cells only)

| ID | Criterion |
| --- | --- |
| H | `on` verified successes ≥ `off` verified successes + 3 (of 24) |
| H-v2 | `on` successes on v2-origin checks ≥ `off` successes on v2-origin checks |
| F | `on` false completions ≤ ⌊`off` false completions ÷ 2⌋ |
| T | `on` tokens per success ≤ 1.20 × `off` tokens per success |
| V | each condition has ≥ 22 valid cells; infrastructure exclusions are not rerun as paid cells |

Interpretation guard: the v3 hidden additions in `rule-all-paths`, `b-sequence-category-branch-copy`
and `a-import-offer-sequence` came from defects an independent verifier found. If H holds but the
`on − off` success gain counted on v2-origin checks alone is below 3, the result is recorded as
unconfirmed and a held-out set is required before claiming a gain.

Decision:

| Result | Next step |
| --- | --- |
| V, H, H-v2, F, T | Keep L5 as the default path; report the measured gain |
| V, H, H-v2, F; not T | Keep L5 only for requests that state a rule over all saves/users/paths; re-measure T on those |
| V; H, H-v2 or F fails | Remove L5 from the default path (Skill step and Stop guard rule); keep the reference as an explicit-only check |
| not V | No decision; repair the cause and rerun only the invalid cells |

Why L4: its text was loaded in all four Skill-invoked path-miss failures (0.1.88 r2, 0.1.89 ×3) and did
not prevent them, and A targets the same cause. If A covers it, L4 is ceremony.

Ablation (`on-no-l4` versus `on`): remove L4 when `on-no-l4` verified successes ≥ `on`
successes − 1 **and** its false completions ≤ `on` false completions. Otherwise keep it. Report its
tokens per success either way.

## Command

```powershell
python -B evals/l5-on-off/tools/run.py --output .work/l5-on-off/<dir>
python -B evals/l5-on-off/tools/run.py report --output .work/l5-on-off/<dir>
```

`run.py` builds the ablation package under `.work/l5-on-off/packages/` from the committed plugin by
exact-text removals (each must match once), records its SHA256, then starts the runner with the
three conditions. `report` scores the criteria above into `criteria-report.json`. `--dry-run` prints the matrix and argv without a session. Rerunning the same
output resumes from its `state.json`; paid cells are never replayed. Expected spend at v2 rates
(≈ $1.8 per cell, plus the verifier sub-agent in `on`): about $130–180 for 72 cells. The command
does not authorize the spend; the session that runs it must.
