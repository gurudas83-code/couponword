"""Inactive Issue 10 candidate-funnel audit adapter.

This module consumes already-available stage facts or pipeline diagnostics. It
does not discover products, change scoring, write caches, or publish offers.
Its only job is to assign a stable trace id and one deterministic first
blocker while retaining later blockers as secondary diagnostics.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable


STAGES = (
    "research",
    "canonical",
    "exact_variant",
    "product_dna",
    "retailer_mapping",
    "fresh_offer",
    "strict_budget",
    "ranking_eligible",
    "displayed",
)


def stable_trace_id(candidate: dict[str, Any]) -> str:
    """Create a deterministic id without exposing a transient list position."""
    identity = {
        "canonical_product_id": candidate.get("canonical_product_id"),
        "retailer_product_id": candidate.get("retailer_product_id"),
        "source_url": candidate.get("source_url"),
        "brand": candidate.get("brand"),
        "model": candidate.get("model"),
        "variant": candidate.get("variant"),
    }
    payload = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    return "trace-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _truthy(value: Any) -> bool:
    return value is True or value == 1 or value == "pass"


def _stage_status(candidate: dict[str, Any], stage: str, budget: float | None) -> bool:
    if stage == "fresh_offer":
        return _truthy(candidate.get(stage)) and candidate.get("verified_price") is not None
    if stage == "strict_budget":
        if budget is None:
            return True
        price = candidate.get("verified_price")
        return price is not None and float(price) <= budget
    return _truthy(candidate.get(stage))


def _reason(candidate: dict[str, Any], stage: str, budget: float | None) -> str:
    explicit = candidate.get(f"{stage}_reason")
    if explicit:
        return str(explicit)
    defaults = {
        "research": "not present in research/discovery input",
        "canonical": "no unique verified canonical owner",
        "exact_variant": "exact physical RAM/storage variant is unresolved",
        "product_dna": "required official Product DNA is unavailable",
        "retailer_mapping": "no verified retailer mapping",
        "fresh_offer": "no fresh verified in-stock offer",
        "strict_budget": (
            "no verified current price for strict budget evaluation"
            if candidate.get("verified_price") is None
            else f"verified price exceeds strict budget {budget:g}"
            if budget is not None
            else "strict budget was not supplied"
        ),
        "ranking_eligible": "approved ranking/evidence threshold not met",
        "displayed": "candidate was not serialized for display",
    }
    return defaults[stage]


def audit_candidate(candidate: dict[str, Any], budget: float | None = None) -> dict[str, Any]:
    """Return one trace with exactly one first blocker and later blockers."""
    trace = dict(candidate)
    trace_id = stable_trace_id(candidate)
    blocked = [stage for stage in STAGES if not _stage_status(candidate, stage, budget)]
    first = blocked[0] if blocked else None
    trace.update({
        "trace_id": trace_id,
        "budget": budget,
        "first_blocker": first,
        "first_blocker_reason": _reason(candidate, first, budget) if first else None,
        "secondary_blockers": [
            {"stage": stage, "reason": _reason(candidate, stage, budget)}
            for stage in blocked[1:]
        ],
    })
    return trace


def audit_candidates(candidates: Iterable[dict[str, Any]], budget: float | None = None) -> list[dict[str, Any]]:
    return [audit_candidate(item, budget=budget) for item in candidates if isinstance(item, dict)]


def summarize_traces(traces: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(traces)
    first_blockers: dict[str, int] = {}
    for row in rows:
        key = str(row.get("first_blocker") or "PASS")
        first_blockers[key] = first_blockers.get(key, 0) + 1
    return {
        "candidate_count": len(rows),
        "first_blocker_breakdown": dict(sorted(first_blockers.items())),
        "passed_count": first_blockers.get("PASS", 0),
    }


def coverage_row(candidates: Iterable[dict[str, Any]], budget: float) -> dict[str, Any]:
    traces = audit_candidates(candidates, budget=budget)
    summary = summarize_traces(traces)

    def count(stage: str) -> int:
        return sum(_stage_status(row, stage, budget) for row in traces)

    return {
        "budget_inr": int(budget),
        "research_count": count("research"),
        "canonical_count": count("canonical"),
        "exact_variant_verified_count": count("exact_variant"),
        "product_dna_supported_count": count("product_dna"),
        "retailer_mapped_count": count("retailer_mapping"),
        "fresh_in_stock_count": count("fresh_offer"),
        "ranking_eligible_count": count("ranking_eligible"),
        "overall_top3_count": count("displayed"),
        "camera_top3_count": 0,
        "battery_top3_count": 0,
        "gaming_top3_count": 0,
        "first_blocker_breakdown": json.dumps(summary["first_blocker_breakdown"], sort_keys=True),
    }


def traces_from_pipeline_result(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Adapt existing pipeline diagnostics without changing the pipeline."""
    traces: list[dict[str, Any]] = []
    for failure in result.get("failures", []):
        if not isinstance(failure, dict):
            continue
        traces.append({
            "candidate_id": failure.get("candidate_id"),
            "source_url": failure.get("source_url"),
            "model": failure.get("title"),
            "research": True,
            "canonical": failure.get("stage") != "canonical_identity",
            "exact_variant": failure.get("stage") not in {"variant_identity", "variant_evidence_integrity"},
            "product_dna": failure.get("stage") not in {"evidence", "official_source"},
            "retailer_mapping": failure.get("stage") != "canonical_identity",
            "fresh_offer": False,
            "ranking_eligible": False,
            "displayed": False,
            "fresh_offer_reason": failure.get("reason"),
        })
    for diagnostic in result.get("fit_diagnostics", []):
        if not isinstance(diagnostic, dict):
            continue
        traces.append({
            "canonical_product_id": diagnostic.get("product_id"),
            "retailer_product_id": diagnostic.get("candidate_asin"),
            "source_url": diagnostic.get("market_source"),
            "brand": diagnostic.get("brand"),
            "model": diagnostic.get("title"),
            "research": True,
            "canonical": bool(diagnostic.get("product_id")),
            "exact_variant": not bool(diagnostic.get("hard_constraint_failures")),
            "product_dna": bool(diagnostic.get("official_source")),
            "retailer_mapping": bool(diagnostic.get("candidate_asin")),
            "fresh_offer": bool((diagnostic.get("price_evidence") or {}).get("verified")),
            "ranking_eligible": diagnostic.get("eligible") is True,
            "displayed": False,
        })
    return audit_candidates(traces)
