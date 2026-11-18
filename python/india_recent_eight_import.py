"""Safely add eight recently source-linked Indian phones to research discovery.

This is model-family discovery, not API-confirmed retail stock, exact SKUs,
current prices, scores or image licences. The original 232 cards remain frozen.
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "india_recent_phone_sources.json"
CORE = ROOT / "data" / "mobile_research_catalogue.json"
MODE = "EIGHT_RECENT_MANUFACTURER_SOURCE_MODELS_RESEARCH_ONLY"
APPROVED = {
    "Motorola Signature 27": ("motorola", "signature 27", "motorola.in"),
    "OPPO Find X10": ("oppo", "find x10", "oppo.com"),
    "OPPO Find X10 Pro Max": ("oppo", "find x10 pro max", "oppo.com"),
    "OPPO F35 5G": ("oppo", "f35 5g", "oppo.com"),
    "OPPO F35 Pro 5G": ("oppo", "f35 pro 5g", "oppo.com"),
    "vivo V80": ("vivo", "v80", "vivo.com"),
    "vivo X Fold6": ("vivo", "x fold6", "vivo.com"),
    "vivo S2 FE": ("vivo", "s2 fe", "vivo.com"),
}


def _official(url: str, host: str) -> bool:
    parsed = urlsplit(url)
    return (parsed.scheme == "https"
            and parsed.hostname in (host, "www." + host)
            and parsed.username is None and parsed.password is None
            and parsed.port in (None, 443))


def build_recent() -> dict:
    recent = json.loads(SOURCE.read_text(encoding="utf-8"))
    original = json.loads(CORE.read_text(encoding="utf-8"))
    if recent.get("market") != "India" or len(original["model_cards"]) != 232:
        raise ValueError("Source/primary catalogue preconditions changed")
    source = {m["name"]: m for m in recent["models"]}
    if len(source) != len(recent["models"]) or not set(APPROVED).issubset(source):
        raise ValueError("Reviewed manufacturer model list changed")
    existing = {m["model_key"] for m in original["model_cards"]}
    # Existing separate historical-sales intake must not overlap.
    from python.india_missing_eight_pages import import_eight
    existing.update(m["model_key"] for m in import_eight()["model_cards"])
    cards, records = [], []
    for name, (brand, model, host) in APPROVED.items():
        item = source[name]
        key = brand + "|" + model
        if key in existing:
            raise ValueError("Duplicate phone already integrated: " + key)
        if not _official(item["source"], host):
            raise ValueError("Unapproved manufacturer source: " + name)
        if "store" in item and not _official(item["store"], host):
            # shop.vivo.com is supported for the official vivo e-store.
            if not (host == "vivo.com" and _official(item["store"], "shop.vivo.com")):
                raise ValueError("Unapproved official store: " + name)
        refkey = "recent-source|" + key
        query = quote(name, safe="")
        links = [
            {"retailer": "amazon", "url": "https://www.amazon.in/s?k=" + query + "&tag=guru07cc-21"},
            {"retailer": "flipkart", "url": "https://www.flipkart.com/search?q=" + query},
            {"retailer": "croma", "url": "https://www.croma.com/search/?text=" + query},
        ]
        # Source descriptions are not independently benchmarked technical
        # specifications, so no unsupported spec values are promoted.
        cards.append({
            "model_key": key, "brand": brand, "model": model,
            "status": "RESEARCH_ONLY", "market_intake": True,
            "status_reason": "India manufacturer-linked model only; exact retail variants, current prices, stock, photo rights and independent performance not verified.",
            "discovery_record_keys": [refkey], "frozen_variant_ids": [],
            "verified_india_variants": [],
            "specifications": {}, "missing_specifications": [],
            "available_specification_fields": [],
            "source_urls": [item["source"]] + ([item["store"]] if item.get("store") else []),
            "image_status": "PLACEHOLDER", "photo": None,
            "verified_retailer_links": [], "retailer_search_links": links,
            "market_reference": "Recent India manufacturer model source",
            "manufacturer_page": item["source"],
        })
        records.append({
            "record_key": refkey, "status": "RESEARCH_ONLY",
            "ram_gb": None, "storage_gb": None,
            "variant_text": "Model-family research; exact India retail SKU not verified",
            "verified_fields": [], "source_urls": [item["source"]],
        })
    if len(cards) != 8 or len({c["model_key"] for c in cards}) != 8:
        raise ValueError("Expected eight distinct source-linked models")
    return {
        "schema_version": 1, "mode": MODE, "core_model_count_unchanged": 232,
        "model_cards": cards, "records": records,
        "notice": "Manufacturer-source research only; no exact retailer SKU, price, stock, rating or image permission is certified.",
    }


def publish_recent(destination: Path) -> dict:
    payload = build_recent()
    target = destination / "data" / "india_recent_eight_research.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload
