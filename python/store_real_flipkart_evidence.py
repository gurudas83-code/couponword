#!/usr/bin/env python3

from __future__ import annotations

from canonical_product import CanonicalProduct
from evidence_offer_updater import apply_price_evidence
from flipkart_retailer_connector import FlipkartRetailerConnector
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

connector = FlipkartRetailerConnector()

base_offer = connector.get_offer(product)

if base_offer is None:
    raise RuntimeError(
        "Flipkart identity not found in retailer registry."
    )

evidence = PriceEvidence(
    product_id="cw-mobile-72",
    retailer="flipkart",
    retailer_product_id="MOBHEYY2FCCGHYEM",
    price=23499,
    mrp=26999,
    availability="out_of_stock",
    source_url=(
        "https://www.flipkart.com/"
        "samsung-m36-5g-velvet-black-black-128-gb/"
        "p/itm1e7be51802033"
        "?pid=MOBHEYY2FCCGHYEM"
    ),
    source_type="retailer_page_verified",
    confidence=0.98,
    notes=(
        "Exact Samsung M36 5G Velvet Black "
        "6GB/128GB listing verified. "
        "Listing currently out of stock."
    ),
)

verified_offer = apply_price_evidence(
    base_offer,
    evidence,
)

add_verified_offer(
    verified_offer
)

print("\nREAL FLIPKART EVIDENCE STORED")
print("Product      :", verified_offer.product_id)
print("Retailer     :", verified_offer.retailer)
print("ID           :", verified_offer.retailer_product_id)
print("Price        :", verified_offer.price)
print("MRP          :", verified_offer.mrp)
print("Availability :", verified_offer.availability)
print("Confidence   :", verified_offer.confidence)
print("Source       :", verified_offer.source)
