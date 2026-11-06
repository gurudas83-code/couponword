"""Ten independent quality contracts for the Hindi phone SEO publication layer."""
from __future__ import annotations

import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET

from python.phone_research_pages import EDITORIAL_MODEL_KEYS, accepted_specs, eligible, slug_for
from python.phone_hindi_pages import BUDGETS, GUIDE_COPY
from python.under25_seo_pages import HI as UNDER25_HI, CATEGORY_TEXT as UNDER25_CATEGORIES, valid_data as under25_data, pth as under25_path
from python.mobile_seo_comparisons import HI as COMPARE_HI, SOURCE as COMPARE_SOURCE, path_for as compare_path

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
SITE = "https://coupon-world.in"

class Parsed(HTMLParser):
    def __init__(self, content):
        super().__init__()
        self.links, self.canonical, self.alternates, self.h1, self.lang = [], [], [], 0, None
        self.feed(content)
    def handle_starttag(self, name, attrs):
        d = dict(attrs)
        if name == "html": self.lang = d.get("lang")
        if name == "h1": self.h1 += 1
        if name == "link" and d.get("rel") == "canonical": self.canonical.append(d.get("href"))
        if name == "link" and d.get("rel") == "alternate": self.alternates.append((d.get("hreflang"),d.get("href")))
        if name == "a": self.links.append(d.get("href") or "")

def get(route):
    target = PUBLIC / route.lstrip("/")
    if route.endswith("/"): target /= "index.html"
    return target.read_text(encoding="utf-8")

class HindiSEOContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.guides=json.loads((ROOT/"data/phone-guides.json").read_text(encoding="utf-8"))["pages"]
        catalogue=json.loads((PUBLIC/"data/mobile_research_catalogue.json").read_text(encoding="utf-8"))
        cards={c["model_key"]: c for c in catalogue["model_cards"]}
        cls.phones=[cards[k] for k in EDITORIAL_MODEL_KEYS if k in cards and eligible(cards[k])]
        cls.cards=cards
        cls.comparison_intake=json.loads(COMPARE_SOURCE.read_text(encoding="utf-8"))["pairs"]
        cls.routes=["/hi/seo/"+g["slug"]+".html" for g in cls.guides]
        cls.routes+=["/hi/phones/"+slug_for(card)+"/" for card in cls.phones]
        cls.routes+=["/hi/guides/phone-budget-guides/","/hi/phones/","/hi/budgets/"]
        cls.sitemap={e.text for e in ET.parse(PUBLIC/"sitemap.xml").getroot().iter() if e.tag.endswith("}loc")}

    def test_01_exact_twenty_english_topic_mirrors(self):
        self.assertEqual(len(self.guides),20)
        self.assertEqual(set(GUIDE_COPY),{p["slug"] for p in self.guides})
        for page in self.guides:
            self.assertIn("हिंदी",get("/hi/seo/"+page["slug"]+".html"))
            self.assertTrue((PUBLIC/"seo"/(page["slug"]+".html")).is_file())

    def test_02_exact_fifty_eligible_model_mirrors(self):
        self.assertEqual(len(self.phones),50)
        self.assertEqual(len({slug_for(c) for c in self.phones}),50)
        for card in self.phones:
            self.assertTrue((PUBLIC/"phones"/slug_for(card)/"index.html").is_file())
            self.assertIn("स्पेसिफिकेशन",get("/hi/phones/"+slug_for(card)+"/"))

    def test_03_unique_hindi_canonical_urls_and_single_h1(self):
        self.assertEqual(len(self.routes),73)
        self.assertEqual(len(set(self.routes)),73)
        for route in self.routes:
            parsed=Parsed(get(route))
            self.assertEqual(parsed.lang,"hi-IN",route)
            self.assertEqual(parsed.h1,1,route)
            self.assertEqual(parsed.canonical,[SITE+route],route)

    def test_04_self_referencing_english_and_hindi_hreflang(self):
        pairs=[("/seo/"+p["slug"]+".html","/hi/seo/"+p["slug"]+".html") for p in self.guides]
        pairs += [("/phones/"+slug_for(c)+"/","/hi/phones/"+slug_for(c)+"/") for c in self.phones]
        pairs += [("/phones/","/hi/phones/"),("/guides/phone-budget-guides/","/hi/guides/phone-budget-guides/")]
        for english,hindi in pairs:
            required={("en-IN",SITE+english),("hi-IN",SITE+hindi)}
            self.assertTrue(required<=set(Parsed(get(english)).alternates),english)
            self.assertTrue(required<=set(Parsed(get(hindi)).alternates),hindi)

    def test_05_manufacturer_evidence_links_and_values_kept(self):
        for card in self.phones:
            page=get("/hi/phones/"+slug_for(card)+"/")
            links=set(Parsed(page).links)
            for _,value in accepted_specs(card):
                self.assertIn(str(value["source_url"]),links,card["model_key"])
            self.assertIn("कीमत",page)

    def test_06_hindi_indexables_in_sitemap_and_no_english_duplicates(self):
        for route in self.routes:
            self.assertIn(SITE+route,self.sitemap,route)
        # Original 73 Hindi pages plus the separately-reviewed under-25k
        # pages. One naming-ambiguous model stays noindex in both languages.
        expected_under25 = {
            SITE + UNDER25_HI,
            *(SITE + UNDER25_HI + "best-" + category + "/" for category in UNDER25_CATEGORIES),
            *(SITE + under25_path(model, hi=True) for model in under25_data()["models"]
              if model["manufacturer_scope"] != "MODEL_NAMING_ALIAS_REQUIRES_REVIEW"),
        }
        self.assertEqual(
            {u for u in self.sitemap if u.startswith(SITE + UNDER25_HI)},
            expected_under25,
        )
        expected_compare = {
            SITE + COMPARE_HI,
            *(SITE + compare_path(self.cards[p["left"]], self.cards[p["right"]], True)
              for p in self.comparison_intake),
        }
        self.assertEqual(len(expected_compare), 51)
        self.assertEqual(
            {u for u in self.sitemap if u.startswith(SITE + COMPARE_HI)},
            expected_compare,
        )
        self.assertEqual(
            {u for u in self.sitemap if u.startswith(SITE + "/hi/")},
            {SITE + route for route in self.routes} | expected_under25 | expected_compare
            | {SITE+'/hi/answers/'}
            | {SITE+x['hindi_route'] for x in json.loads((PUBLIC/'data/mobile_query_answer_coverage.json').read_text())['answers'] if x['indexable']},
        )

    def test_07_all_nineteen_budget_bands_exist_but_not_indexed(self):
        self.assertEqual(BUDGETS,tuple(range(10000,100001,5000)))
        self.assertEqual(len(BUDGETS),19)
        for amount in BUDGETS:
            route=f"/hi/budgets/{amount}/"
            page=get(route)
            self.assertIn('content="noindex,follow"',page)
            self.assertNotIn(SITE+route,self.sitemap)
            self.assertIn(f"₹{amount:,}",page)

    def test_08_no_fabricated_top_three_or_live_offer(self):
        for amount in BUDGETS:
            page=get(f"/hi/budgets/{amount}/")
            self.assertEqual(page.count("प्रमाणित Top-3 उपलब्ध नहीं"),3)
            self.assertNotIn("Offer",page)
            self.assertNotIn("AggregateRating",page)

    def test_09_price_is_budget_only_not_performance_rank(self):
        for amount in BUDGETS:
            page=get(f"/hi/budgets/{amount}/")
            self.assertIn("0%",page)
            self.assertIn("पुराने",page)
            self.assertNotIn('"@type": "Product"',page)

    def test_10_no_broken_internal_hindi_links(self):
        for route in self.routes:
            page=get(route)
            self.assertNotIn("noindex",page)
            for href in Parsed(page).links:
                url=urlsplit(href)
                if not url.path.startswith("/hi/"): continue
                target=PUBLIC/unquote(url.path).lstrip("/")
                self.assertTrue(target.is_file() or (target/"index.html").is_file(),
                                (route,href))

if __name__ == "__main__":
    unittest.main()
