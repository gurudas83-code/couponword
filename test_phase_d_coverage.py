"""Focused Phase-D coverage checks for exact official-store variants."""

import json
import sys
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python"))

from official_spec_extractor import (
    extract_oneplus_13_configuration_specs,
    extract_vivo_selected_capacity,
)


class PhaseDCoverageTests(unittest.TestCase):
    def test_oneplus_13_configuration_binds_exact_12_256(self):
        soup = BeautifulSoup(
            "<title>OnePlus 13 Specs | OnePlus India</title>"
            "<p>Available configurations: 12GB+256GB / 16GB+512GB</p>",
            "lxml",
        )
        specifications = {}

        extract_oneplus_13_configuration_specs(
            soup,
            "https://www.oneplus.in/13/specs",
            specifications,
        )

        self.assertEqual(specifications["ram"]["value"], "12 GB")
        self.assertEqual(specifications["storage"]["value"], "256 GB")
        self.assertEqual(
            specifications["ram"]["source"],
            "oneplus_official_configuration",
        )

    def test_oneplus_13_parser_rejects_13r_page(self):
        soup = BeautifulSoup(
            "<title>OnePlus 13R Specs | OnePlus India</title>"
            "<p>Available configurations: 12GB+256GB</p>",
            "lxml",
        )
        specifications = {}

        extract_oneplus_13_configuration_specs(
            soup,
            "https://www.oneplus.in/13/specs",
            specifications,
        )

        self.assertEqual(specifications, {})

    def test_iqoo_store_heading_binds_the_requested_physical_variant(self):
        soup = BeautifulSoup(
            "<h1>Neo 10 12GB+256GB Inferno Red</h1>",
            "lxml",
        )
        specifications = {}

        extract_vivo_selected_capacity(
            soup,
            specifications,
            "https://shop.vivo.com/in/product/10325?skuId=19299",
            {
                "brand": "iQOO",
                "model": "Neo 10",
                "original_title": "iQOO Neo 10 12GB RAM 256GB Storage",
            },
            True,
        )

        self.assertEqual(specifications["ram"]["value"], "12 GB")
        self.assertEqual(specifications["storage"]["value"], "256 GB")
        self.assertEqual(
            specifications["ram"]["identity_match"]["variant"],
            {"ram_gb": "12", "storage_gb": "256"},
        )

    def test_iqoo_heading_cannot_be_reused_for_a_different_variant(self):
        soup = BeautifulSoup(
            "<h1>Neo 10 8GB+256GB Inferno Red</h1>",
            "lxml",
        )
        specifications = {}

        extract_vivo_selected_capacity(
            soup,
            specifications,
            "https://shop.vivo.com/in/product/10325?skuId=19299",
            {
                "brand": "iQOO",
                "model": "Neo 10",
                "original_title": "iQOO Neo 10 12GB RAM 256GB Storage",
            },
            True,
        )

        self.assertNotIn("ram", specifications)
        self.assertNotIn("storage", specifications)

    def test_new_records_are_exact_variant_product_dna_only(self):
        payload = json.loads(
            (ROOT / "data" / "verified_product_evidence_cache.json")
            .read_text(encoding="utf-8")
        )
        wanted = {
            ("iQOO", "Neo 10"): {"ram_gb": "12", "storage_gb": "256"},
            ("vivo", "V60"): {"ram_gb": "12", "storage_gb": "256"},
            ("OnePlus", "13R"): {"ram_gb": "12", "storage_gb": "256"},
            ("OnePlus", "13"): {"ram_gb": "12", "storage_gb": "256"},
            ("Samsung", "Galaxy S24"): {"ram_gb": "8", "storage_gb": "256"},
        }
        records = {
            (row.get("brand"), row.get("model")): row
            for row in payload.get("records", [])
            if isinstance(row, dict)
        }
        self.assertTrue(set(wanted).issubset(records))
        for key, signature in wanted.items():
            row = records[key]
            self.assertEqual(row.get("variant_signature"), signature)
            self.assertTrue(row.get("official_url", "").startswith("https://"))
            self.assertTrue(row.get("resolver_verified"))


if __name__ == "__main__":
    unittest.main()
