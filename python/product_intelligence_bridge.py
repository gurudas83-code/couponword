#!/usr/bin/env python3
"""
Coupon World AI OS
Product Intelligence Bridge v1.1

Normalizes mixed verified-product formats into a common profile.

Source priority:
1. Published product knowledge
2. Semantic canonical facts
3. Official specifications
4. Conservative text fallback
5. UNKNOWN (never invent)
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_FILE = ROOT / "data" / "product_knowledge.json"
OFFICIAL_SPECS_FILE = ROOT / "data" / "official_specs.json"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def products_by_id(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    products = payload.get("products", [])
    if not isinstance(products, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for item in products:
        if not isinstance(item, dict):
            continue
        pid = str(item.get("product_id") or "").strip()
        if pid:
            out[pid] = item
    return out


def flatten(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return " ".join(flatten(x) for x in value)
    if isinstance(value, dict):
        return " ".join(f"{k} {flatten(v)}" for k, v in value.items())
    return str(value)


def semantic_facts(record: dict[str, Any]) -> list[dict[str, Any]]:
    semantic = record.get("semantic_consolidation")
    if not isinstance(semantic, dict):
        return []

    # v1.3 shape:
    # semantic_consolidation -> result -> facts
    result = semantic.get("result")
    if isinstance(result, dict):
        facts = result.get("facts")
        if isinstance(facts, list):
            return [x for x in facts if isinstance(x, dict)]

    # Older fallback shapes
    facts = semantic.get("facts")
    if isinstance(facts, list):
        return [x for x in facts if isinstance(x, dict)]

    return []


def facts_by_key(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for fact in semantic_facts(record):
        key = str(fact.get("canonical_key") or "").strip().lower()
        if key:
            out[key] = fact
    return out


def fact_value(fact: dict[str, Any] | None) -> Any:
    if not isinstance(fact, dict):
        return None

    summary = fact.get("normalized_summary")
    if summary not in (None, ""):
        return summary

    structured = fact.get("structured_value")
    if structured not in (None, "", {}, []):
        return structured

    value = fact.get("value")
    if value not in (None, ""):
        unit = str(fact.get("unit") or "").strip()
        return f"{value}{(' ' + unit) if unit else ''}"

    values = fact.get("values")
    if values:
        return values

    return None


def first_fact(facts: dict[str, dict[str, Any]], *keys: str) -> Any:
    for key in keys:
        fact = facts.get(key.lower())
        value = fact_value(fact)
        if value not in (None, "", {}, []):
            return value
    return None


def spec_value(value: Any) -> Any:
    if isinstance(value, dict):
        if value.get("value") not in (None, ""):
            return value.get("value")
        if value.get("normalized_value") not in (None, ""):
            return value.get("normalized_value")
    return value


def find_spec(specs: dict[str, Any], *needles: str) -> Any:
    for key, value in specs.items():
        key_text = str(key).lower().replace("_", " ")
        if any(needle.lower() in key_text for needle in needles):
            candidate = spec_value(value)
            if candidate not in (None, "", {}, []):
                return candidate
    return None


def pick(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def regex_first(text: str, pattern: str, flags: int = re.I) -> str | None:
    match = re.search(pattern, text, flags)
    return match.group(1) if match else None


def build_profile(product_id: str) -> dict[str, Any] | None:
    pid = str(product_id).strip()

    knowledge_index = products_by_id(load_json(KNOWLEDGE_FILE))
    official_index = products_by_id(load_json(OFFICIAL_SPECS_FILE))

    published = knowledge_index.get(pid, {})
    official = official_index.get(pid, {})

    if not published and not official:
        return None

    facts = facts_by_key(official)
    specs = official.get("specifications", {})
    if not isinstance(specs, dict):
        specs = {}

    text = " ".join(
        [
            flatten(published),
            flatten(official),
        ]
    ).lower()

    title = pick(
        published.get("title"),
        official.get("title"),
        official.get("search_name"),
    )
    brand = pick(published.get("brand"), official.get("brand"))
    category = pick(published.get("category"), official.get("category"))

    attrs: dict[str, Any] = {}

    # Processor
    attrs["processor"] = pick(
        first_fact(facts, "processor", "chipset", "soc"),
        find_spec(specs, "processor", "chipset", "soc"),
    )

    # RAM capacity only; do not confuse LPDDR type with RAM amount.
    ram_from_title = regex_first(text, r"\b(\d{1,3}\s*gb)\s*ram\b")
    attrs["ram"] = pick(
        first_fact(facts, "ram_capacity", "memory_capacity"),
        find_spec(specs, "ram capacity", "memory capacity"),
        ram_from_title,
    )

    # Memory technology separately.
    attrs["memory_type"] = pick(
        first_fact(facts, "memory_type"),
        find_spec(specs, "memory type"),
        regex_first(text, r"\b(lpddr\d+x?)\b"),
    )

    # Storage capacity and technology.
    storage_capacity = regex_first(
        text,
        r"\b(\d{2,4}\s*gb)\s*(?:storage|internal storage)\b",
    )
    attrs["storage"] = pick(
        first_fact(facts, "storage_capacity", "internal_storage"),
        find_spec(specs, "storage capacity", "internal storage"),
        storage_capacity,
    )
    attrs["storage_type"] = pick(
        first_fact(facts, "storage_type"),
        find_spec(specs, "storage type", "ufs", "ssd"),
        regex_first(text, r"\b(ufs\s*\d(?:\.\d)?)\b"),
    )

    # Display
    attrs["display"] = pick(
        first_fact(facts, "display", "display_size", "screen_size"),
        find_spec(specs, "display", "screen"),
        regex_first(
            text,
            r"\b(\d(?:\.\d{1,2})?\s*(?:-?inch|inches?).{0,45}?(?:amoled|oled|lcd)?)",
        ),
    )

    # Battery capacity.
    semantic_battery = first_fact(facts, "battery_capacity")
    battery_regex = regex_first(text, r"\b(\d{4,5}\s*mah)\b")
    attrs["battery"] = pick(
        semantic_battery,
        find_spec(specs, "battery capacity"),
        battery_regex,
    )

    # Playback/endurance.
    attrs["battery_playback"] = pick(
        first_fact(facts, "battery_playback_duration", "playback_duration"),
        find_spec(specs, "playback", "battery life"),
        regex_first(
            text,
            r"\b((?:up to\s*)?\d{1,3}\s*(?:hours|hrs)(?:.{0,80}?(?:playback|battery))?)",
        ),
    )

    # Charging
    attrs["charging"] = pick(
        first_fact(facts, "charging_duration", "charging_interface"),
        find_spec(specs, "wired charging", "charging"),
        regex_first(text, r"\b(\d{1,3}\s*w\s*(?:fast\s*)?(?:wired\s*)?charging)\b"),
        "Type-C" if "type-c" in text or "usb-c" in text else None,
    )

    # Bluetooth
    attrs["bluetooth"] = pick(
        first_fact(facts, "bluetooth_version"),
        find_spec(specs, "bluetooth"),
        regex_first(text, r"\b(bluetooth(?:\s+version)?\s*5\.\d)\b"),
    )

    # IP rating
    attrs["ip_rating"] = pick(
        first_fact(facts, "ingress_protection_rating", "ip_rating"),
        find_spec(specs, "ingress protection", "ip rating"),
        regex_first(text, r"\b(ip\d{2})\b"),
    )

    # ANC
    attrs["anc"] = pick(
        first_fact(facts, "noise_cancellation_depth", "anc"),
        find_spec(specs, "noise cancellation", "anc"),
        regex_first(
            text,
            r"\b((?:anc|noise cancellation).{0,40}?\d{1,2}\s*db|\d{1,2}\s*db.{0,40}?(?:anc|noise cancellation))\b",
        ),
    )

    # Camera: leave unknown unless actual evidence exists.
    attrs["camera"] = pick(
        first_fact(facts, "camera", "main_camera", "rear_camera"),
        find_spec(specs, "main camera", "rear camera", "camera"),
    )

    # Software support
    android_updates = find_spec(specs, "android updates")
    security_updates = find_spec(specs, "security updates")
    semantic_support = first_fact(
        facts,
        "software_support",
        "android_updates",
        "security_updates",
    )
    if semantic_support:
        attrs["software_support"] = semantic_support
    elif android_updates or security_updates:
        attrs["software_support"] = "; ".join(
            str(x) for x in (android_updates, security_updates) if x
        )
    else:
        attrs["software_support"] = None

    # Connectivity
    wifi = find_spec(specs, "wifi", "wi-fi")
    bluetooth = attrs.get("bluetooth")
    parts = [str(x) for x in (wifi, bluetooth) if x]
    attrs["connectivity"] = "; ".join(parts) if parts else None

    sources: list[str] = []
    if published:
        sources.append("published_knowledge")
    if facts:
        sources.append("semantic_canonical_facts")
    if official:
        sources.append("official_specs")

    known = sum(
        1 for value in attrs.values()
        if value not in (None, "", [], {})
    )
    total = len(attrs)

    return {
        "product_id": pid,
        "title": title,
        "brand": brand,
        "category": category,
        "attributes": attrs,
        "features": published.get("features", [])
        if isinstance(published.get("features"), list)
        else [],
        "best_for": published.get("best_for", [])
        if isinstance(published.get("best_for"), list)
        else [],
        "limitations": published.get("limitations", [])
        if isinstance(published.get("limitations"), list)
        else [],
        "confidence": published.get("confidence", {}),
        "official_product_url": pick(
            published.get("official_product_url"),
            official.get("official_url"),
        ),
        "evidence_sources": sources,
        "attribute_coverage_percent": round((known / total) * 100) if total else 0,
    }


def main() -> int:
    print("=" * 72)
    print("COUPON WORLD PRODUCT INTELLIGENCE BRIDGE v1.1")
    print("=" * 72)

    for pid in ("11", "74"):
        profile = build_profile(pid)
        print()
        print(f"PRODUCT {pid}")

        if profile is None:
            print("STATUS: NOT FOUND")
            continue

        print("TITLE:", profile.get("title"))
        print("SOURCES:", ", ".join(profile.get("evidence_sources", [])) or "none")
        print(
            "ATTRIBUTE COVERAGE:",
            f"{profile.get('attribute_coverage_percent', 0)}%",
        )

        for key, value in profile.get("attributes", {}).items():
            print(
                f"  {key:18}: "
                f"{value if value not in (None, '', [], {}) else 'UNKNOWN'}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
