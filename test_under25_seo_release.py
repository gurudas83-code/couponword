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

    def test_only_one_useful_guide_per_language_is_published(self):
        public=ROOT/'public'
        for base in (EN,HI):
            folder=public/base.lstrip('/')
            self.assertEqual(len(list(folder.rglob('index.html'))),1)
            text=(folder/'index.html').read_text()
            self.assertIn('6.67-inch',text)
            self.assertNotIn('6.73-inch',text)
            self.assertNotIn('class="rank"',text)
            self.assertNotIn('best-gaming/',text)
            self.assertIn('not a ranking',text) if base==EN else self.assertIn('रैंकिंग नहीं',text)
            self.assertIn('3 November 2026',text)
            self.assertIn('Manufacturer sources',text)

if __name__=='__main__': unittest.main()
