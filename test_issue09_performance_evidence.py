import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "python"))
from performance_evidence import (  # noqa: E402
    build_performance_snapshot,
    compatible_records,
    gaming_candidates,
    metric_dimension,
    protocol_key,
    validate_performance_record,
)


def record(pid="cw-mobile-1", variant="v1", metric="gpu_score", value=100, **extra):
    base = {
        "canonical_product_id": pid, "exact_variant_id": variant,
        "manufacturer": "Test", "model": "Test Phone", "metric_name": metric,
        "metric_value": value, "unit": "score", "higher_is_better": True,
        "evidence_type": "VERIFIED_INDEPENDENT_MEASUREMENT",
        "source_url": "https://example.test/report", "observed_at": "2026-10-22T00:00:00Z",
        "verification_status": "VERIFIED_INDEPENDENT_MEASUREMENT",
        "benchmark_name": "GPU Bench", "benchmark_version": "1",
        "benchmark_protocol": "same workload", "test_conditions": "room temperature",
    }
    if metric in {"gaming_average_fps", "gaming_sustained_fps"}:
        base.update({"unit": "fps", "game_title": "Game", "game_version": "1.0", "graphics_preset": "High", "resolution": "1080p"})
    base.update(extra)
    return base


class Issue09Tests(unittest.TestCase):
    def test_dimensions_are_separate(self):
        self.assertEqual(metric_dimension({"metric_name": "physical_ram_gb"}), "physical_ram")
        self.assertEqual(metric_dimension({"metric_name": "virtual_ram_gb"}), "virtual_ram_excluded")
        self.assertEqual(metric_dimension({"metric_name": "gpu_score"}), "gpu")
        self.assertEqual(metric_dimension({"metric_name": "gaming_sustained_fps"}), "sustained_gaming")
        self.assertEqual(metric_dimension({"metric_name": "storage_capacity_gb"}), "storage_capacity")
        self.assertEqual(metric_dimension({"metric_name": "storage_sequential_read_mb_s"}), "storage_performance")

    def test_virtual_ram_rejected(self):
        ok, missing = validate_performance_record(record(metric="virtual_ram_gb"))
        self.assertFalse(ok)
        self.assertIn("virtual_or_expanded_ram_is_not_physical_ram", missing)

    def test_identity_and_variant_required(self):
        item = record()
        item.pop("exact_variant_id")
        ok, missing = validate_performance_record(item)
        self.assertFalse(ok)
        self.assertIn("exact_variant_id", missing)

    def test_benchmark_metadata_required(self):
        item = record()
        item.pop("benchmark_version")
        ok, missing = validate_performance_record(item)
        self.assertFalse(ok)
        self.assertIn("benchmark_version", missing)

    def test_fps_metadata_required(self):
        item = record(metric="gaming_average_fps", value=58)
        item.pop("graphics_preset")
        ok, missing = validate_performance_record(item)
        self.assertFalse(ok)
        self.assertIn("graphics_preset", missing)

    def test_cpu_gpu_not_combined(self):
        self.assertNotEqual(protocol_key(record(metric="cpu_single_core")), protocol_key(record(metric="gpu_score")))

    def test_versions_not_combined(self):
        a = record(benchmark_version="1")
        b = record(benchmark_version="2")
        self.assertNotEqual(protocol_key(a), protocol_key(b))
        self.assertEqual(compatible_records([a, b]), [a])

    def test_workloads_not_combined(self):
        a = record(metric="gpu_score", benchmark_protocol="3DMark Wild Life")
        b = record(metric="gpu_score", benchmark_protocol="3DMark Steel Nomad")
        self.assertEqual(compatible_records([a, b]), [a])

    def test_games_and_presets_not_combined(self):
        a = record(metric="gaming_average_fps", graphics_preset="High")
        b = record(metric="gaming_average_fps", graphics_preset="Low")
        self.assertEqual(compatible_records([a, b]), [a])

    def test_peak_and_sustained_separate(self):
        a = record(metric="gaming_average_fps")
        b = record(metric="gaming_sustained_fps")
        self.assertNotEqual(protocol_key(a), protocol_key(b))

    def test_missing_measurement_not_supported(self):
        snap = {"metrics": []}
        result = gaming_candidates(snap)
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(result["recommendations"], [])

    def test_gpu_does_not_become_fps(self):
        snap = {"metrics": [{"metric_name": "gpu_score", "sample_size": 2, "scores": {"a": 100}}]}
        self.assertEqual(gaming_candidates(snap)["status"], "INCOMPLETE")

    def test_gaming_ranks_distinct_ids(self):
        snap = {"metrics": [{"metric_name": "gaming_sustained_fps", "sample_size": 2, "scores": {"b": 100, "a": 80}}]}
        self.assertEqual([x["canonical_product_id"] for x in gaming_candidates(snap)["recommendations"]], ["b", "a"])

    def test_snapshot_delegates_and_is_deterministic(self):
        products = [{"canonical_product_id": "a", "price": 19000, "price_verified": True, "offer_status": "in_stock", "price_fresh": True, "fit_signals": {"budget": 1.0}, "performance_evidence": [record(pid="a", metric="gpu_score")], "verified_metrics": {"gpu_score": 100}}]
        intent = {"budget_max": 20000, "hard_constraints": ["budget_max"], "priority_weights": {"budget": 100}}
        def builder(*args, **kwargs):
            return {"metrics": [{"metric_name": "gpu_score", "sample_size": 1, "scores": {"a": 100}}, {"metric_name": "gaming_sustained_fps", "sample_size": 0, "scores": {}}]}
        one = build_performance_snapshot(products, intent, evidence_version="test", benchmark_builder=builder, generated_at="fixed")
        two = build_performance_snapshot(products, intent, evidence_version="test", benchmark_builder=builder, generated_at="fixed")
        self.assertEqual(one, two)
        self.assertEqual(one["performance_evidence_contract"], "cpu-gpu-gaming-storage-separated-v1")

    def test_fifty_frozen_replays(self):
        snap = {"metrics": [{"metric_name": "gaming_sustained_fps", "sample_size": 2, "scores": {"a": 100, "b": 80}}]}
        outputs = [gaming_candidates(snap) for _ in range(50)]
        self.assertTrue(all(item == outputs[0] for item in outputs))


if __name__ == "__main__":
    unittest.main()
