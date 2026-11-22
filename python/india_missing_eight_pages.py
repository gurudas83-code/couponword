#!/usr/bin/env python3
"""Eight source-reviewed market-demand phones beside the frozen 232-model registry.

Q2 rows are Counterpoint's estimated model-level sales shares; Q3 rows
are Omdia manufacturer shipment drivers, never a ranked Q3 sales chart.
The output is research only. No API candidate is promoted to price, offer,
verified SKU, product photograph, or the quality ranking automatically.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import quote, urlsplit
from xml.etree import ElementTree as ET

from python.category_research_pages import SITE, doc, esc, schema
from python.new_mobile_media import url as research_art_url, publish_art

ROOT = Path(__file__).resolve().parents[1]
SOURCE_Q2 = ROOT / "data" / "india_q2_2026_reported_top5_sales_models.json"
SOURCE_Q3 = ROOT / "data" / "india_q3_2026_sales_priority_models.json"
SOURCE_CORE = ROOT / "data" / "mobile_research_catalogue.json"
HUB = "/phones/india-sales-coverage-2026/"
MODE = "EIGHT_SOURCE_REVIEWED_MARKET_ADDITIONS_NO_LIVE_OFFERS"
Q2_KEYS = ("oppo|a6x 5g", "vivo|y31 5g")
Q3_KEYS = (
    "samsung|galaxy a07 5g", "samsung|galaxy a17 5g",
    "vivo|y11 5g", "vivo|y21 5g",
    "redmi|redmi 15a 5g", "redmi|redmi a7",
)
HOSTS = {"oppo": "oppo.com", "vivo": "vivo.com", "samsung": "samsung.com", "redmi": "mi.com"}
FIELD_KEYS = {
    "soc": "chipset", "processor": "chipset",
    "display": "display_type_description",
    "refresh rate": "display_refresh_description",
    "rear camera": "rear_camera_system",
    "rear cameras": "rear_camera_system",
    "rear main camera": "rear_camera_system",
    "front camera": "front_camera_system",
    "battery": "battery_capacity_description",
    "charging": "charging_description",
    "mobile network": "network_support",
    "india manufacturer-listed configurations": "india_variant_description",
    "maker ram/storage examples": "india_variant_description",
    "maker-listed example ram/storage": "india_variant_description",
    "ram/storage variants": "india_variant_description",
    "ram/storage variant": "india_variant_description",
}


def _source_ok(url: str, brand: str) -> bool:
    parts = urlsplit(url)
    host = HOSTS[brand.lower()]
    return parts.scheme == "https" and (parts.hostname == host or
             (parts.hostname or "").endswith("." + host)) and not parts.username and not parts.password


def _route(key: str) -> str:
    return HUB + re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-") + "/"


def _retailer_links(brand: str, model: str) -> list[dict]:
    search = quote(brand + " " + model, safe="")
    # Research searches only: neither a verified India SKU nor a current offer.
    return [
        {"retailer": "amazon", "url": "https://www.amazon.in/s?k=" + search + "&tag=guru07cc-21"},
        {"retailer": "flipkart", "url": "https://www.flipkart.com/search?q=" + search},
        {"retailer": "croma", "url": "https://www.croma.com/search/?text=" + search},
    ]


def import_eight() -> dict:
    q2 = json.loads(SOURCE_Q2.read_text(encoding="utf-8"))
    q3 = json.loads(SOURCE_Q3.read_text(encoding="utf-8"))
    core = json.loads(SOURCE_CORE.read_text(encoding="utf-8"))
    primary = core.get("model_cards") or []
    if len(primary) != 232:
        raise ValueError("Core catalogue no longer has its approved 232 models")
    existing_keys = {row["model_key"] for row in primary}
    q2_rows = {row["repository_model_key"]: row for row in q2["models"]
               if row["primary_catalogue_snapshot_status"] == "MISSING"}
    q3_rows = {row["repository_model_key"]: row for row in q3["models"]
               if row["repository_snapshot_status"] == "NEW_SOURCE_REVIEWED_INTAKE_ONLY"}
    if set(q2_rows) != set(Q2_KEYS) or set(q3_rows) != set(Q3_KEYS):
        raise ValueError("The eight market intake keys changed; manual review required")
    rows, cards = [], []
    for key in Q2_KEYS + Q3_KEYS:
        market = "Q2 ranked model sales" if key in q2_rows else "Q3 shipments, not sales rank"
        item = (q2_rows.get(key) or q3_rows.get(key))
        if key in existing_keys:
            raise ValueError("Duplicate market addition in the 232 canonical catalogue: " + key)
        brand, model = item["brand"], item["model"]
        if key != brand.lower() + "|" + model.lower():
            raise ValueError("Market model identity mismatch: " + key)
        official = item["official_spec_url"]
        if not _source_ok(official, brand):
            raise ValueError("Manufacturer host mismatch: " + key)
        report = item["source_report_url"]
        if urlsplit(report).scheme != "https":
            raise ValueError("Missing market report source: " + key)
        source_fields = item.get("verified_manufacturer_facts") or item.get("specs")
        specs = {}
        for field in source_fields:
            label = str(field.get("field") or field.get("label") or "").strip()
            value = str(field.get("value") or "").strip()
            skey = FIELD_KEYS.get(label.lower())
            if not skey or not value or skey in specs or field.get("source_url") != official:
                raise ValueError("Missing, duplicate or unreviewed manufacturer field for " + key + ": " + label)
            specs[skey] = {"value": value, "source_url": official}
        if len(specs) < 5:
            raise ValueError("Insufficient manufacturer facts: " + key)
        if item.get("price_inr") is not None or item.get("stock") is not None or item.get("performance_score") is not None:
            raise ValueError("Cannot admit market prices, stock or quality scores")
        record_key = "sales-intake|" + key
        rows.append({
            "record_key": record_key, "status": "RESEARCH_ONLY",
            "ram_gb": None, "storage_gb": None,
            "variant_text": "Manufacturer model family; exact retail configuration unverified",
            "verified_fields": [], "source_urls": [official],
        })
        cards.append({
            "model_key": key, "brand": brand, "model": model,
            "status": "RESEARCH_ONLY",
            "status_reason": "Manufacturer-linked sales/shipments research only. Exact India retail variant, current offers, stock, photographic rights and independent performance are not established.",
            "discovery_record_keys": [record_key], "frozen_variant_ids": [],
            "verified_india_variants": [],
            "specifications": specs, "missing_specifications": [],
            "available_specification_fields": list(specs),
            "source_urls": [official, report], "image_status": "PLACEHOLDER", "photo": None,
            "research_art_url": research_art_url(key), "detail_url": _route(key), "photo_rights_status": "NOT_CLEARED",
            "verified_retailer_links": [], "retailer_search_links": _retailer_links(brand, model),
            "market_intake": True, "market_reference": market, "market_report_url": report,
        })
    if len(cards) != 8 or len({row["model_key"] for row in cards}) != 8:
        raise ValueError("Eight unique market research additions required")
    return {
        "schema_version": 1, "mode": MODE, "core_model_count_unchanged": 232,
        "market_report_q2": q2["source_url"], "market_report_q3": q3["sales_evidence_url"],
        "model_cards": cards, "records": rows,
        "disclosure": "Historical market-research intake, not live inventory or quality ranking. No API price, exact India SKU or product photo has been admitted.",
    }


def _research_page(card: dict) -> str:
    name = card["brand"] + " " + card["model"]
    route = _route(card["model_key"])
    variant_fields = {
        "india_variant_description", "maker_ram_storage_examples",
        "india_variant_description", "ram_storage_variant", "ram_storage_variants",
    }
    variant = next((field["value"] for key, field in card["specifications"].items()
                    if key in variant_fields), "Manufacturer-listed variant; exact retailer SKU unverified")
    image_verified = card.get("image_status") == "VERIFIED_MATCH" and bool(card.get("photo"))
    image_text = "Verified model image" if image_verified else "Not verified — current illustration is not a model photo"
    image_html = ('<img src="' + esc(card["photo"]) + '" width="540" height="430" loading="lazy" alt="' +
                  esc(name) + ' verified product image">') if image_verified else (
                  '<img src="' + esc(card["research_art_url"]) + '" width="540" height="430" loading="lazy" alt="Generic smartphone illustration; not a photo of this model">')
    retailer = next((row for row in card.get("retailer_search_links", []) if row.get("retailer") == "amazon"), None)
    affiliate_html = ('<a class="cr-button" href="' + esc(retailer["url"]) +
                      '" rel="sponsored nofollow noopener" target="_blank">Search Amazon for this model</a>'
                      if retailer else 'Affiliate link not configured')
    commerce = f'''<section class="cr-commerce" aria-labelledby="commerce-title">
<h2 id="commerce-title">Customer buying details</h2>
<dl class="cr-commerce-grid">
<div><dt>Exact variant</dt><dd>{esc(variant)}</dd></div>
<div><dt>Verified image</dt><dd>{esc(image_text)}</dd></div>
<div><dt>Current price</dt><dd><strong>Not verified</strong><br><small>Live authorized retailer feed required.</small></dd></div>
<div><dt>Stock status</dt><dd><strong>Not verified</strong><br><small>Stock changes by retailer and pincode.</small></dd></div>
<div><dt>Affiliate buying link</dt><dd>{affiliate_html}<br><small>Search link only; exact offer is not certified.</small></dd></div>
<div><dt>Last checked</dt><dd><strong>Retailer price/stock: not checked</strong><br><small>Manufacturer research source reviewed; this is not a live offer timestamp.</small></dd></div>
</dl>
<p class="cr-note"><strong>Before buying:</strong> confirm RAM/storage, seller, warranty, payable price and delivery at the retailer.</p>
</section>'''
    facts = "".join(
        '<div class="cr-fact"><dt>' + esc(key.replace("_", " ").title()) +
        '</dt><dd>' + esc(field["value"]) +
        ' · <a href="' + esc(field["source_url"]) + '" rel="noopener noreferrer" target="_blank">Maker source</a></dd></div>'
        for key, field in card["specifications"].items()
    )
    searches = "".join('<li><a rel="noopener noreferrer nofollow' +
       (' sponsored' if store["retailer"] == "amazon" else "") +
       '" target="_blank" href="' + esc(store["url"]) + '">Search ' +
       esc(store["retailer"].title()) + ' for this model</a> (search only; not a verified listing)</li>'
       for store in card["retailer_search_links"])
    body = f'''<p class="cr-crumb"><a href="/">Home</a> /
<a href="{HUB}">Market additions</a> / {esc(name)}</p>
<article class="cr-detail"><h1>{esc(name)}</h1>
<p class="cr-lead">Source-reviewed research model. {esc(card["market_reference"])}.
This is not a certified exact retailer SKU, a live stock check or an independently tested recommendation.</p>
{image_html}
<p><small>{esc(image_text)}. Exact model imagery requires reuse clearance unless an approved source is recorded.</small></p>
<h2>Manufacturer-linked specifications</h2><dl class="cr-detail-facts">{facts}</dl>
{commerce}
<h2>Check this model at retailers</h2><p>These three links open model-specific store searches.
Confirm exact RAM/storage, model number, warranty, seller, payable price and availability independently before buying.</p>
<ul>{searches}</ul>
<p>Market evidence: <a href="{esc(card["market_report_url"])}" rel="noopener noreferrer" target="_blank">Original report</a>.
No performance ranking, price or stock has been inferred from market sales or shipments.</p></article>'''
    document = doc(name + " — India research and retailer searches",
       "Manufacturer-linked information and dated India market research for " + name + "; retailer search only.",
       route, body, schema(name, route, "phones"))
    # Noindex until model/variant publication evidence is strengthened.
    return document.replace('name="robots" content="index,follow"',
                            'name="robots" content="noindex,follow"', 1)


def _hub(cards: list[dict]) -> str:
    items = []
    for item in cards:
        name = item["brand"] + " " + item["model"]
        main_specs = list(item["specifications"].items())[:3]
        facts = "".join('<div class="cr-fact"><dt>' + esc(k.replace("_", " ").title()) +
             '</dt><dd>' + esc(v["value"]) + '</dd></div>' for k, v in main_specs)
        items.append('<article class="cr-card"><h3><a href="' + _route(item["model_key"]) + '">' +
          esc(name) + '</a></h3><p class="cr-muted">' + esc(item["market_reference"]) +
          ' · manufacturer-linked research, not live availability</p><dl class="cr-facts">' +
          facts + '</dl><div class="cr-card-foot"><a href="' + _route(item["model_key"]) +
          '">Specifications and retailer searches</a></div></article>')
    body = f'''<p class="cr-crumb"><a href="/">Home</a> / <a href="/phones/">Phones</a>
/ Sales-report coverage</p><section class="cr-hero">
<p class="cr-eyebrow">India · market coverage · 2026 Q2/Q3</p>
<h1>8 missing phones now searchable in Coupon World research</h1>
<p>Two models appeared in the <a href="https://counterpointresearch.com/en/insights/top-5-smartphone-model-share-8-countries">Q2 Counterpoint sales Top-5</a>.
Six additional models were identified from <a href="https://omdia.tech.informa.com/pr/2026/oct/indias-smartphone-shipments-fell-26percent-to-a-decade-low-third-quarter-level-despite-festive-season">Q3 Omdia shipment signals</a>.
Q3 is not an ordered Top-10 model sales ranking.</p>
<p><strong>Coverage:</strong> 232 original research cards plus 8 distinct source-reviewed market additions.
All eight remain research-only pending exact retailer SKU and photo-use clearance.
No manufacturer source implies a live Amazon, Flipkart or Croma price.</p>
<p><a href="/#mobileResearchSearch">Search and compare these models with the existing phones</a></p></section>
<section><h2>The 8 market additions</h2><div class="cr-grid">{''.join(items)}</div></section>'''
    return doc("8 India sales-report models added to Coupon World research",
      "Eight source-backed Indian smartphone sales and shipment research additions, separate from the original 232-model catalogue.",
      HUB, body, schema("India smartphone market coverage", HUB, "phones"))


def publish_eight(destination: Path) -> dict:
    payload = import_eight()
    if publish_art(destination, payload["model_cards"]) != 8:
        raise ValueError("Missing sales-research illustrations")
    target = destination / "data" / "india_sales_eight_research.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    root = destination / HUB.lstrip("/")
    root.mkdir(parents=True, exist_ok=True)
    (root / "index.html").write_text(_hub(payload["model_cards"]), encoding="utf-8")
    for card in payload["model_cards"]:
        path = destination / _route(card["model_key"]).lstrip("/")
        path.mkdir(parents=True, exist_ok=True)
        (path / "index.html").write_text(_research_page(card), encoding="utf-8")
    ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", ns)
    sitemap = destination / "sitemap.xml"
    tree = ET.parse(sitemap)
    outer = tree.getroot()
    url = SITE + HUB
    if url in {loc.text for loc in outer.findall(f"{{{ns}}}url/{{{ns}}}loc")}:
        raise ValueError("Market additions duplicated in sitemap")
    child = ET.SubElement(outer, f"{{{ns}}}url")
    ET.SubElement(child, f"{{{ns}}}loc").text = url
    tree.write(sitemap, encoding="utf-8", xml_declaration=True)
    print("8 market research models added; frozen original 232, scoring and offers unchanged")
    return payload

