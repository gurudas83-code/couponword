#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent

REGISTRY_FILE = (
    ROOT
    / "data"
    / "retailer_product_registry.json"
)


def load_registry() -> dict[str, Any]:

    if not REGISTRY_FILE.exists():
        return {
            "version": 1,
            "products": {},
        }

    return json.loads(
        REGISTRY_FILE.read_text(
            encoding="utf-8-sig"
        )
    )


def save_registry(
    data: dict[str, Any],
) -> None:

    REGISTRY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REGISTRY_FILE.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def register_retailer_product(
    *,
    product_id: str,
    retailer: str,
    retailer_product_id: str,
    product_url: str = "",
    confidence: float = 0.0,
    source: str = "",
) -> None:

    product_id = product_id.strip()
    retailer = retailer.strip().lower()
    retailer_product_id = (
        retailer_product_id.strip()
    )

    if not product_id:
        raise ValueError(
            "Canonical product_id required."
        )

    if not retailer:
        raise ValueError(
            "Retailer required."
        )

    if not retailer_product_id:
        raise ValueError(
            "Retailer product ID required."
        )

    data = load_registry()

    products = data.setdefault(
        "products",
        {},
    )

    product_record = products.setdefault(
        product_id,
        {},
    )

    product_record[retailer] = {
        "retailer_product_id":
            retailer_product_id,
        "product_url":
            product_url,
        "confidence":
            confidence,
        "source":
            source,
    }

    save_registry(data)


def get_retailer_product(
    product_id: str,
    retailer: str,
) -> dict[str, Any] | None:

    data = load_registry()

    return (
        data
        .get("products", {})
        .get(product_id, {})
        .get(retailer.lower())
    )


if __name__ == "__main__":

    register_retailer_product(
        product_id="cw-mobile-72",
        retailer="amazon",
        retailer_product_id="B0FDBB2VRC",
        product_url=(
            "https://www.amazon.in/dp/"
            "B0FDBB2VRC"
        ),
        confidence=0.95,
        source="couponworld-existing-data",
    )

    record = get_retailer_product(
        "cw-mobile-72",
        "amazon",
    )

    print(
        "\nCOUPON WORLD "
        "RETAILER PRODUCT REGISTRY"
    )

    print("Product :", "cw-mobile-72")
    print("Amazon  :", record)
