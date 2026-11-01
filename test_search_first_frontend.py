import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class SearchFirstFrontendTests(unittest.TestCase):
    def setUp(self):
        self.html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.script = (ROOT / "mobile-research-preview.js").read_text(encoding="utf-8")
        self.app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.payload = json.loads((ROOT / "data/mobile_research_catalogue.json").read_text(encoding="utf-8"))

    def test_idle_homepage_is_search_first(self):
        self.assertIn('id="mobileResearchSearch"', self.html)
        self.assertIn('id="mobileResearchResults"', self.html)
        self.assertRegex(self.html, r'id="mobileResearchPreview"[^>]*\shidden')
        self.assertRegex(self.html, r'id="mobileResearchCatalogue"[^>]*\shidden')
        self.assertIn("section.hidden = true", self.script)
        self.assertIn("MAX_SEARCH_RESULTS", self.script)
        self.assertIn("INVENTORY_PAGE_SIZE", self.script)

    def test_search_and_details_contract_is_present(self):
        self.assertIn("CouponWorldMobileResearch", self.script)
        self.assertIn("data-research-detail", self.script)
        self.assertIn("mobileResearchDetail", self.html)
        self.assertIn("submitMobileResearchIfApplicable", self.app)
        self.assertIn("window.CouponWorldMobileResearch.search(query)", self.app)

    def test_new_noteworthy_requires_explicit_india_launch_date(self):
        self.assertIn("india_launch_date", self.script)
        self.assertIn("365 * 24 * 60 * 60 * 1000", self.script)
        self.assertIn("researchNewSection.hidden = recent.length === 0", self.script)
        self.assertEqual(sum(1 for card in self.payload["model_cards"] if any(card.get(k) for k in ("india_launch_date", "launch_date_india", "launch_date"))), 0)

    def test_public_counts_and_no_commerce_change(self):
        counts = self.payload["source_counts"]
        self.assertEqual(counts["visible_model_cards"], 232)
        self.assertEqual(counts["deduplicated_discovery_records"], 235)
        self.assertEqual(counts["frozen_verified_variants"], 10)
        self.assertEqual(sum(bool(card.get("specifications")) for card in self.payload["model_cards"]), 40)
        self.assertEqual(sum(len(card.get("specifications", {})) for card in self.payload["model_cards"]), 260)
        self.assertNotIn("purchase_cta_eligible: true", self.html.lower())
        self.assertNotIn("top 3", self.script.lower())


if __name__ == "__main__":
    unittest.main()
