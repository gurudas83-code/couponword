"""Build the public, research-only mobile discovery index.

This adapter exposes existing discovery records for browsing without turning
research rows into canonical products, offers, rankings or purchase actions.
The source universe remains unchanged; the returned payload is a derived
public view with conservative evidence labels and no commerce fields.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


STATUS_ORDER = {
    "NEEDS_VERIFICATION": 0,
    "RESEARCH_ONLY": 1,
    "PARTIALLY_VERIFIED": 2,
    "OFFICIAL_VERIFIED": 3,
}

# Existing catalogue provenance is retained privately, but it is not a legal
# public-image licence. Keep the public research release on neutral
# placeholders until explicit usage rights are recorded.
PUBLIC_IMAGE_RIGHTS_CLEARED = False


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()


def _number(value: Any) -> int | None:
    if value in (None, "", "unknown"):
        return None
    try:
        number = int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _variant_key(brand: Any, model: Any, ram: Any, storage: Any) -> tuple[str, str, int | None, int | None]:
    return (_norm(brand), _norm(model), _number(ram), _number(storage))


def _https_urls(values: Any) -> list[str]:
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, list):
        return []
    return list(dict.fromkeys(item for item in values if isinstance(item, str) and item.startswith("https://")))


def _safe_image_index(catalogue: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, str]]:
    """Index public images only after explicit usage-rights clearance."""
    if not PUBLIC_IMAGE_RIGHTS_CLEARED:
        return {}
    index: dict[tuple[str, str], dict[str, str]] = {}
    for row in catalogue:
        if row.get("category") != "Mobiles" or not row.get("image"):
            continue
        provenance = row.get("image_provenance") or {}
        if provenance.get("verified") is not True:
            continue
        brand = _norm(row.get("brand"))
        title = _norm(row.get("title"))
        if not brand or not title or brand not in title:
            continue
        model_text = title.replace(brand, "", 1).strip()
        index.setdefault(
            (brand, model_text),
            {
                "image_url": str(row["image"]),
                "image_source_url": str(provenance.get("source_page") or ""),
            },
        )
    return index


def _find_image(index: dict[tuple[str, str], dict[str, str]], brand: Any, model: Any) -> dict[str, str] | None:
    brand_norm = _norm(brand)
    model_norm = _norm(model)
    if not brand_norm or not model_norm:
        return None
    for (indexed_brand, indexed_model), image in index.items():
        if indexed_brand != brand_norm:
            continue
        if indexed_model == model_norm:
            return image
        # Prefix matching is allowed only at a token boundary. This prevents
        # an iPhone 17 image from being reused for the distinct iPhone 17e.
        if indexed_model.startswith(model_norm) and len(indexed_model) > len(model_norm):
            next_char = indexed_model[len(model_norm)]
            if not next_char.isalnum():
                return image
        if model_norm.startswith(indexed_model) and len(model_norm) > len(indexed_model):
            next_char = model_norm[len(indexed_model)]
            if not next_char.isalnum():
                return image
    return None


def _status(model: dict[str, Any], variant: dict[str, Any], ram: int | None, storage: int | None) -> tuple[str, str, list[str]]:
    evidence = str(variant.get("official_evidence_status") or "").upper()
    identity = str(variant.get("identity_status") or "").upper()
    official_url = str(model.get("official_product_url") or "")
    exact = ram is not None and storage is not None
    if evidence == "VERIFIED_EXACT" and exact and official_url:
        return "OFFICIAL_VERIFIED", "Exact variant has an official source-backed pairing.", [
            "brand", "model", "ram_gb", "storage_gb", "official_product_url"
        ]
    if official_url and (evidence == "MODEL_ONLY" or str(model.get("india_market_status") or "").upper() in {"OFFICIAL_EVIDENCE_ONLY", "LAUNCH_EVIDENCE_VERIFIED"}):
        return "PARTIALLY_VERIFIED", "Official model evidence exists; the displayed variant is not fully paired.", [
            "brand", "model", "official_product_url"
        ]
    if not exact or identity in {"", "UNVERIFIED"}:
        return "NEEDS_VERIFICATION", "Identity or physical variant evidence is incomplete.", ["brand", "model"]
    return "RESEARCH_ONLY", "Discovery record retained for research; official identity/specification verification is pending.", [
        "brand", "model"
    ]


def _record_key(brand: Any, model: Any, ram: int | None, storage: int | None) -> str:
    material = f"{_norm(brand)}|{_norm(model)}|{ram or ''}|{storage or ''}".encode("utf-8")
    return "research-" + hashlib.sha256(material).hexdigest()[:16]


def _exact_variant(variant: dict[str, Any]) -> bool:
    return _number(variant.get("ram_gb")) is not None and _number(variant.get("storage_gb")) is not None


def build_public_catalogue(root: Path) -> dict[str, Any]:
    priority_payload = _read_json(root / "data/mobile_universe_priority_126.json")
    universe_payload = _read_json(root / "data/mobile_universe_2023_2026.json")
    preview_payload = _read_json(root / "data/mobile_research_preview.json")
    coupons = _read_json(root / "coupons.json")

    priority = priority_payload.get("products") or []
    models = universe_payload.get("models") or []
    preview = preview_payload.get("products") or []
    image_index = _safe_image_index(coupons)
    preview_keys = {
        _variant_key(row.get("brand"), row.get("model"), row.get("ram_gb"), row.get("storage_gb"))
        for row in preview
    }
    priority_keys = {
        _variant_key(row.get("brand"), row.get("model"), row.get("ram_gb"), row.get("storage_gb"))
        for row in priority
    }

    records: dict[tuple[str, str, int | None, int | None], dict[str, Any]] = {}
    excluded_verified_duplicates = 0
    for model in models:
        brand = model.get("brand")
        model_name = model.get("model")
        variants = model.get("variants") or [{}]
        for variant in variants:
            ram = _number(variant.get("ram_gb"))
            storage = _number(variant.get("storage_gb"))
            key = _variant_key(brand, model_name, ram, storage)
            if key in preview_keys:
                excluded_verified_duplicates += 1
                continue
            status, reason, verified_fields = _status(model, variant, ram, storage)
            image = _find_image(image_index, brand, model_name)
            official_url = model.get("official_product_url")
            source_urls = _https_urls([official_url, *(model.get("discovery_sources") or [])])
            variant_text = variant.get("variant_text")
            if not variant_text and ram is not None and storage is not None:
                variant_text = f"{ram}GB/{storage}GB"
            if not variant_text:
                variant_text = "Variant not specified"
            record = {
                "record_key": _record_key(brand, model_name, ram, storage),
                "brand": str(brand or "Unknown"),
                "model": str(model_name or "Unknown model"),
                "ram_gb": ram,
                "storage_gb": storage,
                "variant_text": str(variant_text),
                "variant_confidence": "official_exact" if status == "OFFICIAL_VERIFIED" else "research_seed" if _exact_variant(variant) else "unspecified",
                "launch_year": model.get("launch_year") if isinstance(model.get("launch_year"), int) else None,
                "status": status,
                "status_reason": reason,
                "verified_fields": verified_fields,
                "source_urls": source_urls,
                "source_records": ["mobile_universe_2023_2026"] + (["mobile_universe_priority_126"] if key in priority_keys else []),
                "image_url": image.get("image_url") if image else None,
                "image_source_url": image.get("image_source_url") if image else None,
                "image_status": "VERIFIED_MATCH" if image else "PLACEHOLDER",
                "commerce": {"price": None, "stock": None, "purchase_cta_eligible": False},
            }
            existing = records.get(key)
            if existing is None or STATUS_ORDER[record["status"]] > STATUS_ORDER[existing["status"]]:
                records[key] = record

    rows = sorted(records.values(), key=lambda row: (_norm(row["brand"]), _norm(row["model"]), row["ram_gb"] or 0, row["storage_gb"] or 0))
    status_counts = {status: sum(row["status"] == status for row in rows) for status in STATUS_ORDER}
    return {
        "schema_version": 1,
        "mode": "PUBLIC_MOBILE_RESEARCH_CATALOGUE",
        "notice": "Existing discovery records for research browsing only. No current price, stock, retailer or purchase eligibility is asserted.",
        "source_counts": {
            "priority_rows": len(priority),
            "wider_models": len(models),
            "wider_variants": sum(len(model.get("variants") or []) for model in models),
            "priority_rows_represented": len(priority_keys),
            "frozen_verified_variants": len(preview),
            "deduplicated_discovery_records": len(rows),
            "excluded_verified_section_duplicates": excluded_verified_duplicates,
        },
        "status_counts": status_counts,
        "records": rows,
    }
