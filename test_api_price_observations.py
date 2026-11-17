import copy
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python"))
from build_multi_retailer_public import observed_configuration, observation_url, build_observation_snapshot
from quickcommerce_flipkart_adapter import QuickCommerceFlipkartConnector

class ObservationTests(unittest.TestCase):
    def setUp(self):
        self.card = {"model_key": "samsung|galaxy a56 5g", "brand": "Samsung", "model": "Galaxy A56 5G"}
        self.item = {"id": "MOBHQBDXXJUDBFVH", "name": "Samsung Galaxy A56 5G (Light Violet, 128 GB)",
                     "brand": "Samsung", "quantity": "8 GB RAM", "available": True,
                     "offer_price": 33294, "currency": "INR",
                     "deeplink": "https://www.flipkart.com/-/p/-?pid=MOBHQBDXXJUDBFVH"}
        self.now = datetime.now(timezone.utc)

    def rows(self, items, platform="Flipkart", checked=None):
        return [{"endpoint": "search", "platform": platform, "status": "success",
                 "model_key": self.card["model_key"], "params": {"q": "Samsung Galaxy A56 5G"},
                 "observed_at": checked or self.now.isoformat(), "items": items}]

    def test_explicit_memory_and_wrong_or_ambiguous_models(self):
        self.assertEqual(observed_configuration(self.item, self.card, "flipkart")["ram_gb"], 8)
        for update in [{"name": "Samsung Galaxy A56 Plus (Blue, 128 GB)"},
                       {"brand": None}, {"quantity": "8 GB virtual RAM"},
                       {"name": "Samsung Galaxy A56 5G (Blue, 8GB, 128GB)", "quantity": ""},
                       {"name": "Renewed Samsung Galaxy A56 5G (Blue, 128 GB)"}]:
            self.assertIsNone(observed_configuration(dict(self.item, **update), self.card, "flipkart"))

    def test_parenthesized_model_and_amazon_brand_field(self):
        card = dict(self.card, brand="Nothing", model="Phone (3a)")
        item = dict(self.item, brand="Nothing", name="Phone (3a) (Black, 128 GB) (8 GB RAM)", quantity="")
        self.assertIsNotNone(observed_configuration(item, card, "amazon"))
        self.assertIsNone(observed_configuration(dict(item, name="Phone (3a) Lite (Black, 128 GB) (8 GB RAM)"), card, "amazon"))

    def test_unknown_stock_invalid_price_currency_and_links_rejected(self):
        for update in [{"available": "true"}, {"offer_price": True}, {"offer_price": float("inf")},
                       {"currency": "USD"}, {"deeplink": "https://evil.example/p/x?pid=MOBHQBDXXJUDBFVH"}]:
            result = build_observation_snapshot({}, [self.card], self.rows([dict(self.item, **update)]), now=self.now)
            self.assertEqual(result["counts"]["retailer_rows"], 0)

    def test_different_colors_do_not_get_a_price_winner(self):
        amazon = dict(self.item, id="B0TEST1234", name="Galaxy A56 5G (Dark Blue, 8GB RAM 128GB Storage)",
                      deeplink="https://www.amazon.in/dp/B0TEST1234", offer_price=32000)
        result = build_observation_snapshot({}, [self.card], self.rows([self.item]) + self.rows([amazon], "Amazon"), now=self.now)
        configs = result["models"][self.card["model_key"]]
        self.assertEqual(len(configs), 2)
        self.assertTrue(all(c["lowest_observed_retailer"] is None for c in configs))

    def test_two_stores_same_configuration_and_duplicate_store(self):
        amazon = dict(self.item, id="B0TEST1234", name="Galaxy A56 5G (Light Violet, 8GB RAM 128GB Storage)",
                      deeplink="https://www.amazon.in/dp/B0TEST1234", offer_price=32000)
        rows = self.rows([self.item, self.item]) + self.rows([amazon], "Amazon")
        result = build_observation_snapshot({}, [self.card], rows, now=self.now)
        config = result["models"][self.card["model_key"]][0]
        self.assertEqual(len(config["offers"]), 2)
        self.assertEqual(config["lowest_observed_retailer"], "amazon")
        self.assertFalse(config["purchase_eligible"])
        self.assertNotIn("image", json.dumps(result))

    def test_stale_and_out_of_stock_do_not_win(self):
        old = (self.now - timedelta(hours=7)).isoformat()
        result = build_observation_snapshot({}, [self.card], self.rows([self.item], checked=old), now=self.now)
        config = result["models"][self.card["model_key"]][0]
        self.assertIsNone(config["lowest_observed_retailer"])
        self.assertEqual(config["offers"][0]["observed_at"], old)
        result = build_observation_snapshot({}, [self.card], self.rows([dict(self.item, available=False)]), now=self.now)
        self.assertIsNone(result["models"][self.card["model_key"]][0]["offers"][0]["price"])

    def test_tv_model_code_in_quantity_and_wrong_suffix(self):
        card = {"model_key": "TV01", "brand": "Xiaomi", "model": "S Mini LED 55", "category": "tvs", "model_code": "L55MC-IN"}
        item = dict(self.item, brand="Xiaomi", name="XIAOMI S Mini LED 55 inch", quantity="L55MC-IN")
        self.assertIsNotNone(observed_configuration(item, card, "flipkart"))
        self.assertIsNone(observed_configuration(dict(item, quantity="L55MC-FSMIN"), card, "flipkart"))

    def test_croma_exact_reviewed_id_is_not_a_substring_match(self):
        card = {"model_key": "TV01", "brand": "Xiaomi", "model": "S Mini LED 55", "category": "tvs", "model_code": "L55MC-IN",
                "retailers": {"croma": {"exact_model_link_verified": True, "retailer_research_url": "https://www.croma.com/tv/p/315575"}}}
        item = dict(self.item, id="315575", brand="Xiaomi", name="Xiaomi S Mini LED 55 inch", quantity="",
                    deeplink="https://www.croma.com/tv/p/315575")
        self.assertIsNotNone(observed_configuration(item, card, "croma"))
        self.assertIsNone(observed_configuration(dict(item, id="31557"), card, "croma"))

    def test_croma_false_string_is_out_of_stock_not_truthy(self):
        card = {"model_key": "TV01", "brand": "Xiaomi", "model": "S Mini LED 55", "category": "tvs", "model_code": "L55MC-IN",
                "retailers": {"croma": {"exact_model_link_verified": True, "retailer_research_url": "https://www.croma.com/tv/p/315575"}}}
        item = {"item_id": "315575", "brand": "Xiaomi", "name": "Xiaomi S Mini LED 55 inch",
                "available": "false", "price": "54999", "currency": "INR", "deeplink": "https://www.croma.com/tv/p/315575"}
        row = {"endpoint": "item", "platform": "Croma", "status": "success", "model_key": "TV01",
               "params": {"item_id": "315575"}, "observed_at": self.now.isoformat(), "items": [item]}
        result = build_observation_snapshot({}, [card], [row], now=self.now)
        offer = result["models"]["TV01"][0]["offers"][0]
        self.assertEqual(offer["availability"], "out_of_stock")
        self.assertIsNone(offer["price"])

    def test_earbud_exact_model_prefix_and_pro_are_not_interchangeable(self):
        card = {"model_key": "EB01", "brand": "OnePlus", "model": "Nord Buds 3r", "category": "accessories", "model_code": "E517A"}
        item = dict(self.item, brand="OnePlus", name="OnePlus Nord Buds 3r TWS Earbud", quantity="Ash Black, True Wireless")
        self.assertIsNotNone(observed_configuration(item, card, "flipkart"))
        self.assertIsNone(observed_configuration(dict(item, name="OnePlus Nord Buds 3r Pro TWS Earbud"), card, "flipkart"))
        self.assertIsNone(observed_configuration(dict(item, name="OnePlus Nord Buds 3 TWS Earbud"), card, "flipkart"))

    def test_unknown_ram_is_labelled_and_kept_out_of_cross_store_comparison(self):
        flipkart = dict(self.item, quantity="")
        amazon = dict(self.item, id="B0TEST1234", name="Galaxy A56 5G (Light Violet, 128 GB)",
                      quantity="", deeplink="https://www.amazon.in/dp/B0TEST1234")
        result = build_observation_snapshot({}, [self.card], self.rows([flipkart]) + self.rows([amazon], "Amazon"), now=self.now)
        configs = result["models"][self.card["model_key"]]
        self.assertEqual(len(configs), 2)
        self.assertTrue(all("RAM not stated" in c["variant"] for c in configs))
        self.assertTrue(all(c["lowest_observed_retailer"] is None for c in configs))

    def test_transport_rejects_unapproved_endpoints_before_request(self):
        def opener(*args, **kwargs):
            self.fail("Network must not be called")
        connector = QuickCommerceFlipkartConnector(opener=opener)
        for endpoint, platform, params in [("search", "Croma", {"q": "phone"}),
                                          ("secrets", "Amazon", {"q": "x"}),
                                          ("search", "Other", {"q": "x"}),
                                          ("search", "Amazon", {"api_key": "x"})]:
            with self.assertRaises(ValueError):
                connector.fetch_observation(endpoint, platform, **params)

    def test_history_keeps_source_times_without_turning_replay_into_freshness(self):
        earlier = (self.now - timedelta(hours=1)).isoformat()
        rows = self.rows([dict(self.item, offer_price=34000)], checked=earlier) + self.rows([self.item])
        result = build_observation_snapshot({}, [self.card], rows, now=self.now)
        offer = result["models"][self.card["model_key"]][0]["offers"][0]
        self.assertEqual(offer["observed_at"], self.now.isoformat())
        self.assertEqual([p["price"] for p in offer["history"]], [34000, 33294])
        self.assertEqual(offer["history"][0]["observed_at"], earlier)


class Top30PaidApiScopeTests(unittest.TestCase):
    def test_refresh_queries_are_exactly_the_approved_top30_mobiles(self):
        from scripts.refresh_api_comparison import planned_queries
        calls = planned_queries()
        self.assertEqual(len(calls), 30)
        approved = json.loads((ROOT / "data/top30_research_pilot_20261113.json").read_text())
        self.assertEqual([entry[0] for entry in calls], [row["model_key"] for row in approved["selected_models"]])
        self.assertTrue(all(platform == "Flipkart" and query for _, platform, query in calls))
        self.assertFalse(any(key.startswith(("tv", "earbuds")) for key, _, _ in calls))

if __name__ == "__main__":
    unittest.main()
