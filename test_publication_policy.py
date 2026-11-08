"""Protect the reviewed publication surface, not a target page count."""
import json
import re
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from python.publication_policy import RETIRED, RETAINED_HUBS, SITE, route_file, Links
from urllib.parse import urlsplit,unquote

PUBLIC=Path(__file__).resolve().parent/'public'

class PublicationPolicyTests(unittest.TestCase):
    def test_retired_pages_are_absent_not_soft_404_or_redirect_placeholders(self):
        routes=json.loads(RETIRED.read_text())['routes']
        self.assertEqual(len(routes),977)
        self.assertTrue(all(not route_file(PUBLIC,r).exists() for r in routes))
        self.assertFalse((PUBLIC/'answers').exists())
        self.assertFalse((PUBLIC/'hi/answers').exists())
        text=(PUBLIC/'404.html').read_text()
        self.assertIn('noindex,follow',text)
        self.assertNotIn('refresh',text.lower())
        self.assertNotIn('window.location',text)

    def test_sitemap_contains_only_existing_indexable_self_canonical_pages(self):
        urls=[n.text for n in ET.parse(PUBLIC/'sitemap.xml').getroot().iter() if n.tag.endswith('}loc')]
        self.assertEqual(len(urls),len(set(urls)))
        for url in urls:
            self.assertTrue(url.startswith(SITE+'/'))
            p=route_file(PUBLIC,urlsplit(url).path)
            self.assertTrue(p.is_file(),url)
            html=p.read_text()
            self.assertNotRegex(html,r'name="robots"\s+content="[^"]*noindex')
            canonical=re.search(r'<link\b[^>]*rel="canonical"\s+href="([^"]+)"',html,re.S)
            self.assertIsNotNone(canonical,url)
            self.assertEqual(canonical.group(1),url)
        self.assertTrue(all(SITE+p in urls for p in RETAINED_HUBS))

    def test_retained_internal_navigation_and_guide_inventory_are_real(self):
        for p in PUBLIC.rglob('*.html'):
            for link in Links(p.read_text()).links:
                u=urlsplit(link)
                if not u.netloc and u.path.startswith('/'):
                    self.assertTrue(route_file(PUBLIC,unquote(u.path)).is_file(),(p,link))
        guides=json.loads((PUBLIC/'data/seo-pages.json').read_text())
        self.assertEqual(len(guides),20)
        for g in guides:
            self.assertTrue((PUBLIC/'seo'/(g['slug']+'.html')).is_file())
            self.assertNotIn('keyword',g)

    def test_retained_comparison_guide_has_source_backed_side_by_side_facts(self):
        for route, language in (("compare", "Original source"), ("hi/compare", "मूल स्रोत")):
            page = (PUBLIC / route / "index.html").read_text(encoding="utf-8")
            self.assertIn('id="manufacturer-evidence"', page)
            self.assertIn("Samsung Galaxy A36 5G", page)
            self.assertIn("Samsung Galaxy A56 5G", page)
            self.assertIn(language, page)
            self.assertEqual(page.count('<th scope="row">'), 12)
            self.assertGreaterEqual(page.count('target="_blank"'), 20)
            self.assertIn("https://news.samsung.com/in/", page)
            self.assertIn("https://www.samsung.com/in/", page)
            self.assertNotIn('"@type": "Offer"', page)
            self.assertNotIn('>Buy now<', page)

    def test_homepage_numbers_match_generated_public_research(self):
        home = (PUBLIC / "index.html").read_text(encoding="utf-8")
        data = json.loads((PUBLIC / "data/mobile_research_catalogue.json").read_text(encoding="utf-8"))
        cards = data["model_cards"]
        guides = json.loads((Path(__file__).resolve().parent / "data/phone-guides.json").read_text(encoding="utf-8"))
        values = (
            ("Phone research entries", len(cards)),
            ("With sourced specifications", sum(bool(c.get("specifications")) for c in cards)),
            ("Practical buying guides", len(guides["pages"])),
        )
        for label, value in values:
            self.assertIn(
                "<strong>" + str(value) + "</strong><span>" + label + "</span>",
                home,
            )

    def test_no_unsubstantiated_review_or_offer_schema(self):
        for p in PUBLIC.rglob('*.html'):
            self.assertNotRegex(p.read_text(),r'"@type"\s*:\s*"(?:Offer|AggregateRating|Review)"',p)

if __name__=='__main__':unittest.main()
