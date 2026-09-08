#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mobile_dna_adapter import (
    build_mobile_dna,
    is_mobile,
    load_feature_database,
)
from mobile_product_dna import (
    EvidenceValue,
    MobileProductDNA,
    validate_mobile_dna,
)


@dataclass
class PopulationAssessment:
    product_id: str
    title: str
    asin: str
    status: str
    populated_fields: list[str]
    verified_fields: list[str]
    reasons: list[str]


def populated_dna_fields(
    dna: MobileProductDNA,
) -> list[str]:
    return [
        name
        for name, item in dna.__dict__.items()
        if isinstance(item, EvidenceValue)
        and item.value is not None
    ]


def verified_dna_fields(
    dna: MobileProductDNA,
) -> list[str]:
    return [
        name
        for name, item in dna.__dict__.items()
        if isinstance(item, EvidenceValue)
        and item.value is not None
        and item.verified is True
    ]


def assess_product(
    product: dict[str, Any],
) -> PopulationAssessment:
    dna = build_mobile_dna(product)
    errors = validate_mobile_dna(dna)

    product_id = str(
        product.get("product_id") or ""
    ).strip()

    title = str(
        product.get("title") or ""
    ).strip()

    asin = str(
        product.get("asin") or ""
    ).strip().upper()

    populated = populated_dna_fields(dna)
    verified = verified_dna_fields(dna)

    reasons: list[str] = []

    if errors:
        reasons.extend(errors)

    if not asin:
        reasons.append(
            "exact retailer identity not available"
        )

    if not populated:
        reasons.append(
            "no usable mobile DNA fields"
        )

    if not verified:
        reasons.append(
            "no verified DNA fields"
        )

    if errors or not populated:
        status = "INSUFFICIENT_EVIDENCE"
    elif not asin:
        status = "NEEDS_IDENTITY"
    elif not verified:
        status = "BOOTSTRAP_ONLY"
    else:
        status = "READY"

    return PopulationAssessment(
        product_id=product_id,
        title=title,
        asin=asin,
        status=status,
        populated_fields=populated,
        verified_fields=verified,
        reasons=reasons,
    )


def main() -> int:
    payload = load_feature_database()

    products = [
        product
        for product in payload.get("products", [])
        if isinstance(product, dict)
        and is_mobile(product)
    ]

    assessments = [
        assess_product(product)
        for product in products
    ]

    print("=" * 72)
    print("COUPON WORLD MOBILE REPOSITORY POPULATION DRY RUN")
    print("=" * 72)
    print("Mobile candidates :", len(assessments))
    print("Repository write  : NO")

    counts: dict[str, int] = {}

    for item in assessments:
        counts[item.status] = (
            counts.get(item.status, 0) + 1
        )

        print()
        print("ID       :", item.product_id)
        print("Title    :", item.title)
        print("ASIN     :", item.asin or "NONE")
        print("Status   :", item.status)
        print(
            "DNA      :",
            ", ".join(item.populated_fields)
            or "NONE",
        )
        print(
            "Verified :",
            ", ".join(item.verified_fields)
            or "NONE",
        )

        for reason in item.reasons:
            print("Reason   :", reason)

    print()
    print("-" * 72)
    print("SUMMARY")

    for status in (
        "READY",
        "BOOTSTRAP_ONLY",
        "NEEDS_IDENTITY",
        "INSUFFICIENT_EVIDENCE",
    ):
        print(
            f"{status:22}:",
            counts.get(status, 0),
        )

    print("Repository write       : NO")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())