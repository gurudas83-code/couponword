import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "python"))

from api_contract import apply_response_contract  # noqa: E402


NOW = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)


def product(pid, price, *, source_lane="LIVE_VERIFIED_BUYABLE", capacity=5000, photo=None, cpu=None):
    return {
        "canonical_product_id": pid,
        "exact_variant_id": f"{pid}-8-128",
        "manufacturer": "Fixture",
        "brand": "Fixture",
        "model": f"Phone {pid}",
        "price": price,
        "price_verified": source_lane == "LIVE_VERIFIED_BUYABLE",
        "offer_status": "in_stock" if source_lane == "LIVE_VERIFIED_BUYABLE" else None,
        "price_fresh": source_lane == "LIVE_VERIFIED_BUYABLE",
        "source_lane": source_lane,
        "fit_signals": {
            "budget": {"match": 1, "status": "verified"},
            "battery": {"match": .8, "status": "verified"},
        },
        "verified_metrics": {
            "capacity_mah": capacity,
            **({"measured_photo_quality": photo} if photo is not None else {}),
            **({"cpu_single_core": cpu} if cpu is not None else {}),
        },
    }


class DynamicReferenceApiTests(unittest.TestCase):
    def intent(self, budget=18000):
        return {
            "budget_max": budget,
            "category": "smartphone",
            "hard_constraints": ["budget_max"],
            "priority_weights": {"budget": 20, "battery": 80},
        }

    def test_api_consumes_backend_reference_and_preserves_distinct_scores(self):
        payload = {
            "intent": self.intent(18000),
            "recommendations": [],
            "_benchmark_products": [
                product("a", 9000, capacity=6000, photo=70, cpu=500),
                product("b", 18000, capacity=5000, photo=100, cpu=700),
            ],
            "benchmark_evidence_version": "fixture-api-v1",
        }
        output = apply_response_contract(payload, "phone under 18000", now=NOW)
        reference = output["dynamic_reference"]
        self.assertEqual(reference["reference_status"], "LIVE_VERIFIED_BUYABLE")
        self.assertEqual(reference["requested_budget_inr"], 18000)
        self.assertEqual(len(reference["supported_standard_budgets_inr"]), 15)
        metrics = {row["metric_name"]: row for row in reference["requested_snapshot"]["metrics"]}
        self.assertEqual(metrics["capacity_mah"]["reference_product_id"], "a")
        self.assertEqual(metrics["capacity_mah"]["metric_reference_value"], 6000)
        self.assertEqual(metrics["measured_photo_quality"]["reference_product_id"], "b")
        self.assertEqual(metrics["measured_photo_quality"]["scores"]["b"], 100.0)
        self.assertFalse(reference["production_scoring_changed"])

    def test_exact_arbitrary_budget_and_empty_live_pool_are_honest(self):
        payload = {"intent": self.intent(25000), "recommendations": [], "_benchmark_products": []}
        output = apply_response_contract(payload, "phone under 25000", now=NOW)
        reference = output["dynamic_reference"]
        self.assertEqual(reference["reference_status"], "LIVE_ELIGIBLE_POOL_EMPTY")
        self.assertEqual(reference["requested_budget_inr"], 25000)
        self.assertFalse(reference["live_purchase_ctas_allowed"])
        self.assertEqual(reference["requested_snapshot"]["verification_status"], "LIVE_ELIGIBLE_POOL_EMPTY")

    def test_required_budget_queries_keep_exact_requested_ceiling_and_version(self):
        for budget in (10000, 20000, 30000, 50000, 100000, 150000, 18000, 25000):
            output = apply_response_contract(
                {"intent": self.intent(budget), "recommendations": [], "_benchmark_products": []},
                f"phone under {budget}",
                now=NOW,
            )
            reference = output["dynamic_reference"]
            self.assertEqual(reference["requested_budget_inr"], budget)
            self.assertEqual(reference["requested_snapshot"]["benchmark_version"], reference["benchmark_version"])
            self.assertEqual(reference["requested_snapshot"]["verification_status"], "LIVE_ELIGIBLE_POOL_EMPTY")

    def test_research_reference_never_becomes_live(self):
        research = product("research", 12000, source_lane="RESEARCH_REFERENCE_ONLY")
        research["price_verified"] = True
        research["offer_status"] = "in_stock"
        research["price_fresh"] = True
        payload = {
            "intent": self.intent(20000),
            "recommendations": [],
            "_benchmark_products": [research],
        }
        output = apply_response_contract(payload, "phone under 20000", now=NOW)
        self.assertEqual(output["dynamic_reference"]["reference_status"], "RESEARCH_REFERENCE_ONLY")
        self.assertFalse(output["dynamic_reference"]["live_purchase_ctas_allowed"])

    def test_frontend_reads_backend_fields_without_weight_recalculation(self):
        source = (Path(__file__).resolve().parent / "app.js").read_text(encoding="utf-8")
        self.assertIn("data.dynamic_reference", source)
        self.assertIn("requestedSnapshot.metrics", source)
        self.assertNotIn("relative_score *", source)


if __name__ == "__main__":
    unittest.main()
