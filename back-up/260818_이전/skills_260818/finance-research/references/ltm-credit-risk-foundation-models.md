# LTM / tabular foundation models for credit risk research notes

Use this reference when the user asks about LLM-derived Large Tabular Models (LTMs), tabular foundation models (TFMs), or building/applying foundation models for credit risk underwriting.

## Core framing

- LTM / TFM = foundation-model approach for structured rows-and-columns data, borrowing LLM-era ideas such as transformers, attention, in-context learning, pretraining, and reusable model checkpoints.
- Unlike LLMs, the business output is usually a probability, score, class, regression value, forecast, or risk ranking rather than natural language.
- For credit risk, do not over-index on model benchmark accuracy. The adoption bottleneck is usually data rights, point-in-time labels, calibration, explainability, fair lending, model risk management, auditability, latency, and production governance.
- Recommended thesis: promising category, but in lending the likely winners are those with legal access to proprietary multi-cycle credit data and deployable governance packages, not simply the largest model.

## Market landscape signals to cite

- Fundamental / NEXUS: emerged from stealth in 2026 with $255M funding; positioned NEXUS as a Large Tabular Model for enterprise prediction; announced AWS strategic partnership and SAP Business AI platform availability. Use as evidence that LTM is becoming an enterprise software category.
  - Source: https://press.aboutamazon.com/aws/2026/2/fundamental-announces-255m-in-funding-and-publicly-launches-its-most-powerful-large-tabular-model-ltm
  - Source: https://fundamental.tech/news/sap-nexus-tabular-ai
- Citi Ventures: frames LTMs as a new approach to enterprise AI; useful for market framing and financial-services relevance. Notes banks rely on structured data for fraud, credit risk, regulation, and customer behavior; positions LTMs as deterministic, precise, auditable predictions versus LLM text generation.
  - Source: https://www.citigroup.com/ventures/perspectives/opinion/ltms-large-tabular-models-startups-enterprise-2026.html
- Prior Labs / TabPFN: commercializes tabular foundation models; raised €9M pre-seed in 2025; offers TabPFN deployment options and enterprise licensing. Prior Labs page highlights financial risk management and car-loan approval use cases.
  - Source: https://priorlabs.ai/tabpfn
  - Source: https://www.balderton.com/news/prior-labs-raises-e9m-to-revolutionise-how-businesses-interact-with-their-tabular-data/
- Feedzai / RiskFM: financial-crime-specialized tabular foundation model. Feedzai says it risk-assesses $9T in payments across 120B events annually. Useful analogy for vertical financial risk models, though it is more fraud/AML than credit risk.
  - Source: https://www.feedzai.com/pressrelease/riskfm-ai-risk-model/
- Incumbent/adjacent players to mention as likely acquirers/competitors: FICO, Experian, Equifax, TransUnion, SAS, DataRobot, H2O.ai, Dataiku, Databricks, Snowflake, SAP, AWS, fintech lenders and fraud/AML vendors.

## Technical state notes

- TabPFN / Nature: “Accurate predictions on small data with a tabular foundation model” reports strong performance on datasets up to 10,000 samples and very fast inference compared with tuned baselines.
  - Source: https://doi.org/10.1038/s41586-024-08328-6
- TabPFN-2.5 arXiv: targets up to 50,000 data points and 2,000 features; reports strong win rates versus default XGBoost and introduces a distillation engine for lower-latency production use.
  - Source: https://arxiv.org/abs/2511.08667
- TabICL / TabICLv2: open tabular foundation models focused on scaling in-context learning to larger tables; useful open benchmark/alternative to proprietary LTMs.
  - Source: https://arxiv.org/abs/2502.05564
  - Source: https://arxiv.org/abs/2602.11139
- Credit-risk-specific arXiv signal: “Data Presentation Over Architecture: Resampling Strategies for Credit Risk Prediction with Tabular Foundation Models” benchmarks Home Credit and Lending Club; finds context construction / balanced or hybrid sampling can explain more AUC variance than the TFM family. This is a key caveat: default rarity, context window, and label design matter as much as model architecture.
  - Source: https://arxiv.org/abs/2605.18635
- ScoringBench: argues TFM evaluation should include proper scoring rules and distributional/probabilistic quality, not only point metrics. For credit risk, translate this into PD calibration, Brier/log loss, expected loss, and tail-risk testing.
  - Source: https://arxiv.org/abs/2603.29928

## Credit-risk foundation model preparation checklist

1. Define use case and automation level:
   - New-loan approval, limit/rate assignment, early warning, delinquency transition, collections prioritization, SME cash-flow underwriting, fraud-credit hybrid decisions.
   - Prefer shadow mode / underwriter assist / champion-challenger before automated adverse decisions.
2. Define labels precisely:
   - 30/60/90 DPD, default, charge-off, cure, LGD, EAD, prepayment, fraud-default separation.
   - Preserve decision-time snapshots to prevent leakage.
3. Build data assets:
   - Consumer: CB tradelines, application data, income/employment, DSR/DTI, open banking/cash flow, card behavior, repayment history, device/FDS, macro.
   - SME/corporate: financials, VAT/tax, e-invoices, bank deposits, representative credit, collateral, industry, customer concentration, litigation/seizure/guarantees.
   - Outcome: vintage cohorts, delinquencies, charge-offs, recoveries, collateral disposal, restructurings, utilization, collections events.
   - Governance: feature dictionary, lineage, consent logs, schema versions, data quality rules, model/inference logs.
4. Model design:
   - Single-table TFM is rarely enough. Consider relational customer-account-loan-transaction-collateral encoders, time-series encoders, document/text feature encoders, and multi-task PD/LGD/EAD heads.
   - Add calibration and reason-code layers. Production may require distillation, caching, or smaller challenger models for latency/cost.
5. Evaluation:
   - Compare against logistic scorecards, LightGBM/XGBoost/CatBoost, existing internal scores, and AutoML baselines.
   - Metrics: AUC, KS, PR-AUC, lift, recall at approval rate, approval uplift at fixed loss, expected loss/profit, calibration curve, Brier/log loss, ECE, PD-bucket monotonicity, vintage stability, subgroup fairness, latency, inference cost, override rate.

## Regulatory / business hurdles

- Model risk management: SR 11-7 style concept validation, independent review, ongoing monitoring, change management, model inventory, reproducibility, rollback plan.
  - Source: https://www.federalreserve.gov/boarddocs/srletters/2011/sr1107.htm
- Explainability and adverse action: complex models still need specific, decision-linked reasons. Natural-language explanations alone are insufficient if they are not tied to actual drivers.
  - Source: https://www.consumerfinance.gov/compliance/circulars/circular-2022-03-adverse-action-notification-requirements-in-connection-with-credit-decisions-based-on-complex-algorithms/
- EU AI Act: AI systems used to evaluate natural-person creditworthiness or establish credit scores are high-risk, except systems used for financial fraud detection.
  - Source: https://ai-act-service-desk.ec.europa.eu/en/ai-act/annex-3
- Korea: FSC/FSS announced AI-based credit scoring model verification and financial AI security guidance. Checks include data management, rational algorithm/variable selection, statistical significance, and ability to explain credit model/results to consumers.
  - Source: https://fss.or.kr/fss/bbs/B0000188/view.do?nttId=127206&menuNo=200218
- Privacy/data rights: consent, purpose limitation, pseudonymization, clean room/federated learning/secure enclave may be required for multi-institution training.
- Accounting/capital: if used for PD/LGD/EAD/ECL, calibration and scenario governance matter for IFRS 9 / CECL / provisioning / RWA. A high AUC is not enough.

## Productization and partnership addendum

For Early Warning product design and practical lender risk/asset-manager use cases, load `references/financial-tfm-early-warning-product.md`. That note covers pre-delinquency detection, roll-rate transition prediction, vintage/channel deterioration, limit management, collections prioritization, portfolio loss/ECL forecasting, SME cash-flow warning, product surfaces, MVP scope, success metrics, and CB vs alternative-data partnership risks.

When discussing CB or alternative-data partnerships, emphasize that data access alone can trap the startup as a model-development vendor. Protect the startup's base TFM, training pipeline, adapters, calibration/explainability, deployment infrastructure, derivative-model rights, customer access/reference rights, and revenue share. Treat partner-specific data as adapters/fine-tuning layers rather than the startup's whole model identity.

## Recommended output shape for the user

For a report request, use a concise Korean business-report format:

1. 핵심 결론
2. LTM 정의와 LLM/AutoML 차이
3. 시장 현황 and players
4. 신용 리스크 적용 가능성
5. 구축 준비: data, model, evaluation, governance
6. business/regulatory hurdles
7. phased roadmap: PoC → pilot → shadow/challenger → limited production → own FM/consortium
8. strategic judgment and sources

If useful, create an HTML report attachment with source links and keep the Telegram message as a brief executive summary.