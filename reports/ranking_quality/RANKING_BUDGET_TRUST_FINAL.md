# Coupon-World ranking, budget and trust report

Date: 2026-10-18
Branch: `ranking-quality-repair`
Base: `c29d5646da81a330de52f79e6eae56bce8c21148`
Push/deploy: **not performed**

## A. Actual existing ranking formula

The existing smartphone pipeline remains the authoritative scoring path. The fix in this branch does not alter its weights, thresholds, identity checks or score arithmetic.

| Component | Implementation | Evidence / gate | Source |
|---|---|---|---|
| Smartphone priorities | Initial weights: budget 20, battery 15, display 15, ease 10, camera 10, performance 10, software support 10, connectivity 10; weights are normalized and explicit hard-budget queries raise the budget weight before normalization. | Parsed intent and priority text can adjust weights; unknown signals remain unknown. | `python/intent_engine.py:975-981`, `942-964`, `1144-1428` |
| Criterion match | Each signal is clamped to 0..1. Weighted points are `weight × match`. | Numeric/dict signals only; absent or unverified evidence is unknown. | `python/weighted_fit_engine.py:46-81`, `288-318` |
| Raw fit | `100 × known weighted points / known weight`. | It measures only evidenced criteria. | `python/weighted_fit_engine.py:328-331` |
| Evidence coverage | `100 × known weight / total weight`. | Eligibility requires at least 50% coverage. | `python/weighted_fit_engine.py:335-353` |
| Fit shown to the shopper | `raw_fit × evidence coverage / 100`. | Eligibility also requires fit ≥ 50 and no hard failure. | `python/weighted_fit_engine.py:337-356` |
| Quality score | Weighted capability score excluding the budget criterion. | Budget is a hard constraint, not a capability bonus. | `python/weighted_fit_engine.py:358-368` |
| Ranking | Descending quality score, then quality evidence coverage, fit, and stable identity. | No price-floor, affiliate or random filler tie-break. | `python/weighted_fit_engine.py:383-391`; `python/shopping_intelligence_pipeline.py:2844-2849` |
| Identity and offers | Canonical catalogue ownership, exact physical variant, official evidence and fresh valid offer are checked before recommendation admission. | No unknown/stale/over-budget offer can become a recommendation. | `python/shopping_intelligence_pipeline.py:1793-1817`, `python/weighted_fit_engine.py:84-178` |

Answers to the key questions: the displayed score is out of 100; generic smartphone weights give battery 15, display 15, camera 10 and performance/gaming 10 before normalization; RAM/storage receive points when explicitly required by the intent; software support receives 10; price affects the budget hard gate and the budget criterion, while `quality_score` excludes budget; proximity to the budget previously affected neither sort nor selection; brand reputation is not a hidden score; confidence comes from evidence coverage; missing specifications lower coverage and can make a record ineligible; preference text changes parsed priority weights; ties use deterministic identity; the pipeline never forces three eligible products; and API and frontend consume the same serialized recommendation payload.

## B. ₹50,000 failure root cause

The approved frozen Phase-E receipt (`reports/phase_e/final_certification.md`) showed:

| Previous ranked result | Exact variant | Verified price | Fit | Why it was selected |
|---|---|---:|---:|---|
| Samsung Galaxy A56 5G | 8GB/128GB | ₹31,999 | 62 | Highest quality among that frozen eligible pool |
| Lava Bold N2 Lite | 3GB/64GB | ₹9,099 | 51 | Passed the same hard budget/evidence/fit gates |
| Lava Virat V1 | 4GB/64GB | ₹9,889 | 50 | Passed the same hard budget/evidence/fit gates |

This was a **selection/presentation policy gap**, not a hard-budget defect: the budget gate correctly rejects prices above the maximum, but the sort key did not distinguish an upper-band primary pick from a much cheaper value alternative. The frozen receipt did not reproduce a verified ₹84,000 recommendation. A controlled fit test now proves a ₹84,000 offer is rejected with `Price 84000 exceeds hard budget limit 50000`. If a live page ever displays that price, the remaining investigation must trace the exact API payload/cache; it is not admitted by the current hard gate.

The current local working-tree replay also contains dirty, non-release price/evidence caches and therefore is not used as release evidence. Its frozen catalogue replay remains deterministic and shows the new section split. No research seed was promoted and no score/threshold was changed.

## C. Before and after results

The legacy `recommendations` array is preserved for API compatibility and still contains the quality-ranked eligible pool. The new `recommendation_sections` fields and the frontend presentation separate the primary band from value alternatives.

For a generic `mobile under B` query, primary band is `0.80 × B ≤ verified price ≤ B`; the value section is verified price below that floor. Explicit ranges, exact-model queries and “cheap/value” intent keep the quality-ranked presentation because their intent is different.

| Query | Before | After primary section | After value section | Evidence status |
|---|---|---|---|---|
| under ₹20k | Bold N2 Lite, Virat V1 (mixed list) | none in the ₹16k–₹20k band | Bold N2 Lite ₹9,099; Virat V1 ₹9,889 | verified frozen rows; primary coverage gap |
| under ₹30k | Bold N2 Lite, Virat V1 | none in ₹24k–₹30k | Bold N2 Lite; Virat V1 | verified frozen rows; primary coverage gap |
| under ₹40k | A56, Bold N2 Lite, Virat V1 | A56 ₹31,999 | Bold N2 Lite; Virat V1 | verified frozen rows |
| under ₹50k | A56, Bold N2 Lite, Virat V1 | A56 ₹31,999 | Bold N2 Lite; Virat V1 | verified frozen rows |
| under ₹60k | no approved upper-band evidence in the historical receipt | none in ₹48k–₹60k from this frozen pool | A56, Bold N2 Lite, Virat V1 | coverage gap; no fabricated candidate |

A controlled presentation replay with the same three approved rows returned the same primary/value membership on repeated execution. The current catalogue-mode run executed 1/1 and matched deterministically 1/1; its legacy top three were A36 ₹26,399, Redmi Note 17 Pro Max ₹49,998 and A56 ₹31,999, while the primary section contained only the ₹49,998 row and the value section contained the lower priced rows. Those prices came from the local dirty cache and are explicitly **not** a release or live-market claim.

## D. Customer explanation

For `mobile under 50000`, the page now says **“Top Phones Between ₹40,000 and ₹50,000”** and shows only verified candidates in that band. It then says **“Best Value Phones Below ₹40,000”** for cheaper verified alternatives. Each card keeps exact variant, current offer status, score trace, evidence coverage, source and last-checked time. If the primary band has fewer than three verified candidates, the page says so instead of filling slots with unrelated cheaper phones.

## E. Coverage funnel (current working tree, read-only counts)

- Research-seed rows: **187** (`data/mobile_universe_priority_126.json`); publish-eligible seeds: **0**.
- Product catalogue: **105** rows, **41** mobile/phone rows (`coupons.json`).
- Canonical retailer registry: **37** product keys (`data/retailer_product_registry.json`).
- Official evidence cache: **8** record keys (`data/verified_product_evidence_cache.json`).
- Retailer offer store: **7** rows (`data/retailer_offers.json`); none is a fresh in-stock six-hour offer in the checked store (the newest shown observation is 2026-08-28 and one row is out of stock).
- Fresh-price-qualified, rankable candidates therefore depend on the separate frozen/dirty runtime cache and are not durable release data. This is a coverage/operations blocker, not a reason to relax eligibility.

## F. Tests

- New budget-band and hard-budget regression: **3/3 PASS**.
- Focused ranking, parser, identity, evidence, Gate-3, frontend, mobile-page and security checks: **42/42 PASS**.
- JavaScript syntax (`node --check app.js`): **PASS**.
- Python compilation for modified modules: **PASS**.
- Frozen catalogue replay for `mobile under 50000`: **1 executed, 1 result, 1/1 deterministic match, 0 technical failures**.
- Existing offline pilot `mobile under 10000`: **FIXTURE_GAP** because the original version-matched discovery snapshot is absent from the preserved local research cache. This is the known historical fixture limitation, not a scoring failure; it remains visible and was not skipped or weakened.

## G. Files modified

- `python/shopping_intelligence_pipeline.py`: added the auditable 80% primary/value presentation layer and serialized section fields; existing ranking and gates are unchanged.
- `phase_e_offline_certification.py`: includes primary/value membership in the existing semantic determinism comparison.
- `app.js`: renders primary and value sections while preserving existing card/security/retailer rendering.
- `style.css`: minimal section headings and separation styles.
- `test_phase_g_budget_presentation.py`: focused hard-budget and presentation regressions.
- `reports/ranking_quality/RANKING_BUDGET_TRUST_FINAL.md`: this report.

Dirty `data/retail_price_cache.json`, `data/verified_product_evidence_cache.json`, `data/runtime_shopping_intelligence.json`, `data/market_discovery_cache.json` and `data/official_sitemap_cache.json` were preserved and are excluded from the release commit.

## H. Open issues

1. **Coverage/operations:** current durable offer evidence is not continuously fresh, so the site cannot claim complete market coverage for every budget. A permitted refresh process and persistent authoritative store remain operational work.
2. **Historical fixture:** the old three-result fixture remains a visible FAIL/FIXTURE_GAP; its owner-approved genuine successor remains the applicable regression.
3. **₹84k report:** not reproduced in the verified frozen payload. Exact live API evidence is required before assigning a second root cause.
4. **Deployment:** this branch has not been pushed or deployed; live Render/Pages smoke verification is unverified.

## I. Final status

| Gate | Result |
|---|---|
| Current formula identified | PASS |
| ₹50k hard-budget correctness | PASS (controlled ₹84k rejection) |
| Price-band grouping | PASS locally |
| Customer explanations | PASS locally; live rendering unverified |
| Exact variant safety | PASS in focused regressions |
| Price freshness | PASS as a rejection gate; durable refresh coverage incomplete |
| Determinism | PASS for the frozen 1/1 replay and focused repeated tests |
| Retailer integration | PASS in existing focused tests; no fresh Croma offer claimed |
| Security regression | PASS in focused tests |
| Real market coverage | PARTIAL / INCOMPLETE |
| Live deployment | NOT PERFORMED |

**FINAL QUALITY VERDICT: CONDITIONAL.** The reproduced ranking defect is repaired at the presentation layer without changing the authoritative score or gates. Production release remains blocked by durable offer freshness, the unrecoverable historical fixture and absent live smoke verification.

Local branch: `ranking-quality-repair` (isolated worktree). No push or deploy was performed.