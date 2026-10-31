# IPO first-day momentum and demand analysis

Use this reference when analyzing a newly listed stock where technical indicators are not yet meaningful.

## Core workflow

1. **Confirm IPO terms from primary sources**
   - Prefer SEC final prospectus / 424B4 for U.S. IPOs.
   - Extract: offering price, shares offered, underwriters, expected delivery date, post-offering share count, use of proceeds, lock-up language, customer concentration, and recent financials.
   - For issuer fundamentals, separate GAAP accounting effects from operating quality when filings show large non-operating gains/losses.

2. **Measure first-day demand with market data**
   - Pull first-day OHLCV from a market data source such as Yahoo chart endpoint.
   - Compute:
     - IPO pop at open: `(open / IPO price - 1)`
     - IPO pop at close: `(close / IPO price - 1)`
     - Intraday max pop: `(high / IPO price - 1)`
     - First-day volume vs shares offered: `volume / shares offered`
     - Approximate dollar turnover: volume × VWAP or rough OHLC average
   - Interpret volume/share-offered above 1.0x as the offered float turning over at least once; pair this with price behavior to judge whether demand was sustained or faded intraday.

3. **Compare with recent IPO cohort**
   - Use the most relevant last-12-month cohort by theme and size, not only all IPOs.
   - For AI infrastructure / fintech / software IPOs, compare first-day pop, volume, estimated dollar turnover, and narrative intensity.
   - Avoid overfitting exact rankings when data vendors differ; use tiers such as "top-tier", "strong but below the hottest IPOs", or "moderate".

4. **Assess duration of the supply-demand effect**
   - 1–2 weeks: narrative scarcity, retail/institutional chase, media coverage can dominate.
   - 3–6 weeks: analyst initiation, follow-on contract news, sector tape, and first post-IPO trading base matter more.
   - Medium term: fundamentals, guidance, customer concentration, lock-up schedule, and valuation vs growth determine persistence.

## Report framing

For the user, lead with the investable conclusion rather than a news dump:

- **Core thesis**: what the market is underwriting.
- **Why now**: IPO terms, first-day demand, major contracts/partners, sector narrative.
- **Demand strength**: first-day pop, volume, dollar turnover, comparison cohort.
- **Persistence call**: likely time window for momentum and what must happen for it to continue.
- **Risks / invalidation**: valuation, customer concentration, competition, lock-up, execution.

## Pitfalls

- Do not use technical indicators such as moving averages or RSI on a one-day-old listing; use price/volume, float turnover, intraday acceptance/rejection, and cohort comparison instead.
- Do not treat first-day IPO pop as proof of fundamental undervaluation. It can reflect scarcity, underpricing, and thematic demand.
- Do not compare only percentage return; large offering size and dollar turnover can make a lower-percentage pop more market-relevant.
- Always distinguish "company quality" from "stock attractiveness at the first traded price."