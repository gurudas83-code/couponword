# Task 1 — active engine audit (2026-10-11)

Local active-path audit PASS; production revision consistency BLOCKED pending deployment evidence.

## Request path
`index.html` loads `/app.js?v=13`. Search handlers call `loadShoppingRecommendation`.
That function GETs `https://couponword.onrender.com/api/recommend?q=…`.
`python/shopping_api.py:recommend` scopes bare known mobile brands and invokes
`shopping_intelligence_pipeline.run_pipeline(max_candidates=15,max_results=3,live_fast=True)`.
`intent_engine.parse_query` supplies constraints/weights; `market_discovery.discover_market`
combines provider/local catalogue candidates and applies category/accessory/variant gates.
Generic budgets above15000 evaluate30 candidates; low budgets can recover up to30,
with request-local discovery/scoring reuse for10000/15000.

`_run_pipeline_once` prepares identity, resolves official/exact retailer identity,
loads verified evidence through `product_evidence_store` or extracts official specifications,
obtains exact structured/recent verified prices through `retail_price_evidence`, builds
signals with `product_fit_signal_builder`, and scores with `weighted_fit_engine`.
Canonical catalogue admission is required before recommendation. Eligible records are
sorted by fit, evidence coverage, partial-model pin and stable listing ID; model families
are deduplicated. Serializer builds multi-retailer output and diagnostics. Frontend preserves
returned order and pairs selected offer price with its retailer URL. It does not independently rank.

Legacy `shopping_brain`, `shopping_decision_engine`, `recommendation_engine` and
`real_recommendation_ranker` are not imported by this active pipeline/route. They were not removed.

## State and caps
- Permanent identity/catalogue: coupons.json and retailer_product_registry.json.
- Reviewed deployment evidence: phase_e_release_evidence.json; runtime evidence cache:
  verified_product_evidence_cache.json. These are evidence stores, not additional rankers.
- Price cache TTL6hours; discovery cache TTL24hours. Candidate snapshot policy catalogue-breadth-v3.
- Discovery cap30 is a recall boundary, not proof of complete market coverage.
- Payload exposes discovered, identity_prepared, identity_verified, official_verified,
  evidence_ready, fit_scored, qualifying_50_plus_raw, qualifying_unique_models and returned counts;
  failures/failure_summary and fit_diagnostics explain rejection stages. These stages overlap;
  subtracting adjacent counts is not a valid exclusive rejection breakdown.
- Existing saved API evidence: 60k returned2; 100k returned3. Signature excluded when current
  exact price was unavailable. See workspace outputs/failed-price-reuse/scoring-api.json.
- Confirmed ranking concern: fit is raw performance multiplied by coverage, while budget
  contributes full credit to every affordable phone. Task5 must separate these concepts.

## Version defect and minimal correction
Before: /health returned status/service only, so a successful health response could not
identify Render's deployed commit. After: revision exposes only a valid40-character
RENDER_GIT_COMMIT, otherwise null. No local hash is guessed; no deployment initiated.
Read-only GitHub remote check: main5167712b369c81ab85779819763eee6e9b90a831.
Local audit started at d30d2a6 (four commits ahead). Render exact SHA remains UNVERIFIED.
No checked-in Render start configuration was found in the inspected workflow paths;
dashboard start command cannot be certified from source alone.

## Validation
7 tests PASS: test_phase_g_active_route, test_phase_e_budget_breadth,
test_phase_e_recovery_reuse. Route regression verifies exact active call parameters,
unchanged response/order and valid/absent/invalid revision behavior. Prior health lacked
revision; the new revision assertion would fail before this change. No live quality PASS claimed.
All unrelated data/caches/backups, including pending Signature admission, preserved.
