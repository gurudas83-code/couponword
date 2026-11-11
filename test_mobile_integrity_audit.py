#!/usr/bin/env python3
"""Regression guards for all mobile search links and preserved source dates."""
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from python.mobile_research_catalogue import build_public_catalogue
from scripts.mobile_integrity_audit import catalogue_and_audit, safe_url

ROOT = Path(__file__).resolve().parent


class MobileIntegrityAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogue = build_public_catalogue(ROOT)
        cls.report, cls.links = catalogue_and_audit()

    def test_full_corpus_and_merchant_query_coverage(self):
        self.assertEqual(self.report["inventory"]["model_cards"], 232)
        self.assertEqual(self.report["inventory"]["discovery_records"], 235)
        self.assertEqual(self.report["inventory"]["query_corpus"], 1000)
        self.assertEqual(self.report["inventory"]["search_links"], {
            "Amazon": 232, "Flipkart": 232, "Croma": 232,
        })
        self.assertEqual(self.report["blocking_issue_count"], 0)

    def test_all_croma_links_target_phone_not_generic_category(self):
        links = []
        for card in self.catalogue["model_cards"]:
            target = next(x for x in card["retailer_search_links"] if x["retailer"] == "Croma")
            parsed = urlsplit(target["url"])
            self.assertEqual(parsed.path, "/search/")
            self.assertTrue(parse_qs(parsed.query)["text"][0])
            self.assertNotIn("/phones-and-wearables/c/1", target["url"])
            self.assertEqual(target["link_scope"], "MODEL_TARGETED_SEARCH_NOT_VERIFIED_PRODUCT")
            links.append(target["url"])
        # Existing Redmi 13 duplicate identity is flagged, not invented away.
        self.assertEqual(len(set(links)), 231)
        self.assertIn("redmi 13 5g", self.report["duplicate_display_identities"])

    def test_snapshot_dates_retain_evidence_provenance(self):
        dates = [card["research_checked_at"] for card in self.catalogue["model_cards"]]
        self.assertIn("2026-11-03", dates)
        self.assertIn("2026-11-04", dates)
        self.assertTrue(all(date in ("2026-11-03", "2026-11-04") for date in dates))
        self.assertEqual(self.report["inventory"]["historical_budget_references"], 86)
        for card in self.catalogue["model_cards"]:
            ref = card.get("research_budget_reference")
            if ref:
                self.assertFalse(ref["live_offer"])
                self.assertEqual(ref["ranking_weight"], 0)

    def test_network_auditor_refuses_unknown_hosts(self):
        self.assertFalse(safe_url("https://www.amazon.in.evil.example/steal"))
        self.assertFalse(safe_url("http://www.samsung.com/in/"))
        self.assertFalse(safe_url("https://127.0.0.1:8443/"))
        self.assertFalse(safe_url("https://www.amazon.in@attacker.example/"))
        self.assertTrue(safe_url("https://www.croma.com/search/?text=Galaxy%20A56"))


if __name__ == "__main__":
    unittest.main()
