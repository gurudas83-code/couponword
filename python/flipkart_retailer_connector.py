#!/usr/bin/env python3

from __future__ import annotations

from canonical_product import CanonicalProduct
from retailer_contract import RetailerOffer
from retailer_product_registry import get_retailer_product


class FlipkartRetailerConnector:
    name = "flipkart"
    live_data_available = False

    def get_offer(
        self,
        product: CanonicalProduct,
    ) -> RetailerOffer | None:

        registry_record = get_retailer_product(
            product.product_id,
            "flipkart",
        )

        if not registry_record:
            return None

        retailer_product_id = str(
            registry_record.get(
                "retailer_product_id",
                "",
            )
        ).strip()

        if not retailer_product_id:
            return None

        product_url = str(
            registry_record.get(
                "product_url",
                "",
            )
        ).strip()

        confidence = product.confidence

        registry_confidence = registry_record.get(
            "confidence"
        )

        if registry_confidence is not None:
            try:
                confidence = float(
                    registry_confidence
                )
            except (TypeError, ValueError):
                pass

        return RetailerOffer(
            retailer=self.name,
            product_id=product.product_id,
            retailer_product_id=retailer_product_id,
            brand=product.brand,
            model=product.model,
            variant=product.variant,
            title=product.title,
            price=None,
            mrp=None,
            currency="INR",
            availability="unknown",
            product_url=product_url,
            affiliate_url="",
            source=str(
                registry_record.get(
                    "source",
                    "retailer-registry",
                )
            ),
            confidence=confidence,
        )


if __name__ == "__main__":

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

    offer = connector.get_offer(product)

    print("\nFLIPKART REGISTRY-AWARE CONNECTOR")
    print("Connector :", connector.name)
    print("Live data :", connector.live_data_available)
    print("Offer     :", offer)
