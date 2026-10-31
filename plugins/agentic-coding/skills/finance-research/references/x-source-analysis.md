# X source collection and stock-performance analysis notes

Use this reference when an investment report needs to incorporate a specific X/Twitter account as a source, especially for "positive mentions over a lookback window" and subsequent stock-return checks.

## Source handling

- Prefer configured official tooling (`xurl`) when available and authenticated.
- If official tooling is not available, public X web/guest endpoints may provide partial historical visibility. Treat this as best-effort, not complete archival coverage.
- Always state the collection boundary: account, lookback period, newest/oldest collected post, number of posts, and whether the period had zero collected posts.
- If the requested window has no accessible posts, say so clearly and do not invent recent mentions from older posts.
- If using older accessible posts only as context, label the section as "참고용" and separate it from the strict answer.

## Positive mention classification

For finance source analysis, classify a ticker as positively mentioned only when the nearby text includes explicit positive language or constructive setup language, such as:

- `Strong Buy`, `Buy`, `Add`, `Hold/add`, `winner`, `fire sale`, `asymmetrical upside`
- positive assessment terms: `positive`, `highly positive`, `blowout`, `secured`, `better economics`, `record`, `insane growth`
- thesis-style constructive framing tied to a ticker, contract, earnings, guidance, orderbook, or capex beneficiary status

Avoid treating every ticker in a broad list as positive if the post is mixed, sector-crash related, or simply lists market movers. Flag ambiguous cases separately or omit them from the positive list.

## Return calculation

- Use adjusted close / auto-adjusted close when available.
- For "1M" returns, use the latest available trading close and the closest trading close at or before 30 calendar days earlier.
- Report the price-date pair or at least the latest close date so the user can see whether data is delayed by market holidays/weekends.
- If a ticker is newly listed or lacks a 30-day history, mark `N/A` rather than forcing a return.

## Output style for the user

- Start with the strict-window answer first: whether the account had positive mentions during the requested lookback.
- Then provide a compact table-like bullet list: `Ticker: positive mention basis / 1M return`.
- If strict-window data is empty but older context is available, add a separate "참고용: 과거 접근 가능 게시물 기준" section.
- Keep caveats short and actionable; do not turn source limitations into a long tooling explanation.