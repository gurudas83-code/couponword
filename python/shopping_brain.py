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
from pathlib import Path

from intent_engine import parse_query
from product_scoring import score_product
from recommendation_engine import explain_product
from price_engine import analyze_price


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


def main() -> int:

    query = input("Shopping Query > ").strip()

    if not query:
        print("ERROR: Shopping query is required.")
        return 1

    intent = parse_query(query)

    products = load_products()

    matches = match_products(
        products,
        intent,
    )

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
            print(f"Price      : ₹{price_info['price']:.2f}")
        else:
            print("Price      : Price unavailable")

        if price_info.get("mrp") is not None:
            print(f"MRP        : ₹{price_info['mrp']:.2f}")

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