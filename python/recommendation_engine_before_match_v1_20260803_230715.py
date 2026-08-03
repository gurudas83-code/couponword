#!/usr/bin/env python3

from __future__ import annotations


def explain_product(product: dict, intent: dict) -> list[str]:
    reasons = []

    title = str(product.get("title", "")).lower()
    category = str(product.get("category", "")).lower()
    brand = str(product.get("brand", "")).lower()
    price = product.get("price")

    # Category
    query_category = intent.get("category")
    if query_category:
        query_category = query_category.lower()
        if query_category in category or query_category in title:
            reasons.append("✓ Category matched")

    # Brand
    for query_brand in intent.get("brands", []):
        query_brand = query_brand.lower()
        if query_brand in brand or query_brand in title:
            reasons.append("✓ Brand matched")

    # Features
    for feature in intent.get("features", []):
        feature = feature.lower()
        if feature in title:
            reasons.append(f"✓ {feature.upper()} matched")

    # Budget
    budget = intent.get("budget_max")
    if budget is not None:
        if price in (None, ""):
            reasons.append("✗ Price unavailable")
        else:
            try:
                if float(price) <= budget:
                    reasons.append("✓ Within budget")
                else:
                    reasons.append("✗ Above budget")
            except (TypeError, ValueError):
                reasons.append("✗ Invalid price")

    if not reasons:
        reasons.append("No matching reason available")

    return reasons


if __name__ == "__main__":
    product = {
        "title": "boAt Airdopes 311 Pro ANC Earbuds",
        "category": "Earbuds",
        "brand": "boAt",
        "price": 1799,
    }

    intent = {
        "category": "earbuds",
        "brands": ["boAt"],
        "features": ["ANC"],
        "budget_max": 2000,
    }

    for reason in explain_product(product, intent):
        print(reason)