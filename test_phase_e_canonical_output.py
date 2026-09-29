"""Canonical IDs must come from a unique registry owner and exact catalogue variant."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python"))
# The attachment contains only the files needed for this patch. The full
# checkout already has the identity gate and evidence store next to registry.
if (ROOT.parent / "couponword-phase-e" / "python").is_dir():
    sys.path.append(str(ROOT.parent / "couponword-phase-e" / "python"))
import retailer_product_registry as registry


class CanonicalOutputTests(unittest.TestCase):
    def test_catalogued_id_requires_exact_asin_model_brand_and_capacity(self):
        base = "Redmi 13 5G Hawaiian Blue (8GB RAM, 128GB Storage)"

        def lookup(title=base, brand="Redmi", asin="B0F1N8B7Z4"):
            return registry.find_catalogued_mobile_id(
                retailer_product_id=asin, candidate_title=title,
                candidate_brand=brand,
            )

        self.assertEqual(lookup(), "cw-mobile-10")
        self.assertIsNone(lookup(asin="B0F1N8B7Z5"))
        self.assertIsNone(lookup(brand="Samsung"))
        self.assertIsNone(lookup(title=base.replace("13 5G", "15 5G")))
        self.assertIsNone(lookup(title=base.replace("8GB RAM", "6GB RAM")))
        self.assertIsNone(lookup(title=base.replace("128GB", "256GB")))
        self.assertIsNone(lookup(title="Redmi 13 5G"))

    def test_duplicate_owner_and_missing_catalogue_fail_closed(self):
        registered = registry.load_registry()
        corrupted = json.loads(json.dumps(registered))
        corrupted["products"]["cw-mobile-999"] = {
            "amazon": {"retailer_product_id": "B0F1N8B7Z4"}
        }
        base = "Redmi 13 5G Hawaiian Blue (8GB RAM, 128GB Storage)"
        with patch.object(registry, "load_registry", return_value=corrupted):
            self.assertIsNone(registry.find_catalogued_mobile_id(
                retailer_product_id="B0F1N8B7Z4", candidate_title=base,
                candidate_brand="Redmi",
            ))
        with tempfile.TemporaryDirectory() as path:
            with patch.object(registry, "ROOT", Path(path)):
                self.assertIsNone(registry.find_catalogued_mobile_id(
                    retailer_product_id="B0F1N8B7Z4", candidate_title=base,
                    candidate_brand="Redmi",
                ))


if __name__ == "__main__":
    unittest.main()
