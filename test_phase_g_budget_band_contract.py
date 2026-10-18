import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python"))

import shopping_api
from intent_engine import parse_query
from shopping_intelligence_pipeline import build_budget_presentation


class BudgetBandContractTests(unittest.TestCase):
    def _payload(self):
        rows = [
            {"product_id": "p31999", "price": 31999, "title": "A56"},
            {"product_id": "p39999", "price": 39999, "title": "Near"},
            {"product_id": "p40000", "price": 40000, "title": "Floor"},
            {"product_id": "p49998", "price": 49998, "title": "Upper"},
            {"product_id": "p50000", "price": 50000, "title": "Cap"},
        ]
        sections = build_budget_presentation(
            rows, parse_query("mobile under 50000"), "mobile under 50000"
        )
        return {
            "query": "mobile under 50000",
            "recommendations": rows,
            "recommendation_sections": sections,
            "primary_recommendations": sections["primary_recommendations"],
            "value_recommendations": sections["value_recommendations"],
            "result_status": "PASS",
        }

    def test_api_serializes_primary_and_value_sections(self):
        payload = self._payload()
        with patch.object(shopping_api, "run_pipeline", return_value=payload):
            response = shopping_api.app.test_client().get(
                "/api/recommend?q=mobile+under+50000"
            )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["recommendation_sections"]["primary_floor"], 40000)
        self.assertEqual(
            [row["price"] for row in data["primary_recommendations"]],
            [40000, 49998, 50000],
        )
        self.assertEqual(
            [row["price"] for row in data["value_recommendations"]],
            [31999, 39999],
        )
        self.assertNotIn(50001, [row["price"] for row in data["primary_recommendations"] + data["value_recommendations"]])
        self.assertNotIn(84000, [row["price"] for row in data["primary_recommendations"] + data["value_recommendations"]])

    def test_frontend_uses_serialized_sections_and_no_primary_message(self):
        source = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("data.primary_recommendations", source)
        self.assertIn("data.value_recommendations", source)
        self.assertIn("recommendationSections.no_primary_message", source)
        self.assertIn("ai-primary-section", source)
        self.assertIn("ai-value-section", source)
        result = subprocess.run(
            ["node", "--check", "app.js"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
