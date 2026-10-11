import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent / "python"))
import shopping_api


class ActiveRouteTests(unittest.TestCase):
    def test_route_preserves_pipeline_order_and_contract(self):
        payload = {"recommendations": [{"product_id": "second"}, {"product_id": "first"}],
                   "result_status": "PARTIAL", "stage_counts": {"discovered": 30}}
        with patch.object(shopping_api, "run_pipeline", return_value=payload) as pipeline:
            response = shopping_api.app.test_client().get("/api/recommend?q=mobile+under+50000")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), payload)
        pipeline.assert_called_once_with(query="mobile under 50000", max_candidates=15,
                                         max_results=3, live_fast=True)

    def test_health_exposes_only_valid_deployment_revision(self):
        client = shopping_api.app.test_client()
        for value, expected in [("a" * 40, "a" * 40), ("", None), ("not-a-revision", None)]:
            with self.subTest(value=value), patch.dict("os.environ", {"RENDER_GIT_COMMIT": value}):
                self.assertEqual(client.get("/health").get_json()["revision"], expected)


if __name__ == "__main__":
    unittest.main()
