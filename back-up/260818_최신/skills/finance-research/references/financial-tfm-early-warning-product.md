# Financial TFM early-warning product notes

Use this reference when the user asks about financial Tabular Foundation Models (TFMs/LTMs), credit-risk AI products, or lender early-warning systems from a risk/asset-management operator's perspective.

## Core definition

Early Warning is not a passive delinquency report. It is an operating system that predicts deterioration before delinquency or loss, prioritizes accounts/cohorts by economic impact, recommends actions, and tracks whether those actions improved outcomes.

Recommended definition:

> A lender risk platform that predicts 30/60/90-day or 6-12 month risk deterioration at borrower, account, product, channel, vintage, and portfolio level, then converts those predictions into watchlists, action queues, and loss/provision forecasts.

Core loop: `Prediction -> Prioritization -> Action -> Monitoring`.

## What risk / asset managers actually care about

Frame the product around questions risk teams ask daily/monthly:

- Which portfolio segment will drive next month's delinquency increase?
- Which normal accounts are likely to roll into 30+ DPD?
- Which 1-29 DPD accounts will cure versus roll to 30/60/90+ DPD?
- Which vintages, channels, products, regions, occupations, or score bands are worsening versus historical curves?
- How much provision, NPL, net charge-off, or ECL pressure is implied?
- Which action is best: soft reminder, limit freeze/cut, refinancing, restructure, collections escalation, NPL sale, or watch-only?
- Where should limited collections/call-center capacity be allocated first?

## High-value use cases

1. Pre-delinquency detection
   - Target: currently performing accounts.
   - Predict: probability of 1+ missed payment or 30/60/90+ DPD within a time window.
   - Inputs: payroll delay, balance shortfalls, card-loan/cash-advance increase, utilization spike, new external borrowing, income/cash-flow decline.
   - Actions: reminders, payment-date adjustment, refinancing offer, limit freeze, human review.

2. Roll-rate transition prediction
   - Predict transitions: Current -> 1-29 DPD -> 30+ -> 60+ -> 90+ -> charge-off/NPL sale.
   - Segment borrowers into self-cure, temporary liquidity stress, structural default risk, and low-recovery/cost-minimize groups.
   - Useful for collections prioritization and staffing.

3. Vintage deterioration monitoring
   - Compare cohorts by origination month/quarter, product, channel, score band, policy version, rate/limit bucket, region, occupation, or partner.
   - Answer: which recent cohort is deteriorating faster than comparable historical curves?
   - Especially relevant to card loans, unsecured personal loans, BNPL, savings-bank loans, capital-company loans, and fintech-originated loans.

4. Limit and exposure management
   - For cards, overdrafts, revolving credit, credit lines, BNPL, and top-up loans.
   - Recommend limit increase, freeze, reduction, utilization cap, retention offer, or watch-only.
   - Important: optimize risk and profitability, not blanket reduction.

5. Collections and recovery prioritization
   - Rank accounts by expected incremental recovery, not just default probability.
   - Combine PD, exposure, LGD, cure probability, contactability, and expected action impact.
   - Metrics: cure rate, roll-rate reduction, recovery per contact, net charge-off reduction, false-alarm burden.

6. Portfolio loss / provision early forecast
   - Output expected delinquency, NPL, net charge-off, ECL/provision change, and contribution by segment.
   - Translate model signals into CFO/risk-committee language: bps change in loss rate, provision amount, reserve coverage pressure, RWA/capital implications when relevant.

7. Channel / partner risk management
   - Track loan-comparison platforms, agents, affiliates, branches, campaigns, embedded-commerce partners, and app-originated flows.
   - Identify channels where CAC looks attractive but credit quality deteriorates.
   - Recommend channel-level policy tightening, pricing changes, or volume caps.

8. SME / self-employed cash-flow deterioration
   - Signals: sales/PG/card receipts decline, tax/social-insurance arrears, delayed customer payments, rising fixed-cost outflows, high line utilization, representative-owner personal credit stress, litigation/seizure signals, customer concentration problems.
   - Actions: review, collateral request, limit adjustment, covenant trigger, refinancing/restructure, collections escalation.

## Product surfaces

- Portfolio Dashboard: for executives and asset/risk managers. Shows expected delinquency/loss, vintage/channel deterioration, product-level risk, and provision/ECL impact.
- Watchlist: ranked list of risky borrowers/accounts/cohorts with risk increase, expected loss, reason codes, confidence, and owner/action status.
- Account Detail: risk trend, top drivers, comparable cohort outcomes, recommended action, expected effect, override log.
- Action Queue: daily operational list for reminders, collection calls, limit management, refinancing offers, and monitoring-only cases.
- Model Risk / Audit pack: performance drift, calibration, fairness/subgroup checks, feature/reason-code logic, version history, action-outcome logs.

## Where TFM adds value over ordinary XGBoost/LightGBM

Do not claim TFM is automatically better. It must earn adoption through capabilities that classic models struggle to package repeatedly:

- Multi-table learning across customer, account, loan, card, transaction, repayment, collateral, and collections tables.
- Temporal representation of recent changes versus long-run borrower patterns.
- Transfer across products/tasks: e.g. card-loan deterioration patterns informing unsecured-loan risk, or consumer stress signals informing BNPL limits.
- Thin-file handling through similarity and representation learning.
- Customer-specific adapters/calibration for each lender while retaining a shared base model.
- Multi-task heads: delinquency, roll-rate, charge-off, cure, recovery, limit-risk, refinancing suitability.

## Recommended MVP

Start narrower than a full risk platform:

> 90-day delinquency-transition Early Warning for unsecured personal loans / card loans.

Minimum modules:

1. Data connector and point-in-time feature builder.
2. 30/60/90+ DPD probability and roll-rate model.
3. Vintage/channel dashboard.
4. Ranked watchlist and action queue.
5. Reason codes and model validation report.
6. Outcome tracking after interventions.

Success metrics:

- Reduction in 30+ DPD transition at fixed action capacity.
- Cure-rate improvement among early delinquency accounts.
- Recovery per contact / per agent-hour.
- Net charge-off or provision savings estimate.
- False-positive burden and manual override rate.
- Uplift versus existing scorecard, LightGBM/XGBoost, or lender incumbent model.

## Partnership-risk notes for financial TFM go-to-market

CB partnership:
- Strong for long-history credit data, labels, credibility, and lender distribution.
- Risk: CB owns data and customer relationships; startup may become an external AI lab unless model IP, derivative-model rights, customer access, and revenue share are protected.

Alternative-data / fintech platform partnership such as Toss-like players:
- Strong for real-time cash flow, behavioral signals, thin-file users, consent channel, and product distribution.
- Risk can be higher than CB because these partners often have data, engineering talent, user relationship, and financial-product distribution; they may internalize the model if the startup only provides modeling labor.

Defensive structure:
- Startup owns base TFM, architecture, training pipeline, calibration/explainability, deployment infrastructure, and multi-source orchestration layer.
- Partner-specific data should be separated into adapters/fine-tuning layers.
- Secure joint product rights, reference rights, revenue share, derivative-model terms, and post-termination rights.
- Avoid dependence on one partner; combine CB, alternative data, lender internal outcome data, and cash-flow data where legally permitted.
