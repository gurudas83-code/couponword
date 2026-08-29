#!/usr/bin/env python3

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from evidence_freshness import freshness_status
from multi_retailer_engine import compare_offers
from retailer_contract import RetailerOffer
from stored_offer_comparison import load_product_offers


ROOT = Path(__file__).resolve().parent.parent
PILOT_FILE = ROOT / "data" / "pilot_canonical_products.json"
OUTPUT_FILE = ROOT / "data" / "multi_retailer_public.json"


def to_offer(value) -> RetailerOffer:
    if isinstance(value, RetailerOffer):
        return value

    if isinstance(value, dict):
        return RetailerOffer(**value)

    raise TypeError(
        f"Unsupported offer type: {type(value).__name__}"
    )


def public_offer(value) -> dict:
    offer = to_offer(value)

    return {
        "retailer": offer.retailer,
        "retailer_product_id": offer.retailer_product_id,
        "price": offer.price,
        "mrp": offer.mrp,
        "currency": offer.currency,
        "availability": offer.availability,
        "freshness": freshness_status(offer),
        "product_url": offer.product_url,
        "affiliate_url": offer.affiliate_url,
        "last_checked": offer.last_checked,
        "source": offer.source,
        "confidence": offer.confidence,
    }


def main():
    pilot = json.loads(
        PILOT_FILE.read_text(encoding="utf-8-sig")
    )

    products = []

    for product in pilot.get("products", []):
        product_id = product["product_id"]

        offers = load_product_offers(product_id)
        result = compare_offers(offers)

        matched_offers = [
            public_offer(item)
            for item in result["identity_matched_offers"]
        ]

        best_offer = result.get("best_offer")

        products.append(
            {
                "product_id": product_id,
                "title": product["title"],
                "brand": product["brand"],
                "model": product["model"],
                "variant": product.get("variant", ""),
                "attributes": product.get("attributes", {}),
                "status": result["status"],
                "identity_matched_offer_count":
                    result["identity_matched_offer_count"],
                "comparable_offer_count":
                    result["comparable_offer_count"],
                "best_offer":
                    public_offer(best_offer)
                    if best_offer
                    else None,
                "price_gap": result["price_gap"],
                "offers": matched_offers,
            }
        )

    payload = {
        "version": 1,
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "products": products,
    }

    OUTPUT_FILE.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 72)
    print("MULTI-RETAILER PUBLIC DATA BUILT")
    print("=" * 72)
    print("Products :", len(products))
    print(
        "Generated:",
        payload["generated_at"],
    )
    print("Output   :", OUTPUT_FILE)

    for product in products:
        print()
        print(product["product_id"])
        print(
            "Offers     :",
            product["identity_matched_offer_count"],
        )
        print(
            "Comparable :",
            product["comparable_offer_count"],
        )

        best = product["best_offer"]

        if best:
            print(
                "Best       :",
                best["retailer"],
                best["price"],
            )
        else:
            print("Best       : None")


if __name__ == "__main__":
    main()
