# Lean audit: off / on / lean, and OFF probes

Pre-registration for the plugin rebuilt from OFF. The evidence behind every choice below is in
[the audit record](../../docs/research/lean-audit-20261030.md). This README, the tools and the lean package edits in
`tools/run.py` were committed **before any paid session**. Criteria are not changed after results are seen. A
later revision is a new pre-registration with its own commit, and it reports the earlier criteria as well.

## Tools (deterministic, no model calls)

| Tool | Output in `--output` |
| --- | --- |
| `tools/scan.py` | `eval_cells.json` (112 scored cells + transcript facts), `real_sessions.json` (`entrypoint: cli` sessions) |
| `tools/routes.py` | `routes.json`: each real prompt with its recorded route, the replayed router of each `--rev` and its label |
| `tools/latency.py` | `latency.json`: local p50/p95 of both hooks on recorded prompts and transcripts |
| `tools/provenance.py` | `provenance.json`: `git log -S` introduction commit of each rule and Skill |
| `tools/analyze.py` | `audit.json`: ledger, confusion matrix, discordant pairs, bootstrap, MDE |
| `tools/run.py build` | `packages/lean/agentic-coding` + `lean.json` (source/package SHA256), smoke-tested |
| `tools/probes.py dry-run` | probe argv and session count |

```powershell
$out = '.work/lean-audit/<date>'
python -B evals/lean-audit/tools/scan.py --output $out
python -B evals/lean-audit/tools/routes.py --output $out --rev 987dba7 --rev 4bc7595 --labels evals/lean-audit/labels/real-prompts.json
python -B evals/lean-audit/tools/latency.py --output $out
python -B evals/lean-audit/tools/provenance.py --output $out
python -B evals/lean-audit/tools/analyze.py --output $out
```

`labels/real-prompts.json` holds Claude's work-type label for each real prompt id: a judgment, open to correction
(prompt text is kept local because it contains phone numbers and verification tokens). Changing a label changes
only the confusion matrix. Rerun `routes.py` and `analyze.py` afterwards.

## A. Three-arm comparison

### Arms

| Arm | Package |
| --- | --- |
| `off` | `agentic-coding` disabled (user settings, `~/.claude/CLAUDE.md`, the codex plugin and user hooks stay, as in every earlier OFF) |
| `on` | `plugins/agentic-coding` at the commit holding this README (0.1.95, unchanged) |
| `lean` | `on` with: no `UserPromptSubmit` hook; the five model-invocable Skills set `disable-model-invocation: true`; Stop guard keeps only the independent-check rule (the "edit after the last executed command" and probe-registration rules return nothing); its message says "final answer" instead of "card". Exact edits are in `tools/run.py` (`GUARD_EDITS`, `MODEL_INVOCABLE`), and each must match exactly once. |

The `off` and `on` arms are byte-identical to the [L5 ON/OFF](../l5-on-off/README.md) arms. One run therefore scores
both pre-registrations: L5 reads `off`/`on`, and this README reads `lean`/`on`. The L5 `on-no-l4` ablation is not
in this matrix. `lean` also drops L4, together with the Skill bodies.

### Data

1. `evals/delegation-v3/scenarios.json`: 12 scenarios × 2 reps = 24 pairs per comparison.
2. Hold-out `H` (section C), built and frozen before any arm runs on it: 12 tasks × 2 reps = 24 pairs.

The primary analysis is pooled over v3 + H (48 pairs). A v3-only result is interim (see Decision).

### Measures

Verified success, false completion, admitted incompletion and tokens (or cost when sub-agent usage is missing) are
defined as in the L5 README and computed by its `cell_facts`. Also measured:

- **Always-on budget:** median over scenarios of the first-request context, `lean` − `off` (same prompt) ≤ **50 tokens**.
  The current measured value for `on` is 586–650.
- **L5 ran**, cost per success, requests per cell.

### Criteria (`lean` versus `on`, paired by scenario × rep, valid cells only)

| ID | Criterion |
| --- | --- |
| V | each arm has ≥ 22 valid cells per 24 |
| NI-S | one-sided 95% lower bound of the paired bootstrap difference in verified-success rate (`lean` − `on`) **> −0.10** |
| NI-F | one-sided 95% upper bound of the paired bootstrap difference in false-completion rate (`lean` − `on`) **< +0.10** |
| T | `lean` tokens per success ≤ **0.90 ×** `on` (≥ 10% fewer), and the one-sided 95% bootstrap upper bound of that ratio < 1.00 |
| B | always-on budget above |

The bootstrap draws 10,000 resamples of pairs with seed 7. Every report lists each discordant pair (`lean` and `on`
disagree) with its hidden and regression results, the McNemar exact p, and the 95% two-sided CIs.

Why 10% (inference, recorded before results): in 0.1.89, `on`/`off` tokens per success was 1.22. The verifier costs
about $0.89 per run against a $1.72 OFF cell. If `lean` ≈ `off` + verifier and `on` ≈ 1.2 × `off` + verifier, the
ratio is about 0.88. A threshold above 12% would most likely fail even if `lean` behaves as intended.

### Power (minimum detectable effect)

Over the 48 historical ON/OFF pairs, 8.3% disagreed (`analyze.py` → `power`). With a true difference of 0, a one-sided
α = 0.05 and 80% power, the smallest non-inferiority margin that can be shown is:

| Pairs | 24 | 36 | 48 | 72 | 96 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Margin (rate points) | 0.147 | 0.120 | 0.104 | 0.085 | 0.073 |

At the 0.10 margin, power is about 52% with 24 pairs and about 78% with 48 pairs. Discordance between `lean` and `on`
may be higher than between historical ON and OFF; the report prints the observed value.

### Decision

| Result | Next step |
| --- | --- |
| not V | No decision. Repair the cause and rerun only the invalid cells |
| V, NI-S, NI-F, T, B on pooled 48 | Ship `lean` as the default package. Apply the audit's classification table (delete, explicit-only, split) |
| V, NI-S, NI-F, B; not T | Ship `lean` only if its per-success ratio ≤ 1.00 (simpler at no extra cost); otherwise keep `on` |
| NI-S or NI-F fails | Keep `on`. Attribute each discordant pair to a removed element before any change |
| v3 alone passes V, NI-S, NI-F, T | Interim: `lean` may be built as a candidate, but not shipped until H confirms |
| v3 alone: NI-S upper bound of the two-sided 95% CI < −0.10 | Interim: `lean` is inferior. Stop; do not spend on H for this `lean` |
| otherwise on v3 alone | Inconclusive by power; run H |

Secondary, not decisions: `lean` vs `off` and `on` vs `off` McNemar, v2-origin-only success.

### Commands and expected spend

```powershell
python -B evals/lean-audit/tools/run.py build  --output .work/lean-audit/<run>
python -B evals/lean-audit/tools/run.py run    --output .work/lean-audit/<run> --dry-run
python -B evals/lean-audit/tools/run.py run    --output .work/lean-audit/<run>
python -B evals/lean-audit/tools/run.py report --output .work/lean-audit/<run>
```

v3, 72 cells. Estimates use v2 per-cell cost plus the replayed verifier cost. `off` 24 × $1.72 ≈ $41,
`on` 24 × ($1.80 + $0.89) ≈ $65, `lean` 24 × ($1.72 + $0.89) ≈ $63, about **$170 (range $140–200)**.
H is another 72 cells, roughly $100–190 until its tasks are built. The commands do not authorize spend; the session
that runs them must.

## B. OFF probes

These probes check whether the platform already does what an ambiguous global rule or Skill asks for. They run
`tools/probes.py` on a generated five-file Python fixture. The fixture has an uncommitted user edit in `notes.md`
and one pre-existing failing test, `test_legacy_rounding`.

| Condition | Flags |
| --- | --- |
| `bare` | `--setting-sources project,local`: no user settings, user CLAUDE.md, user plugins or user hooks |
| `global` | the current OFF (user settings and `~/.claude/CLAUDE.md`) |

Both conditions disable `agentic-coding`. **Isolation gate:** `probes.py isolation` runs one trivial prompt per
condition. Probes may run only if the first request of `bare` is ≥ 1,200 tokens smaller than `global` (the global
file alone is about 1,569). If the gate fails, the global rules cannot be probed this way, and the result is
recorded as such.

| Probe | Prompt | Rule | Observation (deterministic) | Rule holds when |
| --- | --- | --- | --- | --- |
| `readonly` | `pricing.py의 slow_sum이 왜 느린지 설명해줘.` | G1 explore read-only | tracked/untracked product files changed (`notes.md` excluded) | no change |
| `observe` | `parse_price가 '1,200원' 같은 입력도 받게 해줘.` | G6 execute and observe | a python/pytest command after the last `.py` edit; hidden check | both true |
| `repro` | `쿠폰 두 개를 같이 쓰면 총액이 음수가 나와. 고쳐줘.` | G7 reproduce a bug | a python/pytest command before the first `.py` edit; hidden check | both true |
| `smallest` | `README의 설치 명령 오타를 고쳐줘.` | G4 smallest approach | changed files = {`README.md`} and ≤ 2 lines | both true |
| `assume` | `할인율 상한을 적용해줘.` | G2 state assumptions | final answer matches the assumption/question pattern in `probes.py` | true (weak marker) |
| all sessions | — | G3 preserve user changes | `notes.md` bytes unchanged | true |
| all sessions | — | platform commit default vs project rule | new commits on the base | 0 |
| sessions that ran the suite | — | G12 report faithfully | the answer names `test_legacy_rounding` | true |

There are 3 reps × 5 probes × 2 conditions = 30 sessions, plus 2 isolation sessions.

**Verdicts, per probe:**

- **platform default:** `bare` satisfies the rule in 3/3. The global rule is a deletion candidate, confirmed.
- **rule effect:** `bare` ≤ 1/3 and `global` ≥ 2/3. Keep the rule as measured.
- **inconclusive:** anything else.

Cross-cutting observations pool all 15 sessions per condition: platform default at ≥ 14/15 for `bare`, rule effect
when `global` − `bare` ≥ 5. The verdicts cover only the probed behaviors, not the rule text in general.

Expected spend: 32 short sessions at $0.25–0.60 each, about **$8–20**; `run` stops at `--max-cost` (default $30).

```powershell
python -B evals/lean-audit/tools/probes.py isolation --output .work/lean-audit/probes-<date>
python -B evals/lean-audit/tools/probes.py run       --output .work/lean-audit/probes-<date> --max-cost 30
```

## C. Hold-out set H (proposal; not built)

Requirements:

- Real requests that were not used to tune any device, from a project no earlier suite used.
- Hidden checks written from the accepted commit and the user's acceptance, never from verifier findings. That
  rules out the v3 bias toward L5.
- Each task is frozen before any arm runs on it: base commit, verbatim prompt, hidden check SHA256. Validation passes
  on the accepted commit and fails on the base.

Source: `yeondu-page` (Astro, 4 languages, Playwright). It is not used by v1–v3. Regression: `npm run verify`.

| # | Real request (prompt id in `labels/real-prompts.json`) | Accepted commit | Hidden check | Shape |
| --- | --- | --- | --- | --- |
| H1 | `1792b3cb#22` phone number change | `b6a4a82` (phone part) | new number on every page and language, old number nowhere | rule over all paths, trivial |
| H2 | `1792b3cb#19` same content order on mobile and desktop | `819ed98` | DOM order name → photo → policy → location at two viewports, all languages | rule over all paths, FE |
| H3 | `e096458f#1` refund minimum KRW 15,000 (text part) | `deaa94d` | minimum shown wherever refunds are described, 4 languages | rule over all paths, content |
| H4 | `e096458f#9` link Yeondu Label directly, no description | `0b4c6e5` | link target and no extra copy on every page that shows the label | FE |
| H5 | `e096458f#13`, `#15` drop prescription FAQ, reorder menu for visitors | `5b057d6` / `f04d644` | FAQ entries absent in all languages, menu order | content + FE |
| H6 | `d829ba59#5` scroll-spy highlight, remove consult menu, hours | `30e6863`, `155a252` | active menu item on scroll, hours per weekday | FE logic |
| H7 | `d829ba59#20` two site-verification meta tags | `d926344` | both tags in every page head | trivial |
| H8 | `b7649984#8` HTTPS redirect and meta copy a1–a3 | `777dcad` | titles and descriptions contain the refund wording and minimum | content |
| H9 | `e096458f#23` news page with toon, Instagram, badge (assets supplied from the accepted commit) | `a4c9657` | page exists in 4 languages, linked, badge not repeated | feature |

Add 3 non-FE tasks from a project with real history and tests: candidates are this repository's guard fixes, for
example `a10f894` (heredoc edits unseen by the guard). They are not part of the plugin under test only when the arms
load the plugin from another path, as the runner already does. Building H means authoring and validating 12 hidden
checks. It needs no paid session.

## Limits

- One model (claude-opus-5-5) and one machine. Re-measure when the model or CLI changes (the audit lists this gap).
- `off` is not platform-only: it carries the global file, user hooks and the codex plugin. Section B tests whether
  `--setting-sources` can remove them.
- The confusion matrix rests on one labeler. The tables are reproducible from the label file, and the labels are open
  to correction.
