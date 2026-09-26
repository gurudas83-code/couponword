"""Official domain and title must agree on the Lava Bold N2 identity."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "python"))
from resolver_engine import compare_identity
from product_evidence_store import (
    variant_signature_from_specifications,
    variant_signature_from_text,
)


class LavaIdentityTests(unittest.TestCase):
    def test_official_page_does_not_override_explicit_foreign_brand(self):
        url = "https://www.lavamobiles.com/smartphones/bold-n2"
        expected = "Lava Bold N2"
        self.assertEqual(compare_identity(expected, "Bold N2", url, "Lava").decision,
                         "verified")
        self.assertEqual(compare_identity(expected, "Lava Bold N2", url, "Lava").decision,
                         "verified")
        self.assertEqual(compare_identity(expected, "Redmi Bold N2", url, "Lava").decision,
                         "reject")
        self.assertEqual(compare_identity(expected, "Bold N2 Lite", url, "Lava").decision,
                         "reject")
        self.assertEqual(compare_identity("Lava Bold N2 Lite", "Bold N2", url,
                                          "Lava").decision, "reject")

    def test_existing_official_manufacturer_matches_still_work(self):
        for expected, title, brand, url in (
            ("Samsung Galaxy A07 5G", "Samsung Galaxy A07 5G", "Samsung",
             "https://www.samsung.com/in/smartphones/galaxy-a07"),
            ("OnePlus N6 Lite", "OnePlus N6 Lite", "OnePlus",
             "https://www.oneplus.in/n6-lite/specs"),
            ("Xiaomi Redmi 13 5G", "Redmi 13 5G", "Xiaomi",
             "https://www.mi.com/in/product/redmi-13-5g/"),
        ):
            with self.subTest(title=title):
                self.assertEqual(
                    compare_identity(expected, title, url, brand).decision,
                    "verified",
                )

    def test_combined_official_memory_row_requires_one_exact_variant(self):
        for model, listing, official in (
            ("Bold N2", "4 GB RAM, 64 GB Storage", "4GB+4GB* RAM | 64GB ROM"),
            ("Bold N2 Lite", "3 GB RAM, 64 GB Storage", "3GB+3GB* RAM | 64GB ROM"),
        ):
            with self.subTest(model=model):
                requested = variant_signature_from_text(f"{model} ({listing})")
                extracted = variant_signature_from_specifications(
                    {"ram_storage": {"value": official}}
                )
                self.assertEqual(requested, extracted)
        self.assertEqual(
            variant_signature_from_specifications(
                {"ram_storage": "4GB+64GB | 6GB+128GB"}
            ),
            {},
        )
        self.assertEqual(
            variant_signature_from_specifications(
                {"ram": {"value": "4GB+4GB* RAM | 64GB ROM"}}
            ),
            {"ram_gb": "4", "storage_gb": "64"},
        )


if __name__ == "__main__":
    unittest.main()
