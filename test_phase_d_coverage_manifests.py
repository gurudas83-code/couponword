import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


class PhaseDCoverageManifestTests(unittest.TestCase):
    def test_master_and_gap_counts_are_reconciled(self):
        master = load("mobile_universe_2023_2026.json")
        gap = load("mobile_coverage_gap_2023_2026.json")
        progress = load("mobile_coverage_progress.json")

        self.assertEqual(master["denominator_status"], "COVERAGE_DENOMINATOR_UNVERIFIED")
        self.assertEqual(master["counts"]["discovered_unique_models"], 232)
        self.assertEqual(master["counts"]["discovered_exact_variants"], 147)
        self.assertEqual(gap["counts"]["total_variant_rows"], 237)
        self.assertEqual(progress["cursor"], progress["queue_total"])
        self.assertEqual(progress["queue_remaining"], 0)

    def test_gap_manifest_keeps_unverified_rows_out_of_shopping(self):
        gap = load("mobile_coverage_gap_2023_2026.json")

        self.assertEqual(gap["counts"]["fresh_in_stock_offer_rows"], 0)
        self.assertTrue(all(row["current_fresh_offer"] is False for row in gap["gaps"]))
        self.assertTrue(all(
            row["existing_canonical_id"] is None
            or row["existing_canonical_id"].startswith("cw-mobile-")
            for row in gap["gaps"]
        ))
        self.assertGreater(gap["counts"]["research_only_rows"], 0)

    def test_exact_evidence_admissions_are_durable_knowledge_only_records(self):
        repository = load("mobile_intelligence_repository.json")
        products = repository["products"]

        self.assertGreaterEqual(len(products), 21)
        self.assertIn("dna-oneplus-n6-lite-4gb-64gb", products)
        self.assertIn("dna-samsung-galaxy-a56-5g-8gb-128gb", products)
        self.assertIsNone(products["dna-oneplus-n6-lite-4gb-64gb"]["canonical_product_id"])
        self.assertNotIn("dna-samsung-galaxy-f36-5g-8gb-128gb", products)
        for record in products.values():
            dna = record["dna"]
            self.assertIsNone(record.get("canonical_product_id"))
            self.assertTrue(dna["brand"]["verified"])
            self.assertTrue(dna["model"]["verified"])
            self.assertTrue(dna["ram_gb"]["verified"])
            self.assertTrue(dna["storage_gb"]["verified"])


if __name__ == "__main__":
    unittest.main()
