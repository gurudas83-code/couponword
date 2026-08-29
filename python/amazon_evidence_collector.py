#!/usr/bin/env python3

from __future__ import annotations

from canonical_product import CanonicalProduct
from amazon_data_provider import (
    AmazonDataProvider,
    get_default_provider,
)
from price_evidence import PriceEvidence
from retailer_contract import RetailerOffer
from retailer_evidence_collector import (
    RetailerEvidenceCollector,
)


class AmazonEvidenceCollector(
    RetailerEvidenceCollector
):
    name = "amazon"

    def __init__(
        self,
        provider: AmazonDataProvider | None = None,
    ):
        self.provider = (
            provider
            or get_default_provider()
        )

    def collect(
        self,
        product: CanonicalProduct,
        offer: RetailerOffer,
    ) -> PriceEvidence | None:

        if offer.retailer.strip().lower() != self.name:
            return None

        asin = str(
            offer.retailer_product_id or ""
        ).strip().upper()

        if not asin:
            return None

        # Current manual provider must never create
        # fake live retailer evidence.
        if not getattr(
            self.provider,
            "api_available",
            False,
        ):
            return None

        live = self.provider.get_product(
            asin,
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
            offer.product_url
            or f"https://www.amazon.in/dp/{asin}"
        )

        return PriceEvidence(
            product_id=product.product_id,
            retailer=self.name,
            retailer_product_id=asin,
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
                or getattr(
                    self.provider,
                    "name",
                    "amazon-provider",
                )
            ),
            confidence=0.95,
            notes=(
                "Evidence supplied by configured "
                "Amazon data provider."
            ),
        )


if __name__ == "__main__":

    collector = AmazonEvidenceCollector()

    print()
    print(
        "COUPON WORLD AMAZON EVIDENCE COLLECTOR"
    )
    print(
        "Provider      :",
        getattr(
            collector.provider,
            "name",
            "unknown",
        ),
    )
    print(
        "API available :",
        getattr(
            collector.provider,
            "api_available",
            False,
        ),
    )
    print(
        "Safe fallback :",
        "enabled",
    )
