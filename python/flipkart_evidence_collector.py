#!/usr/bin/env python3

from __future__ import annotations

import json
import re
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlsplit

from canonical_product import CanonicalProduct
from product_matcher import clean_text, similarity
from price_evidence import PriceEvidence
from retailer_contract import RetailerOffer
from retailer_evidence_collector import RetailerEvidenceCollector


class FlipkartEvidenceCollector(RetailerEvidenceCollector):
    name = "flipkart"

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/151 Safari/537.36"
    )

    def __init__(self, provider=None, timeout: int = 20):
        self.provider = provider
        self.timeout = timeout

    @property
    def api_available(self) -> bool:
        return bool(
            self.provider
            and getattr(self.provider, "api_available", False)
        )

    def _collect_from_provider(
        self,
        product: CanonicalProduct,
        offer: RetailerOffer,
        retailer_product_id: str,
    ) -> PriceEvidence | None:

        if not self.api_available:
            return None

        live = self.provider.get_product(
            retailer_product_id,
            title=product.title,
            brand=product.brand,
            category=product.category,
        )

        price = getattr(live, "price", None)

        if price in (None, ""):
            return None

        mrp = getattr(live, "mrp", None)

        availability = (
            getattr(live, "availability", "unknown")
            or "unknown"
        )

        source_url = (
            getattr(live, "source_url", "")
            or offer.product_url
        )

        if not source_url:
            return None

        return PriceEvidence(
            product_id=product.product_id,
            retailer=self.name,
            retailer_product_id=retailer_product_id,
            price=price,
            mrp=mrp or None,
            availability=availability,
            source_url=source_url,
            source_type=(
                getattr(live, "source", "")
                or "flipkart-provider"
            ),
            confidence=0.95,
            notes=(
                "Evidence supplied by configured "
                "Flipkart data provider."
            ),
        )

    def _extract_product_json_ld(self, html: str) -> dict | None:

        blocks = re.findall(
            r'<script[^>]+type=["\']application/ld\+json["\']'
            r'[^>]*>(.*?)</script>',
            html,
            flags=re.I | re.S,
        )

        for raw in blocks:
            try:
                data = json.loads(unescape(raw.strip()))
            except (json.JSONDecodeError, TypeError, ValueError):
                continue

            items = data if isinstance(data, list) else [data]

            for item in items:
                if not isinstance(item, dict):
                    continue

                item_type = item.get("@type")

                if isinstance(item_type, list):
                    is_product = "Product" in item_type
                else:
                    is_product = item_type == "Product"

                if is_product:
                    return item

        return None

    @staticmethod
    def _is_flipkart_url(value: str) -> bool:

        try:
            hostname = (
                urlsplit(str(value or "").strip())
                .hostname
                or ""
            ).lower()
        except ValueError:
            return False

        return (
            hostname == "flipkart.com"
            or hostname.endswith(".flipkart.com")
        )

    @staticmethod
    def _structured_brand(structured: dict) -> str:

        brand = structured.get("brand")

        if isinstance(brand, dict):
            brand = brand.get("name")

        return str(brand or "").strip()

    def _page_identity_matches(
        self,
        product: CanonicalProduct,
        structured: dict,
    ) -> bool:

        page_name = str(
            structured.get("name") or ""
        ).strip()

        page_brand = self._structured_brand(
            structured
        )

        if not page_name or not page_brand:
            return False

        if clean_text(page_brand) != clean_text(product.brand):
            return False

        # Exact configuration safety gate.
        #
        # Flipkart Product JSON-LD commonly exposes RAM/storage in the
        # description even when RAM is absent from the visible product name.
        # When both the canonical product and retailer page provide explicit
        # configuration evidence, they must agree.
        description = str(
            structured.get("description") or ""
        ).strip()

        page_identity_text = f"{page_name} {description}"

        page_ram_match = re.search(
            r"\b(\d+)\s*GB\s*RAM\b",
            page_identity_text,
            flags=re.I,
        )

        page_storage_match = re.search(
            r"\b(\d+)\s*GB\s*(?:ROM|STORAGE)\b",
            page_identity_text,
            flags=re.I,
        )

        canonical_variant = str(
            product.variant or ""
        ).strip()

        canonical_ram_match = re.search(
            r"\b(\d+)\s*GB\s*/",
            canonical_variant,
            flags=re.I,
        )

        canonical_storage_match = re.search(
            r"/\s*(\d+)\s*GB\b",
            canonical_variant,
            flags=re.I,
        )

        if canonical_ram_match and page_ram_match:
            if (
                canonical_ram_match.group(1)
                != page_ram_match.group(1)
            ):
                return False

        if canonical_storage_match and page_storage_match:
            if (
                canonical_storage_match.group(1)
                != page_storage_match.group(1)
            ):
                return False

        page = clean_text(page_name)
        model = clean_text(product.model)

        if not model:
            return False

        if model in page:
            return True

        ignore = {
            "galaxy",
            "series",
            "edition",
            "smartphone",
            "mobile",
        }

        tokens = [
            token
            for token in model.split()
            if len(token) >= 2
            and token not in ignore
        ]

        if tokens:
            matched = sum(
                1
                for token in tokens
                if token in page.split()
            )

            if matched / len(tokens) >= 0.80:
                return True

        return (
            similarity(
                product.model,
                page_name,
            )
            >= 0.60
        )

    @staticmethod
    def _availability(value: object) -> str:

        text = str(value or "").strip().lower()

        if text.endswith("/instock"):
            return "in_stock"

        if text.endswith("/outofstock"):
            return "out_of_stock"

        return "unknown"

    def _collect_from_product_page(
        self,
        product: CanonicalProduct,
        offer: RetailerOffer,
        retailer_product_id: str,
    ) -> PriceEvidence | None:

        source_url = str(offer.product_url or "").strip()

        if not source_url:
            return None

        if not self._is_flipkart_url(source_url):
            return None

        request = Request(
            source_url,
            headers={
                "User-Agent": self.USER_AGENT,
                "Accept-Language": "en-IN,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml",
            },
        )

        try:
            with urlopen(
                request,
                timeout=self.timeout,
            ) as response:

                final_url = response.geturl()

                if not self._is_flipkart_url(final_url):
                    return None

                html = response.read().decode(
                    "utf-8",
                    errors="ignore",
                )

        except (HTTPError, URLError, TimeoutError, OSError):
            return None

        structured = self._extract_product_json_ld(html)

        if not structured:
            return None

        if not self._page_identity_matches(
            product,
            structured,
        ):
            return None

        offers = structured.get("offers")

        if not isinstance(offers, dict):
            return None

        price = offers.get("price")

        if price in (None, ""):
            return None

        currency = str(
            offers.get("priceCurrency") or ""
        ).strip().upper()

        if currency != "INR":
            return None

        availability = self._availability(
            offers.get("availability")
        )

        return PriceEvidence(
            product_id=product.product_id,
            retailer=self.name,
            retailer_product_id=retailer_product_id,
            price=price,
            mrp=None,
            availability=availability,
            source_url=source_url,
            source_type="flipkart-product-jsonld",
            confidence=0.90,
            notes=(
                "Price and availability observed from "
                "Flipkart Product JSON-LD."
            ),
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

        evidence = self._collect_from_provider(
            product,
            offer,
            retailer_product_id,
        )

        if evidence is not None:
            return evidence

        return self._collect_from_product_page(
            product,
            offer,
            retailer_product_id,
        )


if __name__ == "__main__":
    collector = FlipkartEvidenceCollector()

    print()
    print("COUPON WORLD FLIPKART EVIDENCE COLLECTOR")
    print("API available :", collector.api_available)
    print("HTTP fallback :", "enabled")
