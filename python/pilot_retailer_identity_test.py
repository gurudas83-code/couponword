#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path

from canonical_product import CanonicalProduct
from retailer_connector_manager import RetailerConnectorManager


ROOT = Path(__file__).resolve().parent.parent
PILOT_FILE = ROOT / "data" / "pilot_canonical_products.json"


def load_products():
    data = json.loads(
        PILOT_FILE.read_text(encoding="utf-8-sig")
    )

    products = []

    for item in data.get("products", []):
        products.append(
            CanonicalProduct(
                product_id=item["product_id"],
                title=item["title"],
                brand=item["brand"],
                model=item["model"],
                variant=item.get("variant", ""),
                category=item.get("category", ""),
                identifiers=dict(item.get("identifiers") or {}),
                attributes=dict(item.get("attributes") or {}),
                source_product_id=item.get("source_product_id", ""),
                source=item.get("source", "pilot_manifest"),
                confidence=float(item.get("confidence", 0.0)),
            )
        )

    return products


def main():
    manager = RetailerConnectorManager()
    products = load_products()

    total_offers = 0

    print()
    print("=" * 80)
    print("COUPON WORLD - PILOT RETAILER IDENTITY TEST")
    print("=" * 80)

    for product in products:
        offers = manager.collect_offers(product)

        total_offers += len(offers)

        print()
        print("PRODUCT :", product.product_id)
        print("BRAND   :", product.brand)
        print("MODEL   :", product.model)
        print("VARIANT :", product.variant or "-")
        print("OFFERS  :", len(offers))

        for offer in offers:
            print(
                "  ",
                offer.retailer,
                "| ID:",
                offer.retailer_product_id,
                "| price:",
                offer.price,
                "| stock:",
                offer.availability,
            )

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("Products     :", len(products))
    print("Offers found :", total_offers)


if __name__ == "__main__":
    main()
