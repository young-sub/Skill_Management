---
name: finance-research
description: "Finance and investment research workflows: concise thesis-first analysis, company/sector research, valuation framing, risks, and event-driven watchpoints."
---

# Finance research

Use this skill when the user asks about stocks, ETFs, sectors, markets, earnings, valuation, catalysts, risks, portfolio context, or investment research. The goal is not to give financial advice or price targets as certainties; the goal is to produce a clear, decision-useful research frame.

## User-specific operating style

The user primarily cares about finance/investment research but still asks across other domains. For finance analysis:

- Use **Korean polite/formal speech by default** (`~입니다`, `~습니다`). This is a strong style preference, especially in Telegram.
- Prefer **balanced length**: not a long report by default, but not so short that the core thesis disappears.
- Lead with the **core investment thesis**.
- Include why it matters now, key evidence, risks, and watchpoints.
- Treat the preferred format as **adaptive, not rigid**: carry forward feedback about format, length, concision, and emphasis so the user does not need to restate it in each analysis request.
- For daily market reports, keep the **macro section brief** (usually 3-5 lines) and spend more attention on actionable stock selection.
- Avoid producing only obvious mega-cap consensus ideas. Include at least one **less-consensus small/mid-cap or new-momentum idea** in both domestic and overseas sections when possible, and label lower-confidence theme-extension candidates clearly.
- Expand into detailed financials, model assumptions, source excerpts, or scenario work only when asked.
- Avoid news dumps. Convert information into investment meaning: `news/event -> business impact -> earnings impact -> valuation/sentiment impact -> what to watch next`.
- Avoid overconfident buy/sell language. Frame conditions: what would make the setup attractive, risky, or invalidated.

Session-specific profile and preferences are summarized in `references/user-finance-profile.md`.

For Telegram investment-channel daily reports, use `references/telegram-investment-daily.md` for the preferred source list, report format, and tracking/weighting workflow.

For active ETF holdings-following systems that surface emerging stocks/themes and explain why they matter, use `references/active-etf-signal-agent.md`. Keep deterministic evidence/scoring separate from LLM commentary, and separate user-preference feedback from investment-outcome learning.

For recurring or ad-hoc Korean global-market morning briefings, especially Kim Hyun-seok / Wall Street Now style analysis, use `references/global-market-briefing.md` for the market-numbers -> data/Fed -> rates -> sectors -> internals -> risk-scenarios workflow.

For sovereign-rate, yen-carry, Korea mortgage-rate, household-debt, and real-estate spillover questions, use `references/rates-carry-housing-transmission.md`. Always connect `US/Japan/Korea yields -> curve/FX/carry -> US & Korea equities -> Korean 주담대/부동산` and distinguish rising carry pressure from an actual forced yen-carry unwind.

For US-listed insider buying/selling, Form 4/Form 144 checks, 10b5-1/planned sale interpretation, or “최근 내부자 매도” questions, use `references/sec-insider-transactions.md`. Separate actual Form 4 sales from proposed Form 144 sale notices and cite SEC filings as the primary source.

For newly listed stocks and IPO demand/momentum reports, use `references/ipo-first-day-analysis.md` for the preferred workflow: SEC 424B4 terms, first-day OHLCV/turnover, recent IPO cohort comparison, and supply-demand persistence framing.

For Korean private companies preparing to list, IPO-candidate sector maps, or “상장 준비 중인 회사” requests, use `references/korean-ipo-pipeline-research.md`: anchor status in KRX KIND 예비심사기업 data, separate actual 예심청구 from 주관사/프리IPO/media-only preparation, then compare business model, technology edge, financial quality, and listing risks.

For US solar, battery ESS/BESS, solar-plus-storage, and energy-transition infrastructure requests, use `references/us-solar-ess-research.md` for the segment map, source checklist, stock universe, risk factors, and preferred concise Korean output shape.

For drone/UAV, military drone, C-UAS/anti-drone, drone delivery, or domestic-vs-overseas drone industry outlook requests, use `references/drone-industry-market-research.md` for reusable market-size figures, source excerpts, domestic/overseas company maps, and Korean investment-report structure.

For PE/private credit mezzanine, structured equity, CB/BW/EB/CPS/RCPS, convertible PIPE, or downside-protected investment-condition requests, use `references/mezzanine-structured-equity-research.md`. Screen by funding need, repayment capacity, downside protection, negotiability, and equity upside—not theme exposure alone—and provide draft terms when requested.

For banks, savings banks, card/capital companies, BNPL/fintech lenders, private credit, and other lending-heavy financials, use `references/lending-finance-company-analysis.md` for the problem map, cost structure, Korean terminology, and concise user-facing output shape.

For lending-business, underwriting, credit screening cost, borrower/lender friction, or loan-market infrastructure requests, use `references/lending-underwriting-market-research.md`. It contains the reusable information-source map, cost-conversion ranges, corporate vs personal loan hurdles, decline/limit-cut cases, and the HTML/PDF market-report output pattern that worked for this user.

For LLM-derived Large Tabular Models (LTMs), tabular foundation models (TFMs), or credit-risk foundation model strategy, use `references/ltm-credit-risk-foundation-models.md`. It captures the market map (Fundamental/NEXUS, Prior Labs/TabPFN, TabICL, Feedzai RiskFM), credit-risk build checklist, regulatory hurdles, and preferred Korean business-report structure.

For financial TFM productization, especially lender Early Warning concepts, risk/asset-manager use cases, watchlists, action queues, vintage/channel monitoring, and CB vs alternative-data partnership risks, use `references/financial-tfm-early-warning-product.md`. Treat Early Warning as an operating system: `Prediction -> Prioritization -> Action -> Monitoring`, not just a risk score.

## Default response shape

For a company, ETF, or sector request, use this compact structure unless the user asks for a full report:

```markdown
## [Ticker/company] 핵심 분석

### 핵심 thesis
[One tight paragraph: what the market is debating, why the asset matters, and the main investment setup.]

### 지금 중요한 이유
[Why this matters now: earnings, product cycle, macro, regulation, sector rotation, event, or valuation reset.]

### 핵심 변수
- [Variable 1]: [why it matters]
- [Variable 2]: [why it matters]
- [Variable 3]: [why it matters]
- [Optional variable 4]

### 중기 모멘텀
- [3-12 month catalyst/event/watchpoint]
- [Earnings, guidance, product launch, policy, supply chain, macro, etc.]

### 깨지는 조건
[What would invalidate the thesis or weaken the setup.]
```

For quick questions, compress this to 5-8 bullets. For deeper requests, expand each section with data and sources.

## Analysis priorities

When analyzing a company, prioritize:

1. **Technology / product edge** — what the company can do that others cannot, and whether it matters commercially.
2. **Earnings growth** — revenue growth, margin trend, operating leverage, free cash flow, and guidance.
3. **Valuation** — current multiple versus growth, peers, risk, and market expectations.
4. **Risks** — business model, competition, regulation, margin pressure, capex intensity, cyclicality, and thesis-break conditions.

## Core workflow

1. **Clarify the asset and horizon from context.** If the user does not specify, assume a medium-term investment lens unless the query clearly asks for trading, long-term compounding, or macro.
2. **Check current facts with tools when needed.** Prices, earnings, dates, rates, and recent news must be grounded in current data rather than memory.
3. **Preserve source provenance.** When the user asks where figures came from, distinguish each source class explicitly: market data API/tool output, primary filings/IR, news/RSS/search results, Telegram/social-channel posts, YouTube transcripts, and prior-session memory. Do not imply a figure came from a primary market feed if it was only quoted inside a channel post or article.
4. **Separate company quality from stock attractiveness.** A great company can be a poor setup at the wrong price.
4. **Identify the market debate.** Good finance analysis usually turns on the disagreement: growth durability, margins, AI monetization, capex burden, regulation, cyclicality, or valuation.
5. **Tie events to investment meaning.** Do not list events without explaining how they could change estimates, multiples, or sentiment.
6. **End with watchpoints and invalidation.** The user values actionable monitoring variables.

## Medium-term momentum lens

The user often focuses on medium-term momentum and event-driven sector/stock setups. In those cases, emphasize:

- Upcoming earnings and guidance
- Product launches or developer conferences
- Regulatory rulings or policy events
- Capex cycles and supply chain signals
- Sector rotation and narrative shifts
- Estimate revisions and margin inflection
- Relative valuation versus closest peers

## Preferred domains and examples

The user is especially interested in:

- US equities
- Korean exposure mostly through ETFs
- AI, semiconductors, AI infrastructure
- Physical AI, robotics, autonomous systems
- Power/electricity and data center infrastructure
- Event-driven sectors receiving market attention

When relevant, connect technology to investability. Example: for Alphabet/Google, do not stop at "Gemini is an AI model"; explain whether Gemini, TPU, Google Cloud, and AI Search can protect Search economics or drive re-rating.

## Pitfalls to avoid

- Too long by default: do not produce a full report unless requested.
- Too short: do not remove the thesis logic, the reason it matters, or invalidation conditions.
- News-listing: do not summarize headlines without investment interpretation.
- Generic pros/cons: make risks specific enough to monitor.
- Pure technology explainer: for investment questions, always connect technology to revenue, margins, moat, valuation, or catalyst.
- False precision: avoid unsupported price targets or certainty language.
- Ignoring valuation: momentum can matter, but valuation determines how much good news is already priced in.

## Source hierarchy

Prefer primary and high-quality sources for important claims:

1. Company filings, earnings releases, investor presentations, call transcripts
2. Official product announcements and technical docs
3. Market data and reputable financial data providers
4. Sector research, credible media, and analyst commentary
5. Social media or community commentary only as sentiment/context, not as core evidence

### Private/company-specific news lookup tip

For Korean private fintech/startup requests where generic web/news search is noisy or sparse, check the company's own newsroom/blog as a primary source before concluding there is little news. Many company sites expose a Next.js bundle or WordPress REST endpoint behind the rendered page. Useful pattern:

- Inspect the public newsroom page for links and Next.js script chunks.
- Search chunks for `wp-json`, `all?per_page`, `categories`, or post-type names.
- Query the discovered endpoint directly, then filter by the requested month/date range.
- Cross-check any company press item with outside media when it materially affects investment or industry interpretation.

Example pattern from PFCT/PeopleFund: the PFCT newsroom uses `https://blog.pfct.co.kr/wp-json/pfct/v1/all?per_page=...&status=publish&page=1&categories=...`, which surfaces dated press/in-media items more cleanly than generic search.

## Compliance note

Phrase outputs as research and scenario framing, not personalized financial advice. Encourage the user to treat conclusions as inputs to their own decision process.
