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
    EDITORIAL_MODEL_KEYS, CORE_EDITORIAL_KEYS, REVIEWED_ADDITIONS, HUB, SITE, accepted_specs, eligible, model_title, slug_for,
)
from python.under25_seo_pages import EN as UNDER25_EN, CATEGORY_TEXT as UNDER25_CATEGORIES, valid_data as under25_data, pth as under25_path

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
        self.assertEqual(len(EDITORIAL_MODEL_KEYS), 50)
        self.assertEqual(len(REVIEWED_ADDITIONS), 30)
        self.assertEqual(len(self.selected), 50)
        self.assertEqual(len({slug_for(c) for c in self.selected}), len(self.selected))
        for card in self.selected:
            self.assertIn(card["status"], {"OFFICIAL_VERIFIED", "PARTIALLY_VERIFIED"})
            if card["model_key"] in CORE_EDITORIAL_KEYS:
                self.assertEqual(card["status"], "OFFICIAL_VERIFIED")
            else:
                review = REVIEWED_ADDITIONS[card["model_key"]]
                self.assertTrue(review["manufacturer_page_verified"])
                self.assertGreaterEqual(
                    len(accepted_specs(card)), review["minimum_source_fields"]
                )
                self.assertIn(
                    review["manufacturer_source_url"],
                    {item["source_url"] for _, item in accepted_specs(card)},
                )
            specs = accepted_specs(card)
            self.assertGreaterEqual(len(specs), 8)
            for field, item in specs:
                self.assertTrue(item["source_url"].startswith("https://"), (card["model_key"], field))

    def test_corrections_and_no_duplicate_phone_identities(self):
        f05 = self.cards["samsung|galaxy f05"]
        self.assertEqual(f05["specifications"]["network_support"]["value"], "4G LTE")
        self.assertEqual(self.cards["xiaomi|14 ultra"]["specifications"]["network_support"]["value"], "5G")
        poco = self.cards["poco|x7 pro"]["specifications"]["battery_mah_typical"]
        self.assertEqual(poco["value"], 6550)
        self.assertEqual(poco["applicability"], "INDIA_MARKET_ONLY")
        self.assertEqual(poco["source_url"], "https://www.mi.com/global/support/faq/details/KA-522489/")
        self.assertEqual(self.cards["samsung|galaxy a57 5g"]["specifications"]["chipset"]["value"], "Exynos 1680")
        for key in ("samsung|galaxy f70 pro 5g", "samsung|galaxy m47 5g"):
            self.assertEqual(self.cards[key]["specifications"]["chipset"]["value"], "Qualcomm Snapdragon 6 Gen 3")
        a06 = SITE + HUB + "samsung-galaxy-a06-5g/"
        self.assertIn(a06, self.sitemap)
        self.assertFalse((PUBLIC / "phones/samsung-galaxy-a06-5g-light/").exists())
        self.assertFalse((PUBLIC / "phones/samsung-galaxy-s24-5g/").exists())
        self.assertEqual(len([u for u in self.sitemap if u.startswith(SITE + HUB + "samsung-galaxy-s24")]),1)

    def test_exactly_50_distinct_phones_with_original_sources(self):
        by_source = {}
        for card in self.selected:
            for key, spec in accepted_specs(card):
                self.assertTrue(spec["source_url"].startswith("https://"), key)
            by_source[card["model_key"]] = card["status"]
        self.assertEqual(len(by_source),50)
        self.assertEqual(len(CORE_EDITORIAL_KEYS),20)
        self.assertEqual(len(REVIEWED_ADDITIONS),30)
        self.assertTrue(any(card["brand"]=="Apple" for card in self.selected))
        self.assertTrue(any(card["brand"]=="Google" for card in self.selected))
        self.assertTrue(any(card["brand"]=="Samsung" for card in self.selected))
        self.assertTrue(any(card["brand"]=="Redmi" for card in self.selected))

    def test_hub_and_model_pages_are_crawlable_and_distinct(self):
        hub = PUBLIC / "phones" / "index.html"
        self.assertTrue(hub.exists())
        hub_html = hub.read_text(encoding="utf-8")
        hub_page = ParsedPage(hub_html)
        self.assertEqual(hub_page.canonicals, [SITE + HUB])
        self.assertEqual(hub_page.h1s, 1)
        self.assertIn(SITE + HUB, self.sitemap)
        self.assertIn("certified live offer", hub_html.lower())
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
            self.assertGreaterEqual(html.count(">Manufacturer source</a>"), len(accepted_specs(card)))
            self.assertGreater(len(" ".join(page.text_bits).split()), 170)
            self.assertIn("Unknowns and purchasing limitations", html)
            self.assertIn("No physical hands-on testing", html)
            self.assertIn("/assets/discovery-analytics.js", html)
            self.assertIn("G-921WL91ZGW", html)
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
        # The market-signal hub is one additional curated research collection;
        # its ten noindex model-intake details do not enter the sitemap.
        market = SITE + HUB + "india-market-demand-q3-2026/"
        self.assertIn(market, self.sitemap)
        # Preserve the original 50 models + two hubs, and strictly
        # reconcile the independent source-reviewed under-25k SEO layer.
        intake = under25_data()
        expected_under25 = {
            SITE + UNDER25_EN,
            *(SITE + UNDER25_EN + "best-" + category + "/" for category in UNDER25_CATEGORIES),
            *(SITE + under25_path(model) for model in intake["models"]
              if model["manufacturer_scope"] != "MODEL_NAMING_ALIAS_REQUIRES_REVIEW"),
        }
        actual_under25 = {url for url in self.sitemap if url.startswith(SITE + UNDER25_EN)}
        self.assertEqual(actual_under25, expected_under25)
        self.assertEqual(
            len([url for url in self.sitemap if url.startswith(SITE + HUB)]),
            len(self.selected) + 2 + len(expected_under25),
        )
        self.assertFalse(any(url.startswith(market) and url != market for url in self.sitemap))

    def test_outdated_thin_mobile_page_consolidates_into_real_guide(self):
        old_url = SITE + "/seo/best-mobile-under-15000.html"
        target_url = SITE + "/seo/phones-under-15000.html"
        legacy = (PUBLIC / "seo/best-mobile-under-15000.html").read_text(encoding="utf-8")
        self.assertIn('http-equiv="refresh"', legacy)
        self.assertIn("0; url=" + target_url, legacy)
        self.assertIn('rel="canonical" href="' + target_url + '"', legacy)
        self.assertNotIn(old_url, self.sitemap)
        self.assertIn(target_url, self.sitemap)
        self.assertTrue((PUBLIC / "seo/phones-under-15000.html").is_file())

    def test_no_unreviewed_records_silently_get_seo_pages(self):
        allowed = {slug_for(card) for card in self.selected}
        produced = {p.name for p in (PUBLIC / "phones").iterdir() if p.is_dir()}
        self.assertEqual(produced, allowed | {"india-market-demand-q3-2026", "under-25000"})
        for page in (PUBLIC / "phones" / "india-market-demand-q3-2026").glob("*/index.html"):
            self.assertIn('name="robots" content="noindex,follow"', page.read_text(encoding="utf-8"))
        self.assertFalse((PUBLIC / "phones" / "apple-iphone-11" / "index.html").exists())


if __name__ == "__main__":
    unittest.main()
