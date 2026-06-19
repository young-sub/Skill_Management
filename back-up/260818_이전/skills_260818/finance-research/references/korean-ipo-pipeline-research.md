# Korean IPO pipeline research — KRX KIND + private-company triangulation

Use this when researching Korean private companies preparing to list, especially sectors with many 기술특례/예비심사 candidates.

## Primary source: KRX KIND 예비심사기업

KRX KIND is the best first stop for verifying whether a company has actually filed a listing preliminary review (`상장예비심사청구`) versus only being reported as IPO-preparing.

Useful pages/patterns:

- Main page: `https://kind.krx.co.kr/listinvstg/listinvstgcom.do?method=searchListInvstgCorpMain`
- Detail page pattern: `https://kind.krx.co.kr/listinvstg/listinvstgcom.do?method=searchListInvstgCorpDetail&bizProcNo=<ID>`
- Search POST target: `https://kind.krx.co.kr/listinvstg/listinvstgcom.do`
  - `method=searchListInvstgCorpSub`
  - `forward=listinvstgcom_sub`
  - `orderMode=2`, `orderStat=D`
  - `listTypeArrStr=01|02|03|04|05|06|07|`
  - `invstgRsltArrStr=01|02|03|04|05|08|07|06|`
  - set both `searchCorpNameTmp` and `searchCorpName` to the company name

Fields worth extracting from detail page:

- 회사명 / 설립일 / 대표이사 / 업종 / 주요제품
- 매출액, 법인세차감전계속사업이익, 순이익, 자기자본
- 심사청구일, 심사결과
- 상장예정주식수, 공모예정주식수
- 상장주선인, 감사인

Interpretation:

- `청구서 접수`: actually in KRX review pipeline.
- `심사 철회`: not currently in active review; treat as re-try candidate, not near-term IPO.
- No KIND row: likely only 주관사 선정/프리IPO/보도 단계 unless another official filing confirms otherwise.

## Triangulation workflow

1. Start with KIND to separate `filed` vs `preparing/reported`.
2. For filed companies, open detail page and extract financials + products + sponsor.
3. For non-filed companies, search reputable business media for:
   - 주관사 계약
   - 기술성평가 통과/탈락
   - 프리IPO 규모 and investors
   - planned IPO timing
   - latest revenue, losses, backlog, major contracts
4. Classify companies into clear buckets:
   - 예심 청구 완료
   - 예심 철회/재도전
   - 주관사·프리IPO 단계
   - 보도상 준비 단계 only
5. For investment framing, compare by:
   - IPO visibility
   - revenue/backlog proof
   - technology/product edge
   - business model repeatability
   - capital impairment/cash burn
   - sector/regulatory risks

## Example from Korean drone IPO research, 2026-05

Active KIND preliminary review rows:

- 니어스랩: `bizProcNo=20251114000430`; 청구일 2026-03-23; 주관사 삼성증권; 주요제품 `KAiDEN, XAiDEN, 풍력발전기 점검 솔루션`; KRX detail showed revenue about 55.35억 원, large losses and negative equity.
- 넥스트에어로스페이스: `bizProcNo=20260129000320`; 청구일 2026-05-21; 주관사 삼성증권; 주요제품 `무인항공기 및 무인 비행장치 제조`; KRX detail showed revenue about 120.84억 원 and net loss about 172.7억 원.
- 숨비: `bizProcNo=20240729000236`; 청구일 2025-01-20; 심사철회 2025-04-18; 주관사 키움증권. Treat as re-try/uncertain, not active pipeline.

Reported/pre-filed candidates from media searches:

- 파블로항공: instead of active KIND row, media reported IPO schedule reset after technology evaluation did not meet required grade; still important due to swarm-drone and defense story.
- 프리뉴: Korea Investment & Securities as sponsor, pre-IPO funding, technology-special listing preparation; no KIND row at the time.
- 메이사: Kiwoom sponsor, pre-IPO funding, 2026 H2 target; drone/satellite spatial AI platform rather than pure drone maker.
- 가이온: Korea Investment & Securities sponsor, IPO target, data/security/drone control platform; check capital structure due IFRS-related capital impairment discussion in media.
- 인투스카이: IBK Investment & Securities sponsor contract reported, but no KIND row at the time.

## Output pattern for the user

Keep Telegram output compact but research-grounded:

- Start with `기준일` and source basis: `KRX 예비심사 공시 + 주요 보도 기준`.
- Lead with the ranked conclusion: which companies are actually closest to listing.
- Avoid pipe tables in Telegram; use labeled bullets.
- Explicitly separate `상장 가시성` from `사업성/기술 매력`.
- End with 5 watchpoints: 예심 결과, 수주잔고→매출 전환, 양산능력, 방산 고객 질, 현금소진/자본잠식.

## Pitfalls

- Do not treat 주관사 선정 or 프리IPO as equivalent to KRX 예심청구.
- Do not over-rank pure media hype; current KIND status should anchor the IPO pipeline.
- For 기술특례 candidates, avoid generic “성장성 높음” and foreground actual revenue, losses, equity, and technology-evaluation status.
- Drone/defense candidates often pivot from civil use cases into defense narratives; verify whether defense revenue is actual, backlog, MOU, or only product demo.
