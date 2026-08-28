#!/usr/bin/env python3

from __future__ import annotations

from evidence_offer_updater import apply_price_evidence
from price_evidence import PriceEvidence
from retailer_contract import RetailerOffer
from retailer_offer_store import (
    add_verified_offer,
    load_offer_database,
)


if __name__ == "__main__":

    base_offer = RetailerOffer(
        retailer="amazon",
        product_id="cw-mobile-test",
        retailer_product_id="B0TEST123",
        brand="Samsung",
        model="Galaxy Test",
        variant="8GB/128GB",
        title="Samsung Galaxy Test",
        price=None,
        mrp=None,
        availability="unknown",
        product_url="https://example.com/product",
        source="identity-only",
        confidence=0.95,
    )

    evidence = PriceEvidence(
        product_id="cw-mobile-test",
        retailer="amazon",
        retailer_product_id="B0TEST123",
        price=19999,
        mrp=22999,
        availability="in_stock",
        source_url="https://example.com/evidence",
        source_type="manual_verified",
        confidence=0.93,
        notes="Persistence test only",
    )

    verified_offer = apply_price_evidence(
        base_offer,
        evidence,
    )

    add_verified_offer(
        verified_offer
    )

    database = load_offer_database()

    print(
        "\nCOUPON WORLD VERIFIED OFFER STORE TEST"
    )

    print(
        "Stored offers :",
        len(database.get("offers", [])),
    )

    for offer in database.get("offers", []):

        if (
            offer.get("product_id")
            == "cw-mobile-test"
            and offer.get("retailer")
            == "amazon"
        ):
            print(
                "Stored offer  :",
                offer,
            )
