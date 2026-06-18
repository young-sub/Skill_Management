# Agentic_Template active ETF report system notes

Session-specific reference for reviewing or improving `Agentic_Template/src/agent_treport/` and its relationship to `src/agent-pack`.

## Project intent

`src/agent_treport/` tracks active ETF holdings from multiple asset managers, watches changes over a chosen period, combines the holdings signal with news/financial/disclosure evidence, and sends a Telegram report explaining which stocks/themes appear to be gaining market attention and why.

The investment view is: active ETF managers' holdings changes can reveal emerging alpha or theme rotation earlier than broad consensus, but raw holdings changes are only a candidate signal until confirmed by catalysts, price/volume behavior, financials, disclosures, and subsequent outcomes.

`src/agent-pack` is the generic commercial-agent harness layer. Treat it as the reusable framework for execution state, evidence ledgers, artifacts, model traces, approvals, feedback events, and eval/outcome tracking. Domain semantics such as ETFs, tickers, themes, Telegram report layout, and finance-specific scoring should stay in `agent_treport`.

## Current direction to preserve

The system may begin with deterministic/naive logic, but do not simply replace it with freeform LLM reasoning. Evolve it into an evidence-bound agent:

1. Deterministic holdings and market-data layer
2. Candidate signal scoring layer
3. External evidence collection layer
4. LLM evidence-alignment and commentary layer
5. Report rendering layer
6. User-feedback and investment-outcome learning layer

## Data sourcing pattern: reduce paid API dependence

Prefer a layered evidence strategy:

1. Primary sources
   - SEC EDGAR submissions and companyfacts
   - DART/KIND for Korea
   - company IR/newsroom/press releases
   - ETF manager holdings/factsheet CSV, PDF, or webpage

2. RSS/public feeds
   - Google News RSS for discovery
   - company IR RSS/news feeds
   - SEC latest filings feeds
   - GDELT for broad news-volume/theme discovery

3. Search discovery
   - Brave/Tavily/SerpAPI/Bing/DuckDuckGo-style discovery is acceptable, but search snippets should not become final evidence. Fetch and store the source document when possible.

4. Existing APIs as fallback/enrichment
   - yfinance/Finnhub/Alpha Vantage/NewsAPI/Naver can fill price/news gaps, but should not outrank primary filings/IR or reputable source documents.

## Provider additions worth prioritizing

Add providers through the existing `external_evidence` abstraction rather than building separate bespoke flows.

High-ROI additions:

- `google_news_rss`: keyless discovery for ticker/company/theme/catalyst queries; requires dedupe and relevance filtering.
- `sec_companyfacts`: official financial facts for revenue, margin, operating income, cash flow, capex, shares, and selected XBRL tags.
- `company_ir_feed`: ticker registry of IR/newsroom/press-release RSS or HTML sources.
- `web_search_discovery`: query planning -> search results -> source fetch -> evidence candidate; never rely only on snippets.
- `telegram_public_channel`: optional social/research-channel signal layer; store channel, message ID, timestamp, ticker, mention type, evidence quality, price at mention, and later 1d/3d/5d relative outcomes.

## Evidence metadata to standardize

Each evidence candidate should carry enough metadata for ranking, auditing, and LLM grounding:

```json
{
  "source_tier": "primary|reputable_media|rss_aggregator|search_discovery|social",
  "discovery_method": "google_news_rss|company_ir_feed|sec|dart|search|telegram",
  "freshness_hours": 12,
  "is_primary_source": true,
  "canonical_url": "...",
  "publisher": "...",
  "query": "...",
  "claim_type": "earnings|guidance|order|product|regulation|price_volume|filing|theme",
  "catalyst_strength": "high|medium|low",
  "ticker_relevance": "direct|sector|theme|weak",
  "requires_llm_validation": true
}
```

Scoring should reflect source tier and freshness. SEC/IR/earnings releases are strong evidence; Google RSS headlines and social mentions are discovery or weak evidence unless confirmed.

## LLM role separation

Use LLMs for bounded reasoning, not uncontrolled fact collection:

1. Query planner: generate ticker/company/theme/catalyst searches.
2. Deterministic fetcher: collect actual documents from RSS/search/IR/SEC/DART.
3. Evidence classifier: decide whether a document supports, contradicts, or is irrelevant to the ETF signal; require source IDs.
4. Report writer: write `why_now`, risk, watchpoint, and confidence only from validated evidence.
5. Quality gate: downgrade/remove uncited claims.

## Telegram report shape

Telegram should be thesis-first and short enough to read on mobile:

- Title/date/universe/data-quality line
- One-sentence market/ETF alpha read
- Top 3 signals, each with the same slots:
  - ticker and theme
  - ETF flow signal
  - why now
  - confirming evidence count/types
  - key risk or thesis-break condition
  - confidence/tier
- Watchlist: 2 lower-confidence names or fading/crowded signals
- Theme map
- Full artifact path/link

Prefer decision-useful language over raw scores. A useful ranking formula can combine: signal score + evidence quality + novelty + user-theme relevance + cross-source confirmation - mega-cap repetition - weak-data penalty - post-spike chase penalty.

## Feedback and outcome learning

For Hermes-like improvement, store three different learning streams separately:

1. User/report feedback: too verbose, too obvious, weak risk section, preferred format, useful/not useful.
2. Signal-quality feedback: whether ETF/catalyst reasoning was later judged right or wrong.
3. Investment outcome: 1d/3d/5d/20d absolute and benchmark-relative returns after report publication.

Do not let user liking alone update alpha scoring. Do not let short-term price outcome alone rewrite user-facing style preferences.

## Implementation priority

1. Add `google_news_rss` provider and evidence metadata/dedupe.
2. Improve Telegram renderer to Top 3 thesis slots plus watchlist and data-quality line.
3. Add LLM evidence-alignment/commentary step with source IDs.
4. Add feedback events and outcome-tracking records through `agent-pack` primitives.
5. Add primary-source financial/disclosure enrichment such as SEC companyfacts, DART, and company IR feeds.
