"""Three initial picks must not suppress the bounded higher-budget pool."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent / "python"))
import shopping_intelligence_pipeline as pipeline

class BudgetBreadthTests(unittest.TestCase):
    def test_three_initial_picks_do_not_hide_better_reserve_candidate(self):
        # Discovery order is frozen: the better candidate sits beyond slot 15.
        candidates = [{"asin": str(i), "fit": 51} for i in range(29)]
        candidates.append({"asin": "better-exact-listing", "fit": 62})
        def discover(**kw):
            return {"candidates": candidates[:kw["max_candidates"]]}
        def score(query, limit, results, fast, **kw):
            rows = sorted(kw["_discovery"]["candidates"], key=lambda r: -r["fit"])
            return {"intent": pipeline.parse_query(query), "recommendations": rows[:3], "timings": {}}
        for budget in (20000, 30000, 40000, 50000, 120000):
            with self.subTest(budget=budget), patch.object(pipeline, "discover_market", side_effect=discover) as discovery, patch.object(pipeline, "_run_pipeline_once", side_effect=score) as scoring:
                result = pipeline.run_pipeline(f"mobile under {budget}", max_results=3, live_fast=True)
                self.assertEqual(result["recommendations"][0]["asin"], "better-exact-listing")
                self.assertEqual(discovery.call_count, 1)
                self.assertEqual(scoring.call_count, 1)
                self.assertEqual(discovery.call_args.kwargs["max_candidates"], 30)

    def test_low_budget_and_brand_queries_keep_existing_initial_bound(self):
        for query in ("mobile under 10000", "mobile under 15000", "Samsung phone under 50000"):
            with self.subTest(query=query), patch.object(pipeline, "discover_market", return_value={}) as discovery, patch.object(pipeline, "_run_pipeline_once", return_value={"intent":pipeline.parse_query(query), "recommendations":[{}, {}, {}], "timings":{}}):
                pipeline.run_pipeline(query, max_results=3, live_fast=True)
                self.assertEqual(discovery.call_args.kwargs["max_candidates"],15)

if __name__ == "__main__":
    unittest.main()
