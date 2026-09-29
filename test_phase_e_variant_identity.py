"""Guard automatic mobile identity reuse against conflicting capacities."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python"))
from mobile_exact_identity_gate import AUTO_REUSE, classify_mobile_identity_reuse


class VariantIdentityTests(unittest.TestCase):
    def test_explicit_ambiguous_capacities_never_auto_merge(self):
        base = "Samsung Galaxy A07 5G"
        expected = f"{base} 4GB RAM 128GB Storage"
        for candidate in (
            f"{base} 4GB RAM 128GB Storage 256GB Storage",
            f"{base} 4GB RAM 8GB RAM 128GB Storage",
        ):
            with self.subTest(candidate=candidate):
                result = classify_mobile_identity_reuse(
                    expected, candidate, "https://www.amazon.in/dp/B000000001",
                    "Samsung",
                )
                self.assertNotEqual(result["status"], AUTO_REUSE)

    def test_priority_seed_wrong_ram_and_storage_not_auto_reused(self):
        products = json.loads(
            (ROOT / "data/mobile_universe_priority_126.json").read_text(
                encoding="utf-8-sig"
            )
        )["products"]
        self.assertEqual(len(products), 126)
        reviewed = 0
        for row in products:
            ram, storage = row.get("ram_gb"), row.get("storage_gb")
            if not ram or not storage:
                continue
            reviewed += 1
            model = f"{row['brand']} {row['model']}"
            expected = f"{model} {ram}GB RAM {storage}GB Storage"
            for candidate in (
                f"{model} {ram * 2}GB RAM {storage}GB Storage",
                f"{model} {ram}GB RAM {storage * 2}GB Storage",
            ):
                with self.subTest(priority=row["priority"], candidate=candidate):
                    result = classify_mobile_identity_reuse(
                        expected, candidate,
                        "https://www.amazon.in/dp/B000000001", row["brand"],
                    )
                    self.assertNotEqual(result["status"], AUTO_REUSE)
        self.assertEqual(reviewed, 125)


if __name__ == "__main__":
    unittest.main()
