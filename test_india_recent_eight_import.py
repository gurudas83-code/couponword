"""Regression checks for eight new source-only Indian phone research models."""
import json
import tempfile
import unittest
from pathlib import Path

from python.india_recent_eight_import import APPROVED, MODE, build_recent, publish_recent


class RecentIndiaPhonesTests(unittest.TestCase):
    def test_exactly_eight_research_only_and_nonoverlapping(self):
        payload = build_recent()
        self.assertEqual(payload["mode"], MODE)
        self.assertEqual(payload["core_model_count_unchanged"], 232)
        self.assertEqual(len(payload["model_cards"]), 8)
        self.assertEqual(len(payload["records"]), 8)
        self.assertEqual({c["brand"] + " " + c["model"] for c in payload["model_cards"]},
                         {"Motorola signature 27", "oppo find x10", "oppo find x10 pro max",
                          "oppo f35 5g", "oppo f35 pro 5g", "vivo v80",
                          "vivo x fold6", "vivo s2 fe"})
        self.assertEqual(len(APPROVED), 8)
        for card in payload["model_cards"]:
            self.assertEqual(card["status"], "RESEARCH_ONLY")
            self.assertEqual(card["specifications"], {})
            self.assertEqual(card["verified_retailer_links"], [])
            self.assertEqual(card["frozen_variant_ids"], [])
            self.assertIsNone(card["photo"])
            self.assertTrue(card["source_urls"][0].startswith("https://"))
            self.assertEqual({x["retailer"] for x in card["retailer_search_links"]},
                             {"amazon", "flipkart", "croma"})
            self.assertIn("tag=guru07cc-21", card["retailer_search_links"][0]["url"])
            self.assertNotIn("price", card)
            self.assertNotIn("stock", card)

    def test_publish_additive_not_core(self):
        with tempfile.TemporaryDirectory() as folder:
            payload = publish_recent(Path(folder))
            output = Path(folder) / "data/india_recent_eight_research.json"
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), payload)


if __name__ == "__main__":
    unittest.main()
