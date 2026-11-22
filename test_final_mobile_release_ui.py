import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class FinalMobileReleaseUITests(unittest.TestCase):
    def test_homepage_has_mobile_budget_shortcuts_and_clean_skin(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('<body class="clean-ui">', source)
        # Five primary shortcuts; the full 40-band coverage stays in the
        # advanced filter, not in a crowded homepage button menu.
        primary = (("₹5k–&lt;₹10k", "mobile under 10000"),
                   ("₹10k–&lt;₹15k", "mobile under 15000"),
                   ("₹15k–&lt;₹20k", "mobile under 20000"),
                   ("₹20k–&lt;₹25k", "mobile under 25000"),
                   ("₹25k–&lt;₹30k", "mobile under 30000"))
        self.assertEqual(
            len(re.findall(r'<button[^>]*data-mobile-query="mobile under \d+"', source)),
            len(primary),
        )
        for budget, query in primary:
            self.assertRegex(
                source,
                rf'data-mobile-query="{re.escape(query)}"[^>]*>{re.escape(budget)}</button>',
            )
        self.assertNotIn('class="cw-budget-more"', source)
        self.assertIn('id="researchGuidedBudget"', source)
        for cap in range(5000, 200001, 5000):
            self.assertIn(f'<option value="{cap}">', source)


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
