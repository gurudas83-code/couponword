"""Preserve Top30 SEO source-lead vs publication boundary (no live offer claims)."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent

class Top30SourceLeadContract(unittest.TestCase):
    def test_exact_top30_and_gap_partition(self):
        pilot = json.loads((ROOT / "data/top30_research_pilot_20261113.json").read_text(encoding="utf-8"))
        gap = json.loads((ROOT / "data/top30_seo_source_leads_20261113.json").read_text(encoding="utf-8"))
        from python.phone_research_pages import EDITORIAL_MODEL_KEYS
        selected = [x["model_key"] for x in pilot["selected_models"]]
        gated = [x["model_key"] for x in gap["models"]]
        self.assertEqual(len(selected), 30)
        self.assertEqual(len(set(selected)), 30)
        self.assertEqual(len(gated), 20)
        self.assertEqual(len(set(gated)), 20)
        self.assertEqual(set(gated), set(selected) - set(EDITORIAL_MODEL_KEYS))
        self.assertEqual(len(set(selected) & set(EDITORIAL_MODEL_KEYS)), 10)
        self.assertTrue(gap["source_leads_are_not_verified_fields"])
        self.assertTrue(gap["requires_manual_editorial_admission"])
        for item in gap["models"]:
            with self.subTest(key=item["model_key"]):
                self.assertTrue(item["manufacturer_source_leads"])
                self.assertTrue(all(url.startswith("https://") for url in item["manufacturer_source_leads"]))
                self.assertEqual(item["reviewed_distinct_source_fields"], 0)
                self.assertFalse(item["indexable_standalone_page_permitted"])
                self.assertFalse(item["approved_editorial_addition"])

if __name__ == "__main__":
    unittest.main()
