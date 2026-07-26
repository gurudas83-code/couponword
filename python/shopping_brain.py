#!/usr/bin/env python3
"""
Coupon World AI OS
Shopping Brain v0.3

Purpose:
- Accept a shopping query
- Parse shopping intent
- Load products from coupons.json
- Filter matching products
- Score and rank products
- Explain why each product is recommended
"""

from __future__ import annotations

import json
from pathlib import Path

from intent_engine import parse_query
from product_scoring import score_product
from recommendation_engine import explain_product


ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "coupons.json"


def load_products() -> list[dict]:
    data = json.loads(DB.read_text(encoding="utf-8"))

    if not isinstance(data, list):
        raise ValueError("coupons.json must contain a list")

    return data


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

            if price in (None, ""):
                continue

            try:
                numeric_price = float(price)
            except (TypeError, ValueError):
                continue

            if numeric_price > budget_max:
                continue

        ranked_product = product.copy()
        ranked_product["score"] = score_product(ranked_product, intent)
        ranked_product["reasons"] = explain_product(ranked_product, intent)

        matches.append(ranked_product)

    matches.sort(
        key=lambda product: product.get("score", 0),
        reverse=True,
    )

    return matches


def main() -> int:
    query = input("Shopping Query > ").strip()

    if not query:
        print("ERROR: Shopping query is required.")
        return 1

    intent = parse_query(query)
    products = load_products()
    matches = match_products(products, intent)

    print("\n" + "=" * 64)
    print("COUPON WORLD SHOPPING BRAIN")
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
        print("No matching products found.")
        return 0

    for position, product in enumerate(matches[:10], start=1):
        print("\n" + "-" * 64)
        print(f"RECOMMENDATION #{position}")
        print("-" * 64)

        print("Title :", product.get("title") or "Untitled product")
        print(
            "ID    :",
            product.get("id") or product.get("sl_no") or "No ID",
        )
        print("Brand :", product.get("brand") or "Unknown brand")
        print("Price :", product.get("price") or "Price unavailable")
        print("Score :", product.get("score", 0))

        print("Why this product?")

        for reason in product.get("reasons", []):
            print(" ", reason)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())