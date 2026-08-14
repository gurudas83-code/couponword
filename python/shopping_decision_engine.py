#!/usr/bin/env python3
"""
Coupon World AI OS
Shopping Decision Engine v1.0

Connects:
Intent Engine v2 -> Weighted Fit Engine -> Top 3-5 recommendation policy.

This module does NOT discover products from the web.
It accepts candidate products from any source and ranks them neutrally.
"""

from __future__ import annotations

from typing import Any

from intent_engine import parse_query
from weighted_fit_engine import rank_recommendations


def decide(
    query: str,
    candidates: list[dict[str, Any]],
    max_results: int = 5,
    min_results: int = 3,
) -> dict[str, Any]:
    intent = parse_query(query)

    ranking = rank_recommendations(
        products=candidates,
        intent=intent,
        max_results=max_results,
        min_results=min_results,
    )

    return {
        "query": query,
        "intent": intent,
        "threshold_percent": ranking["threshold_percent"],
        "recommendation_count": ranking["recommendation_count"],
        "has_preferred_minimum": ranking["has_preferred_minimum"],
        "recommendations": ranking["recommendations"],
        "message": ranking["message"],
    }


def print_decision(result: dict[str, Any]) -> None:
    print("=" * 72)
    print("COUPON WORLD SHOPPING DECISION ENGINE v1.0")
    print("=" * 72)
    print("QUERY:", result["query"])
    print("CATEGORY:", result["intent"].get("category"))
    print("PROFILE:", result["intent"].get("user_profile"))
    print("USE CASE:", result["intent"].get("use_case"))
    print("THRESHOLD:", f'{result["threshold_percent"]}%')
    print()

    recommendations = result["recommendations"]

    if not recommendations:
        print("No qualifying recommendation found.")
        return

    for position, product in enumerate(recommendations, start=1):
        assessment = product["fit_assessment"]

        print("-" * 72)
        print(f"#{position} | {product.get('title')}")
        print("FIT:", f'{assessment["fit_percent"]}%')
        print(
            "EVIDENCE COVERAGE:",
            f'{assessment["evidence_coverage_percent"]}%'
        )
        print(
            "CONFIDENCE:",
            assessment["recommendation_confidence"].upper()
        )

        matched = assessment.get("matched_requirements", [])
        partial = assessment.get("partial_requirements", [])
        unknown = assessment.get("unknown_requirements", [])
        weak = assessment.get("weak_requirements", [])

        if matched:
            print("STRONG MATCH:", ", ".join(matched))
        if partial:
            print("PARTIAL MATCH:", ", ".join(partial))
        if weak:
            print("WEAK:", ", ".join(weak))
        if unknown:
            print("UNKNOWN:", ", ".join(unknown))

    if len(recommendations) < 3:
        print()
        print(
            "NOTE: Fewer than 3 products crossed the 50% fit/evidence threshold."
        )


if __name__ == "__main__":
    query = (
        "Phone under 25000 for my father "
        "with good battery and large display"
    )

    candidates = [
        {
            "title": "Candidate A",
            "price": 23999,
            "fit_signals": {
                "budget": 1.0,
                "battery": 0.95,
                "display": 0.95,
                "ease_of_use": 0.90,
                "camera": 0.60,
                "performance": 0.65,
                "software_support": 0.85,
                "connectivity": 1.0,
            },
        },
        {
            "title": "Candidate B",
            "price": 22999,
            "fit_signals": {
                "budget": 1.0,
                "battery": 0.88,
                "display": 0.85,
                "ease_of_use": 0.80,
                "camera": 0.75,
                "performance": 0.75,
                "software_support": 0.75,
                "connectivity": 1.0,
            },
        },
        {
            "title": "Candidate C",
            "price": 24999,
            "fit_signals": {
                "budget": 1.0,
                "battery": 0.80,
                "display": 0.80,
                "ease_of_use": 0.70,
                "camera": 0.85,
                "performance": 0.80,
                "software_support": 0.60,
                "connectivity": 1.0,
            },
        },
        {
            "title": "Candidate D",
            "price": 19999,
            "fit_signals": {
                "budget": 1.0,
                "battery": 0.70,
                "display": 0.65,
                "ease_of_use": 0.75,
                "camera": 0.55,
                "performance": 0.60,
                "software_support": 0.55,
                "connectivity": 0.90,
            },
        },
        {
            "title": "Candidate E",
            "price": 18999,
            "fit_signals": {
                "budget": 1.0,
                "battery": 0.55,
                "display": 0.55,
                "ease_of_use": 0.55,
                "camera": 0.45,
                "performance": 0.50,
                "software_support": 0.45,
                "connectivity": 0.80,
            },
        },
        {
            "title": "Candidate F Over Budget",
            "price": 32999,
            "fit_signals": {
                "budget": 0.0,
                "battery": 1.0,
                "display": 1.0,
                "ease_of_use": 1.0,
                "camera": 1.0,
                "performance": 1.0,
                "software_support": 1.0,
                "connectivity": 1.0,
            },
        },
    ]

    result = decide(query, candidates)
    print_decision(result)
