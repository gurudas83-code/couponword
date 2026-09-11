#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from retailer_contract import RetailerOffer


ROOT = Path(__file__).resolve().parent.parent
OFFERS_DB = ROOT / "data" / "retailer_offers.json"


def load_offer_database() -> dict[str, Any]:
    if not OFFERS_DB.exists():
        return {
            "version": 1,
            "offers": [],
        }

    return json.loads(
        OFFERS_DB.read_text(encoding="utf-8-sig")
    )


def save_offer_database(data: dict[str, Any]) -> None:
    OFFERS_DB.parent.mkdir(parents=True, exist_ok=True)

    OFFERS_DB.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def add_verified_offer(
    offer: RetailerOffer,
) -> None:

    if not offer.product_id:
        raise ValueError(
            "Canonical product_id is required."
        )

    if not offer.retailer:
        raise ValueError(
            "Retailer name is required."
        )

    if not offer.retailer_product_id:
        raise ValueError(
            "Retailer product identifier is required."
        )

    data = load_offer_database()

    offers = data.setdefault("offers", [])

    key = (
        offer.product_id,
        offer.retailer,
        offer.retailer_product_id,
    )

    new_record = offer.to_dict()

    for index, existing in enumerate(offers):
        existing_key = (
            existing.get("product_id"),
            existing.get("retailer"),
            existing.get("retailer_product_id"),
        )

        if existing_key == key:
            offers[index] = new_record
            save_offer_database(data)
            return

    offers.append(new_record)
    save_offer_database(data)


if __name__ == "__main__":
    data = load_offer_database()

    print("\nCOUPON WORLD RETAILER OFFER STORE")
    print("Database :", OFFERS_DB)
    print("Version  :", data.get("version"))
    print("Offers   :", len(data.get("offers", [])))
