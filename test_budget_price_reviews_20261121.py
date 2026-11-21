"""Checks 21-Nov source-backed price additions without live API calls."""
import json
import unittest
from pathlib import Path
from python.mobile_research_catalogue import build_public_catalogue

ROOT = Path(__file__).resolve().parent

class BudgetResearchPriceReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogue = build_public_catalogue(ROOT)
        cls.cards = {row["model_key"]: row for row in cls.catalogue["model_cards"]}
        cls.ledger = json.loads((ROOT / "data/mobile_budget_price_reviews_20261121.json").read_text())

    def test_exact_variant_and_price_provenance(self):
        self.assertEqual(len(self.catalogue["model_cards"]), 232)
        self.assertEqual(len(self.ledger["records"]), 4)
        for item in self.ledger["records"]:
            card = self.cards[item["model_key"]]
            ref = card["research_budget_reference"]
            self.assertEqual(ref["ram_gb"], item["ram_gb"])
            self.assertEqual(ref["storage_gb"], item["storage_gb"])
            self.assertEqual(ref["reference_price_inr"], item["reference_price_inr"])
            self.assertEqual(ref["source_url"], item["source_url"])
            self.assertEqual(ref["checked_at"], "2026-11-21")
            self.assertEqual(ref["ranking_weight"], 0)
            self.assertFalse(ref["live_offer"])
            self.assertEqual(ref["delivery_status"], "NOT_VERIFIED")
            self.assertEqual(ref["evidence_basis"], "DIRECT_RETAILER_PAGE_SNAPSHOT")
            self.assertEqual(card["status"], "OFFICIAL_VERIFIED")
            self.assertGreaterEqual(len(card["specifications"]), 2)

    def test_strict_ten_and_fifteen_k_bands_and_mismatched_model_block(self):
        def candidates(lo, hi):
            return {card["model_key"] for card in self.catalogue["model_cards"]
                    if card["status"] == "OFFICIAL_VERIFIED" and
                    (card.get("research_budget_reference") or {}).get("reference_price_inr") is not None and
                    lo <= card["research_budget_reference"]["reference_price_inr"] < hi and
                    len(card["specifications"]) >= 2}
        self.assertEqual(candidates(5000, 10000), {"lava|bold n2 lite"})
        self.assertEqual(candidates(10000, 15000),
                         {"lava|bold n2", "lava|virat v1", "lava|virat v1 5g"})
        a5x = self.cards["oppo|a5x"]
        self.assertIsNone(a5x["research_budget_reference"])
        self.assertIn("A5x 5G", a5x["research_budget_reference_block_reason"])

    def test_unavailable_and_unmatched_variants_are_not_promoted(self):
        self.assertEqual(len(self.ledger["excluded_observations"]), 4)
        for item in self.ledger["excluded_observations"]:
            self.assertIn(item["reason"], {
                "out_of_stock_on_retailer_page", "unavailable_online_store_only"})
        self.assertNotIn("oppo|a5x", {row["model_key"] for row in self.ledger["records"]})
        self.assertTrue(all(row["reference_price_inr"] < 15000 for row in self.ledger["records"]))

if __name__ == "__main__":
    unittest.main()
