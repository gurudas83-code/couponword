"""Read-only activation checks for the existing engine wiring."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python"))


class EngineActivationStatusTests(unittest.TestCase):
    def test_existing_connector_set_is_safe_and_explicit(self):
        from retailer_connector_manager import RetailerConnectorManager

        manager = RetailerConnectorManager()
        self.assertEqual([connector.name for connector in manager.connectors], ["amazon", "flipkart"])
        self.assertFalse(any(getattr(connector, "live_data_available", False) for connector in manager.connectors))

    def test_existing_store_has_no_fresh_buyable_offer(self):
        from retailer_offer_store import find_fresh_verified_offer, load_offer_database

        records = load_offer_database().get("offers", [])
        self.assertEqual(len(records), 7)
        fresh = 0
        for record in records:
            if find_fresh_verified_offer(
                product_id=record.get("product_id", ""),
                brand=record.get("brand", ""),
                model=record.get("model", ""),
                variant=record.get("variant", ""),
            ):
                fresh += 1
        self.assertEqual(fresh, 0)

    def test_existing_workflows_do_not_claim_six_hour_mobile_refresh(self):
        workflows = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
        text = "\n".join(path.read_text(encoding="utf-8") for path in workflows)
        self.assertNotIn("30 0,6,12,18 * * *", text)
        self.assertIn("30 3 * * *", text)


if __name__ == "__main__":
    unittest.main()
