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


def _load_verified_mobile_retailer_links(root: Path) -> dict[tuple[str, str], list[dict[str, Any]]]:
    """Load exact mobile listing evidence without turning it into a live offer.

    The research catalogue may show a direct listing only when the existing
    offer evidence binds retailer, listing ID, model and physical variant.
    Price, stock and CTA eligibility deliberately remain outside this view.
    """
    offers_path = root / "data/retailer_offers.json"
    coupons_path = root / "coupons.json"
    if not offers_path.is_file() or not coupons_path.is_file():
        return {}
    offers = _read_json(offers_path).get("offers") or []
    coupons = _read_json(coupons_path)
    mobile_ids = {
        f"cw-mobile-{item.get('id')}": item
        for item in coupons
        if isinstance(item, dict) and str(item.get("category") or "").casefold() in {"mobile", "mobiles", "phone", "phones"}
    }
    allowed_hosts = {
        "amazon": {"amazon.in", "www.amazon.in"},
        "flipkart": {"flipkart.com", "www.flipkart.com"},
        "croma": {"croma.com", "www.croma.com"},
    }
    result: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for offer in offers:
        if not isinstance(offer, dict) or offer.get("product_id") not in mobile_ids:
            continue
        retailer = str(offer.get("retailer") or "").casefold()
        url = str(offer.get("product_url") or "")
        parsed = urlparse(url)
        listing_id = str(offer.get("retailer_product_id") or "").strip()
        if (
            retailer not in allowed_hosts
            or parsed.scheme != "https"
            or parsed.hostname not in allowed_hosts[retailer]
            or not listing_id
            or not offer.get("brand")
            or not offer.get("model")
            or not offer.get("variant")
            or offer.get("source") not in {"retailer_page_verified", "amazon_primary_buybox", "retailer_price_observed"}
        ):
            continue
        identity = (_norm(offer.get("brand")), _norm(offer.get("model")))
        result.setdefault(identity, []).append({
            "retailer": retailer,
            "url": url,
            "retailer_product_id": listing_id,
            "variant": str(offer.get("variant")),
            "source": str(offer.get("source")),
            "confidence": offer.get("confidence"),
            "checked_at": str(offer.get("last_checked") or offer.get("observed_at") or ""),
            "exact_identity_verified": True,
        })
    for identity in result:
        result[identity] = sorted(
            result[identity], key=lambda item: (item["retailer"], item["variant"], item["url"])
        )
    return result


def _load_model_photos(root: Path, models: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Load reviewed photos by exact catalogue model key."""
    photos = _read_json(root / "data/mobile_model_photos.json")
    model_keys = {model["model_key"] for model in models}
    used_assets: set[str] = set()
    for key, photo in photos.items():
        asset = photo["url"]
        if key not in model_keys:
            raise ValueError(f"unknown model photo assignment: {key}")
        alias = photo.get("same_model_as")
        if alias:
            original = photos.get(alias)
            if (
                original is None or original.get("same_model_as")
                or not re.fullmatch(re.escape(alias) + r" [1-9][0-9]*gb", key)
                or {name: value for name, value in photo.items() if name != "same_model_as"} != original
            ):
                raise ValueError(f"invalid storage-only model photo alias: {key}")
        elif asset in used_assets:
            raise ValueError(f"duplicate model photo assignment: {key}")
        if not re.fullmatch(r"/assets/phone-photos/[a-z0-9-]+\.(?:jpg|png)", asset):
            raise ValueError(f"invalid local phone photo path: {asset}")
        if not (root / asset.lstrip("/")).is_file():
            raise ValueError(f"phone photo asset missing: {asset}")
        if not photo["source"].startswith("https://commons.wikimedia.org/wiki/File:"):
            raise ValueError(f"phone photo source missing: {key}")
        if not photo["author"].strip() or photo["license"] not in {"CC BY 3.0", "CC BY 4.0", "CC BY-SA 4.0", "CC0"}:
            raise ValueError(f"phone photo attribution or reuse license missing: {key}")
        if not photo["license_url"].startswith("https://creativecommons.org/"):
            raise ValueError(f"phone photo license URL missing: {key}")
        if not all(isinstance(photo[axis], int) and photo[axis] > 0 for axis in ("width", "height")):
            raise ValueError(f"phone photo dimensions missing: {key}")
        if not alias:
            used_assets.add(asset)
    return photos


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



# Model-shared manufacturer corrections. Only approved non-frozen variants
# may override an older incorrect imported fact; identity, rank and price stay
# unchanged. Unknown 'corrected' fields fail publication rather than silently
# superseding existing source evidence.
APPROVED_SPEC_CORRECTIONS = {
    ("samsung|galaxy f05", "network_support"): ("4G LTE", "https://www.samsung.com/in/smartphones/galaxy-f/galaxy-f05-blue-64gb-sm-e055fdbdins/"),
    ("xiaomi|14 ultra", "network_support"): ("5G", "https://www.mi.com/in/product/xiaomi-14-ultra/specs/"),
    ("poco|x7 pro", "battery_mah_typical"): (6550, "https://www.mi.com/global/support/faq/details/KA-522489/"),
    ("samsung|galaxy a57 5g", "chipset"): ("Exynos 1680", "https://news.samsung.com/sg/samsung-unveils-galaxy-a57-5g-and-galaxy-a37-5g-packing-pro-level-features-at-awesome-price"),
    ("samsung|galaxy f70 pro 5g", "chipset"): ("Qualcomm Snapdragon 6 Gen 3", "https://www.samsung.com/in/smartphones/galaxy-f/galaxy-f70-pro-5g-aura-green-128gb-sm-e476bzgbins/"),
    ("samsung|galaxy m47 5g", "chipset"): ("Qualcomm Snapdragon 6 Gen 3", "https://www.samsung.com/in/smartphones/galaxy-m/galaxy-m47-5g-rogue-red-128gb-sm-m476bzrbins/"),
}


# Small, source-bound supplements for the first Apple review batch. These are
# model-shared facts explicitly documented by Apple; variant-specific memory,
# battery capacity in mAh, and update-year promises remain pending when Apple
# does not publish them on the cited technical page.
APPLE_MODEL_SUPPLEMENTS = {
    "apple|iphone 11": {
        "display_type_description": "Liquid Retina HD display; 6.1-inch all-screen LCD with IPS technology.",
        "rear_camera_system": "Dual 12MP Wide and Ultra Wide cameras; optical image stabilization on the Wide camera.",
        "front_camera_system": "TrueDepth camera system with a 12MP front camera.",
        "battery_and_charging": "Built-in rechargeable lithium-ion battery; fast-charge capable; Qi wireless charging supported.",
        "operating_system": "iOS",
        "durability": "IP68-rated splash, water and dust resistance.",
    },
    "apple|iphone 13": {
        "display_type_description": "Super Retina XDR display; 6.1-inch all-screen OLED display.",
        "rear_camera_system": "Dual 12MP Wide and Ultra Wide cameras; sensor-shift optical image stabilization on the Wide camera.",
        "front_camera_system": "TrueDepth camera system with a 12MP front camera.",
        "battery_and_charging": "Built-in rechargeable lithium-ion battery; fast-charge capable; MagSafe and Qi wireless charging supported.",
        "operating_system": "iOS",
        "durability": "IP68-rated splash, water and dust resistance.",
    },
    "apple|iphone 15": {
        "display_type_description": "Super Retina XDR display; 6.1-inch all-screen OLED display.",
        "rear_camera_system": "48MP Main and 12MP Ultra Wide cameras; sensor-shift optical image stabilization on the Main camera.",
        "front_camera_system": "12MP TrueDepth front camera with autofocus.",
        "battery_and_charging": "Built-in rechargeable lithium-ion battery; USB-C charging; MagSafe and Qi2 wireless charging supported.",
        "operating_system": "iOS",
        "durability": "IP68-rated splash, water and dust resistance.",
    },
    "apple|iphone 15 plus": {
        "display_type_description": "Super Retina XDR display; 6.7-inch all-screen OLED display.",
        "rear_camera_system": "48MP Main and 12MP Ultra Wide cameras; sensor-shift optical image stabilization on the Main camera.",
        "front_camera_system": "12MP TrueDepth front camera with autofocus.",
        "battery_and_charging": "Built-in rechargeable lithium-ion battery; USB-C charging; MagSafe and Qi2 wireless charging supported.",
        "operating_system": "iOS",
        "durability": "IP68-rated splash, water and dust resistance.",
    },
    "apple|iphone 16": {
        "display_type_description": "Super Retina XDR display; 6.1-inch all-screen OLED display.",
        "rear_camera_system": "48MP Fusion Main and 12MP Ultra Wide cameras; sensor-shift optical image stabilization.",
        "front_camera_system": "12MP TrueDepth front camera with autofocus.",
        "battery_and_charging": "Built-in rechargeable lithium-ion battery; USB-C charging; MagSafe and Qi2 wireless charging supported.",
        "operating_system": "iOS",
        "durability": "IP68-rated splash, water and dust resistance.",
    },
    "apple|iphone 16 plus": {
        "display_type_description": "Super Retina XDR display; 6.7-inch all-screen OLED display.",
        "rear_camera_system": "48MP Fusion Main and 12MP Ultra Wide cameras; sensor-shift optical image stabilization.",
        "front_camera_system": "12MP TrueDepth front camera with autofocus.",
        "battery_and_charging": "Built-in rechargeable lithium-ion battery; USB-C charging; MagSafe and Qi2 wireless charging supported.",
        "operating_system": "iOS",
        "durability": "IP68-rated splash, water and dust resistance.",
    },
    "apple|iphone 16 pro": {
        "display_type_description": "Super Retina XDR display with ProMotion; 6.3-inch all-screen OLED display.",
        "rear_camera_system": "48MP Fusion Main, 48MP Ultra Wide and 12MP 5x Telephoto cameras; second-generation sensor-shift optical image stabilization.",
        "front_camera_system": "12MP TrueDepth front camera with autofocus.",
        "battery_and_charging": "Built-in rechargeable lithium-ion battery; USB-C charging; MagSafe and Qi2 wireless charging supported.",
        "operating_system": "iOS",
        "durability": "IP68-rated splash, water and dust resistance.",
    },
    "apple|iphone 16 pro max": {
        "display_type_description": "Super Retina XDR display with ProMotion; 6.9-inch all-screen OLED display.",
        "rear_camera_system": "48MP Fusion Main, 48MP Fusion Ultra Wide and 48MP Fusion Telephoto cameras; second-generation sensor-shift optical image stabilization.",
        "front_camera_system": "12MP TrueDepth front camera with autofocus.",
        "battery_and_charging": "Built-in rechargeable lithium-ion battery; USB-C charging; MagSafe and Qi2 wireless charging supported.",
        "operating_system": "iOS",
        "durability": "IP68-rated splash, water and dust resistance.",
    },
    "apple|iphone 16e": {
        "display_type_description": "Super Retina XDR display; 6.1-inch all-screen OLED display.",
        "rear_camera_system": "48MP Fusion Main camera with an enabled 12MP 2x Telephoto view; optical image stabilization.",
        "front_camera_system": "12MP TrueDepth front camera with autofocus.",
        "battery_and_charging": "Built-in rechargeable lithium-ion battery; USB-C charging with fast-charge support.",
        "operating_system": "iOS",
        "durability": "IP68-rated splash, water and dust resistance.",
    },
    "apple|iphone 16e iphone se 4": {
        "display_type_description": "Super Retina XDR display; 6.1-inch all-screen OLED display.",
        "rear_camera_system": "48MP Fusion Main camera with an enabled 12MP 2x Telephoto view; optical image stabilization.",
        "front_camera_system": "12MP TrueDepth front camera with autofocus.",
        "battery_and_charging": "Built-in rechargeable lithium-ion battery; USB-C charging with fast-charge support.",
        "operating_system": "iOS",
        "durability": "IP68-rated splash, water and dust resistance.",
    },
    "apple|iphone 17": {
        "display_type_description": "Super Retina XDR display with ProMotion; 6.3-inch all-screen OLED display.",
        "rear_camera_system": "48MP Dual Fusion camera system with a 48MP Fusion Main and 12MP optical-quality 2x Telephoto view; sensor-shift optical image stabilization.",
        "front_camera_system": "18MP Center Stage front camera with autofocus.",
        "battery_and_charging": "Built-in rechargeable lithium-ion battery; USB-C charging with fast-charge support.",
        "operating_system": "iOS",
        "durability": "IP68-rated splash, water and dust resistance.",
    },
    "apple|iphone 17 pro": {
        "display_type_description": "Super Retina XDR display with ProMotion; 6.3-inch all-screen OLED display.",
        "rear_camera_system": "48MP Pro Fusion Main, 48MP Fusion Ultra Wide and 48MP Fusion Telephoto cameras; second-generation sensor-shift optical image stabilization.",
        "front_camera_system": "18MP Center Stage front camera with autofocus.",
        "battery_and_charging": "Built-in rechargeable lithium-ion battery; USB-C charging with fast-charge support.",
        "operating_system": "iOS",
        "durability": "IP68-rated splash, water and dust resistance.",
    },
    "apple|iphone 17 pro max": {
        "display_type_description": "Super Retina XDR display with ProMotion; 6.9-inch all-screen OLED display.",
        "rear_camera_system": "48MP Pro Fusion Main, 48MP Fusion Ultra Wide and 48MP Fusion Telephoto cameras; second-generation sensor-shift optical image stabilization.",
        "front_camera_system": "18MP Center Stage front camera with autofocus.",
        "battery_and_charging": "Built-in rechargeable lithium-ion battery; USB-C charging with fast-charge support.",
        "operating_system": "iOS",
        "durability": "IP68-rated splash, water and dust resistance.",
    },
    "apple|iphone 17e": {
        "display_type_description": "Super Retina XDR display; 6.1-inch all-screen OLED display.",
        "rear_camera_system": "48MP Fusion Main camera with an enabled 12MP 2x Telephoto view; optical image stabilization.",
        "front_camera_system": "12MP TrueDepth front camera with autofocus.",
        "battery_and_charging": "Built-in rechargeable lithium-ion battery; USB-C charging with fast-charge support.",
        "operating_system": "iOS",
        "durability": "IP68-rated splash, water and dust resistance.",
    },
    "apple|iphone 18 pro": {
        "display_type_description": "Super Retina XDR display with ProMotion; 6.3-inch all-screen OLED display.",
        "rear_camera_system": "48MP Pro Fusion Main, 48MP Fusion Ultra Wide and 48MP Fusion Telephoto cameras; second-generation sensor-shift optical image stabilization.",
        "front_camera_system": "18MP Center Stage front camera with autofocus.",
        "battery_and_charging": "Built-in rechargeable lithium-ion battery; USB-C charging; MagSafe and Qi2 wireless charging supported.",
        "operating_system": "iOS 27",
        "durability": "IP68-rated splash, water and dust resistance.",
    },
    "apple|iphone 18 pro max": {
        "display_type_description": "Super Retina XDR display with ProMotion; 6.9-inch all-screen OLED display.",
        "rear_camera_system": "48MP Pro Fusion Main, 48MP Fusion Ultra Wide and 48MP Fusion Telephoto cameras; second-generation sensor-shift optical image stabilization.",
        "front_camera_system": "18MP Center Stage front camera with autofocus.",
        "battery_and_charging": "Built-in rechargeable lithium-ion battery; USB-C charging; MagSafe and Qi2 wireless charging supported.",
        "operating_system": "iOS 27",
        "durability": "IP68-rated splash, water and dust resistance.",
    },
    "apple|iphone air": {
        "display_type_description": "Super Retina XDR display with ProMotion; 6.5-inch all-screen OLED display.",
        "rear_camera_system": "48MP Fusion Main camera with an enabled 12MP optical-quality 2x Telephoto view; sensor-shift optical image stabilization.",
        "front_camera_system": "18MP Center Stage front camera with autofocus.",
        "battery_and_charging": "Built-in rechargeable lithium-ion battery; USB-C charging; MagSafe and Qi2 wireless charging supported.",
        "operating_system": "iOS 27",
        "durability": "IP68-rated splash, water and dust resistance.",
    },
    "apple|iphone se 2022 iphone se 3": {
        "display_type_description": "Retina HD display; 4.7-inch widescreen LCD with IPS technology.",
        "rear_camera_system": "12MP Main camera with optical image stabilization.",
        "front_camera_system": "7MP FaceTime HD front camera.",
        "battery_and_charging": "Built-in rechargeable lithium-ion battery; fast-charge capable; Qi wireless charging supported.",
        "operating_system": "iOS",
        "durability": "IP67-rated splash, water and dust resistance.",
    },
    "cmf|phone 1": {
        "display_type_description": "6.67-inch Super AMOLED display with adaptive refresh rate up to 120Hz.",
        "rear_camera_system": "50MP Sony rear camera system with Nothing's TrueLens Engine computational photography.",
        "front_camera_system": "16MP front camera.",
        "battery_and_charging": "5000mAh battery with 33W wired charging.",
        "operating_system": "Nothing OS, Android-based.",
    },
    "google|pixel 10": {
        "display_type_description": "6.3-inch Actua OLED display with Smooth Display from 60Hz to 120Hz.",
        "rear_camera_system": "48MP wide, 13MP ultrawide and 10.8MP 5x telephoto cameras; optical and electronic stabilization on wide and telephoto.",
        "front_camera_system": "10.5MP Dual PD selfie camera with autofocus.",
        "battery_and_charging": "Typical 4970mAh battery; 30W USB-C PPS fast charging; Pixelsnap Qi2 wireless charging up to 15W.",
        "operating_system": "Android.",
        "durability": "IP68 dust and water resistance.",
    },
    "google|pixel 10a": {
        "display_type_description": "160mm Actua pOLED display with Smooth Display from 60Hz to 120Hz.",
        "rear_camera_system": "48MP wide and 13MP ultrawide cameras; optical and electronic stabilization on the wide camera.",
        "front_camera_system": "13MP selfie camera.",
        "battery_and_charging": "Typical 5100mAh battery; up to 50% in about 30 minutes with 45W USB-C PPS charging; Qi wireless charging.",
        "operating_system": "Android.",
        "durability": "IP68 dust and water resistance.",
    },
    "google|pixel 11": {
        "display_type_description": "6.3-inch Actua OLED display with Smooth Display from 60Hz to 120Hz.",
        "rear_camera_system": "48MP wide, 13MP ultrawide and 10.8MP 5x telephoto cameras; optical and electronic stabilization on wide and telephoto.",
        "front_camera_system": "10.5MP Dual PD selfie camera with autofocus.",
        "battery_and_charging": "Typical 4985mAh battery; up to 55% in about 30 minutes with 30W USB-C PPS charging; Pixelsnap Qi2.2 wireless charging up to 25W.",
        "operating_system": "Android 17.",
        "durability": "IP68 dust and water resistance.",
    },
    "google|pixel 11 pro": {
        "display_type_description": "6.3-inch Super Actua LTPO OLED display with Smooth Display from 1Hz to 120Hz.",
        "rear_camera_system": "50MP wide, 48MP ultrawide and 48MP 5x telephoto cameras; optical and electronic stabilization on wide and telephoto.",
        "front_camera_system": "42MP Dual PD selfie camera with autofocus.",
        "battery_and_charging": "Typical 4850mAh battery; up to 55% in about 30 minutes with 30W USB-C PPS charging; Pixelsnap Qi2.2 wireless charging up to 25W.",
        "operating_system": "Android 17.",
        "durability": "IP68 dust and water resistance.",
    },
    "google|pixel 7a": {
        "display_type_description": "6.1-inch OLED display with refresh rate up to 90Hz.",
        "rear_camera_system": "64MP wide and 13MP ultrawide cameras.",
        "front_camera_system": "13MP selfie camera.",
        "battery_and_charging": "4385mAh battery; wired fast charging; Qi wireless charging.",
        "operating_system": "Android.",
        "durability": "IP67 dust and water resistance.",
    },
    "google|pixel 8a": {
        "display_type_description": "6.1-inch Actua OLED display with refresh rate up to 120Hz.",
        "rear_camera_system": "64MP wide and 13MP ultrawide cameras.",
        "front_camera_system": "13MP selfie camera.",
        "battery_and_charging": "Typical 4492mAh battery; wired fast charging; Qi wireless charging.",
        "operating_system": "Android.",
        "durability": "IP67 dust and water resistance.",
    },
    "google|pixel 9": {
        "display_type_description": "6.3-inch Actua OLED display with Smooth Display from 60Hz to 120Hz.",
        "rear_camera_system": "50MP wide and 48MP ultrawide cameras with Macro Focus; Super Res Zoom up to 8x.",
        "front_camera_system": "10.5MP selfie camera with autofocus.",
        "battery_and_charging": "Typical 4700mAh battery; up to 55% in about 30 minutes with 45W USB-C charging; Qi-certified wireless charging.",
        "operating_system": "Android.",
        "durability": "IP68 dust and water resistance.",
    },
    "google|pixel 9 pro": {
        "display_type_description": "6.3-inch Super Actua LTPO OLED display with Smooth Display from 1Hz to 120Hz.",
        "rear_camera_system": "50MP wide, 48MP ultrawide with Macro Focus and 48MP 5x telephoto cameras.",
        "front_camera_system": "42MP Dual PD selfie camera with autofocus.",
        "battery_and_charging": "Typical 4700mAh battery; fast USB-C charging; Qi-certified wireless charging.",
        "operating_system": "Android.",
        "durability": "IP68 dust and water resistance.",
    },
    "google|pixel 9 pro xl": {
        "display_type_description": "6.8-inch Super Actua LTPO OLED display with Smooth Display from 1Hz to 120Hz.",
        "rear_camera_system": "50MP wide, 48MP ultrawide with Macro Focus and 48MP 5x telephoto cameras.",
        "front_camera_system": "42MP Dual PD selfie camera with autofocus.",
        "battery_and_charging": "Typical 5060mAh battery; fast USB-C charging; Qi-certified wireless charging.",
        "operating_system": "Android.",
        "durability": "IP68 dust and water resistance.",
    },
    "google|pixel 9a": {
        "display_type_description": "6.3-inch Actua pOLED display with Smooth Display from 60Hz to 120Hz.",
        "rear_camera_system": "48MP wide and 13MP ultrawide cameras; optical and electronic stabilization on the wide camera.",
        "front_camera_system": "13MP selfie camera.",
        "battery_and_charging": "Typical 5100mAh battery; fast charging; Qi-certified wireless charging.",
        "operating_system": "Android.",
        "durability": "IP68 dust and water resistance.",
    },
    "infinix|gt 30 pro": {
        "display_type_description": "1.5K AMOLED display with a 144Hz refresh rate.",
        "rear_camera_system": "108MP main and 8MP ultra-wide rear cameras.",
        "front_camera_system": "13MP front camera.",
        "battery_and_charging": "5500mAh battery; 45W wired charging and 30W wireless charging.",
        "operating_system": "XOS 15 powered by Android 15.",
        "durability": "IP64 splash and dust resistance.",
    },
    "infinix|hot 30i": {
        "display_type_description": "6.6-inch HD+ IPS display.",
        "rear_camera_system": "50MP primary camera with AI lens.",
        "front_camera_system": "5MP front camera.",
        "battery_and_charging": "5000mAh lithium-ion polymer battery with quick charging.",
        "operating_system": "Android 12.",
    },
    "infinix|hot 50 5g": {
        "display_type_description": "120Hz punch-hole display with Dynamic Bar.",
        "rear_camera_system": "48MP rear camera.",
        "front_camera_system": "Front camera specification is not confirmed in the cited page.",
        "battery_and_charging": "5000mAh battery with 18W fast charging.",
        "operating_system": "Android-based XOS; version not confirmed in the cited page.",
        "durability": "IP54-rated dust and splash resistance.",
    },
    "infinix|hot 70 pro 5g": {
        "display_type_description": "6.76-inch LCD display with a 144Hz refresh rate.",
        "rear_camera_system": "Rear camera system is not fully confirmed in the cited product page.",
        "front_camera_system": "Front camera specification is not confirmed in the cited product page.",
        "battery_and_charging": "6000mAh battery with 45W wired charging.",
        "operating_system": "Android-based XOS; version not confirmed in the cited page.",
        "durability": "IP68-rated dust and water resistance.",
    },
    "infinix|note 50x": {
        "display_type_description": "6.67-inch IPS display with a 120Hz refresh rate.",
        "rear_camera_system": "50MP dual rear camera system.",
        "front_camera_system": "8MP front camera.",
        "battery_and_charging": "5500mAh battery with 45W wired charging.",
        "operating_system": "XOS 15.",
        "durability": "IP64-rated dust and splash resistance; MIL-STD-810H certification is listed by the manufacturer.",
    },
    "infinix|note 60 pro 5g": {
        "display_type_description": "6.78-inch AMOLED display.",
        "rear_camera_system": "Rear camera system is not fully confirmed in the cited product page.",
        "front_camera_system": "Front camera specification is not confirmed in the cited product page.",
        "battery_and_charging": "6500mAh battery with 90W wired charging.",
        "operating_system": "Android-based XOS; version not confirmed in the cited page.",
        "durability": "IP64-rated dust and splash resistance.",
    },
    "infinix|smart 20 4g": {
        "display_type_description": "6.78-inch HD+ IPS a-Si LCD display with refresh rates up to 120Hz.",
        "rear_camera_system": "8MP rear camera with autofocus and rear dual flash.",
        "front_camera_system": "8MP front camera.",
        "battery_and_charging": "5200mAh battery with 15W charging; 10W charger included.",
        "operating_system": "XOS 16 powered by Android 16.",
        "durability": "IP64-rated dust and splash resistance.",
    },
    "infinix|smart 8 128gb": {
        "display_type_description": "6.76-inch IPS a-Si LCD display with 60/90Hz refresh rate.",
        "rear_camera_system": "50MP dual AI camera.",
        "battery_and_charging": "5000mAh battery with 10W charging.",
        "operating_system": "Android 13 Go.",
    },
    "infinix|smart 8 hd": {
        "display_type_description": "6.76-inch IPS a-Si LCD display with 60/90Hz refresh rate.",
        "rear_camera_system": "13MP rear camera with AI lens.",
        "front_camera_system": "8MP front camera.",
        "battery_and_charging": "5000mAh battery with 10W charging.",
        "operating_system": "XOS 13.",
    },
    "iqoo|13": {
        "display_type_description": "6.82-inch AMOLED display with 3168 × 1440 resolution.",
        "rear_camera_system": "50MP main, 50MP ultra-wide and 50MP 2x telephoto cameras.",
        "front_camera_system": "32MP front camera.",
        "battery_and_charging": "6000mAh battery with 120W fast charging.",
        "operating_system": "Funtouch OS 15 based on Android 15.",
    },
    "iqoo|15": {
        "display_type_description": "6.85-inch AMOLED display with 3168 × 1440 resolution.",
        "rear_camera_system": "50MP main, 50MP ultra-wide and 50MP 3x periscope cameras.",
        "front_camera_system": "32MP front camera.",
        "battery_and_charging": "7000mAh battery with 100W wired and 40W wireless charging.",
        "operating_system": "OriginOS 6 based on Android 16.",
    },
    "iqoo|15r": {
        "display_type_description": "6.59-inch AMOLED display with 2750 × 1260 resolution.",
        "rear_camera_system": "50MP main and 8MP ultra-wide cameras.",
        "front_camera_system": "32MP front camera.",
        "battery_and_charging": "7600mAh battery with 100W charging.",
        "operating_system": "OriginOS 6.0.",
    },
    "iqoo|neo 10": {
        "display_type_description": "6.78-inch AMOLED display with 2800 × 1260 (1.5K) resolution.",
        "rear_camera_system": "50MP main and 8MP ultra-wide cameras.",
        "front_camera_system": "32MP front camera.",
        "battery_and_charging": "7000mAh typical battery with 120W charging.",
    },
    "iqoo|neo 9 pro": {
        "display_type_description": "6.78-inch AMOLED display with 2800 × 1260 (1.5K) resolution.",
        "rear_camera_system": "50MP main and 8MP ultra-wide cameras.",
        "battery_and_charging": "5160mAh typical battery (5040mAh minimum) with 120W fast charging.",
        "operating_system": "Funtouch OS 14 based on Android 14.",
    },
    "iqoo|z10r": {
        "display_type_description": "6.77-inch AMOLED display with 2392 × 1080 resolution.",
        "rear_camera_system": "50MP Sony main and 2MP bokeh cameras.",
        "front_camera_system": "32MP front camera.",
        "battery_and_charging": "5700mAh typical battery with 44W charging.",
        "operating_system": "Funtouch OS 15 based on Android 15.",
    },
    "iqoo|z11 5g": {
        "display_type_description": "6.83-inch AMOLED display with 2800 × 1260 resolution.",
        "rear_camera_system": "50MP main and 8MP ultra-wide cameras.",
        "front_camera_system": "32MP front camera.",
        "battery_and_charging": "7050mAh battery with 44W charging.",
        "operating_system": "OriginOS 6.0.",
    },
    "iqoo|z11 lite 5g": {
        "display_type_description": "6.74-inch LCD display with 1600 × 720 resolution.",
        "rear_camera_system": "50MP rear camera with 0.08MP secondary camera.",
        "front_camera_system": "5MP front camera.",
        "battery_and_charging": "6500mAh battery with 44W fast charging.",
        "operating_system": "OriginOS 6.0.",
    },
    "iqoo|z11x": {
        "display_type_description": "6.76-inch LCD display with 2344 × 1080 resolution.",
        "rear_camera_system": "50MP Sony IMX852 main and 2MP bokeh cameras.",
        "front_camera_system": "32MP front camera.",
        "battery_and_charging": "7200mAh battery with 44W charging.",
        "operating_system": "OriginOS 6.0.",
    },
    "iqoo|z9 5g": {
        "display_type_description": "6.67-inch 120Hz AMOLED display.",
        "rear_camera_system": "50MP Sony IMX882 main camera with OIS.",
        "battery_and_charging": "5000mAh battery.",
        "operating_system": "Funtouch OS 14 based on Android 14.",
        "durability": "IP54-rated dust and splash resistance.",
    },
    "iqoo|z9x 5g": {
        "display_type_description": "6.72-inch LCD display with 2408 × 1080 resolution.",
        "rear_camera_system": "50MP AI main and 2MP bokeh cameras.",
        "front_camera_system": "8MP front camera.",
        "battery_and_charging": "6000mAh typical battery (5870mAh minimum) with 44W fast charging.",
        "operating_system": "Funtouch OS 14 based on Android 14.",
    },
    "lava|agni 4": {
        "display_type_description": "6.67-inch flat AMOLED display with 120Hz refresh rate and 1220 × 2712 resolution.",
        "rear_camera_system": "50MP OIS main and 8MP ultra-wide cameras.",
        "front_camera_system": "50MP Samsung front camera with EIS.",
        "battery_and_charging": "5000mAh Li-Po battery with 66W fast charging.",
        "operating_system": "Android 15 with clean Android and zero bloatware.",
    },
    "lava|bold n2": {
        "battery_and_charging": "5000mAh battery with Type-C port and 10W charging.",
    },
    "lava|bold n2 lite": {
        "display_size_description": "17.13cm (6.75-inch) HD+ display.",
        "battery_and_charging": "5000mAh battery with Type-C port and 10W charging.",
    },
    "lava|virat v1": {
        "display_size_description": "17.13cm (6.75-inch) HD+ display.",
        "battery_and_charging": "5000mAh battery with Type-C port and 10W charging.",
        "durability": "IP64-rated dust and water resistance.",
    },
    "lava|virat v1 5g": {
        "display_type_description": "6.75-inch HD+ display with 120Hz refresh rate.",
        "battery_and_charging": "6000mAh battery with Type-C charging; 10W charging and 18W support.",
        "durability": "IP64-rated dust and water resistance.",
    },
    "motorola|edge 50 fusion": {
        "display_type_description": "6.67-inch pOLED Endless Edge display with 144Hz refresh rate.",
        "battery_and_charging": "5000mAh battery with 68W TurboPower charging.",
        "operating_system": "Android 14.",
        "durability": "IP68-rated water and dust resistance.",
    },
    "motorola|edge 50 pro": {
        "display_type_description": "6.7-inch 1.5K pOLED display with 144Hz refresh rate.",
        "rear_camera_system": "50MP OIS main, 13MP ultra-wide/macro and 10MP 3x telephoto cameras.",
        "front_camera_system": "50MP front camera with autofocus.",
        "battery_and_charging": "4500mAh battery with 125W wired and up to 50W wireless charging.",
        "operating_system": "Hello UI based on Android 14.",
        "durability": "IP68-rated water resistance.",
    },
    "motorola|edge 50 ultra": {
        "display_type_description": "6.7-inch 1.5K pOLED display with 144Hz refresh rate.",
        "battery_and_charging": "4500mAh battery with 125W wired and up to 50W wireless charging.",
        "operating_system": "Android 14.",
        "durability": "IP68-rated water and dust resistance.",
    },
    "motorola|edge 60 fusion": {
        "display_type_description": "6.67-inch 1.5K pOLED quad-curved display with 120Hz refresh rate.",
        "battery_and_charging": "5500mAh battery with 68W TurboPower charging.",
        "operating_system": "Android 15 with 3 OS upgrades and 4 years of security updates.",
        "durability": "IP68/IP69 water resistance with MIL-STD-810H certification.",
    },
    "motorola|edge 60 pro": {
        "display_type_description": "6.7-inch 1.5K pOLED quad-curved display with 120Hz refresh rate.",
        "rear_camera_system": "50MP OIS main, 50MP ultra-wide/macro and 10MP 3x telephoto cameras.",
        "front_camera_system": "50MP front camera.",
        "battery_and_charging": "6000mAh battery with 90W wired and 15W wireless charging.",
        "operating_system": "Android 16 with 3 OS upgrades and 4 years of security updates.",
        "durability": "IP68/IP69 water and dust protection with MIL-STD-810H certification.",
    },
    "motorola|edge 70": {
        "display_type_description": "6.67-inch Extreme AMOLED display with 120Hz refresh rate.",
        "rear_camera_system": "50MP OIS main and 50MP ultra-wide cameras.",
        "front_camera_system": "50MP front camera.",
        "battery_and_charging": "5000mAh silicon-carbon battery with 68W wired and 15W wireless charging.",
        "operating_system": "Android 16.",
        "durability": "IP69/IP68 protection with MIL-STD-810H certification.",
    },
    "motorola|edge 70 fusion": {
        "display_type_description": "6.8-inch Extreme AMOLED display with up to 144Hz refresh rate.",
        "rear_camera_system": "50MP OIS main and 13MP ultra-wide/macro cameras.",
        "front_camera_system": "32MP front camera.",
        "battery_and_charging": "7000mAh battery with 68W TurboPower charging.",
        "operating_system": "Android 16.",
        "durability": "IP69/IP68 protection with MIL-STD-810H certification.",
    },
    "motorola|signature": {
        "display_type_description": "6.8-inch Extreme AMOLED display with up to 165Hz refresh rate.",
        "rear_camera_system": "50MP main, 50MP ultra-wide and 50MP 3x periscope telephoto cameras.",
        "battery_and_charging": "5200mAh silicon-carbon battery with 90W wired and 50W wireless charging.",
        "operating_system": "Android 16.",
        "durability": "IP69/IP68 protection with MIL-STD-810H certification.",
    },
    "nothing|phone 2a": {
        "display_type_description": "6.7-inch flexible AMOLED display with 120Hz adaptive refresh rate.",
        "rear_camera_system": "50MP main and 50MP ultra-wide cameras with OIS/EIS on the main camera.",
        "front_camera_system": "32MP front camera.",
        "battery_and_charging": "5000mAh battery with 45W fast charging.",
        "operating_system": "Nothing OS powered by Android 15.",
        "durability": "IP54-rated dust and water resistance.",
    },
    "nothing|phone 2a plus": {
        "display_type_description": "6.7-inch flexible AMOLED display with 120Hz adaptive refresh rate.",
        "rear_camera_system": "50MP main and 50MP ultra-wide cameras with OIS/EIS on the main camera.",
        "front_camera_system": "50MP front camera.",
        "battery_and_charging": "5000mAh battery with 50W fast charging.",
        "operating_system": "Nothing OS 2.6 powered by Android 14.",
        "durability": "IP54-rated dust and water resistance.",
    },
    "nothing|phone 3a": {
        "display_type_description": "6.77-inch FHD+ flexible AMOLED display with 120Hz adaptive refresh rate.",
        "rear_camera_system": "50MP OIS main, 50MP 2x telephoto and 8MP ultra-wide cameras.",
        "front_camera_system": "32MP front camera.",
        "battery_and_charging": "5000mAh battery with 50W fast charging.",
        "operating_system": "Nothing OS 3 powered by Android 15.",
        "durability": "IP64-rated dust and water resistance.",
    },
    "nothing|phone 3a pro": {
        "display_type_description": "6.77-inch FHD+ flexible AMOLED display with 120Hz adaptive refresh rate.",
        "rear_camera_system": "50MP OIS main, 50MP 3x periscope telephoto and 8MP ultra-wide cameras.",
        "front_camera_system": "50MP front camera.",
        "battery_and_charging": "5000mAh battery with 50W fast charging.",
        "operating_system": "Nothing OS 3 powered by Android 15.",
        "durability": "IP64-rated dust and water resistance.",
    },
    "nothing|phone 4a pro": {
        "rear_camera_system": "50MP OIS periscope camera with up to 140x ultra zoom; the cited page identifies a 3-camera system with a Sony sensor.",
        "operating_system": "Nothing OS with Essential AI tools.",
    },
    "nothing|phone 4b": {
        "rear_camera_system": "50MP main camera with 4K video recording.",
        "operating_system": "Nothing OS with Essential AI tools.",
    },
    "oneplus|12": {
        "display_type_description": "6.82-inch 120Hz ProXDR LTPO display with 3168 × 1440 QHD+ resolution.",
        "rear_camera_system": "50MP LYT-808 OIS wide, 64MP periscope telephoto and 48MP ultra-wide cameras.",
        "battery_and_charging": "5400mAh battery with 100W wired and 50W wireless charging.",
        "operating_system": "OxygenOS 14 based on Android 14.",
    },
    "oneplus|12r": {
        "display_type_description": "6.78-inch 120Hz AMOLED ProXDR LTPO display with 2780 × 1264 resolution.",
        "rear_camera_system": "50MP OIS main, 8MP ultra-wide and 2MP macro cameras.",
        "battery_and_charging": "5500mAh battery with 100W SUPERVOOC charging.",
        "operating_system": "OxygenOS 14 based on Android 14.",
    },
    "oneplus|13": {
        "display_type_description": "6.82-inch 120Hz ProXDR LTPO 4.1 display with 3168 × 1440 QHD+ resolution.",
        "rear_camera_system": "50MP wide, 50MP ultra-wide and 50MP telephoto cameras.",
        "battery_and_charging": "6000mAh battery with 100W wired and 50W wireless charging.",
        "operating_system": "OxygenOS 15 based on Android 15.",
    },
    "oneplus|13r": {
        "display_type_description": "6.78-inch 120Hz ProXDR LTPO 4.1 display with 2780 × 1264 resolution.",
        "rear_camera_system": "50MP OIS main, 50MP 2x telephoto and 8MP ultra-wide cameras.",
        "battery_and_charging": "6000mAh battery with 80W SUPERVOOC charging.",
        "operating_system": "OxygenOS 15 based on Android 15.",
    },
    "oneplus|13s": {
        "display_type_description": "6.32-inch compact display with 120Hz refresh rate.",
        "rear_camera_system": "50MP autofocus wide and 50MP autofocus 2x telephoto cameras.",
        "front_camera_system": "32MP autofocus front camera.",
        "battery_and_charging": "5850mAh battery with 80W SUPERVOOC fast charging.",
    },
    "oneplus|15r": {
        "display_type_description": "165Hz display; exact panel type and resolution remain unconfirmed on the cited page.",
        "rear_camera_system": "50MP Sony IMX906 OIS main and 8MP ultra-wide cameras.",
        "front_camera_system": "32MP autofocus front camera.",
        "battery_and_charging": "7400mAh battery with 80W SUPERVOOC charging.",
        "operating_system": "OxygenOS 16.",
    },
    "oneplus|15r 16gb": {
        "display_type_description": "165Hz display; exact panel type and resolution remain unconfirmed on the cited page.",
        "rear_camera_system": "50MP Sony IMX906 OIS main and 8MP ultra-wide cameras.",
        "front_camera_system": "32MP autofocus front camera.",
        "battery_and_charging": "7400mAh battery with 80W SUPERVOOC charging.",
        "operating_system": "OxygenOS 16.",
    },
    "oneplus|n6 5g": {
        "display_type_description": "120Hz display; exact panel type and resolution remain unconfirmed on the cited page.",
        "rear_camera_system": "50MP main camera with 60fps video recording.",
        "battery_and_charging": "8000mAh battery with 45W SUPERVOOC fast charging.",
        "operating_system": "OxygenOS 16.",
    },
    "oneplus|n6x 5g": {
        "display_type_description": "6.8-inch display with 120Hz refresh rate.",
        "battery_and_charging": "7000mAh battery with 45W SUPERVOOC fast charging.",
        "operating_system": "OxygenOS 16.",
        "durability": "MIL-STD-810H and IP64 durability ratings.",
    },
    "oneplus|nord 4": {
        "display_type_description": "6.74-inch AMOLED display with 120Hz refresh rate.",
        "rear_camera_system": "50MP OIS main and 8MP ultra-wide cameras.",
        "front_camera_system": "16MP front camera.",
        "battery_and_charging": "5500mAh battery with 100W SUPERVOOC charging.",
        "operating_system": "OxygenOS 14.1 based on Android 14.",
    },
    "oneplus|nord 5": {
        "display_type_description": "144Hz AMOLED display.",
        "rear_camera_system": "50MP rear camera system; the cited page also describes 50MP front and back cameras.",
        "front_camera_system": "50MP front camera.",
    },
    "oneplus|nord 6": {
        "display_type_description": "165Hz Sunburst AMOLED display.",
        "rear_camera_system": "50MP Sony main camera with dual-axis OIS.",
        "front_camera_system": "32MP front camera with multi-focus sensor.",
        "battery_and_charging": "9000mAh battery with 80W charging.",
    },
    "oneplus|nord ce 6 5g": {
        "display_type_description": "1.5K AMOLED display with 144Hz refresh rate.",
        "battery_and_charging": "8000mAh battery with power-bank reverse charging.",
    },
    "oneplus|nord ce 6 lite 5g": {
        "display_type_description": "144Hz display with up to 1000 nits peak brightness.",
        "rear_camera_system": "50MP main camera with 4K video and 4K Motion Photos.",
        "battery_and_charging": "7000mAh battery with 45W SUPERVOOC fast charging.",
        "operating_system": "OxygenOS 16.",
    },
    "oneplus|nord ce4": {
        "rear_camera_system": "50MP Sony LYT600 main and 8MP Sony IMX355 ultra-wide cameras with OIS/EIS support.",
        "battery_and_charging": "5500mAh battery with 100W SUPERVOOC charging.",
        "operating_system": "OxygenOS 14 based on Android 14.",
    },
    "oppo|a17": {
        "display_type_description": "6.56-inch LCD display with HD+ 1612 × 720 resolution.",
        "rear_camera_system": "50MP main and secondary rear camera system.",
        "front_camera_system": "5MP front camera.",
        "battery_and_charging": "5000mAh typical battery.",
        "operating_system": "ColorOS 12.1.",
    },
    "oppo|a38": {
        "display_type_description": "6.56-inch LCD display with 90/60Hz refresh rate and HD+ 1612 × 720 resolution.",
        "rear_camera_system": "50MP main and 2MP mono cameras.",
        "front_camera_system": "5MP front camera.",
        "battery_and_charging": "5000mAh typical battery with 33W SUPERVOOC charging.",
        "operating_system": "ColorOS 13.1.",
    },
    "oppo|a3x 128gb": {
        "display_type_description": "LCD display with 90Hz refresh rate and 1604 × 720 resolution.",
        "rear_camera_system": "8MP main rear camera.",
        "front_camera_system": "5MP front camera.",
        "battery_and_charging": "5100mAh typical battery with 45W SUPERVOOC 2.0 charging.",
        "operating_system": "ColorOS 14.0.",
    },
    "oppo|a5 5g": {
        "display_type_description": "120Hz ultra-bright display.",
        "rear_camera_system": "50MP main and 2MP depth cameras.",
        "front_camera_system": "8MP front camera.",
        "battery_and_charging": "6000mAh battery with 45W SUPERVOOC charging.",
        "durability": "IP65 water and dust resistance with MIL-STD 810H/SGS-tested shock resistance.",
    },
    "oppo|a5x": {
        "display_type_description": "16.94cm LCD display with up to 90Hz refresh rate and 720 × 1604 resolution.",
        "rear_camera_system": "32MP autofocus main camera.",
        "front_camera_system": "5MP front camera.",
        "battery_and_charging": "6000mAh battery with 45W SUPERVOOC charging.",
        "durability": "IP65 water and dust resistance with damage-proof 360° Armour Body.",
    },
    "oppo|a6 pro": {
        "display_type_description": "120Hz ultra-bright 17.15cm LCD display.",
        "battery_and_charging": "7000mAh battery with 80W SUPERVOOC charging.",
        "operating_system": "ColorOS 15 based on Android 15.",
        "durability": "IP69, IP68 and IP66 water and dust resistance.",
    },
    "oppo|a6c 4g": {
        "display_type_description": "17.15cm LCD display with 120Hz refresh rate and HD+ 1570 × 720 resolution.",
        "chipset": "UNISOC T7250.",
        "rear_camera_system": "13MP autofocus main camera.",
        "front_camera_system": "5MP front camera.",
        "battery_and_charging": "7000mAh battery with 15W charging and 15W PD support.",
    },
    "oppo|f31": {
        "display_type_description": "120Hz AMOLED display.",
        "rear_camera_system": "50MP main camera with two 2MP portrait cameras.",
        "front_camera_system": "16MP front camera.",
        "battery_and_charging": "7000mAh battery with 80W SUPERVOOC charging.",
        "durability": "IP69, IP68 and IP66 water and dust resistance.",
    },
    "oppo|f31 pro plus": {
        "display_type_description": "17.27cm flexible AMOLED display with 120Hz refresh rate and FHD+ 2800 × 1280 resolution.",
        "rear_camera_system": "50MP OIS main and 2MP monochrome cameras.",
        "front_camera_system": "32MP front camera.",
        "battery_and_charging": "7000mAh battery with 80W SUPERVOOC charging.",
        "chipset": "Qualcomm Snapdragon 7 Gen 3.",
    },
    "oppo|f33 pro 5g": {
        "display_type_description": "6.57-inch flat AMOLED display with 120Hz refresh rate.",
        "rear_camera_system": "50MP main and 2MP portrait cameras.",
        "front_camera_system": "50MP ultra-wide selfie camera with OIS and autofocus.",
        "battery_and_charging": "7000mAh battery with 80W SUPERVOOC charging.",
        "operating_system": "ColorOS 16 based on Android.",
        "durability": "IP69K, IP68 and IP66 water and dust resistance.",
    },
    "oppo|find x9 5g": {
        "display_type_description": "16.74cm flexible AMOLED display with 120Hz refresh rate and FHD+ 2760 × 1256 resolution.",
        "rear_camera_system": "50MP OIS wide, 50MP autofocus ultra-wide, 50MP OIS telephoto and 2MP monochrome cameras.",
        "front_camera_system": "32MP front camera.",
        "battery_and_charging": "7025mAh battery with 80W wired and 50W AIRVOOC wireless charging.",
        "chipset": "MediaTek Dimensity 9500.",
        "operating_system": "ColorOS 16.0.",
    },
    "oppo|k12x": {
        "display_type_description": "120Hz ultra-bright display.",
        "battery_and_charging": "5100mAh battery with 45W SUPERVOOC charging.",
        "durability": "360° Damage-Proof Armour Body with Splash Touch.",
    },
    "oppo|k13 5g": {
        "display_type_description": "16.94cm rigid AMOLED display with 120Hz refresh rate and FHD+ 1080 × 2400 resolution.",
        "rear_camera_system": "50MP main and 2MP monochrome cameras.",
        "front_camera_system": "16MP front camera.",
        "battery_and_charging": "7000mAh battery with 80W SUPERVOOC charging.",
        "chipset": "Qualcomm Snapdragon 6 Gen 4.",
    },
    "oppo|k13 turbo": {
        "display_type_description": "1.5K 120Hz flat display with 2800 × 1280 resolution.",
        "chipset": "MediaTek Dimensity 8450.",
        "battery_and_charging": "7000mAh battery with 80W SUPERVOOC charging.",
        "rear_camera_system": "50MP main camera with OIS.",
        "durability": "IP66, IP68 and IP69 water and dust resistance; cooling-fan module is independently sealed.",
    },
    "oppo|k13 turbo 5g": {
        "display_type_description": "1.5K 120Hz flat display with 2800 × 1280 resolution.",
        "chipset": "MediaTek Dimensity 8450.",
        "battery_and_charging": "7000mAh battery with 80W SUPERVOOC charging.",
        "rear_camera_system": "50MP main camera with OIS.",
        "durability": "IP66, IP68 and IP69 water and dust resistance; cooling-fan module is independently sealed.",
    },
    "oppo|k14x 5g": {
        "display_type_description": "17.15cm LCD display with 120Hz refresh rate and HD+ 1570 × 720 resolution.",
        "chipset": "MediaTek Dimensity 6300.",
        "rear_camera_system": "50MP main and 2MP monochrome cameras.",
        "front_camera_system": "5MP front camera.",
        "battery_and_charging": "6500mAh battery with 45W SUPERVOOC charging.",
        "operating_system": "ColorOS 15.0.",
        "durability": "IP64 water and dust resistance.",
    },
    "oppo|reno 11 pro": {
        "display_type_description": "6.7-inch 120Hz AMOLED display.",
        "rear_camera_system": "50MP main, 32MP telephoto portrait and 8MP ultra-wide cameras.",
        "front_camera_system": "32MP front camera.",
        "battery_and_charging": "4600mAh battery with 80W SUPERVOOC charging.",
        "chipset": "MediaTek Dimensity 8200.",
    },
    "oppo|reno 12 pro": {
        "display_type_description": "6.7-inch FHD+ AMOLED quad-curved display with 120Hz dynamic refresh rate.",
        "rear_camera_system": "50MP OIS main, 50MP telephoto and 8MP ultra-wide cameras.",
        "front_camera_system": "50MP autofocus front camera.",
        "battery_and_charging": "5000mAh battery with 80W SUPERVOOC charging.",
        "durability": "IP65 rating with Corning Gorilla Glass Victus 2.",
    },
    "oppo|reno12": {
        "display_type_description": "6.7-inch FHD+ AMOLED 3D-curved display with 120Hz dynamic refresh rate.",
        "rear_camera_system": "50MP OIS main, 8MP ultra-wide and 2MP macro cameras.",
        "front_camera_system": "32MP front camera.",
        "battery_and_charging": "5000mAh battery with 80W SUPERVOOC charging.",
        "durability": "IP65 rating with Corning Gorilla Glass 7i.",
    },
    "oppo|reno14": {
        "display_type_description": "16.74cm flexible AMOLED display with up to 120Hz refresh rate and 1256 × 2760 resolution.",
        "rear_camera_system": "50MP OIS main, 8MP ultra-wide and 50MP OIS 3.5x telephoto cameras.",
        "front_camera_system": "50MP autofocus front camera.",
        "battery_and_charging": "6000mAh battery with 80W SUPERVOOC charging.",
        "chipset": "MediaTek Dimensity 8350.",
        "operating_system": "ColorOS 15.0.",
    },
    "oppo|reno16 5g": {
        "rear_camera_system": "50MP OIS main, 50MP ultra-wide and 50MP OIS telephoto cameras.",
        "front_camera_system": "50MP front camera.",
        "battery_and_charging": "6700mAh battery with 80W SUPERVOOC charging.",
        "chipset": "Qualcomm Snapdragon 7 Gen 4.",
    },
    "oppo|reno16c 5g": {
        "display_type_description": "Reno16c 5G display and camera details remain limited to the cited official model page; unverified fields stay pending.",
        "operating_system": "ColorOS 16.",
    },
    "poco|f6 5g": {
        "display_type_description": "6.67-inch 1.5K Flow AMOLED display with up to 120Hz refresh rate and 2712 × 1220 resolution.",
        "chipset": "Qualcomm Snapdragon 8s Gen 3.",
        "rear_camera_system": "50MP Sony IMX882 OIS main and 8MP ultra-wide cameras.",
        "front_camera_system": "20MP front camera.",
        "battery_and_charging": "5000mAh battery with 90W wired charging.",
        "operating_system": "Xiaomi HyperOS.",
    },
}


def _apply_model_supplements(model_cards: list[dict[str, Any]]) -> None:
    """Add only documented model-level supplements for the active review batch."""
    for card in model_cards:
        identity = f"{_norm(card.get('brand'))}|{_norm(card.get('model'))}"
        base = re.sub(r"\s+(?:256|512)gb$", "", identity)
        supplements = APPLE_MODEL_SUPPLEMENTS.get(base)
        if not supplements:
            continue
        approved_hosts = {
            "support.apple.com", "www.apple.com", "store.google.com",
            "support.google.com", "in.nothing.tech", "infinixmobiles.in",
            "www.iqoo.com", "shop.iqoo.com", "www.lavamobiles.com",
            "checkout.nothing.tech",
            "en-in.support.motorola.com", "en-us.support.motorola.com",
            "www.oneplus.in",
            "www.oppo.com",
            "www.mi.com", "mi.com",
        }
        source = next(
            (
                url for url in card.get("source_urls") or []
                if (urlparse(url).hostname or "").casefold() in approved_hosts
            ),
            None,
        )
        if not source:
            continue
        for key, value in supplements.items():
            if key not in card.get("specifications", {}):
                card["specifications"][key] = {
                    "label": TECHNICAL_FIELD_LABELS[key],
                    "value": value,
                    "source_url": source,
                    "applicability": "MODEL_SHARED",
                    "checked_date": "2026-11-12",
                }
        card["missing_specifications"] = [key for key in TECHNICAL_FIELD_LABELS if key not in card["specifications"]]
        card["available_specification_fields"] = [TECHNICAL_FIELD_LABELS[key] for key in card["specifications"]]
        card["source_urls"] = list(dict.fromkeys([*card.get("source_urls", []), source]))


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
            # Existing frozen facts retain precedence, except for individually
            # reviewed source corrections on models with no frozen variants.
            correction = APPROVED_SPEC_CORRECTIONS.get((entry["model_key"], key))
            if item.get("evidence_status") == "MANUFACTURER_CORRECTED":
                if (correction is None or item.get("value") != correction[0]
                        or item.get("source_url") != correction[1]
                        or card.get("frozen_variant_ids")):
                    raise ValueError("unapproved corrected manufacturer fact or frozen-variant overwrite")
                card["specifications"][key] = item
            elif key not in card["specifications"]:
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
        # Keep each model's latest documented fact-check date, not an unrelated
        # site-build or scheduled link-probe timestamp. Six models have evidence
        # reviewed after the workbook's 2026-11-03 baseline.
        field_dates = [
            str(spec.get("checked_at") or "")[:10]
            for spec in entry.get("specifications", {}).values()
            if isinstance(spec, dict) and str(spec.get("checked_at") or "")[:10] >= payload["research_as_of"]
        ]
        card["research_checked_at"] = max([payload["research_as_of"], *field_dates])

def _apply_independent_tests(root, model_cards):
    path = root / "data" / "mobile_independent_test_evidence.json"
    if not path.exists():
        return
    evidence = json.loads(path.read_text(encoding="utf-8"))
    by_key = {item["model_key"]: item for item in evidence["models"]}
    if len(by_key) != len(evidence["models"]):
        raise ValueError("duplicate independent test model")
    for card in model_cards:
        item = by_key.get(card["model_key"])
        if not item:
            continue
        for metric in item["metrics"]:
            if metric.get("ranking_eligible") is not False or metric.get("scope") not in {"SOURCE_TEST_UNIT_ONLY", "MODEL_CONTEXT_ONLY"}:
                raise ValueError("independent research tests cannot enter ranking")
            if urlparse(metric["source_url"]).hostname not in {"www.notebookcheck.net", "www.phonearena.com"}:
                raise ValueError("unapproved independent test source")
        card["independent_tests"] = item["metrics"]
        card["independent_test_limitation"] = item["limitation"]


def build_public_catalogue(root: Path) -> dict[str, Any]:
    priority_payload = _read_json(root / "data/mobile_universe_priority_126.json")
    universe_payload = _read_json(root / "data/mobile_universe_2023_2026.json")
    preview_payload = _read_json(root / "data/mobile_research_preview.json")

    priority = priority_payload.get("products") or []
    models = universe_payload.get("models") or []
    preview = preview_payload.get("products") or []
    photos = _load_model_photos(root, models)
    india_variants = _read_json(root / "data/mobile_india_variant_sources.json")
    for key, variants in india_variants.items():
        pairs = {(row["ram_gb"], row["storage_gb"]) for row in variants}
        if key not in photos or len(pairs) != len(variants) or not variants:
            raise ValueError(f"invalid India variant photo or identity mapping: {key}")
        for ram, storage in pairs:
            if type(ram) is not int or type(storage) is not int or min(ram, storage) <= 0:
                raise ValueError(f"invalid physical memory configuration: {key}")
        for row in variants:
            if not row["source_url"].startswith(("https://www.oneplus.in/", "https://www.samsung.com/in/", "https://news.samsung.com/in/")):
                raise ValueError(f"invalid manufacturer India variant source: {key}")
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
            image = photos.get(model["model_key"])
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
                "image_url": image["url"] if image else None,
                "image_source_url": image["source"] if image else None,
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
        photo = photos.get(card["model_key"])
        if photo:
            card.update(image_status="VERIFIED_MATCH", photo=photo)
        if card["model_key"] in india_variants:
            card["verified_india_variants"] = india_variants[card["model_key"]]
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
    verified_retailer_links = _load_verified_mobile_retailer_links(root)
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
        if verified_retailer_links.get(identity):
            card["verified_retailer_links"] = verified_retailer_links[identity]

    _apply_workbook_research(root, model_cards)
    _apply_model_supplements(model_cards)
    _apply_independent_tests(root, model_cards)

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
