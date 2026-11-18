#!/usr/bin/env python3
"""Strict research-only publication gate for India's eight missing model identities."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from python.india_missing_eight_pages import ROOT, HUB, MODE, import_eight, publish_eight, _route


class EightMarketAdditionsTests(unittest.TestCase):
    def test_exact_model_keys_no_duplicates_no_ranking(self):
        imported = import_eight()
        original = json.loads((ROOT / "data/mobile_research_catalogue.json").read_text(encoding="utf-8"))
        source_keys = {row["model_key"] for row in original["model_cards"]}
        self.assertEqual(len(source_keys), 232)
        self.assertEqual(len(imported["model_cards"]), 8)
        self.assertEqual(imported["mode"], MODE)
        self.assertEqual(imported["core_model_count_unchanged"], 232)
        expected = {
            "oppo|a6x 5g", "vivo|y31 5g",
            "samsung|galaxy a07 5g", "samsung|galaxy a17 5g",
            "vivo|y11 5g", "vivo|y21 5g",
            "redmi|redmi 15a 5g", "redmi|redmi a7",
        }
        self.assertEqual({row["model_key"] for row in imported["model_cards"]}, expected)
        self.assertFalse(expected.intersection(source_keys))
        self.assertEqual(len(imported["records"]), 8)
        for card in imported["model_cards"]:
            self.assertEqual(card["status"], "RESEARCH_ONLY")
            self.assertTrue(card["market_intake"])
            self.assertEqual(card["image_status"], "PLACEHOLDER")
            self.assertIsNone(card["photo"])
            self.assertEqual(card["verified_retailer_links"], [])
            self.assertEqual({item["retailer"] for item in card["retailer_search_links"]},
                             {"amazon", "flipkart", "croma"})
            self.assertTrue(all(item.get("source_url") for item in card["specifications"].values()))
            self.assertGreaterEqual(len(card["specifications"]), 5)
            self.assertFalse(any(key in card for key in ("price", "stock", "score", "rank")))
            self.assertIn("manufacturer", card["status_reason"].lower())

    def test_site_publication_sitemap_and_safe_product_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp)
            ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
            root = ET.Element("{" + ns + "}urlset")
            ET.ElementTree(root).write(destination / "sitemap.xml", encoding="utf-8")
            payload = publish_eight(destination)
            data = json.loads((destination / "data/india_sales_eight_research.json").read_text(encoding="utf-8"))
            self.assertEqual(data["mode"], MODE)
            self.assertEqual(len(data["model_cards"]), 8)
            hub = (destination / HUB.lstrip("/") / "index.html").read_text(encoding="utf-8")
            self.assertIn("232 original research cards plus 8 distinct", hub)
            self.assertIn('name="robots" content="index,follow"', hub)
            self.assertIn("Q3 is not an ordered Top-10", hub)
            sitemap = (destination / "sitemap.xml").read_text(encoding="utf-8")
            self.assertIn("https://coupon-world.in" + HUB, sitemap)
            for card in payload["model_cards"]:
                page = (destination / _route(card["model_key"]).lstrip("/") / "index.html").read_text(encoding="utf-8")
                self.assertIn('name="robots" content="noindex,follow"', page)
                self.assertIn("Generic smartphone illustration", page)
                for site in ("Amazon", "Flipkart", "Croma"):
                    self.assertIn("Search " + site + " for this model", page)
                self.assertEqual(page.count("Maker source"), len(card["specifications"]))
                self.assertNotIn('"@type": "Offer"', page)
                self.assertNotIn("Verified listing", page)
                self.assertNotIn('class="shop-button"', page)

if __name__ == "__main__":
    unittest.main()
