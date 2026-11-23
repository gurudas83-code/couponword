import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.refresh_affiliate_offers import load_top30_model_keys, validate_offers


class AffiliatePriceRefreshTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.top30 = load_top30_model_keys()
        cls.now = datetime.now(timezone.utc)

    def row(self, model_key, availability="in_stock"):
        return {
            "model_key": model_key,
            "verification_status": "VERIFIED",
            "source_type": "amazon_pa_api",
            "retailer_product_id": "sku-" + model_key.replace("|", "-"),
            "product_url": "https://www.amazon.in/dp/B012345678",
            "affiliate_url": "https://www.amazon.in/dp/B012345678?tag=couponworld-21",
            "availability": availability,
            "price": 19999,
            "checked_at": (self.now - timedelta(minutes=5)).isoformat(),
        }

    def test_complete_top30_feed_is_admitted(self):
        rows = [self.row(key) for key in sorted(self.top30)]
        admitted = validate_offers(rows, self.now, 6, self.top30)
        self.assertEqual(len(admitted), 30)

    def test_missing_model_rejects_without_partial_update(self):
        rows = [self.row(key) for key in sorted(self.top30)[:-1]]
        with self.assertRaisesRegex(ValueError, "missing_top30_models"):
            validate_offers(rows, self.now, 6, self.top30)

    def test_non_top30_model_is_rejected(self):
        rows = [self.row(key) for key in sorted(self.top30)]
        rows[0]["model_key"] = "not|approved"
        with self.assertRaisesRegex(ValueError, "model_not_in_approved_top30"):
            validate_offers(rows, self.now, 6, self.top30)

    def test_stale_offer_is_rejected(self):
        rows = [self.row(key) for key in sorted(self.top30)]
        rows[0]["checked_at"] = (self.now - timedelta(hours=7)).isoformat()
        with self.assertRaisesRegex(ValueError, "offer_stale"):
            validate_offers(rows, self.now, 6, self.top30)


if __name__ == "__main__":
    unittest.main()

