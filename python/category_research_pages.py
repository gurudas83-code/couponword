#!/usr/bin/env python3
"""Publish evidence-only accessories/TV research using the existing Pages build.

No prices, stock, affiliate CTAs, performance rankings or new recommendation
engine. The catalogue is curated from official manufacturer pages.
"""
from __future__ import annotations

import html
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "category_research_verified.json"
SITE = "https://coupon-world.in"
CATEGORIES = ("accessories", "tvs")
SOURCE_HOSTS = {
    "OnePlus": "oneplus.in",
    "Samsung": "samsung.com",
    "Apple": "apple.com",
    "Xiaomi": "mi.com",
    "LG": "lg.com",
    "Sony": "sony.co.in",
    "TCL": "tcl.com",
}

def esc(value: object) -> str:
    return html.escape(str(value), quote=True)

def load_checked_records() -> dict:
    raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    if raw.get("mode") != "CATEGORY_RESEARCH_ONLY":
        raise ValueError("Only research-only category data may be published")
    if set(raw.get("categories", {})) != set(CATEGORIES):
        raise ValueError("Both approved categories must be present")
    records = raw.get("records")
    if not isinstance(records, list) or len(records) < 8:
        raise ValueError("Curated accessories/TV records are incomplete")
    seen = set()
    counts = {category: 0 for category in CATEGORIES}
    for item in records:
        category = item.get("category")
        slug = item.get("slug", "")
        if category not in CATEGORIES or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            raise ValueError(f"Invalid research category or slug: {category}/{slug}")
        key = (category, slug)
        if key in seen:
            raise ValueError(f"Duplicate research route: {key}")
        seen.add(key)
        counts[category] += 1
        if item.get("review_status") != "MANUFACTURER_SOURCE_REVIEWED_MODEL":
            raise ValueError(f"Unreviewed product: {slug}")
        if not item.get("brand") or not item.get("model") or not item.get("product_type"):
            raise ValueError(f"Missing model identity: {slug}")
        source = str(item.get("source_url") or "")
        host = (urlsplit(source).hostname or "").lower()
        brand_host = SOURCE_HOSTS.get(item["brand"])
        if urlsplit(source).scheme != "https" or not brand_host or not (
            host == brand_host or host.endswith("." + brand_host)
        ):
            raise ValueError(f"Not a matching manufacturer HTTPS source: {slug}")
        checked = date.fromisoformat(item.get("reviewed_at", ""))
        if checked > date.today():
            raise ValueError(f"Future source review date: {slug}")
        fields = item.get("specifications")
        if not isinstance(fields, list) or len(fields) < 5:
            raise ValueError(f"Not enough documented fields: {slug}")
        labels = set()
        for field in fields:
            label = str(field.get("label") or "").strip()
            value = str(field.get("value") or "").strip()
            if not label or not value or label in labels or field.get("source_url") != source:
                raise ValueError(f"Unverified/duplicated field: {slug}/{label}")
            labels.add(label)
        if not item.get("decision_note") or not item.get("compatibility_caution") or len(item.get("unknowns") or []) < 2:
            raise ValueError(f"Missing limitations: {slug}")
        if any(item.get(k) not in (None, "", False) for k in (
            "price", "mrp", "stock", "availability", "rating",
            "performance_score", "purchase_cta_eligible", "affiliate_url"
        )):
            raise ValueError(f"Commerce/ranking data not permitted: {slug}")
    if any(counts[c] < 4 for c in CATEGORIES):
        raise ValueError(f"Both categories need at least four researched models: {counts}")
    return raw

def nav() -> str:
    return (
        '<header class="cr-header"><nav aria-label="Primary navigation">'
        '<a class="cr-logo" href="/">CW <strong>Coupon World</strong></a>'
        '<a href="/phones/">Phones</a>'
        '<a href="/accessories/">Mobile accessories</a>'
        '<a href="/tvs/">Televisions</a>'
        '<a href="/guides/">Buying guides</a>'
        '</nav></header>'
    )

def doc(title: str, description: str, route: str, body: str, schema: dict, data: str = "") -> str:
    canonical = SITE + route
    schema_txt = json.dumps(schema, ensure_ascii=False).replace("<", "\\u003c")
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="index,follow">
<title>{esc(title)} | Coupon World</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:url" content="{esc(canonical)}">
<link rel="stylesheet" href="/assets/category-research.css">
<script type="application/ld+json">{schema_txt}</script>
</head><body class="category-research">
<a class="cr-skip" href="#content">Skip to content</a>
{nav()}
<main class="cr-shell" id="content">{body}</main>
<footer class="cr-footer"><p><a href="/">Coupon World</a> · <a href="/phones/">Phones</a> · <a href="/accessories/">Accessories</a> · <a href="/tvs/">TVs</a> · <a href="/guides/about-coupon-world/">About &amp; affiliate disclosure</a></p>
<p>Manufacturer-source research for India. Confirm the exact model, availability, current price and warranty at the retailer. No commissioned testing or product ownership is claimed.</p>
<p>As an Amazon Associate I earn from qualifying purchases.</p></footer>
{data}
</body></html>'''

def schema(title: str, route: str, parent: str | None = None) -> dict:
    crumbs = [{"@type":"ListItem","position":1,"name":"Home","item":SITE + "/"}]
    if parent:
        crumbs.append({"@type":"ListItem","position":2,"name":parent.title(),"item":SITE + "/" + parent + "/"})
    crumbs.append({"@type":"ListItem","position":len(crumbs)+1,"name":title,"item":SITE+route})
    return {"@context":"https://schema.org","@graph":[
        {"@type":"WebPage","name":title,"url":SITE+route},
        {"@type":"BreadcrumbList","itemListElement":crumbs}
    ]}

def facts_html(item: dict, limit: int | None = None) -> str:
    fields = item["specifications"][:limit] if limit else item["specifications"]
    return "".join(
        '<div class="cr-fact"><dt>' + esc(f["label"]) + '</dt><dd>' + esc(f["value"]) +
        (' <a target="_blank" rel="noopener noreferrer" href="' +
         esc(f["source_url"]) + '">Maker source</a></dd></div>')
        for f in fields
    )

def card_html(item: dict) -> str:
    route = "/" + item["category"] + "/" + item["slug"] + "/"
    searchable = " ".join([item["brand"], item["model"], item["product_type"]] +
                          [str(f["label"]) + " " + str(f["value"]) for f in item["specifications"]])
    return f'''<article class="cr-card" data-model="{esc(item["slug"])}"
data-brand="{esc(item["brand"])}" data-type="{esc(item["product_type"])}"
data-search="{esc(searchable.lower())}">
<div class="cr-card-head"><span class="cr-tag">{esc(item["product_type"])}</span>
<span class="cr-check">Manufacturer source</span></div>
<h3><a href="{esc(route)}">{esc(item["model"])}</a></h3>
<p class="cr-muted">{esc(item["brand"])} · Checked {esc(item["reviewed_at"])}</p>
<dl class="cr-facts">{facts_html(item, 3)}</dl>
<div class="cr-card-foot"><a href="{esc(route)}">View specifications and limitations</a>
<label class="cr-compare-label"><input type="checkbox" data-compare="{esc(item["slug"])}"> Compare</label></div>
</article>'''

def hub_html(category: str, meta: dict, items: list[dict]) -> str:
    title = meta["title"]
    route = "/" + category + "/"
    brands = sorted({r["brand"] for r in items})
    types = sorted({r["product_type"] for r in items})
    options = lambda values: "".join('<option value="' + esc(x) + '">' + esc(x) + "</option>" for x in values)
    checks = "".join("<li>" + esc(x) + "</li>" for x in meta["buyer_checks"])
    other = "tvs" if category == "accessories" else "accessories"
    data = json.dumps({"category":category,"records":items}, ensure_ascii=False).replace("<", "\\u003c").replace("&", "\\u0026")
    body = f'''<p class="cr-crumb"><a href="/">Home</a> / {esc(title)}</p>
<section class="cr-hero"><p class="cr-eyebrow">India · evidence-first research</p>
<h1>{esc(title)}, with the sources visible.</h1>
<p>{esc(meta["description"])}</p>
<p class="cr-muted">{len(items)} source-reviewed models · {sum(len(r["specifications"]) for r in items)} documented facts · No verified live offers</p>
<div class="cr-actions"><a class="cr-primary" href="/phones/">Phone research</a>
<a href="/{other}/">Explore {'televisions' if other == 'tvs' else 'mobile accessories'}</a></div></section>
<section aria-labelledby="cr-explore-title"><h2 id="cr-explore-title">Explore documented products</h2>
<p>Filter by manufacturer or product type. Compare up to three <strong>same-type</strong> models side by side using source-backed facts. This is <strong>not</strong> a ranking, price comparison, or compatibility guarantee.</p>
<form class="cr-filters" id="cr-filters" role="search">
<label>Search features or models <input type="search" id="cr-query" placeholder="Brand, model or documented feature" autocomplete="off"></label>
<label>Manufacturer <select id="cr-brand"><option value="">All brands</option>{options(brands)}</select></label>
<label>Type <select id="cr-type"><option value="">All types</option>{options(types)}</select></label>
<button type="reset" id="cr-reset">Clear</button></form>
<p id="cr-status" role="status">{len(items)} researched models shown.</p>
<div class="cr-grid" id="cr-grid">{''.join(card_html(item) for item in items)}</div>
<p id="cr-no-results" hidden>No matching researched models. Try another brand or feature; no product or price is invented to fill gaps.</p>
</section>
<section class="cr-comparison" id="cr-comparison" hidden aria-labelledby="cr-compare-title"><h2 id="cr-compare-title">Compare manufacturer-documented facts</h2><p id="cr-comparison-status" role="status"></p><div class="cr-scroll" id="cr-comparison-table"></div><button type="button" id="cr-clear-compare">Clear comparison</button></section>
<section class="cr-guidance"><h2>What to verify before buying</h2><ul>{checks}</ul>
<p>Evidence shown here comes from original maker pages. Missing independent testing, compatibility, price or stock stays <strong>unknown</strong>. We do not promote these research cards into the existing purchase-eligible recommendation engine without its normal verified evidence and identity gates.</p></section>'''
    script = (f'<script type="application/json" id="cr-payload">{data}</script>'
              '<script defer src="/assets/category-research.js"></script>')
    return doc(title, meta["description"], route, body, schema(title, route), script)

def product_html(item: dict) -> str:
    route = "/" + item["category"] + "/" + item["slug"] + "/"
    title = item["model"]
    unknowns = "".join("<li>" + esc(x) + "</li>" for x in item["unknowns"])
    body = f'''<p class="cr-crumb"><a href="/">Home</a> / <a href="/{esc(item["category"])}/">{esc(item["category"].title())}</a> / {esc(title)}</p>
<article class="cr-detail"><p class="cr-eyebrow">{esc(item["product_type"])} · India manufacturer research</p>
<h1>{esc(title)}</h1>
<p class="cr-lead">Documented specifications, source links, buying considerations and unknowns. This is not a lab-tested review or verified current retailer offer.</p>
<div class="cr-meta"><span>Manufacturer: {esc(item["brand"])}</span>
<span>Source checked: {esc(item["reviewed_at"])}</span>
<span>Evidence: manufacturer-linked model facts</span></div>
<h2>Specifications and evidence</h2>
<dl class="cr-detail-facts">{facts_html(item)}</dl>
<p><a class="cr-primary" href="{esc(item["source_url"])}" target="_blank" rel="noopener noreferrer">Open original manufacturer specifications</a></p>
<section><h2>What these facts mean</h2><p>{esc(item["decision_note"])}</p>
<p><strong>Compatibility / exact-variant caution:</strong> {esc(item["compatibility_caution"])}</p></section>
<section><h2>Not yet verified</h2><ul>{unknowns}</ul>
<p>Current price, retailer inventory, cashback, exact cable/console/device compatibility and third-party performance claims are not inferred from this record.</p></section>
<section><h2>Continue researching</h2><p><a href="/{esc(item["category"])}/">Compare more {esc(item["category"])}</a>
 · <a href="/phones/">Explore the existing smartphone research</a>
 · <a href="/guides/about-coupon-world/">Read our disclosure</a></p></section>
</article>'''
    return doc(title + " specifications India", "Manufacturer-sourced " + title +
               " specifications, limitations and original evidence for India. No live merchant price or unverified performance claims.",
               route, body, schema(title, route, item["category"]))

def publish_category_research_pages(destination: Path) -> list[str]:
    payload = load_checked_records()
    names = []
    for category in CATEGORIES:
        items = sorted((r for r in payload["records"] if r["category"] == category),
                       key=lambda x: x["model"].casefold())
        meta = payload["categories"][category]
        hub_path = destination / category
        hub_path.mkdir(parents=True, exist_ok=True)
        (hub_path / "index.html").write_text(hub_html(category, meta, items), encoding="utf-8")
        names.append(SITE + "/" + category + "/")
        for item in items:
            page = hub_path / item["slug"]
            page.mkdir(parents=True, exist_ok=True)
            (page / "index.html").write_text(product_html(item), encoding="utf-8")
            names.append(SITE + "/" + category + "/" + item["slug"] + "/")

    ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", ns)
    sitemap = destination / "sitemap.xml"
    tree = ET.parse(sitemap)
    root = tree.getroot()
    existing = {str(e.text) for e in root.findall(f"{{{ns}}}url/{{{ns}}}loc")}
    for url in names:
        if url in existing:
            raise ValueError("Duplicate sitemap URL " + url)
        entry = ET.SubElement(root, f"{{{ns}}}url")
        ET.SubElement(entry, f"{{{ns}}}loc").text = url
        if url.rstrip("/").split("/")[-1] not in CATEGORIES:
            ET.SubElement(entry, f"{{{ns}}}lastmod").text = payload["reviewed_at"]
    tree.write(sitemap, encoding="utf-8", xml_declaration=True)
    print(f"accessories and TVs: {len(payload['records'])} research pages, 2 hubs")
    return names
