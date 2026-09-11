#!/usr/bin/env python3

from __future__ import annotations

from typing import Protocol

from canonical_product import CanonicalProduct
from retailer_contract import RetailerOffer


class RetailerConnector(Protocol):
    """
    Common interface for every retailer source.

    Amazon, Flipkart, Croma, Reliance etc. must return
    Coupon World's standard RetailerOffer object.
    """

    name: str
    live_data_available: bool

    def get_offer(
        self,
        product: CanonicalProduct,
    ) -> RetailerOffer | None:
        ...


class UnavailableRetailerConnector:
    """
    Safe placeholder for retailers where live API/feed
    integration is not configured yet.
    """

    name = "unavailable"
    live_data_available = False

    def get_offer(
        self,
        product: CanonicalProduct,
    ) -> RetailerOffer | None:
        return None


if __name__ == "__main__":

    connector = UnavailableRetailerConnector()

    print("\nCOUPON WORLD RETAILER CONNECTOR CONTRACT")
    print("Connector :", connector.name)
    print("Live data :", connector.live_data_available)
    print("Safe fallback : yes")
