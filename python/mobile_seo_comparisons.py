"""Editorial, source-backed, bilingual 50-phone-comparison publication.

No new recommendation engine. Exact identity, source-linked facts, and
indexable URL admission are inherited from the reviewed phone editorial layer.
The 2025-2026 model keyword history informs topic selection, not claimed query
volume, real-time trends, offers, or model performance results.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from xml.etree import ElementTree as ET

from python.affiliate_links import AMAZON_TAG
from python.phone_research_pages import (
    EDITORIAL_MODEL_KEYS, SITE, accepted_specs, eligible, model_title, slug_for,
    value_text,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/mobile_seo_comparisons_20261106.json"
EN = "/compare/"
HI = "/hi/compare/"
MIN_FIELDS = 8
MAX_FIELDS = 28
TOPIC_FIELDS = ("chipset", "processor", "gpu", "camera", "battery", "charg",
                "display", "screen", "refresh", "software", "system", "support",
                "storage", "ram", "network", "ip_", "durability", "weight", "resolution")


def esc(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def path_for(left: dict, right: dict, hi: bool = False) -> str:
    return (HI if hi else EN) + slug_for(left) + "-vs-" + slug_for(right) + "/"


def topic_label(text: str, hi: bool) -> str:
    if not hi:
        return text
    mapping = {
        "Chipset": "चिपसेट", "GPU": "GPU", "Display": "स्क्रीन",
        "Battery": "बैटरी", "Charging": "चार्जिंग", "Camera": "कैमरा",
        "Network": "नेटवर्क", "Storage": "स्टोरेज", "Security": "सुरक्षा",
    }
    for english, hindi in mapping.items():
        if english.lower() in text.lower():
            return text.replace(english, hindi)
    return text


def spec_items(card: dict) -> dict[str, dict]:
    return {k: item for k, item in accepted_specs(card)}


def source_cell(item: dict | None, hi: bool) -> str:
    if item is None:
        return '<span class="unknown">' + (
            "इस मॉडल का मान स्रोत में नहीं मिला" if hi else "Not documented for this model"
        ) + "</span>"
    value = value_text(item.get("value"))
    url = str(item["source_url"])
    return (f'<strong>{esc(value)}</strong> '
            f'<a class="source" href="{esc(url)}" target="_blank" rel="nofollow noopener noreferrer">'
            + ("स्रोत" if hi else "Source") + "</a>")


def source_table(left: dict, right: dict, hi: bool) -> tuple[str, int, int]:
    a, b = spec_items(left), spec_items(right)
    common = [k for k in a if k in b]
    # Prefer comparable keys, then coverage of major buying-decision dimensions.
    keys = sorted(set(a) | set(b), key=lambda k: (
        0 if k in common else 1,
        0 if any(word in k.lower() for word in TOPIC_FIELDS) else 1,
        str((a.get(k) or b.get(k) or {}).get("label") or k).lower()
    ))[:MAX_FIELDS]
    headings = ("तकनीकी विशेषता", "प्रथम फोन", "दूसरा फोन") if hi else (
        "Specification", "First phone", "Second phone")
    rows = []
    differences = 0
    for key in keys:
        ia, ib = a.get(key), b.get(key)
        if ia and ib and value_text(ia.get("value")).casefold() != value_text(ib.get("value")).casefold():
            differences += 1
        label = (ia or ib or {}).get("label") or key.replace("_", " ").title()
        rows.append(f"<tr><th scope=\"row\">{esc(topic_label(str(label), hi))}</th>"
                    f"<td>{source_cell(ia, hi)}</td><td>{source_cell(ib, hi)}</td></tr>")
    table = ("<div class=\"table-wrap\"><table><thead><tr>"
             + "".join("<th scope=\"col\">" + esc(x) + "</th>" for x in headings)
             + "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>")
    return table, len(common), differences


def retailer_links(card: dict, hi: bool) -> str:
    name = model_title(card)
    amazon = "https://www.amazon.in/s?" + urlencode({"k": name, "tag": AMAZON_TAG})
    flipkart = "https://www.flipkart.com/search?" + urlencode({"q": name})
    # Croma has no verified exact listing for these models. Browse category only.
    croma = "https://www.croma.com/"
    options = (
        (amazon, "Amazon पर खोजें (affiliate)" if hi else "Search Amazon (affiliate)", True),
        (flipkart, "Flipkart पर खोजें" if hi else "Search Flipkart", False),
        (croma, "Croma ब्राउज़ करें" if hi else "Browse Croma", False),
    )
    links = []
    for url, label, sponsored in options:
        host = urlsplit(url).hostname
        if host not in {"www.amazon.in", "www.flipkart.com", "www.croma.com"}:
            raise ValueError("Unapproved retailer domain in comparison")
        rel = "sponsored nofollow noopener noreferrer" if sponsored else "nofollow noopener noreferrer"
        links.append(f'<a href="{esc(url)}" rel="{rel}" target="_blank">{esc(label)}</a>')
    return '<div class="retail">' + " ".join(links) + "</div>"


def document(title: str, description: str, path: str, body: str, hi: bool, reviewed: str,
             breadcrumb: list[dict]) -> str:
    counterpart = (EN + path[len(HI):]) if hi else (HI + path[len(EN):])
    canonical = SITE + path
    language = "hi-IN" if hi else "en-IN"
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebPage", "name": title, "description": description, "url": canonical,
             "dateModified": reviewed, "isPartOf": {"@type": "WebSite", "name": "Coupon World", "url": SITE + "/"}},
            {"@type": "BreadcrumbList", "itemListElement": breadcrumb},
        ],
    }
    structured = json.dumps(ld, ensure_ascii=False).replace("<", "\\u003c")
    return (f'<!doctype html><html lang="{language}"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(title)} | Coupon World</title>'
            f'<meta name="description" content="{esc(description)}">'
            '<meta name="robots" content="index,follow">'
            f'<link rel="canonical" href="{esc(canonical)}">'
            f'<link rel="alternate" hreflang="en-IN" href="{esc(SITE + (counterpart if hi else path))}">'
            f'<link rel="alternate" hreflang="hi-IN" href="{esc(SITE + (path if hi else counterpart))}">'
            '<meta property="og:type" content="website">'
            f'<meta property="og:title" content="{esc(title)}">'
            f'<meta property="og:description" content="{esc(description)}">'
            f'<meta property="og:url" content="{esc(canonical)}">'
            '<link rel="stylesheet" href="/assets/phone-guides.css?v=20261104">'
            '<link rel="stylesheet" href="/assets/compare-seo.css?v=20261106">'
            '<script async src="https://www.googletagmanager.com/gtag/js?id=G-921WL91ZGW"></script>'
            '<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag("js",new Date());gtag("config","G-921WL91ZGW");</script>'
            '<script defer src="/assets/discovery-analytics.js?v=20261104"></script>'
            f'<script type="application/ld+json">{structured}</script></head><body>'
            '<a class="skip" href="#main">Skip to content</a>'
            '<header class="comparison-nav"><a href="/">Coupon World</a>'
            f'<a href="{HI if hi else EN}">{"सभी तुलनाएँ" if hi else "All comparisons"}</a>'
            f'<a href="{counterpart}" lang="{"en-IN" if hi else "hi-IN"}">{"English" if hi else "हिंदी"}</a>'
            '<a href="/phones/">Phone specifications</a></header>'
            f'<main id="main" class="comparison-page">{body}</main>'
            '<footer class="comparison-footer"><a href="/guides/about-coupon-world/">About our evidence and affiliate disclosure</a>'
            '<p>As an Amazon Associate I earn from qualifying purchases. Search links do not certify a matching product, current price, stock, delivery, or commission.</p>'
            '</footer></body></html>')


def breadcrumb(title: str, path: str, hi: bool) -> list[dict]:
    hub = HI if hi else EN
    return [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "Phone comparisons", "item": SITE + hub},
        {"@type": "ListItem", "position": 3, "name": title, "item": SITE + path},
    ]


def render_pair(item: dict, left: dict, right: dict, hi: bool, related: list[tuple[dict,dict]]) -> str:
    a, b = model_title(left), model_title(right)
    path = path_for(left, right, hi)
    title = (f"{a} vs {b}: स्पेसिफिकेशन और निर्णय गाइड" if hi
             else f"{a} vs {b}: Specs, Evidence & Buying Decision")
    desc = (f"{a} और {b} की निर्माता-स्रोत वाली तकनीकी तुलना, प्रमाण की सीमाएँ और खरीद से पहले जाँच।"
            if hi else f"{a} compared with {b}: source-linked specifications, honest evidence gaps and a practical India buying checklist.")
    facts, common, differences = source_table(left, right, hi)
    count_a, count_b = len(spec_items(left)), len(spec_items(right))
    focus = esc(item["intent_hi"] if hi else item["intent_en"])
    intro = ("यह तुलना खोजे जाने वाले मॉडल नामों और अलग खरीद जरूरतों से चुनी गई है। यह दोनों फोन का प्रत्यक्ष परीक्षण नहीं है।"
             if hi else "This comparison is chosen from buyer-relevant model searches. It is not a hands-on review or a test conducted under a shared laboratory protocol.")
    contrast = (f"दोनों के लिए {common} एक ही नाम वाले तकनीकी फ़ील्ड हैं; उनमें {differences} दर्ज मान अलग हैं। "
                "अलग मान का अर्थ अपने-आप बेहतर फोन नहीं है।" if hi else
                f"The saved source records share {common} specification field names; {differences} of their recorded values differ. "
                "A different value is not automatically a better real-world outcome.")
    cross_checks = [
        ("कैमरा और वीडियो", "लेंस, OIS और वीडियो मोड के निर्माता विवरण देखें; असली फोटो गुणवत्ता के लिए एक समान स्वतंत्र नमूने आवश्यक हैं.") if hi else
        ("Camera and video", "Compare lens types, OIS and supported video modes. Camera quality still needs comparable independent photographs and footage."),
        ("बैटरी और चार्जिंग", "mAh और घोषित वाट क्षमता को वास्तविक स्क्रीन-ऑन समय या चार्जिंग समय न मानें.") if hi else
        ("Battery and charging", "Advertised mAh and charging watts are not measured endurance or charging-time results."),
        ("प्रदर्शन और गेमिंग", "प्रोसेसर और GPU के नाम सिर्फ हार्डवेयर पहचानते हैं; FPS और तापमान की तुलना समान सेटिंग पर करें.") if hi else
        ("Performance and gaming", "A chipset or GPU model is not a controlled FPS or thermal-throttling benchmark; look for tests with the same settings."),
        ("भारत में सही वेरिएंट", "RAM, स्टोरेज, 4G/5G बैंड, वारंटी और सॉफ़्टवेयर अपडेट निर्माता के सटीक भारतीय मॉडल से मिलाएँ.") if hi else
        ("Exact India variant", "Check RAM, storage, India network bands, warranty and software policy against the actual manufacturer/SKU record."),
    ]
    reasoning = "".join(f"<li><strong>{esc(head)}:</strong> {esc(detail)}</li>" for head, detail in cross_checks)
    related_html = "".join(
        f'<li><a href="{esc(path_for(x,y,hi))}">{esc(model_title(x))} vs {esc(model_title(y))}</a></li>'
        for x,y in related
    )
    retail = (
        f'<div class="retailer-card"><h3>{esc(a)}</h3>{retailer_links(left,hi)}</div>'
        f'<div class="retailer-card"><h3>{esc(b)}</h3>{retailer_links(right,hi)}</div>'
    )
    intro_note = ("हर फीचर का मूल स्रोत साथ दिया है। जहाँ जानकारी नहीं मिली, वहाँ अनुमान नहीं लगाया गया।"
                  if hi else "Every recorded value points to its source. Missing data is shown as unknown, not silently inferred from a similar model.")
    warning = ("इन पन्नों की संपादकीय तुलना साइट की प्रमाण-आधारित अंतिम performance ranking नहीं है। "
               "कीमत का performance score में भार 0% है; आज की कीमत या स्टॉक का दावा नहीं किया गया है."
               if hi else "This editorial guide does not change Coupon World's approved evidence-gated performance ranking. "
               "Price has 0% performance-score weight and no current price, stock or exact buyability is certified.")
    research_date = ("स्रोत-अध्ययन की संपादकीय समीक्षा: " if hi else "Editorial comparison review: ") + "6 November 2026"
    buy_note = ("नीचे दिए गए लिंक खोज/ब्राउज़ पेज हैं, न कि सटीक वेरिएंट की सत्यापित खरीद लिस्टिंग। "
                "Croma पर यह मॉडल उपलब्ध न भी हो सकता है; बैंक ऑफर और एक्सचेंज शर्तें अलग जाँचें."
                if hi else "These destinations are retailer searches or category browsing, not verified exact-product purchase offers. "
                "Croma may not carry the device. Verify final price, seller, exchange/bank conditions and delivery yourself.")
    body = (
        f'<nav class="crumbs"><a href="/">Home</a> / <a href="{HI if hi else EN}">{"फोन तुलना" if hi else "Phone comparisons"}</a></nav>'
        f'<article><p class="eyebrow">{"भारत · स्रोत-आधारित मोबाइल तुलना" if hi else "INDIA · MANUFACTURER-SOURCED PHONE COMPARISON"}</p>'
        f'<h1>{esc(title)}</h1><p class="lead">{focus}</p><p>{esc(intro)}</p>'
        f'<p class="research-date">{esc(research_date)}</p>'
        f'<aside class="notice"><strong>{"इस गाइड की सीमा" if hi else "Important research boundary"}</strong><p>{esc(warning)}</p></aside>'
        f'<section><h2>{"इन दोनों की तुलना कैसे करें?" if hi else "What makes this decision different?"}</h2>'
        f'<p>{focus} {esc(intro_note)}</p><p>{esc(contrast)}</p></section>'
        f'<section><h2>{"स्रोत-समर्थित आमने-सामने विवरण" if hi else "Source-linked side-by-side specifications"}</h2>'
        f'<p>{esc(a)}: {count_a} {"सत्यापित स्रोत-फ़ील्ड" if hi else "sourced fields"}; '
        f'{esc(b)}: {count_b} {"सत्यापित स्रोत-फ़ील्ड" if hi else "sourced fields"}. '
        f'{"कोई खाली मान भरा नहीं गया है।" if hi else "Unknown specifications are not guessed."}</p>{facts}</section>'
        f'<section><h2>{"खरीद के फैसले में क्या महत्वपूर्ण है?" if hi else "How to interpret these differences"}</h2>'
        f'<ol>{reasoning}</ol><p>{esc(warning)}</p></section>'
        f'<section><h2>{"असली मॉडल पेज और प्रमाण" if hi else "Check the original model research"}</h2>'
        f'<p><a href="/phones/{slug_for(left)}/">{esc(a)} — {"मूल स्पेसिफिकेशन" if hi else "full sourced specifications"}</a></p>'
        f'<p><a href="/phones/{slug_for(right)}/">{esc(b)} — {"मूल स्पेसिफिकेशन" if hi else "full sourced specifications"}</a></p>'
        f'<p>{esc(intro_note)}</p></section>'
        f'<section><h2>{"विक्रेता पर वास्तविक जानकारी जाँचें" if hi else "Verify the actual retailer listing"}</h2>'
        f'<p>{esc(buy_note)}</p><div class="retailer-grid">{retail}</div></section>'
        f'<section><h2>{"अगली प्रासंगिक तुलनाएँ" if hi else "Other useful comparisons"}</h2>'
        f'<ul>{related_html}</ul></section>'
        f'<section><h2>{"सामान्य सवाल" if hi else "Frequently asked buyer questions"}</h2>'
        f'<h3>{"कौन सा फोन बेहतर कैमरा देता है?" if hi else "Which phone actually takes better photos?"}</h3>'
        f'<p>{"केवल सेंसर संख्या से फैसला संभव नहीं। दोनों के तुलनीय स्वतंत्र फोटो और वीडियो टेस्ट चाहिए।" if hi else "Manufacturer sensor specifications alone do not establish a camera winner. Compare independent samples under consistent lighting and framing."}</p>'
        f'<h3>{"कौन सा फोन तेज है और गेमिंग में बेहतर है?" if hi else "Which phone performs better in sustained gaming?"}</h3>'
        f'<p>{"दोनों के समान गेम सेटिंग, फ्रेमरेट और तापमान के स्वतंत्र परीक्षण के बिना विजेता घोषित नहीं किया जा सकता।" if hi else "A sustained-gaming winner requires the same game/settings and independently measured FPS, temperatures and power behaviour."}</p>'
        f'<h3>{"आज खरीदना उचित है?" if hi else "Is either phone the better deal today?"}</h3>'
        f'<p>{"वास्तविक भारत वेरिएंट, स्टॉक और अंतिम चेकआउट कीमत की यहाँ पुष्टि नहीं है। कीमत केवल बजट फ़िल्टर के लिए है।" if hi else "Current stock and checkout totals are unverified. Dated price references can filter budgets but never change the approved performance score."}</p>'
        '</section></article>'
    )
    return document(title, desc, path, body, hi, "2026-11-06", breadcrumb(title, path, hi))


def render_hub(entries: list[tuple[dict, dict, dict]], hi: bool) -> str:
    path = HI if hi else EN
    title = ("50 प्रमाण-आधारित मोबाइल तुलना: भारत" if hi
             else "50 Evidence-Based Phone Comparisons for India")
    description = ("50 मोबाइल जोड़ियों की स्रोत-सहित तकनीकी तुलना: कैमरा, बैटरी, स्क्रीन और सॉफ़्टवेयर पर समझदारी से चुनाव।"
                   if hi else "50 curated phone comparisons for India with manufacturer-linked specifications, evidence gaps and honest buying decisions.")
    list_html = []
    for item, a, b in entries:
        focus = item["intent_hi"] if hi else item["intent_en"]
        p = path_for(a,b,hi)
        list_html.append(f'<li><a href="{p}"><strong>{esc(model_title(a))} vs {esc(model_title(b))}</strong></a>'
                         f'<p>{esc(focus)}</p></li>')
    note = ("ये 50 पन्ने सबसे अधिक खोजे गए 50 की प्रमाणित रैंकिंग नहीं हैं। "
            "ऐतिहासिक Google Keyword Planner model-level डेटा ने विषय चुनने में मदद की; जोड़ी-विशेष की वर्तमान खोज संख्या उपलब्ध नहीं है।"
            if hi else "These are 50 curated buyer comparisons, not a claimed ranking of the 50 most-searched queries. "
            "Historical Google Keyword Planner model-level metrics informed topic selection; current search volume for individual comparison queries is not established.")
    body = (
        f'<article><p class="eyebrow">{"भारत · मोबाइल शोध" if hi else "INDIA · PHONE RESEARCH"}</p>'
        f'<h1>{esc(title)}</h1><p class="lead">{esc(description)}</p>'
        f'<aside class="notice"><strong>{"कीवर्ड डेटा की सीमा" if hi else "Keyword evidence and limitations"}</strong><p>{esc(note)}</p></aside>'
        f'<p>{"सभी तुलना पन्नों में निर्माता-स्रोत, अनुपलब्ध जानकारी और खरीद से पहले के प्रश्न स्पष्ट हैं।" if hi else "All comparison pages link their factual fields to sources, disclose missing evidence and avoid invented performance wins or live offers."}</p>'
        f'<ol class="comparison-list">{"".join(list_html)}</ol></article>'
    )
    return document(title, description, path, body, hi, "2026-11-06", breadcrumb(title, path, hi))


def _write(destination: Path, path: str, html_body: str) -> None:
    target = destination / path.lstrip("/") / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html_body, encoding="utf-8")


def _add_hub_link(destination: Path, path: str, hi: bool = False) -> None:
    file = destination / path.lstrip("/") / "index.html" if path.endswith("/") else destination / path.lstrip("/")
    if not file.is_file():
        raise FileNotFoundError(f"Comparison navigation target missing: {file}")
    content = file.read_text(encoding="utf-8")
    href = HI if hi else EN
    if 'href="' + href + '"' in content:
        return
    if "</main>" not in content:
        raise ValueError(f"Cannot place comparison navigation in {path}")
    label = "50 स्रोत-सहित फोन तुलनाएँ" if hi else "50 manufacturer-sourced phone comparisons"
    section = '<section class="comparison-discovery"><h2><a href="' + href + '">' + label + '</a></h2><p>' + (
        "भारत के लोकप्रिय मोबाइल मॉडल की जानकारी, अंतर और शोध सीमाएँ देखें।" if hi
        else "Explore exact model-to-model specifications, buyer tradeoffs and openly documented evidence gaps."
    ) + '</p></section>'
    file.write_text(content.replace("</main>", section + "</main>", 1), encoding="utf-8")


def _sitemap(destination: Path, routes: list[str]) -> None:
    ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", ns)
    filename = destination / "sitemap.xml"
    tree = ET.parse(filename)
    root = tree.getroot()
    old = {node.text for node in root.findall("{" + ns + "}url/{" + ns + "}loc")}
    for route in routes:
        url = SITE + route
        if url in old:
            raise ValueError("Duplicate comparison sitemap URL: " + url)
        node = ET.SubElement(root, "{" + ns + "}url")
        ET.SubElement(node, "{" + ns + "}loc").text = url
        ET.SubElement(node, "{" + ns + "}lastmod").text = "2026-11-06"
        old.add(url)
    tree.write(filename, encoding="utf-8", xml_declaration=True)


def publish_comparisons(destination: Path) -> list[str]:
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    pairs = payload.get("pairs") or []
    if payload.get("schema_version") != 1 or len(pairs) != 50:
        raise ValueError("Only the 50 reviewed comparison briefs can be published")
    catalogue = json.loads((destination / "data/mobile_research_catalogue.json").read_text(encoding="utf-8"))
    cards = {item["model_key"]: item for item in catalogue["model_cards"]}
    if len(cards) != 232:
        raise ValueError("Do not replace the 232 primary research identities")
    allowed = set(EDITORIAL_MODEL_KEYS)
    seen = set()
    entries = []
    for n, row in enumerate(pairs, 1):
        left_key, right_key = row["left"], row["right"]
        if row.get("id") != n or left_key == right_key or {left_key, right_key} - allowed:
            raise ValueError(f"Unreviewed model or incorrect comparison index: {n}")
        identity = tuple(sorted((left_key, right_key)))
        if identity in seen:
            raise ValueError(f"Duplicate reverse-order comparison: {identity}")
        seen.add(identity)
        a, b = cards[left_key], cards[right_key]
        if not eligible(a) or not eligible(b):
            raise ValueError(f"Comparison has insufficient reviewed manufacturer evidence: {identity}")
        if len(spec_items(a)) < MIN_FIELDS or len(spec_items(b)) < MIN_FIELDS:
            raise ValueError(f"Comparison has fewer than eight source-linked fields: {identity}")
        if len(row.get("intent_en", "").split()) < 10 or len(row.get("intent_hi", "")) < 45:
            raise ValueError("Each comparison needs a genuinely distinct editorial buying angle")
        entries.append((row, a, b))
    routes = []
    for hi in (False, True):
        for n, (row, a, b) in enumerate(entries):
            links = [(x,y) for _,x,y in entries if (x["model_key"] in {a["model_key"], b["model_key"]}
                                                  or y["model_key"] in {a["model_key"], b["model_key"]})
                     and (x["model_key"], y["model_key"]) != (a["model_key"], b["model_key"])][:4]
            if not links:
                links = [(x,y) for _,x,y in entries[:4] if (x["model_key"],y["model_key"])!=(a["model_key"],b["model_key"])]
            path = path_for(a,b,hi)
            _write(destination,path,render_pair(row,a,b,hi,links))
            routes.append(path)
        hub = HI if hi else EN
        _write(destination,hub,render_hub(entries,hi))
        routes.append(hub)
    for link, lang in (("/index.html", False), ("/phones/", False), ("/hi/phones/", True)):
        _add_hub_link(destination,link,lang)
    _sitemap(destination,routes)
    print(f"Evidence comparison release: 50 English + 50 Hindi comparison pages, 2 hubs; {len(routes)} indexed routes")
    return routes
