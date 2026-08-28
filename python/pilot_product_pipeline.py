#!/usr/bin/env python3

from __future__ import annotations

from amazon_data_provider import AmazonProductData
from amazon_retailer_adapter import amazon_product_to_offer
from canonical_product import CanonicalProduct
from retailer_offer_store import add_verified_offer


def build_samsung_m36_product() -> CanonicalProduct:
    return CanonicalProduct(
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
        source="couponworld",
        confidence=0.95,
    )


def build_amazon_offer(
    product: CanonicalProduct,
):
    asin = product.identifiers.get("amazon_asin", "")

    amazon_product = AmazonProductData(
        asin=asin,
        title=(
            "Samsung Galaxy M36 5G Mobile "
            "(Velvet Black, 6GB RAM, 128GB Storage)"
        ),
        brand=product.brand,
        category=product.category,
        source="couponworld-existing-data",
    )

    return amazon_product_to_offer(
        amazon_product,
        product_id=product.product_id,
        model=product.model,
        variant=product.variant,
        availability="unknown",
        product_url=(
            "https://www.amazon.in/dp/"
            f"{asin}?tag=guru0906-21"
        ),
        confidence=0.95,
    )


if __name__ == "__main__":
    product = build_samsung_m36_product()
    offer = build_amazon_offer(product)

    print("\nCANONICAL PRODUCT")
    print(product.to_dict())

    print("\nAMAZON OFFER")
    print(offer.to_dict())

    if offer.price is None:
        print("\nPRICE STATUS")
        print("No verified price available - offer not stored as verified price.")

    else:
        add_verified_offer(offer)
        print("\nOffer saved.")
