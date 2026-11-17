"""Read-only fixture tests; no API key, network, offer-store writes or deploy."""
from __future__ import annotations
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python"))

from canonical_product import CanonicalProduct
from quickcommerce_flipkart_adapter import (
    SOURCE, QuickCommerceFlipkartConnector, normalize_search_response, dry_run
)
from retailer_publication_gate import evaluate_offer

FIXTURE = ROOT / "tests" / "fixtures" / "quickcommerce_flipkart_a56_search.json"


def product(color="Light Violet", variant="8GB/128GB", model="Galaxy A56 5G"):
    return CanonicalProduct(
        product_id="cw-api-dryrun-a56", title="Samsung Galaxy A56 5G",
        brand="Samsung", model=model, variant=variant, category="Mobiles",
        identifiers={}, attributes={"color": color}, source_product_id="fixture",
        confidence=0.9
    )


class QuickCommerceFlipkartAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_exact_variant_and_price(self):
        offer = QuickCommerceFlipkartConnector(fixture=self.payload).get_offer(product())
        self.assertEqual(offer.retailer, "flipkart")
        self.assertEqual(offer.retailer_product_id, "MOBHQBDXXJUDBFVH")
        self.assertEqual(offer.price, 33175.0)
        self.assertEqual(offer.mrp, 49999.0)
        self.assertEqual(offer.availability, "in_stock")
        self.assertEqual(offer.source, SOURCE)
        self.assertFalse(offer.metadata["publication_authorized"])
        self.assertEqual(offer.last_checked, "")  # fixture is not a fresh observation

    def test_wrong_ram_storage_color_or_model_fails_closed(self):
        for row in (
            product(variant="12GB/128GB"),
            product(variant="8GB/512GB"),
            product(color="Green"),
            product(model="Galaxy A56 Plus"),
        ):
            self.assertIsNone(QuickCommerceFlipkartConnector(fixture=self.payload).get_offer(row))

    def test_strict_item_link_identity(self):
        payload = copy.deepcopy(self.payload)
        payload["data"]["products"][1]["deeplink"] = "https://www.flipkart.com/-/p/-?pid=WRONGPID"
        self.assertIsNone(QuickCommerceFlipkartConnector(fixture=payload).get_offer(product()))

    def test_out_of_stock_never_becomes_buyable(self):
        payload = copy.deepcopy(self.payload)
        payload["data"]["products"][1]["available"] = False
        payload["data"]["products"][1]["offer_price"] = 0
        offer = QuickCommerceFlipkartConnector(fixture=payload).get_offer(product())
        self.assertEqual(offer.availability, "out_of_stock")
        self.assertIsNone(offer.price)

    def test_wrong_or_missing_price_rejected(self):
        payload = copy.deepcopy(self.payload)
        payload["data"]["products"][1]["offer_price"] = 0
        self.assertIsNone(QuickCommerceFlipkartConnector(fixture=payload).get_offer(product()))

    def test_publication_gate_rejects_quickcommerce(self):
        offer = QuickCommerceFlipkartConnector(fixture=self.payload).get_offer(product())
        record = offer.to_dict()
        record.update({
            "verification_status": "VERIFIED",
            "source_type": SOURCE,
            "checked_at": "2026-11-16T12:00:00+00:00",
        })
        from datetime import datetime, timezone
        ok, reason = evaluate_offer(
            record, now=datetime(2026, 11, 16, 12, 1, tzinfo=timezone.utc),
            max_age_hours=6,
        )
        self.assertFalse(ok)
        self.assertEqual(reason, "source_not_authorized")

    def test_dry_run_never_publishes(self):
        result = dry_run(FIXTURE, product())
        self.assertEqual(result["price_observation"], 33175.0)
        self.assertIs(result["publishable"], False)

    def test_live_request_is_private_and_stays_research_only(self):
        from urllib.parse import parse_qs, urlsplit
        from unittest.mock import patch
        requests = []

        class Response:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, size=-1):
                return json.dumps(QuickCommerceFlipkartAdapterTests.payload).encode("utf-8")

        def fake_open(request, timeout):
            requests.append((request, timeout))
            return Response()

        with patch.dict("os.environ", {"QUICKCOMMERCE_API_KEY": "TEST_PRIVATE_KEY"}):
            offer = QuickCommerceFlipkartConnector(opener=fake_open).get_offer(product())
        self.assertEqual(len(requests), 1)
        request, timeout = requests[0]
        self.assertEqual(timeout, 15)
        self.assertTrue(request.full_url.startswith("https://api.quickcommerceapi.com/v1/search?"))
        self.assertNotIn("TEST_PRIVATE_KEY", request.full_url)
        self.assertEqual(request.get_header("X-api-key"), "TEST_PRIVATE_KEY")
        query = parse_qs(urlsplit(request.full_url).query)
        self.assertEqual(query["platform"], ["Flipkart"])
        self.assertEqual(query["pincode"], ["110001"])
        self.assertEqual(offer.price, 33175.0)
        self.assertEqual(offer.source, SOURCE)
        self.assertFalse(offer.metadata["publication_authorized"])

    def test_rejects_untrusted_schema_and_invalid_price_types(self):
        bad = copy.deepcopy(self.payload)
        bad["data"]["platform"] = "Amazon"
        with self.assertRaises(ValueError):
            normalize_search_response(bad, product())
        bad = copy.deepcopy(self.payload)
        bad["data"]["products"][1]["offer_price"] = "NaN"
        self.assertIsNone(normalize_search_response(bad, product()))
        bad = copy.deepcopy(self.payload)
        bad["data"]["products"][1]["currency"] = "USD"
        with self.assertRaises(ValueError):
            normalize_search_response(bad, product())
        bad = copy.deepcopy(self.payload)
        bad["data"]["products"][1]["available"] = "true"
        self.assertIsNone(normalize_search_response(bad, product()))

    def test_smoke_script_defaults_to_offline_and_never_publishes(self):
        import importlib.util
        path = ROOT / "scripts" / "quickcommerce_flipkart_smoke.py"
        spec = importlib.util.spec_from_file_location("quickcommerce_flipkart_smoke", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.run(live=False)
        self.assertEqual(result["status"], "RESEARCH_ONLY")
        self.assertEqual(result["retailer_product_id"], "MOBHQBDXXJUDBFVH")
        self.assertEqual(result["price_observation"], 33175.0)
        self.assertFalse(result["publishable"])

    def test_invalid_pincode_rejected_without_request(self):
        for invalid in ("", "000000", "11001", "1100010", "ABCDEF"):
            with self.assertRaises(ValueError):
                QuickCommerceFlipkartConnector(pincode=invalid)

    def test_live_requires_private_key(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ, {"QUICKCOMMERCE_API_KEY": ""}):
            with self.assertRaises(RuntimeError):
                QuickCommerceFlipkartConnector().get_offer(product())


if __name__ == "__main__":
    unittest.main()
