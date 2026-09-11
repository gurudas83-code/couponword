from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
STORE_PATH = ROOT / "data" / "verified_product_evidence_cache.json"

SCHEMA_VERSION = "1.1"


def clean(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def normalize_text(value: Any) -> str:
    text = clean(value).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def normalize_brand(value: Any) -> str:
    return normalize_text(value)


def normalize_model(
    value: Any,
    brand: Any = "",
) -> str:
    """
    Conservative model normalization.

    We deliberately do NOT fuzzy-match different model families.
    Only cosmetic/variant details are removed.
    """
    text = normalize_text(value)
    brand_key = normalize_brand(brand)

    if brand_key and text.startswith(brand_key + " "):
        text = text[len(brand_key):].strip()

    # Remove common retailer/commerce words.
    removable = {
        "mobile",
        "smartphone",
        "phone",
        "india",
        "new",
    }

    tokens = [
        token
        for token in text.split()
        if token not in removable
    ]

    return " ".join(tokens).strip()



def _capacity_gb(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("value")

    text = clean(value).lower()

    if not text:
        return ""

    tb_match = re.search(
        r"\b(\d+(?:\.\d+)?)\s*tb\b",
        text,
        re.I,
    )

    if tb_match:
        try:
            return str(int(round(float(tb_match.group(1)) * 1024)))
        except (TypeError, ValueError):
            return ""

    gb_match = re.search(
        r"\b(\d+(?:\.\d+)?)\s*gb\b",
        text,
        re.I,
    )

    if gb_match:
        try:
            return str(int(float(gb_match.group(1))))
        except (TypeError, ValueError):
            return ""

    if re.fullmatch(r"\d+(?:\.0+)?", text):
        try:
            return str(int(float(text)))
        except (TypeError, ValueError):
            return ""

    return ""


def variant_signature_from_text(*values: Any) -> dict[str, str]:
    """
    Extract only variant-sensitive capacity identity.

    This intentionally ignores cosmetic variants such as colour so
    same-capacity colour siblings may share verified official evidence.
    """
    text = " ".join(
        clean(value)
        for value in values
        if clean(value)
    ).lower()

    if not text:
        return {}

    signature: dict[str, str] = {}

    ram_patterns = (
        r"\b(\d{1,3})\s*gb\s*(?:ram|memory)\b",
        r"\b(?:ram|memory)\s*(?:\(\s*gb\s*\))?"
        r"\s*[:=\-]?\s*(\d{1,3})(?:\s*gb)?\b",
    )

    storage_patterns = (
        r"\b(\d{2,4})\s*gb\s*"
        r"(?:storage|internal\s+storage|rom)\b",
        r"\b(?:storage|internal\s+storage|rom)"
        r"\s*(?:\(\s*gb\s*\))?"
        r"\s*[:=\-]?\s*(\d{2,4})(?:\s*gb)?\b",
    )

    for pattern in ram_patterns:
        match = re.search(pattern, text, re.I)

        if match:
            signature["ram_gb"] = str(int(match.group(1)))
            break

    for pattern in storage_patterns:
        match = re.search(pattern, text, re.I)

        if match:
            signature["storage_gb"] = str(int(match.group(1)))
            break

    # Common compact marketplace/query variants:
    #   6GB + 128GB
    #   6GB/128GB
    #   6GB 128GB
    if "ram_gb" not in signature or "storage_gb" not in signature:
        capacities = [
            int(value)
            for value in re.findall(
                r"\b(\d{1,4})\s*gb\b",
                text,
                re.I,
            )
        ]

        plausible_ram = [
            value
            for value in capacities
            if 1 <= value <= 32
        ]

        plausible_storage = [
            value
            for value in capacities
            if value >= 32
        ]

        if "ram_gb" not in signature and plausible_ram:
            signature["ram_gb"] = str(plausible_ram[0])

        if "storage_gb" not in signature and plausible_storage:
            signature["storage_gb"] = str(plausible_storage[0])

    return signature


def variant_signature_from_specifications(
    specifications: Any,
) -> dict[str, str]:
    if not isinstance(specifications, dict):
        return {}

    signature: dict[str, str] = {}

    for key in (
        "memory_gb",
        "ram_gb",
        "ram",
        "memory",
    ):
        if key not in specifications:
            continue

        value = _capacity_gb(specifications.get(key))

        if value:
            signature["ram_gb"] = value
            break

    for key in (
        "storage_gb",
        "storage_capacity_gb",
        "storage",
        "rom_gb",
        "rom",
    ):
        if key not in specifications:
            continue

        value = _capacity_gb(specifications.get(key))

        if value:
            signature["storage_gb"] = value
            break

    return signature


def record_variant_signature(
    record: dict[str, Any],
) -> dict[str, str]:
    stored = record.get("variant_signature")

    if isinstance(stored, dict):
        normalized = {
            key: clean(value)
            for key, value in stored.items()
            if key in {"ram_gb", "storage_gb"}
            and clean(value)
        }

        if normalized:
            return normalized

    return variant_signature_from_specifications(
        record.get("specifications")
    )


def variant_signatures_match(
    requested: dict[str, str],
    stored: dict[str, str],
) -> bool:
    """
    Fail closed for model-level cache reuse.

    Whole-record evidence may contain capacity-specific facts, so
    model fallback is allowed only when both sides expose the same
    RAM/storage identity. Empty-to-empty remains valid for products
    without capacity variants.
    """
    return requested == stored


def build_model_key(
    *,
    brand: Any,
    model: Any = "",
    search_name: Any = "",
    title: Any = "",
) -> str:
    brand_key = normalize_brand(brand)

    source = (
        clean(model)
        or clean(search_name)
        or clean(title)
    )

    model_key = normalize_model(
        source,
        brand=brand_key,
    )

    if not brand_key or not model_key:
        return ""

    return f"{brand_key}|{model_key}"


def empty_store() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": None,
        "records": [],
    }


def load_store() -> dict[str, Any]:
    if not STORE_PATH.exists():
        return empty_store()

    try:
        data = json.loads(
            STORE_PATH.read_text(
                encoding="utf-8-sig"
            )
        )
    except Exception:
        return empty_store()

    if not isinstance(data, dict):
        return empty_store()

    records = data.get("records")

    if not isinstance(records, list):
        data["records"] = []

    return data


def save_store(data: dict[str, Any]) -> None:
    STORE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data["schema_version"] = SCHEMA_VERSION
    data["updated_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    temp = STORE_PATH.with_suffix(".tmp")

    temp.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    temp.replace(STORE_PATH)


def extraction_is_cacheable(
    extraction: dict[str, Any],
) -> tuple[bool, str]:
    """
    Fail closed.

    Only evidence that has already passed official-source /
    extraction verification may enter persistent memory.
    """
    if not isinstance(extraction, dict):
        return False, "Extraction is not a dict"

    if extraction.get("fetch_status") != "success":
        return False, "Extraction fetch did not succeed"

    if extraction.get("resolver_verified") is not True:
        return False, "Resolver verification is missing"

    review = extraction.get("review") or {}
    status = clean(review.get("status")).lower()

    if status in {
        "rejected",
        "rejected_candidate",
        "error",
    }:
        return False, f"Rejected review status: {status}"

    page_identity = extraction.get(
        "page_identity_score"
    )

    if page_identity is not None:
        try:
            if float(page_identity) < 0.50:
                return (
                    False,
                    "Official page identity score below 0.50",
                )
        except (TypeError, ValueError):
            return False, "Invalid page identity score"

    specifications = extraction.get(
        "specifications"
    )
    features = extraction.get("features")

    spec_count = (
        len(specifications)
        if isinstance(specifications, dict)
        else 0
    )

    feature_count = (
        len(features)
        if isinstance(features, list)
        else 0
    )

    if spec_count == 0 and feature_count == 0:
        return False, "No usable evidence"

    return True, ""


def find_verified_evidence(
    *,
    asin: Any = "",
    brand: Any = "",
    model: Any = "",
    search_name: Any = "",
    title: Any = "",
) -> dict[str, Any] | None:
    """
    Match order:
      1. exact ASIN
      2. exact conservative brand + model key

    No fuzzy product-family matching.
    """
    data = load_store()
    records = data.get("records") or []

    asin_key = clean(asin).upper()

    if asin_key:
        requested_variant = variant_signature_from_text(
            title,
            search_name,
            model,
        )

        for record in records:
            if not isinstance(record, dict):
                continue

            if (
                clean(record.get("asin")).upper()
                != asin_key
            ):
                continue

            stored_variant = record_variant_signature(record)

            # Exact ASIN remains the highest-priority cache identity,
            # but explicit RAM/storage evidence in the current candidate
            # must not conflict with (or be absent from) stored variant
            # evidence. With no explicit requested capacities, preserve
            # the historical exact-ASIN behavior.
            if requested_variant:
                incompatible = any(
                    not stored_variant.get(key)
                    or stored_variant.get(key) != value
                    for key, value in requested_variant.items()
                )

                if incompatible:
                    continue

            result = dict(record)
            result["cache_match_mode"] = "asin"
            result["cache_variant_signature"] = stored_variant
            return result

    model_key = build_model_key(
        brand=brand,
        model=model,
        search_name=search_name,
        title=title,
    )

    if not model_key:
        return None

    requested_variant = variant_signature_from_text(
        title,
        search_name,
        model,
    )

    for record in records:
        if not isinstance(record, dict):
            continue

        if clean(record.get("model_key")) != model_key:
            continue

        stored_variant = record_variant_signature(record)

        if not variant_signatures_match(
            requested_variant,
            stored_variant,
        ):
            continue

        result = dict(record)
        result["cache_match_mode"] = "brand_model"
        result["cache_variant_signature"] = stored_variant
        return result

    return None


def save_verified_evidence(
    *,
    identity: dict[str, Any],
    extraction: dict[str, Any],
    asin: Any = "",
) -> tuple[bool, str]:
    usable, reason = extraction_is_cacheable(
        extraction
    )

    if not usable:
        return False, reason

    brand = clean(
        extraction.get("brand")
        or identity.get("brand")
    )

    model = clean(identity.get("model"))

    search_name = clean(
        extraction.get("search_name")
        or identity.get("search_name")
    )

    title = clean(
        identity.get("title")
        or search_name
    )

    asin_value = clean(
        asin
        or identity.get("asin")
    ).upper()

    model_key = build_model_key(
        brand=brand,
        model=model,
        search_name=search_name,
        title=title,
    )

    variant_signature = variant_signature_from_specifications(
        extraction.get("specifications")
    )

    if not asin_value and not model_key:
        return (
            False,
            "Neither ASIN nor strict brand/model key available",
        )

    record = {
        "asin": asin_value or None,
        "brand": brand,
        "model": model or None,
        "search_name": search_name or None,
        "model_key": model_key or None,
        "variant_signature": variant_signature,
        "official_url": clean(
            extraction.get("official_url")
            or extraction.get("canonical_url")
        ) or None,
        "resolver_verified": True,
        "fetch_status": "success",
        "page_identity_score": extraction.get(
            "page_identity_score"
        ),
        "specifications": extraction.get(
            "specifications"
        ) or {},
        "features": extraction.get(
            "features"
        ) or [],
        "review": extraction.get("review") or {},
        "saved_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    data = load_store()
    records = data.get("records") or []

    replacement_index = None

    for index, existing in enumerate(records):
        if not isinstance(existing, dict):
            continue

        existing_asin = clean(
            existing.get("asin")
        ).upper()

        existing_model_key = clean(
            existing.get("model_key")
        )

        if (
            asin_value
            and existing_asin
            and asin_value == existing_asin
        ):
            replacement_index = index
            break

        if (
            model_key
            and existing_model_key
            and model_key == existing_model_key
            and variant_signatures_match(
                variant_signature,
                record_variant_signature(existing),
            )
        ):
            replacement_index = index
            break

    if replacement_index is None:
        records.append(record)
    else:
        records[replacement_index] = record

    data["records"] = records
    save_store(data)

    return True, "verified evidence saved"
