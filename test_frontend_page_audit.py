"""Offline, synthetic regression tests for the generated HTML page-audit reporter."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.frontend_page_audit import audit


class FrontendPageAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "sitemap.xml").write_text(
            '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            '<url><loc>https://coupon-world.in/</loc></url></urlset>', encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_source_linked_indexable_page_is_recorded_without_fabricated_index_status(self):
        html = ('<!doctype html><html lang="en"><head><title>Documented Phone Guide</title>'
                '<meta name="description" content="A practical guide to source-backed phone research">'
                '<link rel="canonical" href="https://coupon-world.in/"></head><body><main>'
                '<h1>Documented Phone Guide</h1><p>' + "Evidence over hype. " * 75 +
                '</p><img src="/phone.svg" alt="Concept phone illustration"></main></body></html>')
        (self.root / "index.html").write_text(html, encoding="utf-8")
        result = audit(self.root)
        self.assertEqual(result["pages_scanned"], 1)
        self.assertEqual(result["indexable_candidates"], 1)
        self.assertFalse(result["pages"][0]["issues"])
        self.assertNotIn("indexed_by_google", json.dumps(result).lower())

    def test_unlicensed_claim_is_not_invented_but_missing_alt_and_affiliate_rel_are_flagged(self):
        (self.root / "index.html").write_text(
            '<html><head><title>Thin Page</title></head><body>'
            '<main><h1>Phone</h1><img src="/device.svg">'
            '<a href="https://www.amazon.in/dp/B012345678" target="_blank">Retailer</a>'
            '</main></body></html>', encoding="utf-8")
        page = audit(self.root)["pages"][0]
        found = {entry["code"] for entry in page["issues"]}
        self.assertIn("IMAGE_MISSING_ALT", found)
        self.assertIn("AMAZON_TAG_MISSING", found)
        self.assertIn("AMAZON_SPONSORED_REL", found)
        self.assertIn("CANONICAL_MISSING_OR_MULTIPLE", found)

    def test_deliberate_noindex_legacy_redirect_is_not_flagged_as_canonical_candidate(self):
        (self.root / "index.html").write_text(
            '<html><head><title>Home</title><meta name="description" content="Intro">'
            '<link rel="canonical" href="https://coupon-world.in/"></head>'
            '<body><main><h1>Home</h1></main></body></html>', encoding="utf-8")
        (self.root / "buying-guides.html").write_text(
            '<html><head><title>Moved</title><meta name="robots" content="noindex,follow">'
            '<meta http-equiv="refresh" content="0; url=https://coupon-world.in/guides/">'
            '<link rel="canonical" href="https://coupon-world.in/guides/">'
            '</head><body><main><h1>Moved</h1></main></body></html>', encoding="utf-8")
        results = audit(self.root)
        redirect = next(x for x in results["pages"] if x["path"] == "buying-guides.html")
        self.assertFalse(redirect["indexable_candidate"])
        self.assertNotIn("SITEMAP_INDEX_CONFLICT", [x["code"] for x in redirect["issues"]])


if __name__ == "__main__":
    unittest.main()
