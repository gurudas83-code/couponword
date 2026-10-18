"""Focused checks for the first verified Phase-D knowledge batch."""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python"))

from official_spec_extractor import extract_one


class PhaseDVerifiedMobileBatchTests(unittest.TestCase):
    def test_batch_dna_records_are_exact_and_not_shopping_records(self):
        payload = json.loads(
            (ROOT / "data" / "mobile_intelligence_repository.json")
            .read_text(encoding="utf-8")
        )
        expected = {
            "dna-samsung-galaxy-f05-4gb-64gb": ("Samsung", "Galaxy F05", 4, 64),
            "dna-vivo-t4x-6gb-128gb": ("vivo", "T4x 5G", 6, 128),
            "dna-vivo-t5x-6gb-128gb": ("vivo", "T5x 5G", 6, 128),
            "dna-vivo-t5-pro-8gb-128gb": ("vivo", "T5 Pro 5G", 8, 128),
        }
        products = payload.get("products", {})
        for product_id, (brand, model, ram, storage) in expected.items():
            record = products[product_id]
            self.assertIsNone(record.get("canonical_product_id"))
            dna = record["dna"]
            self.assertEqual(dna["brand"]["value"], brand)
            self.assertEqual(dna["model"]["value"], model)
            self.assertEqual(dna["ram_gb"]["value"], ram)
            self.assertEqual(dna["storage_gb"]["value"], storage)
            self.assertTrue(dna["brand"]["verified"])
            self.assertIn("not recommendation eligible", dna["warnings"][0])

    def test_batch_evidence_records_bind_exact_variants(self):
        payload = json.loads(
            (ROOT / "data" / "verified_product_evidence_cache.json")
            .read_text(encoding="utf-8")
        )
        wanted = {
            ("Samsung", "Galaxy F05"): {"ram_gb": "4", "storage_gb": "64"},
            ("vivo", "T4x 5G"): {"ram_gb": "6", "storage_gb": "128"},
            ("vivo", "T5x 5G"): {"ram_gb": "6", "storage_gb": "128"},
            ("vivo", "T5 Pro 5G"): {"ram_gb": "8", "storage_gb": "128"},
        }
        rows = {(row.get("brand"), row.get("model")): row for row in payload["records"]}
        for key, signature in wanted.items():
            row = rows[key]
            self.assertEqual(row.get("variant_signature"), signature)
            self.assertTrue(row.get("resolver_verified"))
            self.assertEqual(row.get("fetch_status"), "success")
            self.assertTrue(row.get("official_url", "").startswith("https://"))

    def test_vivo_selected_sku_capacity_survives_page_cleanup(self):
        html = """
        <html><head><title>vivo T4x 5G | vivo India E-Store</title>
        <link rel="canonical" href="https://shop.vivo.com/in/product/10303?skuId=19292">
        <meta property="og:title" content="vivo T4x 5G"></head>
        <body><header><nav>menu</nav></header>
        <main><h1>T4x 5G 6GB+128GB Glacial Teal</h1>
        <script type="application/ld+json">{"@type":"Product","name":"T4x 5G","brand":{"name":"vivo"},"sku":"19292"}</script>
        </main></body></html>
        """
        with patch(
            "official_spec_extractor.fetch_page",
            return_value=(html, None, 200),
        ):
            output = extract_one(
                {
                    "product_id": "vivo-t4x-6gb-128gb",
                    "core_title": "vivo T4x 5G",
                    "official_url": "https://shop.vivo.com/in/product/10303?skuId=19292",
                    "status": "verified",
                    "verified": True,
                    "resolver_mode": "official",
                },
                {
                    "brand": "vivo",
                    "model": "T4x 5G",
                    "search_name": "vivo T4x 5G",
                    "original_title": "vivo T4x 5G 6GB RAM 128GB Storage",
                },
            )
        self.assertEqual(output["review"]["status"], "candidate_ready")
        self.assertEqual(output["specifications"]["ram"]["value"], "6 GB")
        self.assertEqual(output["specifications"]["storage"]["value"], "128 GB")
        self.assertEqual(
            output["specifications"]["ram"]["source"],
            "official_selected_sku_heading",
        )


if __name__ == "__main__":
    unittest.main()
