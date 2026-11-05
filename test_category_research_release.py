#!/usr/bin/env python3
"""Release regression for accessories and TVs without weakening phone gates."""
from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from python.category_research_pages import load_checked_records, publish_category_research_pages

ROOT = Path(__file__).resolve().parent


class CategoryResearchReleaseTests(unittest.TestCase):
    def test_source_counts_identity_and_strict_commerce_separation(self):
        data = load_checked_records()
        self.assertEqual(data["mode"], "CATEGORY_RESEARCH_ONLY")
        items = data["records"]
        self.assertEqual(len(items), 8)
        self.assertEqual(sum(r["category"] == "accessories" for r in items), 4)
        self.assertEqual(sum(r["category"] == "tvs" for r in items), 4)
        self.assertEqual(sum(len(r["specifications"]) for r in items), 56)
        self.assertEqual(len({(r["category"], r["slug"]) for r in items}), len(items))
        for row in items:
            self.assertEqual(row["review_status"], "MANUFACTURER_SOURCE_REVIEWED_MODEL")
            self.assertGreaterEqual(len(row["specifications"]), 5)
            self.assertTrue(all(f["source_url"] == row["source_url"] for f in row["specifications"]))
            for key in ("price", "mrp", "availability", "rating", "stock", "affiliate_url",
                        "performance_score", "purchase_cta_eligible"):
                self.assertNotIn(key, row)

    def test_exact_size_protocol_and_limitations(self):
        rows = {row["slug"]: row for row in load_checked_records()["records"]}
        def facts(slug):
            return " ".join(f["value"] for f in rows[slug]["specifications"])
        self.assertIn("50 Hz", facts("sony-k-43s20-bravia-2"))
        self.assertIn("1920 × 1080", facts("xiaomi-tv-a-2025-43"))
        self.assertIn("60 Hz", facts("lg-43ut80506la"))
        self.assertIn("PD 3.0 PPS", facts("samsung-ep-t2510-25w"))
        self.assertIn("Sold separately", facts("apple-20w-usb-c-adapter"))
        self.assertIn("55-inch", rows["tcl-c655-43"]["decision_note"])
        self.assertIn("not the case", rows["oneplus-buds-3"]["compatibility_caution"])

    def test_pages_and_canonical_sitemap_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sitemap_root = ET.Element("{http://www.sitemaps.org/schemas/sitemap/0.9}urlset")
            ET.ElementTree(sitemap_root).write(root / "sitemap.xml", encoding="utf-8")
            urls = publish_category_research_pages(root)
            self.assertEqual(len(urls), 10)
            self.assertEqual(len(set(urls)), len(urls))
            sitemap = (root / "sitemap.xml").read_text(encoding="utf-8")
            for category in ("accessories", "tvs"):
                hub = root / category / "index.html"
                html = hub.read_text(encoding="utf-8")
                self.assertIn('id="cr-filters"', html)
                self.assertIn('id="cr-comparison"', html)
                self.assertEqual(html.count('data-model="'), 4)
                self.assertIn('/assets/category-research.js', html)
                payload = re.search(r'<script type="application/json" id="cr-payload">(.*?)</script>', html, re.S)
                self.assertIsNotNone(payload)
                self.assertEqual(len(json.loads(payload.group(1))["records"]), 4)
                self.assertIn(f"https://coupon-world.in/{category}/", sitemap)
                for row in load_checked_records()["records"]:
                    if row["category"] != category:
                        continue
                    route = f"{category}/{row['slug']}/"
                    page = (root / route / "index.html").read_text(encoding="utf-8")
                    self.assertIn(f"https://coupon-world.in/{route}", page)
                    self.assertIn(f"https://coupon-world.in/{route}", sitemap)
                    self.assertEqual(page.count("Maker source"), len(row["specifications"]))
                    self.assertIn("Not yet verified", page)
                    self.assertIn("No", page)
                    self.assertNotIn('"@type": "Product"', page)
                    self.assertNotIn('"@type": "Offer"', page)
                    self.assertNotIn('class="shop-button"', page)
                    self.assertNotIn('class="purchase-cta"', page)

    def test_homepage_category_navigation_without_phone_contract_change(self):
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="mobileResearchSearch"', homepage)
        self.assertIn('id="researchCategories"', homepage)
        self.assertIn('href="/phones/"', homepage)
        self.assertIn('href="/accessories/"', homepage)
        self.assertIn('href="/tvs/"', homepage)
        self.assertIn('0% price', (ROOT / "reports" / "release_readiness_20261104.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
