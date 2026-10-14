import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent / "python"))

import retailer_offer_store as store
from retailer_contract import RetailerOffer


class OfferStorePersistenceTests(unittest.TestCase):
    def test_save_replaces_complete_json_without_leaving_temp_files(self):
        with tempfile.TemporaryDirectory(prefix="cw-offer-store-") as directory:
            target = Path(directory) / "retailer_offers.json"
            with patch.object(store, "OFFERS_DB", target):
                store.save_offer_database({"version": 1, "offers": [{"id": "complete"}]})
                self.assertEqual(
                    json.loads(target.read_text(encoding="utf-8")),
                    {"version": 1, "offers": [{"id": "complete"}]},
                )
                self.assertEqual(list(target.parent.glob("*.tmp")), [])

    def test_repeated_exact_admission_remains_idempotent(self):
        offer = RetailerOffer(
            retailer="vivo",
            product_id="cw-mobile-96",
            retailer_product_id="19410",
            brand="Vivo",
            model="T5 Pro 5G",
            variant="8GB/128GB",
            title="vivo T5 Pro 5G 8GB+128GB",
            price=41999,
            availability="in_stock",
            product_url="https://shop.vivo.com/in/product/10344?skuId=19410",
            source="json_ld_offer",
            confidence=0.98,
            metadata={
                "evidence_source_url": "https://shop.vivo.com/in/product/10344?skuId=19410",
                "evidence_source_type": "json_ld_offer",
                "evidence_observed_at": "2026-10-14T17:45:11Z",
            },
        )
        with tempfile.TemporaryDirectory(prefix="cw-offer-store-") as directory:
            target = Path(directory) / "retailer_offers.json"
            with patch.object(store, "OFFERS_DB", target):
                store.add_verified_offer(offer)
                store.add_verified_offer(offer)
                records = store.load_offer_database()["offers"]
                self.assertEqual(len(records), 1)
                self.assertEqual(records[0]["retailer_product_id"], "19410")


if __name__ == "__main__":
    unittest.main()
