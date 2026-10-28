# Dynamic reference baseline

Status: `RESEARCH_REFERENCE_ONLY`; no current authorized retailer pool was promoted to live.

The isolated adapter is `python/budget_benchmark.py`:

- `STANDARD_BUDGET_CEILINGS` at line 17 defines the 15 cumulative ceilings.
- `normalize_budget_ceiling` preserves arbitrary exact ceilings without upward rounding.
- `eligible_population` and `_offer_is_verified_current` preserve the existing current-price, freshness, stock, identity and fit gates.
- `_metric_snapshot` computes independent maxima/minima and direction-aware relative scores.
- `build_budget_reference_snapshots` creates one snapshot per ceiling.
- `build_metric_reference_matrix` flattens provenance and sample counts.

Approved scoring remains in `python/weighted_fit_engine.py`: `MIN_FIT_PERCENT = 50` (line 22), `calculate_product_fit` (line 221), and `rank_recommendations` (line 384). No weights or thresholds were changed. The dynamic reference value is an input trace only; it does not replace the weighted fit formula.

Shared live gates remain in `python/shared_candidate_pool.py`: six-hour freshness at line 21, exact offer checks in `_offer_is_eligible`, and category ranking in `rank_shared_pool_categories`.

Research-only and live-verified outputs are separate. With no authorized fresh offers in the current checkout, all live matrices remain `UNAVAILABLE`.
