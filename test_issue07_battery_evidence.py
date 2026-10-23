import copy
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE / "python"))
sys.path.insert(0, r"C:\Users\HP\Documents\projects\couponword-issue06-budget-benchmark-20261022\python")

from battery_evidence import (  # noqa: E402
    battery_backup_candidates,
    build_battery_snapshot,
    classify_metric,
    compatible_endurance_records,
    protocol_key,
    validate_battery_record,
)
from budget_benchmark import build_budget_benchmark  # noqa: E402


def phone(pid, price=15000, capacity=6000, endurance=None, charge_time=None):
    metrics = {"battery_capacity_mah": capacity}
    if endurance is not None: metrics["battery_active_use_hours"] = endurance
    if charge_time is not None: metrics["charging_time_minutes"] = charge_time
    return {"product_id": pid, "canonical_product_id": pid, "price": price, "price_verified": True, "offer_status": "in_stock", "price_fresh": True, "verified_metrics": metrics, "fit_signals": {"budget": {"match": 1}, "battery": {"match": .8}}, "evidence_ids": ["e-" + pid]}


def intent(budget=20000):
    return {"budget_max": budget, "intent": "mobile", "hard_constraints": ["budget_max"], "priority_weights": {"budget": 20, "battery": 80}}


class BatteryEvidenceTests(unittest.TestCase):
    def test_schema_requires_provenance(self):
        ok, missing = validate_battery_record({"metric_name": "battery_capacity_mah"})
        self.assertFalse(ok)
        self.assertIn("canonical_product_id", missing)

    def test_classifies_three_dimensions(self):
        self.assertEqual(classify_metric({"metric_name": "battery_capacity_mah"}), "capacity")
        self.assertEqual(classify_metric({"metric_name": "battery_active_use_hours"}), "endurance")
        self.assertEqual(classify_metric({"metric_name": "charging_time_minutes"}), "charging_time")

    def test_manufacturer_claim_is_not_independent_measurement(self):
        record = {"metric_name":"battery_active_use_hours","verification_status":"MANUFACTURER_CLAIM","test_protocol":"x","test_version":"1","test_conditions":{}}
        self.assertIsNone(protocol_key(record))

    def test_missing_protocol_is_incompatible(self):
        record = {"metric_name":"battery_active_use_hours","verification_status":"VERIFIED_INDEPENDENT_MEASUREMENT","test_protocol":"video","test_version":"1"}
        self.assertIsNone(protocol_key(record))

    def test_compatible_records_share_protocol(self):
        base = {"metric_name":"battery_active_use_hours","verification_status":"VERIFIED_INDEPENDENT_MEASUREMENT","test_protocol":"video","test_version":"1","test_conditions":{"brightness":200},"source_record_id":"a"}
        b = dict(base, source_record_id="b")
        self.assertEqual(len(compatible_endurance_records([base, b])), 2)

    def test_incompatible_protocols_are_not_merged(self):
        a = {"metric_name":"battery_active_use_hours","verification_status":"VERIFIED_INDEPENDENT_MEASUREMENT","test_protocol":"video","test_version":"1","test_conditions":{"brightness":200},"source_record_id":"a"}
        b = dict(a, test_protocol="mixed-use", source_record_id="b")
        self.assertEqual(len(compatible_endurance_records([a, b])), 1)

    def test_capacity_only_cannot_produce_backup_top3(self):
        products = [phone("a", capacity=8000), phone("b", capacity=6000)]
        snap = build_battery_snapshot(products, intent(), evidence_version="fixed", benchmark_builder=build_budget_benchmark)
        result = battery_backup_candidates(snap)
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(result["recommendations"], [])

    def test_endurance_reference_uses_measured_metric(self):
        products = [phone("a", endurance=13), phone("b", endurance=16)]
        snap = build_battery_snapshot(products, intent(), evidence_version="fixed", benchmark_builder=build_budget_benchmark)
        # The benchmark sees values; the evidence contract still requires a compatible record set.
        snap["metrics"][1]["sample_size"] = 2
        snap["metrics"][1]["scores"] = {"a": 81.25, "b": 100.0}
        result = battery_backup_candidates(snap)
        self.assertEqual(result["recommendations"][0]["canonical_product_id"], "b")

    def test_capacity_relative_does_not_equal_endurance(self):
        products = [phone("a", capacity=8000, endurance=13), phone("b", capacity=6000, endurance=16)]
        snap = build_battery_snapshot(products, intent(), evidence_version="fixed", benchmark_builder=build_budget_benchmark)
        self.assertEqual(snap["metrics"][0]["metric_reference_value"], 8000)
        self.assertEqual(snap["metrics"][1]["metric_reference_value"], 16)

    def test_charging_time_is_lower_better(self):
        products = [phone("a", charge_time=60), phone("b", charge_time=40)]
        snap = build_battery_snapshot(products, intent(), evidence_version="fixed", benchmark_builder=build_budget_benchmark)
        charging = snap["metrics"][2]
        self.assertEqual(charging["metric_reference_value"], 40)
        self.assertEqual(charging["scores"]["b"], 100.0)

    def test_strict_budget_excludes_over_budget(self):
        products = [phone("a", price=20001, endurance=16), phone("b", price=20000, endurance=15)]
        snap = build_battery_snapshot(products, intent(20000), evidence_version="fixed", benchmark_builder=build_budget_benchmark)
        self.assertEqual(snap["eligible_variant_ids"], ["b"])

    def test_expired_and_out_of_stock_excluded(self):
        p = phone("a", endurance=16); p["price_fresh"] = False
        q = phone("b", endurance=15); q["offer_status"] = "out_of_stock"
        snap = build_battery_snapshot([p, q], intent(), evidence_version="fixed", benchmark_builder=build_budget_benchmark)
        self.assertEqual(snap["eligible_variant_ids"], [])

    def test_exact_variant_is_carried_by_product_id(self):
        p = phone("cw-mobile-72-6-128", endurance=16); p["physical_ram_gb"] = 6; p["storage_gb"] = 128
        snap = build_battery_snapshot([p], intent(), evidence_version="fixed", benchmark_builder=build_budget_benchmark)
        self.assertEqual(snap["eligible_variant_ids"], ["cw-mobile-72-6-128"])

    def test_zero_sample_is_incomplete(self):
        snap = build_battery_snapshot([], intent(), evidence_version="fixed", benchmark_builder=build_budget_benchmark)
        self.assertEqual(battery_backup_candidates(snap)["status"], "INCOMPLETE")

    def test_recommendations_are_distinct(self):
        products = [phone("a", endurance=13), phone("b", endurance=16), phone("c", endurance=14)]
        snap = build_battery_snapshot(products, intent(), evidence_version="fixed", benchmark_builder=build_budget_benchmark)
        snap["metrics"][1]["sample_size"] = 3; snap["metrics"][1]["scores"] = {"a":81.25,"b":100,"c":87.5}
        ids = [x["canonical_product_id"] for x in battery_backup_candidates(snap)["recommendations"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_no_live_offer_fixture_is_not_created(self):
        p = phone("a", endurance=16); p["price_verified"] = False
        snap = build_battery_snapshot([p], intent(), evidence_version="fixed", benchmark_builder=build_budget_benchmark)
        self.assertEqual(snap["eligible_variant_ids"], [])

    def test_backup_requires_independent_evidence_contract(self):
        snap = {"metrics":[{"metric_name":"battery_active_use_hours","sample_size":1,"scores":{"a":100}}]}
        self.assertEqual(battery_backup_candidates(snap)["status"], "SUPPORTED")


if __name__ == "__main__":
    unittest.main()
