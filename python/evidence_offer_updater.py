#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import replace

from price_evidence import PriceEvidence
from retailer_contract import RetailerOffer


def apply_price_evidence(
    offer: RetailerOffer,
    evidence: PriceEvidence,
) -> RetailerOffer:

    if offer.product_id != evidence.product_id:
        raise ValueError(
            "Canonical product_id mismatch."
        )

    if (
        offer.retailer.strip().lower()
        != evidence.retailer.strip().lower()
    ):
        raise ValueError(
            "Retailer mismatch."
        )

    if (
        offer.retailer_product_id
        != evidence.retailer_product_id
    ):
        raise ValueError(
            "Retailer product identifier mismatch."
        )

    return replace(
        offer,
        price=evidence.price,
        mrp=evidence.mrp,
        availability=evidence.availability,
        source=evidence.source_type,
        confidence=min(
            offer.confidence,
            evidence.confidence,
        ),
        last_checked=evidence.observed_at,
        metadata={
            **offer.metadata,
            "evidence_source_url":
                evidence.source_url,
            "evidence_source_type":
                evidence.source_type,
            "evidence_observed_at":
                evidence.observed_at,
            "evidence_notes":
                evidence.notes,
        },
    )


if __name__ == "__main__":

    offer = RetailerOffer(
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
        notes="Test evidence only",
    )

    updated = apply_price_evidence(
        offer,
        evidence,
    )

    print(
        "\nCOUPON WORLD EVIDENCE → OFFER"
    )

    print("Before price :", offer.price)
    print("After price  :", updated.price)
    print("MRP          :", updated.mrp)
    print("Stock        :", updated.availability)
    print("Confidence   :", updated.confidence)
    print("Source       :", updated.source)
    print("Checked      :", updated.last_checked)
    print("Metadata     :", updated.metadata)
