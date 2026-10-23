"""Review-only battery evidence adapter for the existing budget benchmark.

This module does not change the production fit scorer. It classifies capacity,
endurance and charging evidence, rejects incompatible endurance protocols, and
delegates comparable-population math to Issue 06's budget_benchmark module.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

ALLOWED_STATUSES = {
    "VERIFIED_OFFICIAL_SPEC", "VERIFIED_INDEPENDENT_MEASUREMENT",
    "MANUFACTURER_CLAIM", "USER_OPINION", "NOT_VERIFIED", "CONFLICT",
    "INCOMPATIBLE_PROTOCOL",
}


def validate_battery_record(record: dict[str, Any]) -> tuple[bool, list[str]]:
    required = ("canonical_product_id", "model", "metric_name", "metric_value", "unit", "evidence_type", "source_url", "verification_status")
    missing = [key for key in required if record.get(key) in (None, "")]
    status = str(record.get("verification_status") or "")
    if status and status not in ALLOWED_STATUSES:
        missing.append("verification_status_invalid")
    return not missing, missing


def classify_metric(record: dict[str, Any]) -> str:
    name = str(record.get("metric_name") or "").lower()
    if "capacity" in name or name.endswith("mah"):
        return "capacity"
    if any(token in name for token in ("endurance", "active_use", "video_playback", "web_browsing", "gaming", "mixed_use")):
        return "endurance"
    if "charging_time" in name or "charge_time" in name:
        return "charging_time"
    if "charging" in name or "watt" in name:
        return "charging_spec"
    return "other"


def protocol_key(record: dict[str, Any]) -> str | None:
    if classify_metric(record) != "endurance" or record.get("verification_status") != "VERIFIED_INDEPENDENT_MEASUREMENT":
        return None
    protocol = record.get("test_protocol")
    version = record.get("test_version")
    conditions = record.get("test_conditions")
    if not protocol or not version or not conditions:
        return None
    raw = json.dumps({"protocol": protocol, "version": version, "conditions": conditions}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def compatible_endurance_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        key = protocol_key(record)
        if key:
            groups.setdefault(key, []).append(record)
    if not groups:
        return []
    # Use the largest compatible group; never merge unlike protocols.
    return max(groups.values(), key=lambda group: (len(group), sorted(str(x.get("source_record_id", "")) for x in group)))


def build_battery_snapshot(products: list[dict[str, Any]], intent: dict[str, Any], *, evidence_version: str, benchmark_builder: Callable[..., dict[str, Any]] | None = None) -> dict[str, Any]:
    """Delegate capacity/endurance/charging reference math to Issue 06."""
    if benchmark_builder is None:
        try:
            from budget_benchmark import build_budget_benchmark as benchmark_builder
        except ImportError as exc:
            raise RuntimeError("Issue 06 budget_benchmark integration is required") from exc
    metrics = [
        {"name": "battery_capacity_mah", "unit": "mAh", "direction": "higher_is_better"},
        {"name": "battery_active_use_hours", "unit": "hours", "direction": "higher_is_better"},
        {"name": "charging_time_minutes", "unit": "minutes", "direction": "lower_is_better"},
    ]
    snapshot = benchmark_builder(products, intent, metrics, evidence_version=evidence_version)
    snapshot["battery_evidence_contract"] = "capacity/endurance/charging-separated-v1"
    snapshot["backup_quality_status"] = "supported" if snapshot.get("metrics", [{}])[1].get("sample_size", 0) else "insufficient_comparable_endurance"
    return snapshot


def battery_backup_candidates(snapshot: dict[str, Any], limit: int = 3) -> dict[str, Any]:
    metrics = {str(item.get("metric_name")): item for item in snapshot.get("metrics", [])}
    endurance = metrics.get("battery_active_use_hours") or {}
    if not endurance.get("sample_size"):
        return {"status": "INCOMPLETE", "recommendations": [], "reason": "No compatible independently measured endurance evidence; capacity cannot substitute for battery backup."}
    scores = endurance.get("scores") or {}
    ranked = sorted(scores.items(), key=lambda item: (-float(item[1]), item[0]))[:max(1, int(limit))]
    return {"status": "SUPPORTED", "recommendations": [{"canonical_product_id": pid, "endurance_relative": score} for pid, score in ranked], "reason": "Comparable independent endurance protocol only."}
