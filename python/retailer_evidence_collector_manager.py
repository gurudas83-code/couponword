#!/usr/bin/env python3

from __future__ import annotations

from typing import Iterable

from canonical_product import CanonicalProduct
from price_evidence import PriceEvidence
from retailer_contract import RetailerOffer
from retailer_evidence_collector import (
    RetailerEvidenceCollector,
    collector_matches_offer,
)


class RetailerEvidenceCollectorManager:

    def __init__(
        self,
        collectors: Iterable[RetailerEvidenceCollector] | None = None,
    ):
        self.collectors = list(collectors or [])

    def collect_evidence(
        self,
        product: CanonicalProduct,
        offers: Iterable[RetailerOffer],
    ) -> list[PriceEvidence]:

        evidence_records: list[PriceEvidence] = []

        for offer in offers:

            matching_collectors = [
                collector
                for collector in self.collectors
                if collector_matches_offer(
                    collector,
                    offer,
                )
            ]

            for collector in matching_collectors:
                try:
                    evidence = collector.collect(
                        product,
                        offer,
                    )

                    if evidence is not None:
                        evidence_records.append(
                            evidence
                        )

                except Exception as exc:
                    print(
                        f"Evidence collector error "
                        f"[{collector.name}]: {exc}"
                    )

        return evidence_records


if __name__ == "__main__":

    from retailer_evidence_collector import (
        UnavailableEvidenceCollector,
    )

    product = CanonicalProduct(
        product_id="cw-test-001",
        title="Test Product",
        brand="Test",
        model="Test Model",
        variant="",
        category="Test",
        identifiers={},
        attributes={},
        source_product_id="test",
        confidence=0.95,
    )

    offers = [
        RetailerOffer(
            retailer="amazon",
            product_id=product.product_id,
            retailer_product_id="B0TEST123",
        ),
        RetailerOffer(
            retailer="flipkart",
            product_id=product.product_id,
            retailer_product_id="TESTPID123",
        ),
    ]

    manager = RetailerEvidenceCollectorManager(
        [
            UnavailableEvidenceCollector(
                "amazon"
            ),
            UnavailableEvidenceCollector(
                "flipkart"
            ),
        ]
    )

    evidence = manager.collect_evidence(
        product,
        offers,
    )

    print(
        "\nCOUPON WORLD EVIDENCE COLLECTOR MANAGER"
    )
    print(
        "Collectors :",
        len(manager.collectors),
    )
    print(
        "Offers     :",
        len(offers),
    )
    print(
        "Evidence   :",
        len(evidence),
    )
