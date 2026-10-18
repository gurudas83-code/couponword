import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class ProductDnaDuplicatePreventionTests(unittest.TestCase):
    def test_committed_dna_has_one_product_per_source_variant(self):
        payload = json.loads(
            (ROOT / "data" / "mobile_intelligence_repository.json").read_text(
                encoding="utf-8"
            )
        )
        seen = {}
        duplicates = []
        for product_id, wrapper in payload.get("products", {}).items():
            dna = wrapper.get("dna", {}) if isinstance(wrapper, dict) else {}
            ram = dna.get("ram_gb", {}).get("value")
            storage = dna.get("storage_gb", {}).get("value")
            for field in dna.values():
                if not isinstance(field, dict) or not field.get("source_url"):
                    continue
                key = (str(field["source_url"]).rstrip("/"), str(ram), str(storage))
                if key in seen and seen[key] != product_id:
                    duplicates.append((key, seen[key], product_id))
                seen[key] = product_id
        self.assertEqual(duplicates, [])


if __name__ == "__main__":
    unittest.main()
