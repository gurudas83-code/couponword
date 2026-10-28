"""Issue 15 shared hard-eligible candidate-pool adapter.

This module is deliberately a boundary adapter.  It owns only the common
shopping gates (identity, exact variant, budget, retailer authorization,
freshness and stock).  Existing scoring engines remain responsible for fit
and specialist quality scores supplied on each candidate.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from product_evidence_store import variant_signature_from_text
from weighted_fit_engine import MIN_FIT_PERCENT, MIN_EVIDENCE_COVERAGE_PERCENT, recommendation_sort_key


POOL_VERSION = "issue15-shared-pool-v1"
FRESHNESS_TTL_SECONDS = 6 * 60 * 60
CATEGORIES = ("overall", "camera", "battery", "gaming")


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


def _variant(candidate: dict[str, Any]) -> dict[str, str]:
    declared = candidate.get("variant")
    if isinstance(declared, dict):
        result = {
            key: _text(declared.get(key))
            for key in ("ram_gb", "storage_gb")
            if _text(declared.get(key))
        }
        if result:
            return result
    return variant_signature_from_text(
        candidate.get("title"),
        candidate.get("model"),
        f"{candidate.get('ram_gb', '')}GB RAM {candidate.get('storage_gb', '')}GB storage",
    )


def _offer_id(offer: dict[str, Any], index: int) -> str:
    return _text(offer.get("offer_id")) or ":".join(
        _text(offer.get(key)) for key in ("retailer", "retailer_product_id")
    ) or f"offer-{index}"


def _query_variant(constraints: dict[str, Any]) -> dict[str, str]:
    return {
        key: _text(constraints.get(key))
        for key in ("ram_gb", "storage_gb")
        if _text(constraints.get(key))
    }


def _variant_matches(candidate_variant: dict[str, str], expected: dict[str, str]) -> bool:
    return all(candidate_variant.get(key) == value for key, value in expected.items())


def _offer_is_eligible(
    candidate: dict[str, Any],
    offer: dict[str, Any],
    constraints: dict[str, Any],
    now: datetime,
) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    if offer.get("source_authorized") is not True:
        blockers.append("UNAUTHORIZED_RETAILER_SOURCE")
    if not _text(offer.get("retailer_product_id")):
        blockers.append("MISSING_RETAILER_PRODUCT_ID")
    if not _text(offer.get("product_id")) or offer.get("product_id") != candidate.get("canonical_product_id"):
        blockers.append("CANONICAL_PRODUCT_ID_MISMATCH")
    candidate_variant = _variant(candidate)
    offer_variant = variant_signature_from_text(offer.get("variant"), offer.get("title"))
    if not _variant_matches(offer_variant, candidate_variant) or not _variant_matches(candidate_variant, offer_variant):
        blockers.append("EXACT_VARIANT_MISMATCH")
    try:
        price = float(offer.get("price"))
    except (TypeError, ValueError):
        price = None
    if price is None or price <= 0:
        blockers.append("INVALID_CURRENT_PRICE")
    budget = constraints.get("budget_max")
    if budget not in (None, "") and price is not None:
        try:
            if price > float(budget):
                blockers.append("STRICT_BUDGET_EXCEEDED")
        except (TypeError, ValueError):
            blockers.append("INVALID_BUDGET")
    observed = _utc(offer.get("observed_at"))
    if observed is None:
        blockers.append("MISSING_OBSERVATION_TIMESTAMP")
    else:
        age = (now - observed).total_seconds()
        if age < 0 or age > FRESHNESS_TTL_SECONDS:
            blockers.append("OFFER_EXPIRED")
    if _text(offer.get("availability")).casefold() != "in_stock":
        blockers.append("STOCK_NOT_VERIFIED_IN_STOCK")
    return not blockers, blockers


def _candidate_blockers(candidate: dict[str, Any], constraints: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not _text(candidate.get("canonical_product_id")):
        blockers.append("MISSING_CANONICAL_PRODUCT_ID")
    if not _text(candidate.get("brand")) or not _text(candidate.get("model")):
        blockers.append("INCOMPLETE_PRODUCT_IDENTITY")
    if candidate.get("identity_conflict") is True:
        blockers.append("UNRESOLVED_MODEL_VARIANT_CONFLICT")
    brands = {_text(value).casefold() for value in constraints.get("brands", []) or []}
    if brands and _text(candidate.get("brand")).casefold() not in brands:
        blockers.append("EXPLICIT_BRAND_CONSTRAINT_MISMATCH")
    expected_variant = _query_variant(constraints)
    if expected_variant and not _variant_matches(_variant(candidate), expected_variant):
        blockers.append("REQUESTED_PHYSICAL_VARIANT_MISMATCH")
    return blockers


def _version(query_id: str, constraints: dict[str, Any], candidates: list[dict[str, Any]], evidence_version: str) -> str:
    payload = {
        "base": POOL_VERSION,
        "query_id": query_id,
        "constraints": constraints,
        "evidence_version": evidence_version,
        "eligible": [
            {
                "canonical_product_id": item["canonical_product_id"],
                "offer_ids": [offer["offer_id"] for offer in item["eligible_offers"]],
            }
            for item in candidates
        ],
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
    return f"{POOL_VERSION}:{digest}"


def build_shared_candidate_pool(
    *,
    query_id: str,
    budget_max: int | float | None,
    candidates: Iterable[dict[str, Any]],
    constraints: dict[str, Any] | None = None,
    evidence_version: str = "unknown",
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build one authoritative hard-eligible pool from exact candidate records."""
    current = _now(now)
    query_constraints = dict(constraints or {})
    query_constraints.setdefault("budget_max", budget_max)
    eligible: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    for candidate in candidates:
        row = dict(candidate)
        blockers = _candidate_blockers(row, query_constraints)
        valid_offers: list[dict[str, Any]] = []
        offer_blockers: dict[str, list[str]] = {}
        for index, raw_offer in enumerate(row.get("offers") or []):
            offer = dict(raw_offer)
            offer_key = _offer_id(offer, index)
            offer["offer_id"] = offer_key
            ok, reasons = _offer_is_eligible(row, offer, query_constraints, current)
            if ok:
                valid_offers.append(offer)
            else:
                offer_blockers[offer_key] = reasons
        if not valid_offers:
            blockers = blockers + ["NO_CURRENT_VERIFIED_OFFER"]
        if blockers:
            diagnostics.append({
                "canonical_product_id": _text(row.get("canonical_product_id")),
                "hard_eligibility_status": "HARD_INELIGIBLE",
                "hard_eligibility_blockers": sorted(set(blockers)),
                "offer_blockers": offer_blockers,
            })
            continue
        valid_offers.sort(key=lambda offer: (float(offer.get("price")), _text(offer.get("retailer")), offer["offer_id"]))
        selected = dict(row)
        selected["eligible_offers"] = valid_offers
        selected["selected_offer"] = valid_offers[0]
        selected["hard_eligibility_status"] = "HARD_ELIGIBLE"
        selected["hard_eligibility_blockers"] = []
        selected["offer_ids"] = [offer["offer_id"] for offer in valid_offers]
        selected["offer_observed_at"] = valid_offers[0].get("observed_at")
        selected["offer_expires_at"] = (
            _utc(valid_offers[0].get("observed_at")) + timedelta(seconds=FRESHNESS_TTL_SECONDS)
        ).isoformat()
        eligible.append(selected)
    eligible.sort(key=lambda item: _text(item.get("canonical_product_id")))
    version = _version(query_id, query_constraints, eligible, evidence_version)
    return {
        "query_id": query_id,
        "query_budget_inr": budget_max,
        "query_constraints": query_constraints,
        "candidate_pool_version": version,
        "candidate_pool_generated_at": current.isoformat(),
        "candidate_pool_evidence_version": evidence_version,
        "eligible_canonical_variant_ids": [item["canonical_product_id"] for item in eligible],
        "eligible_offer_ids": [offer_id for item in eligible for offer_id in item["offer_ids"]],
        "hard_eligibility_status": "HARD_ELIGIBLE_POOL_READY" if eligible else "NO_HARD_ELIGIBLE_CANDIDATES",
        "candidates": eligible,
        "rejected_candidates": diagnostics,
        "cache_key": f"{query_id}:{version}",
    }


def _quality_status(candidate: dict[str, Any], category: str) -> tuple[str, float | None, str]:
    if category == "overall":
        assessment = candidate.get("overall_fit_assessment") or {}
        if assessment.get("eligible") is not True:
            return "CATEGORY_EVIDENCE_INSUFFICIENT", None, "Overall approved fit assessment is not eligible"
        return "SUPPORTED", float(assessment.get("quality_score") or assessment.get("fit_percent") or 0), "Existing overall scorer"
    evidence = candidate.get(f"{category}_evidence") or {}
    if evidence.get("sufficient") is not True:
        return "CATEGORY_EVIDENCE_INSUFFICIENT", None, _text(evidence.get("reason")) or "Comparable category evidence is unavailable"
    score = evidence.get("score")
    try:
        return "SUPPORTED", float(score), "Existing specialist scorer supplied category evidence"
    except (TypeError, ValueError):
        return "CATEGORY_EVIDENCE_INSUFFICIENT", None, "Category evidence has no approved score"


def rank_shared_pool_categories(pool: dict[str, Any], max_results: int = 3) -> dict[str, Any]:
    """Rank only members of the same hard-eligible pool for all four sections."""
    version = _text(pool.get("candidate_pool_version"))
    results: dict[str, Any] = {}
    for category in CATEGORIES:
        supported: list[tuple[float, str, dict[str, Any]]] = []
        shortages: list[dict[str, Any]] = []
        for candidate in pool.get("candidates") or []:
            status, score, reason = _quality_status(candidate, category)
            if status != "SUPPORTED":
                shortages.append({"canonical_product_id": candidate.get("canonical_product_id"), "status": status, "reason": reason})
                continue
            supported.append((score or 0.0, _text(candidate.get("canonical_product_id")), candidate))
        supported.sort(key=lambda item: (-item[0], item[1]))
        results[category] = {
            "candidate_pool_version": version,
            "results": [
                {"rank": index, "canonical_product_id": item[2]["canonical_product_id"], "score": item[0], "offer_ids": item[2]["offer_ids"]}
                for index, item in enumerate(supported[:max_results], start=1)
            ],
            "category_evidence_shortages": shortages,
            "result_count": min(len(supported), max_results),
        }
    return results


def validate_category_results(pool: dict[str, Any], results: dict[str, Any]) -> list[str]:
    """Return invariant failures; an empty list is a shared-pool consistency pass."""
    errors: list[str] = []
    pool_ids = set(pool.get("eligible_canonical_variant_ids") or [])
    version = _text(pool.get("candidate_pool_version"))
    for category in CATEGORIES:
        section = results.get(category) or {}
        if section.get("candidate_pool_version") != version:
            errors.append(f"{category}: candidate-pool version mismatch")
        seen: set[str] = set()
        for result in section.get("results") or []:
            pid = _text(result.get("canonical_product_id"))
            if pid not in pool_ids:
                errors.append(f"{category}: result reintroduced hard-ineligible candidate {pid}")
            if pid in seen:
                errors.append(f"{category}: duplicate canonical variant {pid}")
            seen.add(pid)
    return errors


def invalidate_if_stale(pool: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    current = _now(now)
    stale: list[str] = []
    for candidate in pool.get("candidates") or []:
        expires = _utc(candidate.get("offer_expires_at"))
        if expires is None or current >= expires:
            stale.append(_text(candidate.get("canonical_product_id")))
    result = dict(pool)
    result["cache_valid"] = not stale
    result["stale_canonical_variant_ids"] = stale
    if stale:
        result["hard_eligibility_status"] = "POOL_INVALIDATED_OFFER_EXPIRED"
    return result


__all__ = [
    "CATEGORIES",
    "FRESHNESS_TTL_SECONDS",
    "MIN_FIT_PERCENT",
    "MIN_EVIDENCE_COVERAGE_PERCENT",
    "build_shared_candidate_pool",
    "invalidate_if_stale",
    "rank_shared_pool_categories",
    "validate_category_results",
]
