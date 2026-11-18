"""Safely add eight recently source-linked Indian phones to research discovery.

This is model-family discovery, not API-confirmed retail stock, exact SKUs,
current prices, scores or image licences. The original 232 cards remain frozen.
"""
from __future__ import annotations

import json
from html import escape
from pathlib import Path
from xml.etree import ElementTree as ET

from python.category_research_pages import SITE, doc, schema
from python.new_mobile_media import url as research_art_url, publish_art, RIGHTS_NOTE
from urllib.parse import quote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "india_recent_phone_sources.json"
CORE = ROOT / "data" / "mobile_research_catalogue.json"
MODE = "RECENT_INDIA_MANUFACTURER_MODELS_RESEARCH_ONLY"
PUBLIC_DATA_NAME = "india_recent_manufacturer_research.json"
HUB = "/phones/new-india-mobiles/"


def detail_route(model_key: str) -> str:
    from python.new_mobile_media import slug
    return HUB + slug(model_key) + "/"


def _name(card: dict) -> str:
    return next(name for name, meta in APPROVED.items()
                if card["model_key"] == meta[0] + "|" + meta[1])
REVIEWED_SPECS = {
    "chipset", "display_type_description", "display_refresh_description",
    "battery_capacity_description", "rear_camera_system", "india_variant_description",
}
APPROVED = {
    "Motorola Signature 27": ("motorola", "signature 27", "motorola.in"),
    "Karbonn Rebel": ("karbonn", "rebel", "karbonnr-bel.com"),
    "Karbonn Rebel Pro": ("karbonn", "rebel pro", "karbonnr-bel.com"),
    "OPPO Find X10": ("oppo", "find x10", "oppo.com"),
    "OPPO Find X10 Pro Max": ("oppo", "find x10 pro max", "oppo.com"),
    "OPPO F35 5G": ("oppo", "f35 5g", "oppo.com"),
    "OPPO F35 Pro 5G": ("oppo", "f35 pro 5g", "oppo.com"),
    "vivo V80": ("vivo", "v80", "vivo.com"),
    "vivo X Fold6": ("vivo", "x fold6", "vivo.com"),
    "vivo S2 FE": ("vivo", "s2 fe", "vivo.com"),
    "Samsung Galaxy F70 5G": ("samsung", "galaxy f70 5g", "samsung.com"),
    "REDMI 17C 5G": ("redmi", "redmi 17c 5g", "mi.com"),
    "realme P4s Lite": ("realme", "p4s lite", "realme.com"),
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
            approved_store = ((host == "vivo.com" and _official(item["store"], "shop.vivo.com"))
                              or (host == "realme.com" and _official(item["store"], "buy.realme.com")))
            if not approved_store:
                raise ValueError("Unapproved official store: " + name)
        facts = item.get("reviewed_specs") or {}
        if not isinstance(facts, dict) or not set(facts).issubset(REVIEWED_SPECS):
            raise ValueError("Unreviewed specification field: " + name)
        if any(not isinstance(value, str) or not value.strip() for value in facts.values()):
            raise ValueError("Empty manufacturer specification: " + name)
        specs = {key: {"value": value, "source_url": item["source"], "checked_at": item.get("reviewed_on") or "2026-11-07"}
                 for key, value in facts.items()}
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
            "specifications": specs, "missing_specifications": [],
            "available_specification_fields": list(specs),
            "recent_source_intake": True,
            "research_checked_at": item.get("reviewed_on") or "2026-11-07",
            "api_probe_eligible": item.get("api_probe_eligible", True),
            "api_probe_note": item.get("api_probe_note"),
            "source_urls": [item["source"]] + ([item["store"]] if item.get("store") else []),
            "image_status": "PLACEHOLDER", "photo": None,
            "research_art_url": research_art_url(key), "detail_url": detail_route(key),
            "photo_rights_status": "NOT_CLEARED",
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
    if len(cards) != len(APPROVED) or len({c["model_key"] for c in cards}) != len(APPROVED):
        raise ValueError("Source-linked model identities changed")
    return {
        "schema_version": 2, "mode": MODE, "core_model_count_unchanged": 232,
        "research_addition_count": len(APPROVED), "reviewed_on": recent["checked_on"],
        "model_cards": cards, "records": records,
        "notice": "Manufacturer-source research only; no exact retailer SKU, price, stock, rating or image permission is certified.",
    }


def _hub(cards: list[dict]) -> str:
    """One source-linked indexable hub; no autogenerated thin model pages."""
    ordered = sorted(cards, key=lambda card: (
        0 if card.get("research_checked_at") == "2026-11-18" else 1,
        card["model_key"]
    ))
    items = []
    for card in ordered:
        display = _name(card)
        sources = card["source_urls"][0]
        facts = "".join(
            '<li>' + escape(key.replace("_", " ").title()) + ': ' +
            escape(str(field["value"])) + "</li>"
            for key, field in list(card["specifications"].items())[:4]
        )
        q = quote(display, safe="")
        items.append(
            '<article class="cr-card"><a href="' + detail_route(card["model_key"]) + '"><img src="' + card["research_art_url"] + '" width="540" height="430" loading="lazy" alt="Generic smartphone illustration; not a photo of ' + escape(display) + '"></a><h2><a href="' + detail_route(card["model_key"]) + '">' + escape(display) + '</a></h2>' +
            ('<p><strong>Specifications reviewed 18 November 2026</strong></p>' if card.get("research_checked_at") == "2026-11-18"
             else '<p>Official India manufacturer model identified; full field verification pending</p>') +
            ('<ul>' + facts + '</ul>' if facts else '') +
            '<p><a href="' + escape(sources, quote=True) +
            '" rel="noopener noreferrer" target="_blank">Manufacturer source</a></p>' +
            '<p><a href="/?q=' + q + '#mobileResearchSearch">Compare in Coupon World research</a></p>' +
            '<p>Price: unavailable — no current exact-SKU API evidence. Photo: original illustration, not model photography.</p></article>'
        )
    body = (
        '<p class="cr-crumb"><a href="/">Home</a> / <a href="/phones/">Phones</a> / New India research</p>'
        '<section class="cr-hero"><p class="cr-eyebrow">INDIA SMARTPHONE RESEARCH · 18 NOVEMBER 2026</p>'
        '<h1>13 recently added India smartphones — official manufacturer sources</h1>'
        '<p>These are additional model-family research records beyond the original 232 phones, '
        'not a sales ranking or verified shopping inventory. Three models newly reviewed '
        'on 18 November are Samsung Galaxy F70 5G, REDMI 17C 5G and realme P4s Lite.</p>'
        '<p>Manufacturer-stated specifications are linked to their evidence pages. '
        'Coverage varies by model; missing details must not be inferred. No independent '
        'hands-on test, checkout price, availability or manufacturer-image reuse right is implied.</p>'
        '<p><a href="/phones/india-sales-coverage-2026/">Also explore eight '
        'earlier sales-report research additions</a></p></section>'
        '<section><div class="cr-grid">' + "".join(items) + '</div></section>'
    )
    return doc(
        "New India Smartphones 2026 — Manufacturer Source Research | Coupon World",
        "Thirteen recent manufacturer-linked India smartphone models with source references, documented facts and research-only retailer checks.",
        HUB, body, schema("Recent India smartphone manufacturer research", HUB, "phones")
    )


def _detail_page(card: dict) -> str:
    """Model identity and documented facts; not thin indexable SEO or a priced offer."""
    name = _name(card)
    route = detail_route(card["model_key"])
    specs = "".join(
        '<div class="cr-fact"><dt>' + escape(key.replace("_", " ").title()) +
        '</dt><dd>' + escape(str(field["value"])) + ' · <a href="' +
        escape(field["source_url"], quote=True) +
        '" rel="noopener noreferrer" target="_blank">Maker source</a></dd></div>'
        for key, field in card["specifications"].items()
    )
    links = "".join(
        '<li><a href="' + escape(x["url"], quote=True) +
        '" target="_blank" rel="noopener noreferrer nofollow' +
        (' sponsored' if x["retailer"] == "amazon" else '') +
        '">Search ' + escape(x["retailer"].title()) + ' for this model</a></li>'
        for x in card["retailer_search_links"]
    )
    body = (
        '<p class="cr-crumb"><a href="/">Home</a> / <a href="' + HUB +
        '">New India mobiles</a> / ' + escape(name) + '</p>'
        '<article class="cr-detail"><h1>' + escape(name) + '</h1>'
        '<p>Manufacturer-linked smartphone research · exact India retail variants '
        'and availability not certified.</p>'
        '<img src="' + card["research_art_url"] + '" width="540" height="430" '
        'loading="eager" alt="Generic smartphone illustration; not a photo of ' +
        escape(name, quote=True) + '">'
        '<p><small>Original illustrated artwork. NOT the exact product photograph. '
        'Product imagery can be added only with model-verified commercial reuse rights.</small></p>'
        '<h2>Specifications</h2>' +
        ('<dl class="cr-detail-facts">' + specs + '</dl>' if specs else
         '<p>Manufacturer model source is recorded; technical fields are pending '
         'source-by-source verification. Do not assume missing specifications.</p>') +
        '<h2>Price and availability</h2>'
        '<p class="cr-muted"><strong>Current price unavailable.</strong> '
        'No exact-variant, fresh, publisher-authorized API price has passed verification. '
        'Retailer prices, stock, delivery location and warranty must be checked on their websites.</p>'
        '<h2>Check retailer listings</h2><ul>' + links + '</ul>'
        '<p><a href="' + escape(card["manufacturer_page"], quote=True) +
        '" rel="noopener noreferrer" target="_blank">Official manufacturer page '
        '(product photography and specifications)</a></p>'
        '<p>Search results are not verified SKU listings and do not constitute '
        'a price comparison. As an Amazon Associate we may earn from qualifying purchases.</p>'
        '</article>'
    )
    html = doc(name + " — manufacturer-source India specifications",
               "India manufacturer-source specifications and retailer searches for " +
               name + "; prices are unavailable until verified.",
               route, body, schema(name, route, "phones"))
    return html.replace('name="robots" content="index,follow"',
                        'name="robots" content="noindex,follow"', 1)


def publish_recent(destination: Path) -> dict:
    payload = build_recent()
    count = publish_art(destination, payload["model_cards"])
    if count != 13:
        raise ValueError("Missing model illustrations")
    for card in payload["model_cards"]:
        path = destination / detail_route(card["model_key"]).lstrip("/") / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_detail_page(card), encoding="utf-8")
    target = destination / "data" / PUBLIC_DATA_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    page = destination / HUB.lstrip("/") / "index.html"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(_hub(payload["model_cards"]), encoding="utf-8")
    ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", ns)
    sitemap = destination / "sitemap.xml"
    tree = ET.parse(sitemap)
    root = tree.getroot()
    if SITE + HUB in {loc.text for loc in root.findall(f"{{{ns}}}url/{{{ns}}}loc")}:
        raise ValueError("Recent manufacturer hub duplicated in sitemap")
    item = ET.SubElement(root, f"{{{ns}}}url")
    ET.SubElement(item, f"{{{ns}}}loc").text = SITE + HUB
    tree.write(sitemap, encoding="utf-8", xml_declaration=True)
    print(len(payload["model_cards"]), "recent manufacturer-sourced India phone models available in research")
    return payload