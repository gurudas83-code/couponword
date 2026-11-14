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
        routes=json.loads(RETIRED.read_text(encoding="utf-8"))['routes']
        self.assertEqual(len(routes),977)
        routes=[r for r in routes if not r.startswith('/answers/') and not r.startswith('/hi/answers/')]
        self.assertTrue(all(not route_file(PUBLIC,r).exists() for r in routes))
        text=(PUBLIC/'404.html').read_text(encoding="utf-8")
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
            html=p.read_text(encoding="utf-8")
            self.assertNotRegex(html,r'name="robots"\s+content="[^"]*noindex')
            canonical=re.search(r'<link\b[^>]*rel="canonical"\s+href="([^"]+)"',html,re.S)
            self.assertIsNotNone(canonical,url)
            self.assertEqual(canonical.group(1),url)
        self.assertTrue(all(SITE+p in urls for p in RETAINED_HUBS))

    def test_retained_internal_navigation_and_guide_inventory_are_real(self):
        for p in PUBLIC.rglob('*.html'):
            for link in Links(p.read_text(encoding="utf-8")).links:
                u=urlsplit(link)
                if not u.netloc and u.path.startswith('/'):
                    self.assertTrue(route_file(PUBLIC,unquote(u.path)).is_file(),(p,link))
        guides=json.loads((PUBLIC/'data/seo-pages.json').read_text(encoding="utf-8"))
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

    def test_comparison_nav_does_not_advertise_retired_pair_pages(self):
        # The earlier hundred template comparison URLs were retired as thin
        # content. Existing navigation must accurately describe the retained
        # English/Hindi methodology guides rather than promise 50 live pairs.
        for relative, old_label, current_label in (
            ("index.html", "50 manufacturer-sourced phone comparisons",
             "Evidence-backed phone comparison guide"),
            ("phones/index.html", "50 manufacturer-sourced phone comparisons",
             "Evidence-backed phone comparison guide"),
            ("hi/phones/index.html", "50 स्रोत-सहित फोन तुलनाएँ",
             "स्रोत-आधारित फोन तुलना गाइड"),
        ):
            html = (PUBLIC / relative).read_text(encoding="utf-8")
            self.assertNotIn(old_label, html, relative)
            self.assertIn(current_label, html, relative)
        self.assertTrue((PUBLIC / "compare/index.html").is_file())
        self.assertTrue((PUBLIC / "hi/compare/index.html").is_file())

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

    def test_discovery_manifest_cites_exact_generated_sitemap_not_google_indexing(self):
        manifest = json.loads((PUBLIC / "data/discovery_release_status.json").read_text(encoding="utf-8"))
        urls = [n.text for n in ET.parse(PUBLIC / "sitemap.xml").getroot().iter()
                if n.tag.endswith("}loc")]
        self.assertEqual(manifest["generated_sitemap_url_count"], len(urls))
        self.assertEqual(sum(manifest["generated_sitemap_categories"].values()), len(urls))
        self.assertEqual(manifest["google_search_console_status"], "NOT_MEASURED")
        self.assertIsNone(manifest["google_indexed_url_count"])
        for url in manifest["priority_urls_verified_in_generated_sitemap"]:
            self.assertIn(url, urls)
        self.assertEqual(len(manifest["priority_urls_verified_in_generated_sitemap"]), 4)

    def test_no_unsubstantiated_review_or_offer_schema(self):
        for p in PUBLIC.rglob('*.html'):
            self.assertNotRegex(p.read_text(encoding="utf-8"),r'"@type"\s*:\s*"(?:Offer|AggregateRating|Review)"',p)

if __name__=='__main__':unittest.main()
