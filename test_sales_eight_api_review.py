"""No-charge unit tests for the private missing-six API audit review."""
import unittest
from scripts.sales_eight_api_review import REMAINING_SIX, review


def fixture():
    return {
        "mode": "PRIVATE_RESEARCH_OBSERVATIONS",
        "calls_attempted": 6,
        "records": [
            {"audit_id": key, "status": "NO_STRICT_MODEL_CANDIDATE", "candidates": []}
            for key in REMAINING_SIX
        ],
    }


class ReviewTests(unittest.TestCase):
    def test_no_price_or_offer_promotion(self):
        value = review(fixture())
        self.assertEqual(value["models_in_scope"], 6)
        self.assertEqual(value["public_prices_published"], 0)
        self.assertEqual(value["canonical_models_imported"], 0)

    def test_rejects_false_public_verified_candidate(self):
        data = fixture()
        data["records"][0]["candidates"] = [{
            "publishable": True,
            "exact_canonical_variant_verified": False,
            "image_publish_eligible": False,
        }]
        with self.assertRaises(ValueError):
            review(data)

    def test_rejects_duplicate(self):
        data = fixture()
        data["records"][1]["audit_id"] = data["records"][0]["audit_id"]
        with self.assertRaises(ValueError):
            review(data)

    def test_rejects_budget_overrun(self):
        data = fixture()
        data["calls_attempted"] = 7
        with self.assertRaises(ValueError):
            review(data)


if __name__ == "__main__":
    unittest.main()
