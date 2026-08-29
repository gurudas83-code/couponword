#!/usr/bin/env python3

from __future__ import annotations

from canonical_product import CanonicalProduct
from amazon_retailer_connector import AmazonRetailerConnector
from evidence_offer_updater import apply_price_evidence
from price_evidence import PriceEvidence
from retailer_offer_store import add_verified_offer


product = CanonicalProduct(
    product_id="cw-mobile-10",
    title="Redmi 13 5G",
    brand="Redmi",
    model="Redmi 13 5G",
    variant="8GB/128GB",
    category="Mobiles",
    identifiers={"amazon_asin": "B0F1N8B7Z4"},
    attributes={
        "ram": "8GB",
        "storage": "128GB",
        "color": "Hawaiian Blue",
    },
    source_product_id="10",
    source="pilot_manifest",
    confidence=0.95,
)

connector = AmazonRetailerConnector()
base_offer = connector.get_offer(product)

if base_offer is None:
    raise RuntimeError("Amazon identity not found for Redmi")

evidence = PriceEvidence(
    product_id=product.product_id,
    retailer="amazon",
    retailer_product_id=base_offer.retailer_product_id,
    price=19990,
    mrp=19990,
    availability="unknown",
    source_url=base_offer.product_url,
    source_type="market_price_observed",
    confidence=0.80,
    notes=(
        "Exact ASIN B0F1N8B7Z4 verified for Redmi 13 5G "
        "Hawaiian Blue 8GB/128GB. Price observed at Rs 19,990. "
        "Live Amazon availability not independently verified, "
        "therefore availability remains unknown."
    ),
)

verified_offer = apply_price_evidence(
    base_offer,
    evidence,
)

add_verified_offer(verified_offer)

print()
print("REDMI AMAZON PRICE EVIDENCE STORED")
print("Product      :", verified_offer.product_id)
print("Retailer     :", verified_offer.retailer)
print("ID           :", verified_offer.retailer_product_id)
print("Price        :", verified_offer.price)
print("Availability :", verified_offer.availability)
print("Confidence   :", verified_offer.confidence)
print("Source       :", verified_offer.source)
