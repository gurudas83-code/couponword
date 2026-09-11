#!/usr/bin/env python3

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mobile_product_dna import MobileProductDNA, validate_mobile_dna


ROOT = Path(__file__).resolve().parent.parent

REPOSITORY_FILE = (
    ROOT
    / "data"
    / "mobile_intelligence_repository.json"
)

SCHEMA_VERSION = "1.0"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def empty_repository() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": None,
        "products": {},
    }


def load_repository() -> dict[str, Any]:
    if not REPOSITORY_FILE.exists():
        return empty_repository()

    try:
        data = json.loads(
            REPOSITORY_FILE.read_text(
                encoding="utf-8-sig"
            )
        )
    except Exception:
        return empty_repository()

    if not isinstance(data, dict):
        return empty_repository()

    products = data.get("products")

    if not isinstance(products, dict):
        data["products"] = {}

    data.setdefault(
        "schema_version",
        SCHEMA_VERSION,
    )
    data.setdefault("updated_at", None)

    return data


def save_repository(
    data: dict[str, Any],
) -> None:
    REPOSITORY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data["schema_version"] = SCHEMA_VERSION
    data["updated_at"] = utc_now_iso()

    temp = REPOSITORY_FILE.with_suffix(".tmp")

    temp.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    temp.replace(REPOSITORY_FILE)


def save_mobile_dna(
    dna: MobileProductDNA,
) -> tuple[bool, str]:
    errors = validate_mobile_dna(dna)

    if errors:
        return (
            False,
            "; ".join(errors),
        )

    product_id = str(
        dna.product_id or ""
    ).strip()

    if not product_id:
        return False, "product_id is required"

    data = load_repository()

    products = data.setdefault(
        "products",
        {},
    )

    existing = products.get(product_id)

    created_at = utc_now_iso()

    if isinstance(existing, dict):
        created_at = (
            existing.get("created_at")
            or created_at
        )

    products[product_id] = {
        "product_id": product_id,
        "canonical_product_id": (
            dna.canonical_product_id
            or product_id
        ),
        "dna": dna.to_dict(),
        "created_at": created_at,
        "updated_at": utc_now_iso(),
    }

    save_repository(data)

    return True, "mobile DNA saved"


def get_mobile_record(
    product_id: str,
) -> dict[str, Any] | None:
    product_id = str(
        product_id or ""
    ).strip()

    if not product_id:
        return None

    data = load_repository()

    record = (
        data
        .get("products", {})
        .get(product_id)
    )

    if not isinstance(record, dict):
        return None

    return dict(record)


def get_mobile_dna_dict(
    product_id: str,
) -> dict[str, Any] | None:
    record = get_mobile_record(product_id)

    if not record:
        return None

    dna = record.get("dna")

    if not isinstance(dna, dict):
        return None

    return dict(dna)


def list_mobile_records() -> list[dict[str, Any]]:
    data = load_repository()
    products = data.get("products", {})

    if not isinstance(products, dict):
        return []

    return [
        dict(record)
        for record in products.values()
        if isinstance(record, dict)
    ]


if __name__ == "__main__":
    print("MOBILE INTELLIGENCE REPOSITORY")
    print("File      :", REPOSITORY_FILE)
    print("Records   :", len(list_mobile_records()))
    print("DB write  : NO")
