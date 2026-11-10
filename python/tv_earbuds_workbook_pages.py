#!/usr/bin/env python3
"""Publish the 20-TV / 20-earbuds workbook as dated, evidence-labelled research.

This is a projection into the existing static Pages artifact, NOT another
shopping engine. No live offer, availability, SKU identity or performance
ranking can be inferred from an editorial workbook or retailer search URL.
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

from python.category_research_pages import esc, doc, schema, SITE

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "india_tv_earbuds_40_catalogue.json"
ROUTES = {
    "tvs": ("india-20", "20 TVs to research in India", "Televisions"),
    "accessories": ("earbuds-20", "20 wireless earbuds to research in India", "Earbuds"),
}
HOSTS = {"amazon": ("amazon.in", "amzn.in"),
         "flipkart": ("flipkart.com",), "croma": ("croma.com",)}

def clean_url(url):
    return str(url or "").strip()

def load_catalogue():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    if data.get("mode") != "DATED_RESEARCH_ONLY_NO_LIVE_OFFERS":
        raise ValueError("Untrusted workbook catalogue mode")
    items = data.get("records", [])
    if len(items) != 40 or len({x.get("id") for x in items}) != 40:
        raise ValueError("Exactly 40 unique records required")
    if sum(x.get("category") == "tvs" for x in items) != 20 or \
       sum(x.get("category") == "accessories" for x in items) != 20:
        raise ValueError("Exactly twenty per category required")
    for x in items:
        if x.get("product_status") != "RESEARCH_ONLY" or x.get("purchase_cta_eligible") is not False or \
           x.get("performance_ranking_eligible") is not False or x.get("price_ranking_weight") != 0:
            raise ValueError("Research product promoted into commerce or ranking")
        if not x.get("brand") or not x.get("model") or not x.get("evidence_caveat"):
            raise ValueError("Missing research identity or limitations")
        specs = x.get("specifications")
        if not isinstance(specs, list):
            raise ValueError("Invalid specifications")
        for spec in specs:
            if not spec.get("label") or not spec.get("value"):
                raise ValueError("Blank specification field")
        for store, info in x.get("retailers", {}).items():
            if store not in HOSTS or info.get("live_offer") is not False or info.get("checkout_eligible") is not False:
                raise ValueError("Unapproved merchant admission")
            url = clean_url(info.get("retailer_research_url"))
            parsed = urlsplit(url)
            if parsed.scheme != "https" or not any(
                parsed.hostname == host or (parsed.hostname or "").endswith("." + host)
                for host in HOSTS[store]
            ):
                raise ValueError("Invalid retailer research URL: " + store)
            price = info.get("price_inr")
            if price is not None:
                if isinstance(price, bool) or not isinstance(price, (int, float)) or price <= 0:
                    raise ValueError("Invalid dated retailer reference")
                if not info.get("checked_at") or not info.get("observation_source_url"):
                    raise ValueError("Unsubstantiated dated price reference")
    return data

def model_route(item):
    category = item["category"]
    folder = ROUTES[category][0]
    return "/" + category + "/" + folder + "/" + item["id"].lower() + "/"

def list_route(category):
    return "/" + category + "/" + ROUTES[category][0] + "/"

def research_specifications(item):
    # The quote is dated, not an official maker specification. Keep separate.
    return item["specifications"]

def retailer_link(info, retailer):
    exact = info.get("exact_model_link_verified") is True
    label = ("Verified product on " if exact else "Search model on ") + retailer.title()
    return '<a href="' + esc(info["retailer_research_url"]) + \
        '" target="_blank" rel="noopener noreferrer nofollow" aria-label="' + esc(label) + '">' + esc(label) + '</a>'

def quote_text(info, store):
    if store == "amazon":
        # An Amazon affiliate account does not imply Creators API price rights.
        return "Not API-verified"
    value = info.get("price_inr")
    return "₹" + format(round(value), ",") + " · dated " + esc(info.get("checked_at")) \
        if value is not None else "Not verified"

def research_visual(item):
    """Original CSS/SVG-style television illustration, never a model photograph."""
    if item.get("category") != "tvs":
        return ""
    import hashlib
    palette = [("#123c64", "#42c4df"), ("#2d275f", "#d174e9"),
               ("#143e43", "#6fe2a9"), ("#3d2850", "#f9a566")]
    a, b = palette[int(hashlib.sha256(item["id"].encode()).hexdigest()[:2], 16) % len(palette)]
    return (
        '<div class="cw-tv-visual" role="img" aria-label="Illustrative television graphic, not an exact product photo" '
        'style="--cw-tv-a:' + a + ';--cw-tv-b:' + b + '">'
        '<div class="cw-tv-bezel"><div class="cw-tv-screen"><span class="cw-tv-glow"></span>'
        '<span class="cw-tv-landscape"></span></div></div>'
        '<div class="cw-tv-foot"></div><span class="cw-tv-visual-caption">Illustration · not product photo</span></div>'
    )

TV_VISUAL_CSS = """<style>
.cw-tv-visual{width:100%;max-width:420px;box-sizing:border-box;display:flex;align-items:center;flex-direction:column;justify-content:center;padding:18px 18px 9px;border-radius:16px;background:linear-gradient(145deg,#f3f6fc,#e8edf5);margin:12px auto 16px}
.cw-tv-bezel{width:90%;aspect-ratio:16/9;padding:5px;border-radius:9px;background:linear-gradient(135deg,#202937,#05080d);box-shadow:0 13px 23px #192c4836,0 2px 3px #15233d40}
.cw-tv-screen{width:100%;height:100%;position:relative;overflow:hidden;border-radius:4px;background:linear-gradient(130deg,var(--cw-tv-a) 0%,#142e56 45%,var(--cw-tv-b) 100%)}
.cw-tv-glow{position:absolute;inset:-30% -10%;background:radial-gradient(ellipse at 78% 23%,#ffffffaa,transparent 34%),radial-gradient(ellipse at 22% 80%,#50e4f5aa,transparent 48%);transform:rotate(-9deg)}
.cw-tv-landscape{position:absolute;left:-10%;right:-10%;bottom:-25%;height:68%;border-radius:50% 45% 0 0;background:linear-gradient(155deg,#ffffff66,#121d5eaa);transform:rotate(-11deg)}
.cw-tv-foot{width:27%;height:13px;border-bottom:4px solid #424a58;background:linear-gradient(90deg,transparent 44%,#525e6e 44%,#525e6e 56%,transparent 56%);border-radius:0 0 45% 45%}
.cw-tv-visual-caption{font-size:10px;letter-spacing:.03em;color:#596778;margin-top:8px}
@media(prefers-color-scheme:dark){.cw-tv-visual{background:linear-gradient(145deg,#252c39,#1c2431)}.cw-tv-visual-caption{color:#bdc7d7}}
</style>"""

def card(item):
    route = model_route(item)
    fields = research_specifications(item)
    summary = "; ".join(str(f["label"]) + ": " + str(f["value"]) for f in fields)
    search = " ".join((item["brand"], item["model"], summary)).casefold()
    choices = "".join(
        "<li><b>" + esc(store.title()) + ":</b> " + quote_text(item["retailers"][store], store) +
        " · " + retailer_link(item["retailers"][store], store) + "</li>"
        for store in ("amazon", "flipkart", "croma")
    )
    first = "".join("<dt>" + esc(f["label"]) + "</dt><dd>" + esc(f["value"]) + "</dd>"
                    for f in fields[:3])
    return f'''<article class="cr-card" data-model="{esc(item["id"].lower())}"
data-brand="{esc(item["brand"])}" data-type="{esc(item["product_type"])}"
data-search="{esc(search)}">
<div class="cr-card-head"><span class="cr-tag">{esc(item["brand"])}</span>
<span class="cr-check">{esc(item["source_grade"])}</span></div>
{research_visual(item)}\n<h3><a href="{esc(route)}">{esc(item["model"])}</a></h3>
<dl class="cr-facts">{first}</dl>
<p class="cr-muted">Prices are dated research references, not current offers.</p>
<ul class="cw-retailer-prices">{choices}</ul>
<div class="cr-card-foot"><a href="{esc(route)}">Detailed research</a>
<label class="cr-compare-label"><input type="checkbox" data-compare="{esc(item["id"].lower())}"> Compare</label></div></article>'''

def item_payload(item):
    # Existing category-research.js supports source-linked spec comparisons.
    return {
        "slug": item["id"].lower(), "brand":item["brand"],
        "model":item["model"], "product_type":item["product_type"],
        "specifications": research_specifications(item),
        "source_grade":item["source_grade"],
    }

def hub(category, items):
    folder,title,_=ROUTES[category]
    route = list_route(category)
    brands = sorted({x["brand"] for x in items})
    option = "".join('<option value="' + esc(x) + '">' + esc(x) + '</option>' for x in brands)
    serialized = json.dumps({"category": category, "records":[item_payload(x) for x in items]},
                            ensure_ascii=False).replace("<", "\\u003c").replace("&","\\u0026")
    body=f'''<p class="cr-crumb"><a href="/">Home</a> / <a href="/{esc(category)}/">{esc(category.title())}</a> / Research shortlist</p>
<section class="cr-hero">
<p class="cr-eyebrow">India · 5 November 2026 · Dated research snapshot</p>
<h1>{esc(title)}</h1>
<p>Research all 20 models from the Coupon World comparison workbook, check specifications and open independently labelled verified-product links or retailer searches for Amazon, Flipkart and Croma.</p>
<p><strong>Important:</strong> The reference prices are not live API quotes. No stock, exact purchase eligibility, independent sound/picture quality ranking, or retailer checkout is certified here.</p>
<p><a href="/{esc(category)}/">Return to the source-reviewed category hub</a></p>
{('<figure class="cw-licensed-tv-photo"><img src="https://c.pxhere.com/photos/af/b7/photo-156633.jpg!d" alt="Generic television in a room, CC0 public-domain editorial photograph; not one of the listed TV models" loading="lazy" decoding="async" referrerpolicy="no-referrer" width="960" height="640"><figcaption>Illustrative television photograph, not a listed model. <a href="https://pxhere.com/en/photo/156633" rel="noopener noreferrer nofollow" target="_blank">Photo source and CC0 public-domain license: PxHere</a>.</figcaption></figure><style>.cw-licensed-tv-photo{max-width:780px;margin:20px auto 24px}.cw-licensed-tv-photo img{width:100%;height:auto;max-height:360px;object-fit:cover;border-radius:18px;box-shadow:0 10px 28px #0002}.cw-licensed-tv-photo figcaption{font-size:12px;color:inherit;opacity:.82;margin-top:8px;text-align:center}</style>' if category == "tvs" else "")}
</section>
<section aria-labelledby="research-list"><h2 id="research-list">Search and compare all 20</h2>
<form class="cr-filters" id="cr-filters" role="search">
<label>Search model or specifications <input type="search" id="cr-query" placeholder="Brand, model or technical feature"></label>
<label>Brand <select id="cr-brand"><option value="">All brands</option>{option}</select></label>
<label>Type <select id="cr-type"><option value="">All types</option><option value="{esc(items[0]["product_type"])}">{esc(items[0]["product_type"])}</option></select></label>
<button type="reset">Clear</button></form>
<p id="cr-status" role="status">20 researched models shown.</p>
{TV_VISUAL_CSS if category == "tvs" else ""}\n<div class="cr-grid" id="cr-grid">{''.join(card(x) for x in items)}</div>
<p id="cr-no-results" hidden>No matching model in this curated 20-product workbook.</p></section>
<section class="cr-comparison" id="cr-comparison" hidden>
<h2>Compare documented product specifications</h2><p id="cr-comparison-status" role="status"></p><div class="cr-scroll" id="cr-comparison-table"></div>
<button type="button" id="cr-clear-compare">Clear comparison</button></section>
<section class="cr-guidance"><h2>Price evidence and safety</h2>
<p>Amazon: no authorized live-price API connected; any attributed historical Amazon quotes stay out of public price promotion. Flipkart/Croma: amounts shown are dated public references, may vary by colour, seller, region or delivery address. Missing quote means unknown—not zero or unavailable.</p>
<p>Research order is the workbook's editorial order. It is not a verified Top 20 performance ranking. Performance rank continues to exclude price (0% weight), and no product is declared purchase-eligible by this page.</p></section>'''
    script=f'<script type="application/json" id="cr-payload">{serialized}</script>' \
           '<script defer src="/assets/category-research.js"></script>'
    return doc(title, "Comparison of 20 India-market " + ("televisions" if category == "tvs" else "wireless earbuds") +
               " with dated Amazon/Flipkart/Croma research links and source-grade disclosure.",
               route,body,schema(title,route,category),script)

def detail(item):
    route = model_route(item)
    cat=item["category"]
    fields = "".join(
        '<div class="cr-fact"><dt>'+esc(spec["label"])+
        '</dt><dd>'+esc(spec["value"])+'</dd></div>'
        for spec in item["specifications"])
    original_source=clean_url(item.get("source_url"))
    sources='<a target="_blank" rel="noopener noreferrer nofollow" href="'+esc(original_source)+'">Review recorded source</a>' \
       if urlsplit(original_source).scheme == "https" else "No product-specific source certified"
    merchant=''.join(
        '<tr><th scope="row">'+esc(s.title())+'</th><td>'+quote_text(item["retailers"][s],s)+
        '</td><td>'+retailer_link(item["retailers"][s],s)+'</td></tr>'
        for s in ("amazon","flipkart","croma")
    )
    body=f'''<p class="cr-crumb"><a href="/">Home</a> / <a href="/{esc(cat)}/">{esc(cat.title())}</a> / <a href="{esc(list_route(cat))}">20-model shortlist</a> / {esc(item["model"])}</p>
<article class="cr-detail">
<p class="cr-eyebrow">{esc(item["brand"])} · Research-only model</p>
<h1>{esc(item["model"])}</h1>\n{TV_VISUAL_CSS if cat == "tvs" else ""}\n{research_visual(item)}
<p class="cr-lead">Specifications and dated retailer references from the comparison workbook. Not an independently tested recommendation or real-time buyable offer.</p>
<p><b>Evidence grade:</b> {esc(item["source_grade"])} · <b>Model code:</b> {esc(item.get("model_code") or "Not established")}</p>
<h2>Documented / researched specifications</h2>
<dl class="cr-detail-facts">{fields}</dl>
<p>These fields were compiled in the workbook and have not all been individually confirmed for the exact Indian retail SKU. {sources}</p>
<section><h2>Amazon, Flipkart and Croma</h2>
<p>Only links marked <strong>Verified product</strong> have an independently matched product identity. Links marked <strong>Search model</strong> are retailer searches, not exact-product buy buttons. No current stock or shipping guarantee is made.</p>
<div class="cr-scroll"><table class="cr-compare-table"><thead><tr><th>Retailer</th><th>Dated quoted reference</th><th>Research link</th></tr></thead><tbody>{merchant}</tbody></table></div></section>
<section><h2>Why this product may be considered</h2><p>{esc(item["buyer_use_case"] or "Model-specific suitability remains under review.")}</p></section>
<section><h2>Important gaps and buyer checks</h2><p>{esc(item["evidence_caveat"])}</p>
<ul><li>Confirm the precise model suffix and screen size / earbud colour and features</li>
<li>Check manufacturer model page and Indian warranty before purchase</li>
<li>Verify current payable price, availability and delivery at the retailer</li>
<li>Do not infer performance winners from manufacturer specs or dated price differences</li></ul></section>
<p><a href="{esc(list_route(cat))}">Back to 20-model comparison</a></p></article>'''
    # All 40 workbook model pages stay accessible but noindex pending exact-
    # model/field review. Prevent scaling thin, unverified SEO pages.
    page=doc(item["model"]+" research India",item["brand"]+" "+item["model"]+
             " manufacturer, editorial and dated retailer references for India.",
             route,body,schema(item["model"],route,cat))
    return page.replace('name="robots" content="index,follow"',
                        'name="robots" content="noindex,follow"',1)

def publish_workbook_catalogue(destination):
    data=load_catalogue()
    urls=[]
    for cat in ("tvs","accessories"):
        subset=[x for x in data["records"] if x["category"]==cat]
        folder=ROUTES[cat][0]
        folderroot=destination / cat / folder
        folderroot.mkdir(parents=True,exist_ok=True)
        (folderroot/"index.html").write_text(hub(cat,subset),encoding="utf-8")
        url=SITE+list_route(cat)
        urls.append(url)
        for item in subset:
            dst=folderroot/item["id"].lower()
            dst.mkdir(parents=True,exist_ok=True)
            (dst/"index.html").write_text(detail(item),encoding="utf-8")
        # Link the list on the existing source-reviewed hub without altering
        # its curated manufacturer-only records or its static model pages.
        oldhub=destination / cat / "index.html"
        html=oldhub.read_text(encoding="utf-8")
        insertion='<section class="cr-guidance"><h2>Expanded India research list</h2>' \
            '<p>Explore <a href="'+list_route(cat)+'">the 20-model India '+ \
            ('TV' if cat=="tvs" else 'earbuds')+ \
            ' comparison</a> with dated Amazon, Flipkart and Croma listing references. ' \
            'Not current stock or verified purchase offers.</p></section>'
        if 'Expanded India research list' not in html:
            html=html.replace("</main>",insertion+"</main>",1)
            oldhub.write_text(html,encoding="utf-8")
    ns="http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("",ns)
    sitemap=destination/"sitemap.xml"
    tree=ET.parse(sitemap);root=tree.getroot()
    existing={str(e.text) for e in root.findall(f"{{{ns}}}url/{{{ns}}}loc")}
    # Only substantive list pages are indexable; not the 40 noindex detail
    # pages. They remain linked from each list and are live for visitors.
    for url in urls:
        if url in existing:raise ValueError("Duplicate collection sitemap "+url)
        node=ET.SubElement(root,f"{{{ns}}}url")
        ET.SubElement(node,f"{{{ns}}}loc").text=url
    tree.write(sitemap,encoding="utf-8",xml_declaration=True)
    print("Expanded research: 20 televisions + 20 earbuds, 40 model detail routes; no buyable offers")
    return urls

if __name__=="__main__":
    print(load_catalogue()["counts"])
