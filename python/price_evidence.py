#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone


@dataclass(slots=True)
class PriceEvidence:
    product_id: str
    retailer: str
    retailer_product_id: str

    price: float | None = None
    mrp: float | None = None
    availability: str = "unknown"

    source_url: str = ""
    source_type: str = ""

    observed_at: str = ""
    confidence: float = 0.0

    notes: str = ""

    def __post_init__(self):

        if not self.observed_at:
            self.observed_at = datetime.now(
                timezone.utc
            ).isoformat()

        self.retailer = (
            self.retailer
            .strip()
            .lower()
        )

        self.availability = (
            self.availability
            .strip()
            .lower()
        )

        if self.price is not None:
            self.price = float(self.price)

            if self.price <= 0:
                raise ValueError(
                    "Price must be greater than zero."
                )

        if self.mrp is not None:
            self.mrp = float(self.mrp)

            if self.mrp <= 0:
                raise ValueError(
                    "MRP must be greater than zero."
                )

        if self.price is not None and self.mrp is not None:
            if self.price > self.mrp:
                raise ValueError(
                    "Price cannot exceed MRP."
                )

        if not self.product_id:
            raise ValueError(
                "Canonical product_id required."
            )

        if not self.retailer:
            raise ValueError(
                "Retailer required."
            )

        if not self.retailer_product_id:
            raise ValueError(
                "Retailer product identifier required."
            )

        if not self.source_url:
            raise ValueError(
                "Evidence source URL required."
            )

    def to_dict(self) -> dict:
        return asdict(self)


if __name__ == "__main__":

    evidence = PriceEvidence(
        product_id="cw-mobile-test",
        retailer="amazon",
        retailer_product_id="B0TEST123",
        price=19999,
        mrp=22999,
        availability="in_stock",
        source_url="https://example.com/test",
        source_type="manual_verified",
        confidence=0.95,
        notes="Test evidence only",
    )

    print("\nCOUPON WORLD PRICE EVIDENCE")
    print(evidence.to_dict())
