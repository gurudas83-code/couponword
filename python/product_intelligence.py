#!/usr/bin/env python3

"""
Coupon World Product Intelligence Engine v2

Purpose:
- Measure product database health
- Report field coverage and category distribution
- Detect duplicate IDs, links, ASINs and titles
- Identify products needing enrichment
- Preview cautious brand and description proposals

READ-ONLY:
- Does not modify coupons.json
- Does not invent prices, ratings, reviews or availability
- Does not claim that a product is "best"
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "coupons.json"


KNOWN_BRANDS = {
    "amazon basics": "Amazon Basics",
    "american tourister": "American Tourister",
    "apple": "Apple",
    "asus": "ASUS",
    "bajaj": "Bajaj",
    "bausch lomb": "Bausch + Lomb",
    "boat": "boAt",
    "boult": "Boult",
    "campus": "Campus",
    "cello": "Cello",
    "dell": "Dell",
    "encasify": "Encasify",
    "fire-boltt": "Fire-Boltt",
    "fire boltt": "Fire-Boltt",
    "hauser": "Hauser",
    "homestrap": "HomeStrap",
    "hp": "HP",
    "jbl": "JBL",
    "jiada": "JIADA",
    "kore": "KORE",
    "lakme": "Lakmé",
    "levi": "Levi's",
    "logitech": "Logitech",
    "mamaearth": "Mamaearth",
    "mi": "Mi",
    "milton": "Milton",
    "noise": "Noise",
    "oneplus": "OnePlus",
    "philips": "Philips",
    "prestige": "Prestige",
    "puma": "Puma",
    "realme": "realme",
    "redmi": "Redmi",
    "samsung": "Samsung",
    "sony": "Sony",
    "strauss": "Strauss",
    "teeslix": "TeeSlix",
    "titan": "Titan",
    "ugaoo": "Ugaoo",
    "wildcraft": "Wildcraft",
    "yamaha": "Yamaha",
}


REQUIRED_FIELDS = (
    "title",
    "category",
    "link",
)

QUALITY_FIELDS = (
    "brand",
    "description",
    "asin",
    "image",
    "price",
)


def clean(value: object) -> str:
    return re.sub(
        r"\s+",
        " ",
        str(value or ""),
    ).strip()


def normalize_text(value: object) -> str:
    return re.sub(
        r"[^a-z0-9]+",
        " ",
        clean(value).lower(),
    ).strip()


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


def has_value(product: dict, field: str) -> bool:
    value = product.get(field)

    if field == "price":
        if value in (None, ""):
            return False

        try:
            return float(value) > 0
        except (TypeError, ValueError):
            return False

    return clean(value) != ""


def detect_brand(title: str) -> tuple[str, str]:
    """
    Return:
        (brand, confidence)

    HIGH:
        title starts with a known brand

    MEDIUM:
        brand appears naturally before compatibility wording

    LOW:
        no safe brand evidence
    """

    title = clean(title)
    normalized = normalize_text(title)

    if not normalized:
        return "", "LOW"

    compatibility_markers = (
        " for ",
        " compatible with ",
        " works with ",
        " fit for ",
        " suitable for ",
    )

    title_lower = f" {title.lower()} "

    earliest_marker = None

    for marker in compatibility_markers:
        position = title_lower.find(marker)

        if position != -1:
            if (
                earliest_marker is None
                or position < earliest_marker
            ):
                earliest_marker = position

    evidence_text = title

    if earliest_marker is not None:
        evidence_text = title_lower[:earliest_marker].strip()

    normalized_evidence = normalize_text(evidence_text)

    matches: list[tuple[int, str, str]] = []

    for token, brand in KNOWN_BRANDS.items():
        normalized_token = normalize_text(token)

        if not normalized_token:
            continue

        if re.search(
            rf"\b{re.escape(normalized_token)}\b",
            normalized_evidence,
        ):
            matches.append(
                (
                    len(normalized_token),
                    normalized_token,
                    brand,
                )
            )

    if not matches:
        return "", "LOW"

    matches.sort(reverse=True)

    _, token, brand = matches[0]

    if normalized.startswith(token):
        return brand, "HIGH"

    return brand, "MEDIUM"


def build_description(
    title: str,
    category: str,
    brand: str,
) -> str:
    if not title:
        return ""

    if brand and category:
        return (
            f"{title} is listed as a {category.lower()} product "
            f"from {brand}. Check the retailer page for current "
            "specifications, price and availability before purchasing."
        )

    if category:
        return (
            f"{title} is listed in the {category} category. "
            "Check the retailer page for current specifications, "
            "price and availability before purchasing."
        )

    return (
        f"{title}. Check the retailer page for current specifications, "
        "price and availability before purchasing."
    )


def product_completeness(product: dict) -> int:
    fields = REQUIRED_FIELDS + QUALITY_FIELDS

    completed = sum(
        1
        for field in fields
        if has_value(product, field)
    )

    return round(
        completed / len(fields) * 100
    )


def product_missing_fields(product: dict) -> list[str]:
    return [
        field
        for field in REQUIRED_FIELDS + QUALITY_FIELDS
        if not has_value(product, field)
    ]


def database_health(products: list[dict]) -> int:
    if not products:
        return 0

    scores = [
        product_completeness(product)
        for product in products
    ]

    return round(
        sum(scores) / len(scores)
    )


def duplicate_values(
    products: list[dict],
    field: str,
    normalize: bool = False,
) -> dict[str, int]:
    counter = Counter()

    for product in products:
        value = product.get(field)

        if value in (None, ""):
            continue

        key = (
            normalize_text(value)
            if normalize
            else clean(value)
        )

        if key:
            counter[key] += 1

    return {
        value: count
        for value, count in counter.items()
        if count > 1
    }


def link_type(product: dict) -> str:
    explicit = clean(product.get("linkType")).lower()

    if explicit:
        return explicit

    link = clean(product.get("link"))

    if not link:
        return "missing"

    parsed = urlparse(link)

    if "/dp/" in parsed.path or "/d/" in parsed.path:
        return "product"

    if "/s" in parsed.path or "k=" in parsed.query:
        return "search"

    return "other"


def enrichment_score(product: dict) -> int:
    weights = {
        "brand": 15,
        "description": 20,
        "asin": 15,
        "image": 25,
        "price": 25,
    }

    return sum(
        weight
        for field, weight in weights.items()
        if not has_value(product, field)
    )


def proposal_confidence(
    product: dict,
    brand_confidence: str,
) -> str:
    evidence = 0

    if has_value(product, "title"):
        evidence += 1

    if has_value(product, "category"):
        evidence += 1

    if has_value(product, "asin"):
        evidence += 1

    if has_value(product, "image"):
        evidence += 1

    if has_value(product, "price"):
        evidence += 1

    if brand_confidence == "HIGH":
        evidence += 2
    elif brand_confidence == "MEDIUM":
        evidence += 1

    if evidence >= 5:
        return "HIGH"

    if evidence >= 3:
        return "MEDIUM"

    return "LOW"


def print_section(title: str) -> None:
    print()
    print("=" * 76)
    print(title)
    print("=" * 76)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Coupon World read-only product health "
            "and intelligence dashboard"
        )
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum proposals and priority products to display",
    )

    args = parser.parse_args()

    try:
        raw_products = json.loads(
            DB.read_text(
                encoding="utf-8"
            )
        )
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}")
        return 1

    if not isinstance(raw_products, list):
        print("FAIL: coupons.json must contain a JSON list")
        return 1

    products = [
        product
        for product in raw_products
        if isinstance(product, dict)
    ]

    field_coverage = {
        field: sum(
            1
            for product in products
            if has_value(product, field)
        )
        for field in REQUIRED_FIELDS + QUALITY_FIELDS
    }

    complete_products = [
        product
        for product in products
        if not product_missing_fields(product)
    ]

    incomplete_products = [
        product
        for product in products
        if product_missing_fields(product)
    ]

    categories = Counter(
        clean(product.get("category"))
        or "[MISSING]"
        for product in products
    )

    stores = Counter(
        clean(product.get("store"))
        or "[MISSING]"
        for product in products
    )

    link_types = Counter(
        link_type(product)
        for product in products
    )

    duplicate_ids = duplicate_values(
        products,
        "id",
    )

    duplicate_links = duplicate_values(
        products,
        "link",
    )

    duplicate_asins = duplicate_values(
        products,
        "asin",
    )

    duplicate_titles = duplicate_values(
        products,
        "title",
        normalize=True,
    )

    priority_products = sorted(
        enumerate(
            products,
            start=1,
        ),
        key=lambda item: (
            enrichment_score(item[1]),
            -product_completeness(item[1]),
        ),
        reverse=True,
    )

    proposals = []

    for index, product in enumerate(
        products,
        start=1,
    ):
        title = clean(product.get("title"))
        category = clean(product.get("category"))
        existing_brand = clean(product.get("brand"))
        existing_description = clean(
            product.get("description")
        )

        if existing_brand:
            proposed_brand = existing_brand
            brand_confidence = "HIGH"
        else:
            proposed_brand, brand_confidence = detect_brand(
                title
            )

        proposed_description = (
            existing_description
            or build_description(
                title,
                category,
                proposed_brand,
            )
        )

        changes = []

        if not existing_brand and proposed_brand:
            changes.append("brand")

        if (
            not existing_description
            and proposed_description
        ):
            changes.append("description")

        if not changes:
            continue

        proposals.append(
            {
                "id": product_identity(
                    product,
                    index,
                ),
                "title": title,
                "brand": proposed_brand,
                "brand_confidence": brand_confidence,
                "description": proposed_description,
                "changes": changes,
                "confidence": proposal_confidence(
                    product,
                    brand_confidence,
                ),
                "missing": product_missing_fields(
                    product
                ),
            }
        )

    print_section(
        "COUPON WORLD PRODUCT INTELLIGENCE DASHBOARD v2"
    )

    print(f"Products                    : {len(products)}")
    print(f"Complete products           : {len(complete_products)}")
    print(f"Incomplete products         : {len(incomplete_products)}")
    print(f"Database health             : {database_health(products)}%")
    print("Database changed            : NO")

    print_section("FIELD COVERAGE")

    for field in REQUIRED_FIELDS + QUALITY_FIELDS:
        covered = field_coverage[field]

        percentage = (
            round(
                covered / len(products) * 100,
                1,
            )
            if products
            else 0
        )

        print(
            f"{field.title():<28}: "
            f"{covered:>3}/{len(products)} "
            f"({percentage:>5.1f}%)"
        )

    print_section("CATEGORY DISTRIBUTION")

    for category, count in categories.most_common():
        status = (
            "OK"
            if count >= 3
            else "WEAK"
        )

        print(
            f"{count:>3} | {status:<4} | {category}"
        )

    print_section("STORE DISTRIBUTION")

    for store, count in stores.most_common():
        print(
            f"{count:>3} | {store}"
        )

    print_section("LINK TYPE DISTRIBUTION")

    for name, count in link_types.most_common():
        print(
            f"{count:>3} | {name}"
        )

    print_section("DUPLICATE CHECKS")

    print(
        "Duplicate IDs              :",
        len(duplicate_ids),
    )
    print(
        "Duplicate links            :",
        len(duplicate_links),
    )
    print(
        "Duplicate ASINs            :",
        len(duplicate_asins),
    )
    print(
        "Duplicate titles           :",
        len(duplicate_titles),
    )

    print_section("TOP PRODUCTS NEEDING ENRICHMENT")

    for index, product in priority_products[: args.limit]:
        missing = product_missing_fields(product)

        print(
            f"ID {product_identity(product, index):<5} | "
            f"Score {product_completeness(product):>3}% | "
            f"Priority {enrichment_score(product):>3} | "
            f"{clean(product.get('title'))}"
        )

        print(
            "Missing:",
            ", ".join(missing)
            or "none",
        )

        print("-" * 76)

    print_section("SAFE INTELLIGENCE PROPOSALS")

    print(
        "Products with proposals    :",
        len(proposals),
    )

    for proposal in proposals[: args.limit]:
        print(
            f"ID {proposal['id']} | "
            f"Confidence {proposal['confidence']} | "
            f"Changes: {', '.join(proposal['changes'])}"
        )

        print(
            "Title       :",
            proposal["title"],
        )

        print(
            "Brand       :",
            proposal["brand"]
            or "[NOT VERIFIED]",
        )

        print(
            "Brand proof :",
            proposal["brand_confidence"],
        )

        print(
            "Description :",
            proposal["description"],
        )

        print(
            "Still missing:",
            ", ".join(proposal["missing"])
            or "none",
        )

        print("-" * 76)

    print_section("NEXT BEST ACTION")

    missing_counts = {
        field: (
            len(products)
            - field_coverage[field]
        )
        for field in QUALITY_FIELDS
    }

    ordered_actions = sorted(
        missing_counts.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    for number, (field, count) in enumerate(
        ordered_actions,
        start=1,
    ):
        print(
            f"{number}. Improve {field} coverage "
            f"({count} products missing)"
        )

    print()
    print("SAFETY RULES")
    print("-" * 76)
    print("No features invented.")
    print("No prices invented.")
    print("No ratings or reviews invented.")
    print("No 'best product' claims generated.")
    print("No files modified.")

    print()
    print("PRODUCT INTELLIGENCE STATUS: PASS")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
