# P0 recommendation API timeout root-cause fix — 2026-10-25

## Decision

`API_TIMEOUT_ROOT_CAUSE_FIXED_LOCALLY`

The browser acceptance blocker had two reproduced causes:

1. When the configured Amazon provider reported `api_available = False`, the discovery fallback still invoked the Amazon search-card scraper. The exact-price path then fetched Amazon product pages for discovered candidates. Those unauthorized external calls caused the old local request to remain pending and exceeded a 5-second client window.
2. The local frontend origin was not present in the backend CORS allow-list, so the browser displayed `Failed to fetch` even after the API itself became responsive.

## Focused changes

- `python/market_discovery.py`: skip Amazon search-card calls when the configured authorized provider is unavailable; preserve the lane when the provider is available. The compatibility fallback used by isolated AST tests remains unchanged.
- `python/retail_price_evidence.py`: skip current Amazon page retrieval when the authorized provider is unavailable; recent verified cache behavior remains unchanged.
- `python/shopping_api.py`: allow only exact local E2E origins (`http://127.0.0.1:4173` and `http://localhost:4173`) in addition to the production origin; no wildcard or credentialed CORS.
- `app.js`: include unavailable Performance in the specialist status and show the exact dynamic reference status code in the unavailable label.
- `test_recommendation_timeout_guard.py`: focused provider-disabled, price-fetch, CORS, and frontend-status regressions.
- `test_phase_g_price_timestamp.py`: explicitly marks mocked page-fetch cases as provider-authorized test fixtures; assertions are unchanged.

## Measurements

Before fix:

- `best phone under 10000`: direct local request exceeded a 5-second bounded client timeout; browser remained at `Finding the best matches…`.
- `best phone under 20000`: same pending behavior under the provider-disabled retry.

After fix, with `TAVILY_API_KEY` removed and the existing provider-disabled configuration:

| Query | HTTP | Client duration | Pipeline total | Dynamic reference | Recommendations | CTA allowed |
|---|---:|---:|---:|---|---:|---|
| best phone under 10000 | 200 | 3344 ms | 2.051 s | LIVE_ELIGIBLE_POOL_EMPTY | 3 research-only | false |
| best phone under 20000 | 200 | 1482 ms | 1.385 s | LIVE_ELIGIBLE_POOL_EMPTY | 3 research-only | false |
| best phone under 50000 | 200 | 1840 ms | 1.699 s | LIVE_ELIGIBLE_POOL_EMPTY | 3 research-only | false |
| best phone under 100000 | 200 | 1793 ms | 1.758 s | LIVE_ELIGIBLE_POOL_EMPTY | 3 research-only | false |
| best phone under 18000 | 200 | 1347 ms | 1.297 s | LIVE_ELIGIBLE_POOL_EMPTY | 3 research-only | false |

The first post-fix request is slower because it warms the local discovery path; subsequent requests are below the previous 5-second client budget. No current price, stock, or buyable offer was created.

## Browser verification

After the exact local CORS fix, the permitted browser received the API response. The observed UI showed recommendation cards with `CURRENT OFFER UNAVAILABLE`, no purchase CTA, specialist unavailable messaging, and the dynamic benchmark block:

- `Live reference unavailable (LIVE_ELIGIBLE_POOL_EMPTY)`
- requested budget `₹10000`
- benchmark version `budget-relative-v2`
- no comparable verified metric reference

The browser no longer remained indefinitely at `Finding the best matches…`. Exact viewport overrides were not exposed by the permitted browser surface, so width-specific acceptance remains unverified.

## Regression results

- Focused affected suite: **60 PASS, 0 FAIL**.
- Full discovered suite: **388 tests: 385 PASS, 3 FAIL, 2 skipped**.
- The three remaining failures are preserved known/fixture issues, not caused by this fix:
  - `test_phase_e_offline_certification.py::OfflineCertificationHarnessTests::test_existing_snapshot_reaches_real_pipeline` — historical snapshot fixture reports `executed=0`; the approved catalogue-mode successor passes. Classified `FIXTURE_GAP`.
  - `test_phase_g_active_route.py::ActiveRouteTests::test_route_preserves_pipeline_order_and_contract` — test expects the pre-Issue-17 raw payload, while the approved route now adds the additive `issue17-v1` contract. Classified `STALE_TEST_EXPECTATION`.
  - `test_phase_g_frontend_offer.py::FrontendOfferTests::test_display_price_url_variant_and_time_share_one_source` — isolated JavaScript slice starts after the variable declarations it consumes (`hasExplicitOfferContract`). Classified `TEST_HARNESS_SLICE_ISSUE`.
- Two skips remain unchanged: optional dependency/fixture skips from the existing suite.
- Deterministic replay: **50/50 PASS**.
- JavaScript syntax: **PASS**.

## Safety and release state

- Approved scoring weights and eligibility thresholds: unchanged.
- Exact variant and six-hour price rules: unchanged.
- Research-only records were not promoted to live offers.
- Production data, caches, scheduler, protected branches, and deployment: unchanged.
- Local dirty data/cache and historical untracked reports were preserved and not staged.
- Browser viewport acceptance: **PARTIAL / BLOCKED for exact widths**.
- Real retailer blockers remain: Amazon authorized API unavailable locally, Flipkart live access absent, Croma connector absent, and fresh verified buyable offers remain zero.
