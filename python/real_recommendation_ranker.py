#!/usr/bin/env python3
"""
Coupon World AI OS
Real Recommendation Ranker v1.0

Flow:
User query
-> Intent Engine v2
-> Real published/verified product profiles
-> Product Fit Signals
-> Weighted Fit Engine
-> Keep only products with Fit >= 50%
-> Sort descending
-> Return up to Top 5

Important:
- Does not invent missing evidence.
- Does not use affiliate availability as a ranking factor.
- If fewer than 3 qualifying real products are available, it reports that
  clearly instead of padding the list with weak matches.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PYTHON_DIR = ROOT / "python"

if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from intent_engine import parse_query
from product_intelligence_bridge import build_profile
from product_fit_signal_builder import build_fit_signals
from weighted_fit_engine import rank_recommendations


KNOWLEDGE_FILE = ROOT / "data" / "product_knowledge.json"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def published_product_ids() -> list[str]:
    payload = load_json(KNOWLEDGE_FILE)
    products = payload.get("products", [])

    if not isinstance(products, list):
        return []

    ids: list[str] = []

    for product in products:
        if not isinstance(product, dict):
            continue

        pid = str(product.get("product_id") or "").strip()

        if pid and pid not in ids:
            ids.append(pid)

    return ids


def normalize_category(value: Any) -> str:
    text = str(value or "").strip().lower()

    aliases = {
        "mobiles": "smartphone",
        "mobile": "smartphone",
        "phones": "smartphone",
        "phone": "smartphone",
        "smartphones": "smartphone",
        "electronics": "electronics",
        "earbud": "earbuds",
        "tws": "earbuds",
        "headphone": "headphones",
        "notebooks": "laptop",
        "notebook": "laptop",
    }

    return aliases.get(text, text)


def profile_matches_category(
    profile: dict[str, Any],
    intent_category: str | None,
) -> bool:
    if not intent_category:
        return True

    wanted = normalize_category(intent_category)
    category = normalize_category(profile.get("category"))
    title = str(profile.get("title") or "").lower()

    if category == wanted:
        return True

    title_terms = {
        "smartphone": ("phone", "mobile", "smartphone"),
        "earbuds": ("earbuds", "earbud", "tws", "buds"),
        "headphones": ("headphone", "headphones", "headset"),
        "laptop": ("laptop", "notebook"),
        "smartwatch": ("smartwatch", "smart watch"),
        "tablet": ("tablet", " tab "),
        "speaker": ("speaker",),
    }

    return any(term in f" {title} " for term in title_terms.get(wanted, ()))


def build_real_candidates(
    query: str,
    product_ids: list[str] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, str]]]:
    intent = parse_query(query)

    ids = product_ids or published_product_ids()

    candidates: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []

    for pid in ids:
        profile = build_profile(pid)

        if profile is None:
            skipped.append(
                {
                    "product_id": str(pid),
                    "reason": "No usable verified product profile",
                }
            )
            continue

        if not profile_matches_category(profile, intent.get("category")):
            skipped.append(
                {
                    "product_id": str(pid),
                    "reason": "Category does not match query intent",
                }
            )
            continue

        profile["fit_signals"] = build_fit_signals(profile, intent)
        candidates.append(profile)

    return intent, candidates, skipped


def rank_real_products(
    query: str,
    product_ids: list[str] | None = None,
    max_results: int = 5,
) -> dict[str, Any]:
    intent, candidates, skipped = build_real_candidates(
        query=query,
        product_ids=product_ids,
    )

    ranking = rank_recommendations(
        products=candidates,
        intent=intent,
        max_results=max_results,
        min_results=3,
    )

    return {
        "query": query,
        "intent": intent,
        "candidate_count": len(candidates),
        "skipped": skipped,
        **ranking,
    }


def criterion_summary(assessment: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    strong: list[str] = []
    tradeoffs: list[str] = []
    unknown: list[str] = []

    criteria = assessment.get("criteria", [])

    if not isinstance(criteria, list):
        return strong, tradeoffs, unknown

    for item in criteria:
        if not isinstance(item, dict):
            continue

        criterion = str(item.get("criterion") or "").strip()
        match = item.get("match_score")
        reason = str(item.get("reason") or "").strip()

        if match is None:
            unknown.append(f"{criterion}: {reason}")
            continue

        try:
            score = float(match)
        except (TypeError, ValueError):
            unknown.append(f"{criterion}: {reason}")
            continue

        if score >= 0.80:
            strong.append(f"{criterion}: {reason}")
        elif score < 0.50:
            tradeoffs.append(f"{criterion}: {reason}")

    return strong, tradeoffs, unknown


def print_ranked(result: dict[str, Any]) -> None:
    print("=" * 76)
    print("COUPON WORLD REAL RECOMMENDATION RANKER v1.0")
    print("=" * 76)
    print("QUERY:", result["query"])
    print("CATEGORY:", result["intent"].get("category"))
    print("REAL CANDIDATES EVALUATED:", result["candidate_count"])
    print("QUALIFYING PRODUCTS:", result["recommendation_count"])
    print("FIT THRESHOLD:", f'{result["threshold_percent"]}%')
    print()

    recommendations = result.get("recommendations", [])

    if not recommendations:
        print("No real product crossed the fit/evidence threshold.")
        print(
            "This is a candidate-coverage limitation, not permission "
            "to invent weaker recommendations."
        )
        return

    for position, product in enumerate(recommendations, start=1):
        assessment = product.get("fit_assessment", {})
        strong, tradeoffs, unknown = criterion_summary(assessment)

        print("-" * 76)
        print(f"#{position} | {product.get('title')}")
        print("PRODUCT ID:", product.get("product_id"))
        print("FIT:", f'{assessment.get("fit_percent", 0)}%')
        print(
            "EVIDENCE COVERAGE:",
            f'{assessment.get("evidence_coverage_percent", 0)}%',
        )
        print(
            "CONFIDENCE:",
            str(assessment.get("recommendation_confidence", "low")).upper(),
        )

        if strong:
            print("WHY IT FITS:")
            for item in strong[:4]:
                print("  +", item)

        if tradeoffs:
            print("TRADE-OFFS:")
            for item in tradeoffs[:3]:
                print("  -", item)

        if unknown:
            print("UNVERIFIED/UNKNOWN:")
            for item in unknown[:3]:
                print("  ?", item)

        source = product.get("official_product_url")
        if source:
            print("OFFICIAL SOURCE:", source)

    if result["recommendation_count"] < 3:
        print()
        print(
            "STATUS: FEWER THAN 3 QUALIFYING REAL PRODUCTS ARE CURRENTLY "
            "AVAILABLE IN THE VERIFIED CANDIDATE POOL."
        )
        print(
            "NEXT ARCHITECTURE NEED: MARKET DISCOVERY must add more real "
            "candidates before a full Top 3-5 answer can be produced."
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rank real verified Coupon World products for a shopping query"
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Natural-language shopping query",
    )
    parser.add_argument(
        "--product-id",
        action="append",
        default=[],
        help="Optional product ID; may be repeated. Default: all published products.",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=5,
        help="Maximum recommendations to show (default: 5)",
    )

    args = parser.parse_args()

    result = rank_real_products(
        query=args.query,
        product_ids=args.product_id or None,
        max_results=max(1, min(args.max_results, 5)),
    )

    print_ranked(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
