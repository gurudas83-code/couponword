#!/usr/bin/env python3

from __future__ import annotations

from amazon_data_provider import AmazonProductData
from offer_normalizer import normalize_offer
from retailer_contract import RetailerOffer


def amazon_product_to_offer(
    product: AmazonProductData,
    *,
    product_id: str = "",
    model: str = "",
    variant: str = "",
    availability: str = "",
    product_url: str = "",
    affiliate_url: str = "",
    confidence: float = 0.0,
) -> RetailerOffer:
    """
    Convert existing Coupon World AmazonProductData
    into the common multi-retailer RetailerOffer format.

    Extra fields are supplied only when independently verified.
    Nothing is fabricated.
    """

    raw = {
        "product_id": product_id,
        "asin": product.asin,
        "title": product.title,
        "brand": product.brand,
        "model": model,
        "variant": variant,
        "price": product.price,
        "mrp": product.mrp,
        "availability": availability,
        "product_url": product_url,
        "affiliate_url": affiliate_url,
        "source": product.source,
        "confidence": confidence,
    }

    return normalize_offer("Amazon", raw)


if __name__ == "__main__":

    sample = AmazonProductData(
        asin="B0TEST123",
        title="Samsung Galaxy Test 8GB 128GB",
        brand="Samsung",
        category="Mobiles",
        price="₹19,999",
        mrp="₹22,999",
        source="manual-verified",
    )

    offer = amazon_product_to_offer(
        sample,
        product_id="cw-test-001",
        model="Galaxy Test",
        variant="8GB/128GB",
        availability="In Stock",
        product_url="https://www.amazon.in/example",
        confidence=0.95,
    )

    print("\nAMAZON ADAPTER TEST")
    print(offer.to_dict())
