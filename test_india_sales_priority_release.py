#!/usr/bin/env python3
"""Q3 India sales-reference coverage, duplicate prevention and publisher gate."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from python.india_sales_priority_pages import (
    ROUTE, SOURCE, ROOT, validate, model_route, publish_sales_priority
)


class IndiaMarketCoverageTests(unittest.TestCase):
    def test_sources_are_manufacturer_hosted_and_model_counts_exact(self):
        data = validate()
        self.assertEqual(len(data["models"]), 10)
        self.assertEqual(data["source_period"], "2026-Q3")
        self.assertIn("NOT an ordered India top-10", data["ranking_disclosure"])
        existing = [x for x in data["models"] if x["repository_snapshot_status"]=="EXISTING_232_MODEL"]
        new = [x for x in data["models"] if x["repository_snapshot_status"]=="NEW_SOURCE_REVIEWED_INTAKE_ONLY"]
        self.assertEqual(len(existing),4)
        self.assertEqual(len(new),6)
        self.assertEqual(sum(len(x["specs"]) for x in data["models"]),67)
        self.assertEqual({x["model"] for x in new},
            {"Galaxy A07 5G","Galaxy A17 5G","Y11 5G","Y21 5G","Redmi 15A 5G","Redmi A7"})

    def test_no_ranked_sales_or_unverified_purchase_offers(self):
        data=validate()
        self.assertNotIn("rankings", data)
        for item in data["models"]:
            self.assertIsNone(item["price_inr"])
            self.assertIsNone(item["stock"])
            self.assertIsNone(item["performance_score"])
            self.assertIs(item["merchant_offer_eligible"],False)
            self.assertIn(item["repository_model_key"].split("|")[0],item["brand"].lower())
            self.assertTrue(item["notes"])
            self.assertEqual(len({x["label"] for x in item["specs"]}),len(item["specs"]))

    def test_static_model_pages_and_sitemap_are_research_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            ns="http://www.sitemaps.org/schemas/sitemap/0.9"
            ET.ElementTree(ET.Element("{"+ns+"}urlset")).write(root/"sitemap.xml",encoding="utf-8")
            url=publish_sales_priority(root)
            self.assertEqual(url, "https://coupon-world.in"+ROUTE)
            hub=(root/ROUTE.lstrip("/")/"index.html").read_text(encoding="utf-8")
            self.assertIn("4 already included",hub)
            self.assertIn("6 were missing",hub)
            self.assertIn("NOT an official nationwide Top 10 ranking",hub)
            self.assertEqual(hub.count('class="cr-card"'),10)
            self.assertIn(url,(root/"sitemap.xml").read_text(encoding="utf-8"))
            self.assertIn('name="robots" content="index,follow"',hub)
            for item in validate()["models"]:
                page=(root/model_route(item).lstrip("/")/"index.html").read_text(encoding="utf-8")
                self.assertIn('name="robots" content="noindex,follow"',page)
                self.assertEqual(page.count("Manufacturer source"),len(item["specs"]))
                self.assertIn(item["source_report_url"],page)
                self.assertNotIn('"@type": "Offer"',page)
                self.assertNotIn('class="shop-button"',page)
                self.assertNotIn('class="purchase-cta"',page)

    def test_existing_phone_catalogue_invariants_unchanged(self):
        from python.mobile_research_catalogue import build_public_catalogue
        data=build_public_catalogue(ROOT)
        self.assertEqual(len(data["model_cards"]),232)
        self.assertEqual(len(data["records"]),235)
        self.assertEqual(sum(len(c["frozen_variant_ids"]) for c in data["model_cards"]),10)


if __name__ == "__main__":
    unittest.main()
