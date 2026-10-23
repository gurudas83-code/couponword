import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "python"))
from budget_benchmark import (  # noqa: E402
    BENCHMARK_VERSION,
    build_budget_benchmark,
    constraint_signature,
    invalidate_affected_snapshots,
    normalize_budget_ceiling,
)


def phone(pid, price, battery=None, camera=None, cpu=None, *, in_stock=True, fresh=True, verified=True):
    metrics = {}
    if battery is not None: metrics["capacity_mah"] = battery
    if camera is not None: metrics["camera_resolution_mp"] = camera
    if cpu is not None: metrics["cpu_benchmark"] = cpu
    return {
        "product_id": pid, "canonical_product_id": pid, "price": price,
        "price_verified": verified, "offer_status": "in_stock" if in_stock else "out_of_stock",
        "price_fresh": fresh, "verified_metrics": metrics,
        "evidence_ids": ["e-" + pid], "evidence_protocol_versions": ["fixture-v1"],
    }


def intent(budget):
    return {"budget_max": budget, "intent": "mobile", "hard_constraints": ["budget_max"], "priority_weights": {"budget": 20, "battery": 80}}


class BudgetBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.products = [phone("a", 8000, 5000, 50, 400), phone("b", 12000, 6000, 108, 500), phone("c", 18000, 8000, 200, 700)]
        for p in self.products:
            p["fit_signals"] = {"budget": {"match": 1, "status": "verified"}, "battery": {"match": .8, "status": "verified"}}

    def test_any_budget_is_exact_not_anchor_rounded(self):
        self.assertEqual(normalize_budget_ceiling(18000), 18000)
        snap = build_budget_benchmark(self.products, intent(15000), [{"name": "capacity_mah", "unit": "mAh"}], evidence_version="e1", generated_at="fixed")
        self.assertEqual(snap["budget_ceiling_inr"], 15000)
        self.assertEqual(snap["eligible_variant_ids"], ["a", "b"])
        self.assertNotIn("c", snap["eligible_variant_ids"])

    def test_anchor_budgets_use_same_path(self):
        for budget in (10000, 20000, 50000, 100000):
            snap = build_budget_benchmark(self.products, intent(budget), [], evidence_version="e1", generated_at="fixed")
            self.assertEqual(snap["benchmark_version"], BENCHMARK_VERSION)

    def test_strict_budget_and_current_offer_gates(self):
        blocked = [phone("stale", 9000, 5000, in_stock=False), phone("expired", 9000, 5000, fresh=False), phone("unverified", 9000, 5000, verified=False), phone("over", 19000, 5000)]
        for p in blocked: p["fit_signals"] = {"budget": {"match": 1}, "battery": {"match": .8}}
        snap = build_budget_benchmark(blocked, intent(10000), [], evidence_version="e1", generated_at="fixed")
        self.assertEqual(snap["eligible_variant_ids"], [])
        self.assertEqual(snap["verification_status"], "no_verified_current_offer")

    def test_capacity_relative_best_is_100(self):
        snap = build_budget_benchmark(self.products, intent(20000), [{"name": "capacity_mah", "unit": "mAh"}], evidence_version="e1", generated_at="fixed")
        metric = snap["metrics"][0]
        self.assertEqual(metric["metric_reference_value"], 8000)
        self.assertEqual(metric["scores"]["c"], 100.0)
        self.assertEqual(metric["scores"]["a"], 62.5)

    def test_capacity_is_not_endurance(self):
        snap = build_budget_benchmark(self.products, intent(20000), [{"name": "capacity_mah", "unit": "mAh"}], evidence_version="e1", generated_at="fixed")
        self.assertNotIn("endurance_hours", snap["metrics"][0]["metric_name"])

    def test_camera_mp_is_not_camera_quality(self):
        snap = build_budget_benchmark(self.products, intent(20000), [{"name": "camera_resolution_mp", "unit": "MP"}], evidence_version="e1", generated_at="fixed")
        self.assertEqual(snap["metrics"][0]["metric_reference_value"], 200)
        self.assertNotIn("camera_quality", snap["metrics"][0]["metric_name"])

    def test_missing_metric_is_unavailable(self):
        snap = build_budget_benchmark(self.products, intent(20000), [{"name": "measured_endurance_hours", "unit": "hours"}], evidence_version="e1", generated_at="fixed")
        self.assertEqual(snap["metrics"][0]["sample_size"], 0)
        self.assertEqual(snap["metrics"][0]["normalization_method"], "unavailable")

    def test_lower_is_better(self):
        for p, latency in zip(self.products, (100, 50, 25)): p["verified_metrics"]["latency_ms"] = latency
        snap = build_budget_benchmark(self.products, intent(20000), [{"name": "latency_ms", "direction": "lower_is_better", "unit": "ms"}], evidence_version="e1", generated_at="fixed")
        self.assertEqual(snap["metrics"][0]["scores"]["c"], 100.0)
        self.assertEqual(snap["metrics"][0]["scores"]["a"], 25.0)

    def test_snapshot_is_deterministic_for_fixed_timestamp(self):
        args = (self.products, intent(18000), [{"name": "capacity_mah", "unit": "mAh"}])
        a = build_budget_benchmark(*args, evidence_version="e1", generated_at="fixed")
        b = build_budget_benchmark(*args, evidence_version="e1", generated_at="fixed")
        self.assertEqual(a, b)

    def test_constraint_signature_stable(self):
        self.assertEqual(constraint_signature(intent(10000)), constraint_signature(intent(10000)))

    def test_changed_evidence_invalidates(self):
        snap = build_budget_benchmark(self.products, intent(18000), [], evidence_version="e1", generated_at="fixed")
        self.assertTrue(invalidate_affected_snapshots(snap, {"e-a"}, set()))
        self.assertTrue(invalidate_affected_snapshots(snap, set(), {"a"}))

    def test_unrelated_variant_does_not_force_by_itself(self):
        snap = build_budget_benchmark(self.products, intent(18000), [], evidence_version="e1", generated_at="fixed")
        self.assertFalse(invalidate_affected_snapshots(snap, set(), set()))

    def test_no_virtual_ram_metric(self):
        self.products[0]["virtual_ram_gb"] = 12
        snap = build_budget_benchmark(self.products, intent(20000), [{"name": "physical_ram_gb", "unit": "GB"}], evidence_version="e1", generated_at="fixed")
        self.assertEqual(snap["metrics"][0]["sample_size"], 0)

    def test_same_population_for_specialist_metrics(self):
        snap = build_budget_benchmark(self.products, intent(18000), [{"name": "capacity_mah"}, {"name": "camera_resolution_mp"}], evidence_version="e1", generated_at="fixed")
        self.assertEqual(snap["eligible_variant_ids"], ["a", "b", "c"])
        self.assertEqual(snap["metrics"][0]["sample_size"], 3)

    def test_top_ids_are_distinct(self):
        snap = build_budget_benchmark(self.products, intent(18000), [], evidence_version="e1", generated_at="fixed")
        ids = snap["eligible_variant_ids"]
        self.assertEqual(len(ids), len(set(ids)))

    def test_fifty_frozen_replays(self):
        expected = build_budget_benchmark(self.products, intent(18000), [{"name": "capacity_mah"}], evidence_version="e1", generated_at="fixed")
        for _ in range(50):
            self.assertEqual(expected, build_budget_benchmark(copy.deepcopy(self.products), intent(18000), [{"name": "capacity_mah"}], evidence_version="e1", generated_at="fixed"))


if __name__ == "__main__":
    unittest.main()
