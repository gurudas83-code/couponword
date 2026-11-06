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

    def test_exactly_102_indexable_canonical_urls(self):
        expected = {SITE + EN, SITE + HI}
        for item in self.items:
            left, right = self.cards[item["left"]], self.cards[item["right"]]
            expected.add(SITE + path_for(left, right))
            expected.add(SITE + path_for(left, right, True))
        self.assertEqual(len(expected), 102)
        self.assertEqual(len(self.urls), len(set(self.urls)))
        actual = {u for u in self.urls if u.startswith(SITE + EN) or u.startswith(SITE + HI)}
        self.assertEqual(actual, expected)
        for route in (EN,HI):
            markup = self._page(route)
            self.assertIn("50", markup)
            self.assertEqual(markup.count('class="comparison-list"'), 1)
            self.assertIn("not a claimed ranking" if route == EN else "सबसे अधिक खोजे गए", markup)

    def test_source_links_no_fabricated_buyability_and_translation(self):
        targets = []
        seen_titles = set()
        for item in self.items:
            a, b = self.cards[item["left"]], self.cards[item["right"]]
            for hi in (False,True):
                route = path_for(a,b,hi)
                content = self._page(route)
                page = Page(content)
                self.assertEqual(page.lang, "hi-IN" if hi else "en-IN")
                self.assertEqual(page.h1, 1, route)
                self.assertEqual(page.canonical, [SITE + route], route)
                self.assertIn('name="robots" content="index,follow"', content, route)
                self.assertIn(("hi-IN", SITE + path_for(a,b,True)), page.alternates)
                self.assertIn(("en-IN", SITE + path_for(a,b,False)), page.alternates)
                self.assertIn(item["intent_hi"] if hi else item["intent_en"], unescape(content))
                self.assertIn("0%", content, route)
                self.assertNotIn('"@type": "Offer"', content)
                self.assertNotIn('"@type": "Product"', content)
                self.assertNotIn('"@type": "AggregateRating"', content)
                self.assertNotIn("price_inr", content)
                self.assertNotIn('class="purchase-cta"', content)
                self.assertIn('https://www.amazon.in/s?', content)
                self.assertIn('tag=guru07cc-21', content.replace("&amp;","&"))
                self.assertIn('https://www.flipkart.com/search?', content)
                self.assertIn('https://www.croma.com/', content)
                self.assertIn("source" if not hi else "स्रोत", content)
                self.assertGreaterEqual(content.count('class="source"'), 8, route)
                self.assertGreater(len(" ".join(page.body_text).split()), 260, route)
                title = re.search(r"<title>(.*?)</title>", content)
                self.assertIsNotNone(title)
                self.assertNotIn((hi,title.group(1)),seen_titles)
                seen_titles.add((hi,title.group(1)))
                targets.extend([(route,a) for a in page.links])
        self.assertEqual(len(seen_titles), 100)
        for route, anchor in targets:
            href = anchor.get("href") or ""
            if not href.startswith("/") or href.startswith("//"):
                continue
            file = PUBLIC / unquote(urlsplit(href).path).lstrip("/")
            self.assertTrue(file.is_file() or (file / "index.html").is_file(), (route,href))

    def test_noindex_or_data_eligibility_shortcuts(self):
        # The build must reject data with fewer than 50/50 vetted source records;
        # do not silently publish only easy keyword permutations.
        self.assertTrue((PUBLIC / "assets/compare-seo.css").is_file())
        for source_page in ("/", "/phones/", "/hi/phones/"):
            target = PUBLIC / source_page.lstrip("/") / "index.html"
            self.assertTrue(target.exists(), source_page)
            markup = target.read_text(encoding="utf-8")
            self.assertIn('href="' + (HI if source_page.startswith("/hi") else EN) + '"', markup)
        english_index = self._page(EN)
        hindi_index = self._page(HI)
        for item in self.items:
            a, b = self.cards[item["left"]], self.cards[item["right"]]
            self.assertIn(path_for(a,b), english_index)
            self.assertIn(path_for(a,b,True), hindi_index)


if __name__ == "__main__":
    unittest.main()
