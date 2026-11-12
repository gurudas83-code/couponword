"""Publish a small, useful guide hierarchy instead of keyword permutations.

Google does not certify sites through these checks. The contract removes the
identified low-value batches, preserves factual research, and validates actual
URLs, canonicals, disclosure and sitemap membership before publication.
"""
from __future__ import annotations

import html
import json
import re
import shutil
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
from xml.etree import ElementTree as ET

from python.page_feedback import markup as feedback_markup

ROOT=Path(__file__).resolve().parents[1]
SITE='https://coupon-world.in'
RETIRED=ROOT/'data/retired_public_routes_20261106.json'
RETAINED_HUBS=('/compare/','/hi/compare/','/phones/under-25000/','/hi/phones/under-25000/')
POLICY_SOURCES={
 'Helpful content':'https://developers.google.com/search/docs/fundamentals/creating-helpful-content',
 'Spam policies':'https://developers.google.com/search/docs/essentials/spam-policies',
 'AI-assisted content':'https://developers.google.com/search/docs/fundamentals/using-gen-ai-content',
 'Reviews':'https://developers.google.com/search/docs/specialty/ecommerce/write-high-quality-reviews',
 'Removed URLs':'https://developers.google.com/crawling/docs/troubleshooting/http-status-codes',
 'Structured data':'https://developers.google.com/search/docs/appearance/structured-data/sd-policies',
}

def esc(v):return html.escape(str(v),quote=True)

def route_file(root,route):
    return root/route.lstrip('/')/('index.html' if route.endswith('/') else '')

def doc(path,title,body,hi=False,index=True):
    alternate=path[3:] if hi else '/hi'+path
    schema={'@context':'https://schema.org','@type':'WebPage','name':title,'url':SITE+path,'inLanguage':'hi-IN' if hi else 'en-IN'}
    feedback=feedback_markup('budget_guide' if 'under-25000' in path else 'comparison_guide', hi)
    return f'''<!doctype html><html lang="{'hi-IN' if hi else 'en-IN'}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} | Coupon World</title><meta name="description" content="{esc(title)}: practical decisions, source-linked facts and clearly explained evidence limits."><meta name="robots" content="{'index,follow' if index else 'noindex,follow'}"><link rel="canonical" href="{SITE+path}"><link rel="alternate" hreflang="{'hi-IN' if hi else 'en-IN'}" href="{SITE+path}"><link rel="alternate" hreflang="{'en-IN' if hi else 'hi-IN'}" href="{SITE+alternate}"><link rel="stylesheet" href="/assets/phone-guides.css"><link rel="stylesheet" href="/assets/page-feedback.css?v=20261112"><style>main{{max-width:960px;margin:2rem auto;padding:1rem}}nav{{display:flex;flex-wrap:wrap;gap:1rem;padding:1rem}}table{{border-collapse:collapse;width:100%}}td,th{{text-align:left;border-bottom:1px solid #d8dfd6;padding:.7rem;vertical-align:top}}.table-wrap{{overflow:auto}}a{{overflow-wrap:anywhere}}h1{{font-size:clamp(1.8rem,4vw,3rem)}}footer{{max-width:960px;margin:2rem auto;padding:1rem}}</style><script async src="https://www.googletagmanager.com/gtag/js?id=G-921WL91ZGW"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag("js",new Date());gtag("config","G-921WL91ZGW");</script><script defer src="/assets/discovery-analytics.js?v=20261104"></script><script type="application/ld+json">{json.dumps(schema,ensure_ascii=False).replace('<','\\u003c')}</script></head><body><a class="skip" href="#content">Skip to content</a><header><nav><a href="/">Coupon World</a><a href="/guides/phone-budget-guides/">Buying guides</a><a href="/phones/">Phone specifications</a><a href="{alternate}">{'English' if hi else 'हिंदी'}</a></nav></header><main id="content"><h1>{esc(title)}</h1><p>Coupon World editorial research · Guide revised 12 November 2026</p>{body}{feedback}</main><script defer src="/assets/page-feedback.js?v=20261112"></script><footer><a href="/guides/about-coupon-world/">About, research method and corrections</a><p>Prepared with AI assistance from documented sources. No hands-on testing, live price, stock, or tested overall winner is claimed. As an Amazon Associate I earn from qualifying purchases.</p></footer></body></html>'''

def write(root,path,content):
    file=route_file(root,path);file.parent.mkdir(parents=True,exist_ok=True);file.write_text(content,encoding='utf-8')

def evidence_comparison_matrix(root: Path, hi: bool = False) -> str:
    """Show documented A36/A56 facts, retaining source provenance in each cell.

    This is a factual table on the retained guide, not a benchmark or a new
    ranking/offer engine. Require publisher-approved exact model identities.
    """
    from python.phone_research_pages import (
        accepted_specs, eligible, model_title, specification_value,
    )

    catalogue = json.loads((root / "data/mobile_research_catalogue.json").read_text(encoding="utf-8"))
    by_key = {card["model_key"]: card for card in catalogue["model_cards"]}
    models = [
        by_key["samsung|galaxy a36 5g"],
        by_key["samsung|galaxy a56 5g"],
    ]
    if any(not eligible(card) for card in models):
        raise ValueError("Retained comparison guide needs two eligible manufacturer-backed phones")
    documented = [dict(accepted_specs(card)) for card in models]
    keys = (
        ("chipset", "Processor", "प्रोसेसर"),
        ("display_type", "Display technology", "स्क्रीन तकनीक"),
        ("display_inches", "Screen diagonal", "स्क्रीन आकार"),
        ("display_refresh_max_hz", "Maximum refresh rate", "अधिकतम रिफ्रेश रेट"),
        ("rear_main_mp", "Main camera resolution", "मुख्य कैमरा रिज़ॉल्यूशन"),
        ("rear_ultrawide_mp", "Ultrawide camera resolution", "अल्ट्रावाइड कैमरा रिज़ॉल्यूशन"),
        ("front_mp", "Front camera resolution", "फ्रंट कैमरा रिज़ॉल्यूशन"),
        ("battery_mah_typical", "Typical battery capacity", "सामान्य बैटरी क्षमता"),
        ("wired_charging_max_w", "Maximum wired charging", "अधिकतम वायर्ड चार्जिंग"),
        ("launch_android", "Android at launch", "लॉन्च के समय एंड्रॉयड"),
        ("os_upgrade_generations", "Promised OS upgrades", "घोषित OS अपडेट"),
        ("security_support_years", "Promised security support", "घोषित सुरक्षा अपडेट"),
    )
    if sum(all(key in fields for fields in documented) for key, _, _ in keys) < 10:
        raise ValueError("Insufficient comparable verified specifications for the retained guide")

    def cell(key: str, values: dict) -> str:
        item = values.get(key)
        if not item:
            return "<td>" + ("अभी स्रोत उपलब्ध नहीं" if hi else "Source not documented") + "</td>"
        url = str(item["source_url"])
        value = specification_value(key, item)
        source_label = "मूल स्रोत" if hi else "Original source"
        return (
            "<td><strong>" + esc(value) + "</strong> "
            '<a href="' + esc(url) +
            '" rel="nofollow noopener noreferrer" target="_blank">' + source_label +
            "</a></td>"
        )

    rows = "".join(
        "<tr><th scope=\"row\">" + esc(label_hi if hi else label_en) + "</th>" +
        cell(key, documented[0]) + cell(key, documented[1]) + "</tr>"
        for key, label_en, label_hi in keys
    )
    lead = (
        "एक ही पंक्ति में दोनों निर्माता-स्रोतों के तकनीकी तथ्य दिए हैं। "
        "मॉडल-स्तर की जानकारी को सटीक भारतीय RAM/स्टोरेज वेरिएंट की खरीद पुष्टि न मानें। "
        "मेगापिक्सल, बैटरी क्षमता और प्रोसेसर नाम वास्तविक फोटो, गेम FPS या रनटाइम के परीक्षण नहीं हैं।"
        if hi else
        "Compare twelve comparable manufacturer-backed facts with the original source beside each value. "
        "These model-level facts do not certify a specific India RAM/storage SKU. "
        "Megapixels, capacity and processor names are not independently tested photo quality, sustained FPS or battery runtime."
    )
    title = "मूल स्रोतों के साथ तकनीकी तुलना" if hi else "Side-by-side specifications with manufacturer sources"
    first, second = (esc(model_title(card)) for card in models)
    return (
        '<section id="manufacturer-evidence" aria-labelledby="manufacturer-evidence-title">'
        '<h2 id="manufacturer-evidence-title">' + title + "</h2>"
        "<p>" + lead + "</p>"
        '<div class="table-wrap"><table>'
        "<caption>" + ("प्रत्येक तथ्य के लिए स्रोत उपलब्ध" if hi else "Manufacturer-backed recorded values; check regional SKU applicability") + "</caption>"
        "<thead><tr><th scope=\"col\">" + ("विशेषता" if hi else "Feature") + "</th>"
        '<th scope="col">' + first + '</th><th scope="col">' + second +
        "</th></tr></thead><tbody>" + rows + "</tbody></table></div></section>"
    )


def comparison_guide(root,hi=False):
    path='/hi/compare/' if hi else '/compare/'
    title='दो फोन की उपयोगी तुलना कैसे करें' if hi else 'How to compare two phones for your own needs'
    body=('''<p>पहले दोनों सटीक मॉडल और भौतिक RAM/स्टोरेज तय करें। नाम में Pro, Plus या 5G बदलने पर दूसरा उपकरण हो सकता है। अपने काम—कॉल, फोटो, गेमिंग या पढ़ाई—को प्राथमिकता दें।</p><h2>एक वास्तविक उदाहरण: Galaxy A36 5G और A56 5G</h2><p>निर्माता के रिकॉर्ड में A36 का Snapdragon 6 Gen 3 और A56 का Exynos 1580 अलग हैं। इससे अपने-आप वास्तविक गेमिंग FPS या कैमरा विजेता तय नहीं होता। दोनों के लिए दर्ज 5000 mAh क्षमता और 45 W अधिकतम चार्जिंग समान होने पर भी रनटाइम और चार्जिंग समय की गारंटी समान नहीं है।</p>''' if hi else '''<p>Start with the two exact model names and physical RAM/storage configurations. Pro, Plus and 5G suffixes can identify different devices. Then name the task that matters most: calls, photographs, games or study.</p><h2>A concrete example: Galaxy A36 5G and Galaxy A56 5G</h2><p>The documented A36 Snapdragon 6 Gen 3 and A56 Exynos 1580 are different processors. That difference alone cannot identify a real gaming-FPS or camera winner. Both records list 5000 mAh typical batteries and 45 W maximum wired charging, but equal headline numbers do not guarantee equal runtime or charging duration.</p>''')
    body+='<p><a href="/phones/samsung-galaxy-a36-5g/">Galaxy A36: original specification sources</a> · <a href="/phones/samsung-galaxy-a56-5g/">Galaxy A56: original specification sources</a></p>'
    body+=evidence_comparison_matrix(root,hi)
    if hi:
        body+='''<h2>तुलना का क्रम</h2><ol><li>भारतीय SKU, भौतिक RAM और स्टोरेज समान संदर्भ में रखें। दूसरे वेरिएंट की कीमत न लें।</li><li>जरूरी शर्त और पसंद अलग लिखें। OIS जरूरी है तो बिना स्रोत पुष्टि वाला फोन बाहर रखें।</li><li>कैमरे के लिए एक जैसी परिस्थितियों के नमूने, गेमिंग के लिए समान सेटिंग के लंबे सत्र और बैटरी के लिए समान काम का रनटाइम देखें।</li><li>OS पीढ़ियाँ और सुरक्षा अपडेट के वर्ष अलग मिलाएँ; शेष समर्थन की शुरुआत या अंतिम तारीख भी देखें।</li><li>अंत में उसी वेरिएंट का विक्रेता, वारंटी, अंतिम भुगतान और डिलीवरी जाँचें।</li></ol><h2>क्या निष्कर्ष निकाला जा सकता है?</h2><p>निर्माता की तालिका हार्डवेयर अंतर दिखाती है। समान परीक्षण के बिना कैमरा, FPS या बैटरी का प्रमाणित विजेता नहीं चुना जा सकता। अलग प्रकाश, गेम सेटिंग या रनटाइम पद्धति के स्कोर सीधे न जोड़ें।</p>'''
    else:
        body+='''<h2>A comparison sequence that avoids misleading results</h2><ol><li>Keep the India SKU, physical RAM and storage explicit. Never reuse another memory variant's price.</li><li>Write mandatory conditions separately from preferences. If OIS is mandatory, withhold a phone whose source does not confirm it.</li><li>For cameras, compare samples in similar conditions. For gaming, compare sustained sessions with the same settings. For battery life, compare the same workload.</li><li>Separate OS generations from security-update years and check the stated support start or end date.</li><li>Finally verify the actual retailer listing, warranty, payable price and delivery for that SKU.</li></ol><h2>What can you conclude?</h2><p>A manufacturer table establishes documented hardware differences. A controlled camera, FPS or endurance winner needs compatible tests. Scores from different lighting, graphics settings or runtime protocols must not be averaged as if they measured the same thing.</p>'''
    body+='<p><a href="/?q=Galaxy+A36+vs+Galaxy+A56#mobileResearchSearch">Compare the two documented models in the existing research tool</a></p><p><a href="/seo/compare-phones-exact-variants.html">Exact-variant checklist</a> · <a href="/seo/phone-research-evidence-method.html">Evidence method</a></p>'
    return path,doc(path,title,body,hi)

def budget_guide(root,hi=False):
    path='/hi/phones/under-25000/' if hi else '/phones/under-25000/'
    title='₹25,000 से कम फोन चुनने की स्रोत-आधारित गाइड' if hi else 'Choosing a phone under ₹25,000: a source-linked guide'
    if hi:
        body='''<p>₹25,000 को खर्च की सीमा मानें, प्रदर्शन का स्कोर नहीं। नीचे मॉडल उदाहरण पुराने exact-variant price references से शोध शुरू करने के लिए हैं। यह आज ₹25,000 में उपलब्ध ऑफर या सर्वश्रेष्ठ फोन की रैंकिंग नहीं है।</p><h2>पहले अपनी जरूरत तय करें</h2><p>कैमरे के लिए OIS और नमूने, गेमिंग के लिए लंबे सत्र के FPS, बैटरी के लिए रनटाइम और लंबे उपयोग के लिए शेष अपडेट समर्थन देखें। एक व्यक्ति की पहली पसंद दूसरे व्यक्ति की जरूरत से अलग हो सकती है।</p>'''
    else:
        body='''<p>Treat ₹25,000 as a spending limit, not a performance score. The examples below are starting points from dated exact-variant price references. They are not a ranking or a claim that these phones are currently available below ₹25,000.</p><h2>Choose the job before choosing the model</h2><p>For photography, inspect OIS and actual samples. For games, look for sustained FPS and heat at the settings you use. For time away from a charger, inspect measured runtime. For years of ownership, check remaining update support. Those needs can lead to different shortlists.</p>'''
    body+='''<h2>Three documented examples and the decisions they raise</h2><div class="table-wrap"><table><thead><tr><th>Research example</th><th>Useful source fact</th><th>What still needs checking</th></tr></thead><tbody><tr><td><a href="/phones/poco-x7-pro/">POCO X7 Pro</a><br>8GB/256GB dated reference</td><td>6.67-inch AMOLED; India typical battery 6550 mAh.</td><td>Do not substitute the global 6000 mAh battery. Sustained game performance still needs a compatible test.</td></tr><tr><td><a href="/phones/samsung-galaxy-a36-5g/">Samsung Galaxy A36 5G</a><br>8GB/128GB dated reference</td><td>OIS, 120 Hz Super AMOLED, six OS generations and six years of security updates.</td><td>Support is not six years remaining from every purchase date. Do not transfer the 8/128 reference to 8/256.</td></tr><tr><td><a href="/phones/nothing-phone-3a/">Nothing Phone (3a)</a><br>8GB/128GB dated reference</td><td>The India page describes an OIS main camera and a 2x optical telephoto.</td><td>Lens versatility does not prove better low-light photographs or video.</td></tr></tbody></table></div><p>Budget-reference checks: 3 November 2026. These reference dates are not a new price or stock check. Open the model research page for the original evidence and its regional/variant scope.</p>'''
    body+='''<h2>Manufacturer sources</h2><ul><li><a href="https://www.mi.com/pk/support/faq/details/KA-522489/">Xiaomi: POCO X7 Pro regional battery distinction</a></li><li><a href="https://www.samsung.com/in/smartphones/galaxy-a/galaxy-a36-5g-awesome-black-256gb-sm-a366ezkkins/">Samsung India: A36 technical specifications and update policy</a></li><li><a href="https://in.nothing.tech/products/phone-3a">Nothing India: Phone (3a) camera specifications</a></li></ul>'''
    body+=('''<h2>खरीद से पहले अंतिम जाँच</h2><p>विक्रेता पर भौतिक RAM/स्टोरेज, भारतीय वारंटी, स्टॉक और पिनकोड की डिलीवरी देखें। बैंक कार्ड, एक्सचेंज और सदस्यता की छूट को बिना शर्त कीमत से अलग रखें। ₹25,000 की सीमा में सस्ते दस्तावेज़ित विकल्प भी शामिल होने चाहिए।</p>''' if hi else '''<h2>Before paying</h2><p>Confirm physical RAM/storage, India warranty, stock and postcode-specific delivery at the retailer. Keep card, exchange and membership discounts separate from an unconditional price. An under-₹25,000 search should also include documented cheaper options.</p>''')
    body+=('''<h2>आम खरीद सवाल</h2><h3>कैमरा, गेमिंग या बैटरी के लिए किस गाइड से शुरू करें?</h3><p>अपनी प्राथमिकता वाली गाइड खोलें: <a href="/seo/camera-phone-buying-guide.html">कैमरा</a>, <a href="/seo/gaming-phone-buying-guide.html">गेमिंग</a> या <a href="/seo/battery-phone-buying-guide.html">बैटरी</a>। ये पेज स्रोत और सीमाएँ दिखाते हैं; समान लैब टेस्ट के बिना अंतिम विजेता घोषित नहीं किया गया है।</p><h3>क्या आज की कीमत और स्टॉक सत्यापित हैं?</h3><p>नहीं। retailer पर सही मॉडल, RAM, स्टोरेज, विक्रेता, वारंटी, पिनकोड और अंतिम कीमत खुद जाँचें।</p>''' if hi else '''<h2>Questions people ask before buying</h2><h3>Which guide should I start with for camera, gaming or battery?</h3><p>Open the guide that matches your priority: <a href="/seo/camera-phone-buying-guide.html">camera</a>, <a href="/seo/gaming-phone-buying-guide.html">gaming</a> or <a href="/seo/battery-phone-buying-guide.html">battery</a>. These pages keep source context and limitations visible; no final winner is claimed without one identical lab protocol across every model.</p><h3>Are today’s price and stock verified?</h3><p>No. Confirm the exact model, RAM, storage, seller, warranty, postcode and final payable price on the retailer.</p>''')
    body+='<p><a href="/?q=phone+under+25000#mobileResearchSearch">Research phones below ₹25,000</a> · <a href="/seo/phone-price-stock-verification.html">How dated prices differ from live offers</a></p>'
    return path,doc(path,title,body,hi)

class Links(HTMLParser):
    def __init__(self,text):super().__init__();self.links=[];self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='a' and a.get('href'):self.links.append(a['href'])

def link_retained_comparison_guide(root):
    """Add crawlable, truthful navigation to the retained EN/HI guide.

    The 100 old pairwise comparison pages are intentionally retired; only the
    two useful guides remain. Generate entry links after those guides exist.
    """
    entries = (
        ("index.html", "/compare/", "Evidence-backed phone comparison guide",
         "Learn how to compare documented India phone variants with original sources."),
        ("phones/index.html", "/compare/", "Evidence-backed phone comparison guide",
         "See source-backed Galaxy A36 and A56 facts, then compare your own exact models."),
        ("hi/phones/index.html", "/hi/compare/", "स्रोत-आधारित फोन तुलना गाइड",
         "Galaxy A36 और A56 के प्रमाण तथा सही भारतीय वेरिएंट चुनने की जाँच-पद्धति देखें।"),
    )
    for relative, href, label, description in entries:
        file = root / relative
        if not file.is_file():
            raise FileNotFoundError("Comparison guide navigation missing source: " + relative)
        page = file.read_text(encoding="utf-8")
        marker = 'id="cw-comparison-guide-entry"'
        if marker in page:
            raise ValueError("Comparison guide navigation was added twice: " + relative)
        if "</main>" not in page:
            raise ValueError("Comparison guide navigation needs main landmark: " + relative)
        section = (
            '<section class="comparison-discovery" id="cw-comparison-guide-entry">'
            '<h2><a href="' + href + '">' + html.escape(label) + '</a></h2>'
            '<p>' + html.escape(description) + '</p></section>'
        )
        file.write_text(page.replace("</main>", section + "</main>", 1), encoding="utf-8")


def apply_policy(destination):
    root=Path(destination)
    # No page-per-query or arbitrary pair/budget permutation publishing.
    for prefix in ('answers','hi/answers','compare','hi/compare','phones/under-25000','hi/phones/under-25000'):
        path=root/prefix
        if path.exists():shutil.rmtree(path)
    for hi in (False,True):
        for renderer in (comparison_guide,budget_guide):
            path,content=renderer(root,hi);write(root,path,content)
    link_retained_comparison_guide(root)
    guides=json.loads((ROOT/'data/phone-guides.json').read_text(encoding='utf-8'))['pages']
    approved={g['slug']+'.html' for g in guides} | {'india-smartphone-search-demand.html'}
    for file in (root/'seo').glob('*.html'):
        if file.name not in approved:file.unlink()
    # The legacy guide directory must list real reviewed pages, not 50
    # ready-labelled keyword placeholders pointing to missing templates.
    (root/'data/seo-pages.json').write_text(json.dumps([{'slug':g['slug'],'title':g['title'],'metaDescription':g['intro'],'category':'Smartphone','intent':'Research guide','priority':i,'status':'ready'} for i,g in enumerate(guides,1)],ensure_ascii=False,indent=2)+'\n', encoding='utf-8')
    for filename in ('mobile_query_answer_coverage.json',):
        path=root/'data'/filename
        if path.exists():path.unlink()
    # Real 404 status is supplied by GitHub Pages, with no blanket redirect.
    (root/'404.html').write_text('''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,follow"><title>Page not found | Coupon World</title></head><body><main><h1>Page not found</h1><p>This page is no longer available. Choose a research guide or search for an exact phone.</p><ul><li><a href="/guides/phone-budget-guides/">Phone buying guides</a></li><li><a href="/phones/">Source-linked phone specifications</a></li><li><a href="/#mobileResearchSearch">Search phone research</a></li></ul></main></body></html>''',encoding='utf-8')
    ns='{http://www.sitemaps.org/schemas/sitemap/0.9}'
    ET.register_namespace('',ns[1:-1]);tree=ET.parse(root/'sitemap.xml');sitemap=tree.getroot()
    for node in list(sitemap):
        loc=node.find(ns+'loc');url=urlsplit(loc.text or '') if loc is not None else None
        if url is None:continue
        path=route_file(root,url.path)
        if not path.is_file() or re.search(r'name="robots"\s+content="[^"]*noindex',path.read_text(encoding='utf-8'),re.I):sitemap.remove(node)
    locations={n.text for n in sitemap.iter(ns+'loc')}
    for path in RETAINED_HUBS:
        if SITE+path not in locations:
            item=ET.SubElement(sitemap,ns+'url');ET.SubElement(item,ns+'loc').text=SITE+path
    tree.write(root/'sitemap.xml',encoding='utf-8',xml_declaration=True)
    retired=json.loads(RETIRED.read_text(encoding='utf-8'))['routes']
    for route in retired:
        if route_file(root,route).exists():raise ValueError('Retired page was republished: '+route)
    # Check all retained static internal navigation. A removed page must not
    # remain reachable from an active card, guide, sitemap or language link.
    for page in root.rglob('*.html'):
        text=page.read_text(encoding='utf-8')
        for href in Links(text).links:
            url=urlsplit(href)
            if url.netloc or not url.path.startswith('/'):continue
            if not route_file(root,unquote(url.path)).is_file():raise ValueError(f'Broken internal link {page.relative_to(root)} -> {href}')
    print(f'Publication cleanup: {len(retired)} retired routes absent; retained navigation and sitemap verified')
