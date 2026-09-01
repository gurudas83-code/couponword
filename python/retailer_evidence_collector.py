#!/usr/bin/env python3

from __future__ import annotations

from abc import ABC, abstractmethod

from canonical_product import CanonicalProduct
from price_evidence import PriceEvidence
from retailer_contract import RetailerOffer


class RetailerEvidenceCollector(ABC):
    """
    Base contract for retailer evidence collectors.

    A collector receives:
      - canonical product truth
      - retailer identity offer

    It may return verified/observed PriceEvidence.

    It must NEVER invent:
      - price
      - MRP
      - availability
      - observation time
    """

    name: str = "unknown"

    @abstractmethod
    def collect(
        self,
        product: CanonicalProduct,
        offer: RetailerOffer,
    ) -> PriceEvidence | None:
        raise NotImplementedError


class UnavailableEvidenceCollector(RetailerEvidenceCollector):
    """
    Safe placeholder for retailers without an active
    evidence source/API.
    """

    def __init__(self, name: str):
        self.name = name

    def collect(
        self,
        product: CanonicalProduct,
        offer: RetailerOffer,
    ) -> PriceEvidence | None:
        return None


def collector_matches_offer(
    collector: RetailerEvidenceCollector,
    offer: RetailerOffer,
) -> bool:
    return (
        str(collector.name).strip().lower()
        == str(offer.retailer).strip().lower()
    )


if __name__ == "__main__":

    sample = RetailerOffer(
        retailer="amazon",
        product_id="cw-test-001",
        retailer_product_id="B0TEST123",
        brand="Test",
        model="Test Model",
    )

    collector = UnavailableEvidenceCollector(
        "amazon"
    )

    print("\nCOUPON WORLD EVIDENCE COLLECTOR CONTRACT")
    print("Collector :", collector.name)
    print(
        "Matches   :",
        collector_matches_offer(
            collector,
            sample,
        ),
    )
    print(
        "Evidence  :",
        collector.collect(
            None,
            sample,
        ),
    )
