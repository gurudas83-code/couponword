#!/usr/bin/env python3

from __future__ import annotations


def score_product(product: dict, intent: dict) -> int:
    score = 0

    title = str(product.get("title", "")).lower()
    category = str(product.get("category", "")).lower()
    brand = str(product.get("brand", "")).lower()

    # Category match
    query_category = intent.get("category")
    if query_category:
        query_category = query_category.lower()
        if query_category in category or query_category in title:
            score += 50

    # Brand match
    for query_brand in intent.get("brands", []):
        query_brand = query_brand.lower()
        if query_brand in brand or query_brand in title:
            score += 30

    # Feature match
    for feature in intent.get("features", []):
        feature = feature.lower()
        if feature in title:
            score += 20

    # Budget preference
    budget = intent.get("budget_max")
    price = product.get("price")

    if budget is not None and price not in (None, ""):
        try:
            if float(price) <= budget:
                score += 15
        except (ValueError, TypeError):
            pass

    return score

if __name__ == "__main__":
    sample_product = {
        "title": "boAt Airdopes 311 Pro ANC Earbuds",
        "category": "Earbuds",
        "brand": "boAt",
        "price": 1799,
    }

    sample_intent = {
        "category": "earbuds",
        "brands": ["boAt"],
        "features": ["ANC"],
        "budget_max": 2000,
    }

    print(score_product(sample_product, sample_intent))