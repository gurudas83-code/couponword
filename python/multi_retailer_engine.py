#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

from retailer_contract import RetailerOffer
from offer_normalizer import normalize_offer
from product_matcher import match_offers


def compare_offers(
    offers: Iterable[RetailerOffer],
) -> dict:

    offers = list(offers)

    if not offers:
        return {
            "status": "no_offers",
            "offers": [],
        }

    anchor = offers[0]

    matched: list[RetailerOffer] = []
    rejected: list[dict] = []

    for offer in offers:
        if offer is anchor:
            matched.append(offer)
            continue

        result = match_offers(anchor, offer)

        if result["same_product"]:
            matched.append(offer)
        else:
            rejected.append(
                {
                    "offer": asdict(offer),
                    "reason": "product_or_variant_mismatch",
                    "match_result": result,
                }
            )

    available = [
        offer
        for offer in matched
        if offer.availability == "in_stock"
        and offer.price is not None
    ]

    available.sort(
        key=lambda offer: offer.price
    )

    best_offer = available[0] if available else None

    price_gap = None

    if len(available) >= 2:
        price_gap = round(
            available[-1].price - available[0].price,
            2,
        )

    return {
        "status": "ok",
        "matched_offer_count": len(matched),
        "rejected_offer_count": len(rejected),

        "best_offer": (
            asdict(best_offer)
            if best_offer
            else None
        ),

        "price_gap": price_gap,

        "matched_offers": [
            asdict(offer)
            for offer in available
        ],

        "rejected_offers": rejected,
    }


if __name__ == "__main__":

    amazon = normalize_offer(
        "Amazon",
        {
            "asin": "B0TEST123",
            "title": "Samsung Galaxy Test 8GB 128GB",
            "brand": "Samsung",
            "model": "Galaxy Test",
            "variant": "8GB/128GB",
            "price": "₹19,999",
            "availability": "In Stock",
            "source": "manual",
            "confidence": 0.95,
        },
    )

    flipkart = normalize_offer(
        "Flipkart",
        {
            "fsn": "MOBTEST456",
            "name": "Samsung Galaxy Test 8 GB 128 GB",
            "brand": "Samsung",
            "model": "Galaxy Test",
            "configuration": "8GB/128GB",
            "selling_price": "18,999",
            "stock": "Available",
            "source": "manual",
            "confidence": 0.93,
        },
    )

    wrong_variant = normalize_offer(
        "Flipkart",
        {
            "fsn": "MOBTEST999",
            "name": "Samsung Galaxy Test 6 GB 128 GB",
            "brand": "Samsung",
            "model": "Galaxy Test",
            "configuration": "6GB/128GB",
            "selling_price": "17,999",
            "stock": "Available",
            "source": "manual",
            "confidence": 0.92,
        },
    )

    result = compare_offers(
        [
            amazon,
            flipkart,
            wrong_variant,
        ]
    )

    print("\nMULTI-RETAILER COMPARISON")
    print(result)

    if result["best_offer"]:
        best = result["best_offer"]

        print("\nBEST BUYING OPTION")
        print(
            best["retailer"],
            "₹",
            best["price"],
        )

        print(
            "PRICE GAP:",
            result["price_gap"],
        )
