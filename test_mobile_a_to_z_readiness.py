"""Release-readiness assertions; all missing evidence remains explicitly missing."""
import unittest
from datetime import datetime, timezone

from scripts.mobile_a_to_z_readiness import build


class MobileReadinessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = build(as_of=datetime(2026, 11, 21, 12, 0, tzinfo=timezone.utc))

    def test_reconciles_core_registry_and_623_query_audit(self):
        r = self.report
        t = r["totals"]
        self.assertEqual(t["core_models"], 232)
        self.assertEqual(len(r["models"]), 232)
        self.assertEqual(len({x["model_key"] for x in r["models"]}), 232)
        self.assertEqual(t["previous_incomplete_queries"], 623)
        self.assertEqual(sum(t["previous_query_gaps"].values()), 623)
        self.assertEqual(t["historical_price_missing"] + t["historical_price_evidence"], 232)

    def test_never_promotes_historical_prices_to_checkout_offers(self):
        r = self.report
        self.assertEqual(r["totals"]["authorized_live_checkout_prices_verified_by_this_audit"], 0)
        self.assertTrue(all(x["authorized_current_offer_verified"] is False for x in r["models"]))
        self.assertTrue(all("CURRENT_AUTHORIZED_EXACT_SKU_OFFER" in x["missing_gates"]
                            for x in r["models"]))
        self.assertEqual(len(r["work_queues"]["price_missing"]),
                         r["totals"]["historical_price_missing"])

    def test_model_evidence_and_limited_licenses_are_audited(self):
        r = self.report
        self.assertEqual(r["totals"]["exact_licensed_photo_verified"] +
                         r["totals"]["photo_review_remaining"], 232)
        self.assertEqual(r["totals"]["manufacturer_or_identity_review_remaining"],
                         len(r["work_queues"]["manufacturer_review"]))
        self.assertEqual(r["totals"]["exact_india_variant_review_remaining"],
                         len(r["work_queues"]["india_variant_missing"]))

    def test_api_category_separation_and_stale_observations(self):
        r = self.report
        t = r["totals"]
        self.assertGreater(t["non_phone_observation_ids"], 0)
        self.assertLessEqual(t["api_observed_phone_models"], 232)
        self.assertEqual(t["observations_currently_inside_6h_window"], 0)
        self.assertTrue(all(x["api_observation_offers"] >= 0 for x in r["models"]))


if __name__ == "__main__":
    unittest.main()
