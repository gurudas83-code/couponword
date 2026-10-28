"""Additive Issue 17 API/frontend response-contract normalization."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from retail_price_evidence import CACHE_MAX_AGE_SECONDS, retailer_host_allowed


API_CONTRACT_VERSION = "issue17-v1"

REFERENCE_METRICS = (
    {"name": "capacity_mah", "unit": "mAh", "direction": "higher_is_better", "section": "battery"},
    {"name": "measured_endurance_hours", "unit": "hours", "direction": "higher_is_better", "section": "battery"},
    {"name": "camera_resolution_mp", "unit": "MP", "direction": "higher_is_better", "section": "camera"},
    {"name": "measured_photo_quality", "unit": "score", "direction": "higher_is_better", "section": "camera"},
    {"name": "cpu_single_core", "unit": "score", "direction": "higher_is_better", "section": "performance"},
    {"name": "cpu_multi_core", "unit": "score", "direction": "higher_is_better", "section": "performance"},
    {"name": "gpu_score", "unit": "score", "direction": "higher_is_better", "section": "gaming"},
    {"name": "gaming_sustained_fps", "unit": "fps", "direction": "higher_is_better", "section": "gaming"},
    {"name": "thermal_rise_c", "unit": "°C", "direction": "lower_is_better", "section": "gaming"},
    {"name": "physical_ram_gb", "unit": "GB", "direction": "higher_is_better", "section": "performance"},
    {"name": "storage_capacity_gb", "unit": "GB", "direction": "higher_is_better", "section": "performance"},
)


def _benchmark_products_from_recommendations(recommendations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Adapt authoritative API recommendations to the existing benchmark input.

    Only an exact, current offer can enter the live lane. Research candidates
    remain visible to the benchmark as unavailable/reference-only data and
    never gain a purchase CTA from this adapter.
    """
    products: list[dict[str, Any]] = []
    for recommendation in recommendations:
        identity = recommendation.get("identity_evidence") or {}
        variant = recommendation.get("physical_variant") or identity.get("variant") or {}
        evidence = (recommendation.get("provenance") or {}).get("price_evidence") or {}
        offer = recommendation.get("best_offer") or {}
        if not isinstance(offer, dict):
            offer = {}
        criteria = (recommendation.get("score_trace") or {}).get("criteria") or []
        fit_signals = {}
        for criterion in criteria:
            if not isinstance(criterion, dict) or not criterion.get("criterion"):
                continue
            fit_signals[criterion["criterion"]] = {
                "match": criterion.get("match_score"),
                "status": criterion.get("evidence_status") or "unknown",
                "reason": criterion.get("reason") or "",
            }
        current = recommendation.get("current_offer_verified") is True
        canonical_id = recommendation.get("canonical_product_id")
        products.append({
            "canonical_product_id": canonical_id,
            "exact_variant_id": recommendation.get("exact_variant_id") or canonical_id,
            "manufacturer": recommendation.get("brand"),
            "brand": recommendation.get("brand"),
            "model": recommendation.get("title"),
            "price": recommendation.get("verified_current_price_inr") if current else None,
            "price_verified": current,
            "offer_status": offer.get("availability") if current else None,
            "price_fresh": current,
            "fit_signals": fit_signals,
            "verified_metrics": recommendation.get("verified_metrics") or {},
            "metric_records": recommendation.get("metric_records") or [],
            "metric_metadata": recommendation.get("metric_metadata") or {},
            "variant": variant,
            "source_lane": "LIVE_VERIFIED_BUYABLE" if current else "RESEARCH_REFERENCE_ONLY",
            "evidence_ids": recommendation.get("evidence_ids") or [],
            "evidence_protocol_versions": recommendation.get("evidence_protocol_versions") or [],
        })
    return products


def _dynamic_reference_contract(payload: dict[str, Any], intent: dict[str, Any], recommendations: list[dict[str, Any]], now: datetime) -> dict[str, Any]:
    """Attach dynamic references without changing the approved ranker."""
    from budget_benchmark import (
        BENCHMARK_VERSION,
        STANDARD_BUDGET_CEILINGS,
        build_budget_benchmark,
        build_budget_reference_snapshots,
    )

    products = payload.get("_benchmark_products")
    if not isinstance(products, list):
        products = _benchmark_products_from_recommendations(recommendations)
    exact_budget = intent.get("budget_max")
    if exact_budget in (None, ""):
        exact_budget = STANDARD_BUDGET_CEILINGS[0]
    evidence_version = str(payload.get("benchmark_evidence_version") or "api-response-evidence-v1")
    generated_at = now.isoformat()
    requested = build_budget_benchmark(
        products,
        {**intent, "budget_max": exact_budget},
        list(REFERENCE_METRICS),
        evidence_version=evidence_version,
        generated_at=generated_at,
    )
    standard = build_budget_reference_snapshots(
        products,
        intent,
        list(REFERENCE_METRICS),
        evidence_version=evidence_version,
        generated_at=generated_at,
    )
    live_eligible = [item for item in requested.get("eligible_products", []) if item.get("source_lane") == "LIVE_VERIFIED_BUYABLE"]
    if requested.get("eligible_products") and len(live_eligible) == len(requested["eligible_products"]):
        status = "LIVE_VERIFIED_BUYABLE"
    elif requested.get("eligible_products"):
        status = "RESEARCH_REFERENCE_ONLY"
    else:
        status = "LIVE_ELIGIBLE_POOL_EMPTY"
    standard_summary = [
        {
            "budget_ceiling_inr": snapshot.get("budget_ceiling_inr"),
            "verification_status": snapshot.get("verification_status"),
            "eligible_variant_ids": snapshot.get("eligible_variant_ids", []),
            "metric_count": len(snapshot.get("metrics", [])),
        }
        for snapshot in standard.get("snapshots", [])
    ]
    return {
        "benchmark_version": BENCHMARK_VERSION,
        "reference_status": status,
        "requested_budget_inr": requested.get("budget_ceiling_inr"),
        "requested_snapshot": requested,
        "standard_budget_snapshots": standard_summary,
        "supported_standard_budgets_inr": list(STANDARD_BUDGET_CEILINGS),
        "supported_exact_budget": True,
        "metric_definitions": list(REFERENCE_METRICS),
        "score_source": "backend_dynamic_reference_adapter",
        "production_scoring_changed": False,
        "live_purchase_ctas_allowed": status == "LIVE_VERIFIED_BUYABLE",
    }


def _text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _utc(value: Any) -> datetime | None:
    text = _text(value)
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _offer_mapping_verified(recommendation: dict[str, Any], canonical_id: str) -> bool:
    for offer in recommendation.get("retailer_offers") or []:
        if not isinstance(offer, dict):
            continue
        if (
            _text(offer.get("product_id")) == canonical_id
            and _text(offer.get("retailer_product_id"))
            and _text(offer.get("retailer"))
        ):
            return True
    return False


def _price_contract(recommendation: dict[str, Any], canonical_id: str, now: datetime) -> dict[str, Any]:
    evidence = ((recommendation.get("provenance") or {}).get("price_evidence") or {})
    observed_at = _text(evidence.get("verified_at"))
    observed = _utc(observed_at)
    expires_at = None
    if observed is not None:
        expires_at = datetime.fromtimestamp(
            observed.timestamp() + CACHE_MAX_AGE_SECONDS,
            timezone.utc,
        ).isoformat()
    try:
        price = float(evidence.get("price"))
    except (TypeError, ValueError):
        price = None
    source_url = _text(evidence.get("source_url"))
    availability = _text(evidence.get("availability")).casefold()
    fresh = bool(
        observed is not None
        and 0 <= (now - observed).total_seconds() <= CACHE_MAX_AGE_SECONDS
    )
    exact_current = bool(
        evidence.get("verified") is True
        and canonical_id
        and price is not None
        and price > 0
        and _text(evidence.get("retailer_product_id"))
        and retailer_host_allowed(source_url)
        and availability == "in_stock"
        and fresh
    )
    if exact_current:
        price_status = "VERIFIED_CURRENT"
    elif observed is not None and (not fresh or availability in {"out_of_stock", "expired"}):
        price_status = "HISTORICAL_OR_EXPIRED"
    else:
        price_status = "CURRENT_OFFER_UNAVAILABLE"
    mapping = _offer_mapping_verified(recommendation, canonical_id)
    return {
        "verified_current_price_inr": price if exact_current else None,
        "price_status": price_status,
        "current_offer_verified": exact_current,
        "retailer_mapping_verified": mapping,
        "offer_observed_at": observed_at or None,
        "offer_expires_at": expires_at,
        "purchase_cta_eligible": bool(exact_current and mapping),
        "cta_state": "VERIFIED_BUYABLE" if exact_current and mapping else "CURRENT_OFFER_UNAVAILABLE",
    }


def _normalize_recommendation(recommendation: dict[str, Any], now: datetime) -> dict[str, Any]:
    result = dict(recommendation)
    canonical_id = _text(result.get("canonical_product_id"))
    identity = result.get("identity_evidence") or {}
    variant = identity.get("variant") if isinstance(identity, dict) else {}
    result["canonical_product_id"] = canonical_id or None
    result["exact_variant_id"] = result.get("exact_variant_id") or None
    result["physical_variant"] = variant if isinstance(variant, dict) else {}
    result["identity_status"] = _text(identity.get("status")) if isinstance(identity, dict) else "unknown"
    result.update(_price_contract(result, canonical_id, now))
    result["has_affiliate_destination"] = bool(_text(result.get("affiliate_url")))
    return result


def apply_response_contract(payload: dict[str, Any], requested_query: str, *, now: datetime | None = None) -> dict[str, Any]:
    """Preserve legacy keys and add explicit Issue 17 contract fields."""
    output = dict(payload)
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    intent = output.get("intent") if isinstance(output.get("intent"), dict) else {}
    recommendations = [
        _normalize_recommendation(item, current)
        for item in output.get("recommendations", [])
        if isinstance(item, dict)
    ]
    output["api_contract_version"] = API_CONTRACT_VERSION
    output["requested_query"] = requested_query
    output["requested_budget_inr"] = intent.get("budget_max")
    output["requested_category"] = intent.get("category")
    output["recommendations"] = recommendations
    existing_categories = output.get("category_results") if isinstance(output.get("category_results"), dict) else {}
    category_results = {
        "overall": {
            "status": output.get("result_status", "PARTIAL"),
            "recommendations": recommendations,
            "result_count": len(recommendations),
        },
    }
    for category in ("camera", "battery", "gaming", "performance"):
        supplied = existing_categories.get(category)
        if isinstance(supplied, dict):
            section = dict(supplied)
            section.setdefault("recommendations", [])
            section.setdefault("result_count", len(section.get("recommendations") or []))
            category_results[category] = section
        else:
            category_results[category] = {
                "status": "CATEGORY_EVIDENCE_UNAVAILABLE",
                "recommendations": [],
                "result_count": 0,
                "reason": f"No verified {category}-specific API result is available for this response.",
            }
    output["category_results"] = category_results
    output["dynamic_reference"] = _dynamic_reference_contract(output, intent, recommendations, current)
    output["optional_stretch"] = {
        "stretch_enabled": False,
        "stretch_status": "DISABLED_OWNER_REVIEW",
        "requested_budget_inr": intent.get("budget_max"),
        "optional_stretch_recommendation": None,
        "suppression_reason": "Issue 16 stretch prototype remains isolated and inactive.",
    }
    output["market_data_status"] = (
        "VERIFIED_CURRENT_RESULTS"
        if any(item.get("current_offer_verified") for item in recommendations)
        else "CURRENT_OFFERS_UNAVAILABLE"
    )
    output["cache_dependencies"] = {
        "requested_budget_inr": intent.get("budget_max"),
        "requested_category": intent.get("category"),
        "query_constraints": intent,
        "candidate_pool_version": output.get("candidate_pool_version"),
        "api_contract_version": API_CONTRACT_VERSION,
        "benchmark_version": output["dynamic_reference"]["benchmark_version"],
        "price_ttl_seconds": CACHE_MAX_AGE_SECONDS,
    }
    cache_payload = {
        "query": requested_query,
        "budget": intent.get("budget_max"),
        "category": intent.get("category"),
        "intent": intent,
        "candidate_pool_version": output.get("candidate_pool_version"),
        "api_contract_version": API_CONTRACT_VERSION,
    }
    output["response_cache_key"] = hashlib.sha256(
        json.dumps(cache_payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return output


__all__ = ["API_CONTRACT_VERSION", "apply_response_contract"]
