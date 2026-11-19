import tempfile
import unittest
from pathlib import Path

from scripts.audit_budget_price_conflicts import generate, write

ROOT = Path(__file__).resolve().parent


class HistoricalBudgetMismatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = generate(ROOT)

    def test_historical_snapshots_not_current_authorized_offers(self):
        a = self.audit
        self.assertEqual(a["mode"], "HISTORICAL_BUDGET_BAND_CONFLICT_AUDIT_ONLY")
        self.assertEqual(a["models_in_core_catalogue"], 232)
        self.assertEqual(a["dated_workbook_models"], 86)
        self.assertEqual(a["workbook_as_of"], "2026-11-03")
        self.assertEqual(a["same_memory_comparisons"], 39)
        self.assertEqual(a["status_counts"].get("DIFFERENT_5000_BAND"), 17)
        self.assertEqual(a["status_counts"].get("DIFFERENT_AMOUNT_SAME_BAND"), 10)
        self.assertEqual(a["status_counts"].get("SAME_AMOUNT"), 12)
        self.assertEqual(a["status_counts"].get("NO_COMPARABLE_SAVED_MEMORY"), 47)
        self.assertEqual(sum(a["status_counts"].values()), 86)
        self.assertTrue(all(not row["publish_as_current"] for row in a["rows"]))

    def test_examples_crossed_in_historical_snapshots(self):
        diffs = {row["model_key"]: row for row in self.audit["rows"]}
        for model in ("samsung|galaxy a06 5g", "samsung|galaxy a36 5g",
                      "samsung|galaxy a56 5g", "google|pixel 8a"):
            self.assertEqual(diffs[model]["status"], "DIFFERENT_5000_BAND")
        self.assertEqual(diffs["samsung|galaxy a06 5g"]["workbook_band_lower_inr"], 10000)
        self.assertEqual(diffs["samsung|galaxy a06 5g"]["saved_band_lower_inr"], 15000)

    def test_audit_files_contain_full_source_and_no_live_claim(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "evidence.json"
            write(self.audit, out)
            text = out.with_suffix(".md").read_text(encoding="utf-8")
            self.assertIn("Colour", text.title())
            self.assertIn("## Models needing current exact-offer verification", text)
            self.assertTrue(out.exists())

    def test_public_budget_ui_protects_against_confusing_history_and_live_prices(self):
        script = (ROOT / "mobile-research-preview.js").read_text(encoding="utf-8")
        price = (ROOT / "assets" / "retailer-observations.js").read_text(encoding="utf-8")
        self.assertIn("Historical price-band matches · NOT current prices", script)
        self.assertIn("newer date or a different colour", script)
        self.assertIn('var price = typeof offer.price', price)
        self.assertIn('(isFresh ? "₹" : "Historical ₹")', price)
        self.assertIn("offer.price >= Math.max(0, budget - 5000) && offer.price < budget", price)
        self.assertIn("opening saved price history does NOT call the paid API", price)


if __name__ == "__main__":
    unittest.main()
