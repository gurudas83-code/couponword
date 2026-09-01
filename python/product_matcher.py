#!/usr/bin/env python3

from __future__ import annotations

import re
from difflib import SequenceMatcher

from retailer_contract import RetailerOffer
from offer_normalizer import normalize_offer


def clean_text(value: str) -> str:
    text = str(value or "").lower().strip()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def similarity(a: str, b: str) -> float:
    a = clean_text(a)
    b = clean_text(b)

    if not a or not b:
        return 0.0

    return SequenceMatcher(None, a, b).ratio()


def exact_text_match(a: str, b: str) -> bool:
    return clean_text(a) == clean_text(b) and bool(clean_text(a))


def match_offers(
    offer_a: RetailerOffer,
    offer_b: RetailerOffer,
) -> dict:

    brand_match = exact_text_match(
        offer_a.brand,
        offer_b.brand,
    )

    model_similarity = similarity(
        offer_a.model,
        offer_b.model,
    )

    variant_match = exact_text_match(
        offer_a.variant,
        offer_b.variant,
    )

    title_similarity = similarity(
        offer_a.title,
        offer_b.title,
    )

    score = 0.0

    if brand_match:
        score += 0.25

    score += model_similarity * 0.35

    if variant_match:
        score += 0.30

    score += title_similarity * 0.10

    score = round(score, 4)

    same_product = (
        brand_match
        and model_similarity >= 0.85
        and variant_match
        and score >= 0.85
    )

    return {
        "same_product": same_product,
        "match_score": score,
        "brand_match": brand_match,
        "model_similarity": round(model_similarity, 4),
        "variant_match": variant_match,
        "title_similarity": round(title_similarity, 4),
        "retailer_a": offer_a.retailer,
        "retailer_b": offer_b.retailer,
        "product_a": offer_a.title,
        "product_b": offer_b.title,
    }


if __name__ == "__main__":

    amazon_raw = {
        "asin": "B0TEST123",
        "title": "Samsung Galaxy Test 8GB 128GB",
        "brand": "Samsung",
        "model": "Galaxy Test",
        "variant": "8GB/128GB",
        "price": "₹19,999",
        "availability": "In Stock",
        "source": "manual",
        "confidence": 0.95,
    }

    flipkart_raw = {
        "fsn": "MOBTEST456",
        "name": "Samsung Galaxy Test 8 GB 128 GB",
        "brand": "Samsung",
        "model": "Galaxy Test",
        "configuration": "8GB/128GB",
        "selling_price": "18,999",
        "stock": "Available",
        "source": "manual",
        "confidence": 0.93,
    }

    wrong_variant_raw = {
        "fsn": "MOBTEST999",
        "name": "Samsung Galaxy Test 6 GB 128 GB",
        "brand": "Samsung",
        "model": "Galaxy Test",
        "configuration": "6GB/128GB",
        "selling_price": "17,999",
        "stock": "Available",
        "source": "manual",
        "confidence": 0.92,
    }

    amazon_offer = normalize_offer(
        "Amazon",
        amazon_raw,
    )

    flipkart_offer = normalize_offer(
        "Flipkart",
        flipkart_raw,
    )

    wrong_offer = normalize_offer(
        "Flipkart",
        wrong_variant_raw,
    )

    print("\nTEST 1 - SAME VARIANT")
    print(match_offers(amazon_offer, flipkart_offer))

    print("\nTEST 2 - WRONG VARIANT")
    print(match_offers(amazon_offer, wrong_offer))
