#!/usr/bin/env python3

from __future__ import annotations

from retailer_contract import RetailerOffer
from retailer_offer_store import load_offer_database
from multi_retailer_engine import compare_offers


def load_product_offers(
    product_id: str,
) -> list[RetailerOffer]:

    data = load_offer_database()

    offers = []

    for record in data.get("offers", []):

        if record.get("product_id") != product_id:
            continue

        offers.append(
            RetailerOffer(
                retailer=record.get("retailer", ""),
                product_id=record.get("product_id", ""),
                retailer_product_id=record.get(
                    "retailer_product_id",
                    "",
                ),
                brand=record.get("brand", ""),
                model=record.get("model", ""),
                variant=record.get("variant", ""),
                title=record.get("title", ""),
                price=record.get("price"),
                mrp=record.get("mrp"),
                currency=record.get(
                    "currency",
                    "INR",
                ),
                availability=record.get(
                    "availability",
                    "unknown",
                ),
                product_url=record.get(
                    "product_url",
                    "",
                ),
                affiliate_url=record.get(
                    "affiliate_url",
                    "",
                ),
                source=record.get(
                    "source",
                    "",
                ),
                confidence=float(
                    record.get(
                        "confidence",
                        0.0,
                    )
                ),
                last_checked=record.get(
                    "last_checked",
                    "",
                ),
                metadata=record.get(
                    "metadata",
                    {},
                ),
            )
        )

    return offers


if __name__ == "__main__":

    product_id = "cw-mobile-72"

    offers = load_product_offers(
        product_id
    )

    print(
        "\nSTORED MULTI-RETAILER COMPARISON"
    )

    print("Product :", product_id)
    print("Offers  :", len(offers))

    for offer in offers:
        print()
        print("Retailer :", offer.retailer)
        print("Price    :", offer.price)
        print("Stock    :", offer.availability)
        print("Checked  :", offer.last_checked)
        print("Source   :", offer.source)

    comparison = compare_offers(
        offers
    )

    print("\nCOMPARISON RESULT")
    print(comparison)
