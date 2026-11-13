# Coupon World — Reuse-first integration audit (2026-11-13)

## Scope
Read-only architecture/data review of the current GitHub main branch. This is **not** a production deployment or runtime benchmark.

## Confirmed existing assets
- `python/shopping_intelligence_pipeline.py`: active shopping candidate/evidence pipeline per `reports/phase_g/01_engine_audit.md`.
- `python/weighted_fit_engine.py`: weighted fit and hard constraint logic.
- `python/intent_engine.py`, `python/product_fit_signal_builder.py`, `python/product_evidence_store.py`: intent, signals and evidence.
- `python/camera_evidence.py`, `python/battery_evidence.py`, `python/performance_evidence.py`: domain evidence modules.
- `python/multi_retailer_orchestrator.py` and `python/retailer_product_registry.py`: retailer plumbing.
- `mobile-research-preview.js`: independent browser research sorting/filtering; PR #82 now prefers sourced fields.
- `index.html` loads both `/app.js?v=first-load-20261107` and `/mobile-research-preview.js?v=p1-20261107`. These are separate paths; do not assume they share one ranking result.

## Critical verified limitation
`data/mobile_independent_test_evidence.json` (checked_at 2026-11-04): 6 model entries, 16 metrics (6 battery, 6 gaming, 4 camera), **0 ranking_eligible=true**. There is 1 held source due to conflicting data. Evidence must not be promoted into verified performance winners without protocol/variant comparability.

## Historical architecture finding
`reports/phase_g/01_engine_audit.md` traces frontend shopping requests through `/api/recommend` -> `python/shopping_api.py` -> `shopping_intelligence_pipeline` -> `weighted_fit_engine`. It explicitly says legacy `real_recommendation_ranker` and `recommendation_engine` are not imported by the active route. Reusing these as new parallel engines would introduce duplication.

## Policy checks to complete before activation
1. **Price**: historical weighted-fit hard constraint reads `product.price` and rejects unknown price; inspect active path to confirm current policy permits dated/reference price **for budget eligibility only**, never ranking.
2. **Research-vs-shopping integration**: trace browser research answers separately from shopping API responses. Verify no double-ranking or contradictory claims.
3. **Evidence ledger**: inventory all official spec and independent benchmark rows by exact India variant, protocol, source URL, timestamp and ranking eligibility; do not equate 226 sourced-spec cards with 226 independently performance-tested variants.
4. **Retailers**: verify exact variant matching, 3-retailer reference links, affiliate tag, and no fabricated live offer/stock.
5. **Production**: confirm Pages JS commit and Render API revision independently, then run live query tests.

## Decision
**REUSE existing engines; do not create another ranker.** Keep measured performance winners disabled until a defensible comparable cohort exists. Expose useful evidence-backed research results with explicit confidence/limitations meanwhile.

## Release gates
- Unit/contract tests: budget cap does not alter ranking weights; missing reference price cannot silently qualify a budget recommendation.
- Cross-path consistency tests: same exact variant, 5G/OIS/brand/budget conditions produce compatible research and shopping answers.
- Performance-ranking test: unverified or incompatible independent test rows never enter winner calculations.
- GitHub CI all green, followed by independent live production verification.

Status: **AUDIT DOCUMENTED; integration changes and deployment not yet claimed.**
