import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "python"))

from shopping_intelligence_pipeline import build_budget_presentation
from weighted_fit_engine import calculate_product_fit


class BudgetPresentationTests(unittest.TestCase):
    def item(self, product_id, price):
        return {"product_id": product_id, "price": price, "quality_score": 80}

    def test_generic_under_budget_splits_primary_and_value_without_reordering_quality(self):
        intent = {
            "category": "smartphone",
            "budget_min": None,
            "budget_max": 50000,
            "brands": [],
            "must_have": [],
        }
        result = build_budget_presentation(
            [
                self.item("near-1", 49998),
                self.item("near-2", 42000),
                self.item("value-1", 31999),
                self.item("value-2", 9099),
                self.item("over-budget", 84000),
            ],
            intent,
            "mobile under 50000",
        )
        self.assertEqual(result["mode"], "budget_band")
        self.assertEqual(result["primary_floor"], 40000)
        self.assertEqual(
            [row["product_id"] for row in result["primary_recommendations"]],
            ["near-1", "near-2"],
        )
        self.assertEqual(
            [row["product_id"] for row in result["value_recommendations"]],
            ["value-1", "value-2"],
        )
        self.assertNotIn(
            "over-budget",
            [row["product_id"] for row in result["primary_recommendations"] + result["value_recommendations"]],
        )

    def test_value_language_keeps_quality_ranked_contract(self):
        intent = {
            "category": "smartphone",
            "budget_min": None,
            "budget_max": 50000,
            "brands": [],
            "must_have": [],
        }
        result = build_budget_presentation(
            [self.item("cheap", 18000)], intent, "best value phone under 50000"
        )
        self.assertEqual(result["mode"], "quality_ranked")
        self.assertEqual(result["primary_recommendations"][0]["product_id"], "cheap")
        self.assertEqual(result["value_recommendations"], [])

    def test_hard_budget_still_rejects_reported_84000_leak(self):
        intent = {"budget_max": 50000, "hard_constraints": ["budget_max"],
                  "priority_weights": {"budget": 25, "performance": 75}}
        result = calculate_product_fit(
            {"product_id": "reported-84000", "price": 84000,
             "fit_signals": {"budget": 1, "performance": 1}},
            intent,
        )
        self.assertFalse(result["eligible"])
        self.assertTrue(any("exceeds hard budget" in reason for reason in result["hard_constraint_failures"]))


if __name__ == "__main__":
    unittest.main()
