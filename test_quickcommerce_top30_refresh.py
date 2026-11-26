import copy
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.refresh_quickcommerce_affiliate_offers import (
    TOP30_COUNT,
    build_offer,
    load_top30_targets,
    merge_with_previous_store,
    refresh_targets,
    select_exact_listing,
)
from scripts.quickcommerce_catalogue_audit import query_for


ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "tests" / "fixtures" / "quickcommerce_flipkart_a56_search.json"


class FakeConnector:
    def __init__(self, payloads, observed, pincode="110001"):
        self.payloads = payloads
        self.observed = observed
        self.pincode = pincode
        self.calls = []

    def search(self, query):
        self.calls.append(query)
        return self.payloads[query], self.observed


class QuickCommerceTop30RefreshTests(unittest.TestCase):
    def test_provider_query_normalizes_parenthesized_phone_name(self):
        row = {"brand": "Nothing", "model": "Phone (3a)"}
        self.assertEqual(query_for(row), "Nothing Phone 3a")

    def test_existing_fixture_produces_one_exact_physical_variant(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        row = {
            "audit_id": "samsung|galaxy a56 5g",
            "brand": "Samsung",
            "model": "Galaxy A56 5G",
            "category": "mobiles",
        }
        item, variant = select_exact_listing(payload, row)
        self.assertEqual(item["id"], "MOBHQBE6G85PXAYG")
        self.assertEqual(variant["variant"], "8GB/128GB · Dark Blue")
        offer = build_offer(
            item,
            variant,
            row,
            observed_at="2026-11-23T10:00:00+00:00",
            pincode="110001",
            request_id="fixture-request",
        )
        self.assertEqual(offer["price"], 33415.0)
        self.assertEqual(offer["availability"], "in_stock")
        self.assertEqual(offer["source_type"], "quickcommerce_authorized_api")
        self.assertEqual(offer["metadata"]["affiliate_attribution"], "not_asserted")

    def test_batch_calls_each_model_once_and_requires_complete_coverage(self):
        now = datetime.now(timezone.utc)
        observed = (now - timedelta(minutes=1)).isoformat()
        targets = []
        payloads = {}
        for index in range(TOP30_COUNT):
            brand = f"Brand{index}"
            model = f"Model {index}"
            row = {"audit_id": f"{brand.casefold()}|{model.casefold()}", "brand": brand, "model": model, "category": "mobiles"}
            query = f"{brand} {model}"
            pid = f"MOB{index:012d}"
            payloads[query] = {
                "status": "success",
                "request_id": f"request-{index}",
                "data": {
                    "platform": "Flipkart",
                    "products": [{
                        "id": pid,
                        "name": f"{brand} {model} (Black, 128 GB)",
                        "brand": brand,
                        "available": True,
                        "offer_price": 10000 + index,
                        "mrp": 15000 + index,
                        "quantity": "8 GB RAM",
                        "currency": "INR",
                        "deeplink": f"https://www.flipkart.com/-/p/-?pid={pid}",
                    }],
                },
            }
            targets.append(row)
        connector = FakeConnector(payloads, observed)
        result = refresh_targets(targets, connector, delay_seconds=0, now=now)
        self.assertEqual(result["model_count"], TOP30_COUNT)
        self.assertEqual(len(result["offers"]), TOP30_COUNT)
        self.assertEqual(len(connector.calls), TOP30_COUNT)
        self.assertEqual(len(set(connector.calls)), TOP30_COUNT)

    def test_all_missing_exact_models_produce_no_store_payload(self):
        now = datetime.now(timezone.utc)
        observed = (now - timedelta(minutes=1)).isoformat()
        targets = load_top30_targets()
        payloads = {}
        for row in targets:
            payloads[" ".join((row["brand"], row["model"]))] = {"status": "success", "data": {"platform": "Flipkart", "products": []}}
        connector = FakeConnector(payloads, observed)
        with self.assertRaisesRegex(ValueError, "no publishable offers"):
            refresh_targets(targets, connector, delay_seconds=0, now=now)
        self.assertEqual(len(connector.calls), TOP30_COUNT)

    def test_missing_model_does_not_block_verified_models(self):
        now = datetime.now(timezone.utc)
        observed = (now - timedelta(minutes=1)).isoformat()
        targets = []
        payloads = {}
        missing_index = 7
        for index in range(TOP30_COUNT):
            brand = f"Brand{index}"
            model = f"Model {index}"
            row = {"audit_id": f"{brand.casefold()}|{model.casefold()}", "brand": brand, "model": model, "category": "mobiles"}
            query = f"{brand} {model}"
            targets.append(row)
            if index == missing_index:
                payloads[query] = {"status": "success", "data": {"platform": "Flipkart", "products": []}}
                continue
            pid = f"MOB{index:012d}"
            payloads[query] = {
                "status": "success",
                "request_id": f"request-{index}",
                "data": {
                    "platform": "Flipkart",
                    "products": [{
                        "id": pid,
                        "name": f"{brand} {model} (Black, 128 GB)",
                        "brand": brand,
                        "available": True,
                        "offer_price": 10000 + index,
                        "mrp": 15000 + index,
                        "quantity": "8 GB RAM",
                        "currency": "INR",
                        "deeplink": f"https://www.flipkart.com/-/p/-?pid={pid}",
                    }],
                },
            }
        result = refresh_targets(targets, FakeConnector(payloads, observed), delay_seconds=0, now=now)
        self.assertEqual(result["model_count"], TOP30_COUNT)
        self.assertEqual(result["offer_count"], TOP30_COUNT - 1)
        self.assertEqual(result["refresh_failures"][0]["model_key"], f"brand{missing_index}|model {missing_index}")

    def test_missing_model_retains_previous_verified_offer(self):
        fresh = {"offers": [{"model_key": "brand0|model 0", "price": 11000}]}
        previous = {"offers": [
            {"model_key": "brand0|model 0", "price": 10000},
            {"model_key": "brand7|model 7", "price": 17000},
        ]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "retailer_offers.json"
            path.write_text(json.dumps(previous), encoding="utf-8")
            merged = merge_with_previous_store(fresh, path)
        self.assertEqual(merged["offer_count"], 2)
        self.assertEqual(merged["retained_previous_offer_count"], 1)
        self.assertEqual(merged["offers"][0]["price"], 11000)
        self.assertEqual(merged["offers"][1]["price"], 17000)

    def test_out_of_stock_exact_sku_has_no_payable_price(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["data"]["products"] = [copy.deepcopy(payload["data"]["products"][1])]
        payload["data"]["products"][0]["available"] = False
        payload["data"]["products"][0]["offer_price"] = 0
        row = {"audit_id": "samsung|galaxy a56 5g", "brand": "Samsung", "model": "Galaxy A56 5G", "category": "mobiles"}
        item, variant = select_exact_listing(payload, row)
        offer = build_offer(item, variant, row, observed_at="2026-11-23T10:00:00+00:00", pincode="110001", request_id="out")
        self.assertEqual(offer["availability"], "out_of_stock")
        self.assertIsNone(offer["price"])

    def test_catalogue_model_key_accepts_only_provider_trailing_5g_alias(self):
        pid = "MOB123456789012"
        payload = {
            "status": "success",
            "data": {
                "platform": "Flipkart",
                "products": [{
                    "id": pid,
                    "name": "Infinix GT 30 Pro 5G (Shadow Ash, 256 GB)",
                    "brand": "Infinix",
                    "available": True,
                    "offer_price": 23999,
                    "mrp": 29999,
                    "quantity": "12 GB",
                    "currency": "INR",
                    "deeplink": f"https://www.flipkart.com/-/p/-?pid={pid}",
                }],
            },
        }
        row = {"audit_id": "infinix|gt 30 pro", "brand": "Infinix", "model": "GT 30 Pro", "category": "mobiles"}
        item, variant = select_exact_listing(payload, row)
        self.assertEqual(item["id"], pid)
        self.assertEqual(variant["variant"], "12GB/256GB · Shadow Ash")


if __name__ == "__main__":
    unittest.main()



