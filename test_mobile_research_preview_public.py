"""Publish-safety checks for the public mobile research preview."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PREVIEW = ROOT / "data" / "mobile_research_preview.json"
FROZEN = {
    "cw-mobile-93", "cw-mobile-100", "cw-mobile-106", "cw-mobile-107",
    "cw-mobile-108", "cw-mobile-109", "cw-mobile-110", "cw-mobile-111",
    "cw-mobile-112", "cw-mobile-113",
}


class PublicMobileResearchPreviewTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(PREVIEW.read_text(encoding="utf-8"))
        self.rows = self.payload["products"]

    def test_exact_frozen_variants_are_unique_and_research_only(self):
        ids = [row["canonical_product_id"] for row in self.rows]
        self.assertEqual(set(ids), FROZEN)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(row["technical_lane"] == "TECHNICAL_RESEARCH" for row in self.rows))
        self.assertTrue(all(row["manufacturer_spec_status"] == "VERIFIED" for row in self.rows))

    def test_no_commerce_or_private_evidence_is_exposed(self):
        raw = PREVIEW.read_text(encoding="utf-8").lower()
        for forbidden in ("password", "credential", "api_key", "token", "private_product_id", "retailer_offer"):
            self.assertNotIn(forbidden, raw)
        for row in self.rows:
            commerce = row["commerce"]
            self.assertIsNone(commerce["price"])
            self.assertIsNone(commerce["stock"])
            self.assertFalse(commerce["purchase_cta_eligible"])
            self.assertFalse(commerce["publication_eligible"])

    def test_sources_are_https_and_redmi_uses_india_50mp(self):
        for row in self.rows:
            urls = [row["official_source"]]
            urls += [item["source_url"] for item in row["specifications"].values()]
            urls += row["battery_evidence"]["source_urls"]
            urls += row["camera_evidence"]["source_urls"]
            self.assertTrue(all(url.startswith("https://") for url in urls))
        redmi = [row for row in self.rows if row["model"] == "Note 14 5G"]
        self.assertEqual(len(redmi), 3)
        self.assertTrue(all(row["specifications"]["rear_main_mp"]["value"] == 50 for row in redmi))

    def test_preview_is_public_and_safe_in_frontend(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "mobile-research-preview.js").read_text(encoding="utf-8")
        payload = json.loads(PREVIEW.read_text(encoding="utf-8"))
        self.assertIn('id="mobileResearchPreview"', html)
        self.assertIn("Compare 4 Verified Smartphones", html)
        self.assertIn('href="#mobileResearchPreview"', html)
        self.assertIn('src="/mobile-research-preview.js?v=3"', html)
        self.assertIn("section.hidden = false", script)
        self.assertNotIn("section.hidden = true", script)
        self.assertTrue(payload["default_enabled"])
        self.assertEqual(payload["mode"], "PUBLIC_TECHNICAL_RESEARCH_PREVIEW")


if __name__ == "__main__":
    unittest.main()
