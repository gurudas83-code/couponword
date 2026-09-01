#!/usr/bin/env python3

from __future__ import annotations

from canonical_product import CanonicalProduct
from amazon_evidence_collector import AmazonEvidenceCollector
from flipkart_evidence_collector import FlipkartEvidenceCollector
from evidence_offer_updater import apply_price_evidence
from evidence_validator import validate_price_evidence
from multi_retailer_engine import compare_offers
from retailer_connector_manager import RetailerConnectorManager
from retailer_evidence_collector_manager import (
    RetailerEvidenceCollectorManager,
)
from retailer_offer_store import add_verified_offer


class MultiRetailerOrchestrator:

    def __init__(
        self,
        connector_manager=None,
        evidence_manager=None,
    ):
        self.connector_manager = (
            connector_manager
            or RetailerConnectorManager()
        )

        self.evidence_manager = (
            evidence_manager
            or RetailerEvidenceCollectorManager(
                [
                    AmazonEvidenceCollector(),
                    FlipkartEvidenceCollector(),
                ]
            )
        )

    def run(
        self,
        product: CanonicalProduct,
        write: bool = False,
    ) -> dict:

        identity_offers = (
            self.connector_manager.collect_offers(
                product
            )
        )

        evidence_records = (
            self.evidence_manager.collect_evidence(
                product,
                identity_offers,
            )
        )

        evidence_by_key = {
            (
                evidence.retailer,
                evidence.retailer_product_id,
            ): evidence
            for evidence in evidence_records
        }

        final_offers = []
        rejected_evidence = []

        for offer in identity_offers:

            key = (
                offer.retailer,
                offer.retailer_product_id,
            )

            evidence = evidence_by_key.get(key)

            if evidence is None:
                final_offers.append(offer)
                continue

            valid, errors = validate_price_evidence(
                offer,
                evidence,
            )

            if not valid:
                rejected_evidence.append(
                    {
                        "retailer": offer.retailer,
                        "retailer_product_id":
                            offer.retailer_product_id,
                        "errors": errors,
                    }
                )

                final_offers.append(offer)
                continue

            updated_offer = apply_price_evidence(
                offer,
                evidence,
            )

            if write:
                add_verified_offer(
                    updated_offer
                )

            final_offers.append(
                updated_offer
            )

        comparison = compare_offers(
            final_offers
        )

        return {
            "product_id": product.product_id,
            "identity_offer_count":
                len(identity_offers),
            "evidence_count":
                len(evidence_records),
            "rejected_evidence":
                rejected_evidence,
            "write_enabled": write,
            "offers": [
                offer.to_dict()
                for offer in final_offers
            ],
            "comparison": comparison,
        }


if __name__ == "__main__":

    product = CanonicalProduct(
        product_id="cw-mobile-72",
        title="Samsung Galaxy M36 5G",
        brand="Samsung",
        model="Galaxy M36 5G",
        variant="6GB/128GB",
        category="Mobiles",
        identifiers={
            "amazon_asin": "B0FDBB2VRC",
        },
        attributes={
            "ram": "6GB",
            "storage": "128GB",
            "color": "Velvet Black",
        },
        source_product_id="72",
        confidence=0.95,
    )

    orchestrator = MultiRetailerOrchestrator()

    result = orchestrator.run(
        product
    )

    print(
        "\nCOUPON WORLD MULTI-RETAILER ORCHESTRATOR"
    )
    print(
        "Product         :",
        result["product_id"],
    )
    print(
        "Identity offers :",
        result["identity_offer_count"],
    )
    print(
        "Evidence        :",
        result["evidence_count"],
    )
    print(
        "Rejected        :",
        len(result["rejected_evidence"]),
    )

    comparison = result["comparison"]

    print(
        "Comparable      :",
        comparison.get(
            "comparable_offer_count"
        ),
    )
    print(
        "Best offer      :",
        comparison.get(
            "best_offer"
        ),
    )

