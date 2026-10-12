import unittest

from python.shopping_intelligence_pipeline import premium_market_quality_status


class PremiumQualityGuardTests(unittest.TestCase):
    def test_gate3_budget_is_not_marked_premium_incomplete(self):
        # Pure contract check through the returned payload shape used by API.
        status, reason = premium_market_quality_status(
            {"category": "smartphone", "budget_max": 100000}, {}
        )
        self.assertEqual(status, "VERIFIED_SCOPE")
        self.assertIsNone(reason)

    def test_premium_guard_contract_is_explicit(self):
        status, reason = premium_market_quality_status(
            {"category": "smartphone", "budget_max": 120000}, {}
        )
        self.assertEqual(status, "INCOMPLETE")
        self.assertIn("best-in-market", reason)
        verified, _ = premium_market_quality_status(
            {"category": "smartphone", "budget_max": 150000},
            {"premium_market_coverage_verified": True},
        )
        self.assertEqual(verified, "VERIFIED_SCOPE")


if __name__ == "__main__":
    unittest.main()
