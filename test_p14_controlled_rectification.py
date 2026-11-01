from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python"))

from intent_engine import parse_query
from market_discovery import discovery_variant_gate
from cta_eligibility import evaluate_offer


class P14ControlledRectificationTests(unittest.TestCase):
    def test_exact_physical_variant_forms_are_hard_constraints(self):
        expected = {"8gb_ram", "256gb_storage"}
        for query in (
            "Samsung Galaxy A36 8GB 256GB",
            "Samsung Galaxy A36 8 GB / 256 GB",
            "Samsung Galaxy A36 8/256",
            "Samsung Galaxy A36 8GB RAM 256GB storage",
        ):
            intent = parse_query(query)
            self.assertEqual(intent["category"], "smartphone", query)
            self.assertEqual(set(intent["must_have"]), expected, query)
            title = "Samsung Galaxy A36 5G 8GB RAM 128GB Storage"
            gate = discovery_variant_gate(title, intent, exact_memory_variant=True)
            self.assertEqual(gate["status"], "reject", query)

    def test_exact_variant_without_capacity_keeps_normal_query_behavior(self):
        intent = parse_query("Samsung Galaxy A36 5G")
        self.assertEqual(intent["brands"], ["Samsung"])
        self.assertFalse(any(item.endswith("gb_ram") or item.endswith("gb_storage") for item in intent["must_have"]))

    def test_negative_brand_forms_and_positive_brand_queries(self):
        for query in (
            "best phone excluding Samsung",
            "best phone without Samsung",
            "best phone no Samsung",
            "best phone except Samsung",
            "best phone Samsung mat dikhana",
            "best phone Samsung ko chhodkar",
        ):
            intent = parse_query(query)
            self.assertIn("brand_samsung", intent["avoid"], query)
            self.assertNotIn("brand_samsung", intent["must_have"], query)
        positive = parse_query("Samsung Galaxy A36 5G")
        self.assertEqual(positive["brands"], ["Samsung"])
        self.assertNotIn("brand_samsung", positive["avoid"])
        mixed = parse_query("only Samsung excluding Samsung")
        self.assertIn("brand_samsung", mixed["avoid"])
        self.assertNotIn("brand_samsung", mixed["must_have"])

    def test_cta_contract_rejects_stale_unknown_wrong_and_expired_offers(self):
        base = {
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
        from datetime import datetime, timezone
        now = datetime(2026, 10, 22, 12, tzinfo=timezone.utc)
        self.assertFalse(evaluate_offer({**base, "availability": "unknown"}, product_id="cw-mobile-test", variant="8GB/128GB", now=now)["eligible"])
        self.assertFalse(evaluate_offer({**base, "retailer_product_id": "WRONG"}, product_id="cw-mobile-test", variant="8GB/128GB", now=now, expected_retailer_product_id="B0TEST123")["eligible"])
        self.assertFalse(evaluate_offer({**base, "last_checked": "2026-10-21T00:00:00+00:00"}, product_id="cw-mobile-test", variant="8GB/128GB", now=now)["eligible"])

    def test_public_build_regenerates_fail_closed_product_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "public"
            result = subprocess.run(
                [sys.executable, "scripts/build_public_pages.py", "--output", str(output)],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            pages = list((output / "products").rglob("index.html"))
            self.assertEqual(len(pages), 105)
            page = next(p for p in pages if "samsung-galaxy-a36-5g-dark-blue-8gb-ram-128gb-storage" in str(p))
            html = page.read_text(encoding="utf-8")
            self.assertIn("Current price and stock not verified.", html)
            self.assertNotIn("Status: available", html)
            self.assertNotIn('<a class="cta" href=', html)
            self.assertNotIn("Check Latest Offer", html)

    def test_exact_variant_api_fails_closed_with_explicit_reason(self):
        from unittest.mock import patch
        import shopping_api
        payload = {
            "query": "Samsung Galaxy A36 8GB 256GB",
            "intent": {"category": "smartphone", "brands": ["Samsung"], "must_have": ["8gb_ram", "256gb_storage"]},
            "recommendations": [],
            "result_status": "PARTIAL",
            "market_data_status": "CURRENT_OFFERS_UNAVAILABLE",
            "failures": [{"stage": "canonical_identity", "reason": "Exact physical variant has no unique verified catalogue owner"}],
        }
        with patch.object(shopping_api, "run_pipeline", return_value=payload):
            response = shopping_api.app.test_client().get("/api/recommend", query_string={"q": payload["query"]})
        body = response.get_json()
        self.assertEqual(body["response_reason"], "EXACT_VARIANT_UNAVAILABLE")
        self.assertEqual(body["hard_gate_rejections"][0]["code"], "EXACT_VARIANT_UNAVAILABLE")
        self.assertEqual(body["recommendations"], [])

    def test_public_research_remains_offerless(self):
        preview = json.loads((ROOT / "data/mobile_research_preview.json").read_text(encoding="utf-8"))
        self.assertEqual(len(preview["products"]), 10)
        self.assertTrue(all(row["manufacturer_spec_status"] == "VERIFIED" for row in preview["products"]))
        self.assertTrue(all(row["commerce"]["purchase_cta_eligible"] is False for row in preview["products"]))


if __name__ == "__main__":
    unittest.main()
