"""Review-only camera evidence adapter.

Hardware specifications and measured photo/video quality stay separate. Metric
math is delegated to Issue 06's budget benchmark implementation.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

ALLOWED = {"OFFICIAL_HARDWARE_SPEC", "VERIFIED_INDEPENDENT_MEASUREMENT", "STRUCTURED_EDITORIAL_EVALUATION", "MANUFACTURER_CLAIM", "USER_OPINION", "NOT_VERIFIED", "CONFLICT"}


def classify_camera_metric(record: dict[str, Any]) -> str:
    name = str(record.get("metric_name") or "").lower()
    if any(x in name for x in ("megapixel", "resolution", "sensor", "ois", "eis", "aperture", "autofocus", "lens", "zoom", "camera_module")):
        return "hardware"
    if any(x in name for x in ("photo", "low_light", "dynamic_range", "detail", "color", "exposure", "portrait", "texture")):
        return "photo_quality"
    if any(x in name for x in ("video", "stabilization", "motion", "video_quality", "video_detail")):
        return "video_quality"
    if "front" in name or "selfie" in name:
        return "front_camera"
    return "other"


def validate_camera_record(record: dict[str, Any]) -> tuple[bool, list[str]]:
    required = ("canonical_product_id", "model", "camera_module", "metric_name", "metric_value", "unit", "evidence_type", "source_url", "verification_status")
    missing = [key for key in required if record.get(key) in (None, "")]
    if record.get("verification_status") not in ALLOWED:
        missing.append("verification_status_invalid")
    if classify_camera_metric(record) in {"photo_quality", "video_quality"} and record.get("evidence_type") not in {"VERIFIED_INDEPENDENT_MEASUREMENT", "STRUCTURED_EDITORIAL_EVALUATION"}:
        missing.append("quality_evidence_type_not_measurement_or_structured_review")
    return not missing, missing


def protocol_key(record: dict[str, Any]) -> str | None:
    if classify_camera_metric(record) not in {"photo_quality", "video_quality"}:
        return None
    if record.get("verification_status") != "VERIFIED_INDEPENDENT_MEASUREMENT":
        return None
    required = {"source_name": record.get("source_name"), "test_protocol": record.get("test_protocol"), "test_version": record.get("test_version"), "metric_definition": record.get("metric_definition"), "camera_module": record.get("camera_module"), "test_conditions": record.get("test_conditions")}
    if any(value in (None, "") for value in required.values()):
        return None
    return hashlib.sha256(json.dumps(required, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def compatible_quality_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        key = protocol_key(record)
        if key:
            groups.setdefault(key, []).append(record)
    return max(groups.values(), key=len) if groups else []


def build_camera_snapshot(products: list[dict[str, Any]], intent: dict[str, Any], *, evidence_version: str, benchmark_builder: Callable[..., dict[str, Any]] | None = None, generated_at: str | None = None) -> dict[str, Any]:
    if benchmark_builder is None:
        try:
            from budget_benchmark import build_budget_benchmark as benchmark_builder
        except ImportError as exc:
            raise RuntimeError("Issue 06 budget_benchmark integration is required") from exc
    metrics = [
        {"name": "camera_resolution_mp", "unit": "MP", "direction": "higher_is_better"},
        {"name": "photo_quality_score", "unit": "score", "direction": "higher_is_better"},
        {"name": "video_quality_score", "unit": "score", "direction": "higher_is_better"},
    ]
    kwargs = {"evidence_version": evidence_version}
    if generated_at is not None:
        kwargs["generated_at"] = generated_at
    snap = benchmark_builder(products, intent, metrics, **kwargs)
    snap["camera_evidence_contract"] = "hardware-photo-video-separated-v1"
    snap["quality_status"] = "supported" if any(x.get("sample_size", 0) for x in snap.get("metrics", [])[1:]) else "insufficient_comparable_quality_evidence"
    return snap


def camera_candidates(snapshot: dict[str, Any], limit: int = 3) -> dict[str, Any]:
    metrics = {str(x.get("metric_name")): x for x in snapshot.get("metrics", [])}
    quality = metrics.get("photo_quality_score") or {}
    if not quality.get("sample_size"):
        return {"status": "INCOMPLETE", "recommendations": [], "reason": "No comparable independent photo-quality evidence; resolution hardware is not a quality substitute."}
    ranked = sorted((quality.get("scores") or {}).items(), key=lambda x: (-float(x[1]), x[0]))[:max(1, int(limit))]
    return {"status": "SUPPORTED", "recommendations":[{"canonical_product_id":pid,"quality_relative":score} for pid,score in ranked], "reason":"Comparable quality protocol only."}
