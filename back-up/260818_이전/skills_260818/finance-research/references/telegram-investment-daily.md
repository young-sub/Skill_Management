# Telegram investment-channel daily report workflow

Use this reference when the user asks for recurring or ad-hoc daily reports based on Telegram investment channels.

## Default sources

Initial equal-weight source set:

Telegram public channels:

- `beluga_investment`
- `athletes_village`
- `awake_schedule`
- `grmtstudy`
- `kimcharger`
- `meritz_research`
- `merITz_tech`
- `sim_the_best`
- `d_ticker`
- `egzion`

For Telegram, use public web pages: `https://t.me/s/{channel}`. Paginate with `?before={message_id}` when necessary.
Proceed with Telegram-channel-only logic. Do not include notes about unused or excluded external sources in routine daily reports.

## Channel accessibility smoke test

When adding channels or before trusting a recurring report, verify each channel can be read from `https://t.me/s/{channel}`:

- Fetch the latest page for every configured channel.
- Parse text posts from `tgme_widget_message` blocks and report `status`, text-post count, latest message datetime/id, and a <=100 Korean-character summary of the latest text post.
- Treat HTTP 200 plus at least one parsed text post as accessible. Media-only latest posts can still be accessible; note that text analysis may skip them.
- If a channel casing is unusual, preserve the exact handle that worked, e.g. `merITz_tech`.

## Lookback window

- Tuesday-Friday daily reports: recent 24 hours.
- Monday daily reports: recent 48 hours to capture weekend issues.
- Convert Telegram UTC datetimes to KST for weekday/window decisions.

## Report style

Korean polite/formal speech. Keep it clear, brief, and decision-useful. Avoid long macro exposition and avoid repeating only obvious mega-cap consensus names.

Preferred order for **08:00 daily reports**:

1. **Macro market trends — brief**
   - 3-5 lines.
   - Include only the most relevant market direction, rates/FX/oil, and key risk/opportunity.
2. **Domestic core 3 stocks**
   - Include large/mid-cap core names only when they are genuinely central to the day's theme.
   - For each: investment points, risks, judgment.
3. **Domestic small/mid-cap or new-momentum ideas — at least 1**
   - Prefer names with evidence: earnings, filings, supply/demand, fund flow, or theme-leadership signals.
   - If multiple, provide main candidate plus optional watch candidate.
4. **Overseas core 3 stocks**
   - Map the day's Korean-channel themes to global tickers when direct overseas mentions are sparse.
   - For each: investment points, risks, judgment.
5. **Overseas small/mid-cap or new-momentum ideas — at least 1**
   - If direct channel evidence is weak, label as a lower-confidence theme-extension candidate.
6. **Tracking list**
   - Domestic and overseas names included in the report.
7. **Channel-weight tracking memo**
   - Keep this short in the report: note data accumulation and any emerging weighting observations.

Preferred order for **15:00 same-day new-momentum reports**:

- Use the same source set as the 08:00 daily report, but the window is same-day 00:00-15:00 KST unless the user says otherwise.
- Exclude broad market/macro commentary entirely.
- Exclude stocks already shown in the 08:00 report's **core stocks / 핵심종목** section. If a prior report output is available, read it first and de-duplicate before selecting names.
- Compress aggressively to **domestic 3 stocks + overseas 3 stocks**. Do not produce long watchlists.
- For each stock, use one sentence for the core momentum and one short confirmation/risk point.
- End with only a short priority order: `국내: 1순위 / 2순위 / 3순위`, `해외: 1순위 / 2순위 / 3순위`.

## Stock selection heuristics

Do not rank by mention count alone. Combine:

- Mention count across channels.
- Information freshness: new report, filing, earnings, supply/demand, price action, event.
- Investment meaning: effect on earnings, margins, estimates, multiples, supply-demand, or narrative.
- Crowding: avoid only obvious mega-cap repeats; add less-consensus small/mid-cap ideas.
- Risk: mark chase risk after sharp intraday rises.

## Channel-weight tracking

Start with all channels at weight `1.0` for the first 2-3 weeks. Do not overfit early noise.

For each report, append records to `~/.hermes/finance_daily/channel_tracking.jsonl` when feasible. Record:

- date/time
- channel
- mentioned stock name/ticker if known
- mention timestamp
- price at mention/report time if available
- mention type: `simple`, `report`, `earnings`, `flow`, `theme`, `filing`, `macro`
- 1-day, 3-day, and 5-trading-day returns when later available
- benchmark-relative return: domestic vs KOSPI/KOSDAQ; overseas vs S&P 500/Nasdaq/SOX as appropriate

Later weighting inputs:

- Performance: average 5-trading-day excess return.
- Hit rate: share of positive excess-return mentions.
- Lead quality: whether the channel mentioned a name before broader channel clustering.
- Evidence quality: filings/earnings/research/supply-chain data outrank simple headlines.
- Chase penalty: frequent post-spike mentions or high drawdowns after mentions.

Potential weights after enough data:

- Strong leading/evidence channel: `1.2-1.5`
- Neutral/news relay: `0.8-1.0`
- Repeated chase/noisy channel: `0.5-0.8`

## Pitfalls

- Do not let high-volume channels dominate when weights are equal; normalize qualitatively by channel and content value.
- Do not infer precise tickers when uncertain. Store the company name only rather than inventing a ticker.
- If a channel has no text posts in the window, say so only if it matters; otherwise just exclude it from evidence.
- For overseas small/mid-cap ideas derived from Korean-channel themes rather than direct mentions, explicitly state that confidence is lower and that it is a theme-extension candidate.
- **Do not let collection/tooling failures become silent deliveries.** In scheduled daily-report jobs, `[SILENT]` should only mean there is genuinely nothing to report. Missing optional Python packages, partial channel failures, HTTP errors, or sparse data should produce a short report with a collection-limit note, not `[SILENT]`.
- **Avoid unnecessary external parser dependencies in cron jobs.** Telegram `t.me/s/{channel}` pages can be parsed with Python stdlib (`urllib.request` or `requests`, `re`, `html`, `datetime`). Do not require `bs4`/BeautifulSoup unless the job environment explicitly installs it.
- **For Telegram delivery, prefer explicit targets over bare `telegram` when the user names a fixed room.** Use the concrete target/chat id (and topic id if applicable) so scheduled outputs do not disappear into a default/home channel unexpectedly.