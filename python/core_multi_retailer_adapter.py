#!/usr/bin/env python3

from __future__ import annotations

import re
from typing import Any

from canonical_product import CanonicalProduct
from core_identity_bridge import resolve_stable_identity
from retailer_product_registry import find_canonical_product_id


def clean(value: Any) -> str:
    return str(value or "").strip()


def capacity_gb(value: Any) -> str:
    """
    Return a normalized GB capacity only when the evidence
    explicitly represents a numeric GB value.
    """
    if isinstance(value, dict):
        value = (
            value.get("value")
            or value.get("normalized_value")
            or value.get("amount")
        )

    text = clean(value)

    match = re.search(
        r"(?<!\d)(\d{1,4})\s*GB\b",
        text,
        flags=re.I,
    )

    if not match:
        return ""

    return f"{int(match.group(1))}GB"


def first_capacity(
    attributes: dict[str, Any],
    *keys: str,
) -> str:
    for key in keys:
        value = capacity_gb(attributes.get(key))
        if value:
            return value

    return ""


def verified_variant(
    attributes: dict[str, Any],
    assessment: dict[str, Any],
) -> str:
    """
    Build RAM/storage variant only from explicit verified evidence.

    Priority:
    1. Explicit structured profile attributes.
    2. Verified Core fit criteria.

    If either RAM or storage remains unknown, leave variant blank.
    Never infer.
    """

    ram = first_capacity(
        attributes,
        "ram",
        "ram_capacity",
        "memory_capacity",
    )

    storage = first_capacity(
        attributes,
        "storage",
        "storage_capacity",
        "internal_storage",
    )

    criteria = assessment.get("criteria") or []

    if isinstance(criteria, list):
        for item in criteria:
            if not isinstance(item, dict):
                continue

            if clean(item.get("evidence_status")).lower() != "verified":
                continue

            criterion = clean(item.get("criterion")).lower()
            reason = clean(item.get("reason"))

            if criterion == "ram" and not ram:
                ram = capacity_gb(reason)

            elif criterion == "storage" and not storage:
                storage = capacity_gb(reason)

    if ram and storage:
        return f"{ram}/{storage}"

    return ""


def build_canonical_product(
    *,
    profile: dict[str, Any],
    identity: dict[str, Any],
    assessment: dict[str, Any] | None = None,
) -> CanonicalProduct:
    """
    Adapt a verified Core V1 runtime product into the canonical
    contract consumed by the Multi-Retailer Intelligence layer.

    This adapter does not score, rank, verify price, or modify
    Shopping Brain recommendations.
    """

    attributes = profile.get("attributes")
    if not isinstance(attributes, dict):
        attributes = {}

    identifiers: dict[str, str] = {}

    asin = clean(profile.get("asin") or identity.get("asin"))
    product_id = clean(profile.get("product_id"))

    if not asin:
        stable_identity = resolve_stable_identity(
            brand=profile.get("brand") or identity.get("brand"),
            model=identity.get("model"),
            search_name=identity.get("search_name"),
            title=profile.get("title") or identity.get("original_title"),
        )

        if stable_identity:
            asin = clean(stable_identity.get("asin"))

    if asin:
        identifiers["amazon_asin"] = asin

        registry_product_id = find_canonical_product_id(
            retailer="amazon",
            retailer_product_id=asin,
        )

        if registry_product_id:
            product_id = registry_product_id

    return CanonicalProduct(
        product_id=product_id,
        title=clean(profile.get("title")),
        brand=clean(profile.get("brand")),
        model=clean(identity.get("model")),
        variant=verified_variant(
            attributes,
            assessment or {},
        ),
        category=clean(profile.get("category")),
        identifiers=identifiers,
        attributes=dict(attributes),
        source_product_id=clean(profile.get("product_id")),
        source="core_v1_runtime",
        confidence=0.0,
    )
