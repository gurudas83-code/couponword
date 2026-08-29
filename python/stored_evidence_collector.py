#!/usr/bin/env python3

from __future__ import annotations

from canonical_product import CanonicalProduct
from price_evidence import PriceEvidence
from retailer_contract import RetailerOffer
from retailer_evidence_collector import (
    RetailerEvidenceCollector,
)
from retailer_offer_store import load_offer_database


class StoredEvidenceCollector(
    RetailerEvidenceCollector
):
    """
    Replays previously verified retailer evidence.

    This collector does NOT fetch the internet and does NOT
    manufacture freshness. It preserves the original
    last_checked timestamp from the stored offer.
    """

    def __init__(self, retailer: str):
        self.name = (
            str(retailer)
            .strip()
            .lower()
        )

    def collect(
        self,
        product: CanonicalProduct,
        offer: RetailerOffer,
    ) -> PriceEvidence | None:

        data = load_offer_database()

        for record in data.get("offers", []):

            if (
                record.get("product_id")
                != product.product_id
            ):
                continue

            if (
                str(record.get("retailer", ""))
                .strip()
                .lower()
                != self.name
            ):
                continue

            if (
                record.get("retailer_product_id")
                != offer.retailer_product_id
            ):
                continue

            price = record.get("price")

            if price is None:
                return None

            source_url = (
                record.get("metadata", {})
                .get("evidence_source_url")
                or record.get("product_url")
                or ""
            )

            if not source_url:
                return None

            source_type = (
                record.get("metadata", {})
                .get("evidence_source_type")
                or record.get("source")
                or "stored_verified"
            )

            observed_at = (
                record.get("metadata", {})
                .get("evidence_observed_at")
                or record.get("last_checked")
                or ""
            )

            # Never replace an old observation time
            # with the current time.
            if not observed_at:
                return None

            return PriceEvidence(
                product_id=product.product_id,
                retailer=self.name,
                retailer_product_id=
                    offer.retailer_product_id,
                price=price,
                mrp=record.get("mrp"),
                availability=record.get(
                    "availability",
                    "unknown",
                ),
                source_url=source_url,
                source_type=source_type,
                observed_at=observed_at,
                confidence=float(
                    record.get(
                        "confidence",
                        0.0,
                    )
                ),
                notes=(
                    record.get("metadata", {})
                    .get(
                        "evidence_notes",
                        "Replayed from verified offer store.",
                    )
                ),
            )

        return None


if __name__ == "__main__":

    collector = StoredEvidenceCollector(
        "flipkart"
    )

    print(
        "\nCOUPON WORLD STORED EVIDENCE COLLECTOR"
    )
    print("Collector :", collector.name)
    print(
        "Rule      : preserve original observation time"
    )
