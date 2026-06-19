# Lending underwriting market research notes

Use this reference when the user asks about lending businesses, loan underwriting, credit screening costs, or borrower/lender friction in consumer or SME/corporate lending.

## Corporate lending underwriting: information sources and friction

Core underwriting question: can the borrower generate enough operating cash flow to repay, and if not, can collateral/guarantees produce recovery?

Common information categories:
- Identity/basic company data: business registration, corporate registry, owners/officers, operating history, licenses, real operating site.
- Financials: 3-year financial statements, tax filings, VAT sales, audit reports, account ledgers, debt schedule.
- Cash flow: bank-account deposits, card/PG sales, e-tax invoices, customer payment cycles, payroll/rent/material outflows, line-of-credit utilization.
- Credit information: company credit rating, arrears/defaults, public information, tax/social-insurance arrears, guaranty balances, representative-owner credit.
- Collateral: registry, senior liens, tenant deposits, appraisal value, auction discount, liquidity, LTV, collateral revaluation.
- Business/industry: customer concentration, order backlog, industry outlook, input cost/FX sensitivity, regulation, bank portfolio limits.
- Governance: representative history, shareholder structure, related-party transactions, litigation, seizure/attachment, accounting transparency.

Indicative cost structure:
- Corporate registry: around KRW 1,000 per issuance.
- Tax/local-tax payment certificates: usually free online.
- Corporate credit-rating certificate: roughly KRW 140k-500k depending on business type/size; TCB roughly KRW 280k-400k in common public examples.
- CB/company credit inquiry: bank contract pricing is private; think thousands to tens of thousands KRW per query as a working estimate.
- Real-estate appraisal: material cost item. Examples using public fee tables: KRW 1.3m VAT-included for KRW 1bn collateral, KRW 3.1m for KRW 3bn, KRW 4.8m for KRW 5bn, KRW 8.7m for KRW 10bn.
- Site visit / manual verification: mostly lender labor cost; tens of thousands to KRW 1m+ depending on complexity/location.

Borrower hurdles:
- Preparing many documents, often from different systems.
- Reconciling financial statements, VAT sales, tax invoices, and bank deposits.
- Proving cash flow rather than accounting profit.
- Representative-owner personal credit, tax arrears, and guarantees affecting company credit.
- Collateral haircut: lenders use recoverable value after senior liens, tenant deposits, auction discount, disposal cost, and liquidity.
- Industry/portfolio limits can block loans even when the borrower itself looks acceptable.

Lender hurdles:
- Information asymmetry: inflated sales, related-party revenue, stale receivables, overstated inventory, hidden guarantees/litigation.
- High manual underwriting cost for SME loans.
- Large loss severity on default and slow recovery in workout/rehabilitation.
- RWA/capital and provisioning burden, especially lower-rated or real-estate/PF/CRE exposures.
- Ongoing monitoring cost after disbursement.

Common decline / limit-cut cases:
- Sales grow but receivables and inventory grow faster; operating cash flow negative.
- Interest coverage below 1x.
- Single customer accounts for 70-90% of revenue.
- Owner has recent personal arrears/card-loan stress.
- Collateral has high senior lien or tenant deposits, leaving little real margin.
- Tax/social-insurance arrears exist.
- Revolving credit line is constantly 90-100% used.
- Litigation, guarantees, or related-party support create off-balance-sheet risk.

## Personal unsecured lending: information sources and friction

Core underwriting question: without collateral, does the consumer have enough stable income and repayment discipline to service the loan?

Common information categories:
- Identity/KYC: mobile identity, ID OCR, certificate auth, account verification, device/IP/FDS signals.
- Credit bureau: NICE/KCB/SCI/Korea Credit Information Services; score, arrears, debt, cards, guarantees, credit history.
- Income/employment: tax income certificate, withholding receipt, National Health Insurance qualification/payment, National Pension, payroll deposit.
- Existing debt and DSR/DTI: mortgages, card loans, cash advances, auto loans, unused credit lines depending on internal model.
- Account/cash-flow data: salary deposit, recurring fixed expenses, balance shortages, gambling/suspicious outflows where available.
- Card behavior: installment dependence, cash advance frequency, utilization, payment regularity.
- Non-financial/alternative data: telecom, utilities, health insurance, pension, apartment maintenance, savings assets, platform settlement data.

Indicative cost structure:
- Consumer-facing public certificates are often free online, but the borrower pays time/friction cost.
- KYC/authentication, CB query, FDS, open-banking/mypage/API calls are lender-side per-query or platform costs; public unit prices are usually not disclosed.
- Automated underwriting can be very cheap per application; manual review turns a small personal loan into a much higher-cost case.

Borrower hurdles:
- Credit score and lender internal grade may diverge.
- DSR can block approval even for high-score borrowers.
- Freelancers/platform workers/self-employed may have high actual income but low official recognized income.
- New job, probation, contract work, or recent income gap weakens approval.
- Recent arrears, repeated cash advances/card loans, multiple new loans/queries signal liquidity stress.
- The user often cannot understand why different apps show different limits/rates.

Lender hurdles:
- Need near-real-time low-cost decisions at scale.
- Hidden risks: pending job loss, informal debt, household obligations, gambling/speculative flows, identity fraud, organized loan fraud.
- Unsecured recovery is low; credit cycle deterioration quickly raises loss rates.
- Regulatory/complaint burden: DSR, fair lending/explanation, rate-change requests, adverse-action style explanation expectations.

Market/product opportunities:
- Borrower-side: pre-diagnosis of approval blockers, DSR simulator, high-interest debt consolidation, credit-file cleanup checklist, income-proof packaging for freelancers/platform workers.
- Lender-side: consented data ingestion, cash-flow underwriting, early-warning triggers, explainable decline reasons, fraud detection, and risk-based refinancing rather than blanket rejection.

## Report output pattern that worked

For market-analysis report requests, produce both HTML and PDF when possible:
1. Write a self-contained HTML report with cover page, executive summary, cost tables, borrower/lender hurdle sections, concrete decline cases, market opportunities, and sources.
2. Convert to PDF with Playwright/Chromium if available.
3. Attach both files to the user.

Use tables for cost-conversion sections. Telegram does not render markdown tables well, so put full tables in the generated HTML/PDF and keep the chat summary short with MEDIA links.