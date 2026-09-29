#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent

REGISTRY_FILE = (
    ROOT
    / "data"
    / "retailer_product_registry.json"
)


def load_registry() -> dict[str, Any]:

    if not REGISTRY_FILE.exists():
        return {
            "version": 1,
            "products": {},
        }

    return json.loads(
        REGISTRY_FILE.read_text(
            encoding="utf-8-sig"
        )
    )


def save_registry(
    data: dict[str, Any],
) -> None:

    REGISTRY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REGISTRY_FILE.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def register_retailer_product(
    *,
    product_id: str,
    retailer: str,
    retailer_product_id: str,
    product_url: str = "",
    confidence: float = 0.0,
    source: str = "",
) -> None:

    product_id = product_id.strip()
    retailer = retailer.strip().lower()
    retailer_product_id = (
        retailer_product_id.strip()
    )

    if not product_id:
        raise ValueError(
            "Canonical product_id required."
        )

    if not retailer:
        raise ValueError(
            "Retailer required."
        )

    if not retailer_product_id:
        raise ValueError(
            "Retailer product ID required."
        )

    data = load_registry()

    products = data.setdefault(
        "products",
        {},
    )

    for owner_id, owner_retailers in products.items():
        if owner_id == product_id or not isinstance(owner_retailers, dict):
            continue
        owner_record = owner_retailers.get(retailer)
        if (
            isinstance(owner_record, dict)
            and str(owner_record.get("retailer_product_id") or "").strip().casefold()
            == retailer_product_id.casefold()
        ):
            raise ValueError(
                "Retailer product ID already belongs to another canonical product."
            )

    product_record = products.setdefault(
        product_id,
        {},
    )

    product_record[retailer] = {
        "retailer_product_id":
            retailer_product_id,
        "product_url":
            product_url,
        "confidence":
            confidence,
        "source":
            source,
    }

    save_registry(data)


def get_retailer_product(
    product_id: str,
    retailer: str,
) -> dict[str, Any] | None:

    data = load_registry()

    return (
        data
        .get("products", {})
        .get(product_id, {})
        .get(retailer.lower())
    )


def find_canonical_product_id(
    *,
    retailer: str,
    retailer_product_id: str,
) -> str | None:
    """
    Resolve a stable retailer identity back to Coupon World's
    canonical product_id.

    Read-only. Never creates or modifies registry records.
    """

    retailer = str(retailer or "").strip().lower()
    retailer_product_id = str(
        retailer_product_id or ""
    ).strip()

    if not retailer or not retailer_product_id:
        return None

    data = load_registry()

    matching_ids: list[str] = []

    for product_id, retailer_records in (
        data.get("products", {}).items()
    ):
        if not isinstance(retailer_records, dict):
            continue

        record = retailer_records.get(retailer)

        if not isinstance(record, dict):
            continue

        registered_id = str(
            record.get("retailer_product_id") or ""
        ).strip()

        if (
            registered_id.casefold()
            == retailer_product_id.casefold()
        ):
            matching_ids.append(str(product_id))

    return matching_ids[0] if len(matching_ids) == 1 else None


def find_catalogued_mobile_id(
    *, retailer_product_id: str, candidate_title: str, candidate_brand: str,
) -> str | None:
    """Expose an existing canonical ID only for an exact catalogue variant.

    A registry entry alone does not establish that a search-card title still
    describes the same phone and physical RAM/storage variant.
    """
    from mobile_exact_identity_gate import AUTO_REUSE, classify_mobile_identity_reuse
    from product_evidence_store import variant_signature_from_text

    asin = str(retailer_product_id or "").strip().upper()
    owner = find_canonical_product_id(retailer="amazon", retailer_product_id=asin)
    if not owner or not owner.startswith("cw-mobile-"):
        return None

    catalogue_file = ROOT / "coupons.json"
    if not catalogue_file.is_file():
        return None
    try:
        products = json.loads(catalogue_file.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    if isinstance(products, dict):
        products = products.get("products", [])
    if not isinstance(products, list):
        return None

    matches = [
        item for item in products if isinstance(item, dict)
        and str(item.get("id")) == owner.removeprefix("cw-mobile-")
        and str(item.get("asin") or "").strip().upper() == asin
        and str(item.get("category") or "").strip().casefold() == "mobiles"
    ]
    if len(matches) != 1:
        return None
    item = matches[0]
    if str(item.get("brand") or "").strip().casefold() != str(candidate_brand or "").strip().casefold():
        return None
    expected = variant_signature_from_text(item.get("title"))
    observed = variant_signature_from_text(candidate_title)
    if not all(expected.get(key) and observed.get(key) == expected[key]
               for key in ("ram_gb", "storage_gb")):
        return None
    identity = classify_mobile_identity_reuse(
        expected_text=item.get("title"), candidate_title=candidate_title,
        expected_brand=item.get("brand"),
    )
    return owner if identity.get("status") == AUTO_REUSE else None


if __name__ == "__main__":

    register_retailer_product(
        product_id="cw-mobile-72",
        retailer="amazon",
        retailer_product_id="B0FDBB2VRC",
        product_url=(
            "https://www.amazon.in/dp/"
            "B0FDBB2VRC"
        ),
        confidence=0.95,
        source="couponworld-existing-data",
    )

    record = get_retailer_product(
        "cw-mobile-72",
        "amazon",
    )

    print(
        "\nCOUPON WORLD "
        "RETAILER PRODUCT REGISTRY"
    )

    print("Product :", "cw-mobile-72")
    print("Amazon  :", record)
