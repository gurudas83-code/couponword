#!/usr/bin/env python3

from __future__ import annotations

from typing import Iterable

from amazon_retailer_connector import AmazonRetailerConnector
from flipkart_retailer_connector import FlipkartRetailerConnector
from canonical_product import CanonicalProduct
from retailer_contract import RetailerOffer


class RetailerConnectorManager:
    def __init__(self, connectors: Iterable | None = None):
        self.connectors = list(
            connectors
            or [
                AmazonRetailerConnector(),
                FlipkartRetailerConnector(),
            ]
        )

    def collect_offers(
        self,
        product: CanonicalProduct,
    ) -> list[RetailerOffer]:

        offers: list[RetailerOffer] = []

        for connector in self.connectors:
            try:
                offer = connector.get_offer(product)

                if offer is not None:
                    offers.append(offer)

            except Exception as exc:
                print(
                    f"Connector error [{connector.name}]: {exc}"
                )

        return offers


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

    manager = RetailerConnectorManager()

    offers = manager.collect_offers(product)

    print("\nCOUPON WORLD CONNECTOR MANAGER")
    print("Product    :", product.product_id)
    print("Connectors :", len(manager.connectors))
    print("Offers     :", len(offers))

    print("\nCONNECTOR STATUS")

    for connector in manager.connectors:
        print(
            connector.name,
            "| live:",
            connector.live_data_available,
        )

    print("\nCOLLECTED OFFERS")

    for offer in offers:
        print()
        print("Retailer   :", offer.retailer)
        print("ID         :", offer.retailer_product_id)
        print("Price      :", offer.price)
        print("Stock      :", offer.availability)
        print("Source     :", offer.source)
