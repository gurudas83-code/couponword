#!/usr/bin/env python3

from __future__ import annotations

from canonical_product import CanonicalProduct
from price_evidence import PriceEvidence
from retailer_contract import RetailerOffer
from retailer_evidence_collector import (
    RetailerEvidenceCollector,
)


class FlipkartEvidenceCollector(
    RetailerEvidenceCollector
):
    name = "flipkart"

    def __init__(self, provider=None):
        self.provider = provider

    @property
    def api_available(self) -> bool:
        return bool(
            self.provider
            and getattr(
                self.provider,
                "api_available",
                False,
            )
        )

    def collect(
        self,
        product: CanonicalProduct,
        offer: RetailerOffer,
    ) -> PriceEvidence | None:

        if offer.retailer.strip().lower() != self.name:
            return None

        retailer_product_id = str(
            offer.retailer_product_id or ""
        ).strip()

        if not retailer_product_id:
            return None

        # Until a verified Flipkart data provider is
        # connected, never manufacture price/stock.
        if not self.api_available:
            return None

        live = self.provider.get_product(
            retailer_product_id,
            title=product.title,
            brand=product.brand,
            category=product.category,
        )

        price = getattr(
            live,
            "price",
            None,
        )

        if price in (None, ""):
            return None

        mrp = getattr(
            live,
            "mrp",
            None,
        )

        availability = getattr(
            live,
            "availability",
            "unknown",
        ) or "unknown"

        source_url = (
            getattr(
                live,
                "source_url",
                "",
            )
            or offer.product_url
        )

        if not source_url:
            return None

        return PriceEvidence(
            product_id=product.product_id,
            retailer=self.name,
            retailer_product_id=
                retailer_product_id,
            price=price,
            mrp=mrp or None,
            availability=availability,
            source_url=source_url,
            source_type=(
                getattr(
                    live,
                    "source",
                    "",
                )
                or "flipkart-provider"
            ),
            confidence=0.95,
            notes=(
                "Evidence supplied by configured "
                "Flipkart data provider."
            ),
        )


if __name__ == "__main__":

    collector = FlipkartEvidenceCollector()

    print()
    print(
        "COUPON WORLD FLIPKART EVIDENCE COLLECTOR"
    )
    print(
        "API available :",
        collector.api_available,
    )
    print(
        "Safe fallback :",
        "enabled",
    )
