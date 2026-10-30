# Failure replay: candidate devices on recorded plugin-ON failures

Replays candidate devices against the plugin-ON attempts that actually failed, without running a
coding agent again. It answers "of N recorded failures, how many would this device have changed?"
before any paid ON/OFF run. Counting rules below were committed before the first verifier session.

## Inputs

[attempts.json](attempts.json) lists every valid plugin-ON false completion whose cause is a missed
alternate write path of the same rule (6), plus 3 verified successes of the same scenarios and plugin
generations as controls. Sources: `%TEMP%/claude/delegation-eval-run3`, `-run4-rep3`, `-run5-v087`
(v1, 0.1.87/0.1.88) and `.work/delegation-eval/v2-0189-*` (v2, 0.1.89). The runs kept transcripts but
not diffs, so `tools/reconstruct.py` re-runs each attempt's file-changing tool calls on a fresh clone at
the pinned ref (`npm`/`npx` shimmed to no-ops) and saves the result in `attempts/<id>.patch`. Those
patches are the durable input; the transcripts expire.

## Counting rules

- **Faithful:** the rebuilt patch reproduces the recorded existing-regression result and v2 hidden
  result. Unfaithful attempts are reported and excluded.
- **Stop guard:** the guard of the build the attempt ran (`0.1.87` `9f89615`, `0.1.88` `c9b6a56`,
  `0.1.89` `987dba7`) and the current guard are replayed on the transcript, rebased to the rebuilt
  workspace. `blocks` means it returned `decision: block`.
- **Candidate B, write-path inventory (no model):** `evals/path-check-offline/tools/inventory.py` on
  the rebuilt workspace. *Changed* when a listed candidate path reaches the attempt's pre-registered
  `missed_markers` (`duplicateProduct` for the copy path, `src/worker/backup.ts` for restore). The
  number of listed paths is reported as noise.
- **Candidate A, the shipped independent check (L5):** the verifier template in
  `authoring/references/independent-check.md`, filled with the verbatim request and the base commit,
  in a fresh Claude Code headless session with `agentic-coding` disabled. Product edits are undone,
  its new test files kept. *Changed* when the verdict is `incomplete` **and** at least one test it
  wrote fails on the attempt and passes on the v3 reference (`retest`).
- **Controls:** a control is *harmed* by A when the verdict is `incomplete`; reported together with
  whether its failing tests also fail on the reference. B's noise on controls is its path count.
- A candidate with M = 0 on the failures is dropped.

## Limits

- The fix pass is not replayed. *Changed* means a silent false completion would have been surfaced
  with a failing test; whether the implementer then fixes it is measured by the next ON/OFF run.
- 6 failures, all Labeler; 5 are `rule-all-paths`. The inventory was tuned on `rule-all-paths`, and
  the v3 hidden checks came from defects the same verifier family found.
- Rebuilt patches re-run Python/sed edit scripts; fidelity is established by the faithful rule only.

## Commands

```powershell
python -B evals/failure-replay/tools/reconstruct.py
python -B evals/failure-replay/tools/replay.py precheck --output .work/failure-replay/<dir>
python -B evals/failure-replay/tools/replay.py verify --output .work/failure-replay/<dir> --max-cost 30
python -B evals/failure-replay/tools/replay.py retest --output .work/failure-replay/<dir>
python -B evals/failure-replay/tools/replay.py report --output .work/failure-replay/<dir>
```

`verify` skips attempts that are not faithful and never reruns a cell that already has a session.

## Result (2026-10-30)

All 9 rebuilt attempts were faithful. Of the 6 failures: the Stop guard each attempt ran blocked 0, the
current guard would block 6; A changed 5 by the rule (2 named the recorded missed path as a violation,
2 asked it as a question, 3 of the 5 flags were the NFKC defect); B hit 3 in raw output of 211–246
paths, 0 within 60 rendered lines (a post-hoc measure), so B is dropped. Verifier cost $8.02.
`named`/`asked` and the 60-line measure were added after the first two verdicts and do not change the
pre-registered counts. Record: [research](../../docs/research/failure-replay-20261030.md).
