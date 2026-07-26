#!/usr/bin/env python3
"""
Coupon World AI OS
Shopping Brain v0.1

Purpose:
- Accept a shopping query
- Parse intent
- Load coupons.json
- Find basic matching products
"""

from __future__ import annotations

import json
from pathlib import Path

from intent_engine import parse_query


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

        matches.append(product)

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
    print("Budget maximum  :", intent.get("budget_max"))
    print("Brands          :", ", ".join(intent.get("brands", [])) or "Any")

    print("-" * 64)
    print("Products loaded :", len(products))
    print("Matches found   :", len(matches))

    for product in matches[:10]:
        print(
            "MATCH |",
            product.get("id"),
            "|",
            product.get("title"),
            "|",
            product.get("brand") or "Unknown brand",
            "|",
            product.get("price") or "Price unavailable",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())