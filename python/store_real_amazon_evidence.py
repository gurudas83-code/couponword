#!/usr/bin/env python3

from __future__ import annotations

from amazon_retailer_connector import AmazonRetailerConnector
from canonical_product import CanonicalProduct
from evidence_offer_updater import apply_price_evidence
from price_evidence import PriceEvidence
from retailer_offer_store import add_verified_offer


product = CanonicalProduct(
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

connector = AmazonRetailerConnector()

base_offer = connector.get_offer(product)

if base_offer is None:
    raise RuntimeError(
        "Amazon identity not found."
    )

evidence = PriceEvidence(
    product_id="cw-mobile-72",
    retailer="amazon",
    retailer_product_id="B0FDBB2VRC",
    price=20999,
    mrp=None,

    # Price observed, but live stock was not
    # independently verified.
    availability="unknown",

    source_url=(
        "https://www.amazon.in/dp/"
        "B0FDBB2VRC"
    ),

    source_type="retailer_price_observed",
    confidence=0.90,

    notes=(
        "Exact Samsung Galaxy M36 5G "
        "Velvet Black 6GB/128GB Amazon "
        "price observed at INR 20,999. "
        "Live availability not independently "
        "verified."
    ),
)

verified_offer = apply_price_evidence(
    base_offer,
    evidence,
)

add_verified_offer(
    verified_offer
)

print("\nREAL AMAZON EVIDENCE STORED")
print("Product      :", verified_offer.product_id)
print("Retailer     :", verified_offer.retailer)
print("ID           :", verified_offer.retailer_product_id)
print("Price        :", verified_offer.price)
print("MRP          :", verified_offer.mrp)
print("Availability :", verified_offer.availability)
print("Confidence   :", verified_offer.confidence)
print("Source       :", verified_offer.source)
