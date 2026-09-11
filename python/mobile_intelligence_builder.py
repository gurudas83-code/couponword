#!/usr/bin/env python3

"""
Coupon World - Mobile Intelligence Builder

Phase 1 contract:
- Load structured India mobile-universe seed records.
- Validate universe-level contract.
- Validate identity anchors conservatively.
- Classify records for future intelligence enrichment.
- Never invent canonical product IDs.
- Never perform live web/network calls.
- Never write to the Mobile Intelligence Repository.

This module is intentionally dry-run only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


BUILDER_VERSION = "1.1"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SEED_FILE = PROJECT_ROOT / "data" / "mobile_universe_seed.json"

EXPECTED_SCHEMA_VERSION = "1.0"
EXPECTED_MARKET = "IN"
EXPECTED_CATEGORY = "smartphone"

STATUS_READY_FOR_ENRICHMENT = "READY_FOR_ENRICHMENT"
STATUS_NEEDS_VARIANT = "NEEDS_VARIANT"
STATUS_NEEDS_IDENTITY = "NEEDS_IDENTITY"
STATUS_INVALID = "INVALID"


@dataclass(frozen=True)
class MobileUniverseSeed:
    """
    Candidate mobile model/variant entering the intelligence pipeline.

    canonical_product_id must only be supplied when an existing trusted
    canonical identity already exists. The builder never generates one.
    """

    brand: str
    model: str
    variant: str = ""
    ram_gb: int | None = None
    storage_gb: int | None = None
    canonical_product_id: str = ""
    source: str = ""
    source_reference: str = ""


@dataclass
class BuilderAssessment:
    seed: MobileUniverseSeed
    status: str
    reasons: list[str] = field(default_factory=list)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def positive_int_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None

    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None

    return parsed if parsed > 0 else None


def load_universe_seed(
    path: Path = DEFAULT_SEED_FILE,
) -> dict[str, Any]:
    """
    Load and validate the universe-level JSON contract.

    This validates structure only. It does not assert that any product
    identity or specification is trustworthy.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"mobile universe seed not found: {path}"
        )

    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        raise ValueError(
            "mobile universe seed root must be a JSON object"
        )

    schema_version = clean_text(
        payload.get("schema_version")
    )
    market = clean_text(payload.get("market")).upper()
    category = clean_text(payload.get("category")).lower()
    source_method = clean_text(
        payload.get("source_method")
    )
    products = payload.get("products")

    if schema_version != EXPECTED_SCHEMA_VERSION:
        raise ValueError(
            "unsupported mobile universe schema_version: "
            f"{schema_version or 'missing'}"
        )

    if market != EXPECTED_MARKET:
        raise ValueError(
            f"unexpected market: {market or 'missing'}"
        )

    if category != EXPECTED_CATEGORY:
        raise ValueError(
            f"unexpected category: {category or 'missing'}"
        )

    if not source_method:
        raise ValueError(
            "mobile universe source_method missing"
        )

    if not isinstance(products, list):
        raise ValueError(
            "mobile universe products must be a list"
        )

    return payload


def seed_from_dict(
    record: dict[str, Any],
) -> MobileUniverseSeed:
    """
    Normalize a seed record without manufacturing identity.
    """

    return MobileUniverseSeed(
        brand=clean_text(record.get("brand")),
        model=clean_text(record.get("model")),
        variant=clean_text(record.get("variant")),
        ram_gb=positive_int_or_none(record.get("ram_gb")),
        storage_gb=positive_int_or_none(
            record.get("storage_gb")
        ),
        canonical_product_id=clean_text(
            record.get("canonical_product_id")
        ),
        source=clean_text(record.get("source")),
        source_reference=clean_text(
            record.get("source_reference")
        ),
    )


def assess_seed(
    seed: MobileUniverseSeed,
) -> BuilderAssessment:
    reasons: list[str] = []

    if not seed.brand:
        reasons.append("brand missing")

    if not seed.model:
        reasons.append("model missing")

    if not seed.source:
        reasons.append("seed source missing")

    if not seed.source_reference:
        reasons.append("seed source reference missing")

    if not seed.brand or not seed.model:
        return BuilderAssessment(
            seed=seed,
            status=STATUS_INVALID,
            reasons=reasons,
        )

    if not seed.canonical_product_id:
        reasons.append(
            "trusted canonical product identity not yet resolved"
        )

    if seed.ram_gb is None or seed.storage_gb is None:
        reasons.append(
            "exact RAM/storage variant not yet established"
        )

    if not seed.canonical_product_id:
        return BuilderAssessment(
            seed=seed,
            status=STATUS_NEEDS_IDENTITY,
            reasons=reasons,
        )

    if seed.ram_gb is None or seed.storage_gb is None:
        return BuilderAssessment(
            seed=seed,
            status=STATUS_NEEDS_VARIANT,
            reasons=reasons,
        )

    return BuilderAssessment(
        seed=seed,
        status=STATUS_READY_FOR_ENRICHMENT,
        reasons=reasons,
    )


def assess_universe(
    records: Iterable[dict[str, Any]],
) -> list[BuilderAssessment]:
    assessments: list[BuilderAssessment] = []

    for record in records:
        if not isinstance(record, dict):
            assessments.append(
                BuilderAssessment(
                    seed=MobileUniverseSeed(
                        brand="",
                        model="",
                    ),
                    status=STATUS_INVALID,
                    reasons=[
                        "product seed record must be an object"
                    ],
                )
            )
            continue

        assessments.append(
            assess_seed(seed_from_dict(record))
        )

    return assessments


def print_assessment(
    item: BuilderAssessment,
) -> None:
    seed = item.seed

    print()
    print("Brand        :", seed.brand or "NONE")
    print("Model        :", seed.model or "NONE")
    print("Variant      :", seed.variant or "NONE")
    print(
        "RAM          :",
        seed.ram_gb if seed.ram_gb is not None else "UNKNOWN",
    )
    print(
        "Storage      :",
        (
            seed.storage_gb
            if seed.storage_gb is not None
            else "UNKNOWN"
        ),
    )
    print(
        "Canonical ID :",
        seed.canonical_product_id or "UNRESOLVED",
    )
    print("Source       :", seed.source or "NONE")
    print(
        "Source ref   :",
        seed.source_reference or "NONE",
    )
    print("Status       :", item.status)

    if item.reasons:
        for reason in item.reasons:
            print("Reason       :", reason)
    else:
        print(
            "Reason       : identity + variant anchors present"
        )


def dry_run(
    payload: dict[str, Any],
) -> list[BuilderAssessment]:
    products = payload["products"]
    assessments = assess_universe(products)

    print("=" * 72)
    print(
        "COUPON WORLD VERIFIED MOBILE INTELLIGENCE BUILDER"
    )
    print("=" * 72)
    print("Builder version   :", BUILDER_VERSION)
    print("Mode              : DRY RUN")
    print("Market            :", payload["market"])
    print("Category          :", payload["category"])
    print(
        "Generated at      :",
        payload.get("generated_at") or "NOT SET",
    )
    print(
        "Source method     :",
        payload["source_method"],
    )
    print("Live network calls:", "NO")
    print("Repository write  :", "NO")
    print("Synthetic IDs     :", "NO")
    print("Seed records      :", len(assessments))

    counts: dict[str, int] = {}

    for item in assessments:
        counts[item.status] = (
            counts.get(item.status, 0) + 1
        )
        print_assessment(item)

    print()
    print("-" * 72)
    print("SUMMARY")

    for status in (
        STATUS_READY_FOR_ENRICHMENT,
        STATUS_NEEDS_VARIANT,
        STATUS_NEEDS_IDENTITY,
        STATUS_INVALID,
    ):
        print(
            f"{status:24}:",
            counts.get(status, 0),
        )

    print("Live network calls      : NO")
    print("Repository write        : NO")
    print("Synthetic IDs           : NO")

    return assessments


def main() -> int:
    try:
        payload = load_universe_seed()
        dry_run(payload)
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
    ) as exc:
        print("MOBILE INTELLIGENCE BUILDER: FAIL")
        print("Reason:", exc)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())