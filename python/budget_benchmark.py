"""Experimental budget-relative benchmark layer.

This module is deliberately not imported by the production recommendation path.
It consumes the existing fit engine, applies the existing hard eligibility gates,
and creates reproducible research snapshots for review.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from weighted_fit_engine import calculate_product_fit

BENCHMARK_VERSION = "budget-relative-v2"
STANDARD_BUDGET_CEILINGS = (
    10_000, 20_000, 30_000, 40_000, 50_000,
    60_000, 70_000, 80_000, 90_000, 100_000,
    110_000, 120_000, 130_000, 140_000, 150_000,
)
VERIFIED_METRIC_STATUSES = {
    "VERIFIED_OFFICIAL_SPEC", "OFFICIAL_HARDWARE_SPEC",
    "VERIFIED_INDEPENDENT_MEASUREMENT", "STRUCTURED_EDITORIAL_EVALUATION",
}


def _json_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalize_budget_ceiling(value: Any) -> int:
    """Accept any positive INR ceiling; no anchor rounding is performed."""
    if isinstance(value, bool):
        raise ValueError("budget must be a positive INR number")
    try:
        budget = int(round(float(value)))
    except (TypeError, ValueError):
        raise ValueError("budget must be a positive INR number") from None
    if budget <= 0:
        raise ValueError("budget must be a positive INR number")
    return budget


def constraint_signature(intent: dict[str, Any]) -> str:
    """Stable signature for constraints that define a comparable population."""
    keys = ("brands", "must_have", "avoid", "preferred", "hard_constraints", "category")
    return _json_hash({key: intent.get(key) for key in keys})


def _offer_is_verified_current(product: dict[str, Any], budget: int) -> tuple[bool, str]:
    price = product.get("price")
    try:
        price_f = float(price)
    except (TypeError, ValueError):
        return False, "current verified price unavailable"
    if price_f > budget:
        return False, "price exceeds requested budget"
    if not product.get("canonical_product_id") and not product.get("product_id"):
        return False, "canonical product identity unavailable"
    if product.get("price_verified") is not True:
        return False, "price evidence is not verified"
    if product.get("offer_status") != "in_stock":
        return False, "offer is not verified in_stock"
    if product.get("price_fresh") is not True:
        return False, "price evidence is not within freshness policy"
    return True, "verified current offer"


def eligible_population(products: list[dict[str, Any]], intent: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Run the existing fit engine, then require a verified current offer."""
    budget = normalize_budget_ceiling(intent.get("budget_max"))
    eligible: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    for product in products:
        assessment = calculate_product_fit(product, {**intent, "budget_max": budget})
        if not assessment.get("eligible"):
            rejected.append({"identity": str(product.get("product_id") or product.get("canonical_product_id") or "UNKNOWN"), "reason": "; ".join(assessment.get("hard_constraint_failures") or ["existing fit/evidence gate failed"])})
            continue
        ok, reason = _offer_is_verified_current(product, budget)
        if not ok:
            rejected.append({"identity": str(product.get("product_id") or product.get("canonical_product_id") or "UNKNOWN"), "reason": reason})
            continue
        item = dict(product)
        item["fit_assessment"] = assessment
        eligible.append(item)
    return eligible, rejected


def _metric_value(product: dict[str, Any], metric_name: str) -> float | None:
    metrics = product.get("verified_metrics")
    if not isinstance(metrics, dict):
        metrics = {}
    value = metrics.get(metric_name, product.get(metric_name))
    try:
        if value is None or isinstance(value, bool):
            return None
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def _metric_observation(product: dict[str, Any], metric: dict[str, Any]) -> dict[str, Any] | None:
    """Return one comparable observation without inventing missing evidence.

    Structured metric records are preferred.  The compact ``verified_metrics``
    map remains supported for existing isolated fixtures and is never promoted
    to a live offer by this module.
    """
    name = str(metric["name"])
    expected_group = metric.get("comparable_group_id")
    records = product.get("metric_records") or product.get("verified_metric_records") or []
    if isinstance(records, list):
        matches = [record for record in records if isinstance(record, dict) and record.get("metric_name") == name]
        if expected_group is not None:
            matches = [record for record in matches if record.get("comparable_group_id") == expected_group]
        matches = [record for record in matches if record.get("verification_status") in VERIFIED_METRIC_STATUSES]
        for record in matches:
            value = _metric_value({"verified_metrics": {name: record.get("metric_value")}}, name)
            if value is not None:
                return record | {"metric_value": value}
        if matches:
            return None
    value = _metric_value(product, name)
    if value is None:
        return None
    metadata = (product.get("metric_metadata") or {}).get(name, {})
    if not isinstance(metadata, dict):
        metadata = {}
    if expected_group is not None and metadata.get("comparable_group_id") not in (None, expected_group):
        return None
    return {
        "metric_name": name,
        "metric_value": value,
        "metric_unit": metric.get("unit"),
        "source_name": metadata.get("source_name"),
        "source_url": metadata.get("source_url"),
        "comparable_group_id": metadata.get("comparable_group_id", expected_group),
        "verification_status": metadata.get("verification_status", "FIXTURE_OR_EXISTING_VERIFIED_METRIC"),
        "test_protocol": metadata.get("test_protocol"),
        "test_version": metadata.get("test_version"),
        "observed_at": metadata.get("observed_at"),
    }


def _metric_snapshot(products: list[dict[str, Any]], metric: dict[str, Any]) -> dict[str, Any]:
    name = str(metric["name"])
    direction = str(metric.get("direction", "higher_is_better"))
    values = [(p, _metric_observation(p, metric)) for p in products]
    values = [(p, observation) for p, observation in values if observation is not None]
    if not values:
        return {"metric_name": name, "metric_reference_value": None, "reference_product_id": None, "normalization_method": "unavailable", "sample_size": 0, "missing_evidence_count": len(products), "conflict_count": 0, "scores": {}, "scorecard": []}
    numeric_values = [(p, float(observation["metric_value"]), observation) for p, observation in values]
    reference = max(v for _, v, _ in numeric_values) if direction == "higher_is_better" else min(v for _, v, _ in numeric_values)
    leaders = sorted(str(p.get("canonical_product_id") or p.get("product_id")) for p, value, _ in numeric_values if value == reference)
    reference_id = leaders[0] if leaders else None
    scores: dict[str, float | None] = {}
    scorecard: list[dict[str, Any]] = []
    for product, value, observation in numeric_values:
        identity = str(product.get("canonical_product_id") or product.get("product_id"))
        if reference == 0:
            score = 100.0 if value == 0 else None
        elif direction == "higher_is_better":
            score = round(value / reference * 100, 4)
        else:
            score = round(reference / value * 100, 4) if value > 0 else None
        scores[identity] = score
        scorecard.append({
            "canonical_product_id": identity,
            "metric_value": value,
            "reference_product_id": reference_id,
            "reference_value": reference,
            "relative_score": score,
            "source_name": observation.get("source_name"),
            "source_url": observation.get("source_url"),
            "verification_status": observation.get("verification_status"),
            "comparable_group_id": observation.get("comparable_group_id", metric.get("comparable_group_id")),
            "test_protocol": observation.get("test_protocol"),
            "test_version": observation.get("test_version"),
            "observed_at": observation.get("observed_at"),
        })
    return {"metric_name": name, "metric_reference_value": reference, "reference_product_id": reference_id, "reference_product_ids": leaders, "metric_unit": metric.get("unit"), "normalization_method": direction, "sample_size": len(values), "missing_evidence_count": len(products) - len(values), "conflict_count": 0, "scores": scores, "scorecard": scorecard}


def build_budget_benchmark(products: list[dict[str, Any]], intent: dict[str, Any], metrics: list[dict[str, Any]], *, evidence_version: str, scoring_version: str = "weighted-fit-engine-v1", generated_at: str | None = None) -> dict[str, Any]:
    """Build a versioned benchmark for an exact budget ceiling.

    Results are research/experimental context only. The production ranker is
    unchanged and no live offer is created by this function.
    """
    budget = normalize_budget_ceiling(intent.get("budget_max"))
    eligible, rejected = eligible_population(products, {**intent, "budget_max": budget})
    metric_snapshots = [_metric_snapshot(eligible, metric) for metric in metrics]
    eligible_ids = sorted(str(p.get("canonical_product_id") or p.get("product_id")) for p in eligible)
    snapshot = {
        "budget_ceiling_inr": budget,
        "intent": intent.get("intent", "unknown"),
        "constraint_signature": constraint_signature(intent),
        "eligible_variant_ids": eligible_ids,
        "eligible_products": [
            {
                "canonical_product_id": str(p.get("canonical_product_id") or p.get("product_id")),
                "exact_variant_id": p.get("exact_variant_id") or p.get("variant_id") or str(p.get("canonical_product_id") or p.get("product_id")),
                "manufacturer": p.get("manufacturer") or p.get("brand"),
                "model": p.get("model") or p.get("title"),
                "physical_ram_gb": p.get("physical_ram_gb"),
                "storage_gb": p.get("storage_gb"),
            }
            for p in eligible
        ],
        "eligible_set_hash": _json_hash(eligible_ids),
        "benchmark_version": BENCHMARK_VERSION,
        "scoring_version": scoring_version,
        "metrics": metric_snapshots,
        "source_evidence_ids": sorted({str(x) for p in eligible for x in (p.get("evidence_ids") or [])}),
        "source_protocol_versions": sorted({str(x) for p in eligible for x in (p.get("evidence_protocol_versions") or [])}),
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "verification_status": "research_snapshot" if eligible else "LIVE_ELIGIBLE_POOL_EMPTY",
        "rejected": rejected,
        "production_scoring_changed": False,
    }
    snapshot["snapshot_id"] = _json_hash({k: v for k, v in snapshot.items() if k not in {"generated_at", "snapshot_id"}})
    return snapshot


def build_budget_reference_snapshots(
    products: list[dict[str, Any]],
    intent: dict[str, Any],
    metrics: list[dict[str, Any]],
    *,
    evidence_version: str,
    budgets: list[int] | tuple[int, ...] = STANDARD_BUDGET_CEILINGS,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build independent cumulative snapshots for standard or exact budgets."""
    ceilings = [normalize_budget_ceiling(value) for value in budgets]
    if len(set(ceilings)) != len(ceilings):
        raise ValueError("budget ceilings must be unique")
    snapshots = [
        build_budget_benchmark(
            products,
            {**intent, "budget_max": ceiling},
            metrics,
            evidence_version=evidence_version,
            generated_at=generated_at,
        )
        for ceiling in ceilings
    ]
    return {
        "benchmark_version": BENCHMARK_VERSION,
        "snapshot_type": "RESEARCH_REFERENCE_ONLY",
        "budgets": ceilings,
        "snapshots": snapshots,
        "production_scoring_changed": False,
    }


def build_metric_reference_matrix(snapshot_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten independent metric winners into an auditable matrix."""
    rows: list[dict[str, Any]] = []
    for snapshot in snapshot_bundle.get("snapshots", []):
        budget = snapshot.get("budget_ceiling_inr")
        for metric in snapshot.get("metrics", []):
            rows.append({
                "budget": budget,
                "metric": metric.get("metric_name"),
                "reference_product_id": metric.get("reference_product_id") or "UNAVAILABLE",
                "exact_variant": next((p.get("exact_variant_id") for p in snapshot.get("eligible_products", []) if p.get("canonical_product_id") == metric.get("reference_product_id")), "UNKNOWN"),
                "actual_value": metric.get("metric_reference_value") if metric.get("metric_reference_value") is not None else "UNAVAILABLE",
                "unit": metric.get("metric_unit"),
                "source": ";".join(sorted({str(item.get("source_name")) for item in metric.get("scorecard", []) if item.get("source_name")})) or "UNAVAILABLE",
                "protocol": "|".join(sorted({str(item.get("test_protocol")) for item in metric.get("scorecard", []) if item.get("test_protocol")})) or "UNAVAILABLE",
                "test_version": "|".join(sorted({str(item.get("test_version")) for item in metric.get("scorecard", []) if item.get("test_version")})) or "UNAVAILABLE",
                "date": "|".join(sorted({str(item.get("observed_at")) for item in metric.get("scorecard", []) if item.get("observed_at")})) or "UNAVAILABLE",
                "evidence_status": "SUPPORTED" if metric.get("sample_size") else "NO_COMPARABLE_VERIFIED_REFERENCE",
                "eligible_sample_count": metric.get("sample_size", 0),
            })
    return rows


def invalidate_affected_snapshots(old_snapshot: dict[str, Any], new_evidence_ids: set[str], changed_variant_ids: set[str]) -> bool:
    """Return whether a snapshot must be regenerated after evidence changes."""
    old_ids = set(old_snapshot.get("eligible_variant_ids") or [])
    old_evidence = set(old_snapshot.get("source_evidence_ids") or [])
    return bool(old_ids.intersection(changed_variant_ids) or old_evidence.intersection(new_evidence_ids) or changed_variant_ids)
