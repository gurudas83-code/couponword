"""Focused regression for the test-only provider-disabled local E2E lane."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent
GUARD_PATH = ROOT / "reports" / "local_e2e_closure" / "network_guard_server.py"


def load_guard_module():
    spec = importlib.util.spec_from_file_location("final_network_guard", GUARD_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {GUARD_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProviderDisabledLocalE2ETests(unittest.TestCase):
    def test_provider_seam_is_not_invoked_and_route_stays_zero_offer(self):
        guard = load_guard_module()
        log_path = guard.LOG
        before = log_path.read_text(encoding="utf-8").splitlines() if log_path.exists() else []

        with patch.object(guard.market_discovery, "search_asins", autospec=True) as provider:
            client = guard.shopping_api.app.test_client()
            response = client.get("/api/recommend?q=smartphone%20under%2018000")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["recommendations"], [])
        self.assertEqual(payload["data_lane"], "actual_local_read_only_zero_fresh_offer_state")
        self.assertEqual(provider.call_count, 0)

        after = log_path.read_text(encoding="utf-8").splitlines() if log_path.exists() else []
        self.assertEqual(after, before)
        for line in after:
            if not line.strip():
                continue
            record = json.loads(line)
            self.assertNotIn("amazon.in", record["target"])


if __name__ == "__main__":
    unittest.main()
