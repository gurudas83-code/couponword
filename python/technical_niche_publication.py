"""Reviewed *publication filter* for the existing legacy coupon/product dataset.

Only the site's smartphone / consumer-technology niche is displayed. This does
not modify ROOT/coupons.json, the ranking engine, research database, or API.
Every new legacy record needs an editorial review before public promotion.
"""
from __future__ import annotations

import json
from pathlib import Path

REVIEWED_TECH_IDS = frozenset({
    2, 9, 10, 11, 14, 15, 24, 25, 26, 28, 29, 30, 32, 33,
    34, 36, 37, 38, 39, 41, 42, 52, 53, 54, 55, 56, 57,
    58, 59, 60, 69, *range(72, 106),
})
TECH_CATEGORIES = frozenset({
    "Prime Deal - Electronics", "Electronics",
    "Mobiles", "Cell Phones & Accessories",
})
# The category check is an additional safety net against a future data import
# accidentally reusing a legacy ID for fashion, home or other retail products.
REVIEWED_TECH_COUNT = 65


def select_tech_products(products: list[dict]) -> list[dict]:
    if not isinstance(products, list):
        raise ValueError("Expected product list")
    ids = []
    for product in products:
        if not isinstance(product, dict):
            raise ValueError("Unexpected non-object legacy product")
        identity = product.get("id")
        if isinstance(identity, bool):
            raise ValueError("Boolean legacy product identity")
        try:
            ident = int(identity)
        except (ValueError, TypeError):
            raise ValueError("Missing legacy product identity") from None
        if ident <= 0 or str(ident) != str(identity):
            raise ValueError("Noncanonical legacy product ID")
        ids.append(ident)
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate legacy product IDs")
    if not REVIEWED_TECH_IDS.issubset(set(ids)):
        raise ValueError("Reviewed technical products missing from source")
    approved = [product for product in products
                if int(product["id"]) in REVIEWED_TECH_IDS]
    if len(approved) != REVIEWED_TECH_COUNT:
        raise ValueError("Reviewed technical legacy subset count drift")
    for product in approved:
        if product.get("category") not in TECH_CATEGORIES:
            raise ValueError("Reviewed technical category changed: " + str(product["id"]))
        if not str(product.get("title") or "").strip():
            raise ValueError("Reviewed technical product has no title")
    return approved


def publish_tech_subset(destination: Path, source_products: list[dict]) -> dict:
    selected = select_tech_products(source_products)
    target = destination / "coupons.json"
    target.write_text(json.dumps(selected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "source_records": len(source_products),
        "published_tech_records": len(selected),
        "excluded_non_tech_records": len(source_products) - len(selected),
        "checked_only": True,
        "scope": "TECH_ONLY_LEGACY_PUBLICATION_NOT_VERIFIED_CURRENT_OFFERS",
        "note": "Historic products are not buyable offers without the existing freshness and exact-listing gates.",
    }
