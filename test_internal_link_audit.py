"""Homepage discovery audits never confuse XML sitemaps with HTML links."""
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from scripts.internal_link_audit import SITE, audit, verify_priority


def fixture(root):
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    outer = ET.Element(ns + "urlset")
    paths = ["/", "/phones/", "/seo/phones-under-15000.html",
             "/seo/hidden.html"]
    for route in paths:
        node = ET.SubElement(outer, ns + "url")
        ET.SubElement(node, ns + "loc").text = SITE + route
        file = root / route.lstrip("/")
        if route.endswith("/"):
            file = file / "index.html"
        file.parent.mkdir(parents=True, exist_ok=True)
        markup = '<a href="/phones/">Phones</a><a href="/seo/phones-under-15000.html">Under 15k</a>' if route == "/" else "<h1>Research</h1>"
        file.write_text("<html><body>" + markup + "</body></html>", encoding="utf-8")
    ET.ElementTree(outer).write(root / "sitemap.xml", encoding="utf-8")


class GraphTests(unittest.TestCase):
    def test_sitemap_does_not_make_an_orphan_discoverable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root)
            result = audit(root)
            self.assertEqual(result["sitemap_indexable_url_count"], 4)
            self.assertEqual(result["sitemap_urls_reachable_from_home"], 3)
            self.assertEqual(result["sitemap_urls_without_homepage_link_path"], 1)
            self.assertIn(SITE + "/seo/hidden.html", result["unreachable_urls"])
            self.assertEqual(result["priority_guide_click_depth"]["/seo/phones-under-15000.html"], 1)
            self.assertIsNone(result["google_indexed_count"])

    def test_query_and_fragment_are_not_separate_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root)
            home = root / "index.html"
            home.write_text('<a href="/seo/phones-under-15000.html?q=test#intro">Guide</a>', encoding="utf-8")
            result = audit(root)
            self.assertEqual(result["priority_guide_click_depth"]["/seo/phones-under-15000.html"], 1)


if __name__ == "__main__":
    unittest.main()
