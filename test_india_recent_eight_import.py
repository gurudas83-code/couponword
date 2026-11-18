"""Regression checks for eleven new India manufacturer-linked research models."""
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
        self.assertEqual(len(payload["model_cards"]), 11)
        self.assertEqual(len(payload["records"]), 11)
        self.assertEqual({c["brand"] + " " + c["model"] for c in payload["model_cards"]},
                         {"Motorola signature 27", "oppo find x10", "oppo find x10 pro max",
                          "oppo f35 5g", "oppo f35 pro 5g", "vivo v80",
                          "vivo x fold6", "vivo s2 fe", "samsung galaxy f70 5g",
                          "redmi redmi 17c 5g", "realme p4s lite"})
        self.assertEqual(len(APPROVED), 11)
        for card in payload["model_cards"]:
            self.assertEqual(card["status"], "RESEARCH_ONLY")
            self.assertEqual(set(card["specifications"]), set(card["available_specification_fields"]))
            if card["model_key"] in {"samsung|galaxy f70 5g", "redmi|redmi 17c 5g", "realme|p4s lite"}:
                self.assertGreaterEqual(len(card["specifications"]), 5)
                self.assertTrue(all(field["source_url"] == card["manufacturer_page"]
                                    for field in card["specifications"].values()))
            else:
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
            output = Path(folder) / "data/india_recent_manufacturer_research.json"
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), payload)
            page = Path(folder) / "phones/new-india-mobiles/index.html"
            self.assertTrue(page.is_file())
            html = page.read_text(encoding="utf-8")
            for model in ("Samsung Galaxy F70 5G", "REDMI 17C 5G", "realme P4s Lite"):
                self.assertIn(model, html)
            self.assertIn('rel="canonical"', html)


if __name__ == "__main__":
    unittest.main()
