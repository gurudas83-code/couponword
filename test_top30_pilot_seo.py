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
        self.photos = []
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
        if tag == "img" and attrs.get("src", "").startswith("/assets/phone-photos/"):
            self.photos.append(attrs)
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
                title = model_title(model)
                if title.casefold().startswith("redmi redmi "):
                    title = title[len("Redmi "):]
                self.assertIn(title, body)
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

    def test_comparison_matrix_never_expands_unapproved_model_details(self):
        for path, prefix in ((TOP30_EN, "/phones/"), (TOP30_HI, "/hi/phones/")):
            body = self.html[path]
            self.assertIn('class="cw-source-matrix"', body)
            self.assertIn('class="cw-decision-lens"', body)
            # Only the ten admitted canonical detail pages may appear in the
            # comparison matrix. Twenty research-only candidates stay unranked.
            self.assertEqual(body.count('<tr><th scope="row"><a href="' + prefix), 10)
            self.assertNotIn('"@type": "Offer"', body)
            self.assertNotIn('"@type": "Review"', body)
            self.assertIn("स्रोत" if path == TOP30_HI else "source", body)

    def test_licensed_existing_photos_only_with_model_identity_and_credit(self):
        photo_records = json.loads(
            (ROOT / "data/mobile_model_photos.json").read_text(encoding="utf-8")
        )
        expected = {}
        for row in self.pilot["selected_models"]:
            record = photo_records.get(row["model_key"]) or {}
            local = ROOT / str(record.get("url") or "").lstrip("/")
            if (str(record.get("url") or "").startswith("/assets/phone-photos/")
                    and local.is_file()
                    and str(record.get("source") or "").startswith("https://commons.wikimedia.org/wiki/File:")
                    and str(record.get("license_url") or "").startswith("https://creativecommons.org/licenses/")
                    and record.get("author") and record.get("license")
                    and type(record.get("width")) is int and type(record.get("height")) is int
                    and record["width"] > 0 and record["height"] > 0):
                expected[row["model_key"]] = record
        for path in (TOP30_EN, TOP30_HI):
            body = self.html[path]
            parsed = AuditHTML(body)
            self.assertEqual(len(parsed.photos), len(expected))
            self.assertNotIn('"@type": "Offer"', body)
            for key, photo in expected.items():
                card = self.cards[key]
                self.assertIn('src="' + photo["url"] + '"', body)
                photo_title = model_title(card)
                if photo_title.casefold().startswith("redmi redmi "):
                    photo_title = photo_title[len("Redmi "):]
                self.assertIn('alt="' + photo_title + ' model photograph"', body)
                self.assertIn('href="' + photo["source"] + '"', body.replace("&amp;", "&"))
                self.assertIn('href="' + photo["license_url"] + '"', body)
                self.assertIn(photo["author"], body)
            for img in parsed.photos:
                self.assertEqual(img.get("loading"), "lazy")
                self.assertEqual(img.get("decoding"), "async")
                self.assertTrue((ROOT / img["src"].lstrip("/")).is_file())
                self.assertTrue(img.get("alt", "").endswith("model photograph"))

    def test_photo_click_reveals_three_retailer_searches_without_buy_claims(self):
        from urllib.parse import quote_plus
        for path in (TOP30_EN, TOP30_HI):
            body = self.html[path]
            # Every research candidate has a search option, including the 23
            # without a licensed photographed asset.
            self.assertEqual(body.count('<details class="cw-retail-choices">'), 30)
            self.assertEqual(body.count('<nav aria-label="Search retailers for ') if path == TOP30_EN else body.count('<nav aria-label="रिटेलर में खोजें: '), 30)
            for row in self.pilot["selected_models"]:
                model = self.cards[row["model_key"]]
                query = quote_plus(model_title(model))
                self.assertIn("https://www.amazon.in/s?k=" + query + "&amp;tag=guru07cc-21", body)
                self.assertIn("https://www.flipkart.com/search?q=" + query, body)
                self.assertIn("https://www.croma.com/searchB?q=" + query, body)
            self.assertNotIn("Buy Now", body)
            self.assertNotIn("current verified price", body.lower())
            self.assertIn("nofollow sponsored noopener noreferrer", body)
            self.assertGreaterEqual(body.count('target="_blank" rel="nofollow sponsored noopener noreferrer"'), 60)

    def test_bilingual_buyer_intents_use_existing_evidence_gated_routes(self):
        for path in (TOP30_EN, TOP30_HI):
            body = self.html[path]
            for cap in (10000, 15000, 20000, 25000, 30000):
                self.assertIn(
                    'href="/?q=mobile+under+' + str(cap) +
                    '+nearby+band#mobileResearchSearch"', body
                )
            for anchor in ("budget-paths", "buyer-questions", "documented-specs",
                           "top30-faq", "group-editorial", "group-market",
                           "group-historical-demand", "group-control"):
                self.assertIn('id="' + anchor + '"', body)
            for route in ("/seo/camera-phone-buying-guide.html",
                          "/seo/gaming-phone-buying-guide.html",
                          "/seo/5g-phone-india-checklist.html"):
                self.assertIn('href="' + route + '"', body)
            self.assertIn("Redmi Note 15 5G", body)
            self.assertNotIn("Redmi Redmi Note 15 5G", body)
            self.assertIn('"dateModified": "2026-11-20"', body)
            self.assertNotIn('"@type": "FAQPage"', body)
            self.assertNotIn('"@type": "Offer"', body)
            self.assertNotIn('"@type": "Review"', body)
            self.assertNotIn("Buy Now", body)
            self.assertNotIn("₹19,999 current", body)
        for path, terms in (
            (TOP30_EN, ("Which phone should I shortlist for camera, gaming, battery or 5G?",
                        "independently measured best-in-class results",
                        "Are these the 30 best-selling or best-performing phones")),
            (TOP30_HI, ("कैमरा, गेमिंग, बैटरी और 5G",
                        "वास्तविक", "खरीद से पहले अक्सर पूछे सवाल")),
        ):
            for term in terms:
                self.assertIn(term, self.html[path])

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
