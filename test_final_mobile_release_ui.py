import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class FinalMobileReleaseUITests(unittest.TestCase):
    def test_homepage_has_mobile_budget_shortcuts_and_clean_skin(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('<body class="clean-ui">', source)
        for budget, query in (("₹10k", "mobile under 10000"),
                              ("₹20k", "mobile under 20000"),
                              ("₹30k", "mobile under 30000"),
                              ("₹40k", "mobile under 40000"),
                              ("₹50k", "mobile under 50000"),
                              ("₹60k+", "mobile under 60000")):
            self.assertRegex(
                source,
                rf'data-mobile-query="{re.escape(query)}">{re.escape(budget)}',
            )

    def test_retailer_choices_and_verification_explanation_are_visible(self):
        source = (ROOT / "app.js").read_text(encoding="utf-8")
        for label in ("Amazon", "Flipkart", "Croma"):
            self.assertIn(f'label: "{label}"', source)
        self.assertIn("Not verified", source)
        self.assertIn("fresh verified in-stock offer", source)
        self.assertIn("data-mobile-query", source)

    def test_clean_candidate_keeps_27_product_dna_records_and_no_duplicate_keys(self):
        data = json.loads(
            (ROOT / "data" / "mobile_intelligence_repository.json").read_text(
                encoding="utf-8"
            )
        )
        products = data["products"]
        self.assertEqual(len(products), 27)
        self.assertEqual(len(products), len(set(products)))
        for product_id, record in products.items():
            dna = record["dna"]
            self.assertEqual(product_id, dna["product_id"])
            self.assertTrue(dna["brand"]["verified"])
            self.assertTrue(dna["model"]["verified"])
            self.assertTrue(dna["ram_gb"]["verified"])
            self.assertTrue(dna["storage_gb"]["verified"])


if __name__ == "__main__":
    unittest.main()
