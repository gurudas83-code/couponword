from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python"))

from retailer_publication_gate import evaluate_offer, evaluate_store


class RetailerPublicationGateTests(unittest.TestCase):
    NOW = datetime(2026, 11, 11, 12, 0, tzinfo=timezone.utc)

    def base(self):
        return {
            "product_id": "cw-1",
            "retailer": "amazon",
            "retailer_product_id": "B000000001",
            "product_url": "https://www.amazon.in/dp/B000000001",
            "source_type": "amazon_creators_api",
            "verification_status": "VERIFIED",
            "availability": "in_stock",
            "price": 1999,
            "checked_at": "2026-11-11T10:00:00+00:00",
        }

    def test_current_authorized_exact_offer_is_publishable(self):
        ok, reason = evaluate_offer(self.base(), now=self.NOW, max_age_hours=6)
        self.assertTrue(ok)
        self.assertEqual(reason, "eligible")

    def test_search_url_is_not_publishable(self):
        record = self.base()
        record["product_url"] = "https://www.amazon.in/s?k=phone"
        self.assertEqual(evaluate_offer(record, now=self.NOW, max_age_hours=6)[1], "missing_exact_product_url")

    def test_stale_or_unverified_offer_is_blocked(self):
        record = self.base()
        record["checked_at"] = "2026-11-10T10:00:00+00:00"
        self.assertEqual(evaluate_offer(record, now=self.NOW, max_age_hours=6)[1], "offer_stale")
        record["checked_at"] = "2026-11-11T11:00:00+00:00"
        record["verification_status"] = "RESEARCH_ONLY"
        self.assertEqual(evaluate_offer(record, now=self.NOW, max_age_hours=6)[1], "verification_status_not_verified")

    def test_current_store_is_fail_closed_without_live_feed(self):
        report = evaluate_store(ROOT / "data" / "retailer_offers.json", now=self.NOW)
        self.assertEqual(report["publishable_offer_rows"], 0)
        self.assertEqual(report["status"], "BLOCKED_NO_FRESH_VERIFIED_OFFERS")


if __name__ == "__main__":
    unittest.main()
