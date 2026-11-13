"""Top-30 editorial research hubs: source/SEO integrity, not model performance QA."""
from __future__ import annotations

import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

from python.phone_research_pages import EDITORIAL_MODEL_KEYS, eligible, model_title, slug_for
from python.search_demand_pages import TOP30_EN, TOP30_HI

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
SITE = "https://coupon-world.in"


class AuditHTML(HTMLParser):
    def __init__(self, body: str):
        super().__init__()
        self.canonicals = []
        self.alternates = set()
        self.cards = []
        self.links = []
        self.h1 = 0
        self.feed(body)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonicals.append(attrs.get("href"))
        if tag == "link" and attrs.get("rel") == "alternate":
            self.alternates.add((attrs.get("hreflang"), attrs.get("href")))
        if tag == "h1":
            self.h1 += 1
        if tag == "a":
            self.links.append(attrs.get("href", ""))
        if tag == "article" and "cw-pilot-card" in (attrs.get("class") or "").split():
            self.cards.append(attrs.get("id"))


class Top30ResearchPublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pilot = json.loads(
            (ROOT / "data/top30_research_pilot_20261113.json").read_text(encoding="utf-8")
        )
        catalogue = json.loads(
            (PUBLIC / "data/mobile_research_catalogue.json").read_text(encoding="utf-8")
        )
        cls.cards = {row["model_key"]: row for row in catalogue["model_cards"]}
        cls.approved = {key for key in EDITORIAL_MODEL_KEYS if key in cls.cards and eligible(cls.cards[key])}
        cls.html = {}
        for path in (TOP30_EN, TOP30_HI):
            cls.html[path] = (PUBLIC / path.lstrip("/")).read_text(encoding="utf-8")
        cls.index = {
            x.text for x in ET.parse(PUBLIC / "sitemap.xml").getroot().iter()
            if x.tag.endswith("}loc")
        }

    def test_preserves_thirty_unique_existing_keys_without_ranking(self):
        models = self.pilot["selected_models"]
        keys = [row["model_key"] for row in models]
        self.assertEqual(len(models), 30)
        self.assertEqual(len(set(keys)), 30)
        self.assertTrue(set(keys) <= set(self.cards))
        self.assertTrue(all(row["independent_performance_ranking_eligible_as_of_2026_11_04"] is False for row in models))
        self.assertEqual(
            {g: sum(row["source_group"] == g for row in models)
             for g in ("EDITORIAL", "MARKET", "HISTORICAL_DEMAND", "CONTROL")},
            {"EDITORIAL": 10, "MARKET": 3, "HISTORICAL_DEMAND": 15, "CONTROL": 2},
        )

    def test_two_distinct_indexable_canonical_language_hubs(self):
        for path, language in ((TOP30_EN, "en-IN"), (TOP30_HI, "hi-IN")):
            body = self.html[path]
            parsed = AuditHTML(body)
            self.assertIn('<html lang="' + language + '">', body)
            self.assertEqual(parsed.h1, 1)
            self.assertEqual(parsed.canonicals, [SITE + path])
            self.assertIn(SITE + path, self.index)
            self.assertIn(("en-IN", SITE + TOP30_EN), parsed.alternates)
            self.assertIn(("hi-IN", SITE + TOP30_HI), parsed.alternates)
            self.assertIn('content="index,follow,max-image-preview:large"', body)
            self.assertIn('"@type": "CollectionPage"', body)
            self.assertNotIn('"@type": "Offer"', body)
            self.assertNotIn('"@type": "AggregateRating"', body)
            self.assertEqual(len(parsed.cards), 30)
            self.assertEqual(len(set(parsed.cards)), 30)
            for row in self.pilot["selected_models"]:
                model = self.cards[row["model_key"]]
                self.assertIn(model_title(model), body)
                self.assertIn("phone-" + slug_for(model), parsed.cards)

    def test_link_only_to_already_eligible_detail_pages(self):
        for row in self.pilot["selected_models"]:
            key = row["model_key"]
            model = self.cards[key]
            slug = slug_for(model)
            for path, prefix in ((TOP30_EN, "/phones/"), (TOP30_HI, "/hi/phones/")):
                body = self.html[path]
                detail = prefix + slug + "/"
                if key in self.approved:
                    self.assertIn('href="' + detail + '"', body, key)
                    self.assertTrue((PUBLIC / detail.lstrip("/") / "index.html").is_file())
                else:
                    self.assertNotIn('href="' + detail + '"', body, key)
                    self.assertNotIn(SITE + detail, self.index, key)
                self.assertIn('href="/?q=', body)
        self.assertEqual(len(self.approved), 50)

    def test_standalone_urls_not_mass_generated_without_evidence(self):
        # The 20 non-approved models are discoverable through the research
        # interface; they are not converted into thin, indexable SEO pages.
        keys = [r["model_key"] for r in self.pilot["selected_models"]]
        self.assertEqual(len([k for k in keys if k in self.approved]), 10)
        self.assertEqual(len([k for k in keys if k not in self.approved]), 20)
        for path in (TOP30_EN, TOP30_HI):
            body = self.html[path]
            self.assertIn("https://counterpointresearch.com/", body)
            self.assertIn("https://omdia.tech.informa.com/", body)
            self.assertIn("historical" if path == TOP30_EN else "ऐतिहासिक", body.lower())
            self.assertNotIn('itemprop="price"', body)
            self.assertNotIn("current offer verified", body.lower())
        homepage = (PUBLIC / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="' + TOP30_EN + '"', homepage)


if __name__ == "__main__":
    unittest.main()
