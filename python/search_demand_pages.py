"""Publish one transparent landing page from the archived search-demand signal.

The demand file is a historical Google Keyword Planner planning input. This
page uses it to prioritize editorial coverage, not to claim current traffic,
rankings, sales, or live search volume.
"""
from __future__ import annotations

import html
import json
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://coupon-world.in"
PATH = "/seo/india-smartphone-search-demand.html"
SOURCE = ROOT / "data" / "mobile_google_demand_ranked_126.json"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def publish_search_demand(destination: Path) -> str:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    products = data["products"]
    if data.get("market") != "IN" or data.get("category") != "smartphone":
        raise ValueError("search-demand source must be scoped to Indian smartphones")

    # Only link to pages that the current editorial publication already
    # supports. Do not create thin pages just because a keyword seed exists.
    published = {
        "vivo t4x": ("Vivo T4X 5G", "/phones/vivo-t4x-5g/"),
        "apple iphone 16": ("Apple iPhone 16", "/phones/apple-iphone-16/"),
        "apple iphone 17": ("Apple iPhone 17", "/phones/apple-iphone-17/"),
        "apple iphone 17 pro": ("Apple iPhone 17 Pro", "/phones/apple-iphone-17-pro/"),
        "apple iphone 17 pro max": ("Apple iPhone 17 Pro Max", "/phones/apple-iphone-17-pro-max/"),
        "google pixel 10": ("Google Pixel 10", "/phones/google-pixel-10/"),
        "samsung galaxy a36 5g": ("Samsung Galaxy A36 5G", "/phones/samsung-galaxy-a36-5g/"),
        "samsung galaxy a56 5g": ("Samsung Galaxy A56 5G", "/phones/samsung-galaxy-a56-5g/"),
        "nothing phone 3a": ("Nothing Phone (3a)", "/phones/nothing-phone-3a/"),
        "poco x7 pro": ("POCO X7 Pro", "/phones/poco-x7-pro/"),
    }
    selected = products[:10]
    coverage_rows = []
    for item in selected:
        key = f'{item["brand"]} {item["model"]}'.casefold()
        match = next((value for name, value in published.items() if name in key or key in name), None)
        label = match[0] if match else f'{item["brand"]} {item["model"]}'
        tier = item.get("google_demand_tier", "historical planning signal")
        if match:
            coverage_rows.append(
                f'<tr><th scope="row"><a href="{match[1]}">{esc(label)}</a></th>'
                f'<td>{esc(tier.replace("_", " "))}</td><td>Source-linked page published</td></tr>'
            )
        else:
            coverage_rows.append(
                f'<tr><th scope="row">{esc(label)}</th><td>{esc(tier.replace("_", " "))}</td>'
                '<td>Coverage gap; no page published without an evidence review</td></tr>'
            )

    title = "India Smartphone Search Demand: What We Cover | Coupon World"
    description = (
        "A transparent India smartphone content plan based on historical search-demand signals. "
        "See which source-linked phone pages are published and which topics still need evidence review."
    )
    article = f'''<!doctype html><html lang="en-IN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(description)}"><meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{BASE + PATH}"><link rel="alternate" hreflang="en-IN" href="{BASE + PATH}"><link rel="stylesheet" href="/assets/phone-guides.css?v=20261104">
<meta property="og:type" content="article"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{BASE + PATH}">
<script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@type": "Article", "headline": title, "description": description, "mainEntityOfPage": BASE + PATH, "author": {"@type": "Organization", "name": "Coupon World"}}, ensure_ascii=False).replace("<", "\\u003c")}</script></head>
<body><a class="skip" href="#content">Skip to content</a><header><nav aria-label="Main navigation"><a class="brand" href="/">CW <span>Coupon World<small>Research before you buy</small></span></a><a href="/phones/">Phone specifications</a><a href="/guides/phone-budget-guides/">Buying guides</a><a href="/">Find a phone ↗</a></nav></header>
<main id="content"><nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/guides/phone-budget-guides/">Phone guides</a> / Search demand</nav>
<article><div class="eyebrow">COUPON WORLD / EDITORIAL PRIORITY</div><h1>India smartphone search demand: what we cover</h1>
<p class="lead">Use search demand to decide what to research next, not to manufacture pages. This page connects a historical planning signal to the source-linked phone research already published on Coupon World.</p>
<aside class="note"><strong>Important context</strong><p>The underlying Google Keyword Planner export covers 1 September 2025 to 31 August 2026 and was exported on 12 September 2026. It is not a current Search Console report, a ranking report, a sales forecast, or proof that Google will send traffic.</p></aside>
<section><h2>What people usually need from a phone page</h2><p>The demand file groups model research with practical follow-up questions: price, buy intent, and exact RAM/storage variants. A useful page must answer those questions with a clear model identity, India applicability, source-linked specifications, missing information, and honest retailer checks.</p><ul><li>Confirm the exact model and memory variant.</li><li>Separate dated budget references from today’s price and stock.</li><li>Explain trade-offs instead of inventing a universal “best” score.</li><li>Link to original manufacturer evidence and comparable independent tests where available.</li></ul></section>
<section><h2>Coverage of the highest-priority planning signals</h2><p>These are the first ten entries in the archived planning file. “Published” means a source-linked research page exists. “Coverage gap” means we are deliberately not publishing a thin page yet.</p><div class="table-wrap"><table><thead><tr><th scope="col">Model signal</th><th scope="col">Planning tier</th><th scope="col">Editorial status</th></tr></thead><tbody>{''.join(coverage_rows)}</tbody></table></div></section>
<section><h2>Start with the pages that can answer a real decision</h2><p><a href="/phones/">Browse source-linked phone specifications</a> for exact model research, <a href="/phones/under-25000/">read the under-₹25,000 guide</a> for budget trade-offs, or <a href="/compare/">compare exact variants</a> when two models are already on your shortlist.</p><p>For camera, battery, gaming, software support, and memory questions, use the <a href="/guides/phone-budget-guides/">phone buying guides</a>. Each guide shows what the evidence does and does not establish.</p></section>
<section><h2>What we will publish next</h2><p>New pages will be added only when the model identity, India source coverage, and meaningful editorial explanation pass review. A large keyword list is not enough. If a model lacks reliable evidence, the correct action is to keep it in the research queue rather than create a near-duplicate page.</p></section>
<section class="action"><h2>Help us choose the next question</h2><p>Search the existing research by budget, camera, battery, gaming, software support, RAM, or storage. The tool is designed to expose gaps instead of silently relaxing a user’s request.</p><a class="button" href="/?q=phone+under+25000#mobileResearchSearch">Find a phone by your need ↗</a></section>
</article></main><footer><a href="/guides/phone-budget-guides/">All phone buying guides</a> · <a href="/guides/about-coupon-world/">About and research method</a><p>Prepared from a historical planning export and reviewed source data. No current search volume, ranking, price, stock, or performance winner is claimed.</p></footer></body></html>'''
    target = destination / PATH.lstrip("/")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(article, encoding="utf-8")

    ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", ns)
    sitemap = destination / "sitemap.xml"
    tree = ET.parse(sitemap)
    root = tree.getroot()
    existing = {node.text for node in root.findall(f"{{{ns}}}url/{{{ns}}}loc")}
    url = BASE + PATH
    if url not in existing:
        node = ET.SubElement(root, f"{{{ns}}}url")
        ET.SubElement(node, f"{{{ns}}}loc").text = url
        ET.SubElement(node, f"{{{ns}}}lastmod").text = "2026-11-12"
    tree.write(sitemap, encoding="utf-8", xml_declaration=True)
    return url
