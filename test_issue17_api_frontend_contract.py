from __future__ import annotations

import json
import subprocess
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "python"))

from api_contract import API_CONTRACT_VERSION, apply_response_contract  # noqa: E402


NOW = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)


def recommendation(*, verified_at: str, availability: str = "unknown", affiliate: str = "", offer_product_id: str = "") -> dict:
    return {
        "rank": 1,
        "product_id": "runtime-1",
        "canonical_product_id": "cw-mobile-1",
        "title": "Fixture Phone",
        "brand": "FixtureBrand",
        "identity_evidence": {
            "status": "catalogued_exact_variant",
            "variant": {"ram_gb": "8", "storage_gb": "128"},
        },
        "affiliate_url": affiliate,
        "retailer_offers": ([{
            "product_id": offer_product_id,
            "retailer": "amazon",
            "retailer_product_id": "B0FIXTURE",
            "price": 19999,
        }] if offer_product_id else []),
        "provenance": {
            "price_evidence": {
                "verified": True,
                "price": 19999,
                "currency": "INR",
                "source_url": "https://www.amazon.in/dp/B0FIXTURE",
                "retailer_product_id": "B0FIXTURE",
                "availability": availability,
                "verified_at": verified_at,
            }
        },
    }


class Issue17ContractTests(unittest.TestCase):
    def payload(self, recs=None, budget=18000, category="smartphone"):
        return {
            "schema_version": "1.1",
            "query": "Best phone under 18000",
            "intent": {"category": category, "budget_max": budget, "priority_weights": {"budget": 20}},
            "result_status": "PARTIAL",
            "recommendations": recs or [],
        }

    def test_exact_budget_and_contract_version_are_additive(self):
        output = apply_response_contract(self.payload(), "Best phone under 18000", now=NOW)
        self.assertEqual(output["api_contract_version"], API_CONTRACT_VERSION)
        self.assertEqual(output["requested_budget_inr"], 18000)
        self.assertEqual(output["requested_query"], "Best phone under 18000")
        self.assertEqual(output["optional_stretch"]["stretch_enabled"], False)

    def test_current_price_requires_exact_offer_mapping_and_in_stock(self):
        rec = recommendation(
            verified_at=(NOW - timedelta(minutes=30)).isoformat(),
            availability="in_stock",
            offer_product_id="cw-mobile-1",
        )
        output = apply_response_contract(self.payload([rec]), "Best phone under 18000", now=NOW)
        normalized = output["recommendations"][0]
        self.assertEqual(normalized["price_status"], "VERIFIED_CURRENT")
        self.assertTrue(normalized["current_offer_verified"])
        self.assertTrue(normalized["retailer_mapping_verified"])
        self.assertTrue(normalized["purchase_cta_eligible"])

    def test_affiliate_url_alone_cannot_enable_cta(self):
        rec = recommendation(
            verified_at=(NOW - timedelta(minutes=30)).isoformat(),
            availability="in_stock",
            affiliate="https://www.amazon.in/dp/B0FIXTURE?tag=affiliate",
            offer_product_id="",
        )
        output = apply_response_contract(self.payload([rec]), "Best phone under 18000", now=NOW)
        normalized = output["recommendations"][0]
        self.assertFalse(normalized["retailer_mapping_verified"])
        self.assertFalse(normalized["purchase_cta_eligible"])

    def test_expired_and_unknown_stock_are_not_current(self):
        expired = recommendation(verified_at=(NOW - timedelta(hours=6, seconds=1)).isoformat(), availability="in_stock", offer_product_id="cw-mobile-1")
        unknown = recommendation(verified_at=(NOW - timedelta(minutes=10)).isoformat(), availability="unknown", offer_product_id="cw-mobile-1")
        output = apply_response_contract(self.payload([expired, unknown]), "Best phone under 18000", now=NOW)
        self.assertEqual(output["recommendations"][0]["price_status"], "HISTORICAL_OR_EXPIRED")
        self.assertEqual(output["recommendations"][1]["price_status"], "CURRENT_OFFER_UNAVAILABLE")
        self.assertFalse(any(item["purchase_cta_eligible"] for item in output["recommendations"]))

    def test_four_category_contract_is_honest_when_specialist_assemblers_missing(self):
        output = apply_response_contract(self.payload(), "Best phone under 18000", now=NOW)
        categories = output["category_results"]
        self.assertEqual(categories["overall"]["result_count"], 0)
        self.assertEqual(categories["camera"]["status"], "CATEGORY_EVIDENCE_UNAVAILABLE")
        self.assertEqual(categories["battery"]["status"], "CATEGORY_EVIDENCE_UNAVAILABLE")
        self.assertEqual(categories["gaming"]["status"], "CATEGORY_EVIDENCE_UNAVAILABLE")

    def test_cache_key_changes_with_budget_and_category(self):
        a = apply_response_contract(self.payload(budget=18000), "Best phone under 18000", now=NOW)
        b = apply_response_contract(self.payload(budget=20000), "Best phone under 20000", now=NOW)
        c = apply_response_contract(self.payload(budget=18000, category="camera"), "Best camera phone under 18000", now=NOW)
        self.assertNotEqual(a["response_cache_key"], b["response_cache_key"])
        self.assertNotEqual(a["response_cache_key"], c["response_cache_key"])

    def test_backend_endpoint_preserves_query_when_scoping_brand(self):
        import shopping_api

        original = shopping_api.run_pipeline
        try:
            shopping_api.run_pipeline = lambda **kwargs: self.payload(budget=20000)
            response = shopping_api.app.test_client().get("/api/recommend?q=Samsung")
            body = response.get_json()
        finally:
            shopping_api.run_pipeline = original
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["requested_query"], "Samsung")
        self.assertEqual(body["requested_budget_inr"], 20000)

    def test_frontend_consumes_backend_cta_contract(self):
        source = (Path(__file__).resolve().parent / "app.js").read_text(encoding="utf-8")
        self.assertIn("p.purchase_cta_eligible === true", source)
        self.assertIn("p.current_offer_verified === true", source)
        self.assertIn("CATEGORY_EVIDENCE_UNAVAILABLE", source)
        result = subprocess.run(["node", "--check", "app.js"], cwd=Path(__file__).resolve().parent, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_fifty_identical_contract_replays_are_deterministic(self):
        rec = recommendation(verified_at=(NOW - timedelta(minutes=30)).isoformat(), availability="in_stock", offer_product_id="cw-mobile-1")
        first = apply_response_contract(self.payload([rec]), "Best phone under 18000", now=NOW)
        for _ in range(49):
            replay = apply_response_contract(json.loads(json.dumps(self.payload([rec]))), "Best phone under 18000", now=NOW)
            self.assertEqual(replay, first)


if __name__ == "__main__":
    unittest.main()
