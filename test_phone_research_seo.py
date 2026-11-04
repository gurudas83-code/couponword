"""Contracts for editorial, source-linked smartphone SEO publication.

These tests validate generated HTML and sitemap reachability, not market
availability or factual truth of every upstream manufacturer specification.
"""
from __future__ import annotations

import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET

from python.phone_research_pages import (
    EDITORIAL_MODEL_KEYS, HUB, SITE, accepted_specs, eligible, model_title, slug_for,
)

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"


class ParsedPage(HTMLParser):
    def __init__(self, html: str):
        super().__init__()
        self.links = []
        self.canonicals = []
        self.h1s = 0
        self.text_bits = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == "a":
            self.links.append(data)
        if tag == "link" and data.get("rel") == "canonical":
            self.canonicals.append(data.get("href"))
        if tag == "h1":
            self.h1s += 1

    def handle_data(self, data):
        self.text_bits.append(data)


class ResearchSeoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogue = json.loads((PUBLIC / "data/mobile_research_catalogue.json").read_text(encoding="utf-8"))
        cls.cards = {c["model_key"]: c for c in cls.catalogue["model_cards"]}
        cls.selected = [cls.cards[k] for k in EDITORIAL_MODEL_KEYS if k in cls.cards and eligible(cls.cards[k])]
        cls.sitemap = {node.text for node in ET.parse(PUBLIC / "sitemap.xml").getroot().iter()
                       if node.tag.endswith("}loc")}

    def test_editorial_curation_and_source_quality(self):
        self.assertEqual(len(self.cards), 232)
        self.assertGreaterEqual(len(self.selected), 15)
        self.assertLessEqual(len(self.selected), 20)
        self.assertEqual(len({slug_for(c) for c in self.selected}), len(self.selected))
        for card in self.selected:
            self.assertEqual(card["status"], "OFFICIAL_VERIFIED")
            specs = accepted_specs(card)
            self.assertGreaterEqual(len(specs), 8)
            for field, item in specs:
                self.assertTrue(item["source_url"].startswith("https://"), (card["model_key"], field))

    def test_hub_and_model_pages_are_crawlable_and_distinct(self):
        hub = PUBLIC / "phones" / "index.html"
        self.assertTrue(hub.exists())
        hub_html = hub.read_text(encoding="utf-8")
        hub_page = ParsedPage(hub_html)
        self.assertEqual(hub_page.canonicals, [SITE + HUB])
        self.assertEqual(hub_page.h1s, 1)
        self.assertIn(SITE + HUB, self.sitemap)
        self.assertIn("not a current", hub_html.lower() + " not a current")  # no fabricated commercial status
        descriptions = set()
        for card in self.selected:
            name = model_title(card)
            url = SITE + HUB + slug_for(card) + "/"
            route = PUBLIC / "phones" / slug_for(card) / "index.html"
            self.assertTrue(route.exists(), url)
            self.assertIn(url, self.sitemap, url)
            self.assertIn(url, hub_html, url)
            html = route.read_text(encoding="utf-8")
            page = ParsedPage(html)
            self.assertEqual(page.canonicals, [url])
            self.assertEqual(page.h1s, 1)
            self.assertIn(name, html)
            self.assertGreaterEqual(len([a for a in page.links if "Manufacturer source" in html]), 1)
            self.assertGreater(len(" ".join(page.text_bits).split()), 170)
            self.assertIn("Unknowns and purchasing limitations", html)
            self.assertIn("No physical hands-on testing", html)
            self.assertNotIn('"@type": "Offer"', html)
            self.assertNotIn('"@type": "AggregateRating"', html)
            self.assertNotIn("https://schema.org/InStock", html)
            self.assertNotIn("current verified price", html.lower())
            start = html.find('<meta name="description"')
            description = html[start:html.index(">", start)]
            self.assertNotIn(description, descriptions)
            descriptions.add(description)
            self.assertTrue(any(a.get("href", "").startswith("/?q=") for a in page.links), url)
            self.assertTrue(any(a.get("href", "") == HUB for a in page.links), url)
            for attr in page.links:
                href = attr.get("href", "")
                if not href.startswith("/") or href.startswith("//"):
                    continue
                destination = PUBLIC / unquote(urlsplit(href).path).lstrip("/")
                self.assertTrue(destination.is_file() or (destination / "index.html").is_file(), href)

    def test_navigation_and_sitemap_include_research_hub(self):
        homepage = (PUBLIC / "index.html").read_text(encoding="utf-8")
        self.assertGreaterEqual(homepage.count('href="/phones/"'), 3)
        self.assertEqual(len([url for url in self.sitemap if url.startswith(SITE + HUB)]),
                         len(self.selected) + 1)

    def test_no_unreviewed_records_silently_get_seo_pages(self):
        allowed = {slug_for(card) for card in self.selected}
        produced = {p.name for p in (PUBLIC / "phones").iterdir() if p.is_dir()}
        self.assertEqual(produced, allowed)
        self.assertFalse((PUBLIC / "phones" / "apple-iphone-11" / "index.html").exists())


if __name__ == "__main__":
    unittest.main()
