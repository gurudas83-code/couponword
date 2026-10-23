import unittest
from datetime import datetime, timedelta, timezone

from python.cta_eligibility import (
    AUTHORIZED_OFFER_UNAVAILABLE,
    EXACT_VARIANT_UNVERIFIED,
    OUT_OF_STOCK,
    PRICE_EXPIRED,
    PROVIDER_ERROR,
    STOCK_UNKNOWN,
    VERIFIED_BUYABLE,
    evaluate_offer,
)
from python.multi_retailer_page_renderer import render_multi_retailer_section


NOW = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)


def offer(**changes):
    value = {
        "product_id": "cw-mobile-test",
        "retailer": "amazon",
        "retailer_product_id": "B0TEST123",
        "variant": "8GB/128GB",
        "price": 19999,
        "availability": "in_stock",
        "product_url": "https://www.amazon.in/dp/B0TEST123",
        "source": "amazon_primary_buybox",
        "last_checked": "2026-10-22T10:00:00+00:00",
    }
    value.update(changes)
    return value


class Issue12CtaTests(unittest.TestCase):
    def decision(self, **changes):
        return evaluate_offer(offer(**changes), product_id="cw-mobile-test", variant="8GB/128GB", now=NOW)

    def test_valid_exact_current_offer_enables(self):
        self.assertEqual(self.decision()["status"], VERIFIED_BUYABLE)
        self.assertTrue(self.decision()["eligible"])

    def test_variant_identity_and_destination_gates(self):
        self.assertEqual(self.decision(variant="12GB/256GB")["status"], EXACT_VARIANT_UNVERIFIED)
        self.assertEqual(self.decision(retailer_product_id="")["status"], EXACT_VARIANT_UNVERIFIED)
        self.assertEqual(self.decision(product_url="https://example.com/item")["status"], AUTHORIZED_OFFER_UNAVAILABLE)
        self.assertEqual(self.decision(affiliate_url="https://www.amazon.in/dp/B0TEST123", product_url="")["status"], AUTHORIZED_OFFER_UNAVAILABLE)

    def test_source_price_and_timestamp_gates(self):
        for changes in (
            {"source": "market_price_observed"},
            {"price": 0},
            {"price": -1},
            {"last_checked": None},
            {"last_checked": "2026-10-22T13:00:00+00:00"},
            {"last_checked": "2026-10-22T10:00:00"},
        ):
            self.assertFalse(self.decision(**changes)["eligible"])

    def test_stock_and_expiry_gates(self):
        self.assertEqual(self.decision(availability="unknown")["status"], STOCK_UNKNOWN)
        self.assertEqual(self.decision(availability="out_of_stock")["status"], OUT_OF_STOCK)
        self.assertEqual(self.decision(last_checked="2026-10-22T05:59:59+00:00")["status"], PRICE_EXPIRED)

    def test_provider_error_and_missing_offer_fail_closed(self):
        self.assertEqual(evaluate_offer(None, product_id="cw-mobile-test", variant="8GB/128GB", now=NOW)["eligible"], False)
        self.assertEqual(evaluate_offer(offer(), product_id="cw-mobile-test", variant="8GB/128GB", now=NOW, provider_error=True)["status"], PROVIDER_ERROR)

    def test_replay_is_deterministic(self):
        self.assertEqual([self.decision() for _ in range(50)], [self.decision()] * 50)

    def test_static_renderer_hides_expired_purchase_link(self):
        html = render_multi_retailer_section(
            {"id": "test", "category": "mobile"},
            {"cw-mobile-test": {"variant": "8GB/128GB", "offers": [offer(last_checked="2026-10-21T00:00:00+00:00")] }},
        )
        self.assertNotIn("offer-cta", html)
        self.assertIn("Price unavailable", html)

    def test_static_renderer_allows_only_valid_synthetic_offer(self):
        html = render_multi_retailer_section(
            {"id": "test", "category": "mobile"},
            {"cw-mobile-test": {"variant": "8GB/128GB", "offers": [offer(last_checked=(datetime.now(timezone.utc) - timedelta(hours=2)).isoformat())] }},
        )
        self.assertIn("offer-cta", html)
        self.assertIn("₹19,999", html)


if __name__ == "__main__":
    unittest.main()
