"""A retailer ID must resolve to exactly one canonical product."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python"))

import retailer_product_registry as registry


class RegistryOwnerTests(unittest.TestCase):
    def test_duplicate_owner_fails_closed_and_cannot_be_written(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(registry, "REGISTRY_FILE", Path(directory) / "registry.json"):
                registry.register_retailer_product(
                    product_id="cw-mobile-1", retailer="amazon",
                    retailer_product_id="B012345678",
                )
                self.assertEqual(
                    registry.find_canonical_product_id(
                        retailer="amazon", retailer_product_id="b012345678"
                    ), "cw-mobile-1",
                )
                with self.assertRaises(ValueError):
                    registry.register_retailer_product(
                        product_id="cw-mobile-2", retailer="amazon",
                        retailer_product_id="b012345678",
                    )
                self.assertNotIn("cw-mobile-2", registry.load_registry()["products"])

                # Legacy corrupt data must not silently choose the first owner.
                corrupted = registry.load_registry()
                corrupted["products"]["cw-mobile-2"] = {
                    "amazon": {"retailer_product_id": "B012345678"}
                }
                registry.save_registry(corrupted)
                self.assertIsNone(registry.find_canonical_product_id(
                    retailer="amazon", retailer_product_id="B012345678"
                ))


if __name__ == "__main__":
    unittest.main()
