#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class CanonicalProduct:
    product_id: str

    title: str
    brand: str
    model: str
    variant: str

    category: str = ""

    identifiers: dict[str, str] = field(default_factory=dict)
    attributes: dict[str, Any] = field(default_factory=dict)

    source_product_id: str = ""
    source: str = "couponworld"

    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


if __name__ == "__main__":

    product = CanonicalProduct(
        product_id="cw-mobile-72",
        title="Samsung Galaxy M36 5G",
        brand="Samsung",
        model="Galaxy M36 5G",
        variant="6GB/128GB",
        category="Mobiles",
        identifiers={
            "amazon_asin": "B0FDBB2VRC",
        },
        attributes={
            "ram": "6GB",
            "storage": "128GB",
            "color": "Velvet Black",
        },
        source_product_id="72",
        confidence=0.95,
    )

    print("\nCANONICAL PRODUCT TEST")
    print(product.to_dict())
