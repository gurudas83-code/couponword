from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class ProductionRecoveryPublicTests(unittest.TestCase):
    def test_public_artifact_contains_guides_and_safe_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "public"
            result = subprocess.run(
                [sys.executable, "scripts/build_public_pages.py", "--output", str(output)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output / "guides/index.html").is_file())
            preview = json.loads((output / "data/mobile_research_preview.json").read_text(encoding="utf-8"))
            self.assertEqual(len(preview["products"]), 10)
            self.assertTrue(all(not row["commerce"]["purchase_cta_eligible"] for row in preview["products"]))
            catalogue = json.loads((output / "coupons.json").read_text(encoding="utf-8"))
            self.assertEqual(len(catalogue), 105)
            self.assertIn('mobile-research-preview.js?v=3', (output / "index.html").read_text(encoding="utf-8"))

    def test_homepage_exposes_research_and_accessibility_paths(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("Compare 4 Verified Smartphones", html)
        self.assertIn('href="#main-content"', html)
        self.assertIn('id="mobileNav"', html)
        self.assertIn('og:image', html)

    def test_deal_wall_is_fail_closed(self):
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("deal.active === true", app)
        self.assertIn("deal.cta_eligible === true", app)
        self.assertIn("DEAL_MAX_AGE_MS", app)
        self.assertIn("Verified offers are currently unavailable.", app)
        self.assertNotIn("Date.now();", app.split("DEALS_FILE", 1)[0])

    def test_recommendation_has_timeout_retry_and_stale_guard(self):
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("AbortController", app)
        self.assertIn("RECOMMENDATION_TIMEOUT_MS", app)
        self.assertIn("data-retry-recommendation", app)
        self.assertIn("requestId !== recommendationRequestId", app)

    def test_backend_health_import_is_lazy_and_render_compatible(self):
        sys.path.insert(0, str(ROOT / "python"))
        import shopping_api

        self.assertIsNone(shopping_api.run_pipeline)
        response = shopping_api.app.test_client().get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")
        source = (ROOT / "python/shopping_api.py").read_text(encoding="utf-8")
        self.assertIn('host="0.0.0.0"', source)
        self.assertIn('os.environ.get("PORT", "8000")', source)

    def test_named_a36_a56_comparison_uses_research_route(self):
        sys.path.insert(0, str(ROOT / "python"))
        import shopping_api

        query = "Compare Samsung Galaxy A36 5G and Galaxy A56 5G based on battery, camera and processor."
        with patch.object(shopping_api, "run_pipeline", side_effect=AssertionError("shopping pool must not run")):
            response = shopping_api.app.test_client().get("/api/recommend", query_string={"q": query})
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["request_route"], "research_comparison")
        self.assertFalse(body["candidate_pool_entered"])
        self.assertEqual(body["response_reason"], "RESEARCH_COMPARISON")
        self.assertEqual([item["model"] for item in body["research_comparison"]["models"]], ["Galaxy A36 5G", "Galaxy A56 5G"])
        self.assertEqual([len(item["variants"]) for item in body["research_comparison"]["models"]], [3, 3])
        self.assertFalse(body["research_comparison"]["commerce"]["purchase_cta_eligible"])

    def test_zero_offer_shopping_response_exposes_gate_reason(self):
        sys.path.insert(0, str(ROOT / "python"))
        import shopping_api

        payload = {
            "query": "mobile under 20000",
            "intent": {"category": "smartphone", "budget_max": 20000},
            "recommendations": [],
            "result_status": "PARTIAL",
            "market_data_status": "CURRENT_OFFERS_UNAVAILABLE",
            "stage_counts": {"discovered": 30, "recommendations_returned": 0},
        }
        with patch.object(shopping_api, "run_pipeline", return_value=payload):
            response = shopping_api.app.test_client().get("/api/recommend", query_string={"q": "mobile under 20000"})
        body = response.get_json()
        self.assertEqual(body["request_route"], "shopping_candidate_pool")
        self.assertTrue(body["candidate_pool_entered"])
        self.assertEqual(body["response_reason"], "NO_CURRENT_VERIFIED_OFFER")
        self.assertEqual(body["hard_gate_rejections"][0]["code"], "NO_CURRENT_VERIFIED_OFFER")

    def test_frontend_renders_research_and_offer_gate_states(self):
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("renderResearchComparison", app)
        self.assertIn("Evidence-backed A36 vs A56 comparison", app)
        self.assertIn("loadResearchComparisonFallback", app)
        self.assertIn("isResearchComparisonQuery", app)
        self.assertIn("renderOfferUnavailable", app)
        self.assertIn("NO_CURRENT_VERIFIED_OFFER", (ROOT / "python/shopping_api.py").read_text(encoding="utf-8"))

    def test_catalogue_discovery_is_reference_only(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        preview = (ROOT / "mobile-research-preview.js").read_text(encoding="utf-8")
        self.assertIn('id="catalogueDiscovery"', html)
        self.assertIn('id="catalogueDiscoveryGrid"', html)
        self.assertIn("safeCatalogueRows", preview)
        self.assertIn("Historical / unverified reference", preview)
        self.assertIn("Exact identity, price, stock and purchase eligibility are not asserted", preview)
        self.assertNotIn("row.link", preview)
        self.assertNotIn("row.store", preview)


if __name__ == "__main__":
    unittest.main()
