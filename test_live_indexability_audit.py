"""Controlled regression tests for read-only live indexing baseline reporting."""
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from scripts.live_indexability_audit import audit, check_page
from scripts.sitemap_canonical_audit import SITE, NS


def fake_response(status, canonical="", robots="", final_url="", body=None):
    if body is None:
        body = ('<html><head><link rel="canonical" href="' + canonical + '">'
                '<meta name="robots" content="' + robots + '"></head><body><h1>Research</h1></body></html>')
    return {"status": status, "final_url": final_url,
            "content_type": "text/html", "body": body, "x_robots_tag": ""}


class LiveIndexabilityTests(unittest.TestCase):
    def test_good_page_and_noindex_are_not_confused_with_google_indexing(self):
        good = SITE + "/phones/"
        result = check_page(good, getter=lambda url: fake_response(200, good, "index,follow", url))
        self.assertEqual(result["status"], "PASS")
        self.assertNotIn("indexed_by_google", result)
        bad = check_page(good, getter=lambda url: fake_response(200, good, "noindex,follow", url))
        self.assertEqual(bad["status"], "NOINDEX")

    def test_redirect_and_mismatched_canonical_are_detected(self):
        good = SITE + "/seo/guide.html"
        redirected = check_page(good, getter=lambda url: fake_response(200, good, "index", SITE + "/"))
        self.assertEqual(redirected["status"], "REDIRECTED")
        bad = check_page(good, getter=lambda url: fake_response(200, SITE + "/other.html", "index", url))
        self.assertEqual(bad["status"], "CANONICAL_MISMATCH")

    def test_generated_sitemap_and_live_parity_are_independent(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            urls = [SITE + "/", SITE + "/phones/"]
            xml = ET.Element("{" + NS + "}urlset")
            for url in urls:
                entry = ET.SubElement(xml, "{" + NS + "}url")
                ET.SubElement(entry, "{" + NS + "}loc").text = url
            ET.ElementTree(xml).write(root / "sitemap.xml", encoding="utf-8")
            raw = (root / "sitemap.xml").read_text(encoding="utf-8")
            def getter(url):
                if url.endswith("/sitemap.xml"):
                    return {"status": 200, "body": raw, "content_type": "application/xml",
                            "final_url": url}
                expected = url
                return fake_response(200, expected, "index,follow", url)
            result = audit(root, getter=getter, workers=2)
            self.assertEqual(result["expected_sitemap_urls"], 2)
            self.assertEqual(result["live_sitemap_urls"], 2)
            self.assertEqual(result["sitemap_parity"], "MATCH")
            self.assertEqual(result["statuses"], {"PASS": 2})
            self.assertIsNone(result["google_indexed_count"])


if __name__ == "__main__":
    unittest.main()
