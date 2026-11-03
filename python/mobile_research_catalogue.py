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
from urllib.parse import urlparse
from pathlib import Path
from typing import Any


STATUS_ORDER = {
    "NEEDS_VERIFICATION": 0,
    "RESEARCH_ONLY": 1,
    "PARTIALLY_VERIFIED": 2,
    "OFFICIAL_VERIFIED": 3,
}

# These are the approved technical fields already used by the frozen P13.1
# research preview.  The public catalogue may expose a value only when that
# preview contains source-backed evidence for the same normalized model.
# Everything else remains explicitly pending; discovery rows never acquire
# guessed specifications.
TECHNICAL_FIELD_LABELS = {
    "chipset": "Chipset",
    "gpu": "GPU",
    "display_type": "Display technology",
    "display_inches": "Display size",
    "display_resolution": "Display resolution",
    "display_refresh_max_hz": "Refresh rate",
    "rear_main_mp": "Main camera",
    "rear_ultrawide_mp": "Ultrawide camera",
    "rear_telephoto_mp": "Telephoto camera",
    "front_mp": "Front camera",
    "ois": "OIS",
    "battery_mah_typical": "Battery capacity",
    "wired_charging_max_w": "Wired charging",
    "launch_android": "Launch Android",
    "os_upgrade_generations": "OS updates",
    "security_support_years": "Security updates",
    "ip_rating": "IP rating",
    "network_support": "5G/network support",
    "display_size_description": "Display size",
    "display_resolution_description": "Display resolution",
    "display_type_description": "Display technology",
    "display_refresh_description": "Refresh rate",
    "rear_camera_system": "Rear camera system",
    "front_camera_system": "Front camera system",
    "battery_capacity_description": "Battery capacity",
    "charging_description": "Charging support",
    "battery_and_charging": "Battery and charging",
    "operating_system": "Operating system",
    "security_update_policy": "Security update policy",
    "durability": "Durability",
}

EVIDENCE_FIELD_ALIASES = {
    "processor": "chipset",
    "resolution_main_display": "display_resolution_description",
    "resolution": "display_resolution_description",
    "size_main_display": "display_size_description",
    "display_size": "display_size_description",
    "technology_main_display": "display_type_description",
    "display": "display_type_description",
    "max_refresh_rate_main_display": "display_refresh_description",
    "rear_camera_resolution_multiple": "rear_camera_system",
    "primary_camera_rear_camera": "rear_camera_system",
    "front_camera_resolution": "front_camera_system",
    "secondary_camera_front_camera": "front_camera_system",
    "battery_capacity_mah_typical": "battery_capacity_description",
    "charging": "charging_description",
    "battery_and_charging": "battery_and_charging",
    "operating_system": "operating_system",
    "security_update_period_valid_until": "security_update_policy",
    "cellular_network": "network_support",
    "network": "network_support",
    "durability": "durability",
}

# Existing catalogue provenance is retained privately, but it is not a legal
# public-image licence. Keep the public research release on neutral
# placeholders until explicit usage rights are recorded.
PUBLIC_IMAGE_RIGHTS_CLEARED = False

def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()


# Official India newsroom launch evidence reviewed for the New & Noteworthy
# research section. These dates are model-level launch evidence only; they do
# not assert current stock, price or purchase eligibility.
RECENT_INDIA_LAUNCHES = {
    (_norm("Samsung"), _norm("Galaxy F70e 5G")): {
        "india_launch_date": "2026-02-09",
        "india_launch_source": "https://news.samsung.com/in/samsung-india-unveils-galaxy-f70e-5g-with-showstopper-camera-ultra-smooth-display-premium-leather-finish",
    },
    (_norm("Samsung"), _norm("Galaxy M17e 5G")): {
        "india_launch_date": "2026-03-18",
        "india_launch_source": "https://news.samsung.com/in/samsung-launches-galaxy-m17e-5g-redefining-the-smartphone-experience-for-indias-young-on-the-go-generation",
    },
    (_norm("Samsung"), _norm("Galaxy A37 5G")): {
        "india_launch_date": "2026-03-26",
        "india_launch_source": "https://news.samsung.com/in/samsung-unveils-galaxy-a57-5g-and-galaxy-a37-5g-packing-pro-level-features-in-camera-and-ai",
    },
    (_norm("Samsung"), _norm("Galaxy A57 5G")): {
        "india_launch_date": "2026-03-26",
        "india_launch_source": "https://news.samsung.com/in/samsung-unveils-galaxy-a57-5g-and-galaxy-a37-5g-packing-pro-level-features-in-camera-and-ai",
    },
    (_norm("Samsung"), _norm("Galaxy S26 Ultra")): {
        "india_launch_date": "2026-02-26",
        "india_launch_source": "https://news.samsung.com/in/samsung-india-launches-its-most-advanced-ai-phone-the-galaxy-s26-series-pre-order-now-for-exciting-offers",
    },
    (_norm("Samsung"), _norm("Galaxy S26 FE")): {
        "india_launch_date": "2026-09-14",
        "india_launch_source": "https://news.samsung.com/in/samsung-launches-galaxy-s26-fe-in-india-bringing-flagship-camera-galaxy-ai-and-powerful-performance",
    },
}


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


def _public_spec_value(item: Any) -> dict[str, Any] | None:
    """Return one source-backed spec item safe for the public catalogue."""
    if not isinstance(item, dict):
        return None
    value = item.get("value")
    source_url = item.get("source_url")
    if value in (None, "", [], {}) or not isinstance(source_url, str) or not source_url.startswith("https://"):
        return None
    return {
        "label": str(item.get("label") or "").strip(),
        "value": value,
        "source_url": source_url,
        "applicability": str(item.get("applicability") or "MODEL_SHARED"),
        "checked_date": str(item.get("checked_date") or ""),
    }


def _merge_model_specs(products: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Merge only identical model-level values from frozen evidence.

    A disagreement between physical variants is intentionally withheld rather
    than silently selecting one value.  That keeps a model card useful while
    preserving the exact-variant safety boundary.
    """
    merged: dict[str, dict[str, Any]] = {}
    conflicts: set[str] = set()
    for product in products:
        for key, raw_item in (product.get("specifications") or {}).items():
            if key not in TECHNICAL_FIELD_LABELS:
                continue
            item = _public_spec_value(raw_item)
            if item is None:
                continue
            previous = merged.get(key)
            if previous is None:
                merged[key] = item
            elif str(previous.get("value")) != str(item.get("value")):
                conflicts.add(key)
    for key in conflicts:
        merged.pop(key, None)
    missing = [key for key in TECHNICAL_FIELD_LABELS if key not in merged]
    return merged, missing


def _load_existing_source_specs(root: Path) -> dict[tuple[str, str], list[dict[str, Any]]]:
    """Adapt already-reviewed official evidence into public model-level fields.

    The source files contain retailer identifiers and offer observations too;
    this adapter reads only technical values whose source is an official
    manufacturer host and drops all offer/identity metadata.
    """
    result: dict[tuple[str, str], list[dict[str, Any]]] = {}
    evidence_files = (
        root / "data/phase_e_release_evidence.json",
        root / "data/verified_product_evidence_cache.json",
    )
    for path in evidence_files:
        if not path.is_file():
            continue
        payload = _read_json(path)
        for record in payload.get("records") or []:
            identity = (_norm(record.get("brand")), _norm(record.get("model")))
            if not identity[0] or not identity[1]:
                continue
            official_url = str(record.get("official_url") or "")
            official_host = (urlparse(official_url).hostname or "").casefold()
            if not official_url.startswith("https://") or not official_host or official_host.endswith("amazon.in"):
                continue
            mapped: dict[str, dict[str, Any]] = {}
            for raw_key, raw_item in (record.get("specifications") or {}).items():
                key = EVIDENCE_FIELD_ALIASES.get(str(raw_key))
                if not key or key not in TECHNICAL_FIELD_LABELS or not isinstance(raw_item, dict):
                    continue
                value = raw_item.get("value")
                if value in (None, "", [], {}):
                    continue
                source_url = str(raw_item.get("source_url") or official_url)
                source_host = (urlparse(source_url).hostname or "").casefold()
                if not source_url.startswith("https://") or source_host.endswith("amazon.in"):
                    continue
                observed = str(raw_item.get("observed_at") or record.get("observed_at") or "")
                mapped[key] = {
                    "label": TECHNICAL_FIELD_LABELS[key],
                    "value": value,
                    "source_url": source_url,
                    "applicability": "MODEL_SHARED",
                    "checked_date": observed[:10] if observed else "",
                }
            if mapped:
                result.setdefault(identity, []).append({"specifications": mapped})

    # The official extractor also produces a deliberately sanitized,
    # model-level ledger for manufacturer pages that do not expose a safe
    # exact RAM/storage pairing.  It is kept separate from private Product
    # DNA and is admitted only after the same HTTPS, manufacturer-host and
    # evidence-status checks above.  Model-level facts never create a
    # physical variant claim.
    ledger_path = root / "data/mobile_official_spec_evidence.json"
    if ledger_path.is_file():
        payload = _read_json(ledger_path)
        for record in payload.get("records") or []:
            if not isinstance(record, dict):
                continue
            identity = (_norm(record.get("brand")), _norm(record.get("model")))
            official_url = str(record.get("official_url") or "")
            official_host = (urlparse(official_url).hostname or "").casefold()
            if (
                not identity[0]
                or not identity[1]
                or not official_url.startswith("https://")
                or not official_host
                or official_host.endswith("amazon.in")
                or record.get("review_status") != "candidate_ready"
                or record.get("evidence_status") != "VERIFIED_SOURCE"
            ):
                continue
            mapped: dict[str, dict[str, Any]] = {}
            for key, raw_item in (record.get("specifications") or {}).items():
                if key not in TECHNICAL_FIELD_LABELS or not isinstance(raw_item, dict):
                    continue
                if raw_item.get("applicability") != "MODEL_SHARED":
                    continue
                if raw_item.get("evidence_status") != "VERIFIED_SOURCE":
                    continue
                value = raw_item.get("value")
                source_url = str(raw_item.get("source_url") or official_url)
                source_host = (urlparse(source_url).hostname or "").casefold()
                if (
                    value in (None, "", [], {})
                    or not source_url.startswith("https://")
                    or not source_host
                    or source_host.endswith("amazon.in")
                ):
                    continue
                mapped[key] = {
                    "label": str(raw_item.get("label") or TECHNICAL_FIELD_LABELS[key]),
                    "value": value,
                    "source_url": source_url,
                    "applicability": "MODEL_SHARED",
                    "checked_date": str(raw_item.get("checked_date") or ""),
                }
            if mapped:
                result.setdefault(identity, []).append({"specifications": mapped})
    return result



def _apply_workbook_research(root, model_cards):
    """Add dated model research; never mutate frozen variants or shopping gates."""
    from urllib.parse import urlparse
    path = root / "data" / "mobile_workbook_research.json"
    if not path.exists():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("mode") != "DATED_RESEARCH_NOT_LIVE_OFFERS":
        raise ValueError("invalid workbook research mode")
    cards = {card["model_key"]: card for card in model_cards}
    entries = payload.get("models", [])
    if len(entries) != len(cards) or {item["model_key"] for item in entries} != set(cards):
        raise ValueError("workbook research must reconcile all model keys exactly")
    official_hosts = {"apple.com", "nothing.tech", "google.com", "infinixmobiles.in", "iqoo.com", "lavamobiles.com", "motorola.com", "motorola.in", "oneplus.in", "oppo.com", "mi.com", "po.co", "realme.com", "samsung.com", "tecno-mobile.in", "tecno-mobile.com", "vivo.com"}
    retailer_hosts = {"www.amazon.in", "www.flipkart.com", "www.croma.com", "www.reliancedigital.in", "www.vijaysales.com", "www.poorvika.com"}
    for entry in entries:
        card = cards[entry["model_key"]]
        for key, item in entry.get("specifications", {}).items():
            parsed = urlparse(item.get("source_url", ""))
            if key not in TECHNICAL_FIELD_LABELS or parsed.scheme != "https" or not any(parsed.hostname == host or (parsed.hostname or "").endswith("." + host) for host in official_hosts):
                raise ValueError("unsupported workbook specification source")
            # Existing frozen and admitted source values retain precedence.
            if key not in card["specifications"]:
                card["specifications"][key] = item
            if item["source_url"] not in card["source_urls"]:
                card["source_urls"].append(item["source_url"])
        card["missing_specifications"] = [key for key in TECHNICAL_FIELD_LABELS if key not in card["specifications"]]
        card["available_specification_fields"] = [TECHNICAL_FIELD_LABELS[key] for key in card["specifications"]]
        if card["specifications"] and card["status"] != "OFFICIAL_VERIFIED":
            card["status"] = "PARTIALLY_VERIFIED"
            card["status_reason"] = "Manufacturer research is available; exact variant and current availability are not certified."
        links = entry.get("retailer_search_links", [])
        for item in links:
            parsed = urlparse(item.get("url", ""))
            if parsed.scheme != "https" or parsed.hostname not in retailer_hosts:
                raise ValueError("unsupported retailer research link")
        card["retailer_search_links"] = links
        card["physical_variant_note"] = entry.get("physical_variant_note", "")
        ref = entry.get("research_budget_reference")
        if ref:
            parsed = urlparse(ref.get("source_url", ""))
            negative = any(word in str(ref.get("stock_indication", "")).upper() for word in ("OUT_OF_STOCK", "OUT OF STOCK", "UNAVAILABLE", "SOLD_OUT", "DISCONTINUED"))
            if parsed.scheme != "https" or parsed.hostname not in retailer_hosts or negative or not isinstance(ref.get("reference_price_inr"), (float, int)) or ref["reference_price_inr"] <= 0 or not ref.get("storage_gb") or ref.get("ranking_weight") != 0 or ref.get("live_offer") is not False:
                raise ValueError("invalid research budget reference")
        card["research_budget_reference"] = ref
        card["research_checked_at"] = payload["research_as_of"]

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

    # Keep the source universe's model identities as the public card boundary.
    # Discovery rows are variant records, so their count (235) is intentionally
    # different from the 232 model cards. Frozen exact variants are attached to
    # the same normalized model identity and remain separate evidence records.
    model_cards: list[dict[str, Any]] = []
    cards_by_identity: dict[tuple[str, str], dict[str, Any]] = {}
    for model in models:
        identity = (_norm(model.get("brand")), _norm(model.get("model")))
        if identity in cards_by_identity:
            raise ValueError(f"duplicate source model identity: {identity}")
        card = {
            "model_key": str(model.get("model_key") or f"{identity[0]}|{identity[1]}"),
            "brand": str(model.get("brand") or "Unknown"),
            "model": str(model.get("model") or "Unknown model"),
            "discovery_record_keys": [],
            "frozen_variant_ids": [],
            "status": "RESEARCH_ONLY",
            "status_reason": "Source-backed technical evidence is incomplete for this model.",
            "specifications": {},
            "missing_specifications": list(TECHNICAL_FIELD_LABELS),
            "source_urls": [],
            "image_status": "PLACEHOLDER",
        }
        launch = RECENT_INDIA_LAUNCHES.get(identity)
        if launch:
            card.update({
                "india_launch_date": launch["india_launch_date"],
                "india_launch_source": launch["india_launch_source"],
                "india_launch_evidence_status": "VERIFIED_SOURCE",
            })
            card["source_urls"].append(launch["india_launch_source"])
        cards_by_identity[identity] = card
        model_cards.append(card)

    # Prefer the frozen display name where punctuation differs from the source
    # model label (for example, Nothing Phone (3a) versus Phone 3a). This keeps
    # the model card customer-readable without changing the source identity.
    for product in preview:
        identity = (_norm(product.get("brand")), _norm(product.get("model")))
        card = cards_by_identity.get(identity)
        if card is None:
            raise ValueError(f"frozen model is absent from source universe: {identity}")
        card["brand"] = str(product.get("brand") or card["brand"])
        card["model"] = str(product.get("model") or card["model"])
        card["frozen_variant_ids"].append(str(product.get("canonical_product_id") or ""))
        if STATUS_ORDER.get("OFFICIAL_VERIFIED", 0) > STATUS_ORDER.get(card["status"], 0):
            card["status"] = "OFFICIAL_VERIFIED"
            card["status_reason"] = "Manufacturer-backed technical evidence is available for the frozen India research variants."
        source = product.get("official_source")
        if isinstance(source, str) and source.startswith("https://") and source not in card["source_urls"]:
            card["source_urls"].append(source)
        for spec in (product.get("specifications") or {}).values():
            source_url = spec.get("source_url") if isinstance(spec, dict) else None
            if isinstance(source_url, str) and source_url.startswith("https://") and source_url not in card["source_urls"]:
                card["source_urls"].append(source_url)

    for row in rows:
        identity = (_norm(row.get("brand")), _norm(row.get("model")))
        card = cards_by_identity.get(identity)
        if card is None:
            raise ValueError(f"discovery row is absent from source universe: {identity}")
        card["discovery_record_keys"].append(str(row["record_key"]))
        if STATUS_ORDER.get(row.get("status"), 0) > STATUS_ORDER.get(card["status"], 0):
            card["status"] = str(row["status"])
            card["status_reason"] = str(row.get("status_reason") or card["status_reason"])
        for source in row.get("source_urls") or []:
            if isinstance(source, str) and source.startswith("https://") and source not in card["source_urls"]:
                card["source_urls"].append(source)

    # Attach only model-shared fields that are identical across the frozen
    # variants.  Discovery records remain identity/variant evidence and do not
    # gain specifications merely because a model has a similarly named row.
    preview_by_identity: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for product in preview:
        identity = (_norm(product.get("brand")), _norm(product.get("model")))
        preview_by_identity.setdefault(identity, []).append(product)
    source_specs_by_identity = _load_existing_source_specs(root)
    for identity, card in cards_by_identity.items():
        preview_products = preview_by_identity.get(identity, [])
        preview_keys = {
            key for product in preview_products for key in (product.get("specifications") or {})
        }
        # Frozen P13.1 evidence is authoritative for its models. Existing
        # manufacturer evidence fills only fields that the frozen records do
        # not already cover; conflicting evidence is withheld by the merge.
        supplemental = [
            {"specifications": {key: item for key, item in (product.get("specifications") or {}).items() if key not in preview_keys}}
            for product in source_specs_by_identity.get(identity, [])
        ]
        specs, missing = _merge_model_specs(preview_products + supplemental)
        card["specifications"] = specs
        card["missing_specifications"] = missing
        card["available_specification_fields"] = [TECHNICAL_FIELD_LABELS[key] for key in specs]
        card["source_urls"] = list(dict.fromkeys(card["source_urls"]))

    _apply_workbook_research(root, model_cards)

    model_cards.sort(key=lambda card: (_norm(card["brand"]), _norm(card["model"]), card["model_key"]))
    if len(model_cards) != len(models):
        raise ValueError("public model card count diverges from source model count")
    if len({card["model_key"] for card in model_cards}) != len(model_cards):
        raise ValueError("public model cards contain duplicate model keys")
    if sum(len(card["discovery_record_keys"]) for card in model_cards) != len(rows):
        raise ValueError("public model cards do not retain every discovery record")
    if sum(len(card["frozen_variant_ids"]) for card in model_cards) != len(preview):
        raise ValueError("public model cards do not retain every frozen variant")

    discovery_identities = {(_norm(row.get("brand")), _norm(row.get("model"))) for row in rows}
    frozen_identities = {(_norm(row.get("brand")), _norm(row.get("model"))) for row in preview}
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
            "discovery_model_names": len(discovery_identities),
            "frozen_model_names": len(frozen_identities),
            "model_name_overlaps": len(discovery_identities & frozen_identities),
            "visible_model_cards": len(model_cards),
        },
        "status_counts": status_counts,
        "model_cards": model_cards,
        "records": rows,
    }
