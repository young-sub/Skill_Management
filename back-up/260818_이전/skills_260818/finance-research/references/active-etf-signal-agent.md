# Active ETF signal agent research pattern

Use this reference when reviewing, designing, or improving a system that tracks active ETF holdings to surface emerging stocks/themes and explain why they matter.

For the user's `Agentic_Template/src/agent_treport/` project and its `src/agent-pack` harness context, see `references/agentic-template-agent-treport.md` for project-specific provider, Telegram, evidence, and feedback-loop notes.

## Core principle

Do not replace deterministic ETF/market-data logic with an LLM. Keep a strict split:

1. Deterministic evidence layer
   - holdings snapshots, ticker/entity mapping, source dates, ETF metadata
   - weight/share/dollar-flow changes
   - AUM-adjusted flow and price-move decomposition
   - data-quality issues, coverage limits, source provenance

2. Signal scoring layer
   - manager conviction, consensus across ETFs/managers, flow materiality
   - momentum confirmation, catalyst confirmation, valuation/risk penalty
   - novelty/repetition controls and conviction tiers

3. LLM research layer
   - evidence-bound `why now`, theme classification, manager-read interpretation
   - catalyst synthesis from news/financials/disclosures
   - counter-thesis, missing evidence, confidence labeling
   - Telegram/report wording and compression

4. Feedback/outcome learning layer
   - user preference feedback, report-quality feedback, and investment-outcome feedback must be stored separately
   - user liking a report is not the same as the signal generating alpha

## Useful scoring dimensions

- Manager conviction: new position, persistent add, rank-up inside ETF, size of active bet.
- Consensus: multiple active ETFs/managers buying the same name/theme; penalize single-manager/style artifacts.
- Flow materiality: AUM-adjusted dollar change; compare to average daily trading value where possible.
- Price/weight decomposition: distinguish true buying from weight increase caused by stock-price appreciation.
- Momentum confirmation: relative strength, volume breakout, trend acceleration.
- Catalyst confirmation: earnings revision, guidance, product launch, policy/regulatory event, order/customer news, disclosure.
- Risk/valuation penalty: crowdedness, valuation stretch, liquidity, one-headline dependency, earnings-event risk.
- Novelty: penalize repeatedly covered obvious mega-cap names unless the incremental signal is new.

Prefer conviction tiers over a single opaque score:

- Tier A: ETF flow + price momentum + catalyst are aligned.
- Tier B: strong ETF flow but catalyst needs confirmation.
- Tier C: early interesting signal, higher uncertainty.
- Watch: data-quality or evidence gaps limit confidence.

## LLM output contract

Ask the model for structured JSON, not freeform prose. Require source/evidence IDs for material claims.

Suggested fields:

```json
{
  "ticker": "...",
  "theme": "...",
  "why_now": "...",
  "manager_read": "...",
  "supporting_evidence": [
    {"type": "etf_flow", "claim": "...", "source_id": "..."},
    {"type": "news", "claim": "...", "source_id": "..."}
  ],
  "counter_thesis": "...",
  "confidence": "low|medium|high",
  "missing_evidence": ["..."]
}
```

Validation rule: remove, downgrade, or flag claims without evidence/source IDs.

## Report shape for Telegram

Keep Telegram concise and thesis-first:

1. Today/recent-window active ETF alpha read.
2. Top 3 emerging names: ticker, theme, ETF-flow signal, why now, catalyst, risk, confidence.
3. Theme map: e.g. AI power infrastructure, robotics/Physical AI, AI semis/memory, defense/space, biotech risk-on.
4. Watchlist changes: new, conviction up, fading, crowded/overheated.
5. Data-quality line: coverage, freshness, limitations.

Full HTML/Markdown artifacts should carry the detailed evidence ledger, ETF-level holdings changes, news/disclosure/financial source links, counter-thesis, and next events to watch.

## Agent-pack harness implication

For domain systems built on a generic agent harness, keep canonical state in the harness rather than a provider agent SDK:

- run/workflow state
- context/evidence ledger
- artifacts
- model request/response records
- approval gates
- feedback events
- eval/outcome records

Provider SDKs should be adapter/model-call boundaries only. Domain packages should own ETF, market, report, and Telegram semantics; the generic harness should own execution, evidence, approval, feedback, and inspection primitives.

## Pitfalls

- Do not let the LLM invent or mutate holdings/market-data facts.
- Do not let LLM commentary become uncited narrative.
- Do not merge user-preference feedback with investment-performance learning.
- Do not treat raw ETF weight changes as manager buying without checking price effects and AUM context.
- Do not over-rank obvious mega-caps unless there is a new incremental signal.
