#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mobile_product_dna import (
    EvidenceValue,
    MobileProductDNA,
    validate_mobile_dna,
)


ROOT = Path(__file__).resolve().parent.parent
FEATURE_DB = ROOT / "data" / "intelligence" / "product_features.json"


def load_feature_database() -> dict[str, Any]:
    return json.loads(
        FEATURE_DB.read_text(encoding="utf-8-sig")
    )


def evidence_value(
    feature: dict[str, Any] | None,
    *,
    transform=None,
) -> EvidenceValue:
    if not isinstance(feature, dict):
        return EvidenceValue()

    value = feature.get("value")

    if transform is not None:
        try:
            value = transform(value)
        except (TypeError, ValueError, KeyError):
            value = None

    return EvidenceValue(
        value=value,
        source=feature.get("source"),
        confidence=str(feature.get("confidence") or "unknown"),
        verified=feature.get("verified") is True,
    )


def amount(value: Any) -> Any:
    if isinstance(value, dict):
        return value.get("amount")
    return value


def camera_mp(value: Any) -> Any:
    if not isinstance(value, dict):
        return None
    return value.get("highest_mp")


def supports_5g(value: Any) -> bool | None:
    if not isinstance(value, list):
        return None

    normalized = {str(item).upper() for item in value}

    if "5G" in normalized:
        return True

    return None


def build_mobile_dna(product: dict[str, Any]) -> MobileProductDNA:
    features = product.get("features", {})

    if not isinstance(features, dict):
        features = {}

    dna = MobileProductDNA(
        product_id=str(product.get("product_id") or ""),
    )

    brand = product.get("brand")
    if brand:
        dna.brand = EvidenceValue(
            value=brand,
            source="product_features_record",
            confidence="medium",
            verified=False,
        )

    dna.ram_gb = evidence_value(
        features.get("ram"),
        transform=amount,
    )

    dna.storage_gb = evidence_value(
        features.get("storage"),
        transform=amount,
    )

    dna.display_size_inch = evidence_value(
        features.get("display_size"),
        transform=amount,
    )

    dna.refresh_rate_hz = evidence_value(
        features.get("refresh_rate"),
        transform=amount,
    )

    dna.chipset = evidence_value(
        features.get("processor"),
    )

    dna.main_camera_mp = evidence_value(
        features.get("camera"),
        transform=camera_mp,
    )

    dna.supports_5g = evidence_value(
        features.get("connectivity"),
        transform=supports_5g,
    )

    # IMPORTANT:
    # features["capacity"] is deliberately ignored.
    # Current feature extraction can misread "5G" as "5 g".
    # Battery capacity must come from explicit battery evidence later.

    return dna


def is_mobile(product: dict[str, Any]) -> bool:
    category = str(product.get("category") or "").lower()
    subcategory = str(product.get("subcategory") or "").lower()

    return (
        "mobile" in category
        or "smartphone" in category
        or "mobile" in subcategory
        or "smartphone" in subcategory
    )


def main() -> int:
    payload = load_feature_database()

    products = [
        product
        for product in payload.get("products", [])
        if isinstance(product, dict) and is_mobile(product)
    ]

    print("=" * 72)
    print("COUPON WORLD MOBILE DNA ADAPTER")
    print("=" * 72)
    print("Mobile records :", len(products))

    failed = 0

    for product in products:
        dna = build_mobile_dna(product)
        errors = validate_mobile_dna(dna)

        if errors:
            failed += 1

        populated = [
            name
            for name, item in dna.__dict__.items()
            if isinstance(item, EvidenceValue)
            and item.value is not None
        ]

        print()
        print("ID        :", dna.product_id)
        print("Title     :", product.get("title"))
        print("DNA fields:", ", ".join(populated) or "None")
        print("Validation:", "PASS" if not errors else "FAIL")

        if errors:
            for error in errors:
                print("  -", error)

    print()
    print("-" * 72)
    print("Validated :", len(products) - failed)
    print("Failed    :", failed)
    print("DB write  : NO")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
