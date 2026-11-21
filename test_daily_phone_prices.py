from datetime import datetime, timedelta
import unittest

from scripts.daily_phone_prices import IST, collect, planned_calls, render_store, worklist


class EmptyProvider:
    def fetch_observation(self, endpoint, platform, **parameters):
        return {
            "status": "success",
            "data": {"platform": platform, "items" if endpoint == "item" else "products": []},
        }, "2026-11-21T10:00:00+05:30"


class DailyPhonePriceTests(unittest.TestCase):
    def setUp(self):
        self.rows, self.cards = worklist()
        self.now = datetime(2026, 11, 21, 10, tzinfo=IST)

    def test_rotates_three_stores_within_daily_cap(self):
        stores = {row["model_key"]: set() for row in self.rows}
        for offset in range(3):
            calls = planned_calls(self.rows, self.now.date() + timedelta(days=offset))
            self.assertEqual(len(calls), 60)
            self.assertEqual(len({row["model_key"] for row, _ in calls}), 30)
            for row, platform in calls:
                stores[row["model_key"]].add(platform)
        for row in self.rows:
            expected = {"Amazon", "Flipkart"}
            if row.get("croma_id"):
                expected.add("Croma")
            self.assertEqual(stores[row["model_key"]], expected)

    def test_no_exact_result_and_no_second_spend_on_same_day(self):
        result = collect({}, self.rows, self.cards, EmptyProvider(), self.now, pause=lambda _: None)
        self.assertEqual(result["calls_attempted"], 60)
        self.assertEqual(len(result["stores"]), 30)
        self.assertTrue(all(not store["offers"] for stores in result["stores"].values() for store in stores.values()))
        self.assertEqual(collect(result, self.rows, self.cards, None, self.now), result)

    def test_stale_prices_are_hidden(self):
        cell = render_store({}, "Amazon", {"checked_at": "2026-11-17T10:00:00+05:30"}, self.now)
        self.assertIn("Refresh pending", cell)
        self.assertNotIn("₹", cell)


    def test_lowest_listing_is_sorted_before_alternative_prices(self):
        def offer(price, identifier):
            return {"price": price, "availability": "in_stock", "variant": "8GB / 128GB",
                    "retailer_product_id": identifier, "product_url": "https://www.amazon.in/dp/" + identifier}

        record = {"checked_at": self.now.isoformat(),
                  "offers": [offer(24999, "B012345678"), offer(21999, "B987654321")]}
        cell = render_store({}, "Amazon", record, self.now, "Example Phone", lowest=True)
        self.assertIn('class="phone-watch-price phone-watch-lowest" href="https://www.amazon.in/dp/B987654321">₹21,999', cell)
        self.assertIn('class="phone-watch-price" href="https://www.amazon.in/dp/B012345678">₹24,999', cell)


    def test_price_watch_excludes_reviewed_launch_models(self):
        import json
        from scripts.daily_phone_prices import ROOT

        held = json.loads((ROOT / "data/india_phone_launch_review.json").read_text())
        self.assertEqual(len(held), 6)
        self.assertFalse({row["model_key"] for row in held} & {row["model_key"] for row in self.rows})

    def test_price_expires_after_36_hours(self):
        record = {"checked_at": (self.now - timedelta(hours=37)).isoformat(),
                  "offers": [{"price": 21999, "availability": "in_stock",
                              "retailer_product_id": "B987654321", "variant": "8GB / 128GB",
                              "product_url": "https://www.amazon.in/dp/B987654321"}]}
        self.assertNotIn("₹", render_store({}, "Amazon", record, self.now, "Example Phone"))
