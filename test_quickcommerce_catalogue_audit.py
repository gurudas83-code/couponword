import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("audit", ROOT / "scripts/quickcommerce_catalogue_audit.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class CatalogueAuditTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads((ROOT / "tests/fixtures/quickcommerce_flipkart_a56_search.json").read_text())
        self.row = {"audit_id": "samsung|galaxy a56 5g", "brand": "Samsung", "model": "Galaxy A56 5G", "category": "mobiles"}

    def test_catalogue_mobile_first_complete_and_unique(self):
        rows = audit.load_targets()
        self.assertEqual(len(rows), 272)
        self.assertEqual(len({r["audit_id"] for r in rows}), 272)
        self.assertTrue(all(r["category"] == "mobiles" for r in rows[:232]))
        self.assertEqual(len(audit.load_targets("tvs")), 20)
        self.assertEqual(len(audit.load_targets("earbuds")), 20)

    def test_variants_remain_separate_and_never_publishable(self):
        result = audit.audit_response(self.payload, self.row, "2026-11-17T16:27:14+00:00", "110001")
        self.assertEqual(len(result["candidates"]), 3)
        self.assertEqual({x["price_observation"] for x in result["candidates"]}, {33415., 33175., 37774.})
        for item in result["candidates"]:
            self.assertFalse(item["publishable"])
            self.assertFalse(item["exact_canonical_variant_verified"])
            self.assertFalse(item["image_publish_eligible"])

    def test_wrong_model_brand_currency_stock_price_and_link_rejected(self):
        for key, value in [("name", "Samsung Galaxy A56 5G Plus (Blue, 128 GB)"), ("brand", "Other"),
                           ("currency", "USD"), ("available", "true"), ("offer_price", True),
                           ("offer_price", "NaN"), ("deeplink", "https://evil.example/p/x?pid=MOBHQBDXXJUDBFVH")]:
            payload = copy.deepcopy(self.payload)
            item = payload["data"]["products"][1]
            item[key] = value
            payload["data"]["products"] = [item]
            self.assertEqual(audit.audit_response(payload, self.row, "", "110001")["candidates"], [])

    def test_storage_specific_card_does_not_mix_capacities(self):
        row = dict(self.row, model="Galaxy A56 5G 256GB")
        result = audit.audit_response(self.payload, row, "", "110001")
        self.assertEqual(len(result["candidates"]), 1)
        self.assertIn("256 GB", result["candidates"][0]["title"])

    def test_out_of_stock_has_no_price(self):
        item = self.payload["data"]["products"][1]
        item["available"] = False
        self.payload["data"]["products"] = [item]
        result = audit.audit_response(self.payload, self.row, "", "110001")
        self.assertIsNone(result["candidates"][0]["price_observation"])

    def test_images_are_allowlisted_references_only(self):
        self.assertEqual(audit.image_references({"images": ["https://evil.example/x.jpg", "https://rukminim2.flixcart.com/x.jpg"]}),
                         ["https://rukminim2.flixcart.com/x.jpg"])

    def test_shared_price_parser_rejects_booleans(self):
        self.assertIsNone(audit._positive_price(True))
        self.assertIsNone(audit._positive_price(False))

    def test_tv_requires_exact_model_code(self):
        row = {"brand": "Samsung", "model": "TV", "model_code": "QA55TEST", "category": "tvs"}
        item = dict(self.payload["data"]["products"][1], name="Samsung TV QA55TEST")
        self.assertTrue(audit.listing_candidate(item, row))
        item["name"] += "X"
        self.assertFalse(audit.listing_candidate(item, row))
        self.assertFalse(audit.listing_candidate(item, dict(row, model_code="")))

    def test_budget_and_offline_do_not_make_extra_calls(self):
        connector = audit.QuickCommerceFlipkartConnector(fixture=self.payload)
        with patch.object(connector, "search", wraps=connector.search) as search, patch.object(audit.time, "sleep"):
            self.assertEqual(audit.run([self.row], connector)["calls_attempted"], 0)
            search.assert_not_called()
            result = audit.run([self.row, dict(self.row, audit_id="second")], connector, max_calls=1)
            self.assertEqual(search.call_count, 1)
            self.assertEqual(result["records"][1]["status"], "NOT_REQUESTED_CALL_LIMIT")

    def test_errors_stop_without_retry_and_redact(self):
        connector = audit.QuickCommerceFlipkartConnector()
        with patch.object(connector, "search", side_effect=RuntimeError("SECRET")) as search:
            result = audit.run([self.row, dict(self.row, audit_id="second")], connector, max_calls=2)
        self.assertEqual(search.call_count, 1)
        self.assertNotIn("SECRET", json.dumps(result))
        self.assertEqual(result["records"][1]["status"], "NOT_REQUESTED_AFTER_ERROR")


if __name__ == "__main__":
    unittest.main()
