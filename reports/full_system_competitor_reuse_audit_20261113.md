# Coupon World — Full-system / competitor / reuse audit (2026-11-13)

Scope: read-only main-branch architecture and public-page audit. **No new engine. No unverified deployment or rankings.**

## Locked user requirements
- Reuse approved Intent, Identity, Resolver, Evidence, Product DNA, Weighted Fit, Retailer and SEO modules. Do not build parallel engines or replace approved weights without reproducing a failure.
- Reference/historical price is **only a budget eligibility cap**; price contributes **0%** to Camera/Gaming/Battery/Overall capability rank and tie-breaks. Exact physical RAM/storage and regional identity remain strict.
- Distinguish research-only content from fresh verified purchasable offers. No invented prices, current stock, benchmark winners or product photos.
- Work from existing audits; baseline -> reproduce -> minimal fix -> tests -> merge -> independently verify production.

## Repository and public inventory
- GitHub main tree: 846 entries; 699 files; `python/` 157 files; `data/` 88; `reports/` 62; `products/` 105.
- `data/mobile_research_catalogue.json`: 232 `model_cards`, 235 `records`.
- `data/mobile_research_preview.json`: 10 `products`. **This is a curated preview, not a missing 222-card ingestion defect.**
- `data/retailer_offers.json`: 7 historical offers. Not proof of 7 fresh offers.
- `data/mobile_independent_test_evidence.json`: 6 models, 16 metrics (6 battery/6 gaming/4 camera), **0 ranking-eligible**, 1 held conflicting source. Manufacturer specifications are not independent performance benchmarks.
- Public homepage visibly reports 232 entries, 226 with sourced specifications, 20 practical guides, 20 TVs and 20 earbuds comparison links. The 226 is a public claim, not independently recalculated from the complete ledger in this audit.
- `index.html` loads `app.js` and `mobile-research-preview.js`. The latter explicitly says it is read-only research; shopping remains `/api/recommend`. Do not combine their result ordering or count as one activated ranker.

## Active engine map (based on source and historical phase-G audit)
1. `app.js` -> `python/shopping_api.py` -> `python/shopping_intelligence_pipeline.py` -> existing Intent/Market Discovery/Identity/Official Evidence/Signal Builder/Weighted Fit -> serialized recommendations.
2. `mobile-research-preview.js` -> `data/mobile_research_catalogue.json` -> research-only source-backed filtering and comparison. Evidence-ordering improvement merged as PR #82.
3. Existing modules `python/real_recommendation_ranker.py`, `python/recommendation_engine.py`, `python/shopping_brain.py` (if present) are legacy/alternative entry points per `reports/phase_g/01_engine_audit.md`; **do not wire them in as parallel rankers**.
4. Existing retailer modules: `python/multi_retailer_orchestrator.py`, `python/retailer_product_registry.py`, `python/retailer_offer_store.py`, `python/retail_price_evidence.py`. Existing source modules: `python/official_source_resolver.py`, `python/product_evidence_store.py`, `python/camera_evidence.py`, `python/battery_evidence.py`, `python/performance_evidence.py`.

## Important prior-work correction
`reports/phase_g/05_scoring_audit.md` already implemented a separate non-budget `quality_score` and deterministic sort. `reports/ranking_quality/RANKING_BUDGET_TRUST_FINAL.md` documents the approved formula and states price can still enter a conservative fit criterion. **Do not call this a newly discovered unfixed bug without reproducing a real budget-only ranking perturbation.** Preserve the Phase-G baseline and verify that no price effect leaks through the active pipeline and eligibility/tie-breaks.

## Competitor comparison (observed public features, not equivalent measured tests)
- Smartprix: very large phone list, rich specs, four-device comparison, prices across stores.
- 91mobiles: phone finder, device/spec/performance category scores, expert/user reviews, comparison.
- MySmartPrice: extensive catalogue, price, availability, RAM/storage/display filters.
- Coupon World differentiator: manufacturer-linked evidence, exact-variant caveats, disclosed test-unit limitations, no fake fresh-offer claims. Current disadvantages: much smaller catalogue, limited independently comparable ranking evidence, incomplete buyable retailer links, lower editorial/discovery reach and complex home navigation.
- Subjective scores should not be represented as externally benchmarked results.

## Specific remaining blockers and acceptance tests
| Priority | Blocker | Existing asset / minimum action | Acceptance |
|---|---|---|---|
| P0 | Unverified production parity | Existing `/health` revision + Pages JS; read-only verification | Pages and Render both match intended commit; query response inspected |
| P0 | Budget-only ranking invariant | Existing `test_phase_g_ranking_contract.py`, weighted fit and active route; reproduce price-only changes at same budget eligibility | Same quality rank and tie-break across different within-cap prices; no new formula |
| P0 | Cross-path search confusion | Existing app.js/research JS, query corpus and QA | Exact variant, brand exclusion, under-cap and 5G give correctly scoped, labelled results |
| P1 | Evidence-to-ranking gap | Existing independent-test ledger and verification modules | Only same-protocol, India-compatible test rows marked ranking eligible; do not auto-promote 16 rows |
| P1 | Retailer exact-link gap | Existing retailer registry/adapters | Verified exact SKU links; date/source; no invented offer or stock; Amazon tag validated |
| P1 | Search discoverability | Existing sitemap/SEO scripts and GSC process | Live sitemap and representative indexed URLs verified in GSC; no indexing claim from site: search |
| P2 | TV/earbud expansion | Existing category research records | Manufacturer/source + exact model and link review before buying claims |

## Release conclusion
Architecture and research site are real; the full commercial/performance decision product is **not yet certified complete**. Avoid another engine, speculative code rewrites or unverified production claims. Next code changes should target reproducible failures in the above gates, preserving already-merged work.
