#!/usr/bin/env python3
"""Block regression of the 40-product dated research import and buying gates."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from python.tv_earbuds_workbook_pages import load_catalogue, publish_workbook_catalogue, ROUTES

ROOT = Path(__file__).resolve().parent

class WorkbookTvEarbudsRelease(unittest.TestCase):
    def test_exact_40_research_rows_and_no_buyability(self):
        data=load_catalogue()
        rows=data["records"]
        self.assertEqual(len(rows),40)
        self.assertEqual(len([r for r in rows if r["category"]=="tvs"]),20)
        self.assertEqual(len([r for r in rows if r["category"]=="accessories"]),20)
        for row in rows:
            self.assertEqual(row["product_status"],"RESEARCH_ONLY")
            self.assertEqual(row["price_ranking_weight"],0)
            self.assertFalse(row["purchase_cta_eligible"])
            self.assertFalse(row["performance_ranking_eligible"])
            self.assertEqual(set(row["retailers"]),{"amazon","flipkart","croma"})
            for store in row["retailers"].values():
                self.assertFalse(store["live_offer"])
                self.assertFalse(store["checkout_eligible"])
                self.assertEqual(store["stock_status"],"UNKNOWN")
                self.assertIn(store["link_scope"], {"SEARCH_OR_CATEGORY_BROWSE_NOT_VERIFIED_SKU_CTA", "EXACT_MODEL_SEARCH_NOT_VERIFIED_SKU_CTA", "EXACT_MODEL_LISTING_RESEARCH_NOT_LIVE_OFFER"})
                self.assertFalse(store["checkout_eligible"])
                self.assertFalse(store["live_offer"])
    def test_observations_are_dated_not_live(self):
        rows=load_catalogue()["records"]
        counts={s:sum(bool(x["retailers"][s]["price_inr"]) for x in rows) for s in ("amazon","flipkart","croma")}
        self.assertEqual(counts, load_catalogue()["counts"]["retailer_quote_counts"])
        self.assertEqual(counts, {"amazon":2,"flipkart":3,"croma":9})  # Current evidence-admitted dated quotes; not historical workbook totals
        self.assertEqual(sum(len(x["specifications"]) for x in rows),281)  # Current source-backed research fields; historical workbook had 251
    def test_40_product_routes_and_two_hubs(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            for c in ROUTES:
                p=base/c/"index.html"
                p.parent.mkdir(parents=True,exist_ok=True)
                p.write_text("<main>Source review hub</main>",encoding="utf-8")
            n="http://www.sitemaps.org/schemas/sitemap/0.9"
            ET.ElementTree(ET.Element("{"+n+"}urlset")).write(base/"sitemap.xml",encoding="utf-8")
            published=publish_workbook_catalogue(base)
            self.assertEqual(len(published),2)
            for c in ROUTES:
                slug=ROUTES[c][0]
                hub=(base/c/slug/"index.html").read_text(encoding="utf-8")
                self.assertEqual(hub.count('data-model="'),20)
                self.assertIn('id="cr-payload"',hub)
                self.assertIn('id="cr-comparison"',hub)
                self.assertIn("not current offers",hub.lower())
                for r in (x for x in load_catalogue()["records"] if x["category"]==c):
                    page=(base/c/slug/r["id"].lower()/"index.html").read_text(encoding="utf-8")
                    self.assertIn('name="robots" content="noindex,follow"',page)
                    self.assertIn("Dated quoted reference",page)
                    self.assertIn('rel="canonical"',page)
                    self.assertNotIn('"@type": "Offer"',page)
                    self.assertNotIn('class="shop-button"',page)
                    self.assertNotIn('class="purchase-cta"',page)
                src=(base/c/"index.html").read_text(encoding="utf-8")
                self.assertIn("Expanded India research list",src)
                self.assertIn(f"/{c}/{slug}/",src)
            sitemap=(base/"sitemap.xml").read_text(encoding="utf-8")
            self.assertIn("https://coupon-world.in/tvs/india-20/",sitemap)
            self.assertIn("https://coupon-world.in/accessories/earbuds-20/",sitemap)
            self.assertNotIn("https://coupon-world.in/tvs/india-20/tv01/",sitemap)

if __name__=="__main__":
    unittest.main()
