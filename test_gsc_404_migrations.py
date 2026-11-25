"""Six owner-supplied GSC 404 examples that are intentionally retired.

This is a generated-artifact check. Run after building public/ with
scripts/build_public_pages.py. Do not reintroduce nontech pages or fake offers.
"""
from __future__ import annotations

import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from scripts.build_public_pages import GSC_RETIRED_PRODUCT_404_ROUTES


ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
ORIGIN = "https://coupon-world.in"
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


class GSC404MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public_urls = {node.text for node in ET.parse(PUBLIC / "sitemap.xml").getroot().iter(NS + "loc")}

    def test_all_six_retired_404s_stay_absent(self):
        self.assertEqual(GSC_RETIRED_PRODUCT_404_ROUTES, {
            "jiada-space-astronaut-stationery-set-for-boys-with-badge-notebook-and-1",
            "bausch-lomb-fresh-multi-purpose-500ml-contact-lens-solution-pack-of-1-4",
            "aasons-electric-drill-variable-angle-grinder-connecting-rod-with-1pc-w-5",
            "hebezon-expandable-appliance-roller-stand-with-wheels-heavy-duty-mobil-6",
            "keyboard-case-for-samsung-galaxy-tab-a11-tab-a9-plus-11-folio-cover-sm-2",
            "boat-airdopes-311-pro-tws-earbuds-32",
        })
        for slug in GSC_RETIRED_PRODUCT_404_ROUTES:
            self.assertFalse((PUBLIC / "products" / slug).exists(), slug)
            self.assertNotIn(ORIGIN + "/products/" + slug + "/", self.public_urls)

    def test_sitemap_and_technical_product_count_do_not_expand(self):
        # Two intentionally indexable research entry points (price watch and
        # upcoming India phones) are now included in the generated sitemap.
        self.assertEqual(len(self.public_urls), 201)
        self.assertEqual(
            len(list((PUBLIC / "products").glob("*/index.html"))),
            65,
        )


if __name__ == "__main__":
    unittest.main()
