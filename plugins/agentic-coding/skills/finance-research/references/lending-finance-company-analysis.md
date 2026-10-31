# Lending finance company analysis notes

Use this reference when analyzing banks, savings banks, card/capital companies, BNPL/fintech lenders, private credit, or other lending-heavy financials.

## Core problem map

Lenders usually face problems in five buckets:

1. **Funding cost / margin compression**
   - Banks: deposit beta, competition for deposits, wholesale funding mix, NIM trend.
   - Non-banks: company bonds, CP, ABS/securitization, warehouse lines, institutional funding spreads.
   - BNPL/fintech lenders: loan-sale execution, securitization spreads, partner bank economics.

2. **Credit cost / asset quality deterioration**
   - Track delinquency, NPL/SBL, net charge-offs, provision expense, reserve coverage, vintage curves.
   - Consumer-sensitive areas: credit cards, card loans, auto loans, BNPL, unsecured personal loans.
   - Cyclical/collateral-sensitive areas: CRE, real estate PF, construction, SME, developer loans.

3. **Loan growth and demand weakness**
   - Tightened underwriting can protect loss ratios but lowers origination and fee income.
   - Weak fixed investment or consumer confidence can reduce demand even if funding is available.

4. **Collateral and concentration risk**
   - Korea: real estate PF and savings-bank/second-tier exposure.
   - US/Europe: CRE, regional banks, consumer credit.
   - China: property developers, SME lending, rural/small banks, local-economy concentration.

5. **Regulatory and capital pressure**
   - Higher capital/liquidity requirements, provisioning rules, consumer protection, lending caps, and supervisory pressure can lower ROE.

## Where lenders spend the most money

When the user asks “where do lending companies spend the most?”, answer by distinguishing normal times vs downturns:

- **Normal/core largest cost:** funding cost — interest paid on deposits, bonds, CP, ABS, warehouse lines, or other borrowed capital.
- **Downturn most dangerous cost:** credit loss/provision cost — provisions, charge-offs, collections, NPL sales/write-downs.
- **Operating layer:** personnel, branches, IT, compliance, credit underwriting, collections, marketing/CAC. For fintech lenders, marketing/data/AI infrastructure can be material, but credit losses and funding cost still dominate unit economics.

## Korean terminology mapping

- Funding cost: 조달비용, 예금이자, 회사채/CP/ABS 이자비용
- Credit cost: 대손비용, 대손충당금, 순상각률, 연체율, 부실채권/NPL, 고정이하여신/SBL
- Margin: 순이자마진(NIM), 예대마진, 대출 스프레드
- Coverage: NPL 커버리지, 충당금 적립률

## Preferred concise output shape

For the user, keep it brief and thesis-first:

1. **한 줄 결론**
2. **업권별 차이**: 은행 / 카드·캐피탈 / 저축은행 / 핀테크·BNPL
3. **핵심 지표**: 조달금리, NIM, 연체율, 순상각률, 대손충당금, NPL 커버리지, 대출성장률
4. **투자적 의미**: 이익률, ROE, 밸류에이션, 깨지는 조건

Avoid turning this into a generic textbook explanation. Tie every cost/problem to earnings and valuation impact.