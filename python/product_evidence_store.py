from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
STORE_PATH = ROOT / "data" / "verified_product_evidence_cache.json"

SCHEMA_VERSION = "1.0"


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
        for record in records:
            if not isinstance(record, dict):
                continue

            if (
                clean(record.get("asin")).upper()
                == asin_key
            ):
                result = dict(record)
                result["cache_match_mode"] = "asin"
                return result

    model_key = build_model_key(
        brand=brand,
        model=model,
        search_name=search_name,
        title=title,
    )

    if not model_key:
        return None

    for record in records:
        if not isinstance(record, dict):
            continue

        if clean(record.get("model_key")) == model_key:
            result = dict(record)
            result["cache_match_mode"] = "brand_model"
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
