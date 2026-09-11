#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class RetailerOffer:
    retailer: str
    product_id: str = ""
    retailer_product_id: str = ""

    brand: str = ""
    model: str = ""
    variant: str = ""

    title: str = ""

    price: float | None = None
    mrp: float | None = None
    currency: str = "INR"

    availability: str = "unknown"

    product_url: str = ""
    affiliate_url: str = ""

    source: str = ""
    confidence: float = 0.0

    last_checked: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_retailer_name(value: str) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


def normalize_availability(value: str) -> str:
    text = str(value or "").strip().lower()

    if text in {
        "in stock",
        "instock",
        "available",
        "in_stock",
    }:
        return "in_stock"

    if text in {
        "out of stock",
        "outofstock",
        "unavailable",
        "out_of_stock",
    }:
        return "out_of_stock"

    return "unknown"


if __name__ == "__main__":
    sample = RetailerOffer(
        retailer="Amazon",
        product_id="cw-test-001",
        retailer_product_id="B0TEST123",
        brand="Samsung",
        model="Galaxy Test",
        variant="8GB/128GB",
        title="Samsung Galaxy Test 8GB 128GB",
        price=19999,
        availability="in_stock",
        source="manual",
        confidence=0.95,
    )

    print(sample.to_dict())
