"""Additive Issue 17 API/frontend response-contract normalization."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from retail_price_evidence import CACHE_MAX_AGE_SECONDS, retailer_host_allowed


API_CONTRACT_VERSION = "issue17-v1"


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
    output["category_results"] = {
        "overall": {
            "status": output.get("result_status", "PARTIAL"),
            "recommendations": recommendations,
            "result_count": len(recommendations),
        },
        "camera": {
            "status": "CATEGORY_EVIDENCE_UNAVAILABLE",
            "recommendations": [],
            "result_count": 0,
            "reason": "No active camera-specific API result assembler exists at this HEAD.",
        },
        "battery": {
            "status": "CATEGORY_EVIDENCE_UNAVAILABLE",
            "recommendations": [],
            "result_count": 0,
            "reason": "No active battery-specific API result assembler exists at this HEAD.",
        },
        "gaming": {
            "status": "CATEGORY_EVIDENCE_UNAVAILABLE",
            "recommendations": [],
            "result_count": 0,
            "reason": "No active gaming-specific API result assembler exists at this HEAD.",
        },
    }
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
