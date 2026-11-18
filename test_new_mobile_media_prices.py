"""No unlicensed model photographs or false API prices may enter new research."""
import json
import re
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from python.india_missing_eight_pages import import_eight, publish_eight, _route
from python.india_recent_eight_import import build_recent, publish_recent, detail_route, HUB
from python.new_mobile_media import url, RIGHTS_NOTE
from scripts.new_mobiles_api_probe import approved_targets

ROOT = Path(__file__).resolve().parent


class NewMobileMediaAndPricesTests(unittest.TestCase):
    def test_all_nineteen_have_exact_clickthrough_urls_and_no_unlicensed_images(self):
        cards = import_eight()["model_cards"] + build_recent()["model_cards"]
        self.assertEqual(len(cards), 19)
        self.assertEqual(len({row["model_key"] for row in cards}), 19)
        self.assertEqual(len(approved_targets()), 19)
        for row in cards:
            self.assertEqual(row["image_status"], "PLACEHOLDER")
            self.assertIsNone(row["photo"])
            self.assertEqual(row["photo_rights_status"], "NOT_CLEARED")
            self.assertEqual(row["research_art_url"], url(row["model_key"]))
            self.assertTrue(row["detail_url"].startswith("/phones/"))
            self.assertTrue(row["detail_url"].endswith("/"))
            self.assertFalse(row["verified_retailer_links"])
            self.assertNotIn("price", row)
            self.assertNotIn("stock", row)

    def test_generates_nineteen_original_artworks_and_clickable_full_details(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
            ET.ElementTree(ET.Element("{"+ns+"}urlset")).write(
                target / "sitemap.xml", encoding="utf-8")
            a = publish_eight(target)
            b = publish_recent(target)
            all_cards = a["model_cards"] + b["model_cards"]
            art_paths = list((target / "assets/new-mobile-art").glob("*.svg"))
            self.assertEqual(len(art_paths), 19)
            for row in all_cards:
                artwork = (target / row["research_art_url"].lstrip("/")).read_text("utf-8")
                self.assertIn("NOT AN ACTUAL PRODUCT PHOTO", artwork)
                self.assertNotIn("<image", artwork)
                html = (target / row["detail_url"].lstrip("/") / "index.html").read_text("utf-8")
                self.assertIn('name="robots" content="noindex,follow"', html)
                self.assertIn(row["research_art_url"], html)
                self.assertIn("Current price unavailable", html)
                self.assertIn("Search Amazon", html)
                self.assertIn("Search Flipkart", html)
                self.assertIn("Search Croma", html)
                self.assertNotIn('"@type": "Offer"', html)
            hub = (target / HUB.lstrip("/") / "index.html").read_text("utf-8")
            for row in b["model_cards"]:
                self.assertIn('href="' + row["detail_url"] + '"', hub)
            sitemap = (target / "sitemap.xml").read_text("utf-8")
            self.assertIn("https://coupon-world.in" + HUB, sitemap)
            self.assertNotIn("new-india-mobiles/samsung-", sitemap)

    def test_client_clickable_titles_and_legible_image_disclaimers(self):
        js = (ROOT / "mobile-research-preview.js").read_text("utf-8")
        self.assertEqual(js.count("research-model-name-link"), 2)
        self.assertIn("card.detail_url", js)
        self.assertIn("Original generic artwork", js)
        self.assertIn("Price unavailable", js)

    def test_no_fresh_provider_price_for_new_models_in_saved_snapshot(self):
        observations = json.loads(
            (ROOT / "data/retailer_price_observations.json").read_text("utf-8"))
        self.assertEqual(observations["source_type"], "quickcommerce_third_party_research")
        self.assertIn("2026-11-17", observations["generated_at"])
        self.assertFalse(any(
            x.get("purchase_eligible") is True for group in observations["models"].values()
            for x in group
        ))


if __name__ == "__main__":
    unittest.main()
