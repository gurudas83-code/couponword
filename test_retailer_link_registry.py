from __future__ import annotations

import unittest
from pathlib import Path

from python.mobile_research_catalogue import build_public_catalogue
from python.retailer_link_registry import load_registry_direct_links


ROOT = Path(__file__).resolve().parent


class RetailerLinkRegistryTests(unittest.TestCase):
    def test_registry_exposes_only_direct_reviewed_destinations(self):
        links = load_registry_direct_links(
            ROOT,
            {"samsung|galaxy m36 5g", "redmi|13 5g", "nothing|phone 3"},
        )
        samsung = links[("samsung", "galaxy m36 5g")]
        retailers = {item["retailer"] for item in samsung}
        self.assertEqual(retailers, {"amazon", "flipkart"})
        amazon = next(item for item in samsung if item["retailer"] == "amazon")
        flipkart = next(item for item in samsung if item["retailer"] == "flipkart")
        self.assertIn("/dp/", amazon["url"])
        self.assertIn("tag=guru07cc-21", amazon["url"])
        self.assertNotIn("/s?", amazon["url"])
        self.assertIn("/p/", flipkart["url"])
        self.assertNotIn("/search", flipkart["url"])
        self.assertTrue(all(item["direct_product"] for item in samsung))

    def test_public_catalogue_keeps_search_fallback_separate(self):
        payload = build_public_catalogue(ROOT)
        self.assertEqual(len(payload["model_cards"]), 232)
        direct_cards = [card for card in payload["model_cards"] if card.get("verified_retailer_links")]
        self.assertGreaterEqual(len(direct_cards), 20)
        for card in direct_cards:
            for link in card["verified_retailer_links"]:
                self.assertTrue(link.get("direct_product"))
                self.assertNotIn("/search", link["url"])
                self.assertNotIn("/s?", link["url"])
                if link["retailer"] == "amazon":
                    self.assertIn("tag=guru07cc-21", link["url"])

    def test_frontend_uses_go_to_label_for_direct_links(self):
        source = (ROOT / "mobile-research-preview.js").read_text(encoding="utf-8")
        self.assertIn('label = verified ? "Go to " + store.name + " product"', source)
        self.assertIn('aria-label="Go to Amazon product"', source)
        self.assertIn('aria-label="Search Amazon"', source)


if __name__ == "__main__":
    unittest.main()
