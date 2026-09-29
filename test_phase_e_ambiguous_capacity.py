"""One ambiguous listing cannot silently select the first capacity SKU."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python"))
import product_evidence_store as store


class AmbiguousCapacityTests(unittest.TestCase):
    def test_clear_capacity_and_common_physical_ram_are_unambiguous(self):
        for title in (
            "Lava Bold N2 4GB RAM 64GB Storage",
            "Lava Bold N2 Lite 3GB RAM 32GB Storage",
            "Lava Bold N2 32GB RAM 64GB Storage",
            "Lava Bold N2 Lite 3GB+4GB* RAM 64GB Storage",
            "Lava Bold N2 4GB RAM 64GB Storage 512GB expandable memory",
        ):
            with self.subTest(title=title):
                self.assertFalse(store.variant_text_is_ambiguous(title))

    def test_multiple_physical_ram_or_storage_options_are_ambiguous(self):
        for title in (
            "Samsung Galaxy F70e 4GB RAM 8GB RAM 128GB Storage",
            "Samsung Galaxy F70e 4GB RAM 64GB / 128GB Storage",
            "Samsung Galaxy F70e 4GB RAM 64GB Storage 128GB Storage",
        ):
            with self.subTest(title=title):
                self.assertTrue(store.variant_text_is_ambiguous(title))

    def test_ambiguous_exact_asin_cannot_reuse_first_matching_variant(self):
        record = {
            "asin": "B0TEST1234", "brand": "Samsung",
            "model": "Galaxy F70e", "variant_signature": {
                "ram_gb": "4", "storage_gb": "64"
            },
        }
        with patch.object(store, "load_store", return_value={"records": [record]}):
            self.assertIsNotNone(store.find_verified_evidence(
                asin="B0TEST1234", title="Samsung Galaxy F70e 4GB RAM 64GB Storage"
            ))
            self.assertIsNone(store.find_verified_evidence(
                asin="B0TEST1234",
                title="Samsung Galaxy F70e 4GB RAM 64GB Storage 128GB Storage",
            ))


if __name__ == "__main__":
    unittest.main()
