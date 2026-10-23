"""Review-only CPU/GPU/gaming evidence adapter.

The adapter keeps physical RAM, synthetic benchmarks, storage throughput and
measured gaming results as separate dimensions.  Snapshot math is delegated to
the existing Issue 06 budget benchmark implementation; this module does not
alter production ranking or weights.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

QUALITY_TYPES = {
    "OFFICIAL_HARDWARE_SPEC",
    "VERIFIED_INDEPENDENT_MEASUREMENT",
    "STRUCTURED_EDITORIAL_EVALUATION",
    "MANUFACTURER_CLAIM",
    "USER_OPINION",
    "NOT_VERIFIED",
    "CONFLICT",
}

METRIC_DIMENSIONS = {
    "physical_ram_gb": "physical_ram",
    "cpu_single_core": "cpu",
    "cpu_multi_core": "cpu",
    "sustained_cpu_score": "sustained_cpu",
    "gpu_score": "gpu",
    "sustained_gpu_score": "sustained_gpu",
    "gaming_average_fps": "gaming_fps",
    "gaming_1_percent_low_fps": "gaming_fps",
    "gaming_sustained_fps": "sustained_gaming",
    "frame_time_stability": "frame_time",
    "thermal_throttle_percent": "thermal",
    "storage_capacity_gb": "storage_capacity",
    "storage_sequential_read_mb_s": "storage_performance",
    "storage_random_io": "storage_performance",
}


def metric_dimension(record: dict[str, Any]) -> str:
    name = str(record.get("metric_name") or "").strip().lower()
    if any(token in name for token in ("virtual", "extended", "expansion", "ram plus")):
        return "virtual_ram_excluded"
    return METRIC_DIMENSIONS.get(name, "other")


def validate_performance_record(record: dict[str, Any]) -> tuple[bool, list[str]]:
    required = (
        "canonical_product_id", "exact_variant_id", "manufacturer", "model",
        "metric_name", "metric_value", "unit", "higher_is_better",
        "evidence_type", "source_url", "observed_at", "verification_status",
    )
    missing = [key for key in required if record.get(key) in (None, "")]
    if record.get("verification_status") not in QUALITY_TYPES:
        missing.append("verification_status_invalid")
    if metric_dimension(record) == "virtual_ram_excluded":
        missing.append("virtual_or_expanded_ram_is_not_physical_ram")
    if metric_dimension(record) in {"cpu", "gpu", "gaming_fps", "sustained_gaming", "storage_performance"}:
        for key in ("benchmark_name", "benchmark_version", "benchmark_protocol", "test_conditions"):
            if record.get(key) in (None, ""):
                missing.append(key)
    if metric_dimension(record) in {"gaming_fps", "sustained_gaming", "frame_time"}:
        for key in ("game_title", "game_version", "graphics_preset", "resolution"):
            if record.get(key) in (None, ""):
                missing.append(key)
    return not missing, missing


def protocol_key(record: dict[str, Any]) -> str | None:
    """Return a compatibility key; incompatible protocols never merge."""
    ok, _ = validate_performance_record(record)
    dimension = metric_dimension(record)
    if not ok or dimension in {"physical_ram", "storage_capacity", "virtual_ram_excluded", "other"}:
        return None
    fields = {
        "dimension": dimension,
        "metric_name": record.get("metric_name"),
        "unit": record.get("unit"),
        "benchmark_name": record.get("benchmark_name"),
        "benchmark_version": record.get("benchmark_version"),
        "benchmark_protocol": record.get("benchmark_protocol"),
        "test_conditions": record.get("test_conditions"),
        "game_title": record.get("game_title"),
        "game_version": record.get("game_version"),
        "graphics_preset": record.get("graphics_preset"),
        "resolution": record.get("resolution"),
    }
    return hashlib.sha256(json.dumps(fields, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def compatible_records(records: list[dict[str, Any]], dimension: str | None = None) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        if dimension and metric_dimension(record) != dimension:
            continue
        key = protocol_key(record)
        if key:
            groups.setdefault(key, []).append(record)
    return max(groups.values(), key=len) if groups else []


def build_performance_snapshot(
    products: list[dict[str, Any]],
    intent: dict[str, Any],
    *,
    evidence_version: str,
    benchmark_builder: Callable[..., dict[str, Any]] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    if benchmark_builder is None:
        try:
            from budget_benchmark import build_budget_benchmark as benchmark_builder
        except ImportError as exc:
            raise RuntimeError("Issue 06 budget_benchmark integration is required") from exc
    metrics = [
        {"name": "cpu_single_core", "unit": "score", "direction": "higher_is_better"},
        {"name": "cpu_multi_core", "unit": "score", "direction": "higher_is_better"},
        {"name": "gpu_score", "unit": "score", "direction": "higher_is_better"},
        {"name": "gaming_average_fps", "unit": "fps", "direction": "higher_is_better"},
        {"name": "gaming_sustained_fps", "unit": "fps", "direction": "higher_is_better"},
        {"name": "storage_sequential_read_mb_s", "unit": "MB/s", "direction": "higher_is_better"},
    ]
    kwargs = {"evidence_version": evidence_version}
    if generated_at is not None:
        kwargs["generated_at"] = generated_at
    snapshot = benchmark_builder(products, intent, metrics, **kwargs)
    dimensions = {metric_dimension(record) for product in products for record in (product.get("performance_evidence") or []) if isinstance(record, dict)}
    snapshot["performance_evidence_contract"] = "cpu-gpu-gaming-storage-separated-v1"
    snapshot["dimensions_present"] = sorted(dimensions)
    snapshot["quality_status"] = "supported" if any(item.get("sample_size", 0) for item in snapshot.get("metrics", [])) else "insufficient_comparable_performance_evidence"
    return snapshot


def gaming_candidates(snapshot: dict[str, Any], limit: int = 3) -> dict[str, Any]:
    metrics = {str(item.get("metric_name")): item for item in snapshot.get("metrics", [])}
    gaming = metrics.get("gaming_sustained_fps") or metrics.get("gaming_average_fps") or {}
    if not gaming.get("sample_size"):
        return {"status": "INCOMPLETE", "recommendations": [], "reason": "No compatible measured gaming evidence; CPU/GPU/RAM cannot substitute for FPS."}
    ranked = sorted((gaming.get("scores") or {}).items(), key=lambda item: (-float(item[1]), item[0]))[:max(1, int(limit))]
    return {"status": "SUPPORTED", "recommendations": [{"canonical_product_id": pid, "gaming_relative": score} for pid, score in ranked], "reason": "Compatible gaming protocol only."}
