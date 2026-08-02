#!/usr/bin/env python3
"""
Coupon World Resolver Engine v1.2

Purpose
-------
Validate whether a candidate official page belongs to the expected product.

This module does not search the web. It only compares:
- expected product identity
- candidate page title
- candidate URL
- candidate metadata

It returns a score, decision and explanation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any
from urllib.parse import urlparse


STOP_WORDS = {
    "official",
    "specifications",
    "specification",
    "specs",
    "features",
    "product",
    "page",
    "india",
    "global",
    "with",
    "and",
    "for",
    "the",
    "of",
    "in",
    "black",
    "blue",
    "white",
    "gold",
    "wireless",
    "usb",
    "edition",
    "series",
}

NETWORK_TOKENS = {"4g", "5g", "lte"}
VARIANT_TOKENS = {
    "pro",
    "max",
    "plus",
    "ultra",
    "air",
    "mini",
    "lite",
    "neo",
    "prime",
    "nano",
    "e",
}

ACCEPTABLE_EQUIVALENTS = {
    ("mk240", "mk240 nano"),
    ("mk240 nano", "mk240"),
}

BRAND_ALIASES = {
    "redmi": {"redmi", "xiaomi"},
    "xiaomi": {"xiaomi", "redmi"},
    "realme": {"realme"},
    "apple": {"apple"},
    "logitech": {"logitech"},
    "yamaha": {"yamaha"},
    "samsung": {"samsung"},
    "boat": {"boat", "boatlifestyle"},
    "oneplus": {"oneplus"},
}


DOMAIN_BRANDS = {
    "apple.com": "apple",
    "logitech.com": "logitech",
    "realme.com": "realme",
    "mi.com": "redmi",
    "xiaomi.com": "xiaomi",
    "yamaha.com": "yamaha",
    "samsung.com": "samsung",
    "boat-lifestyle.com": "boat",
    "oneplus.com": "oneplus",
    "oneplus.in": "oneplus",
}


@dataclass
class ParsedIdentity:
    raw: str
    normalized: str
    brand: str
    model_tokens: list[str]
    numeric_tokens: list[str]
    network_tokens: list[str]
    variant_tokens: list[str]
    ram_tokens: list[str]
    storage_tokens: list[str]
    color_tokens: list[str]


@dataclass
class ResolverDecision:
    score: int
    decision: str
    brand_match: bool
    model_match: bool
    network_match: bool | None
    variant_match: bool | None
    storage_match: bool | None
    ram_match: bool | None
    reasons: list[str]
    expected: dict[str, Any]
    candidate: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_text(value: Any) -> str:
    text = str(value or "").lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9+\s.-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(value: Any) -> list[str]:
    return re.findall(r"[a-z0-9]+", normalize_text(value))


def extract_brand(tokens: list[str]) -> str:
    joined = "".join(tokens)

    for brand, aliases in BRAND_ALIASES.items():
        for alias in aliases:
            if alias in tokens or alias in joined:
                return brand

    return ""


def infer_brand_from_url(url: Any) -> str:
    try:
        host = (urlparse(str(url or "")).hostname or "").lower()
    except ValueError:
        return ""

    for domain, brand in DOMAIN_BRANDS.items():
        if host == domain or host.endswith("." + domain):
            return brand

    return ""


def extract_memory_tokens(tokens: list[str], kind: str) -> list[str]:
    found: list[str] = []

    for i, token in enumerate(tokens):
        if re.fullmatch(r"\d{1,4}", token):
            next_token = tokens[i + 1] if i + 1 < len(tokens) else ""

            if next_token in {"gb", "tb"}:
                value = f"{token}{next_token}"

                if kind == "ram" and int(token) <= 64:
                    found.append(value)

                if kind == "storage" and (
                    next_token == "tb" or int(token) >= 64
                ):
                    found.append(value)

        elif re.fullmatch(r"\d{1,4}(gb|tb)", token):
            number = int(re.match(r"\d+", token).group())

            if kind == "ram" and number <= 64:
                found.append(token)

            if kind == "storage" and (
                token.endswith("tb") or number >= 64
            ):
                found.append(token)

    return sorted(set(found))


def extract_color_tokens(tokens: list[str]) -> list[str]:
    known_colors = {
        "black",
        "white",
        "blue",
        "red",
        "green",
        "gold",
        "silver",
        "grey",
        "gray",
        "purple",
        "pink",
        "orange",
        "yellow",
        "hawaiian",
        "master",
    }

    return [token for token in tokens if token in known_colors]


def parse_identity(
    value: Any,
    brand_hint: Any = "",
) -> ParsedIdentity:
    raw = str(value or "")
    normalized = normalize_text(raw)
    tokens = tokenize(normalized)

    brand = normalize_text(brand_hint) or extract_brand(tokens)

    numeric_tokens = [
        token
        for token in tokens
        if any(char.isdigit() for char in token)
        and token not in NETWORK_TOKENS
        and not re.fullmatch(r"\d{1,4}(gb|tb)", token)
    ]

    network_tokens = [
        token
        for token in tokens
        if token in NETWORK_TOKENS
    ]

    variant_tokens = [
        token
        for token in tokens
        if token in VARIANT_TOKENS
    ]

    ram_tokens = extract_memory_tokens(tokens, "ram")
    storage_tokens = extract_memory_tokens(tokens, "storage")
    color_tokens = extract_color_tokens(tokens)

    excluded = (
        STOP_WORDS
        | NETWORK_TOKENS
        | set(VARIANT_TOKENS)
        | set(ram_tokens)
        | set(storage_tokens)
        | set(color_tokens)
        | set(BRAND_ALIASES.keys())
    )

    model_tokens = [
        token
        for token in tokens
        if token not in excluded
        and len(token) >= 2
    ]

    return ParsedIdentity(
        raw=raw,
        normalized=normalized,
        brand=brand,
        model_tokens=model_tokens,
        numeric_tokens=numeric_tokens,
        network_tokens=network_tokens,
        variant_tokens=variant_tokens,
        ram_tokens=ram_tokens,
        storage_tokens=storage_tokens,
        color_tokens=color_tokens,
    )


def equivalent_model(expected: str, candidate: str) -> bool:
    pair = (
        normalize_text(expected),
        normalize_text(candidate),
    )

    return pair in ACCEPTABLE_EQUIVALENTS


def subset_match(
    expected: list[str],
    candidate: list[str],
) -> bool | None:
    if not expected:
        return None

    return set(expected).issubset(set(candidate))


def model_score(
    expected: ParsedIdentity,
    candidate: ParsedIdentity,
) -> tuple[int, bool, list[str]]:
    """
    Give priority to identity-bearing model codes such as:
    13, 17e, MK240, PSS-E30 and Air 8.

    Long retailer descriptions must not make an otherwise exact model fail.
    """
    reasons: list[str] = []

    expected_model = set(expected.model_tokens)
    candidate_model = set(candidate.model_tokens)

    expected_identity_tokens = {
        token
        for token in expected_model.union(expected.numeric_tokens)
        if any(char.isdigit() for char in token)
    }
    candidate_identity_tokens = {
        token
        for token in candidate_model.union(candidate.numeric_tokens)
        if any(char.isdigit() for char in token)
    }

    if expected_identity_tokens:
        missing_identity = expected_identity_tokens.difference(
            candidate_identity_tokens
        )

        if missing_identity:
            reasons.append(
                "Missing identity-bearing model token(s): "
                + ", ".join(sorted(missing_identity))
            )
            return 0, False, reasons

        reasons.append("All identity-bearing model tokens matched")

        expected_alpha = {
            token
            for token in expected_model
            if not any(char.isdigit() for char in token)
        }
        candidate_alpha = {
            token
            for token in candidate_model
            if not any(char.isdigit() for char in token)
        }

        if expected_alpha:
            shared_alpha = expected_alpha.intersection(candidate_alpha)

            if shared_alpha:
                reasons.append(
                    "Supporting model/series token(s) matched: "
                    + ", ".join(sorted(shared_alpha))
                )

        return 50, True, reasons

    if not expected_model:
        return 0, False, ["Expected model tokens are missing"]

    expected_joined = " ".join(expected.model_tokens)
    candidate_joined = " ".join(candidate.model_tokens)

    if equivalent_model(expected_joined, candidate_joined):
        return 50, True, ["Accepted known model equivalent"]

    common = expected_model.intersection(candidate_model)
    coverage = len(common) / len(expected_model)

    if coverage >= 0.75:
        reasons.append("Most expected model tokens matched")
        return 45, True, reasons

    if coverage >= 0.50:
        reasons.append("Partial model-token match; manual review required")
        return 30, False, reasons

    reasons.append("Model token match is weak")
    return round(coverage * 25), False, reasons


def compare_identity(
    expected_text: Any,
    candidate_title: Any,
    candidate_url: Any = "",
    expected_brand: Any = "",
) -> ResolverDecision:
    candidate_path = urlparse(
        str(candidate_url or "")
    ).path.replace("-", " ")

    candidate_combined = (
        f"{candidate_title} "
        f"{candidate_path}"
    )

    expected = parse_identity(
        expected_text,
        brand_hint=expected_brand,
    )

    candidate_brand_hint = infer_brand_from_url(
        candidate_url
    )

    candidate = parse_identity(
        candidate_combined,
        brand_hint=candidate_brand_hint,
    )

    score = 0
    reasons: list[str] = []

    expected_brand_norm = normalize_text(expected.brand)
    candidate_brand_norm = normalize_text(candidate.brand)

    accepted_candidate_brands = BRAND_ALIASES.get(
        expected_brand_norm,
        {expected_brand_norm},
    )

    brand_match = bool(
        expected_brand_norm
        and (
            candidate_brand_norm in accepted_candidate_brands
            or expected_brand_norm == candidate_brand_norm
        )
    )

    if brand_match:
        score += 30
        reasons.append("Brand matched")
    else:
        reasons.append("Brand mismatch")

    model_points, model_match, model_reasons = model_score(
        expected,
        candidate,
    )
    score += model_points
    reasons.extend(model_reasons)

    network_match = subset_match(
        expected.network_tokens,
        candidate.network_tokens,
    )

    if network_match is True:
        score += 10
        reasons.append("Network generation matched")
    elif network_match is False:
        reasons.append("Network generation mismatch")

    variant_match = subset_match(
        expected.variant_tokens,
        candidate.variant_tokens,
    )

    if variant_match is True:
        score += 5
        reasons.append("Variant matched")
    elif variant_match is False:
        reasons.append("Variant mismatch")

    storage_match = subset_match(
        expected.storage_tokens,
        candidate.storage_tokens,
    )

    if storage_match is True:
        score += 3
        reasons.append("Storage matched")
    elif storage_match is False:
        reasons.append("Storage mismatch")

    ram_match = subset_match(
        expected.ram_tokens,
        candidate.ram_tokens,
    )

    if ram_match is True:
        score += 2
        reasons.append("RAM matched")
    elif ram_match is False:
        reasons.append("RAM mismatch")

    score = max(0, min(score, 100))

    critical_failure = (
        not brand_match
        or not model_match
        or network_match is False
        or variant_match is False
    )

    if score >= 80 and not critical_failure:
        decision = "verified"
    elif score >= 60 and brand_match and model_match:
        decision = "manual_review"
    else:
        decision = "reject"

    return ResolverDecision(
        score=score,
        decision=decision,
        brand_match=brand_match,
        model_match=model_match,
        network_match=network_match,
        variant_match=variant_match,
        storage_match=storage_match,
        ram_match=ram_match,
        reasons=reasons,
        expected=asdict(expected),
        candidate=asdict(candidate),
    )


def validate_candidate(
    expected_identity: dict[str, Any],
    candidate_title: str,
    candidate_url: str,
) -> dict[str, Any]:
    expected_text = (
        expected_identity.get("search_name")
        or expected_identity.get("model")
        or expected_identity.get("title")
        or ""
    )

    expected_brand = expected_identity.get("brand") or ""

    return compare_identity(
        expected_text=expected_text,
        candidate_title=candidate_title,
        candidate_url=candidate_url,
        expected_brand=expected_brand,
    ).to_dict()


if __name__ == "__main__":
    tests = [
        (
            "realme Buds Air 8",
            "realme Buds Air Full Specifications",
            "https://www.realme.com/in/realme-buds-air/specs",
            "realme",
        ),
        (
            "Logitech MK240",
            "MK240 Minimalist Keyboard and Mouse",
            "https://www.logitech.com/en-in/shop/p/mk240-minimalist-keyboard-mouse",
            "Logitech",
        ),
        (
            "Apple iPhone 17e 256GB",
            "Buy iPhone 17 256GB",
            "https://www.apple.com/in/shop/buy-iphone/iphone-17",
            "Apple",
        ),
    ]

    for expected, title, url, brand in tests:
        result = compare_identity(
            expected,
            title,
            url,
            brand,
        )

        print("=" * 64)
        print("Expected :", expected)
        print("Candidate:", title)
        print("Score    :", result.score)
        print("Decision :", result.decision)
        print("Reasons  :", "; ".join(result.reasons))
