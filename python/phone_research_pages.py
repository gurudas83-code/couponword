"""Publish a small editorial set of source-linked phone fact pages.

This is a static publishing adapter on top of the existing public research
catalogue, NOT a new search, scoring, offer or recommendation engine.

Do not automatically publish all models: the editorial key set is deliberately
curated. New keys require a documented review of the existing source record.
"""
from __future__ import annotations

import html
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import quote, urlencode, urlsplit
from xml.etree import ElementTree as ET

SITE = "https://coupon-world.in"
HUB = "/phones/"
# Editorial selection from the existing official-evidence registry. Curated
# for actual smartphone-search intent, not generated from keyword permutations.
# A key can still be withheld by the strict source/field gate below.
EDITORIAL_MODEL_KEYS = (
    "iqoo|neo 10",
    "motorola|signature",
    "nothing|phone 3a",
    "oneplus|13",
    "oneplus|13r",
    "redmi|note 14 5g",
    "samsung|galaxy a36 5g",
    "samsung|galaxy a37 5g",
    "samsung|galaxy a56 5g",
    "samsung|galaxy f36 5g",
    "samsung|galaxy f70e 5g",
    "samsung|galaxy m17 5g",
    "samsung|galaxy m17e 5g",
    "samsung|galaxy s24",
    "samsung|galaxy s25 fe",
    "samsung|galaxy s26 ultra",
    "vivo|t4x 5g",
    "vivo|t5 pro 5g",
    "vivo|t5x 5g",
    "vivo|v60",
)

# Not all official-source research is an independently tested India-market
# device. Display only source-linked factual fields, never price/rank claims.
MIN_DOCUMENTED_FIELDS = 8
REQUIRED_SOURCE_SCHEME = "https"
FALLBACK_IMAGE = SITE + "/assets/coupon-world-og.svg"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def slug_for(card: dict) -> str:
    label = str(card["brand"]) + " " + str(card["model"])
    label = label.replace("+", " plus ")
    return re.sub(r"[^a-z0-9]+", "-", label.casefold()).strip("-")


def model_title(card: dict) -> str:
    return f'{card["brand"]} {card["model"]}'.strip()


def value_text(value: object) -> str:
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, list):
        return ", ".join(str(x) for x in value)
    if isinstance(value, (dict, tuple, set)):
        return ""
    return str(value if value is not None else "").strip()


def dated(value: object) -> str | None:
    try:
        return date.fromisoformat(str(value or "")[:10]).isoformat()
    except ValueError:
        return None


def accepted_specs(card: dict) -> list[tuple[str, dict]]:
    result = []
    for key, item in (card.get("specifications") or {}).items():
        if not isinstance(item, dict):
            continue
        source = urlsplit(str(item.get("source_url") or ""))
        value = value_text(item.get("value"))
        if source.scheme != REQUIRED_SOURCE_SCHEME or not source.hostname or not value:
            continue
        result.append((str(key), item))
    return sorted(result, key=lambda row: str(row[1].get("label") or row[0]).casefold())


def eligible(card: dict) -> bool:
    # This is the source catalogue's evidence label. The page itself carefully
    # distinguishes model-level specifications from exact variant certification.
    return card.get("status") == "OFFICIAL_VERIFIED" and len(accepted_specs(card)) >= MIN_DOCUMENTED_FIELDS


def link(href: str, label: object, rel: str = "") -> str:
    rel_text = f' rel="{esc(rel)}"' if rel else ""
    return f'<a href="{esc(href)}"{rel_text}>{esc(label)}</a>'


def breadcrumb_schema(title: str, canonical: str) -> dict:
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Phone specifications", "item": SITE + HUB},
            {"@type": "ListItem", "position": 3, "name": title, "item": canonical},
        ],
    }


def html_doc(title: str, description: str, path: str, body: str, structured: dict) -> str:
    canonical = SITE + path
    js = json.dumps(structured, ensure_ascii=False).replace("<", "\\u003c")
    return f'''<!doctype html><html lang="en-IN"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | Coupon World</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{esc(FALLBACK_IMAGE)}">
<meta name="twitter:card" content="summary">
<link rel="stylesheet" href="/assets/phone-guides.css?v=20261104">
<style>
.page-shell{{max-width:1050px;margin:0 auto;padding:1rem}}
.mobile-fact-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem}}
.mobile-fact-card{{border:1px solid #c8d4df;border-radius:12px;padding:1rem}}
.mobile-fact-card h3{{margin:0 0 .5rem}}
.mobile-fact-table-wrap{{overflow-x:auto}}
.mobile-fact-table{{border-collapse:collapse;width:100%;font-size:.95rem}}
.mobile-fact-table th,.mobile-fact-table td{{padding:.75rem;text-align:left;border-bottom:1px solid #dbe3ea;vertical-align:top}}
.mobile-fact-table th{{width:34%}}
.mobile-fact-note{{padding:1rem;border-inline-start:4px solid #3a7395;background:#eef5f8;margin:1rem 0}}
.mobile-fact-links a{{display:inline-block;margin:.25rem .75rem .25rem 0}}
.mobile-fact-small{{font-size:.92rem;opacity:.85}}
</style>
<script type="application/ld+json">{js}</script>
</head><body><a class="skip" href="#content">Skip to content</a>
<header><nav aria-label="Main navigation"><a class="brand" href="/">CW <span>Coupon World</span></a>
<a href="/phones/">Phone specifications</a><a href="/guides/phone-budget-guides/">Buying guides</a>
<a href="/#mobileResearchSearch">Find a phone</a></nav></header>
<main id="content" class="page-shell">{body}</main>
<footer class="page-shell"><p>{link("/", "Home")} · {link(HUB, "Phone specification hub")} · {link("/seo/phone-research-evidence-method.html", "Evidence methodology")}</p>
<p class="mobile-fact-small">Editorial research only. No physical hands-on testing, current retailer price, stock or purchase eligibility is asserted. Retailer searches may contain affiliate links.</p></footer></body></html>'''


def summary_fields(card: dict, maximum: int = 3) -> list[tuple[str, str]]:
    wanted = (
        "chipset", "display_type", "display_inches", "display_refresh_max_hz",
        "battery_mah_typical", "rear_main_mp", "security_update_policy",
    )
    specs = card.get("specifications") or {}
    result = []
    for key in wanted:
        value = specs.get(key)
        if isinstance(value, dict) and value_text(value.get("value")):
            result.append((str(value.get("label") or key.replace("_", " ").title()), value_text(value["value"])))
        if len(result) == maximum:
            break
    return result


def render_card(card: dict) -> str:
    title = model_title(card)
    keyfacts = summary_fields(card, maximum=2)
    facts = " · ".join(f"{esc(k)}: {esc(v)}" for k, v in keyfacts)
    path = HUB + slug_for(card) + "/"
    return f'<article class="mobile-fact-card"><h3>{link(path, title)}</h3><p>{facts or "Documented specification sources available"}</p><p class="mobile-fact-small">{len(accepted_specs(card))} source-linked fields · Research, not a live offer</p></article>'


def render_model(card: dict, related: list[dict]) -> str:
    title = model_title(card)
    path = HUB + slug_for(card) + "/"
    canonical = SITE + path
    specs = accepted_specs(card)
    published_check = dated(card.get("research_checked_at"))
    date_label = f'<p class="mobile-fact-small">Sources reviewed in research on <time datetime="{esc(published_check)}">{esc(published_check)}</time>. A check date is not a new market price or lab-test date.</p>' if published_check else '<p class="mobile-fact-small">Research check date not available.</p>'
    headline = f"{title} specifications in India"
    description = f"Explore documented {title} specifications, original manufacturer source links, missing evidence and exact-variant cautions. No live price or stock claims."
    rows = []
    for key, item in specs:
        label = str(item.get("label") or key.replace("_", " ").title())
        value = value_text(item.get("value"))
        source = str(item["source_url"])
        checked = dated(item.get("checked_at") or item.get("checked_date"))
        source_note = f'<span class="mobile-fact-small">Checked {esc(checked)}</span>' if checked else ""
        rows.append(f'<tr><th scope="row">{esc(label)}</th><td>{esc(value)}</td>'
                    f'<td>{link(source, "Manufacturer source", "noopener noreferrer")} {source_note}</td></tr>')
    missing = card.get("missing_specifications") or []
    incomplete = ", ".join(str(key).replace("_", " ").title() for key in missing[:8])
    missing_para = (f"<p>Not yet documented in this research: {esc(incomplete)}."
                    f'{" Further fields remain unverified." if len(missing)>8 else ""}</p>') if missing else "<p>No additional fields are listed as missing in the current research export; that does not certify completeness.</p>"
    c = card.get("research_budget_reference")
    budget_text = ('A dated retailer observation exists in the research dataset; it is used only as a budget-screening reference, '
                   'not a current price, stock signal or performance-ranking input.' if c else
                   'No dated price reference is available in this record; it is not eligible for reference-price budget filtering.')
    retail = []
    for item in card.get("retailer_search_links") or []:
        host = urlsplit(str(item.get("url") or "")).hostname
        if host not in {"www.amazon.in", "www.flipkart.com", "www.croma.com"}:
            continue
        retailer = str(item.get("retailer") or "")
        label = ("Browse Croma category" if retailer == "Croma" else f"Search {retailer}")
        retail.append(link(str(item["url"]), label, "nofollow sponsored noopener noreferrer"))
    query = urlencode({"q": title})
    search = f"/?{query}#mobileResearchSearch"
    facts = "".join(f"<li>{esc(k)}: <strong>{esc(v)}</strong></li>" for k,v in summary_fields(card, maximum=3))
    similar = "".join(render_card(item) for item in related)
    body = f'''<nav class="crumbs" aria-label="Breadcrumb">{link("/", "Home")} / {link(HUB, "Phone specifications")} / {esc(title)}</nav>
<article><div class="eyebrow">INDIA SMARTPHONE RESEARCH / MANUFACTURER SOURCES</div>
<h1>{esc(headline)}</h1>
<p class="lead">{esc(description)}</p>
<div class="mobile-fact-note"><strong>Research, not a purchase recommendation.</strong>
<p>Manufacturer-linked model facts appear below. A source-linked model specification does not certify every India RAM/storage configuration, hands-on performance, current availability or an exact retail listing. These pages never rank phones by dated prices.</p></div>
{date_label}
<section><h2>Key documented facts</h2><ul>{facts}</ul>
<p>Use the exact source links in the table; a headline battery capacity or megapixel count does not establish real-world battery or camera quality.</p></section>
<section><h2>Specifications and original sources</h2>
<p>{len(specs)} fields have source links in the saved research record. If a model has multiple memory variants, verify the exact one on the manufacturer's India page before choosing.</p>
<div class="mobile-fact-table-wrap"><table class="mobile-fact-table"><caption>Documented model-level specifications, not a tested review</caption>
<thead><tr><th scope="col">Field</th><th scope="col">Documented value</th><th scope="col">Original evidence</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table></div></section>
<section><h2>Unknowns and purchasing limitations</h2>{missing_para}
<p>{esc(budget_text)}</p><p>{esc(str(card.get("physical_variant_note") or "Exact physical RAM/storage variants must be confirmed independently."))}</p></section>
<section><h2>Compare this phone with others</h2><p>Use Coupon World's existing research filter and compare up to three documented phones side by side. Compare specification sources and test conditions, not raw camera megapixels or battery capacity alone.</p>
<p>{link(search, "Open this model in the phone research tool")}</p></section>
<section><h2>Check retailer listings independently</h2><p>These are retailer searches, not verified exact-product offers. A Croma link may lead only to the general phone category; confirm model, memory configuration, price, seller, stock, warranty and delivery there.</p><p class="mobile-fact-links">{" · ".join(retail)}</p></section>
<section><h2>How this record was prepared</h2><p>Coupon World organizes source-linked manufacturer research. This is not a claim of first-hand phone ownership, testing, or an independent lab benchmark. Further evidence and corrections may change the record. {link("/seo/phone-research-evidence-method.html", "Review our evidence limitations")}.</p></section>
</article><section><h2>Related documented phone research</h2><div class="mobile-fact-grid">{similar}</div></section>'''
    schema = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebPage", "name": headline, "url": canonical,
         "description": description, "about": {"@type": "Thing", "name": title},
         "isPartOf": {"@type": "WebSite", "name": "Coupon World", "url": SITE + "/"},
         **({"dateModified": published_check} if published_check else {})},
        breadcrumb_schema(title, canonical),
    ]}
    return html_doc(headline, description, path, body, schema)


def render_hub(cards: list[dict]) -> str:
    title = "Smartphone specifications with original sources"
    description = (f"Browse {len(cards)} curated India smartphone research pages with manufacturer-linked facts, "
                   "exact-variant cautions, missing fields and independent retailer searches.")
    by_brand: dict[str, list[dict]] = {}
    for card in cards:
        by_brand.setdefault(str(card["brand"]).title(), []).append(card)
    sections = "".join(f'<section><h2>{esc(brand)} phones</h2><div class="mobile-fact-grid">'
                       + "".join(render_card(c) for c in sorted(rows, key=lambda r: model_title(r).casefold()))
                       + "</div></section>" for brand, rows in sorted(by_brand.items()))
    body = f'''<nav class="crumbs" aria-label="Breadcrumb">{link("/", "Home")} / Phone specifications</nav>
<div class="eyebrow">SMARTPHONE RESEARCH / INDIA</div><h1>Smartphone specifications with original sources</h1>
<p class="lead">{esc(description)}</p>
<aside class="mobile-fact-note"><strong>Editorially selected, source-linked records.</strong>
<p>These pages reflect the existing research database, not all phones sold today. No phone on this hub has a certified live offer or an independent overall winner from this page. More models will be published only after sufficient source-backed fields pass the existing evidence checks.</p></aside>
<p>{link("/guides/phone-budget-guides/", "Browse budget and priority guides")} · {link("/#mobileResearchSearch", "Search all 232 research models")}</p>
{sections}
<section><h2>What to compare before buying</h2><p>Use the linked manufacturer specifications to verify processor, display, connectivity and physical memory. Then inspect comparable independent tests for camera, battery and gaming. A missing lab result is not a poor result; it is unknown evidence. Compare the exact India RAM and storage configuration at the retailer.</p></section>'''
    schema = {"@context": "https://schema.org", "@graph": [
        {"@type": "CollectionPage", "name": title, "url": SITE + HUB,
         "description": description, "mainEntity": {"@type": "ItemList",
         "numberOfItems": len(cards), "itemListElement": [
             {"@type": "ListItem", "position": i+1, "name": model_title(card),
              "url": SITE + HUB + slug_for(card) + "/"}
             for i, card in enumerate(cards)]}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Phone specifications", "item": SITE + HUB}]},
    ]}
    return html_doc(title, description, HUB, body, schema)


def render_phone_research_pages(destination: Path) -> list[str]:
    """Produce the editorial pages and amend the *artifact*, never root repo."""
    payload = json.loads((destination / "data" / "mobile_research_catalogue.json").read_text(encoding="utf-8"))
    all_cards = {card["model_key"]: card for card in payload.get("model_cards") or []}
    if len(all_cards) != 232:
        raise RuntimeError("Phone-page publication requires the existing 232-model registry")

    selected = []
    for key in EDITORIAL_MODEL_KEYS:
        card = all_cards.get(key)
        if card and eligible(card):
            selected.append(card)
    if not 15 <= len(selected) <= len(EDITORIAL_MODEL_KEYS):
        raise RuntimeError(f"Source-backed editorial phone pages below quality gate: {len(selected)}")
    if len({slug_for(c) for c in selected}) != len(selected):
        raise RuntimeError("Canonical phone research slugs conflict; publication blocked")

    selected.sort(key=lambda c: model_title(c).casefold())
    output = destination / HUB.lstrip("/")
    output.mkdir(parents=True, exist_ok=True)
    (output / "index.html").write_text(render_hub(selected), encoding="utf-8")
    urls = [SITE + HUB]
    for card in selected:
        name = slug_for(card)
        others = [c for c in selected if c["model_key"] != card["model_key"]]
        related = sorted(others, key=lambda c: (c["brand"].casefold() != card["brand"].casefold(),
                                                model_title(c).casefold()))[:3]
        target = output / name
        target.mkdir(parents=True, exist_ok=True)
        (target / "index.html").write_text(render_model(card, related), encoding="utf-8")
        urls.append(SITE + HUB + name + "/")

    ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", ns)
    sitemap = destination / "sitemap.xml"
    tree = ET.parse(sitemap)
    root = tree.getroot()
    # The old generic under-15k keyword page now redirects immediately to
    # the current substantive guide. Omit the obsolete source URL from the
    # published sitemap while retaining the redirect for old bookmarks.
    legacy_url = SITE + "/seo/best-mobile-under-15000.html"
    for item in list(root.findall(f"{{{ns}}}url")):
        loc = item.find(f"{{{ns}}}loc")
        if loc is not None and loc.text == legacy_url:
            root.remove(item)
    existing = {str(node.text) for node in root.findall(f"{{{ns}}}url/{{{ns}}}loc")}
    for url in urls:
        if url in existing:
            raise RuntimeError(f"Duplicate canonical research URL in public sitemap: {url}")
        element = ET.SubElement(root, f"{{{ns}}}url")
        ET.SubElement(element, f"{{{ns}}}loc").text = url
        if url != SITE + HUB:
            matched = next(c for c in selected if url.endswith("/" + slug_for(c) + "/"))
            checked = dated(matched.get("research_checked_at"))
            if checked:
                ET.SubElement(element, f"{{{ns}}}lastmod").text = checked
    tree.write(sitemap, encoding="utf-8", xml_declaration=True)
    print(f"curated source-linked phone pages: {len(selected)}, hub: {HUB}")
    return urls
