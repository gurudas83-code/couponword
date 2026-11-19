import tempfile
import unittest
from pathlib import Path

from scripts.build_price_evidence_coverage import (
    WIDTH, build, positive_historical_observations,
)


ROOT = Path(__file__).resolve().parent


class PriceEvidenceCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = build(ROOT)

    def test_exact_catalogue_reconciles_without_fake_prices(self):
        r = self.report
        self.assertEqual(r["summary"]["total_models"], 232)
        self.assertEqual(len(r["model_rows"]), 232)
        self.assertEqual(len(set(x["model_key"] for x in r["model_rows"])), 232)
        self.assertEqual(r["summary"]["statuses"]["WORKBOOK_DATED_REFERENCE"], 86)
        self.assertEqual(r["summary"]["statuses"]["API_HISTORICAL_VARIANT_OBSERVATION"], 43)
        self.assertEqual(r["summary"]["statuses"]["API_ONLY_NO_POSITIVE_IN_STOCK_PRICE"], 33)
        self.assertEqual(r["summary"]["statuses"]["NOT_IN_SAVED_API_OBSERVATIONS"], 70)
        self.assertEqual(r["summary"]["still_missing_positive_price_evidence"], 103)
        self.assertEqual(r["summary"]["with_any_dated_price_evidence"], 129)

    def test_nonoverlapping_five_thousand_bands_and_rank_protection(self):
        r = self.report
        self.assertEqual(WIDTH, 5000)
        self.assertEqual(len(r["budget_bands"]), 40)
        self.assertEqual(sum(x["total_with_some_dated_price_evidence"] for x in r["budget_bands"]), 129)
        self.assertEqual(len(r["verification_queue"]), 103)
        for model in r["model_rows"]:
            self.assertFalse(model["live_price_verified"])
            self.assertFalse(model["buy_eligible"])
            self.assertEqual(model["ranking_weight"], 0)
            price = model["price_reference_inr"]
            if price is None:
                self.assertIsNone(model["band_floor_inr"])
            else:
                self.assertTrue(model["band_floor_inr"] <= price < model["band_ceiling_exclusive_inr"])
                self.assertEqual(model["band_ceiling_exclusive_inr"] - model["band_floor_inr"], WIDTH)

    def test_historical_api_observation_has_exact_variant_and_source(self):
        for model in self.report["model_rows"]:
            if model["status"] == "API_HISTORICAL_VARIANT_OBSERVATION":
                variant = model["recorded_variant"]
                self.assertGreater(variant["storage_gb"], 0)
                if not model["model_key"].startswith("apple|"):
                    self.assertGreater(variant["ram_gb"], 0)
                self.assertTrue(model["source_url"].startswith("https://"))
                self.assertTrue(model["source_date"].startswith("2026-11-17"))
                self.assertFalse(model["buy_eligible"])

    def test_ineligible_stale_or_cross_variant_observations_are_excluded(self):
        good = {
            "ram_gb": 8, "storage_gb": 128, "color": "Blue",
            "pincode": "110001", "purchase_eligible": False,
            "offers": [{
                "retailer": "flipkart", "price": 15999, "availability": "in_stock",
                "observed_at": "2026-11-17T17:00:00+00:00",
                "retailer_product_id": "MOBEXACT1234",
                "product_url": "https://www.flipkart.com/-/p/-?pid=MOBEXACT1234",
            }]
        }
        self.assertEqual(len(positive_historical_observations([good], "test|phone")), 1)
        for modified in (
            {**good, "storage_gb": None},
            {**good, "ram_gb": None},
            {**good, "purchase_eligible": True},
            {**good, "offers": [{**good["offers"][0], "availability": "out_of_stock"}]},
            {**good, "offers": [{**good["offers"][0], "price": None}]},
            {**good, "offers": [{**good["offers"][0], "product_url": "http://untrusted.example/x"}]},
        ):
            self.assertEqual(positive_historical_observations([modified], "test|phone"), [])
        # No API calls are part of this offline classification.


if __name__ == "__main__":
    unittest.main()
