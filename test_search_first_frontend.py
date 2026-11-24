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

    def test_new_noteworthy_uses_source_backed_market_intake(self):
        # Current site intentionally distinguishes 13 recent source-linked
        # additions from the frozen core 232, not by an arbitrary age cutoff.
        self.assertIn("market_intake === true", self.script)
        self.assertIn("(card.source_urls || []).length > 0", self.script)
        self.assertIn("researchNewSection.hidden = recent.length === 0", self.script)
        self.assertIn("recently added phones in the searchable catalogue", self.script)

    def test_public_counts_and_no_commerce_change(self):
        counts = self.payload["source_counts"]
        self.assertEqual(counts["visible_model_cards"], 232)
        self.assertEqual(counts["deduplicated_discovery_records"], 235)
        self.assertEqual(counts["frozen_verified_variants"], 10)
        self.assertGreaterEqual(sum(bool(card.get("specifications")) for card in self.payload["model_cards"]), 225)
        self.assertGreaterEqual(sum(len(card.get("specifications", {})) for card in self.payload["model_cards"]), 2479)
        self.assertNotIn("purchase_cta_eligible: true", self.html.lower())
        self.assertIn("Research-Verified Top 3", self.script)
        self.assertIn('card.status !== "OFFICIAL_VERIFIED"', self.script)
        self.assertIn("hasResearchVerifiedEvidence", self.script)
        self.assertIn("isResearchTopThreeQuery(query)", self.script)
        self.assertIn("Go to Amazon product", self.script)
        self.assertIn("Go to Flipkart product", self.script)
        self.assertIn("Search Amazon", self.script)
        self.assertIn("Search Flipkart", self.script)

    def test_top_three_routes_to_existing_local_research_without_paid_api(self):
        self.assertIn("if (!isExplicitTopThreeQuery(query) && !research.isResearchQuery(query)) return false;", self.app)
        self.assertIn("var wantsTopThree = isResearchTopThreeQuery(lastSearchQuery)", self.script)
        self.assertIn('!isResearchTopThreeQuery(query) && inventoryCards.length', self.script)
        self.assertIn("No model meets the minimum manufacturer-backed research evidence", self.script)


if __name__ == "__main__":
    unittest.main()
