import importlib.util
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ISSUE12 = Path(r"C:\Users\HP\Documents\projects\couponword-issue12-cta-gating-20261022")


def load_issue12_cta():
    path = ISSUE12 / "python" / "cta_eligibility.py"
    spec = importlib.util.spec_from_file_location("issue12_cta_eligibility", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CTA = load_issue12_cta()
from python.affiliate_integrity import validate_mapping_destination
NOW = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)


def valid_offer(**changes):
    value = {
        "product_id": "cw-mobile-test",
        "retailer": "amazon",
        "retailer_product_id": "B0TEST1234",
        "variant": "8GB/128GB",
        "price": 19999,
        "availability": "in_stock",
        "product_url": "https://www.amazon.in/dp/B0TEST1234",
        "source": "amazon_primary_buybox",
        "last_checked": "2026-10-22T10:00:00+00:00",
    }
    value.update(changes)
    return value


class Issue13AffiliateIntegrityTests(unittest.TestCase):
    def test_affiliate_or_mapping_alone_is_not_buyable(self):
        for changes in (
            {"price": None, "affiliate_url": "https://www.amazon.in/dp/B0TEST1234?tag=approved-21"},
            {"price": None},
            {"affiliate_url": "https://www.amazon.in/dp/B0TEST1234?tag=approved-21", "availability": "unknown"},
        ):
            with self.subTest(changes=changes):
                result = CTA.evaluate_offer(valid_offer(**changes), product_id="cw-mobile-test", variant="8GB/128GB", now=NOW)
                self.assertFalse(result["eligible"])

    def test_frozen_affiliate_and_offer_matrix(self):
        cases = [
            ("correct mapping no offer", {"price": None}, False),
            ("stale price", {"last_checked": "2026-10-21T00:00:00+00:00"}, False),
            ("unknown stock", {"availability": "unknown"}, False),
            ("out of stock", {"availability": "out_of_stock"}, False),
            ("wrong ram", {"variant": "12GB/128GB"}, False),
            ("wrong storage", {"variant": "8GB/256GB"}, False),
            ("wrong listing id", {"retailer_product_id": "B0OTHER1234"}, False),
            ("affiliate another phone", {"product_url": "https://www.amazon.in/dp/B0OTHER1234", "affiliate_url": "https://www.amazon.in/dp/B0OTHER1234?tag=approved-21"}, False),
            ("missing destination", {"product_url": ""}, False),
            ("unauthorized provider", {"source": "market_price_observed"}, False),
            ("expired observation", {"last_checked": "2026-10-21T05:59:59+00:00"}, False),
            ("MRP only", {"price": None, "mrp": 24999}, False),
            ("conditional discount", {"price": None, "bank_discount": 2000}, False),
            ("valid current offer", {}, True),
            ("invalid retailer domain", {"product_url": "https://shop.example.com/B0TEST1234"}, False),
            ("unapproved redirect", {"product_url": "https://www.amazon.in/gp/redirect.html?url=https://example.com"}, False),
            ("missing merchant id", {"retailer_product_id": ""}, False),
            ("duplicate mapping remains non-offer", {"price": None, "affiliate_url": "https://www.amazon.in/dp/B0TEST1234"}, False),
            ("conflicting same ASIN variant", {"variant": "4GB/128GB"}, False),
            ("failed refresh historical", {"last_checked": "2026-08-01T00:00:00+00:00"}, False),
            ("cached fresh flag ignored", {"freshness": "fresh", "last_checked": "2026-08-01T00:00:00+00:00"}, False),
            ("Issue12 disabled CTA status", {"availability": "unknown"}, False),
            ("specialist same hard gate", {"availability": "unknown"}, False),
            ("strict budget does not enable", {"price": 999999}, True),
            ("no live offer", {"price": None, "availability": "unknown"}, False),
        ]
        self.assertEqual(len(cases), 25)
        for label, changes, expected in cases:
            with self.subTest(label=label):
                candidate = valid_offer(**changes)
                mapping = validate_mapping_destination(candidate, expected_retailer="amazon", expected_retailer_product_id="B0TEST1234")
                result = CTA.evaluate_offer(candidate, product_id="cw-mobile-test", variant="8GB/128GB", now=NOW) if mapping["valid"] else {"eligible": False}
                self.assertEqual(result["eligible"], expected)

    def test_issue12_positive_and_protected_identity(self):
        positive = CTA.evaluate_offer(valid_offer(), product_id="cw-mobile-test", variant="8GB/128GB", now=NOW)
        self.assertEqual(positive["status"], CTA.VERIFIED_BUYABLE)
        wrong_product = CTA.evaluate_offer(valid_offer(product_id="cw-other"), product_id="cw-mobile-test", variant="8GB/128GB", now=NOW)
        self.assertFalse(wrong_product["eligible"])

    def test_fifty_replays_are_deterministic(self):
        expected = CTA.evaluate_offer(valid_offer(), product_id="cw-mobile-test", variant="8GB/128GB", now=NOW)
        self.assertEqual([CTA.evaluate_offer(valid_offer(), product_id="cw-mobile-test", variant="8GB/128GB", now=NOW) for _ in range(50)], [expected] * 50)

    def test_actual_source_files_remain_readable(self):
        registry = json.loads((ROOT / "data" / "retailer_product_registry.json").read_text(encoding="utf-8"))
        self.assertEqual(len(registry["products"]), 37)
        self.assertTrue((ISSUE12 / "python" / "cta_eligibility.py").is_file())


if __name__ == "__main__":
    unittest.main()
