import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python"))

import product_evidence_store as evidence_store
import retailer_offer_store


class ReviewedT5ProReleaseTests(unittest.TestCase):
    def setUp(self):
        self.bundle = json.loads(
            (ROOT / "data" / "phase_e_release_evidence.json").read_text(encoding="utf-8")
        )
        self.registry = json.loads(
            (ROOT / "data" / "retailer_product_registry.json").read_text(encoding="utf-8")
        )
        self.offers = json.loads(
            (ROOT / "data" / "retailer_offers.json").read_text(encoding="utf-8")
        )

    def test_exact_durable_evidence_retrieval(self):
        row = evidence_store.find_verified_evidence(
            asin="B0H6F4KZGF",
            title="vivo T5 Pro 5G 8GB RAM 128GB Storage",
            store_data={"records": self.bundle["records"]},
        )
        self.assertIsNotNone(row)
        self.assertEqual(row["variant_signature"], {"ram_gb": "8", "storage_gb": "128"})
        self.assertEqual(row["official_url"], "https://shop.vivo.com/in/product/10344?skuId=19410")
        self.assertTrue(row["resolver_verified"])

    def test_asin_and_manufacturer_sku_are_separate(self):
        mapping = self.registry["products"]["cw-mobile-96"]
        self.assertEqual(mapping["amazon"]["retailer_product_id"], "B0H6F4KZGF")
        self.assertEqual(mapping["vivo"]["retailer_product_id"], "19410")
        self.assertNotEqual(
            mapping["amazon"]["retailer_product_id"],
            mapping["vivo"]["retailer_product_id"],
        )

    def test_expired_offer_is_not_in_release_store(self):
        self.assertFalse(
            any(
                row.get("product_id") == "cw-mobile-96"
                and row.get("retailer") == "vivo"
                for row in self.offers.get("offers", [])
            )
        )

    def test_old_t5_offer_fails_freshness_gate(self):
        expired = {
            "product_id": "cw-mobile-96",
            "retailer": "vivo",
            "retailer_product_id": "19410",
            "brand": "Vivo",
            "model": "T5 Pro 5G",
            "variant": "8GB/128GB",
            "price": 41999,
            "availability": "in_stock",
            "product_url": "https://shop.vivo.com/in/product/10344?skuId=19410",
            "source": "json_ld_offer",
            "last_checked": "2026-10-14T17:45:11.794966+00:00",
            "metadata": {
                "evidence_source_url": "https://shop.vivo.com/in/product/10344?skuId=19410",
                "evidence_observed_at": "2026-10-14T17:45:11.794966+00:00",
            },
        }
        with patch.object(
            retailer_offer_store,
            "load_offer_database",
            return_value={"offers": [expired]},
        ):
            self.assertIsNone(
                retailer_offer_store.find_fresh_verified_offer(
                    product_id="cw-mobile-96",
                    brand="Vivo",
                    model="T5 Pro 5G",
                    variant="8GB/128GB",
                    now=datetime(2026, 10, 15, 17, 45, 12, tzinfo=timezone.utc),
                )
            )


if __name__ == "__main__":
    unittest.main()
