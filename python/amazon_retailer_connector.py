#!/usr/bin/env python3

from __future__ import annotations

from amazon_data_provider import get_default_provider
from amazon_retailer_adapter import amazon_product_to_offer
from canonical_product import CanonicalProduct
from retailer_contract import RetailerOffer
from retailer_product_registry import get_retailer_product


class AmazonRetailerConnector:
    name = "amazon"

    def __init__(self):
        self.provider = get_default_provider()
        self.live_data_available = self.provider.api_available

    def _resolve_amazon_identity(
        self,
        product: CanonicalProduct,
    ) -> tuple[str, str, float]:

        asin = str(
            product.identifiers.get(
                "amazon_asin",
                "",
            )
        ).strip()

        product_url = ""
        confidence = product.confidence

        if asin:
            return (
                asin,
                product_url,
                confidence,
            )

        registry_record = get_retailer_product(
            product.product_id,
            "amazon",
        )

        if not registry_record:
            return "", "", confidence

        asin = str(
            registry_record.get(
                "retailer_product_id",
                "",
            )
        ).strip()

        product_url = str(
            registry_record.get(
                "product_url",
                "",
            )
        ).strip()

        registry_confidence = (
            registry_record.get(
                "confidence"
            )
        )

        if registry_confidence is not None:
            try:
                confidence = float(
                    registry_confidence
                )
            except (TypeError, ValueError):
                pass

        return (
            asin,
            product_url,
            confidence,
        )

    def get_offer(
        self,
        product: CanonicalProduct,
    ) -> RetailerOffer | None:

        (
            asin,
            product_url,
            confidence,
        ) = self._resolve_amazon_identity(
            product
        )

        if not asin:
            return None

        amazon_product = self.provider.get_product(
            asin,
            title=product.title,
            brand=product.brand,
            category=product.category,
        )

        if not product_url:
            product_url = (
                f"https://www.amazon.in/dp/{asin}"
                f"?tag=guru0906-21"
            )

        offer = amazon_product_to_offer(
            amazon_product,
            product_id=product.product_id,
            model=product.model,
            variant=product.variant,
            availability="unknown",
            product_url=product_url,
            confidence=confidence,
        )

        return offer


if __name__ == "__main__":

    product = CanonicalProduct(
        product_id="cw-mobile-72",
        title="Samsung Galaxy M36 5G",
        brand="Samsung",
        model="Galaxy M36 5G",
        variant="6GB/128GB",
        category="Mobiles",

        # Intentionally empty.
        # Amazon identity should now come from registry.
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

    offer = connector.get_offer(product)

    print("\nAMAZON REGISTRY-AWARE CONNECTOR")

    print(
        "Connector :",
        connector.name,
    )

    print(
        "Live data :",
        connector.live_data_available,
    )

    if offer:
        print(
            "ASIN      :",
            offer.retailer_product_id,
        )

        print(
            "Product   :",
            offer.product_id,
        )

        print(
            "Price     :",
            offer.price,
        )

        print(
            "Stock     :",
            offer.availability,
        )

        print(
            "URL       :",
            offer.product_url,
        )

    else:
        print("Offer     : None")
