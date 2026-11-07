import re
import unittest
from pathlib import Path

from python.mobile_research_catalogue import build_public_catalogue


ROOT = Path(__file__).resolve().parent


class SearchFirstFrontendTests(unittest.TestCase):
    def setUp(self):
        self.html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.script = (ROOT / "mobile-research-preview.js").read_text(encoding="utf-8")
        self.app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.payload = build_public_catalogue(ROOT)

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
        self.assertIn("research.submit(query)", self.app)

    def test_new_noteworthy_uses_explicit_india_launch_date(self):
        self.assertIn("india_launch_date", self.script)
        self.assertIn("365 * 24 * 60 * 60 * 1000", self.script)
        self.assertIn("researchNewSection.hidden = recent.length === 0", self.script)
        recent = [card for card in self.payload["model_cards"] if card.get("india_launch_date")]
        self.assertEqual(len(recent), 6)
        self.assertTrue(all(card.get("india_launch_source", "").startswith("https://news.samsung.com/in/") for card in recent))
        self.assertTrue(all(card.get("india_launch_date", "") >= "2025-11-01" for card in recent))

    def test_public_counts_and_no_commerce_change(self):
        counts = self.payload["source_counts"]
        self.assertEqual(counts["visible_model_cards"], 232)
        self.assertEqual(counts["deduplicated_discovery_records"], 235)
        self.assertEqual(counts["frozen_verified_variants"], 10)
        self.assertEqual(sum(bool(card.get("specifications")) for card in self.payload["model_cards"]), 225)
        self.assertEqual(sum(len(card.get("specifications", {})) for card in self.payload["model_cards"]), 2479)
        self.assertNotIn("purchase_cta_eligible: true", self.html.lower())
        self.assertNotIn("top 3", self.script.lower())


if __name__ == "__main__":
    unittest.main()
