"""Six owner-supplied GSC 404 examples: exact moves versus intentional retirement.

This is a generated-artifact check. Run after building public/ with
scripts/build_public_pages.py. Do not reintroduce nontech pages or fake offers.
"""
from __future__ import annotations

import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from python.technical_niche_publication import REVIEWED_TECH_IDS
from scripts.build_public_pages import (
    GSC_MOVED_TECH_PRODUCT_ROUTES,
    GSC_RETIRED_NONTECH_404_ROUTES,
)
from python import build_product_pages as products


ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
ORIGIN = "https://coupon-world.in"
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


class GSC404MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public_urls = {node.text for node in ET.parse(PUBLIC / "sitemap.xml").getroot().iter(NS + "loc")}
        cls.source_by_id = {int(item["id"]): item for item in products.load_products()}

    def test_two_exact_technical_product_old_urls_redirect_to_same_approved_product(self):
        self.assertEqual(set(GSC_MOVED_TECH_PRODUCT_ROUTES), {
            "keyboard-case-for-samsung-galaxy-tab-a11-tab-a9-plus-11-folio-cover-sm-2",
            "boat-airdopes-311-pro-tws-earbuds-32",
        })
        for old_slug, (id_, expected_asin) in GSC_MOVED_TECH_PRODUCT_ROUTES.items():
            with self.subTest(old_slug=old_slug):
                self.assertIn(id_, REVIEWED_TECH_IDS)
                source = self.source_by_id[id_]
                self.assertEqual(source["asin"], expected_asin)
                target_slug = products.page_dir(source).relative_to(products.OUT).as_posix()
                target = ORIGIN + "/products/" + target_slug + "/"
                old = ORIGIN + "/products/" + old_slug + "/"
                redirect = (PUBLIC / "products" / old_slug / "index.html").read_text(encoding="utf-8")
                self.assertIn('<meta http-equiv="refresh" content="0; url=' + target + '">', redirect)
                self.assertIn('<link rel="canonical" href="' + target + '">', redirect)
                self.assertIn('<a href="' + target + '">', redirect)
                self.assertTrue((PUBLIC / "products" / target_slug / "index.html").is_file())
                self.assertNotIn(old, self.public_urls)
                self.assertNotIn(target, self.public_urls)  # No current verified offer: existing noindex gate
                self.assertNotIn('"@type": "Offer"', redirect)
                self.assertNotIn("current-price", redirect)
                self.assertNotIn("amazon.in", redirect.lower())

    def test_four_retired_nontech_404s_stay_absent(self):
        self.assertEqual(GSC_RETIRED_NONTECH_404_ROUTES, {
            "jiada-space-astronaut-stationery-set-for-boys-with-badge-notebook-and-1",
            "bausch-lomb-fresh-multi-purpose-500ml-contact-lens-solution-pack-of-1-4",
            "aasons-electric-drill-variable-angle-grinder-connecting-rod-with-1pc-w-5",
            "hebezon-expandable-appliance-roller-stand-with-wheels-heavy-duty-mobil-6",
        })
        for slug in GSC_RETIRED_NONTECH_404_ROUTES:
            self.assertFalse((PUBLIC / "products" / slug).exists(), slug)
            self.assertNotIn(ORIGIN + "/products/" + slug + "/", self.public_urls)
        self.assertTrue(set(GSC_MOVED_TECH_PRODUCT_ROUTES).isdisjoint(
            GSC_RETIRED_NONTECH_404_ROUTES))

    def test_sitemap_and_technical_product_count_do_not_expand(self):
        self.assertEqual(len(self.public_urls), 199)
        self.assertEqual(
            len(list((PUBLIC / "products").glob("*/index.html"))),
            65 + len(GSC_MOVED_TECH_PRODUCT_ROUTES),
        )


if __name__ == "__main__":
    unittest.main()
