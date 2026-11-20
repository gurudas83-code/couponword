# Price engine audit and exact-key missing queue — 20 Nov 2026

## Audited source
- Catalogue: `data/mobile_research_catalogue.json`, 232 `model_cards`.
- Price observations: `data/retailer_price_observations.json` on this feature branch.
- Frontend: `assets/retailer-observations.js`; invokes Render `/api/price-observation?model_key=...` on user click, checks exact configuration, six-hour freshness and store URL allowlist.
- Snapshot claims 159 API model keys, 822 configurations, 910 retailer rows, 15,859 rejected rows. These are counts of observations, not 159 freshly verified phones.
- Snapshot was generated 19 Nov 2026; old observations must not be advertised as current.

## Deterministic catalogue-key reconciliation
232 catalogue model keys; union of `models`, `brand_store_prices` and `historical_manufacturer_prices` covers **160 catalogue keys** and leaves **72 without any matching entry** in this branch's JSON. This is not the same as the previous 56 count: that number included workbook/external dated evidence not present in this file. Do not silently equate the two counts.

## First ten catalogue keys without matching JSON entries
1. apple|iphone 13
2. apple|iphone 15 256gb
3. apple|iphone 15 512gb
4. apple|iphone 16e iphone se 4
5. apple|iphone se 2022 iphone se 3
6. cmf|phone 1
7. google|pixel 7a
8. google|pixel 9
9. google|pixel 9 pro
10. google|pixel 9 pro xl

## Engine and release findings
1. The browser's live API lookup is **user-triggered**, not proof of automatic six-hour updates.
2. The front-end uses six-hour freshness checks; saved snapshot rows can remain visible with a stale label.
3. Manufacturer launch prices are historical, not current offers, and must never enter budget filtering.
4. Live Render API's credential status, daily quota and results for these 10 keys are **not verified by this audit**; no paid API invocation has been made.
5. Before adding any price: confirm exact Indian SKU, RAM/storage, in-stock price, official store/retailer deep link, timestamp, and no conditional exchange/bank offer; otherwise mark unavailable.
6. No price has been invented or inserted. No deployment has been performed.

## Next execution
Use the existing Render API's `/api/price-observation` endpoint for each exact key with rate limits; check original retailer and manufacturer product pages, and write only evidenced current-price observations. Retain historical launch prices separately.
