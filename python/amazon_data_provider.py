#!/usr/bin/env python3
"""
Coupon World AI OS
Amazon Data Provider v0.1

Purpose:
- Keep Amazon data-source logic separate from product_pipeline.py
- Support safe manual metadata today
- Provide a clean integration point for Creators API / PA API later

This module never fabricates price, image, rating, reviews, stock,
discount, or availability.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class AmazonProductData:
    asin: str
    title: str = ""
    brand: str = ""
    category: str = ""
    image: str = ""
    price: str = ""
    mrp: str = ""
    discount: str = ""
    source: str = "manual"


class AmazonDataProvider(Protocol):
    name: str
    api_available: bool

    def get_product(
        self,
        asin: str,
        *,
        title: str = "",
        brand: str = "",
        category: str = "",
    ) -> AmazonProductData:
        ...


class ManualAmazonProvider:
    """Uses only verified values supplied by the operator."""

    name = "manual"
    api_available = False

    def get_product(
        self,
        asin: str,
        *,
        title: str = "",
        brand: str = "",
        category: str = "",
    ) -> AmazonProductData:
        return AmazonProductData(
            asin=asin,
            title=title.strip(),
            brand=brand.strip(),
            category=category.strip(),
            source=self.name,
        )


class UnavailableAmazonApiProvider:
    """Placeholder until Creators API / PA API access is approved."""

    name = "amazon-api"
    api_available = False

    def get_product(
        self,
        asin: str,
        *,
        title: str = "",
        brand: str = "",
        category: str = "",
    ) -> AmazonProductData:
        raise RuntimeError(
            "Amazon API access is not available yet. "
            "Use ManualAmazonProvider until Creators API / PA API access is approved."
        )


def get_default_provider() -> AmazonDataProvider:
    return ManualAmazonProvider()


if __name__ == "__main__":
    provider = get_default_provider()
    sample = provider.get_product(
        "B0FMDL81GS",
        title="OnePlus Nord Buds 3r TWS Earbuds",
        brand="OnePlus",
        category="Electronics",
    )

    print(f"ASIN          : {sample.asin}")
    print(f"Provider      : {provider.name}")
    print(f"API available : {'yes' if provider.api_available else 'no'}")
    print("Safe fallback : yes")
