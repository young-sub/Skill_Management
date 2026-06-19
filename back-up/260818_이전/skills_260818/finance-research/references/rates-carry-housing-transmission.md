# Sovereign rates, yen carry, and Korea housing transmission

Use this reference when the user asks about US/Japan/Korea bond yields, yen carry trade risk, equity-market spillovers, Korean mortgage rates, household debt, or real-estate impact.

## Core thesis frame

Do not stop at rate levels. Translate the chain:

`US/Japan/Korea yield move -> curve shape / funding cost / FX -> global risk appetite -> US & Korea equities -> Korean mortgage rates / household debt / housing demand`.

For the user, lead with a concise Korean thesis and then separate the channels: **rates**, **FX/carry**, **equities**, **Korean mortgages/housing**, **watchpoints**.

## Data checklist

Verify current facts with tools before answering:

- **US Treasuries:** 2Y, 10Y, 30Y; 2s10s and 10s30s; weekly/monthly changes when available.
  - Useful source pattern: US Treasury daily yield curve CSV, e.g. `daily-treasury-rates.csv/{year}/all?...&_format=csv`.
- **Japan JGBs:** 2Y, 10Y, 30Y or nearest maturities; BOJ policy-rate context; yen level; super-long JGB stress.
- **Korea KTBs:** 2Y/3Y, 10Y, 30Y or nearest available; BOK policy context; won level; foreign bond/equity flow if available.
- **FX/risk proxies:** USD/JPY, USD/KRW, DXY, VIX, S&P 500, Nasdaq, Russell 2000, KOSPI/KOSDAQ, EWY/EWJ.
- **Korea mortgage/housing:** COFIX, bank household-loan growth, mortgage-loan growth, 5Y bank debenture yield/fixed mortgage benchmark, Seoul apartment and jeonse weekly moves, lending caps/DSR/LTV rules.

## Interpretation rules

### US rates

- 2Y mainly reflects Fed path / policy-rate expectations.
- 10Y is the key equity valuation discount-rate pressure point.
- 30Y is the key fiscal-supply / term-premium / long-duration stress signal.
- If 30Y is above or approaching a psychologically important level while equities still rise, call out the tension rather than declaring risk-on.

### Japan rates and yen carry

Explain yen carry trade simply: cheap yen funding used to buy higher-yielding or higher-return overseas assets.

Japan rate increases matter through three channels:

1. Higher yen funding cost -> lower carry economics.
2. Yen appreciation risk -> FX losses for yen-funded overseas positions.
3. Forced deleveraging -> selling pressure in crowded risk assets such as US tech, Korea/Taiwan semis, EM, high yield, crypto.

Do not overstate every JGB selloff as full carry-trade unwind. Distinguish:

- **Carry pressure rising:** Japan yields rise, but US-Japan short-rate spread remains meaningfully positive and USD/JPY is stable or yen remains weak.
- **Carry unwind risk:** Japan yields rise + yen strengthens quickly + VIX rises + US tech/Korea semis weaken + USD/KRW destabilizes.

Useful watch levels should be stated as scenario thresholds, not deterministic triggers, e.g. Japan 30Y, USD/JPY, VIX, US 30Y, USD/KRW.

### Korea equities

- Exporters/semis can get accounting help from weak won, but this can be overwhelmed by global risk-off and foreign outflows.
- Banks may get some NIM support from higher rates, but mortgage/real-estate/PF credit risk and funding costs can offset it.
- Construction, real estate, PF-sensitive lenders, and high-duration growth stocks are most vulnerable to long-rate rises.
- Export industrials with order-book visibility can be more resilient than domestic rate-sensitive sectors.

### Korea mortgage and housing

Map rate changes into household impact:

- COFIX up -> variable-rate mortgage reset pressure.
- 5Y bank debenture yield up -> fixed mortgage benchmark pressure.
- Household-loan growth reaccelerating despite higher rates -> BOK/regulator dilemma.
- Seoul core can hold up on cash-rich/high-income demand, while debt-dependent buyers are constrained by DSR/LTV.
- Lending caps can redirect demand into quasi-Seoul Gyeonggi areas; call this a financing/geographic substitution effect, not broad national recovery.
- Jeonse price acceleration can support purchase demand, but also increases household cash-flow stress.
- Non-core regions remain more exposed to high rates, unsold inventory, PF, and weak local income growth.

## Preferred output shape

```markdown
## 한줄 결론
[Rates/carry/housing thesis in one sentence]

## 1. 미국 금리 추세
- 2Y / 10Y / 30Y levels and changes
- Curve interpretation
- Equity valuation meaning

## 2. 일본 금리와 엔캐리
- JGB levels and curve shape
- Carry pressure vs actual unwind distinction
- USD/JPY and risk-asset transmission

## 3. 미국·한국 증시 영향
- US: growth/AI, small caps, financials/industrials
- Korea: semis/exporters, banks, construction/PF, growth stocks

## 4. 한국 주담대·부동산 영향
- COFIX / bank debenture / household-loan growth
- Seoul vs Gyeonggi vs 지방
- Jeonse and policy constraints

## 5. 체크포인트
- 5–8 concrete indicators/levels to monitor
```

## Pitfalls

- Do not answer from memory; rates, FX, and mortgage data must be checked current.
- Avoid a raw macro lecture. The user wants investment and market transmission.
- Do not imply personal financial advice about buying/selling property or stocks.
- Do not treat yen carry as binary; frame it as pressure building vs forced unwind.
- Avoid overly long source dumps; cite only the data points needed to support the thesis.
