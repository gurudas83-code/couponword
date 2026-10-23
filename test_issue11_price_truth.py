import unittest
from datetime import datetime, timedelta, timezone

from python.price_truth_audit import (
    CURRENT_VERIFIED,
    HISTORICAL_EXPIRED,
    HISTORICAL_UNVERIFIED,
    PRICE_UNAVAILABLE,
    REFERENCE_PRICE,
    classify_price_record,
    display_price,
)


NOW = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)


def record(**overrides):
    value = {
        "canonical_product_id": "cw-mobile-82",
        "retailer": "amazon",
        "retailer_product_id": "B0GNZSK9HJ",
        "price": 16330,
        "availability": "in_stock",
        "product_url": "https://www.amazon.in/dp/B0GNZSK9HJ",
        "observed_at": "2026-10-21T10:00:00+00:00",
    }
    value.update(overrides)
    return value


class Issue11PriceTruthTests(unittest.TestCase):
    def test_current_verified_requires_six_hour_window(self):
        self.assertEqual(classify_price_record(record(), now=NOW), CURRENT_VERIFIED)
        self.assertEqual(
            classify_price_record(record(observed_at="2026-10-21T05:59:59+00:00"), now=NOW),
            HISTORICAL_EXPIRED,
        )

    def test_expired_and_future_are_not_current(self):
        self.assertEqual(classify_price_record(record(observed_at="2026-10-20T12:00:00+00:00"), now=NOW), HISTORICAL_EXPIRED)
        self.assertEqual(classify_price_record(record(observed_at="2026-10-21T13:00:00+00:00"), now=NOW), HISTORICAL_UNVERIFIED)

    def test_missing_identity_timestamp_stock_or_url_is_unverified(self):
        for changes in (
            {"canonical_product_id": None},
            {"retailer_product_id": None},
            {"observed_at": None},
            {"availability": "unknown"},
            {"product_url": "https://example.invalid/p"},
            {"observed_at": "2026-10-21T10:00:00"},
        ):
            self.assertEqual(classify_price_record(record(**changes), now=NOW), HISTORICAL_UNVERIFIED)

    def test_reference_price_is_not_live_price(self):
        self.assertEqual(classify_price_record(record(price_kind="mrp"), now=NOW), REFERENCE_PRICE)

    def test_missing_and_invalid_price_are_unavailable_or_unverified(self):
        self.assertEqual(classify_price_record(None, now=NOW), PRICE_UNAVAILABLE)
        self.assertEqual(classify_price_record({}, now=NOW), PRICE_UNAVAILABLE)
        self.assertEqual(classify_price_record(record(price="nan"), now=NOW), HISTORICAL_UNVERIFIED)

    def test_display_never_presents_expired_price_as_current(self):
        self.assertEqual(display_price(record(), now=NOW), "₹16,330")
        self.assertEqual(display_price(record(observed_at="2026-10-20T12:00:00+00:00"), now=NOW), "Price unavailable")

    def test_frozen_replay_is_deterministic(self):
        expected = classify_price_record(record(), now=NOW)
        self.assertEqual([classify_price_record(record(), now=NOW) for _ in range(50)], [expected] * 50)


if __name__ == "__main__":
    unittest.main()
