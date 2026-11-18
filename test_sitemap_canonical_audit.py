"""Sitemap publication gates: no 404, noindex, meta refresh or wrong canonical."""
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from scripts.sitemap_canonical_audit import NS, SITE, inspect_url, reconcile, validate


class SitemapAuditTests(unittest.TestCase):
    def build_fixture(self, root):
        paths = {
            "/": ('<link rel="canonical" href="' + SITE + '/">', ""),
            "/phones/": ('<link rel="canonical" href="' + SITE + '/phones/">', ""),
            "/compare/": ('<link rel="canonical" href="' + SITE + '/compare/">', ""),
            "/hi/compare/": ('<link rel="canonical" href="' + SITE + '/hi/compare/">', ""),
            "/seo/valid.html": ('<link rel="canonical" href="' + SITE + '/seo/valid.html">', ""),
            "/seo/old.html": (
                '<meta http-equiv="refresh" content="0;url=/seo/valid.html">'
                '<link rel="canonical" href="' + SITE + '/seo/valid.html">', ""),
            "/seo/draft.html": (
                '<meta name="robots" content="noindex,follow">'
                '<link rel="canonical" href="' + SITE + '/seo/draft.html">', ""),
        }
        outer = ET.Element("{" + NS + "}urlset")
        for route in list(paths) + ["/seo/not-found.html"]:
            node = ET.SubElement(outer, "{" + NS + "}url")
            ET.SubElement(node, "{" + NS + "}loc").text = SITE + route
            if route not in paths:
                continue
            head, _ = paths[route]
            page = root / route.lstrip("/")
            if route.endswith("/"):
                page = page / "index.html"
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_text("<html><head>" + head + "</head><body>Research</body></html>", encoding="utf-8")
        ET.ElementTree(outer).write(root / "sitemap.xml", encoding="utf-8")

    def test_removes_bad_urls_preserves_valid_pages(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.build_fixture(root)
            result = reconcile(root)
            self.assertEqual(result["removed"], 3)
            self.assertEqual(result["retained"], 5)
            self.assertEqual(validate(root)["problems"], [])
            self.assertEqual(result["google_indexed_page_count"], None)
            self.assertTrue((root / "seo/old.html").exists())  # keep old bookmark URLs

    def test_detects_canonical_drift_and_noindex(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.build_fixture(root)
            self.assertEqual(inspect_url(root, SITE + "/seo/draft.html"), "NOINDEX")
            self.assertEqual(inspect_url(root, SITE + "/seo/old.html"), "META_REDIRECT")
            self.assertEqual(inspect_url(root, SITE + "/seo/not-found.html"), "MISSING_PAGE")
            self.assertEqual(inspect_url(root, SITE + "/seo/valid.html"), "OK")

    def test_rejects_unsafe_or_external_sitemap_url(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.build_fixture(root)
            with self.assertRaises(ValueError):
                inspect_url(root, "http://coupon-world.in/seo/valid.html")
            with self.assertRaises(ValueError):
                inspect_url(root, SITE + "/seo/%2e%2e/private.html")


if __name__ == "__main__":
    unittest.main()
