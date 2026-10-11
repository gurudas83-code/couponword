import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
sys.path.insert(0, str(Path(__file__).resolve().parent / "python"))
import retail_price_evidence as prices


class PriceTimestampTests(unittest.TestCase):
    candidate = {"source_url": "https://www.amazon.in/dp/B0GL1WGHJX", "source_host": "www.amazon.in",
                 "asin": "B0GL1WGHJX"}

    def test_cache_keeps_observed_time_and_does_not_claim_live_stock(self):
        observed = (datetime.now(timezone.utc)-timedelta(hours=2)).isoformat()
        with patch.object(prices, "get_recent_cached_price", return_value={"price": 7999, "verified_at": observed}), \
             patch.object(prices, "fetch_structured_price") as fetch:
            result = prices.build_price_evidence(self.candidate)
        self.assertEqual(result["verified_at"], observed)
        self.assertEqual(result["availability"], "unknown")
        fetch.assert_not_called()

    def test_fresh_page_has_price_source_timestamp_and_stock(self):
        with patch.object(prices, "get_recent_cached_price", return_value=None), \
             patch.object(prices, "cache_verified_price"), \
             patch.object(prices, "fetch_structured_price", return_value={"status": "verified", "price": 7999,
                 "availability": "in_stock", "evidence_method": "amazon_primary_buybox"}):
            result = prices.build_price_evidence(self.candidate)
        self.assertTrue(result["verified"])
        self.assertEqual(result["source_url"], self.candidate["source_url"])
        self.assertEqual(result["availability"], "in_stock")
        self.assertLess(abs((datetime.now(timezone.utc)-datetime.fromisoformat(result["verified_at"])).total_seconds()), 5)

    def test_failed_page_without_fresh_cache_is_not_verified(self):
        with patch.object(prices, "get_recent_cached_price", return_value=None), \
             patch.object(prices, "fetch_structured_price", return_value={"status": "blocked"}):
            result = prices.build_price_evidence(self.candidate)
        self.assertFalse(result["verified"])
        self.assertIsNone(result["price"])


if __name__ == "__main__":
    unittest.main()
