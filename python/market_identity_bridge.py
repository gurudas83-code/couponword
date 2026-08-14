#!/usr/bin/env python3
"""
Coupon World AI OS
Market Identity Bridge v1.0

Purpose:
Convert Market Discovery candidates into research-friendly product identities
using the existing product_identity_v2.py logic.

Flow:
market_discovery.py
-> discovered candidates
-> product_identity_v2.build_identity()
-> identity candidates ready for official_source_resolver.py

Important:
- Does not approve products.
- Does not publish products.
- Does not calculate final Fit.
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

from market_discovery import discover_market
from product_identity_v2 import build_identity


def candidate_to_product(candidate: dict[str, Any]) -> dict[str, Any]:
    """
    Adapt a market-discovery candidate to the input shape expected by
    product_identity_v2.build_identity().
    """
    candidate_id = str(candidate.get("candidate_id") or "").strip()

    return {
        "product_id": candidate_id,
        "title": str(candidate.get("title") or "").strip(),
        "brand": "",
        "asin": "",
        "link": str(candidate.get("source_url") or "").strip(),
        "source_url": str(candidate.get("source_url") or "").strip(),
        "source_host": str(candidate.get("source_host") or "").strip(),
        "discovery_channel": str(
            candidate.get("discovery_channel") or ""
        ).strip(),
        "discovery_score": candidate.get("discovery_score"),
        "snippet": str(candidate.get("snippet") or "").strip(),
    }


def build_market_identities(
    query: str,
    max_candidates: int = 15,
) -> dict[str, Any]:
    discovery = discover_market(
        user_query=query,
        max_candidates=max_candidates,
    )

    identities: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for candidate in discovery.get("candidates", []):
        if not isinstance(candidate, dict):
            continue

        product = candidate_to_product(candidate)

        try:
            identity = build_identity(product)
        except Exception as error:
            skipped.append(
                {
                    "candidate_id": candidate.get("candidate_id"),
                    "title": candidate.get("title"),
                    "reason": str(error),
                }
            )
            continue

        if not isinstance(identity, dict):
            skipped.append(
                {
                    "candidate_id": candidate.get("candidate_id"),
                    "title": candidate.get("title"),
                    "reason": "build_identity returned non-dict result",
                }
            )
            continue

        identity["source_url"] = candidate.get("source_url")
        identity["source_host"] = candidate.get("source_host")
        identity["discovery_channel"] = candidate.get("discovery_channel")
        identity["discovery_score"] = candidate.get("discovery_score")
        identity["status"] = "identity_prepared_unverified"

        identities.append(identity)

    return {
        "query": query,
        "intent": discovery.get("intent", {}),
        "discovered_count": discovery.get("candidate_count", 0),
        "identity_count": len(identities),
        "identities": identities,
        "skipped": skipped,
        "note": (
            "These identities are research candidates only. "
            "Official-source verification is still required."
        ),
    }


def print_result(payload: dict[str, Any]) -> None:
    print("=" * 76)
    print("COUPON WORLD MARKET IDENTITY BRIDGE v1.0")
    print("=" * 76)
    print("QUERY:", payload.get("query"))
    print("DISCOVERED:", payload.get("discovered_count"))
    print("IDENTITIES:", payload.get("identity_count"))
    print()

    for index, identity in enumerate(
        payload.get("identities", []),
        start=1,
    ):
        print("-" * 76)
        print(f"#{index} | {identity.get('search_name')}")
        print("PRODUCT ID :", identity.get("product_id"))
        print("BRAND      :", identity.get("brand"))
        print("MODEL      :", identity.get("model"))
        print("SEARCH     :", identity.get("search_name"))
        print("QUERY      :", identity.get("official_search_query"))

        confidence = identity.get("confidence", {})
        if isinstance(confidence, dict):
            print(
                "CONFIDENCE :",
                confidence.get("score"),
                confidence.get("level"),
            )

        print("SOURCE URL :", identity.get("source_url"))
        print("STATE      :", identity.get("status"))

    skipped = payload.get("skipped", [])
    if skipped:
        print()
        print("SKIPPED:", len(skipped))
        for item in skipped:
            print(
                " -",
                item.get("candidate_id"),
                "|",
                item.get("reason"),
            )

    print()
    print(payload.get("note"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert market-discovered products into research identities"
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Natural-language shopping query",
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=15,
        help="Maximum market candidates to process",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON output",
    )

    args = parser.parse_args()

    try:
        payload = build_market_identities(
            query=args.query,
            max_candidates=max(3, min(args.max_candidates, 30)),
        )
    except Exception as error:
        print("ERROR:", str(error))
        return 1

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_result(payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
