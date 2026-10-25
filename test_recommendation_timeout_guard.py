import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent / "python"))

import market_discovery
import retail_price_evidence
import shopping_api


class RecommendationTimeoutGuardTests(unittest.TestCase):
    def test_provider_disabled_skips_amazon_search_cards(self):
        with patch.object(market_discovery, "_amazon_live_search_available", return_value=False), \
             patch.object(market_discovery, "search_asins", side_effect=AssertionError("unauthorized search")):
            result = market_discovery.fallback_search_channel(
                query="phone under 10000", category="smartphone",
                include_domains=["amazon.in"], channel="commerce", max_results=3,
            )
        self.assertIsInstance(result, list)

    def test_provider_enabled_preserves_existing_search_lane(self):
        with patch.object(market_discovery, "_amazon_live_search_available", return_value=True), \
             patch.object(market_discovery, "search_asins", return_value=[]) as search:
            market_discovery.fallback_search_channel(
                query="phone under 10000", category="smartphone",
                include_domains=["amazon.in"], channel="commerce", max_results=3,
            )
        self.assertEqual(search.call_count, 1)

    def test_provider_disabled_skips_amazon_price_page_fetch(self):
        candidate = {"source_url": "https://www.amazon.in/dp/B000000000", "source_host": "www.amazon.in"}
        with patch.object(retail_price_evidence, "_amazon_live_offer_fetch_available", return_value=False), \
             patch.object(retail_price_evidence, "fetch_structured_price", side_effect=AssertionError("unauthorized fetch")):
            result = retail_price_evidence.build_price_evidence(candidate)
        self.assertEqual(result["status"], "provider_unavailable")
        self.assertFalse(result["verified"])

    def test_local_loopback_origins_are_explicitly_allowed(self):
        client = shopping_api.app.test_client()
        for origin in ("http://127.0.0.1:4173", "http://localhost:4173"):
            response = client.options(
                "/api/recommend?q=phone",
                headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
            )
            self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), origin)

    def test_frontend_reports_performance_unavailable_and_reference_status(self):
        source = (Path(__file__).resolve().parent / "app.js").read_text(encoding="utf-8")
        self.assertIn('["camera", "battery", "gaming", "performance"]', source)
        self.assertIn("Live reference unavailable (${referenceStatus})", source)


if __name__ == "__main__":
    unittest.main()
