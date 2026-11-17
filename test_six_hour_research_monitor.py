#!/usr/bin/env python3
"""Offline tests for the bounded, scheduled research monitor."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest
from unittest.mock import patch

from scripts import six_hour_research_monitor as monitor
from scripts import quickcommerce_catalogue_audit as audit


class SixHourResearchMonitorTests(unittest.TestCase):
    def setUp(self):
        self.t0 = datetime(2026, 11, 17, tzinfo=timezone.utc)
        monitor.PRIVATE_DIR.mkdir(parents=True, exist_ok=True)

    def test_paid_targets_are_two_approved_top30_mobiles_only(self):
        rows = monitor.select_targets(self.t0)
        self.assertEqual(len(rows), 2)
        self.assertEqual(len({x["audit_id"] for x in rows}), 2)
        pilot = json.loads((monitor.ROOT / "data/top30_research_pilot_20261113.json").read_text())
        allowed = {item["model_key"] for item in pilot["selected_models"]}
        self.assertEqual(len(allowed), 30)
        self.assertTrue(all(row["category"] == "mobiles" and row["audit_id"] in allowed for row in rows))
        self.assertTrue(all(row["audit_id"] not in {item["audit_id"] for item in audit.load_targets("all") if item["category"] != "mobiles"} for row in rows))

    def test_rotation_in_each_six_hour_slot(self):
        first = monitor.select_targets(self.t0)
        next_slot = monitor.select_targets(self.t0 + timedelta(hours=6))
        self.assertNotEqual([x["audit_id"] for x in first],
                            [x["audit_id"] for x in next_slot])
        self.assertEqual(monitor.slot_index(self.t0 + timedelta(hours=6, minutes=12)), 1)

    def test_hard_cap_and_aware_clock(self):
        with self.assertRaises(ValueError):
            monitor.select_targets(self.t0, limit=3)
        with self.assertRaises(ValueError):
            monitor.slot_index(datetime(2026, 11, 17))
        with self.assertRaises(ValueError):
            monitor.execute(now=self.t0, live=True, max_calls=0)
        with self.assertRaises(ValueError):
            monitor.execute(now=self.t0, live=True, max_calls=3)
        with self.assertRaises(ValueError):
            monitor.execute(now=self.t0, live=False, max_calls=1)

    def test_catalogue_health_is_read_only_and_auditable(self):
        health = monitor.catalogue_health()
        self.assertEqual((health["mobile_models"], health["tv_models"], health["earbud_models"]),
                         (232, 20, 20))
        self.assertEqual(health["mobile_photos_with_existing_verified_references"], 58)
        self.assertEqual(health["specification_links_checked_live_by_this_agent"], 0)

    def test_offline_default_spends_no_credits(self):
        with TemporaryDirectory(dir=monitor.PRIVATE_DIR) as tmp:
            output = Path(tmp) / "report.json"
            result = monitor.execute(now=self.t0, live=False, max_calls=0, output=output)
            self.assertEqual(result["provider_research"]["calls_attempted"], 0)
            self.assertTrue(output.exists())
            stored = json.loads(output.read_text())
            self.assertFalse(stored["publication_authorized"])
            self.assertEqual(stored["new_public_prices"], 0)
            self.assertFalse(stored["public_files_modified"])

    def test_fixture_live_uses_two_top30_calls_only_and_never_publishes(self):
        fixture = json.loads((monitor.ROOT / "tests/fixtures/quickcommerce_flipkart_a56_search.json").read_text())
        connector = audit.QuickCommerceFlipkartConnector(fixture=fixture)
        with TemporaryDirectory(dir=monitor.PRIVATE_DIR) as tmp:
            with patch.object(audit.time, "sleep"):
                result = monitor.execute(now=self.t0, live=True, max_calls=2,
                                         connector=connector, output=Path(tmp) / "report.json")
        self.assertEqual(result["provider_research"]["calls_attempted"], 2)
        self.assertFalse(result["provider_research"]["publishable"])
        self.assertFalse(result["ranking_modified"])
        self.assertEqual(result["new_public_stock_claims"], 0)
        self.assertEqual(result["new_public_images"], 0)

    def test_report_cannot_escape_private_evidence_directory(self):
        with self.assertRaises(ValueError):
            monitor.execute(now=self.t0, live=False, max_calls=0,
                            output=monitor.ROOT / "data/retailer_offers.json")


if __name__ == "__main__":
    unittest.main()
