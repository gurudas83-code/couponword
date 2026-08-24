#!/usr/bin/env python3
"""
Coupon World Product Identity v2

Creates clean, research-friendly product identities from retailer titles.
This script does not overwrite the existing product database.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
PRODUCT_DB = ROOT / "coupons.json"
OUTPUT_DB = ROOT / "data" / "intelligence" / "product_identity_v2.json"


KNOWN_BRANDS = [
    "American Tourister",
    "Amazon Basics",
    "Bausch + Lomb",
    "Fire-Boltt",
    "Boult Audio",
    "Apple",
    "Samsung",
    "Redmi",
    "Xiaomi",
    "realme",
    "OnePlus",
    "Logitech",
    "Yamaha",
    "Nutrilite",
    "Amway",
    "boAt",
    "Noise",
    "Sony",
    "JBL",
    "Philips",
    "Puma",
    "ASUS",
    "Dell",
    "HP",
    "Lenovo",
    "Milton",
    "Titan",
    "Wildcraft",
    "Campus",
    "Mamaearth",
    "Bajaj",
    "Cello",
    "Strauss",
    "Kore",
    "STEMpedia",
]


VARIANT_PATTERNS = [
    r"\b\d+\s*gb\s*ram\b",
    r"\b\d+\s*gb\s*storage\b",
    r"\b\d+\s*tb\s*storage\b",
    r"\b\d+\s*gb\b",
    r"\b\d+\s*tb\b",
    r"\bblack\b",
    r"\bblue\b",
    r"\bwhite\b",
    r"\bgold\b",
    r"\bgrey\b",
    r"\bgray\b",
    r"\bred\b",
    r"\bgreen\b",
    r"\bsilver\b",
    r"\bhawaiian\b",
    r"\bhawaiian blue\b",
    r"\bmaster gold\b",
    r"\bpack of \d+\b",
]


MARKETING_START_WORDS = {
    "with",
    "featuring",
    "designed",
    "ideal",
    "upto",
    "up",
    "built",
    "lightweight",
    "premium",
    "soft",
    "all-day",
}


def load_products() -> list[dict[str, Any]]:
    data = json.loads(PRODUCT_DB.read_text(encoding="utf-8"))

    if not isinstance(data, list):
        raise ValueError("coupons.json must contain a JSON list")

    return [
        product
        for product in data
        if isinstance(product, dict)
    ]


def normalize_spaces(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def detect_brand(product: dict[str, Any]) -> str:
    stored_brand = normalize_spaces(product.get("brand"))

    if stored_brand and stored_brand.lower() != "unknown":
        return stored_brand

    title = normalize_spaces(product.get("title"))
    title_lower = title.lower()

    # Canonical Samsung Galaxy-family identity.
    # Commerce listings sometimes omit "Samsung" and begin directly
    # with Galaxy A/M/F/S/Z. These are Samsung smartphone identities,
    # not a separate "Galaxy" manufacturer.
    if re.search(
        r"\\bgalaxy\\s+(?:a|m|f|s|z)\\s*\\d",
        title_lower,
        flags=re.IGNORECASE,
    ):
        return "Samsung"

    for brand in sorted(KNOWN_BRANDS, key=len, reverse=True):
        if brand.lower() in title_lower:
            return brand

    first_word = title.split()[0] if title else ""

    return first_word


def remove_variant_text(value: str) -> str:
    cleaned = value

    # Remove complete bracketed text
    cleaned = re.sub(
        r"\([^)]*\)",
        " ",
        cleaned,
    )

    for pattern in VARIANT_PATTERNS:
        cleaned = re.sub(
            pattern,
            " ",
            cleaned,
            flags=re.IGNORECASE,
        )

    # Remove leftover brackets if any
    cleaned = cleaned.replace("(", " ").replace(")", " ")

    return normalize_spaces(cleaned)


def get_core_title(title: str) -> str:
    """
    Keep the identity-bearing part of a long retailer title.

    Product features after pipes, long commas and descriptive dashes are
    normally removed from the research name.
    """

    title = normalize_spaces(title)

    # Pipe-separated Amazon-style feature lists.
    title = title.split("|", 1)[0].strip()

    # Long feature description after an en/em dash.
    title = re.split(r"\s+[–—]\s+", title, maxsplit=1)[0].strip()

    comma_parts = [
        part.strip()
        for part in title.split(",")
        if part.strip()
    ]

    if len(comma_parts) > 1:
        first_part = comma_parts[0]

        # Preserve a short model variant, but remove long feature lists.
        if len(first_part.split()) >= 3:
            title = first_part

    return remove_variant_text(title)


def remove_brand_prefix(core_title: str, brand: str) -> str:
    if not brand:
        return core_title

    pattern = re.compile(
        rf"^\s*{re.escape(brand)}\s*",
        flags=re.IGNORECASE,
    )

    return normalize_spaces(pattern.sub("", core_title, count=1))


def trim_marketing_words(model_text: str) -> str:
    tokens = model_text.split()
    kept: list[str] = []

    for token in tokens:
        normalized = re.sub(
            r"[^a-z0-9-]",
            "",
            token.lower(),
        )

        if kept and normalized in MARKETING_START_WORDS:
            break

        kept.append(token)

        # Product research names should normally stay concise.
        if len(kept) >= 9:
            break

    return normalize_spaces(" ".join(kept))


def build_identity(
    product: dict[str, Any],
    position: int,
) -> dict[str, Any]:
    product_id = str(
        product.get("id")
        or product.get("product_id")
        or product.get("sl_no")
        or product.get("asin")
        or position
    )

    original_title = normalize_spaces(product.get("title"))
    brand = detect_brand(product)

    core_title = get_core_title(original_title)
    model = remove_brand_prefix(core_title, brand)
    model = trim_marketing_words(model)

    if not model:
        model = core_title

    search_name = normalize_spaces(
        f"{brand} {model}"
    )

    asin = normalize_spaces(product.get("asin"))

    confidence_score = 40

    if brand:
        confidence_score += 20

    if model and len(model.split()) >= 2:
        confidence_score += 20

    if asin:
        confidence_score += 15

    confidence_score = min(confidence_score, 95)

    needs_review = (
        not brand
        or not model
        or len(search_name.split()) > 10
    )

    return {
        "product_id": product_id,
        "asin": asin or None,
        "original_title": original_title,
        "brand": brand or None,
        "model": model or None,
        "search_name": search_name or original_title,
        "official_search_query": (
            f"{search_name} official specifications"
        ),
        "confidence": {
            "score": confidence_score,
            "level": (
                "high"
                if confidence_score >= 80
                else "medium"
                if confidence_score >= 60
                else "low"
            ),
        },
        "needs_review": needs_review,
    }


def main() -> int:
    products = load_products()

    identities = [
        build_identity(product, position)
        for position, product in enumerate(
            products,
            start=1,
        )
    ]

    OUTPUT_DB.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "schema_version": "2.0",
        "products_total": len(products),
        "identities": identities,
    }

    OUTPUT_DB.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    review_count = sum(
        1
        for identity in identities
        if identity["needs_review"]
    )

    print("=" * 64)
    print("COUPON WORLD PRODUCT IDENTITY v2")
    print("=" * 64)
    print("Products processed :", len(products))
    print("Needs review       :", review_count)
    print("Output             :", OUTPUT_DB)
    print("=" * 64)

    pilot_ids = {"10", "11", "13", "14", "56"}

    print("\nPILOT IDENTITIES")

    for identity in identities:
        if identity["product_id"] in pilot_ids:
            print("-" * 64)
            print("ID     :", identity["product_id"])
            print("Brand  :", identity["brand"])
            print("Model  :", identity["model"])
            print("Search :", identity["search_name"])
            print("Query  :", identity["official_search_query"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
