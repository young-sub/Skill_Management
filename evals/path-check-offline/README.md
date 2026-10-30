# Independent path check: offline falsification

This suite decides whether an independent verifier, given only the request and an
implementation diff, catches incomplete implementations that pass the existing
regression suite. It reuses the frozen `evals/delegation-v2` scenarios. No coding
agent runs; only the verifier does. Criteria below were committed before any
verifier session ran.

## Why

In delegation v2 every failed run (OFF 2/24, plugin 3/24) was a silent false
completion: existing regression passed, a hidden acceptance check failed, and the
final report claimed success. The diagnosis is that the implementer and its own
checks share the same list of paths to consider. A device can differ from plugin OFF
only by supplying something the implementing session cannot: computed facts or an
independent judgement. See [design](../../docs/research/agent-coding-system-direction.md).

## Items

Each of the 12 v2 scenarios yields one `reference` item (complete; must be accepted)
and, where a natural incomplete implementation exists, one `partial` item (must be
rejected). Item recipes live in [items.json](items.json):

| Recipe | Meaning |
| --- | --- |
| `patch` | The authored first-obvious partial patch, applied to the base (or to the reference when `on` is `reference`) |
| `probe` | The reference plus one frozen scenario probe documented as a regression-passing, hidden-failing omission |

`b-contract-catalog-default-page` has no partial item: its reference is one line, and its
probes yield an empty diff or an artificial bound rather than a natural omission. The
`a-import-offer-sequence` partial patch is corrupt at line 119, so its natural probe is used.

Ground truth is observed, not assumed. After the verifier finishes, the runner restores
any product file the verifier changed, then runs the scenario's regression and hidden
commands in that same workspace. A `reference` item is valid only when both pass; a
`partial` item only when regression passes and hidden fails. Invalid items are reported
and excluded from scoring. A free `precheck` pass validates every item before any
verifier runs.

## Conditions

| Condition | Verifier | Input |
| --- | --- | --- |
| `inventory` | none (`tools/inventory.py`, no model) | Diff and repository; lists write paths whose call chain references nothing the diff changed |
| `claude` | Claude Code headless, default model, `agentic-coding` disabled, fresh session | Request(s), inventory candidates, workspace with the uncommitted diff |
| `codex` | `codex exec`, default model, `workspace-write` sandbox, ephemeral, plugins and memories disabled (see amendments) | Same as `claude` |

The verifier prompt is [verifier-prompt.md](verifier-prompt.md). It may add test files and
run existing commands; it may not change product code or install dependencies. It must end
with a one-line JSON verdict. `incomplete` requires a failing test the verifier wrote.

## Pre-registered criteria

Per verifier, over valid items:

- **Detection**: partial items judged `incomplete` ≥ 75% (rounded up) of valid partials.
- **False alarm**: reference items judged `incomplete` ≤ 1.
- A missing or unparsable verdict counts as `complete` (not detected; no false alarm).

The device passes when at least one verifier meets both. If neither does, the
recommendation is to shrink the plugin rather than build this device, and to stop paid
evaluation of it. Secondary, descriptive only: cost and wall time per item, whether a
detection names the actually missing path (manual reading), inventory recall on partial
items, and same-model versus cross-model difference.

## Isolation

- Workspaces are `C:/e/w/<8-hex>/r` outside this repository, cloned from the pinned
  ref; dependencies are private copies of `%TEMP%/claude/eval-deps/<project>`.
- Prompts and paths contain no suite vocabulary. Hidden files are installed only after
  the verifier ends. Transcripts are scanned for suite paths and hidden file names; a
  hit marks the item contaminated and it is reported separately.
- The authored partial patches came from Codex; the Codex verifier never sees them,
  but a shared-author bias is possible and is reported as a limit.

## Commands

```powershell
python -B evals/path-check-offline/tools/run.py precheck --output .work/path-check-offline/<dir>
python -B evals/path-check-offline/tools/run.py run --verifier claude --verifier codex --jobs 2 --output .work/path-check-offline/<dir>
python -B evals/path-check-offline/tools/run.py report --output .work/path-check-offline/<dir>
```

`run` refuses to start without a passing `precheck` in the same output and stops
launching Claude cells once recorded Claude cost exceeds `--max-cost` (default $40).
`replay --verifier <v>` rebuilds every reference item that verifier judged `incomplete` and
runs only the verifier's saved tests there (no hidden files), to tell real defects from
verifier errors.

## Amendments after the first run (criteria unchanged)

- Codex 0.160 `exec` ignored per-plugin `enabled=false` overrides, and its memories held this
  repository's suite vocabulary: every first-run Codex cell read both. The Codex verifier now
  runs with `--disable plugins --disable memories`, so ponytail is off too. `agentic-coding/`
  and `memories/` are leak markers.
- A session that exits non-zero without a verdict (for example HTTP 429) is an excluded
  infrastructure error, not a `complete` verdict.

Result: neither verifier met the false-alarm criterion. See
[the record](../../docs/research/independent-path-check-offline.md).
