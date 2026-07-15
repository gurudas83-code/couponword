#!/usr/bin/env python3

"""
Coupon World Product Expansion Queue v1

Purpose:
- Analyse current category coverage
- Identify underrepresented categories
- Measure direct-product-link coverage
- Prepare a data-driven expansion queue
- Recommend allocation for the next product batch

READ-ONLY:
- Does not modify coupons.json
- Does not add products
- Does not invent product information
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "coupons.json"

DEFAULT_MINIMUM_PER_CATEGORY = 5
DEFAULT_BATCH_SIZE = 25


def clean(value: object) -> str:
    return " ".join(
        str(value or "").strip().split()
    )


def product_identity(
    product: dict,
    index: int,
) -> str:
    return str(
        product.get("id")
        or product.get("sl_no")
        or product.get("asin")
        or index
    )


def link_type(product: dict) -> str:
    explicit = clean(
        product.get("linkType")
    ).lower()

    if explicit:
        return explicit

    link = clean(product.get("link"))

    if not link:
        return "missing"

    parsed = urlparse(link)

    if (
        "/dp/" in parsed.path
        or "/d/" in parsed.path
    ):
        return "product"

    if (
        "/s" in parsed.path
        or "k=" in parsed.query
    ):
        return "search"

    return "other"


def has_image(product: dict) -> bool:
    return bool(
        clean(product.get("image"))
    )


def has_price(product: dict) -> bool:
    value = product.get("price")

    if value in (None, ""):
        return False

    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def has_asin(product: dict) -> bool:
    return bool(
        clean(product.get("asin"))
    )


def category_health(
    products: list[dict],
) -> int:
    if not products:
        return 0

    total_checks = len(products) * 4
    passed_checks = 0

    for product in products:
        if link_type(product) == "product":
            passed_checks += 1

        if has_image(product):
            passed_checks += 1

        if has_price(product):
            passed_checks += 1

        if has_asin(product):
            passed_checks += 1

    return round(
        passed_checks / total_checks * 100
    )


def priority_score(
    product_count: int,
    minimum_target: int,
    direct_links: int,
    health: int,
) -> int:
    """
    Higher score means higher expansion priority.

    The score favours:
    - Categories below minimum coverage
    - Categories with at least some usable direct links
    - Categories with healthier existing data
    """

    gap = max(
        0,
        minimum_target - product_count,
    )

    score = gap * 20

    if product_count == 0:
        score += 25
    elif product_count <= 2:
        score += 15
    elif product_count < minimum_target:
        score += 8

    if direct_links > 0:
        score += min(
            direct_links * 3,
            15,
        )

    score += round(
        health * 0.15
    )

    return score


def allocate_batch(
    rows: list[dict],
    batch_size: int,
) -> dict[str, int]:
    allocation: Counter[str] = Counter()

    eligible = [
        row
        for row in rows
        if row["gap"] > 0
    ]

    remaining = batch_size

    # First fill category minimum gaps.
    while remaining > 0 and eligible:
        changed = False

        for row in eligible:
            category = row["category"]

            if allocation[category] >= row["gap"]:
                continue

            allocation[category] += 1
            remaining -= 1
            changed = True

            if remaining == 0:
                break

        if not changed:
            break

    # If places remain, strengthen healthier existing categories.
    growth_candidates = sorted(
        rows,
        key=lambda row: (
            row["priority"],
            row["health"],
            row["direct_links"],
        ),
        reverse=True,
    )

    index = 0

    while (
        remaining > 0
        and growth_candidates
    ):
        row = growth_candidates[
            index % len(growth_candidates)
        ]

        allocation[
            row["category"]
        ] += 1

        remaining -= 1
        index += 1

    return dict(allocation)


def print_section(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Create a read-only product expansion "
            "priority queue"
        )
    )

    parser.add_argument(
        "--minimum",
        type=int,
        default=DEFAULT_MINIMUM_PER_CATEGORY,
        help=(
            "Minimum target products per existing category "
            f"(default: {DEFAULT_MINIMUM_PER_CATEGORY})"
        ),
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=(
            "Number of future products to allocate "
            f"(default: {DEFAULT_BATCH_SIZE})"
        ),
    )

    args = parser.parse_args()

    if args.minimum < 1:
        print("FAIL: --minimum must be at least 1")
        return 1

    if args.batch_size < 1:
        print("FAIL: --batch-size must be at least 1")
        return 1

    try:
        raw_products = json.loads(
            DB.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ) as exc:
        print(f"FAIL: {exc}")
        return 1

    if not isinstance(raw_products, list):
        print(
            "FAIL: coupons.json must contain a JSON list"
        )
        return 1

    products = [
        product
        for product in raw_products
        if (
            isinstance(product, dict)
            and product.get("active") is not False
        )
    ]

    grouped: dict[str, list[dict]] = defaultdict(list)

    for product in products:
        category = (
            clean(product.get("category"))
            or "[MISSING]"
        )

        grouped[category].append(product)

    rows = []

    for category, category_products in grouped.items():
        count = len(category_products)

        type_counts = Counter(
            link_type(product)
            for product in category_products
        )

        direct_links = type_counts["product"]
        search_links = type_counts["search"]

        health = category_health(
            category_products
        )

        gap = max(
            0,
            args.minimum - count,
        )

        priority = priority_score(
            product_count=count,
            minimum_target=args.minimum,
            direct_links=direct_links,
            health=health,
        )

        rows.append(
            {
                "category": category,
                "count": count,
                "gap": gap,
                "direct_links": direct_links,
                "search_links": search_links,
                "other_links": (
                    count
                    - direct_links
                    - search_links
                ),
                "images": sum(
                    1
                    for product in category_products
                    if has_image(product)
                ),
                "prices": sum(
                    1
                    for product in category_products
                    if has_price(product)
                ),
                "asins": sum(
                    1
                    for product in category_products
                    if has_asin(product)
                ),
                "health": health,
                "priority": priority,
            }
        )

    rows.sort(
        key=lambda row: (
            row["priority"],
            row["gap"],
            row["health"],
        ),
        reverse=True,
    )

    allocation = allocate_batch(
        rows,
        args.batch_size,
    )

    print_section(
        "COUPON WORLD PRODUCT EXPANSION QUEUE v1"
    )

    print(
        f"Active products            : {len(products)}"
    )
    print(
        f"Existing categories        : {len(rows)}"
    )
    print(
        f"Minimum/category target    : {args.minimum}"
    )
    print(
        f"Next batch size            : {args.batch_size}"
    )
    print(
        "Database changed           : NO"
    )

    print_section("CATEGORY EXPANSION PRIORITY")

    print(
        "PRI | NOW | GAP | DIRECT | SEARCH | "
        "IMG | PRICE | ASIN | HEALTH | CATEGORY"
    )

    print("-" * 78)

    for row in rows:
        print(
            f"{row['priority']:>3} | "
            f"{row['count']:>3} | "
            f"{row['gap']:>3} | "
            f"{row['direct_links']:>6} | "
            f"{row['search_links']:>6} | "
            f"{row['images']:>3} | "
            f"{row['prices']:>5} | "
            f"{row['asins']:>4} | "
            f"{row['health']:>5}% | "
            f"{row['category']}"
        )

    print_section(
        f"RECOMMENDED NEXT {args.batch_size} PRODUCT ALLOCATION"
    )

    allocation_rows = sorted(
        allocation.items(),
        key=lambda item: (
            item[1],
            item[0].lower(),
        ),
        reverse=True,
    )

    allocated_total = 0

    for category, count in allocation_rows:
        current = len(
            grouped.get(
                category,
                [],
            )
        )

        after = current + count
        allocated_total += count

        print(
            f"+{count:>2} | "
            f"{current:>3} -> {after:<3} | "
            f"{category}"
        )

    print("-" * 78)
    print(
        f"Allocated products         : {allocated_total}"
    )

    print_section("WEAK CATEGORY QUEUE")

    weak_rows = [
        row
        for row in rows
        if row["count"] < args.minimum
    ]

    if not weak_rows:
        print(
            "No existing category is below "
            "the minimum target."
        )
    else:
        for number, row in enumerate(
            weak_rows,
            start=1,
        ):
            print(
                f"{number:>2}. "
                f"{row['category']} — "
                f"{row['count']} current, "
                f"{row['gap']} needed, "
                f"health {row['health']}%"
            )

    print_section("DIRECT PRODUCT LINK OPPORTUNITIES")

    link_opportunities = sorted(
        rows,
        key=lambda row: (
            row["direct_links"],
            row["health"],
        ),
        reverse=True,
    )

    for row in link_opportunities[:10]:
        print(
            f"{row['direct_links']:>3} direct | "
            f"{row['count']:>3} total | "
            f"{row['health']:>3}% health | "
            f"{row['category']}"
        )

    print_section("NEXT CONTROLLED ACTION")

    print(
        "1. Prepare only verified product URLs "
        "for the recommended categories."
    )
    print(
        "2. Convert URLs into the approved import CSV."
    )
    print(
        "3. Run import preview and reject duplicates/errors."
    )
    print(
        "4. Import a small batch only after preview passes."
    )
    print(
        "5. Rebuild, validate and rerun discovery audit."
    )

    print()
    print("SAFETY RULES")
    print("-" * 78)
    print("No products added.")
    print("No titles invented.")
    print("No prices or images invented.")
    print("No database files modified.")

    print()
    print("PRODUCT QUEUE STATUS: PASS")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
