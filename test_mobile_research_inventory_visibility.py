import json
import unittest
from pathlib import Path

from python.mobile_research_catalogue import build_public_catalogue


ROOT = Path(__file__).resolve().parent


class MobileResearchInventoryVisibilityTests(unittest.TestCase):
    def test_existing_sources_are_reconciled_without_loss(self):
        payload = build_public_catalogue(ROOT)
        counts = payload["source_counts"]
        self.assertEqual(counts["priority_rows"], 187)
        self.assertEqual(counts["wider_models"], 232)
        self.assertEqual(counts["wider_variants"], 237)
        self.assertEqual(counts["priority_rows_represented"], 187)
        self.assertEqual(counts["frozen_verified_variants"], 10)
        self.assertEqual(counts["deduplicated_discovery_records"], len(payload["records"]))
        self.assertGreater(len(payload["records"]), 200)

    def test_statuses_and_keys_are_safe_for_browsing(self):
        payload = build_public_catalogue(ROOT)
        rows = payload["records"]
        self.assertEqual(len({row["record_key"] for row in rows}), len(rows))
        self.assertTrue({row["status"] for row in rows} <= {
            "OFFICIAL_VERIFIED", "PARTIALLY_VERIFIED", "RESEARCH_ONLY", "NEEDS_VERIFICATION"
        })
        self.assertGreater(payload["status_counts"]["OFFICIAL_VERIFIED"], 0)
        for row in rows:
            self.assertNotIn("canonical_product_id", row)
            self.assertNotIn("retailer_url", row)
            self.assertIsNone(row["commerce"]["price"])
            self.assertIsNone(row["commerce"]["stock"])
            self.assertFalse(row["commerce"]["purchase_cta_eligible"])
            if row["status"] == "OFFICIAL_VERIFIED":
                self.assertTrue({"brand", "model", "ram_gb", "storage_gb"} <= set(row["verified_fields"]))

    def test_verified_preview_remains_separate(self):
        preview = json.loads((ROOT / "data/mobile_research_preview.json").read_text(encoding="utf-8"))
        self.assertEqual(len(preview["products"]), 10)
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "mobile-research-preview.js").read_text(encoding="utf-8")
        self.assertIn('id="mobileResearchPreview"', html)
        self.assertIn('id="mobileResearchCatalogue"', html)
        self.assertIn("Explore 232 Smartphone Models", html)
        self.assertIn("235 research records", html)
        self.assertIn("10 frozen verified exact variants", html)
        self.assertIn("/data/mobile_research_catalogue.json", script)
        self.assertIn("no price", script.lower())

    def test_research_filters_have_real_matches(self):
        rows = build_public_catalogue(ROOT)["records"]
        self.assertTrue([row for row in rows if "a36" in (row["brand"] + " " + row["model"]).lower()])
        self.assertTrue([row for row in rows if row["brand"] == "Samsung"])
        self.assertTrue([row for row in rows if row["ram_gb"] == 8])
        self.assertTrue([row for row in rows if row["storage_gb"] == 256])
        self.assertTrue([row for row in rows if row["status"] == "OFFICIAL_VERIFIED"])

    def test_public_images_require_explicit_rights_clearance(self):
        rows = build_public_catalogue(ROOT)["records"]
        self.assertTrue(rows)
        self.assertTrue(all(row["image_status"] == "PLACEHOLDER" for row in rows))
        self.assertTrue(all(row["image_url"] is None for row in rows))


if __name__ == "__main__":
    unittest.main()
