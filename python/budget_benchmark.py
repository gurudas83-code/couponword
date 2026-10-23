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

BENCHMARK_VERSION = "budget-relative-v1"


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


def _metric_snapshot(products: list[dict[str, Any]], metric: dict[str, Any]) -> dict[str, Any]:
    name = str(metric["name"])
    direction = str(metric.get("direction", "higher_is_better"))
    values = [(p, _metric_value(p, name)) for p in products]
    values = [(p, v) for p, v in values if v is not None]
    if not values:
        return {"metric_name": name, "metric_reference_value": None, "normalization_method": "unavailable", "sample_size": 0, "missing_evidence_count": len(products), "conflict_count": 0, "scores": {}}
    reference = max(v for _, v in values) if direction == "higher_is_better" else min(v for _, v in values)
    scores: dict[str, float | None] = {}
    for product, value in values:
        identity = str(product.get("canonical_product_id") or product.get("product_id"))
        if reference == 0:
            score = 100.0 if value == 0 else None
        elif direction == "higher_is_better":
            score = round(value / reference * 100, 4)
        else:
            score = round(reference / value * 100, 4) if value > 0 else None
        scores[identity] = score
    return {"metric_name": name, "metric_reference_value": reference, "metric_unit": metric.get("unit"), "normalization_method": direction, "sample_size": len(values), "missing_evidence_count": len(products) - len(values), "conflict_count": 0, "scores": scores}


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
        "eligible_set_hash": _json_hash(eligible_ids),
        "benchmark_version": BENCHMARK_VERSION,
        "scoring_version": scoring_version,
        "metrics": metric_snapshots,
        "source_evidence_ids": sorted({str(x) for p in eligible for x in (p.get("evidence_ids") or [])}),
        "source_protocol_versions": sorted({str(x) for p in eligible for x in (p.get("evidence_protocol_versions") or [])}),
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "verification_status": "research_snapshot" if eligible else "no_verified_current_offer",
        "rejected": rejected,
        "production_scoring_changed": False,
    }
    snapshot["snapshot_id"] = _json_hash({k: v for k, v in snapshot.items() if k not in {"generated_at", "snapshot_id"}})
    return snapshot


def invalidate_affected_snapshots(old_snapshot: dict[str, Any], new_evidence_ids: set[str], changed_variant_ids: set[str]) -> bool:
    """Return whether a snapshot must be regenerated after evidence changes."""
    old_ids = set(old_snapshot.get("eligible_variant_ids") or [])
    old_evidence = set(old_snapshot.get("source_evidence_ids") or [])
    return bool(old_ids.intersection(changed_variant_ids) or old_evidence.intersection(new_evidence_ids) or changed_variant_ids)
