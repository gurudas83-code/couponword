"""Release gate: fifty differentiated English/Hindi comparisons, not SEO doorway pages."""
from __future__ import annotations

import json
import re
import unittest
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET

from python.mobile_seo_comparisons import (
    EN, HI, MIN_FIELDS, SOURCE, SITE, path_for, publish_comparisons,
)
from python.phone_research_pages import EDITORIAL_MODEL_KEYS, accepted_specs, eligible

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"


class Page(HTMLParser):
    def __init__(self, markup):
        super().__init__()
        self.canonical, self.alternates, self.links, self.h1, self.lang = [], [], [], 0, None
        self.body_text = []
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "html":
            self.lang = d.get("lang")
        if tag == "h1":
            self.h1 += 1
        if tag == "link" and d.get("rel") == "canonical":
            self.canonical.append(d.get("href"))
        if tag == "link" and d.get("rel") == "alternate":
            self.alternates.append((d.get("hreflang"), d.get("href")))
        if tag == "a":
            self.links.append(d)

    def handle_data(self, data):
        if data.strip():
            self.body_text.append(data.strip())


class ComparisonSEOContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(SOURCE.read_text(encoding="utf-8"))
        cls.items = cls.manifest["pairs"]
        cls.catalogue = json.loads((PUBLIC / "data/mobile_research_catalogue.json").read_text(encoding="utf-8"))
        cls.cards = {c["model_key"]: c for c in cls.catalogue["model_cards"]}
        cls.urls = [el.text for el in ET.parse(PUBLIC / "sitemap.xml").getroot().iter()
                    if el.tag.endswith("}loc")]

    def _page(self, route):
        return (PUBLIC / route.lstrip("/") / "index.html").read_text(encoding="utf-8")

    def test_exact_identity_and_genuine_demand_disclosure(self):
        self.assertEqual(len(self.items), 50)
        self.assertEqual([p["id"] for p in self.items], list(range(1,51)))
        self.assertEqual(len(self.cards), 232)
        self.assertIn("historical", self.manifest["india_search_evidence"]["metric"].lower())
        self.assertIn("not query pair volumes", self.manifest["india_search_evidence"]["metric"].lower())
        seen = set()
        for p in self.items:
            a, b = p["left"], p["right"]
            self.assertNotEqual(a, b)
            self.assertIn(a, EDITORIAL_MODEL_KEYS)
            self.assertIn(b, EDITORIAL_MODEL_KEYS)
            self.assertTrue(eligible(self.cards[a]), a)
            self.assertTrue(eligible(self.cards[b]), b)
            self.assertGreaterEqual(len(accepted_specs(self.cards[a])), MIN_FIELDS)
            self.assertGreaterEqual(len(accepted_specs(self.cards[b])), MIN_FIELDS)
            identity = tuple(sorted((a,b)))
            self.assertNotIn(identity, seen)
            seen.add(identity)
            self.assertGreaterEqual(len(p["intent_en"].split()), 10)
            self.assertGreaterEqual(len(p["intent_hi"]), 45)
        self.assertEqual(len(seen), 50)

    def test_only_consolidated_comparison_guides_are_published(self):
        self.assertEqual({u for u in self.urls if u.startswith(SITE+EN) or u.startswith(SITE+HI)}, {SITE+EN,SITE+HI})
        for base in (EN,HI):
            self.assertEqual(len(list((PUBLIC/base.lstrip('/')).rglob('index.html'))),1)
            page=self._page(base)
            self.assertIn('Galaxy A36',page)
            self.assertIn('Galaxy A56',page)
            self.assertNotIn('comparison-list',page)
            self.assertNotIn('50 Evidence-Based',page)
            self.assertNotIn('"@type": "Offer"',page)

if __name__=='__main__': unittest.main()
