"""Offline tests for paid QuickCommerce fallback; no network or credits."""
import os
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent / "python"))
import paid_api_live_bridge as bridge

NOW = datetime(2026, 11, 19, 4, 0, tzinfo=timezone.utc)
CARD = {"model_key": "samsung|galaxy a56 5g", "brand": "Samsung",
        "model": "Galaxy A56 5G", "specifications": {}}
FLIPKART = {"id": "MOBHQBDXXJUDBFVH",
            "name": "Samsung Galaxy A56 5G (Light Violet, 128 GB)",
            "brand": "Samsung", "quantity": "8 GB RAM", "available": True,
            "offer_price": 33294, "currency": "INR",
            "deeplink": "https://www.flipkart.com/-/p/-?pid=MOBHQBDXXJUDBFVH"}
AMAZON = {"id": "B012345678",
          "name": "Samsung Galaxy A56 5G (Light Violet, 128 GB) (8 GB RAM)",
          "brand": "Samsung", "quantity": "8 GB RAM", "available": True,
          "offer_price": 33500, "currency": "INR",
          "deeplink": "https://www.amazon.in/dp/B012345678"}


class FakeProvider:
    def __init__(self, flipkart=None, amazon=None):
        self.items = {
            "Flipkart": [FLIPKART] if flipkart is None else flipkart,
            "Amazon": [AMAZON] if amazon is None else amazon,
        }
        self.calls = []

    def fetch_observation(self, endpoint, platform, **params):
        self.calls.append((endpoint, platform, params))
        if platform == "Croma":
            raise AssertionError("No reviewed Croma ID for this phone")
        return {"status": "success", "data": {
            "platform": platform, "products": self.items[platform]
        }}, NOW.isoformat()


class PaidApiBridgeTests(unittest.TestCase):
    def setUp(self):
        bridge._CACHE.clear()
        bridge._SPEND.clear()
        self.daily_cap = patch.dict(os.environ, {"CW_QUICKCOMMERCE_DAILY_CAP": "10"})
        self.daily_cap.start()

    def tearDown(self):
        self.daily_cap.stop()

    def test_flipkart_found_stops_without_amazon(self):
        client = FakeProvider()
        result = bridge.observe_card(CARD, client=client, now=NOW)
        self.assertEqual(result["status"], "ok", result)
        self.assertEqual(result["configuration"]["offers"][0]["retailer"], "flipkart")
        self.assertEqual([x[1] for x in client.calls], ["Flipkart"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["purchase_eligible"])

    def test_wrong_variant_and_missing_stock_falls_back_to_amazon(self):
        bad_flipkart = dict(FLIPKART, quantity="12 GB RAM")
        client = FakeProvider(flipkart=[bad_flipkart])
        result = bridge.observe_card(CARD, ram_gb=8, storage_gb=128,
                                     color="Light Violet", client=client, now=NOW)
        self.assertEqual(result["status"], "ok", result)
        self.assertEqual(result["configuration"]["offers"][0]["retailer"], "amazon")
        self.assertEqual([x[1] for x in client.calls], ["Flipkart", "Amazon"])

    def test_no_found_returns_explicit_unavailable(self):
        client = FakeProvider(flipkart=[], amazon=[])
        result = bridge.observe_card(CARD, client=client, now=NOW)
        self.assertEqual(result["status"], "no_exact_in_stock_observation")
        self.assertEqual(len(client.calls), 2)

    def test_cache_does_not_rebill_same_model_query(self):
        client = FakeProvider(flipkart=[], amazon=[])
        bridge.observe_card(CARD, client=client, now=NOW)
        bridge.observe_card(CARD, client=client, now=NOW)
        self.assertEqual(len(client.calls), 2)

    def test_cost_cap_stops_next_retailer(self):
        client = FakeProvider(flipkart=[])
        with patch.dict(os.environ, {"CW_QUICKCOMMERCE_DAILY_CAP": "1"}):
            result = bridge.observe_card(CARD, client=client, now=NOW)
        self.assertEqual(result["status"], "budget_exhausted")
        self.assertEqual([x[1] for x in client.calls], ["Flipkart"])

    def test_bad_price_rejected_without_false_verified_claim(self):
        client = FakeProvider(flipkart=[dict(FLIPKART, offer_price=True)], amazon=[])
        result = bridge.observe_card(CARD, client=client, now=NOW)
        self.assertEqual(result["status"], "no_exact_in_stock_observation")

    def test_source_reviewed_new_models_are_lookup_known_but_not_buyable(self):
        from python.india_missing_eight_pages import import_eight
        from python.india_recent_eight_import import build_recent
        additions = import_eight()["model_cards"] + build_recent()["model_cards"]
        known = bridge.catalogue()
        self.assertGreaterEqual(len(additions), 8)
        self.assertTrue(all(card["model_key"] in known for card in additions))
        self.assertEqual(len(known), 232 + 40 + len(additions))

    def test_price_panel_requires_explicit_paid_lookup_click(self):
        script = (Path(__file__).resolve().parent / "assets" / "retailer-observations.js").read_text(encoding="utf-8")
        self.assertIn("data-check-live-price", script)
        self.assertIn("if (liveButton)", script)
        for accidental in (
            "checkPaidApi(panel, modelKey, null);",
            "checkPaidApi(panel, modelKey, configurations[0]);",
            "checkPaidApi(panel, modelKey, selected);",
        ):
            self.assertNotIn(accidental, script)

    def test_route_rejects_bad_model_or_variant_without_paid_call(self):
        import shopping_api
        client = shopping_api.app.test_client()
        self.assertEqual(client.get("/api/price-observation").status_code, 400)
        self.assertEqual(client.get("/api/price-observation?model_key=unknown").status_code, 404)
        self.assertEqual(client.get("/api/price-observation?model_key=x&ram_gb=999").status_code, 400)


if __name__ == "__main__":
    unittest.main()
