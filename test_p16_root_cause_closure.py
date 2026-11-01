from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python"))

from intent_engine import parse_query
from market_discovery import discovery_variant_gate
import shopping_api


class P16RootCauseClosureTests(unittest.TestCase):
    def test_tb_variant_is_a_smartphone_hard_constraint(self):
        intent = parse_query("Samsung Galaxy A36 16GB 1TB")
        self.assertEqual(intent["category"], "smartphone")
        self.assertIn("16gb_ram", intent["must_have"])
        self.assertIn("1024gb_storage", intent["must_have"])
        rejected = discovery_variant_gate(
            "Samsung Galaxy A36 5G 8GB RAM 128GB Storage",
            intent,
            exact_memory_variant=True,
        )
        self.assertEqual(rejected["status"], "reject")

    def test_named_model_exclusion_is_preserved(self):
        intent = parse_query("Best Samsung mobile excluding Galaxy A36")
        self.assertIn("model_galaxy_a36", intent["avoid"])
        self.assertNotIn("model_galaxy_a36", intent["must_have"])

    def test_valid_exact_variant_uses_offer_reason_not_identity_failure(self):
        payload = {
            "query": "Samsung Galaxy A36 8GB 128GB",
            "intent": {
                "category": "smartphone",
                "brands": ["Samsung"],
                "must_have": ["8gb_ram", "128gb_storage"],
            },
            "recommendations": [{
                "product_id": "market-01",
                "canonical_product_id": "cw-mobile-93",
                "title": "Samsung Galaxy A36 5G 8GB RAM 128GB Storage",
                "brand": "Samsung",
                "identity_evidence": {
                    "status": "catalogued_exact_variant",
                    "variant": {"ram_gb": "8", "storage_gb": "128"},
                },
                "provenance": {},
            }],
            "result_status": "PASS",
            "market_data_status": "CURRENT_OFFERS_UNAVAILABLE",
            "failures": [{
                "stage": "canonical_identity",
                "reason": "Exact physical variant has no unique verified catalogue owner",
            }],
        }
        with patch.object(shopping_api, "run_pipeline", return_value=payload):
            response = shopping_api.app.test_client().get(
                "/api/recommend",
                query_string={"q": payload["query"]},
            )
        body = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["response_reason"], "NO_CURRENT_VERIFIED_OFFER")
        self.assertNotIn(
            "EXACT_VARIANT_UNAVAILABLE",
            [item.get("code") for item in body["hard_gate_rejections"]],
        )
        self.assertEqual(len(body["recommendations"]), 1)

    def test_unsupported_exact_variant_stays_empty(self):
        query = "Samsung Galaxy A36 16GB 1TB"
        payload = {
            "query": query,
            "intent": parse_query(query),
            "recommendations": [],
            "result_status": "PARTIAL",
            "market_data_status": "CURRENT_OFFERS_UNAVAILABLE",
            "failures": [{
                "stage": "canonical_identity",
                "reason": "Exact physical variant has no unique verified catalogue owner",
            }],
        }
        with patch.object(shopping_api, "run_pipeline", return_value=payload):
            response = shopping_api.app.test_client().get(
                "/api/recommend", query_string={"q": query}
            )
        body = response.get_json()
        self.assertEqual(body["response_reason"], "EXACT_VARIANT_UNAVAILABLE")
        self.assertEqual(body["recommendations"], [])


if __name__ == "__main__":
    unittest.main()
