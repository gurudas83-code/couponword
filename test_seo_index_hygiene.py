"""Prevent stale catalogue pages from misleading Google Search.

Tests the built Pages artifact; run after scripts/build_public_pages.py.
No live offer is assumed, and approved ranking/identity logic is untouched.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from python.under25_seo_pages import EN as UNDER25_EN, CATEGORY_TEXT as UNDER25_CATEGORIES, valid_data as under25_data, pth as under25_path


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
        # Existing 50 source-linked models + the two hubs remain distinct.
        # Verify exact under-25k pages, excluding any unapproved model alias.
        expected_under25 = {
            ORIGIN + UNDER25_EN,
            *(ORIGIN + UNDER25_EN + "best-" + category + "/" for category in UNDER25_CATEGORIES),
            *(ORIGIN + under25_path(model) for model in under25_data()["models"]
              if model["manufacturer_scope"] != "MODEL_NAMING_ALIAS_REQUIRES_REVIEW"),
        }
        self.assertEqual(
            {url for url in self.urls if url.startswith(ORIGIN + UNDER25_EN)},
            expected_under25,
        )
        self.assertEqual(
            len([url for url in self.urls if url.startswith(ORIGIN + "/phones/")
                 and not url.startswith(ORIGIN + UNDER25_EN)]),
            52,
        )
        self.assertIn(ORIGIN + "/phones/india-market-demand-q3-2026/", self.urls)
        self.assertNotIn(ORIGIN + "/phones/india-market-demand-q3-2026/samsung-galaxy-a07-5g/", self.urls)
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

    def test_google_search_console_ownership_file_is_published(self):
        token = (PUBLIC / "google54faf165096b5622.html").read_text(encoding="utf-8").strip()
        self.assertEqual(token, "google-site-verification: google54faf165096b5622.html")

    def test_crawl_is_open_so_noindex_can_be_observed(self):
        robots = (PUBLIC / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("Allow: /", robots)
        self.assertIn("Sitemap: https://coupon-world.in/sitemap.xml", robots)
        self.assertNotIn("Disallow: /products", robots)


if __name__ == "__main__":
    unittest.main()
