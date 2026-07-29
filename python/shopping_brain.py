#!/usr/bin/env python3
"""
Coupon World AI OS
Shopping Brain v1.0

Purpose:
- Accept a shopping query
- Parse shopping intent
- Load products
- Match products
- Score products
- Explain recommendations
- Show price intelligence
"""

from __future__ import annotations

import json
import argparse
from pathlib import Path
from typing import Any

from intent_engine import parse_query
from product_scoring import score_product
from recommendation_engine import explain_product
from price_engine import analyze_price


ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "coupons.json"

INTELLIGENCE_DIR = ROOT / "data" / "intelligence"
IDENTITY_DB = INTELLIGENCE_DIR / "product_identity.json"
FEATURE_DB = INTELLIGENCE_DIR / "product_features.json"


def _load_database(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    if isinstance(data, dict):
        return data

    return {}


def load_identity_database() -> dict[str, Any]:
    return _load_database(IDENTITY_DB)


def load_feature_database() -> dict[str, Any]:
    return _load_database(FEATURE_DB)


def load_products() -> list[dict]:
    data = json.loads(DB.read_text(encoding="utf-8"))

    if not isinstance(data, list):
        raise ValueError("coupons.json must contain a list")

    return data


def _index_by_product_id(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}

    for item in payload.get("products", []):
        if not isinstance(item, dict):
            continue

        product_id = item.get("product_id")

        if product_id not in (None, ""):
            index[str(product_id)] = item

    return index


def merge_intelligence(
    products: list[dict],
    identity_payload: dict[str, Any],
    feature_payload: dict[str, Any],
) -> list[dict]:
    identity_index = _index_by_product_id(identity_payload)
    feature_index = _index_by_product_id(feature_payload)

    merged_products: list[dict] = []

    for position, product in enumerate(products, start=1):
        merged = product.copy()

        product_id = (
            product.get("id")
            or product.get("sl_no")
            or product.get("asin")
            or position
        )

        product_key = str(product_id)

        merged["identity"] = identity_index.get(product_key, {})
        merged["features"] = feature_index.get(product_key, {})

        merged_products.append(merged)

    return merged_products


def match_products(products: list[dict], intent: dict) -> list[dict]:
    matches = []

    category = intent.get("category")
    brands = [brand.lower() for brand in intent.get("brands", [])]
    budget_max = intent.get("budget_max")

    for product in products:

        if product.get("active") is False:
            continue

        product_category = str(product.get("category", "")).lower()
        product_brand = str(product.get("brand", "")).lower()
        product_title = str(product.get("title", "")).lower()

        if category:
            category_text = category.lower()

            if (
                category_text not in product_category
                and category_text not in product_title
            ):
                continue

        if brands:
            if not any(
                brand in product_brand or brand in product_title
                for brand in brands
            ):
                continue

        if budget_max is not None:

            price = product.get("price")

            if price not in (None, ""):
                try:
                    if float(price) > budget_max:
                        continue
                except (TypeError, ValueError):
                    pass

        ranked_product = product.copy()

        ranked_product["score"] = score_product(
            ranked_product,
            intent,
        )

        ranked_product["reasons"] = explain_product(
            ranked_product,
            intent,
        )

        ranked_product["price_info"] = analyze_price(
            ranked_product,
            intent,
        )

        matches.append(ranked_product)

    matches.sort(
        key=lambda product: product.get("score", 0),
        reverse=True,
    )

    return matches


def build_response(query: str, intent: dict, matches: list[dict]) -> dict:
    """Return Shopping Brain results as a JSON-serializable dictionary."""

    response = {
        "query": query,
        "intent": intent,
        "total_matches": len(matches),
        "matches": [],
    }

    for product in matches[:10]:
        price_info = product.get("price_info", {})

        response["matches"].append({
            "id": product.get("id"),
            "title": product.get("title"),
            "brand": product.get("brand"),
            "price": price_info.get("price"),
            "mrp": price_info.get("mrp"),
            "discount": price_info.get("discount_percent"),
            "score": product.get("score"),
            "reasons": product.get("reasons", []),
            "link": product.get("link"),
            "category": product.get("category"),
        })

    return response


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Coupon World Shopping Brain"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of formatted text",
    )

    parser.add_argument(
        "query",
        nargs="*",
        help="Shopping query",
    )

    args = parser.parse_args()

    if args.query:
        query = " ".join(args.query).strip()
    else:
        query = input("Shopping Query > ").strip()

    if not query:
        print("ERROR: Shopping query is required.")
        return 1

    intent = parse_query(query)

    products = load_products()

    identity_payload = load_identity_database()
    feature_payload = load_feature_database()

    products = merge_intelligence(
        products,
        identity_payload,
        feature_payload,
    )

    matches = match_products(
        products,
        intent,
    )

    if args.json:
        print(
            json.dumps(
                build_response(query, intent, matches),
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    print("\n" + "=" * 64)
    print("COUPON WORLD SHOPPING BRAIN v1.0")
    print("=" * 64)

    print("Intent          :", intent.get("intent"))
    print("Category        :", intent.get("category"))
    print("Budget minimum  :", intent.get("budget_min"))
    print("Budget maximum  :", intent.get("budget_max"))
    print("Features        :", ", ".join(intent.get("features", [])) or "Any")
    print("Brands          :", ", ".join(intent.get("brands", [])) or "Any")

    print("-" * 64)

    print("Products loaded :", len(products))
    print("Matches found   :", len(matches))

    if not matches:
        print("\nNo matching products found.")
        return 0

    for position, product in enumerate(matches[:10], start=1):

        print("\n" + "=" * 64)
        print(f"RECOMMENDATION #{position}")
        print("=" * 64)

        print("Title      :", product.get("title") or "Untitled product")
        print("ID         :", product.get("id") or product.get("sl_no") or "No ID")
        print("Brand      :", product.get("brand") or "Unknown")

        price_info = product.get("price_info", {})

        if price_info.get("price_available"):
            print(f"Price      : {price_info['price']:.2f}")
        else:
            print("Price      : Price unavailable")

        if price_info.get("mrp") is not None:
            print(f"MRP        : {price_info['mrp']:.2f}")

        if price_info.get("discount_percent") is not None:
            print(
                f"Discount   : {price_info['discount_percent']}%"
            )

        if price_info.get("within_budget") is True:
            print("Budget     : Within budget")

        elif price_info.get("within_budget") is False:
            print("Budget     : Above budget")

        print("Score      :", product.get("score", 0))

        print("\nWhy this product?")

        for reason in product.get("reasons", []):
            print("  ", reason)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())









