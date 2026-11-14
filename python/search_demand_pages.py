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
<script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@type": "Article", "headline": title, "description": description, "mainEntityOfPage": BASE + PATH, "dateModified": "2026-11-14", "author": {"@type": "Organization", "name": "Coupon World"}}, ensure_ascii=False).replace("<", "\\u003c")}</script></head>
<body><a class="skip" href="#content">Skip to content</a><header><nav aria-label="Main navigation"><a class="brand" href="/">CW <span>Coupon World<small>Research before you buy</small></span></a><a href="/phones/">Phone specifications</a><a href="/guides/phone-budget-guides/">Buying guides</a><a href="/">Find a phone ↗</a></nav></header>
<main id="content"><nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/guides/phone-budget-guides/">Phone guides</a> / Search demand</nav>
<article><div class="eyebrow">COUPON WORLD / EDITORIAL PRIORITY</div><h1>India smartphone search demand: what we cover</h1>
<p class="byline">By Coupon World editorial team · Updated <time datetime="2026-11-14">14 November 2026</time></p>
<p class="lead">Use search demand to decide what to research next, not to manufacture pages. This page connects a historical planning signal to the source-linked phone research already published on Coupon World.</p>
<section><h2>How this page was created</h2><p>We reviewed an archived Google Keyword Planner export, checked each model against our India-focused source catalogue, and linked only to pages that passed the current evidence review. The list is an editorial planning aid—not a promise of rankings, traffic, sales, or current search volume.</p></section>
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



# The 30-phone pilot is an editorial RESEARCH PRIORITY, not an ordered
# sales/performance ranking. Reuse the existing evidence-gated 50-page publisher
# instead of creating 20 thin, duplicate or unsupported indexable model pages.
TOP30_EN = "/seo/top-30-phone-research-india.html"
TOP30_HI = "/hi/seo/top-30-phone-research-india.html"
TOP30_FILE = ROOT / "data/top30_research_pilot_20261113.json"
TOP30_GROUPS = (
    ("EDITORIAL", "Under-₹25,000 editorial references", "₹25,000 के अंदर संपादकीय स्रोतों से चयन"),
    ("MARKET", "Models cited in India market reports", "भारतीय बाजार रिपोर्टों में उल्लिखित मॉडल"),
    ("HISTORICAL_DEMAND", "Historical search-demand research", "ऐतिहासिक सर्च-डिमांड पर आधारित रिसर्च"),
    ("CONTROL", "Comparison and consistency baselines", "तुलना और परिणाम-जाँच के संदर्भ मॉडल"),
)


def publish_top30_research_hubs(destination: Path) -> list[str]:
    """Publish two useful bilingual hubs, reusing existing canonical model pages.

    Do not index or create a new model detail page without that model passing the
    current 50-page manufacturer evidence and editorial admission checks.
    """
    from urllib.parse import urlencode
    from python.phone_research_pages import (
        EDITORIAL_MODEL_KEYS, accepted_specs, eligible, model_title, slug_for,
        specification_label, specification_value,
    )

    pilot = json.loads(TOP30_FILE.read_text(encoding="utf-8"))
    catalogue = json.loads(
        (destination / "data/mobile_research_catalogue.json").read_text(encoding="utf-8")
    )
    cards = {card["model_key"]: card for card in catalogue["model_cards"]}
    models = pilot["selected_models"]
    keys = [row["model_key"] for row in models]
    if pilot.get("document_type") != "READ_ONLY_TOP30_RESEARCH_PRIORITY_PILOT":
        raise RuntimeError("Top30 pilot manifest has unexpected publication authority")
    if len(cards) != 232 or len(keys) != 30 or len(set(keys)) != 30:
        raise RuntimeError("Top30 pilot must preserve 30 distinct existing model keys")
    if any(key not in cards for key in keys):
        raise RuntimeError("Top30 pilot contains a non-canonical research identity")
    group_counts = {group: sum(row["source_group"] == group for row in models)
                    for group, _, _ in TOP30_GROUPS}
    if group_counts != {"EDITORIAL": 10, "MARKET": 3, "HISTORICAL_DEMAND": 15, "CONTROL": 2}:
        raise RuntimeError("Top30 selection grouping changed without editorial review")

    approved = {key for key in EDITORIAL_MODEL_KEYS
                if key in cards and eligible(cards[key])}
    # A linked detail page is permitted ONLY when the existing editorial
    # publisher will generate its matching canonical route.
    if len(approved) != 50:
        raise RuntimeError("Existing manufacturer-evidence SEO gate is not ready")

    published_count = sum(key in approved for key in keys)
    styles = ('<link rel="stylesheet" href="/assets/phone-guides.css?v=20261104">'
              '<style>.cw-pilot-wrap{max-width:1100px;margin:auto;padding:1rem}'
              '.cw-pilot-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:1rem}'
              '.cw-pilot-card{border:1px solid #ccd6e0;border-radius:14px;padding:1rem;background:#fff}'
              '.cw-pilot-card h3{margin-top:.25rem}.cw-pilot-card li{margin:.4rem 0}'
              '.cw-pilot-note{background:#eef5fa;padding:1rem;border-left:4px solid #276a96}'
              '.cw-pilot-links a{margin-right:1rem}.cw-pilot-card{overflow-wrap:anywhere}</style>')
    output = []
    for hindi, path, other in (
        (False, TOP30_EN, TOP30_HI), (True, TOP30_HI, TOP30_EN)
    ):
        title = ("भारत के 30 प्राथमिकता वाले स्मार्टफोन: स्रोत-आधारित रिसर्च"
                 if hindi else
                 "30 India smartphone research priorities — sources and comparisons")
        description = ("30 मौजूदा मॉडल, दस्तावेज़ित स्पेसिफिकेशन, प्रमाण की सीमाएँ और तुलना के लिंक। यह बिक्री या परफॉर्मेंस रैंकिंग नहीं है।"
                       if hindi else
                       "Explore 30 selected Indian smartphone research models, original specification sources, known gaps and exact-variant comparison. Not a top-selling or performance ranking.")
        group_sections = []
        for group, en_heading, hi_heading in TOP30_GROUPS:
            parts = []
            for row in [x for x in models if x["source_group"] == group]:
                card = cards[row["model_key"]]
                name = model_title(card)
                specs = accepted_specs(card)
                research_url = "/?" + urlencode({"q": name}) + "#mobileResearchSearch"
                exact_page = ("/hi/phones/" if hindi else "/phones/") + slug_for(card) + "/"
                is_published = row["model_key"] in approved
                target = exact_page if is_published else research_url
                status = (("निर्माता-स्रोत वाला विस्तृत पेज" if hindi else "Source-linked model page")
                          if is_published else
                          ("मॉडल का रिसर्च रिकॉर्ड; अलग SEO पेज अभी स्वीकृत नहीं" if hindi
                           else "Research record; standalone SEO page not yet approved"))
                facts = []
                for key, item in specs[:3]:
                    label = specification_label(key, item, hindi=hindi)
                    value = specification_value(key, item)
                    source = str(item["source_url"])
                    # The source was previously admitted by the common
                    # specification evidence adapter; the URL is not a claim
                    # of independent device laboratory testing.
                    facts.append(
                        '<li>' + esc(label) + ': <strong>' + esc(value[:160]) +
                        '</strong> · <a href="' + esc(source) +
                        '" rel="noopener noreferrer"> ' +
                        ("स्रोत" if hindi else "source") + '</a></li>'
                    )
                if not facts:
                    facts.append('<li>' + ("इस रिकॉर्ड में अभी पर्याप्त फ़ील्ड-स्रोत नहीं हैं।"
                                          if hindi else
                                          "Sufficient source-linked technical fields are still pending.") + '</li>')
                fact_note = ("दस्तावेज़ित जानकारी, वास्तविक दुनिया की परफॉर्मेंस रैंकिंग नहीं।"
                             if hindi else
                             "Documented facts, not a measured real-world performance ranking.")
                parts.append(
                    '<article class="cw-pilot-card" id="phone-' + esc(slug_for(card)) + '">' +
                    '<h3>' + esc(name) + '</h3><p>' + esc(status) + '</p>' +
                    '<ul>' + "".join(facts) + '</ul><p><small>' + esc(fact_note) +
                    '</small></p><p class="cw-pilot-links"><a href="' + esc(target) + '">' +
                    ("स्रोत/मॉडल देखें" if hindi else "View documented model / research") +
                    '</a> <a href="' + esc(research_url) + '">' +
                    ("रिसर्च टूल में खोजें" if hindi else "Open research search") +
                    '</a></p></article>'
                )
            heading = hi_heading if hindi else en_heading
            group_sections.append(
                '<section><h2>' + esc(heading) + '</h2><div class="cw-pilot-grid">' +
                "".join(parts) + '</div></section>'
            )

        explainer = (
            '<p>यह 30 मॉडल सिर्फ शोध की प्राथमिकता हैं, भारत के 30 सबसे अधिक बिकने वाले या सर्वश्रेष्ठ फोन नहीं। '
            'चयन में 6 नवंबर की संपादकीय सूची, 2026 की Q2/Q3 बाजार रिपोर्टों और सितंबर 2025–अगस्त 2026 के ऐतिहासिक '
            'Keyword Planner डेटा का उपयोग हुआ है। दोनों तिमाही रिपोर्टों को एक संयुक्त बिक्री रैंकिंग नहीं बनाया गया।</p>'
            '<p>निर्माता की स्पेसिफिकेशन वास्तविक बैटरी बैकअप, कैमरा गुणवत्ता या गेमिंग FPS नहीं मापती। '
            'भारत के RAM/स्टोरेज वेरिएंट, स्रोत की जाँच-तिथि, परीक्षण पद्धति और कीमत/स्टॉक अलग से जाँचें। '
            'जिन मॉडलों पर पर्याप्त तकनीकी प्रमाण नहीं है, उनके लिए गलत या पतला SEO पेज बनाने के बजाय रिसर्च टूल दिया गया है।</p>'
            if hindi else
            '<p>These 30 phones are a research worklist, NOT India’s current top 30 by sales '
            'or best-performance winners. We combined a November editorial coverage audit, Q2/Q3 2026 '
            'market references and historical Google Ads planning signals (September 2025–August 2026). '
            'The market reports do not establish a combined top-30 model sales ranking.</p>'
            '<p>Manufacturer specifications describe declared hardware, not measured battery endurance, '
            'camera quality or sustained game frame rate. Exact India RAM/storage, testing protocols, '
            'price and current stock need separate verification. Where a model lacks admitted evidence, '
            'we provide research access rather than publishing a thin or misleading model SEO page.</p>'
        )
        heading = ("30 स्मार्टफोन: साक्ष्य और तुलना से शुरुआत"
                   if hindi else "30 smartphones to research with evidence")
        links = (
            '<p><a href="/hi/phones/">निर्माता-स्रोत वाले मॉडल</a> · '
            '<a href="/hi/phones/under-25000/">₹25,000 रिसर्च गाइड</a> · '
            '<a href="/hi/compare/">फोन की तुलना</a> · '
            '<a href="/hi/guides/phone-budget-guides/">खरीद गाइड</a></p>'
            if hindi else
            '<p><a href="/phones/">Source-linked model hub</a> · '
            '<a href="/phones/under-25000/">Under-₹25,000 research</a> · '
            '<a href="/compare/">Compare phones</a> · '
            '<a href="/guides/phone-budget-guides/">Buying guides</a></p>'
        )
        note = (f'{published_count} मॉडल पर मौजूदा स्वीकृत स्रोत-पेज हैं; शेष के लिए रिसर्च टूल खोलें।'
                if hindi else
                f'{published_count} models already have evidence-approved canonical pages; the remaining models link to research rather than unsupported SEO detail URLs.')
        schema = {
            "@context": "https://schema.org", "@type": "CollectionPage", "name": title,
            "url": BASE + path, "inLanguage": "hi-IN" if hindi else "en-IN",
            "description": description,
            "isPartOf": {"@type": "WebSite", "name": "Coupon World", "url": BASE + "/"}
        }
        jsonld = json.dumps(schema, ensure_ascii=False).replace("<", "\\u003c")
        body = (
            '<!doctype html><html lang="' + ("hi-IN" if hindi else "en-IN") +
            '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
            '<title>' + esc(title) + ' | Coupon World</title>' +
            '<meta name="description" content="' + esc(description) + '">' +
            '<meta name="robots" content="index,follow,max-image-preview:large">' +
            '<link rel="canonical" href="' + esc(BASE + path) + '">' +
            '<link rel="alternate" hreflang="en-IN" href="' + esc(BASE + TOP30_EN) + '">' +
            '<link rel="alternate" hreflang="hi-IN" href="' + esc(BASE + TOP30_HI) + '">' +
            '<meta property="og:title" content="' + esc(title) + '">' +
            '<meta property="og:description" content="' + esc(description) + '">' +
            '<meta property="og:url" content="' + esc(BASE + path) + '">' +
            styles + '<script type="application/ld+json">' + jsonld + '</script></head><body>' +
            '<a class="skip" href="#main">Skip to content</a>' +
            '<header><nav aria-label="Main navigation"><a href="/">Coupon World</a> · ' +
            '<a href="' + esc(other) + '">' + ("English" if hindi else "हिंदी") +
            '</a> · <a href="/phones/">Phone specifications</a></nav></header>' +
            '<main id="main" class="cw-pilot-wrap"><nav class="crumbs" aria-label="Breadcrumb">' +
            '<a href="/">Home</a> / <a href="/phones/">Phones</a> / ' +
            ("30 प्राथमिकता मॉडल" if hindi else "30 research priorities") + '</nav>' +
            '<article><div class="eyebrow">COUPON WORLD / EVIDENCE FIRST</div><h1>' +
            esc(heading) + '</h1><p class="byline">' +
            ("Coupon World संपादकीय टीम · अपडेट: 14 नवंबर 2026" if hindi else
             "By Coupon World editorial team · Updated 14 November 2026") +
            '</p><p class="lead">' + esc(description) +
            '</p><aside class="cw-pilot-note"><strong>' + esc(note) + '</strong></aside>' +
            '<section><h2>' + ("यह चयन कैसे हुआ" if hindi else "How this shortlist was selected") +
            '</h2>' + explainer +
            '<p><a href="https://counterpointresearch.com/en/insights/top-5-smartphone-model-share-8-countries">Counterpoint Q2 2026</a> · ' +
            '<a href="https://omdia.tech.informa.com/pr/2026/oct/indias-smartphone-shipments-fell-26percent-to-a-decade-low-third-quarter-level-despite-festive-season">Omdia Q3 2026</a></p>' +
            '</section>' + "".join(group_sections) +
            '<section><h2>' + ("अगला सही कदम" if hindi else "Next research step") +
            '</h2><p>' +
            ("अपनी जरूरत और बजट की सीमा लिखकर सही मॉडल चुनें। खरीदने से पहले विक्रेता की कीमत, RAM/स्टोरेज और उपलब्धता जाँचें।"
             if hindi else
             "Compare the documented facts for your own needs, then check exact RAM/storage, current availability and final prices at the retailer.") +
            '</p>' + links + '</section></article></main>' +
            '<footer class="cw-pilot-wrap">' +
            ("संपादकीय शोध; न कोई नया परफॉर्मेंस रैंक, न लाइव कीमत या स्टॉक का दावा।"
             if hindi else
             "Editorial research only. No current price, stock, measured-performance winner or independently certified top-30 sales rank.") +
            '</footer></body></html>'
        )
        target = destination / path.lstrip("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        output.append(BASE + path)

    # One canonical per language; only substantive hubs enter the sitemap.
    ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", ns)
    sitemap = destination / "sitemap.xml"
    tree = ET.parse(sitemap)
    root = tree.getroot()
    existing = {node.text for node in root.findall(f"{{{ns}}}url/{{{ns}}}loc")}
    for url in output:
        if url in existing:
            raise RuntimeError("Duplicate top30 canonical URL: " + url)
        node = ET.SubElement(root, f"{{{ns}}}url")
        ET.SubElement(node, f"{{{ns}}}loc").text = url
        ET.SubElement(node, f"{{{ns}}}lastmod").text = pilot["created_date"]
    tree.write(sitemap, encoding="utf-8", xml_declaration=True)
    print(f"Top30 bilingual research hubs: 2; selected: 30; existing model pages: {published_count}")
    return output
