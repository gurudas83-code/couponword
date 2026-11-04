"""Prevent stale catalogue pages from misleading Google Search.

Tests the built Pages artifact; run after scripts/build_public_pages.py.
No live offer is assumed, and approved ranking/identity logic is untouched.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
ORIGIN = "https://coupon-world.in"
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def robots_instruction(page: str) -> str:
    found = re.search(r'<meta[ ]+name="robots"[ ]+content="([^"]+)"', page, re.I)
    if not found:
        raise AssertionError("Product page is missing a robots meta tag")
    return found.group(1).casefold()


class SearchTrustHygiene(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.urls = [
            node.text
            for node in ET.parse(PUBLIC / "sitemap.xml").getroot().iter(NS + "loc")
        ]

    def test_sitemap_carries_unique_curated_indexable_urls(self):
        self.assertEqual(len(self.urls), len(set(self.urls)))
        self.assertIn(ORIGIN + "/", self.urls)
        self.assertIn(ORIGIN + "/phones/", self.urls)
        self.assertIn(ORIGIN + "/guides/phone-budget-guides/", self.urls)
        self.assertEqual(
            len([url for url in self.urls if url.startswith(ORIGIN + "/phones/")]),
            51,
        )
        self.assertNotIn(ORIGIN + "/seo/best-mobile-under-15000.html", self.urls)

    def test_legacy_products_are_available_but_not_indexed_without_verified_offer(self):
        products = sorted((PUBLIC / "products").glob("*/index.html"))
        self.assertGreaterEqual(len(products), 90)
        indexed = set(self.urls)
        for file in products:
            page = file.read_text(encoding="utf-8")
            canonical = ORIGIN + "/products/" + file.parent.name + "/"
            indexed_by_robots = "noindex" not in robots_instruction(page)
            self.assertEqual(
                canonical in indexed, indexed_by_robots,
                "Sitemap and product robots disagree: " + canonical,
            )
            if not indexed_by_robots:
                self.assertIn("Current price and stock not verified", page)
                self.assertNotIn('"@type": "Offer"', page)
                self.assertNotIn('<span class="current-price">', page)
                self.assertNotIn("View Best Verified Offer", page)

    def test_crawl_is_open_so_noindex_can_be_observed(self):
        robots = (PUBLIC / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("Allow: /", robots)
        self.assertIn("Sitemap: https://coupon-world.in/sitemap.xml", robots)
        self.assertNotIn("Disallow: /products", robots)


if __name__ == "__main__":
    unittest.main()
