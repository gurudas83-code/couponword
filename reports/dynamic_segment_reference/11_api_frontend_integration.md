# API/frontend integration receipt

## Trace

`Query → shopping_api.recommend → run_pipeline → apply_response_contract → _dynamic_reference_contract → build_budget_benchmark/build_budget_reference_snapshots → dynamic_reference JSON → app.js dynamic reference section`

The previous gap was in `python/api_contract.py`: it always replaced camera, battery and gaming sections with unavailable placeholders and never invoked `budget_benchmark.py`. The contract now preserves supplied specialist sections, adds a truthful Performance section, and attaches `dynamic_reference` using the existing benchmark adapter.

The backend returns distinct fields for `fit_percent`, `quality_score`, `evidence_coverage_percent`, `price_status`, `purchase_cta_eligible`, `category_results` and `dynamic_reference`. The frontend displays backend values only; it does not recalculate approved weights or relative scores.

When no current exact offer is available, the response carries `LIVE_ELIGIBLE_POOL_EMPTY`, disables purchase eligibility and shows an honest incomplete reference message. Research-only reference records are explicitly labelled and cannot enable live CTAs.

The stretch block remains `DISABLED_OWNER_REVIEW` by default.
