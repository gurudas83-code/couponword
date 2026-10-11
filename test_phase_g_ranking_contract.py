import random
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "python"))
from weighted_fit_engine import calculate_product_fit, recommendation_sort_key


class RankingContractTests(unittest.TestCase):
    def product(self, ident, capability, price=12000):
        return {"product_id": ident, "price": price, "fit_signals": {
            "budget": 1, "performance": capability, "camera": capability, "display": capability}}

    def test_budget_does_not_count_as_capability(self):
        intent = {"priority_weights": {"budget": 40, "performance": 20, "camera": 20, "display": 20}}
        cheap = calculate_product_fit(self.product("cheap", .5), intent)
        premium = calculate_product_fit(self.product("premium", .9, 90000), intent)
        self.assertEqual(cheap["quality_score"], 50)
        self.assertEqual(premium["quality_score"], 90)
        self.assertLess(recommendation_sort_key(premium, "premium"), recommendation_sort_key(cheap, "cheap"))

    def test_unknown_is_separate_and_does_not_relax_eligibility(self):
        intent = {"priority_weights": {"budget": 24, "performance": 20, "camera": 28, "display": 28}}
        product = self.product("sparse", 1)
        product["fit_signals"].update(camera=None, display=None)
        score = calculate_product_fit(product, intent)
        self.assertEqual(score["quality_score"], 100)
        self.assertLess(score["quality_evidence_coverage_percent"], 50)
        self.assertFalse(score["eligible"])

    def test_twenty_frozen_repetitions_across_budgets_and_priorities(self):
        for budget in (10000,12000,20000,30000,40000,50000,120000,150000):
            for priority in ("performance", "camera", "battery"):
                intent = {"budget_max": budget, "priority_weights": {"budget": 25, priority: 75}}
                records = []
                for ident in ("c", "a", "b"):
                    product = {"product_id": ident, "price": budget, "fit_signals": {"budget": 1, priority: .8}}
                    records.append((ident, calculate_product_fit(product, intent)))
                baseline = sorted(records, key=lambda row: recommendation_sort_key(row[1], row[0]))
                for seed in range(20):
                    shuffled = records.copy(); random.Random(seed).shuffle(shuffled)
                    self.assertEqual(sorted(shuffled, key=lambda row: recommendation_sort_key(row[1], row[0])), baseline)


if __name__ == "__main__":
    unittest.main()
