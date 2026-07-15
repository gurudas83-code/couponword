#!/usr/bin/env python3

"""
Coupon World Internal Link Engine v2

Purpose:
- Detect broad product families from factual title/category text
- Recommend genuinely related internal product links
- Avoid broad same-category random linking
- Preview only

READ-ONLY:
This version does not modify product pages.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "coupons.json"
PRODUCTS_DIR = ROOT / "products"

LEGACY_PRODUCT_PATHS = {
    "17": "amazon-in-fashion-fest-17",
}

PRODUCT_FAMILIES = {
    "earbuds": (
        "earbud",
        "earbuds",
        "tws",
        "buds air",
        "airpods",
    ),
    "headphones": (
        "headphone",
        "headphones",
        "headset",
        "rockerz",
    ),
    "smartphones": (
        "iphone",
        "smartphone",
        "galaxy m",
        "redmi note",
        "redmi 13",
        "nord ce",
        "5g phone",
        "mobile phone",
    ),
    "phone-accessories": (
        "phone case",
        "mobile case",
        "screen protector",
        "charger",
        "charging cable",
        "power bank",
    ),
    "tablet-accessories": (
        "keyboard case",
        "folio cover",
        "tablet case",
        "tab a",
    ),
    "smartwatches": (
        "smartwatch",
        "smart watch",
    ),
    "telescope-accessories": (
        "telescope cover",
        "telescope case",
        "telescope bag",
    ),
    "telescopes": (
        "newtonian reflector",
        "reflector telescope",
        "telescope 235x",
        "76700 telescope",
    ),
    "projectors": (
        "projector",
        "planetarium",
        "nebula lamp",
    ),
    "storage-media": (
        "micro sd",
        "microsd",
        "memory card",
        "sd card",
    ),
    "musical-keyboards": (
        "musical keyboard",
        "mini keyboard",
        "37 keys",
        "61 keys",
        "electronic keyboard",
    ),
    "computer-keyboards": (
        "wireless usb keyboard",
        "keyboard and mouse combo",
        "computer keyboard",
        "gaming keyboard",
    ),
    "stationery": (
        "stationery",
        "notebook",
        "gel pen",
        "pens",
    ),
    "tshirts": (
        "t-shirt",
        "t shirt",
        "tee",
    ),
    "shoes": (
        "sneaker",
        "sneakers",
        "running shoe",
        "shoes",
        "footwear",
    ),
    "bottles": (
        "bottle",
        "thermosteel",
        "water bottle",
    ),
    "storage-organizers": (
        "storage organizer",
        "storage organisers",
        "storage basket",
        "storage baskets",
        "organizer",
        "organiser",
    ),
    "appliance-stands": (
        "appliance roller",
        "washing machine stand",
        "refrigerator stand",
        "moving base",
        "mobile dolly",
    ),
    "tools": (
        "electric drill",
        "angle grinder",
        "grinding wheel",
        "cutting blade",
        "tool kit",
    ),
    "supplements": (
        "tablets",
        "supplement",
        "cal mag",
        "nutrilite",
        "vitamin",
    ),
    "contact-lens-care": (
        "contact lens solution",
        "lens solution",
    ),
    "dumbbells": (
        "dumbbell",
        "dumbbells",
        "weights",
    ),
    "fitness-equipment": (
        "pull up bar",
        "resistance band",
        "fitness equipment",
        "exercise equipment",
    ),
    "backpacks": (
        "backpack",
        "rucksack",
    ),
    "trolley-bags": (
        "trolley bag",
        "luggage",
        "suitcase",
    ),
    "watches": (
        "analog watch",
        "wrist watch",
    ),
    "skincare": (
        "skincare",
        "skin care",
        "face wash",
        "moisturizer",
        "serum",
    ),
    "makeup": (
        "makeup",
        "lipstick",
        "foundation",
        "mascara",
    ),
    "microwave-ovens": (
        "microwave oven",
        "microwave",
    ),
    "induction-cooktops": (
        "induction cooktop",
        "induction stove",
    ),
    "ceiling-fans": (
        "ceiling fan",
    ),
    "trimmers": (
        "trimmer",
        "grooming kit",
    ),
    "computer-mice": (
        "wireless mouse",
        "computer mouse",
    ),
    "speakers": (
        "bluetooth speaker",
        "speaker",
        "echo dot",
    ),
    "cameras": (
        "camera",
        "cctv",
        "security camera",
        "baby monitor",
    ),
}


def clean(value: object) -> str:
    return str(value or "").strip()


def slugify(value: object) -> str:
    value = clean(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)

    return value.strip("-") or "item"


def product_identity(product: dict) -> str:
    return clean(
        product.get("id")
        or product.get("sl_no")
        or product.get("asin")
    )


def page_directory(product: dict) -> Path:
    identity = product_identity(product)

    legacy_path = LEGACY_PRODUCT_PATHS.get(identity)

    if legacy_path:
        return PRODUCTS_DIR / legacy_path

    asin = clean(product.get("asin")).lower()

    suffix = asin or identity or "item"

    return PRODUCTS_DIR / (
        f"{slugify(product.get('title'))}-{slugify(suffix)}"
    )


def page_url(product: dict) -> str:
    relative = page_directory(product).relative_to(ROOT)

    return "/" + relative.as_posix() + "/"


def searchable_text(product: dict) -> str:
    return " ".join(
        [
            clean(product.get("title")),
            clean(product.get("category")),
        ]
    ).lower()


def detect_family(product: dict) -> str:
    text = searchable_text(product)

    best_family = ""
    best_score = 0

    for family, phrases in PRODUCT_FAMILIES.items():
        score = 0

        for phrase in phrases:
            phrase = phrase.lower()

            if phrase in text:
                score += len(phrase.split()) * 10
                score += len(phrase)

        if score > best_score:
            best_family = family
            best_score = score

    return best_family


def active_products(products: list[dict]) -> list[dict]:
    return [
        product
        for product in products
        if product.get("active") is not False
    ]


def related_products(
    product: dict,
    products: list[dict],
    limit: int = 4,
) -> list[dict]:
    identity = product_identity(product)
    family = detect_family(product)

    if not family:
        return []

    candidates = []

    for candidate in products:
        if product_identity(candidate) == identity:
            continue

        if detect_family(candidate) != family:
            continue

        candidates.append(candidate)

    return candidates[:limit]


def main() -> int:
    print("=" * 76)
    print("COUPON WORLD — SMART INTERNAL LINK ENGINE v2")
    print("=" * 76)

    products = json.loads(
        DB.read_text(encoding="utf-8")
    )

    products = active_products(products)

    family_counts = Counter(
        detect_family(product) or "[unclassified]"
        for product in products
    )

    pages_with_links = 0
    pages_without_links = []
    total_links = 0

    print()
    print("SMART LINK PREVIEW")
    print("-" * 76)

    shown = 0

    for product in products:
        family = detect_family(product)

        related = related_products(
            product,
            products,
        )

        if related:
            pages_with_links += 1
            total_links += len(related)
        else:
            pages_without_links.append(product)

        if shown < 25:
            print()
            print(
                f"ID {product_identity(product)} | "
                f"{clean(product.get('title'))}"
            )

            print(
                f"Family: {family or '[UNCLASSIFIED]'}"
            )

            if not related:
                print("Related: NONE")
            else:
                for candidate in related:
                    print(
                        "  -> "
                        f"ID {product_identity(candidate)} | "
                        f"{clean(candidate.get('title'))}"
                    )

                    print(
                        f"     {page_url(candidate)}"
                    )

            shown += 1

    print()
    print("=" * 76)
    print("SMART LINK SUMMARY")
    print("=" * 76)
    print(
        f"Products analysed        : {len(products)}"
    )
    print(
        f"Pages receiving links    : {pages_with_links}"
    )
    print(
        f"Pages without candidates : {len(pages_without_links)}"
    )
    print(
        f"Proposed internal links  : {total_links}"
    )

    print()
    print("PRODUCT FAMILY COVERAGE")
    print("-" * 76)

    for family, count in family_counts.most_common():
        print(
            f"{count:>3} products | {family}"
        )

    print()
    print("PAGES WITHOUT RELATED PRODUCTS")
    print("-" * 76)

    for product in pages_without_links[:30]:
        print(
            f"ID {product_identity(product):<5} | "
            f"{detect_family(product) or '[UNCLASSIFIED]':<24} | "
            f"{clean(product.get('title'))}"
        )

    print()
    print("=" * 76)
    print("SMART INTERNAL LINK STATUS: PREVIEW PASS")
    print("DATABASE CHANGED: NO")
    print("PRODUCT PAGES MODIFIED: NO")
    print("=" * 76)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
