"""Regression and release-contract checks for 25-model bilingual research SEO pages."""
from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from python.under25_seo_pages import (
    BASE, EN, HI, ROOT, SOURCE, CATEGORY_TEXT, publish_under25, valid_data,
    pth, display_name,
)
from python.affiliate_links import AMAZON_TAG


class Under25EditorialRelease(unittest.TestCase):
    def test_source_count_rankings_are_editorial_not_live_offers(self):
        data = valid_data()
        self.assertEqual(data["budget_inr"], 25000)
        self.assertEqual(len(data["models"]), 25)
        self.assertEqual(sum(bool(m["primary_catalogue_present"]) for m in data["models"]),10)
        self.assertEqual(len(data["ranked_categories"]),4)
        self.assertTrue(all(len(v)==5 for v in data["ranked_categories"].values()))
        self.assertTrue(all(m["retailer_offer_verified"] is False for m in data["models"]))
        self.assertIn("Price weight remains 0%",data["disclosure"])

    def test_pages_render_source_provenance_no_fake_prices_and_tagged_retailers(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)
            (dest/"data").mkdir()
            source=(ROOT/"data/mobile_research_catalogue.json")
            (dest/"data/mobile_research_catalogue.json").write_bytes(source.read_bytes())
            ET.ElementTree(ET.Element("{http://www.sitemaps.org/schemas/sitemap/0.9}urlset")).write(
                dest/"sitemap.xml",encoding="utf-8")
            urls=publish_under25(dest)
            # English and Hindi: 25 phones + four priority ranks + hub = 60 routes.
            self.assertEqual(len(list(dest.rglob("index.html"))),60)
            # Both language pages for ambiguous model naming are noindex and
            # omitted from the searchable sitemap.
            self.assertEqual(len(urls),58)
            sitemap=(dest/"sitemap.xml").read_text(encoding="utf-8")
            self.assertEqual(sitemap.count("<loc>"),58)
            cases=valid_data()["models"]
            for model in cases:
                for hindi in (False,True):
                    path=pth(model,hindi)
                    page=(dest/path.lstrip("/")/"index.html").read_text(encoding="utf-8")
                    self.assertIn('rel="canonical" href="'+BASE+path+'"',page)
                    self.assertIn('href="https://www.amazon.in/s?',page)
                    self.assertIn("tag="+AMAZON_TAG,page.replace("&amp;","&"))
                    self.assertIn("https://www.flipkart.com/search?",page)
                    self.assertIn("https://www.croma.com/",page)
                    self.assertIn(model["editorial_reference_url"],page)
                    self.assertNotIn('"@type": "Offer"',page)
                    self.assertNotIn('price-inr=',page)
                    self.assertNotIn('class="purchase-cta"',page)
                    self.assertIn('hreflang="hi-IN"',page)
                    self.assertIn('hreflang="en-IN"',page)
                    if model["manufacturer_scope"]=="MODEL_NAMING_ALIAS_REQUIRES_REVIEW":
                        self.assertIn('content="noindex,follow"',page)
                        self.assertNotIn(BASE+path,sitemap)
                    else:
                        self.assertIn('content="index,follow"',page)
                        self.assertIn(BASE+path,sitemap)
            for category in CATEGORY_TEXT:
                for base in (EN,HI):
                    link=base+"best-"+category+"/"
                    body=(dest/link.lstrip("/")/"index.html").read_text(encoding="utf-8")
                    self.assertEqual(body.count('class="rank"'),5)
                    self.assertIn("91mobiles",body)
                    self.assertIn("Flipkart",body)
                    self.assertIn("Croma",body)
                    self.assertIn(BASE+link,sitemap)
            for base in (EN,HI):
                page=(dest/base.lstrip("/")/"index.html").read_text(encoding="utf-8")
                self.assertEqual(page.count('href="'+base+'best-'),4)
                self.assertIn("25",page)
                self.assertIn("Amazon",page if base==EN else (dest/(base+"best-overall/").lstrip("/")/"index.html").read_text(encoding="utf-8"))


if __name__=="__main__":
    unittest.main()
