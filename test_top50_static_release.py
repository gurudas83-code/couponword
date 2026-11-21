"""Release tests: 232 crawlable phone cards, Top50 queue, safe affiliate checks."""
from __future__ import annotations
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from python import top50_affiliate_checks as affiliate
from scripts.verify_top50_affiliate import audit

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"


class Top50StaticReleaseTests(unittest.TestCase):
    def test_full_232_models_are_in_initial_html(self):
        page = (PUBLIC / "index.html").read_text(encoding="utf-8")
        data = json.loads((PUBLIC / "data/mobile_research_catalogue.json").read_text(encoding="utf-8"))
        self.assertIn('id="mobileResearchCatalogue"', page)
        self.assertNotIn('id="mobileResearchCatalogue" aria-labelledby="mobileResearchCatalogueTitle" hidden', page)
        self.assertEqual(page.count('data-static-mobile-model='), 232)
        self.assertEqual(len(data["model_cards"]), 232)
        self.assertNotIn("<!-- STATIC_232_PHONE_CARDS -->", page)
        self.assertIn("Specifications require further source review", page)

    def test_top50_are_unique_historical_priorities_not_live_offers(self):
        queue = json.loads((PUBLIC / "data/top50_sku_research_queue.json").read_text(encoding="utf-8"))
        catalogue = json.loads((PUBLIC / "data/mobile_research_catalogue.json").read_text(encoding="utf-8"))
        items = queue["products"]
        known = {card["model_key"] for card in catalogue["model_cards"]}
        self.assertEqual(len(items), 50)
        self.assertEqual(len({row["model_key"] for row in items}), 50)
        self.assertTrue(all(row["model_key"] in known for row in items))
        self.assertTrue(all(row["current_verified_price_inr"] is None for row in items))
        self.assertTrue(all(row["current_stock"] is None for row in items))
        self.assertTrue(all(row["exact_retailer_sku_status"] == "NOT_VERIFIED" for row in items))

    def test_existing_shopping_offer_gate_not_edited(self):
        backend = (ROOT / "python/shopping_api.py").read_text(encoding="utf-8")
        source = (ROOT / "mobile-research-preview.js").read_text(encoding="utf-8")
        frontend = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("NO_CURRENT_VERIFIED_OFFER", backend)
        self.assertIn("researchTopThreeEligible", source)
        self.assertIn("Research-Verified Top-3", source)
        self.assertIn("retailer stock observation", source.lower())
        self.assertIn("research.submit(rankingQueryWithoutCount(query), {top3: true})", frontend)
        self.assertNotIn("catalogueSection.hidden = true", source)
        self.assertIn("data-static-mobile-model", source)

    def test_top50_unmapped_never_calls_providers(self):
        queue = json.loads((PUBLIC / "data/top50_sku_research_queue.json").read_text(encoding="utf-8"))
        mapping = {"mode": "REVIEWED_TOP50_VARIANT_TO_RETAILER_SKU", "records": []}
        with patch("scripts.verify_top50_affiliate.amazon_get_item", side_effect=AssertionError("Unapproved call")), \
             patch("scripts.verify_top50_affiliate.flipkart_get_product", side_effect=AssertionError("Unapproved call")):
            report = audit(queue, mapping, live=True, limit=10)
        self.assertEqual(report["live_provider_requests"], 0)
        self.assertEqual(report["unmapped_model_count"], 50)
        self.assertEqual(report["results"], [])

    def test_unapproved_mapping_is_blocked(self):
        queue = json.loads((PUBLIC / "data/top50_sku_research_queue.json").read_text(encoding="utf-8"))
        first = queue["products"][0]
        mapping = {"mode": "REVIEWED_TOP50_VARIANT_TO_RETAILER_SKU",
                   "records": [{"model_key": first["model_key"], "retailer": "amazon",
                                "retailer_product_id": "B0TEST1234",
                                "variant": first["variant_to_check"], "review_status": "NOT_APPROVED"}]}
        with self.assertRaisesRegex(ValueError, "approved"):
            audit(queue, mapping, live=True)

    @patch.dict("os.environ", {}, clear=True)
    def test_unconfigured_providers_are_safe(self):
        self.assertFalse(affiliate.configured("amazon"))
        self.assertFalse(affiliate.configured("flipkart"))
        self.assertEqual(affiliate.amazon_get_item("B0TEST1234")["status"], "NOT_CONFIGURED")
        self.assertEqual(affiliate.flipkart_get_product("MOBTEST1234")["status"], "NOT_CONFIGURED")

    def test_nonpositive_price_is_rejected(self):
        self.assertIsNone(affiliate._positive_inr(0))
        self.assertIsNone(affiliate._positive_inr(-99))
        self.assertIsNone(affiliate._positive_inr("NaN"))
        self.assertEqual(affiliate._positive_inr(15342.499), 15342.5)


if __name__ == "__main__":
    unittest.main()
