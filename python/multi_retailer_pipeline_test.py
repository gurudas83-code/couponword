#!/usr/bin/env python3

from __future__ import annotations

from canonical_product import CanonicalProduct
from multi_retailer_engine import compare_offers
from product_matcher import match_offers
from retailer_connector_manager import RetailerConnectorManager


def build_product() -> CanonicalProduct:
    return CanonicalProduct(
        product_id="cw-mobile-72",
        title="Samsung Galaxy M36 5G",
        brand="Samsung",
        model="Galaxy M36 5G",
        variant="6GB/128GB",
        category="Mobiles",
        identifiers={},
        attributes={
            "ram": "6GB",
            "storage": "128GB",
            "color": "Velvet Black",
        },
        source_product_id="72",
        confidence=0.95,
    )


if __name__ == "__main__":

    product = build_product()

    manager = RetailerConnectorManager()

    offers = manager.collect_offers(product)

    print("\nMULTI RETAILER PIPELINE TEST")
    print("Product :", product.product_id)
    print("Offers  :", len(offers))

    for offer in offers:
        print()
        print("Retailer :", offer.retailer)
        print("ID       :", offer.retailer_product_id)
        print("Model    :", offer.model)
        print("Variant  :", offer.variant)
        print("Price    :", offer.price)
        print("Stock    :", offer.availability)

    if len(offers) >= 2:

        print("\nSAME PRODUCT CHECK")

        match = match_offers(
            offers[0],
            offers[1],
        )

        print(match)

    print("\nPRICE COMPARISON")

    comparison = compare_offers(offers)

    print(comparison)
