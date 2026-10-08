"""The retailer adapter must not invent canonical identity for live search."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python"))

import core_multi_retailer_adapter as adapter


class MultiRetailerIdentityTests(unittest.TestCase):
    def setUp(self):
        self.profile = {
            "product_id": "market-12", "asin": "B0HDD3GR8T",
            "title": "Lava Bold N2 5G", "brand": "Lava",
            "category": "smartphone",
            "attributes": {"ram_gb": 4, "storage_gb": 128},
        }
        self.identity = {"brand": "Lava", "model": "Bold N2 5G"}

    def test_unregistered_search_result_has_no_canonical_owner(self):
        with patch.object(adapter, "find_canonical_product_id", return_value=None):
            product = adapter.build_canonical_product(
                profile=self.profile, identity=self.identity,
            )
        self.assertEqual(product.product_id, "")
        self.assertEqual(product.source_product_id, "market-12")
        self.assertEqual(product.identifiers["amazon_asin"], "B0HDD3GR8T")

    def test_exact_registered_asin_can_supply_canonical_owner(self):
        with patch.object(adapter, "find_canonical_product_id", return_value="cw-mobile-72") as lookup, \
             patch.object(adapter, "catalogued_owner", return_value="cw-mobile-72") as catalogued:
            product = adapter.build_canonical_product(
                profile=self.profile, identity=self.identity,
            )
        self.assertEqual(product.product_id, "cw-mobile-72")
        lookup.assert_called_once_with(
            retailer="amazon", retailer_product_id="B0HDD3GR8T"
        )
        catalogued.assert_called_once()

    def test_exact_f70e_source_title_retains_registered_variant(self):
        profile = dict(self.profile, asin="B0GNZSK9HJ", brand="Samsung",
                       title="Samsung Galaxy F70e 5G")
        identity = {"brand": "Samsung", "model": "Galaxy F70e 5G"}
        self.assertEqual(adapter.build_canonical_product(
            profile=profile, identity=identity).product_id, "")
        identity["original_title"] = (
            "Samsung Galaxy F70e 5G (Spotlight Blue, 128 GB) (4 GB RAM) | "
            '6000 mAh Battery | 6.74" PLS LCD Display | Dimensity 6300 | Octa Core Processor |')
        self.assertEqual(adapter.build_canonical_product(
            profile=profile, identity=identity).product_id, "cw-mobile-82")
        identity["original_title"] = identity["original_title"].replace("4 GB RAM", "6 GB RAM")
        self.assertEqual(adapter.build_canonical_product(
            profile=profile, identity=identity).product_id, "")

    def test_registry_owner_with_wrong_catalogue_variant_is_not_reused(self):
        with patch.object(adapter, "find_canonical_product_id", return_value="cw-mobile-72"), \
             patch.object(adapter, "catalogued_owner", return_value=""):
            product = adapter.build_canonical_product(
                profile=self.profile, identity=self.identity,
            )
        self.assertEqual(product.product_id, "")


if __name__ == "__main__":
    unittest.main()
