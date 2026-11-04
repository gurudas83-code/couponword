import unittest
from unittest.mock import patch
from scripts.verify_runtime_health import probe


class ReadOnlyRuntimeProbeTests(unittest.TestCase):
    def test_healthy_backend_comparison_is_safe(self):
        fixtures = iter([
            ({"status": "ok", "service": "coupon-world-shopping-intelligence", "revision": None}, 1.25),
            ({"request_route": "research_comparison", "candidate_pool_entered": False,
              "research_comparison": {"commerce": {"purchase_cta_eligible": False}}}, 0.5),
        ])
        with patch("scripts.verify_runtime_health.get_json", side_effect=lambda *a, **k: next(fixtures)):
            outcome = probe()
        self.assertEqual(outcome["result"], "PASS")
        self.assertIn("not_tested", outcome)
        self.assertEqual(outcome["safe_comparison_latency_seconds"], .5)

    def test_refuses_a_false_live_offer_on_research_route(self):
        fixtures = iter([
            ({"status": "ok", "service": "coupon-world-shopping-intelligence"}, 1),
            ({"request_route": "research_comparison", "candidate_pool_entered": False,
              "research_comparison": {"commerce": {"purchase_cta_eligible": True}}}, 1),
        ])
        with patch("scripts.verify_runtime_health.get_json", side_effect=lambda *a, **k: next(fixtures)):
            with self.assertRaisesRegex(ValueError, "buyable"):
                probe()


if __name__ == "__main__":
    unittest.main()
