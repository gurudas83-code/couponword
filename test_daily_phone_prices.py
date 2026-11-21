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
