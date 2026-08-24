#!/usr/bin/env python3
"""
Coupon World AI OS
Weighted Fit Engine v1.0

Purpose:
- Score a product against Intent Engine v2 priority weights.
- Treat hard constraints separately.
- Keep "fit" separate from evidence coverage/confidence.
- Return only products with fit >= 50% and sufficient evidence.
- Never force a single winner: recommend 3-5 products when available.
"""

from __future__ import annotations

import re

from dataclasses import dataclass, asdict
from typing import Any


MIN_FIT_PERCENT = 50
MIN_EVIDENCE_COVERAGE_PERCENT = 50
DEFAULT_MAX_RESULTS = 5
DEFAULT_MIN_RESULTS = 3


@dataclass
class CriterionResult:
    criterion: str
    weight: int
    match_score: float | None
    weighted_points: float
    evidence_status: str
    reason: str


def _clamp01(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, number))


def _normalize_signal(value: Any) -> tuple[float | None, str, str]:
    """
    Supported signal forms:

    1. Numeric:
       "battery": 0.9

    2. Dict:
       "battery": {
           "match": 0.9,
           "status": "verified",
           "reason": "5000mAh battery and strong endurance"
       }

    Unknown / absent evidence:
       None
       {"match": None, "status": "unknown", "reason": "..."}
    """

    if value is None:
        return None, "unknown", "No reliable evidence available"

    if isinstance(value, (int, float)):
        return _clamp01(value), "available", ""

    if isinstance(value, dict):
        raw_match = value.get("match")
        status = str(value.get("status") or "available").strip().lower()
        reason = str(value.get("reason") or "").strip()

        if raw_match is None:
            return None, status or "unknown", reason or "No reliable evidence available"

        return _clamp01(raw_match), status or "available", reason

    return None, "unknown", "Unsupported evidence format"


def _hard_constraint_failures(product: dict, intent: dict) -> list[str]:
    failures: list[str] = []
    hard_constraints = intent.get("hard_constraints", [])

    if not isinstance(hard_constraints, list):
        hard_constraints = []

    # --------------------------------------------------------
    # Explicit brand semantics
    #
    # intent["brands"] is mention metadata. A mentioned brand is:
    # - avoided when brand_<name> appears in intent["avoid"]
    # - preferred when brand_<name> appears in intent["preferred"]
    # - otherwise required for a brand-scoped query
    #
    # This gate is deliberately generic: Samsung, Apple, OnePlus,
    # Motorola, Redmi etc. all use the same mechanism.
    # --------------------------------------------------------

    def norm_brand(value):
        return re.sub(
            r"[^a-z0-9]+",
            " ",
            str(value or "").lower(),
        ).strip()

    product_brand = norm_brand(product.get("brand"))

    mentioned_brands = [
        norm_brand(x)
        for x in intent.get("brands", [])
        if norm_brand(x)
    ]

    avoid_markers = {
        norm_brand(x).replace(" ", "_")
        for x in intent.get("avoid", [])
        if norm_brand(x)
    }

    preferred_markers = {
        norm_brand(x).replace(" ", "_")
        for x in intent.get("preferred", [])
        if norm_brand(x)
    }

    must_markers = {
        norm_brand(x).replace(" ", "_")
        for x in intent.get("must_have", [])
        if norm_brand(x)
    }

    for mentioned_brand in mentioned_brands:
        marker = f"brand_{mentioned_brand}".replace(" ", "_")

        if marker in avoid_markers:
            if product_brand == mentioned_brand:
                failures.append(
                    f"Excluded brand matched: {mentioned_brand}"
                )
            continue

        if marker in preferred_markers:
            continue

        # Explicit must-have brand OR ordinary brand-scoped query.
        if (
            marker in must_markers
            or marker not in preferred_markers
        ):
            if product_brand and product_brand != mentioned_brand:
                failures.append(
                    f"Required brand not matched: "
                    f"{mentioned_brand} required, got {product_brand}"
                )

    if "budget_max" in hard_constraints:
        budget_max = intent.get("budget_max")
        price = product.get("price")

        if budget_max not in (None, ""):
            if price in (None, ""):
                failures.append(
                    f"Hard budget cannot be verified because current price is unavailable "
                    f"(budget limit {budget_max})"
                )
            else:
                try:
                    if float(price) > float(budget_max):
                        failures.append(
                            f"Price {price} exceeds hard budget limit {budget_max}"
                        )
                except (TypeError, ValueError):
                    failures.append(
                        "Hard budget cannot be verified because product price is invalid"
                    )

    if "budget_min" in hard_constraints:
        budget_min = intent.get("budget_min")
        price = product.get("price")

        if budget_min not in (None, "") and price not in (None, ""):
            try:
                if float(price) < float(budget_min):
                    failures.append(
                        f"Price {price} is below minimum budget requirement {budget_min}"
                    )
            except (TypeError, ValueError):
                pass

    # Optional explicit hard requirement map on the product.
    requirement_status = product.get("hard_requirement_status", {})
    if isinstance(requirement_status, dict):
        for requirement in intent.get("must_have", []) or []:
            status = requirement_status.get(requirement)

            if status is False:
                failures.append(f"Must-have requirement not met: {requirement}")

    return failures


def calculate_product_fit(product: dict, intent: dict) -> dict:
    weights = intent.get("priority_weights", {})
    if not isinstance(weights, dict) or not weights:
        return {
            "eligible": False,
            "fit_percent": 0,
            "raw_fit_percent": 0,
            "evidence_coverage_percent": 0,
            "recommendation_confidence": "low",
            "hard_constraint_failures": ["No priority weights available"],
            "criteria": [],
            "matched_requirements": [],
            "partial_requirements": [],
            "unknown_requirements": [],
            "weak_requirements": [],
        }

    hard_failures = _hard_constraint_failures(product, intent)

    signals = product.get("fit_signals", {})
    if not isinstance(signals, dict):
        signals = {}

    # ------------------------------------------------------------
    # Signal-backed must-have gate
    #
    # A user-explicit must-have must be positively verified before
    # the product can become a recommendation.
    #
    # UNKNOWN is not treated as failure of the product itself, but it
    # is insufficient evidence for a must-have recommendation.
    # ------------------------------------------------------------
    must_have = intent.get("must_have", [])

    if not isinstance(must_have, list):
        must_have = []

    for requirement in must_have:
        requirement_key = str(requirement or "").strip()

        # Only apply this generic gate when the requirement maps
        # directly to an existing fit signal. Other requirement types
        # continue to use their existing dedicated handling.
        if not requirement_key or requirement_key not in signals:
            continue

        match, evidence_status, reason = _normalize_signal(
            signals.get(requirement_key)
        )

        if match is None:
            hard_failures.append(
                "Must-have requirement is not verified: "
                f"{requirement_key}"
                + (f" ({reason})" if reason else "")
            )
            continue

        if match < 0.50:
            hard_failures.append(
                "Must-have requirement not met: "
                f"{requirement_key}"
                + (f" ({reason})" if reason else "")
            )

    criteria: list[CriterionResult] = []

    total_weight = sum(max(0, int(v)) for v in weights.values()) or 100
    known_weight = 0
    known_weighted_points = 0.0

    matched: list[str] = []
    partial: list[str] = []
    unknown: list[str] = []
    weak: list[str] = []

    for criterion, raw_weight in weights.items():
        weight = max(0, int(raw_weight))
        match, evidence_status, reason = _normalize_signal(signals.get(criterion))

        if match is None:
            weighted_points = 0.0
            unknown.append(criterion)
        else:
            known_weight += weight
            weighted_points = weight * match
            known_weighted_points += weighted_points

            if match >= 0.80:
                matched.append(criterion)
            elif match >= 0.50:
                partial.append(criterion)
            else:
                weak.append(criterion)

        criteria.append(
            CriterionResult(
                criterion=criterion,
                weight=weight,
                match_score=match,
                weighted_points=round(weighted_points, 2),
                evidence_status=evidence_status,
                reason=reason,
            )
        )

    # How well the product matches on dimensions for which evidence exists.
    raw_fit_percent = (
        round((known_weighted_points / known_weight) * 100)
        if known_weight > 0
        else 0
    )

    # How much of the user's weighted requirement space is actually evidenced.
    evidence_coverage_percent = round((known_weight / total_weight) * 100)

    # Conservative final fit:
    # good matching with poor evidence cannot become an artificially high score.
    fit_percent = round(
        raw_fit_percent * (evidence_coverage_percent / 100)
    )

    if evidence_coverage_percent >= 80:
        confidence = "high"
    elif evidence_coverage_percent >= 60:
        confidence = "medium"
    else:
        confidence = "low"

    eligible = (
        not hard_failures
        and fit_percent >= MIN_FIT_PERCENT
        and evidence_coverage_percent >= MIN_EVIDENCE_COVERAGE_PERCENT
    )

    return {
        "eligible": eligible,
        "fit_percent": fit_percent,
        "raw_fit_percent": raw_fit_percent,
        "evidence_coverage_percent": evidence_coverage_percent,
        "recommendation_confidence": confidence,
        "hard_constraint_failures": hard_failures,
        "criteria": [asdict(item) for item in criteria],
        "matched_requirements": matched,
        "partial_requirements": partial,
        "unknown_requirements": unknown,
        "weak_requirements": weak,
    }


def rank_recommendations(
    products: list[dict],
    intent: dict,
    max_results: int = DEFAULT_MAX_RESULTS,
    min_results: int = DEFAULT_MIN_RESULTS,
) -> dict:
    scored: list[dict] = []

    for product in products:
        result = calculate_product_fit(product, intent)

        item = product.copy()
        item["fit_assessment"] = result

        if result["eligible"]:
            scored.append(item)

    scored.sort(
        key=lambda item: (
            item["fit_assessment"]["fit_percent"],
            item["fit_assessment"]["evidence_coverage_percent"],
        ),
        reverse=True,
    )

    recommendations = scored[:max(1, int(max_results))]

    return {
        "recommendation_count": len(recommendations),
        "minimum_preferred_count": min_results,
        "maximum_result_count": max_results,
        "threshold_percent": MIN_FIT_PERCENT,
        "has_preferred_minimum": len(recommendations) >= min_results,
        "recommendations": recommendations,
        "message": (
            f"{len(recommendations)} qualifying product(s) found"
            if recommendations
            else "No product met the 50% fit and evidence threshold"
        ),
    }


if __name__ == "__main__":
    # Small self-test using a parent-phone profile.
    intent = {
        "budget_max": 25000,
        "hard_constraints": ["budget_max"],
        "must_have": [],
        "priority_weights": {
            "budget": 17,
            "battery": 26,
            "display": 22,
            "ease_of_use": 22,
            "camera": 4,
            "performance": 4,
            "software_support": 4,
            "connectivity": 1,
        },
    }

    products = [
        {
            "title": "Sample Phone A",
            "price": 23999,
            "fit_signals": {
                "budget": {"match": 1.0, "status": "verified", "reason": "Within budget"},
                "battery": {"match": 0.95, "status": "verified", "reason": "Strong battery"},
                "display": {"match": 0.90, "status": "verified", "reason": "Large bright display"},
                "ease_of_use": {"match": 0.85, "status": "assessed", "reason": "Simple daily-use profile"},
                "camera": {"match": 0.60, "status": "verified", "reason": "Adequate camera"},
                "performance": {"match": 0.70, "status": "verified", "reason": "Good general performance"},
                "software_support": {"match": 0.80, "status": "verified", "reason": "Good support"},
                "connectivity": {"match": 1.0, "status": "verified", "reason": "Modern connectivity"},
            },
        },
        {
            "title": "Sample Phone B",
            "price": 21999,
            "fit_signals": {
                "budget": 1.0,
                "battery": 0.80,
                "display": 0.75,
                "ease_of_use": 0.70,
                "camera": 0.90,
                "performance": 0.80,
                "software_support": 0.60,
                "connectivity": 1.0,
            },
        },
        {
            "title": "Sample Phone C",
            "price": 29999,
            "fit_signals": {
                "budget": 0.0,
                "battery": 1.0,
                "display": 1.0,
                "ease_of_use": 0.9,
            },
        },
    ]

    ranked = rank_recommendations(products, intent)

    print("=" * 72)
    print("COUPON WORLD WEIGHTED FIT ENGINE v1.0")
    print("=" * 72)

    for position, item in enumerate(ranked["recommendations"], start=1):
        assessment = item["fit_assessment"]
        print(
            position,
            "|",
            item["title"],
            "| FIT:",
            f'{assessment["fit_percent"]}%',
            "| COVERAGE:",
            f'{assessment["evidence_coverage_percent"]}%',
        )
