"""Issue 16 owner-reviewable optional stretch-budget adapter.

The adapter consumes a strict Issue 15-style pool and evaluates at most one
separate, opt-in stretch suggestion.  It does not rank strict results and it
does not alter the approved weighted scoring engine.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from product_evidence_store import variant_signature_from_text


STRETCH_POLICY_VERSION = "issue16-owner-review-v1"
DEFAULT_MAX_ADDITIONAL_INR = 5000
FRESHNESS_TTL_SECONDS = 6 * 60 * 60


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


def _now(value: datetime | None) -> datetime:
    return (value or datetime.now(timezone.utc)).astimezone(timezone.utc)


def stretch_opt_out(user_text: str) -> bool:
    text = _text(user_text).casefold()
    return bool(re.search(
        r"(?:strictly|absolute|max(?:imum)?)\s+(?:under|budget|limit)\s*(?:₹|rs\.?|inr)?\s*[\d,]+"
        r"|cannot\s+spend\s+more|can't\s+spend\s+more|no\s+higher[- ]budget"
        r"|no\s+stretch|do\s+not\s+increase\s+(?:the\s+)?budget|don't\s+increase\s+(?:the\s+)?budget",
        text,
    ))


def _variant(candidate: dict[str, Any]) -> dict[str, str]:
    value = candidate.get("variant")
    if isinstance(value, dict):
        return {key: _text(value.get(key)) for key in ("ram_gb", "storage_gb") if _text(value.get(key))}
    parsed = variant_signature_from_text(candidate.get("variant"), candidate.get("title"))
    if parsed:
        return parsed
    return {key: _text(candidate.get(key)) for key in ("ram_gb", "storage_gb") if _text(candidate.get(key))}


def _variant_matches(left: dict[str, str], right: dict[str, str]) -> bool:
    return bool(left) and bool(right) and left == right


def _offer_is_valid(
    candidate: dict[str, Any],
    offer: dict[str, Any],
    budget: float,
    upper_bound: float,
    now: datetime,
) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    if candidate.get("identity_conflict") is True:
        blockers.append("UNRESOLVED_MAPPING_CONFLICT")
    if not _text(candidate.get("canonical_product_id")):
        blockers.append("MISSING_CANONICAL_PRODUCT_ID")
    if offer.get("source_authorized") is not True:
        blockers.append("UNAUTHORIZED_RETAILER_SOURCE")
    if not _text(offer.get("retailer_product_id")):
        blockers.append("MISSING_RETAILER_PRODUCT_ID")
    if offer.get("product_id") != candidate.get("canonical_product_id"):
        blockers.append("CANONICAL_PRODUCT_ID_MISMATCH")
    if not _variant_matches(_variant(candidate), _variant({"variant": offer.get("variant")})):
        blockers.append("EXACT_VARIANT_MISMATCH")
    try:
        price = float(offer.get("price"))
    except (TypeError, ValueError):
        price = None
    if price is None or price <= 0:
        blockers.append("INVALID_CURRENT_PRICE")
    elif price <= budget:
        blockers.append("NOT_ABOVE_REQUESTED_BUDGET")
    elif price > upper_bound:
        blockers.append("EXCEEDS_STRETCH_CEILING")
    if _text(offer.get("currency")).upper() != "INR":
        blockers.append("NON_INR_PRICE")
    if _text(offer.get("availability")).casefold() != "in_stock":
        blockers.append("STOCK_NOT_VERIFIED_IN_STOCK")
    observed = _utc(offer.get("observed_at"))
    if observed is None:
        blockers.append("MISSING_OBSERVATION_TIMESTAMP")
    else:
        age = (now - observed).total_seconds()
        if age < 0 or age > FRESHNESS_TTL_SECONDS:
            blockers.append("OFFER_EXPIRED")
    hard_blockers = candidate.get("nonbudget_hard_blockers") or []
    blockers.extend(str(item) for item in hard_blockers)
    return not blockers, sorted(set(blockers))


def _improvement_is_credible(candidate: dict[str, Any], category: str) -> tuple[bool, list[dict[str, Any]], str]:
    improvements = candidate.get("verified_improvements") or []
    if not isinstance(improvements, list):
        return False, [], "INSUFFICIENT_BENEFIT_EVIDENCE"
    accepted: list[dict[str, Any]] = []
    for item in improvements:
        if not isinstance(item, dict) or item.get("verified") is not True:
            continue
        if item.get("category") not in {category, "overall", "display", "software", "storage"}:
            continue
        kind = _text(item.get("evidence_kind")).casefold()
        if category == "camera" and kind in {"megapixels", "camera_hardware_only"}:
            continue
        if category == "battery" and kind in {"capacity_only", "mah_only", "standby_only"}:
            continue
        if category == "gaming" and kind in {"ram_only", "chipset_name_only"}:
            continue
        if not _text(item.get("statement")) or not _text(item.get("source_evidence")):
            continue
        accepted.append(item)
    if not accepted:
        return False, [], "NO_MEANINGFUL_VERIFIED_STRETCH"
    return True, accepted, "VERIFIED_MEANINGFUL_BENEFIT"


def _score_comparable(candidate: dict[str, Any], baseline: dict[str, Any]) -> tuple[bool, float | None, float | None, str]:
    candidate_version = _text(candidate.get("score_version"))
    baseline_version = _text(baseline.get("score_version"))
    candidate_scale = _text(candidate.get("score_scale"))
    baseline_scale = _text(baseline.get("score_scale"))
    if not candidate_version or candidate_version != baseline_version or not candidate_scale or candidate_scale != baseline_scale:
        return False, None, None, "INCOMPARABLE_SCORE_REFERENCE"
    try:
        candidate_score = float(candidate.get("comparison_score"))
        baseline_score = float(baseline.get("comparison_score"))
    except (TypeError, ValueError):
        return False, None, None, "INSUFFICIENT_BENEFIT_EVIDENCE"
    if candidate_score <= baseline_score:
        return False, candidate_score, baseline_score, "NO_MEANINGFUL_VERIFIED_STRETCH"
    return True, candidate_score, baseline_score, "VERIFIED_MEANINGFUL_BENEFIT"


def _cache_key(budget: float, intent: dict[str, Any], pool_version: str, evidence_version: str, scoring_version: str) -> str:
    payload = {
        "policy": STRETCH_POLICY_VERSION,
        "budget": budget,
        "intent": intent,
        "pool_version": pool_version,
        "evidence_version": evidence_version,
        "scoring_version": scoring_version,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def evaluate_optional_stretch(
    *,
    user_budget_inr: int | float,
    user_text: str,
    intent: dict[str, Any],
    strict_pool: dict[str, Any],
    stretch_candidates: Iterable[dict[str, Any]],
    enabled: bool = False,
    max_additional_inr: int | float = DEFAULT_MAX_ADDITIONAL_INR,
    evidence_version: str = "unknown",
    scoring_version: str = "unknown",
    category: str = "overall",
    now: datetime | None = None,
) -> dict[str, Any]:
    """Return an owner-reviewable optional suggestion, never a strict result."""
    budget = float(user_budget_inr)
    allowance = float(max_additional_inr)
    current = _now(now)
    strict_ids = {_text(item.get("canonical_product_id")) for item in strict_pool.get("candidates") or []}
    pool_version = _text(strict_pool.get("candidate_pool_version"))
    result: dict[str, Any] = {
        "requested_budget_inr": budget,
        "stretch_policy_version": STRETCH_POLICY_VERSION,
        "stretch_enabled": bool(enabled),
        "stretch_max_additional_inr": allowance,
        "strict_pool_version": pool_version,
        "strict_recommendations": list(strict_pool.get("strict_recommendations") or []),
        "optional_stretch_recommendation": None,
        "stretch_status": "DISABLED_OWNER_REVIEW" if not enabled else "NO_MEANINGFUL_VERIFIED_STRETCH",
        "cache_key": _cache_key(budget, intent, pool_version, evidence_version, scoring_version),
        "suppression_reasons": [],
    }
    if not enabled:
        result["suppression_reasons"].append("STRETCH_DISABLED_PENDING_OWNER_APPROVAL")
        return result
    if stretch_opt_out(user_text):
        result["stretch_status"] = "USER_OPTED_OUT"
        result["suppression_reasons"].append("EXPLICIT_HARD_BUDGET_OR_NO_STRETCH_INSTRUCTION")
        return result
    if allowance < 0:
        result["stretch_status"] = "INVALID_STRETCH_POLICY"
        result["suppression_reasons"].append("NEGATIVE_STRETCH_ALLOWANCE")
        return result

    baseline_candidates = [item for item in strict_pool.get("candidates") or [] if item.get("category") in (None, category)]
    baseline_candidates = [item for item in baseline_candidates if _text(item.get("canonical_product_id"))]
    if not baseline_candidates:
        result["stretch_status"] = "NO_STRICT_COMPARISON_BASELINE"
        result["suppression_reasons"].append("NO_STRICT_COMPARISON_BASELINE")
        return result
    baseline = max(baseline_candidates, key=lambda item: (float(item.get("comparison_score") or -1), _text(item.get("canonical_product_id"))))

    evaluated: list[dict[str, Any]] = []
    for candidate in stretch_candidates:
        candidate = dict(candidate)
        candidate_id = _text(candidate.get("canonical_product_id"))
        if not candidate_id or candidate_id in strict_ids:
            continue
        valid_offers: list[dict[str, Any]] = []
        blockers: dict[str, list[str]] = {}
        upper_bound = budget + allowance
        for index, raw_offer in enumerate(candidate.get("offers") or []):
            offer = dict(raw_offer)
            offer_id = _text(offer.get("offer_id")) or f"{candidate_id}-offer-{index}"
            offer["offer_id"] = offer_id
            valid, reasons = _offer_is_valid(candidate, offer, budget, upper_bound, current)
            if valid:
                valid_offers.append(offer)
            else:
                blockers[offer_id] = reasons
        if not valid_offers:
            result["suppression_reasons"].append({"canonical_product_id": candidate_id, "reason": "NO_VALID_STRETCH_OFFER", "offer_blockers": blockers})
            continue
        valid_offers.sort(key=lambda item: (float(item["price"]), _text(item.get("retailer")), item["offer_id"]))
        credible, improvements, benefit_status = _improvement_is_credible(candidate, category)
        comparable, candidate_score, baseline_score, score_status = _score_comparable(candidate, baseline)
        if not credible or not comparable:
            result["suppression_reasons"].append({"canonical_product_id": candidate_id, "reason": benefit_status if not credible else score_status})
            continue
        selected_offer = valid_offers[0]
        price = float(selected_offer["price"])
        observed = _utc(selected_offer.get("observed_at"))
        evaluated.append({
            "candidate": candidate,
            "offer": selected_offer,
            "score": candidate_score,
            "baseline_score": baseline_score,
            "improvements": improvements,
            "price": price,
            "extra_above_budget_inr": price - budget,
            "extra_vs_comparison_inr": price - float(baseline.get("verified_price_inr")),
            "observed_at": observed.isoformat() if observed else None,
            "expires_at": (observed + timedelta(seconds=FRESHNESS_TTL_SECONDS)).isoformat() if observed else None,
        })
    if not evaluated:
        result["stretch_status"] = "NO_MEANINGFUL_VERIFIED_STRETCH"
        return result
    evaluated.sort(key=lambda row: (-float(row["score"]), row["extra_above_budget_inr"], _text(row["candidate"].get("canonical_product_id"))))
    chosen = evaluated[0]
    candidate = chosen["candidate"]
    result["optional_stretch_recommendation"] = {
        "stretch_canonical_product_id": candidate.get("canonical_product_id"),
        "stretch_exact_variant_id": candidate.get("exact_variant_id") or candidate.get("canonical_product_id"),
        "stretch_verified_price_inr": chosen["price"],
        "extra_above_budget_inr": chosen["extra_above_budget_inr"],
        "comparison_product_id": baseline.get("canonical_product_id"),
        "comparison_verified_price_inr": baseline.get("verified_price_inr"),
        "extra_vs_comparison_inr": chosen["extra_vs_comparison_inr"],
        "verified_improvements": chosen["improvements"],
        "trade_offs": list(candidate.get("trade_offs") or []),
        "source_evidence": candidate.get("source_evidence") or [],
        "evidence_confidence": candidate.get("evidence_confidence") or "unknown",
        "offer_id": chosen["offer"].get("offer_id"),
        "offer_observed_at": chosen["observed_at"],
        "offer_expires_at": chosen["expires_at"],
        "why_consider": candidate.get("why_consider") or "Verified benefit over the selected strict-budget baseline.",
        "why_not_consider": candidate.get("why_not_consider") or "Costs more and remains optional; strict results are unchanged.",
        "comparison_score": chosen["score"],
        "baseline_score": chosen["baseline_score"],
    }
    result["stretch_status"] = "OPTIONAL_STRETCH_VERIFIED"
    return result


def invalidate_stretch_result(result: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    current = _now(now)
    output = dict(result)
    recommendation = output.get("optional_stretch_recommendation")
    expires = _utc(recommendation.get("offer_expires_at")) if isinstance(recommendation, dict) else None
    if expires is None or current >= expires:
        output["optional_stretch_recommendation"] = None
        output["stretch_status"] = "STRETCH_OFFER_EXPIRED"
    return output


__all__ = [
    "DEFAULT_MAX_ADDITIONAL_INR",
    "FRESHNESS_TTL_SECONDS",
    "STRETCH_POLICY_VERSION",
    "evaluate_optional_stretch",
    "invalidate_stretch_result",
    "stretch_opt_out",
]
