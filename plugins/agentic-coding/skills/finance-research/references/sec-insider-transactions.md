# SEC insider transaction workflow

Use this reference when researching recent insider buying/selling for US-listed companies.

## Preferred source order

1. SEC company submissions API: `https://data.sec.gov/submissions/CIK##########.json`
2. Raw filing XML in SEC Archives for Form 4 / 4/A and Form 144
3. Company IR only as context
4. Third-party insider dashboards only as cross-checks, not primary evidence

## Core workflow

1. Resolve the company CIK.
   - If known, use the zero-padded CIK directly.
   - Otherwise search SEC company tickers JSON or a reliable CIK lookup.
2. Pull recent filings from `data.sec.gov/submissions/CIK{CIK}.json`.
3. Filter the last 30-31 days for:
   - `4`, `4/A`: actual insider transaction reports.
   - `144`: proposed sale notices for restricted/control securities.
4. For each filing, fetch the raw XML from SEC Archives.
   - The `primaryDocument` path may include an XSL folder like `xslF345X06/wk-form4_...xml`; for raw XML, use only the document filename under the accession directory, e.g. `/Archives/edgar/data/{CIK}/{accession_no_dashes}/wk-form4_...xml`.
   - The XSL path often returns rendered HTML, not parseable XML.
5. Parse Form 4 non-derivative transactions:
   - `transactionCode`: `S` = sale, `P` = purchase, `A` = award/grant, `M` = option exercise/conversion, `F` = tax withholding/payment.
   - `transactionAcquiredDisposedCode`: `D` means disposed, `A` means acquired.
   - For insider selling, count only `code == S` and `acqdisp == D` as actual market sales unless the user asks for all disposals.
6. Parse Form 144 as proposed/planned sales:
   - Extract seller name, relationship, number of units, aggregate market value, approximate sale date, broker, class of securities, and acquisition source.
   - State clearly that Form 144 is not proof the sale was completed; follow-up Form 4 confirms actual transactions.
7. Summarize separately:
   - Actual Form 4 sales.
   - Proposed Form 144 sales.
   - Grants/awards/exercises that are not sales.

## Interpretation rules

- Do not equate Form 144 with completed selling. Phrase as “매도 예정/계획 공시”.
- Distinguish planned 10b5-1/compensation/tax-related selling from discretionary negative-signal selling when the filing indicates it.
- For investment meaning, emphasize:
  - scale relative to market cap and remaining holdings,
  - whether CEO/CFO/key founders are involved,
  - clustering across multiple executives,
  - whether actual Form 4 filings follow the Form 144 notices,
  - whether selling occurs after a sharp share-price rally.
- Avoid overclaiming that insider sales imply deteriorating fundamentals without corroborating business evidence.

## Output shape for Korean Telegram

```markdown
## [Ticker] 최근 내부자 매도 요약

### 결론
[1-2문장: 실제 매도와 예정 공시를 구분]

### 실제 매도(Form 4)
- [이름/직책]: [날짜], [주식 수], [금액], [평균가], [매도 후 보유]

### 매도 예정(Form 144)
- [이름/직책]: [예정일], [주식 수], [예상금액]

### 해석
- 부정적 요인: [수급/심리]
- 중립 요인: [계획매도/보상주식/세금 가능성]
- 체크포인트: [후속 Form 4, 10b5-1 여부, 잔여 보유]
```

## Example: Palantir pattern from a prior session

For PLTR, the useful distinction was:

- Form 144 notices on 2026-05-20 by several officers/directors were proposed sales totaling roughly 919,982 shares / about $125.2M.
- A Form 4 filed 2026-05-19 reported Alexander D. Moore's actual 2026-05-15 sales of 16,000 shares / about $2.14M.
- The correct user-facing answer separated “실제 매도” from “매도 예정 공시” and warned that Form 144 requires follow-up Form 4 confirmation.