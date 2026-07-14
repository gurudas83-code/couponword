#!/usr/bin/env python3

"""
Coupon World Site Intelligence Report v1

Purpose:
- Analyse current product database quality
- Identify missing product information
- Measure category coverage
- Recommend the next highest-value action

READ-ONLY:
This script does not modify coupons.json or generated pages.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "coupons.json"


def clean(value: object) -> str:
    return str(value or "").strip()


def has_price(product: dict) -> bool:
    value = product.get("price")

    if value in (None, ""):
        return False

    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def is_product_link(product: dict) -> bool:
    link_type = clean(product.get("linkType")).lower()

    if link_type == "product":
        return True

    link = clean(product.get("link")).lower()

    return any(
        token in link
        for token in (
            "/dp/",
            "/gp/product/",
            "amzn.in/d/",
        )
    )


def identity(product: dict, index: int) -> str:
    return str(
        product.get("id")
        or product.get("sl_no")
        or product.get("asin")
        or index
    )


def missing_fields(product: dict) -> list[str]:
    missing: list[str] = []

    if not clean(product.get("image")):
        missing.append("image")

    if not has_price(product):
        missing.append("price")

    if not clean(product.get("description")):
        missing.append("description")

    if not clean(product.get("brand")):
        missing.append("brand")

    if not clean(product.get("asin")):
        missing.append("asin")

    return missing


def priority_score(product: dict) -> int:
    score = 0

    if not clean(product.get("image")):
        score += 30

    if not has_price(product):
        score += 25

    if not clean(product.get("description")):
        score += 20

    if not clean(product.get("brand")):
        score += 10

    if not clean(product.get("asin")):
        score += 10

    if not is_product_link(product):
        score += 5

    return score


def percentage(value: int, total: int) -> str:
    if total == 0:
        return "0.0%"

    return f"{(value / total) * 100:.1f}%"


def determine_next_action(
    total: int,
    missing_images: int,
    missing_prices: int,
    missing_descriptions: int,
    missing_brands: int,
    weak_categories: list[tuple[str, int]],
) -> tuple[str, str]:
    if total == 0:
        return (
            "ADD PRODUCTS",
            "The product database is empty.",
        )

    if missing_images / total >= 0.50:
        return (
            "CONNECT A VERIFIED PRODUCT DATA SOURCE",
            "Most products do not have images. "
            "A legal feed/API or verified merchant catalogue is the highest-value next step.",
        )

    if missing_prices / total >= 0.50:
        return (
            "CONNECT PRICE AND AVAILABILITY DATA",
            "Most products do not have verified prices. "
            "Do not invent prices; connect an approved provider or merchant feed.",
        )

    if missing_descriptions / total >= 0.40:
        return (
            "GENERATE FACTUAL PRODUCT DESCRIPTIONS",
            "Many products lack useful descriptions. "
            "Descriptions should use only verified existing facts.",
        )

    if missing_brands / total >= 0.30:
        return (
            "NORMALIZE PRODUCT BRANDS",
            "Brand coverage is weak and should be cleaned before decision scoring.",
        )

    if weak_categories:
        return (
            "STRENGTHEN CATEGORY COVERAGE",
            "Several categories contain too few products for useful comparisons.",
        )

    return (
        "START QUESTION INTELLIGENCE",
        "The catalogue is sufficiently structured for a controlled question-answer experiment.",
    )


def main() -> int:
    if not DB.exists():
        print("FAIL: coupons.json not found")
        return 1

    try:
        products = json.loads(DB.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"FAIL: Invalid coupons.json: {exc}")
        return 1

    if not isinstance(products, list):
        print("FAIL: coupons.json must contain a list")
        return 1

    valid_products = [
        product
        for product in products
        if isinstance(product, dict)
    ]

    total = len(valid_products)

    missing_images = sum(
        not clean(product.get("image"))
        for product in valid_products
    )

    missing_prices = sum(
        not has_price(product)
        for product in valid_products
    )

    missing_descriptions = sum(
        not clean(product.get("description"))
        for product in valid_products
    )

    missing_brands = sum(
        not clean(product.get("brand"))
        for product in valid_products
    )

    missing_asins = sum(
        not clean(product.get("asin"))
        for product in valid_products
    )

    product_links = sum(
        is_product_link(product)
        for product in valid_products
    )

    search_or_other_links = total - product_links

    category_counts = Counter(
        clean(product.get("category")) or "Uncategorised"
        for product in valid_products
    )

    weak_categories = sorted(
        (
            (category, count)
            for category, count in category_counts.items()
            if count < 3
        ),
        key=lambda item: (item[1], item[0].lower()),
    )

    prioritised = sorted(
        enumerate(valid_products, start=1),
        key=lambda item: (
            -priority_score(item[1]),
            identity(item[1], item[0]),
        ),
    )

    next_action, reason = determine_next_action(
        total,
        missing_images,
        missing_prices,
        missing_descriptions,
        missing_brands,
        weak_categories,
    )

    print("=" * 72)
    print("COUPON WORLD SITE INTELLIGENCE REPORT")
    print("=" * 72)

    print(f"Products                   : {total}")
    print(f"Categories                 : {len(category_counts)}")
    print(f"Direct product links       : {product_links}")
    print(f"Search/other links         : {search_or_other_links}")

    print()
    print("DATA COMPLETENESS")
    print("-" * 72)
    print(
        f"Missing images             : {missing_images:>3} "
        f"({percentage(missing_images, total)})"
    )
    print(
        f"Missing prices             : {missing_prices:>3} "
        f"({percentage(missing_prices, total)})"
    )
    print(
        f"Missing descriptions       : {missing_descriptions:>3} "
        f"({percentage(missing_descriptions, total)})"
    )
    print(
        f"Missing brands             : {missing_brands:>3} "
        f"({percentage(missing_brands, total)})"
    )
    print(
        f"Missing ASINs              : {missing_asins:>3} "
        f"({percentage(missing_asins, total)})"
    )

    print()
    print("CATEGORY COVERAGE")
    print("-" * 72)

    for category, count in category_counts.most_common():
        label = "WEAK" if count < 3 else "OK"
        print(f"{count:>3} | {label:<4} | {category}")

    print()
    print("TOP PRODUCTS NEEDING ENRICHMENT")
    print("-" * 72)

    shown = 0

    for index, product in prioritised:
        fields = missing_fields(product)

        if not fields:
            continue

        print(
            f"ID {identity(product, index):<5} | "
            f"Score {priority_score(product):>3} | "
            f"Missing: {', '.join(fields)} | "
            f"{clean(product.get('title'))[:70]}"
        )

        shown += 1

        if shown >= 10:
            break

    if shown == 0:
        print("No enrichment gaps found.")

    print()
    print("=" * 72)
    print("NEXT BEST ACTION")
    print("=" * 72)
    print(next_action)
    print(reason)

    print()
    print("RECOMMENDED ORDER")
    print("-" * 72)
    print("1. Verified product data source")
    print("2. Image, price and availability enrichment")
    print("3. Brand/category normalization")
    print("4. Factual descriptions")
    print("5. Shopping question intelligence")
    print("6. SEO answer pages and traffic measurement")

    print()
    print("REPORT STATUS: PASS")
    print("Database changed: NO")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
