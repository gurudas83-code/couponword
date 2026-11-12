"""Evidence-first standalone English/Hindi SEO pages for 25 India under-25k research candidates.

Static content only. Never changes the approved phone candidate pool, scoring,
price gate, offer freshness, or the 232-card registry.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from xml.etree import ElementTree as ET

from python.affiliate_links import AMAZON_TAG

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "india_under_25000_seo_facts_20261106.json"
BASE = "https://coupon-world.in"
EN = "/phones/under-25000/"
HI = "/hi/phones/under-25000/"
CSS = "/assets/under25-seo.css?v=20261106"
GADGETS = "https://www.gadgets360.com/mobiles/best-phone-under-25000"
REVIEW = "https://www.91mobiles.com/reviews/best-phones-under-25000/"
CONTENT_UPDATED = "2026-11-12"

CATEGORY_TEXT = {
    "overall": {
        "en": ("Best overall phones under ₹25,000 in India", "Balanced day-to-day ownership: endurance, reliable software, usability, useful cameras and price-bracket evidence."),
        "hi": ("₹25,000 से कम में बेस्ट ओवरऑल मोबाइल", "हर दिन के इस्तेमाल में बैटरी, सॉफ्टवेयर, कैमरा और भरोसेमंद उपयोग का संतुलन।")
    },
    "camera": {
        "en": ("Best camera phones under ₹25,000 in India", "Camera versatility, scene quality, real test findings and useful optical focal lengths — not megapixels alone."),
        "hi": ("₹25,000 से कम में बेस्ट कैमरा फोन", "केवल मेगापिक्सल नहीं: फोटो के असली परीक्षण, अल्ट्रावाइड, जूम और रंगों का मूल्यांकन।")
    },
    "gaming": {
        "en": ("Best gaming phones under ₹25,000 in India", "Chipset headroom, graphics capability, heat, real game stability and usable battery life."),
        "hi": ("₹25,000 से कम में बेस्ट गेमिंग फोन", "चिपसेट, ग्राफिक्स, गर्म होने की संभावना, गेमिंग स्थिरता और बैटरी पर ध्यान।")
    },
    "battery": {
        "en": ("Best battery phones under ₹25,000 in India", "Independent endurance results where available, battery capacity, charging and practical compromises."),
        "hi": ("₹25,000 से कम में बेस्ट बैटरी मोबाइल", "जहाँ उपलब्ध हों वहाँ वास्तविक बैटरी परीक्षण, क्षमता, चार्जिंग और वजन का संतुलन।")
    }
}

# Distinctive Hindi editorial verdicts. Facts and public technical units
# are preserved literally instead of unverified language-model expansion.
HINDI_NOTES = {
 "poco|x7 pro 5g":("भारी गेमिंग और मल्टीटास्किंग इसका प्रमुख आकर्षण है।","कैमरा और लंबे गेमिंग सेशन में गर्म होने का व्यवहार अलग से जाँचें।"),
 "infinix|hot 70 pro 5g+":("अलग डिजाइन और डेढ़ दिन के आसपास की समीक्षा-आधारित बैटरी इस मॉडल की खासियत है।","मॉडल के नाम में 5G और 5G+ का अंतर है; सटीक भारतीय वेरिएंट की पुष्टि करें।"),
 "motorola|moto g max":("बड़ी बैटरी और दो रियर कैमरे व्यावहारिक उपयोग के लिए उपयोगी हैं।","LCD और अपेक्षाकृत साधारण प्रोसेसर गेमिंग में सीमा बन सकते हैं।"),
 "poco|m8 power 5g":("लंबी बैटरी लाइफ और सामान्य कामकाज में संतुलन इसका पक्ष है।","डिस्प्ले के प्रकार पर दो स्रोत अलग बातें कहते हैं; बिना पुष्टि दावा नहीं किया गया है।"),
 "oneplus|n6 5g":("लंबी यात्रा और कम चार्जिंग की जरूरत वाले लोगों के लिए अच्छा विकल्प है।","एंट्री वेरिएंट की कम RAM और साधारण स्क्रीन पर ध्यान दें।"),
 "infinix|note edge":("कर्व्ड डिस्प्ले और बड़ी बैटरी रोजमर्रा के लिए आकर्षक हैं।","कम रोशनी में कैमरा और वीडियो स्थिरता पर समीक्षाओं में सवाल उठे हैं।"),
 "poco|m8 5g":("स्क्रीन, बैटरी और सामान्य प्रोसेसिंग का उपयोगी संतुलन मिलता है।","कैमरा और पहले से इंस्टॉल ऐप्स ध्यान देने योग्य सीमाएँ हैं।"),
 "redmi|redmi note 15 5g":("स्टोरेज और अल्ट्रावाइड कैमरा उपयोगी सुविधाएँ हैं।","अधिक मेगापिक्सल का अर्थ हमेशा बेहतर तस्वीर नहीं होता।"),
 "nothing|phone (3a) lite":("सादा सॉफ्टवेयर और अलग डिजाइन इसकी पहचान हैं।","इस Lite मॉडल में अलग टेलीफोटो कैमरा नहीं है।"),
 "oneplus|nord ce5":("प्रोसेसर, बड़ी बैटरी और AMOLED स्क्रीन का अच्छा मेल है।","एकल स्पीकर और सटीक कीमत/वेरिएंट की जाँच जरूरी है।"),
 "infinix|gt 30 pro 5g":("गेमिंग-केंद्रित चिप और पर्याप्त स्टोरेज इसे दिलचस्प बनाते हैं।","लगातार FPS और गर्म होने के स्वतंत्र परीक्षण देखें।"),
 "vivo|t4 5g":("बड़ी बैटरी के साथ सामान्य प्रदर्शन भी सक्षम दिखता है।","रियर कैमरा विकल्प सीमित हैं; बजट में होना ऑफर पर निर्भर है।"),
 "motorola|edge 60 fusion":("कर्व्ड स्क्रीन, डिजाइन और अल्ट्रावाइड कैमरा इसकी ताकत हैं।","पहले से इंस्टॉल ऐप्स और औसत बैटरी को ध्यान में रखें।"),
 "iqoo|neo 10r":("दमदार Snapdragon चिप गेमिंग और मल्टीटास्किंग के लिए उपयोगी है।","कम रोशनी में कैमरा और प्लास्टिक निर्माण समझौते हैं।"),
 "nothing|phone (3a)":("टेलीफोटो कैमरा और साफ सॉफ्टवेयर पोर्ट्रेट पसंद करने वालों के लिए अच्छे हैं।","कम रोशनी में जूम और वीडियो के परिणाम अलग से देखें।"),
 "samsung|galaxy a36 5g":("लंबा OS और सुरक्षा अपडेट सपोर्ट बड़ा लाभ है।","निर्माता की कीमत कई बार ₹25,000 से ऊपर होती है; हर ऑफर चेक करें।"),
 "realme|p3 pro 5g":("कर्व्ड स्क्रीन और डेली परफॉर्मेंस उपयोगी हैं।","अनावश्यक ऐप्स और कम रोशनी में कैमरा अनुभव कमजोर हो सकता है।"),
 "realme|14 pro+ 5g":("असली 3x पेरिस्कोप जूम और पोर्ट्रेट कैमरा खास है।","कैमरा स्पेक से हर परिस्थिति में सर्वश्रेष्ठ परिणाम सिद्ध नहीं होते।"),
 "tecno|pova slim 5g":("पतला डिजाइन और हल्का अनुभव इसकी अलग पहचान है।","भारी गेमिंग और अधिक बैटरी के लिए दूसरे मॉडल भी जाँचें।"),
 "realme|15t":("बड़ी बैटरी और अपेक्षाकृत छोटा स्क्रीन आकार उपयोगी हैं।","समीक्षाओं में कैमरा और तेज रिफ्रेश गेमिंग की सीमाएँ मिली हैं।"),
 "samsung|galaxy a26 5g":("Samsung सॉफ्टवेयर, AMOLED और IP67 सुरक्षा इसके फायदे हैं।","फोटोग्राफी, स्पीकर और चार्जिंग प्रतिस्पर्धी नहीं मानी गई हैं।"),
 "motorola|moto g57 power":("समीक्षा में कैमरा, अल्ट्रावाइड और बैटरी की अच्छी सराहना हुई है।","कम OS अपग्रेड लंबे समय के उपयोग में कमजोरी हैं।"),
 "lava|virat curve 5g":("कर्व्ड AMOLED और स्टीरियो ऑडियो मनोरंजन के लिए उपयोगी हैं।","कैमरा विविधता और सॉफ्टवेयर अनुभव में सुधार की जगह है।"),
 "samsung|galaxy f70 pro 5g":("Samsung के स्रोत से तकनीकी रिकॉर्ड उपलब्ध है।","सटीक ₹25,000 retailer offer और प्रदर्शन का प्रमाण अभी नहीं मिला।"),
 "oppo|k13 5g":("AMOLED, बड़ी बैटरी और तेज चार्जिंग व्यावहारिक फायदे हैं।","निर्माता के दावों की तुलना स्वतंत्र परीक्षण और सही SKU से करें।")
}

def esc(s):
    return html.escape(str(s or ""), quote=True)

def slug(m):
    return re.sub(r"[^a-z0-9]+", "-", (m["brand"]+" "+m["model"]).lower()).strip("-")

def display_name(m):
    # Avoid "Redmi Redmi..." and other brand name duplicates.
    brand = str(m["brand"]).strip()
    model = str(m["model"]).strip()
    if model.lower().startswith(brand.lower()+" "):
        return model
    return brand+" "+model

def pth(m, hi=False):
    return (HI if hi else EN)+slug(m)+"/"

def seller_links(m, hi=False):
    name = display_name(m)
    amazon = "https://www.amazon.in/s?"+urlencode({"k":name,"tag":AMAZON_TAG})
    flipkart = "https://www.flipkart.com/search?"+urlencode({"q":name})
    # Croma has no verified model-exact listing for most of these brands.
    # Use known public brand catalogues only when brand is appropriate.
    if m["brand"].lower()=="samsung":
        croma = "https://www.croma.com/samsung-android-phones/bc/b-0328-95"
    elif m["brand"].lower()=="oneplus":
        croma = "https://www.croma.com/oneplus-android-phones/bc/b-0948-95"
    else:
        croma = "https://www.croma.com/"
    for u in (amazon,flipkart,croma):
        parsed = urlsplit(u)
        if parsed.scheme!="https" or parsed.hostname not in {"www.amazon.in","www.flipkart.com","www.croma.com"}:
            raise ValueError("Unapproved retailer host")
    return (('<div class="buy-options" aria-label="'+("विक्रेता खोज" if hi else "Retailer research links")+'">'
             '<a target="_blank" rel="sponsored nofollow noopener noreferrer" href="'+esc(amazon)+'">'+("Amazon पर खोजें (affiliate)" if hi else "Search Amazon (affiliate)")+'</a>'
             '<a target="_blank" rel="nofollow noopener noreferrer" href="'+esc(flipkart)+'">'+("Flipkart पर खोजें" if hi else "Search Flipkart")+'</a>'
             '<a target="_blank" rel="nofollow noopener noreferrer" href="'+esc(croma)+'">'+("Croma में देखें" if hi else "Browse Croma")+'</a>'
             '</div>'))

def valid_data():
    data=json.loads(SOURCE.read_text(encoding="utf-8"))
    rows=data["models"]
    keys={x["key"] for x in rows}
    if len(rows)!=25 or len(keys)!=25 or data["budget_inr"]!=25000:
        raise ValueError("25 nonduplicate budget models required")
    if len([x for x in rows if x["primary_catalogue_present"]])!=10:
        raise ValueError("Reconciliation with original core changed")
    for item in rows:
        if item["key"]!=(item["brand"]+"|"+item["model"]).lower():
            raise ValueError("Model identity drift")
        if item.get("price_claim_on_public_page") or item.get("retailer_offer_verified"):
            raise ValueError("Retailer purchase claim not authorized")
        if not item.get("highlight") or not item.get("caution") or not item.get("editorial_reference_url"):
            raise ValueError("Missing individual research")
        if item["key"] not in HINDI_NOTES:
            raise ValueError("Missing individual Hindi review notes")
    for category, ranked in data["ranked_categories"].items():
        if category not in CATEGORY_TEXT or len(ranked)!=5 or len(set(ranked))!=5 or not set(ranked)<=keys:
            raise ValueError("Invalid category shortlist")
    if data["disclosure"] and "Price weight remains 0%" not in data["disclosure"]:
        raise ValueError("Price scoring contract missing")
    return data

def base_document(path,title,desc,body,hi=False,index=True,kind="WebPage",item_list=None):
    other=path.replace(HI,EN,1) if hi else path.replace(EN,HI,1)
    lang="hi-IN" if hi else "en-IN"
    alt="en-IN" if hi else "hi-IN"
    nodes=[
        {"@type":kind,"name":title,"description":desc,"url":BASE+path,
         "dateModified":CONTENT_UPDATED,"publisher":{"@type":"Organization","name":"Coupon World","url":BASE+"/"}},
        {"@type":"BreadcrumbList","itemListElement":[
            {"@type":"ListItem","position":1,"name":"Home","item":BASE+"/"},
            {"@type":"ListItem","position":2,"name":"Phones under ₹25,000","item":BASE+(HI if hi else EN)},
            {"@type":"ListItem","position":3,"name":title,"item":BASE+path}
        ]}
    ]
    if item_list is not None:
        nodes[0]["mainEntity"]={"@type":"ItemList","numberOfItems":len(item_list),"itemListElement":[
            {"@type":"ListItem","position":i+1,"name":n,"url":BASE+u} for i,(n,u) in enumerate(item_list)]}
    structured=json.dumps({"@context":"https://schema.org","@graph":nodes},ensure_ascii=False).replace("<","\\u003c")
    home="होम" if hi else "Home"
    guide="₹25,000 मोबाइल गाइड" if hi else "Under ₹25k guides"
    note=("इस पेज में लाइव कीमत, स्टॉक या खरीदने की पुष्टि नहीं की गई है।"
          if hi else "No live price, stock or purchase eligibility is certified on this page.")
    return (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(title)} | Coupon World</title>'
            f'<meta name="description" content="{esc(desc)}">'
            f'<meta name="robots" content="{"index,follow" if index else "noindex,follow"}">'
            f'<link rel="canonical" href="{esc(BASE+path)}">'
            f'<link rel="alternate" hreflang="{lang}" href="{esc(BASE+path)}">'
            f'<link rel="alternate" hreflang="{alt}" href="{esc(BASE+other)}">'
            f'<link rel="alternate" hreflang="x-default" href="{esc(BASE+(EN if hi else path))}">'
            f'<meta property="og:title" content="{esc(title)}">'
            f'<meta property="og:description" content="{esc(desc)}">'
            f'<meta property="og:type" content="article">'
            f'<meta property="og:url" content="{esc(BASE+path)}">'
            f'<meta property="og:image" content="{BASE}/assets/coupon-world-og.svg">'
            f'<link rel="stylesheet" href="{CSS}">'
            f'<script type="application/ld+json">{structured}</script>'
            f'</head><body><a class="skip" href="#content">{"मुख्य सामग्री" if hi else "Skip to content"}</a>'
            f'<header class="site-header"><div class="container"><a class="brand" href="/">CW · Coupon World</a>'
            f'<nav aria-label="Main navigation"><a href="{HI if hi else EN}">{guide}</a>'
            f'<a href="/phones/">{"मोबाइल रिसर्च" if hi else "Phone research"}</a>'
            f'<a href="{other}" lang="{alt}">{"English" if hi else "हिंदी"}</a></nav></div></header>'
            f'<main id="content" class="container"><nav class="breadcrumb">'
            f'<a href="/">{home}</a> / <a href="{HI if hi else EN}">{guide}</a></nav>{body}</main>'
            f'<footer class="container"><hr><p>{note}</p>'
            f'<p>As an Amazon Associate I earn from qualifying purchases. Amazon links may include an affiliate tracking tag; retailer searches are not verified offers.</p>'
            f'<p>Editorial research updated 6 November 2026. <a href="/seo/phone-research-evidence-method.html">Evidence methodology</a>.</p></footer></body></html>')

def source_item(url,label):
    if urlsplit(str(url)).scheme!="https":
        return ""
    return f'<li><a href="{esc(url)}" target="_blank" rel="nofollow noopener noreferrer">{esc(label)}</a></li>'

def facts_table(m, core):
    facts=[
        ("Display (editorial reference)",m.get("display")),
        ("Processor (editorial reference)",m.get("chip")),
        ("Battery capacity (editorial reference)",m.get("battery")),
        ("Rear cameras (editorial reference)",m.get("camera")),
        ("RAM / storage example (editorial reference)",m.get("memory"))
    ]
    facts=[(lab,val,m["editorial_reference_url"]) for lab,val in facts if val]
    if m["key"]=="samsung|galaxy f70 pro 5g":
        cd=core.get(m["key"]) or {}
        for item in (cd.get("specifications") or {}).values():
            if item.get("value") is not None and item.get("source_url"):
                facts.append((str(item.get("label") or "Documented specification"),str(item["value"]),str(item["source_url"])))
    rows="".join('<tr><th scope="row">'+esc(a)+'</th><td>'+esc(b)+'</td><td>'+f'<a href="{esc(c)}" rel="noopener noreferrer" target="_blank">Source</a></td></tr>' for a,b,c in facts)
    return '<div class="table-wrap"><table><thead><tr><th>Specification</th><th>Documented claim</th><th>Evidence link</th></tr></thead><tbody>'+rows+'</tbody></table></div>' if rows else "<p>Specific technical fields await independently traceable source review.</p>"

def model_page(m, related, core, hi=False):
    name=display_name(m)
    title=(name+" का पूरा विश्लेषण: ₹25,000 मोबाइल गाइड (2026)" if hi else
           name+" under ₹25,000? Specs, Pros & Cons (2026)")
    desc=(name+" के फीचर्स, फायदे, कमियाँ और Amazon, Flipkart, Croma खोज लिंक। 6 नवंबर 2026 की स्रोत-आधारित रिसर्च।" if hi else
          "Research "+name+" for India's ₹25,000 phone shortlist: documented specs, reasons to consider, drawbacks and Amazon, Flipkart, Croma research links.")
    highlights=HINDI_NOTES[m["key"]] if hi else (m["highlight"],m["caution"])
    label1="किसके लिए उपयोगी?" if hi else "Who should consider it?"
    label2="खरीदने से पहले ध्यान दें" if hi else "Main compromises"
    status=("मुख्य 232-मॉडल रिसर्च कैटलॉग में है" if hi else "In the original 232-model research catalogue") if m["primary_catalogue_present"] else ("अलग रिसर्च रिकॉर्ड; मुख्य कैटलॉग में नहीं" if hi else "Research intake only; not yet in the primary catalogue")
    warning=("मॉडल 5G और 5G+ के नाम से अलग रिपोर्ट हुआ है। सही SKU तय होने तक यह पेज Google में इंडेक्स नहीं होगा।" if hi else
             "Inconsistent 5G/5G+ model naming requires an exact Indian SKU check. This page is held from search indexing.") if m["manufacturer_scope"]=="MODEL_NAMING_ALIAS_REQUIRES_REVIEW" else ""
    notice=("इस मॉडल की सूचीबद्ध कीमत तारीख-निर्भर थी। ₹25,000 के अंदर वर्तमान उपलब्धता किसी भी retailer पर प्रमाणित नहीं है। हर retailer पर मॉडल, RAM, स्टोरेज, पिनकोड और वारंटी जाँचें।" if hi else
            "This model appeared in a dated sub-₹25,000 editorial price list. That does not establish a current qualifying offer. Recheck exact RAM, storage, delivery postcode, seller, warranty and final price on each retailer.")
    fields_title="दर्ज तकनीकी जानकारी और स्रोत" if hi else "Documented specifications and evidence"
    table=facts_table(m,core)
    related_html="".join('<li><a href="'+pth(x,hi)+'">'+esc(display_name(x))+'</a></li>' for x in related)
    manufacturer=source_item(m.get("manufacturer_url"),"निर्माता की वेबसाइट" if hi else "Manufacturer specification/reference page") if m.get("manufacturer_url") else ""
    links=source_item(m["editorial_reference_url"],"स्वतंत्र स्रोत की मोबाइल सूची / समीक्षा" if hi else "Original editorial shortlist/review")+manufacturer
    decision=("<p>यह वेबसाइट खुद के किए हुए लैब टेस्ट या लाइव कीमत का दावा नहीं करती। बैटरी का mAh, कैमरे का MP और चिप का नाम अकेले गुणवत्ता नहीं बताता। तुलना के लिए निर्माता का सही मॉडल और स्वतंत्र परीक्षण देखें।</p>" if hi else
              "<p>We have not physically tested this device. Advertised battery mAh does not equal independently measured screen-on time, and camera megapixels are not a photo-quality score. Look for controlled camera samples, game FPS and sustained heat results for your intended usage.</p>")
    body=(f'<section class="hero"><div class="eyebrow">{"भारत · मॉडल विश्लेषण · नवंबर 2026" if hi else "INDIA · PHONE RESEARCH · NOVEMBER 2026"}</div>'
          f'<h1>{esc(title)}</h1><p class="lead">{esc(highlights[0])}</p>'
          f'<span class="badge {"warn" if not m["primary_catalogue_present"] else ""}">{esc(status)}</span></section>'
          f'<aside class="notice"><strong>{"कीमत और उपलब्धता की शर्त" if hi else "Budget and offer verification"}</strong><p>{esc(notice)}</p>'
          +(f'<p>{esc(warning)}</p>' if warning else "")+'</aside>'
          f'<section class="two"><div class="card pro"><h2>{label1}</h2><p>{esc(highlights[0])}</p></div>'
          f'<div class="card con"><h2>{label2}</h2><p>{esc(highlights[1])}</p></div></section>'
          f'<section class="panel"><h2>{fields_title}</h2>'
          f'<p class="muted">{"स्रोत के अनुसार मॉडल-स्तरीय जानकारी; RAM/स्टोरेज उदाहरण को खरीद योग्य स्टॉक न समझें।" if hi else "Model-level editorial reference values, not certified current seller SKUs. Each claim links to its evidence."}</p>'
          f'{table}</section>'
          f'<section class="panel"><h2>{"Amazon, Flipkart और Croma पर जाँचें" if hi else "Compare on Amazon, Flipkart and Croma"}</h2>'
          f'<p>{"ये खोज/कैटेगरी पेज हैं, खरीदने की गारंटी नहीं। Croma बटन पर मॉडल उपलब्ध न भी हो सकता है।" if hi else "These are searches or retailer categories, not exact-product purchase links. Croma may not stock this model or brand."}</p>'
          f'{seller_links(m,hi)}</section>'
          f'<section class="panel"><h2>{"कौन सा मॉडल लेना सही होगा?" if hi else "The purchase decision"}</h2>{decision}'
          f'<p>{"इसे दूसरी जरूरतों के हिसाब से तुलना करें:" if hi else "Compare against alternatives according to your actual priority:"}</p>'
          f'<ul>{related_html}</ul></section>'
          f'<section class="panel"><h2>{"असली शोध स्रोत" if hi else "Primary research trail"}</h2><ul class="source-list">{links}</ul>'
          f'<p class="muted">{"रिसर्च जाँच: 6 नवंबर 2026। निर्माता का मॉडल पेज सभी भारतीय वेरिएंट प्रमाणित नहीं करता।" if hi else "Editorial check: 6 November 2026. A manufacturer model page is not proof of all Indian memory configurations."}</p></section>'
          f'<section class="panel"><h2>{"आम सवाल" if hi else "Frequently asked questions"}</h2>'
          f'<h3>{"क्या यह ₹25,000 से कम में मिल रहा है?" if hi else "Can I buy it under ₹25,000 today?"}</h3>'
          f'<p>{esc(notice)}</p>'
          f'<h3>{"क्या ये अंतिम रैंकिंग है?" if hi else "Is this an approved Coupon World performance ranking?"}</h3>'
          f'<p>{"नहीं। यह स्रोत-सहित संपादकीय शोध है, मौजूदा performance formula का परिणाम नहीं। कीमत ranking में 0% भार रखती है।" if hi else "No. This is an evidence-linked editorial comparison, not a recalculation of Coupon World's approved performance ranking. Price has 0% weight in performance scoring."}</p></section>')
    indexed=m["manufacturer_scope"]!="MODEL_NAMING_ALIAS_REQUIRES_REVIEW"
    return base_document(pth(m,hi),title,desc,body,hi,indexed)

def category_page(category,rows,allmodels,hi=False):
    title,description=CATEGORY_TEXT[category]["hi" if hi else "en"]
    path=(HI if hi else EN)+"best-"+category+"/"
    intro=("<p class='muted'>पाँच मॉडल उपयोगिता के अनुसार चुने हैं। यह स्वतंत्र रूप से सभी 25 फोन के एक जैसे लैब परीक्षण वाली रैंकिंग नहीं है।</p>" if hi else
           "<p class='muted'>Five research candidates, ordered as a contextual editorial shortlist. We have not run one identical lab protocol across all 25 phones, and this is not the site's production performance formula.</p>")
    ranked=[]
    for i,m in enumerate(rows,1):
        note=HINDI_NOTES[m["key"]] if hi else (m["highlight"],m["caution"])
        ranked.append(
            f'<div class="rank"><div class="number">{i}</div><article class="card">'
            f'<h2><a href="{pth(m,hi)}">{esc(display_name(m))}</a></h2>'
            f'<p>{esc(note[0])}</p><p class="muted"><strong>{"कमजोरी:" if hi else "Watch out:"}</strong> {esc(note[1])}</p>'
            f'<p><a class="cta-secondary" href="{pth(m,hi)}">{"पूरी जानकारी" if hi else "See specifications and evidence"}</a></p>'
            f'{seller_links(m,hi)}</article></div>')
    method={
      "overall":("Performance is balanced against camera usefulness, reliable everyday operation, service horizon and endurance. No model gets a bonus for a lower price.","सामान्य कामकाज, बैटरी, कैमरा उपयोगिता और सॉफ्टवेयर सपोर्ट का संतुलन देखा गया है।"),
      "camera":("The independent Moto G57 Power camera review is one anchor; a 3x telephoto on realme 14 Pro+ supports photographic versatility, not a guaranteed better photograph. Evaluate daylight, skin tones, ultrawide, zoom, video stabilization and low-light captures.","Moto G57 Power की टेस्टेड फोटोग्राफी और realme 14 Pro+ का 3x टेलीफोटो अलग ताकतें हैं। रोशनी, रंग और वीडियो को भी देखें।"),
      "gaming":("POCO X7 Pro's Dimensity 8400 Ultra is a leading hardware candidate. Gaming order is conditional on sustained frame stability, thermal data and exact variants; SoC alone is not a measured FPS leaderboard.","POCO X7 Pro का Dimensity 8400 Ultra मजबूत है। वास्तविक FPS, गर्मी और सही RAM वेरिएंट का परीक्षण अलग जरूरी है।"),
      "battery":("A dated 91mobiles PCMark test measured OnePlus N6 at 18.3h and Moto G57 Power at 15.3h under its test conditions. Battery capacity and faster charging do not directly establish identical endurance.","91mobiles के PCMark परीक्षण में OnePlus N6 का 18.3 घंटे और Moto G57 Power का 15.3 घंटे परिणाम दर्ज है। टेस्ट की परिस्थितियाँ महत्वपूर्ण हैं।")
    }
    body=(f'<section class="hero"><div class="eyebrow">{"भारत · उपयोगिता-आधारित चुनाव" if hi else "INDIA · EVIDENCE-LED BUYING PICKS"}</div>'
          f'<h1>{esc(title)}</h1><p class="lead">{esc(description)}</p></section>'
          f'<aside class="notice"><strong>{"जरूरी सूचना" if hi else "Important limitation"}</strong>'
          f'<p>{"किसी भी मॉडल की मौजूदा ₹25,000 कीमत, स्टॉक या विक्रेता का सत्यापन नहीं हुआ है। लिंक पर खुद जाँचें।" if hi else "All models have dated under-budget editorial references; current seller-specific ₹25k pricing, stock and exact memory variants are not verified. Check before buying."}</p></aside>'
          f'{intro}<section><h2>{"श्रेणी की संपादकीय क्रम सूची" if hi else "Category shortlist, in editorial order"}</h2>'
          +''.join(ranked)+'</section>'
          f'<section class="panel"><h2>{"इनका आकलन कैसे किया" if hi else "How these choices were evaluated"}</h2>'
          f'<p>{esc(method[category][1 if hi else 0])}</p>'
          f'<p>{"कीमत का रैंकिंग स्कोर में 0% योगदान है; कीमत केवल बजट सीमा के लिए जाँची जाती है।" if hi else "Price contributes 0% to performance scoring: it only determines whether an exact offer passes the budget ceiling."}</p>'
          f'<p>{"स्रोत: " if hi else "Evidence context: "}'
          f'<a href="{REVIEW}">91mobiles tested picks (12 Oct 2026)</a> · '
          f'<a href="{GADGETS}">Gadgets360 25k shortlist (6 Nov 2026)</a>.</p></section>'
          f'<section class="panel"><h2>{"अभी और मोबाइल देखें" if hi else "Explore all 25 candidates"}</h2>'
          f'<p><a href="{HI if hi else EN}">{"25 मोबाइल रिसर्च पेज" if hi else "Browse the complete 25-model research hub"}</a> · <a href="/compare/">{"सटीक वेरिएंट की तुलना करें" if hi else "Compare exact variants"}</a></p>'
          f'<section class="panel"><h2>{"आम खरीद सवाल" if hi else "Questions people ask before buying"}</h2>'
          f'<h3>{"कैमरा, गेमिंग या बैटरी में किसे चुनें?" if hi else "Should I start with camera, gaming or battery?"}</h3>'
          f'<p>{"अपनी प्राथमिकता वाली गाइड खोलें। ये पेज स्रोत और सीमाएँ दिखाते हैं; समान लैब टेस्ट के बिना अंतिम विजेता घोषित नहीं किया गया है।" if hi else "Start with the priority guide that matches your use. Each guide keeps source context and evidence gaps visible; no final winner is claimed without one identical lab protocol across every model."}</p>'
          f'<p><a href="/seo/camera-phone-buying-guide.html">{"कैमरा गाइड" if hi else "Camera guide"}</a> · <a href="/seo/gaming-phone-buying-guide.html">{"गेमिंग गाइड" if hi else "Gaming guide"}</a> · <a href="/seo/battery-phone-buying-guide.html">{"बैटरी गाइड" if hi else "Battery guide"}</a></p>'
          f'<h3>{"क्या आज की कीमत और स्टॉक सत्यापित हैं?" if hi else "Are today’s price and stock verified?"}</h3>'
          f'<p>{"नहीं। सभी retailer पर सही मॉडल, RAM, स्टोरेज, विक्रेता, वारंटी, पिनकोड और अंतिम कीमत खुद जाँचें।" if hi else "No. Confirm the exact model, RAM, storage, seller, warranty, postcode delivery and final payable price on the retailer before buying."}</p></section>')
    return base_document(path,title,description,body,hi,True,"CollectionPage",
                         [(display_name(m),pth(m,hi)) for m in rows])

def hub_page(data,hi=False):
    title=("₹25,000 से कम के 25 मोबाइल: स्पेसिफिकेशन और तुलना" if hi else
           "25 phones under ₹25,000 in India: model research and priority picks")
    desc=("25 मोबाइल के तकनीकी स्रोत, कमियाँ और 4 जरूरत-आधारित गाइड। Amazon, Flipkart और Croma पर खुद ऑफर चेक करें।" if hi else
          "Compare 25 model-level smartphone research pages for India and read our overall, camera, gaming and battery guides. Exact live prices are not claimed.")
    rows=data["models"]
    sections=[]
    for category,details in CATEGORY_TEXT.items():
        t=details["hi" if hi else "en"][0]
        sections.append('<a class="card" href="'+(HI if hi else EN)+'best-'+category+'/">'
                        '<span class="kicker">'+esc(category)+'</span><h3>'+esc(t)+'</h3>'
                        '<p>'+esc(details["hi" if hi else "en"][1])+'</p></a>')
    cards=[]
    for m in rows:
        status=("मुख्य कैटलॉग में दर्ज" if hi else "In primary research catalogue") if m["primary_catalogue_present"] else ("नया रिसर्च रिकॉर्ड" if hi else "New research intake")
        note=HINDI_NOTES[m["key"]][0] if hi else m["highlight"]
        cards.append('<article class="card"><span class="badge">'+esc(status)+'</span>'
                     '<h3><a href="'+pth(m,hi)+'">'+esc(display_name(m))+'</a></h3>'
                     '<p>'+esc(note)+'</p><a class="cta-secondary" href="'+pth(m,hi)+'">'+("स्रोत और तुलना" if hi else "Specifications and trade-offs")+'</a></article>')
    body=(f'<section class="hero"><div class="eyebrow">{"कूपन वर्ल्ड · स्मार्टफोन रिसर्च" if hi else "COUPON WORLD · PHONE RESEARCH"}</div>'
          f'<h1>{esc(title)}</h1><p class="lead">{esc(desc)}</p></section>'
          f'<aside class="notice"><strong>{"पारदर्शिता" if hi else "Transparent evidence policy"}</strong>'
          f'<p>{"इनमें से 10 मॉडल पुराने 232-मॉडल रिसर्च डेटाबेस में हैं और 15 अलग दर्ज किए गए हैं। किसी मॉडल का आज का दाम/स्टॉक प्रमाणित नहीं है।" if hi else "Of these 25 editorial candidates, 10 already occur in the frozen 232-model research catalogue and 15 are newly registered research intake. This is not 25 verified purchase offers or 25 production performance scores."}</p></aside>'
          f'<section><h2>{"चार जरूरतों की गाइड" if hi else "Start with the four priority guides"}</h2>'
          f'<div class="grid">{"".join(sections)}</div></section>'
          f'<section><h2>{"सभी 25 मॉडल के अलग पेज" if hi else "Individual research pages for all 25 models"}</h2>'
          f'<div class="grid">{"".join(cards)}</div></section>'
          f'<section class="panel"><h2>{"ऑनलाइन खरीद से पहले पाँच बातें" if hi else "Five checks before visiting a retailer"}</h2>'
          f'<ol><li>{"सही 5G मॉडल और निर्माता की पहचान" if hi else "Confirm exact model identity, including 5G suffix."}</li>'
          f'<li>{"RAM, स्टोरेज और कलर का सही वेरिएंट" if hi else "Match physical RAM, storage and colour SKU."}</li>'
          f'<li>{"नए उत्पाद, वारंटी और विक्रेता की जानकारी" if hi else "Check new-versus-refurbished status, warranty and seller."}</li>'
          f'<li>{"अपने पिनकोड का अंतिम देय मूल्य" if hi else "Confirm final payable price and delivery to your postcode."}</li>'
          f'<li>{"सभी तीन रिटेलर पर उपलब्धता की जाँच" if hi else "Compare retailer availability; Croma may not carry every brand."}</li></ol>'
          f'<p>{"स्वतंत्र स्रोत:" if hi else "Independent sources:"} <a href="{GADGETS}">Gadgets360</a> · <a href="{REVIEW}">91mobiles</a>.</p></section>')
    return base_document(HI if hi else EN,title,desc,body,hi,True,"CollectionPage",
                         [(display_name(m),pth(m,hi)) for m in rows])

def save(destination,path,content):
    file=destination/path.lstrip("/")/"index.html"
    file.parent.mkdir(parents=True,exist_ok=True)
    file.write_text(content,encoding="utf-8")

def _link_from_existing_page(destination,src,hi=False):
    p=destination/src.lstrip("/")/"index.html" if src.endswith("/") else destination/src.lstrip("/")
    if not p.is_file():
        return
    body=p.read_text(encoding="utf-8")
    marker=HI if hi else EN
    if marker not in body and "</main>" in body:
        label="₹25,000 तक के 25 मॉडल और सर्वश्रेष्ठ फोन गाइड" if hi else "Explore 25 phones under ₹25,000: best camera, gaming and battery picks"
        link=f'<section class="panel"><h2><a href="{marker}">{esc(label)}</a></h2></section>'
        p.write_text(body.replace("</main>",link+"</main>",1),encoding="utf-8")

def publish_under25(destination:Path)->list[str]:
    data=valid_data()
    coredata=json.loads((destination/"data"/"mobile_research_catalogue.json").read_text(encoding="utf-8"))
    cards={item["model_key"]:item for item in coredata["model_cards"]}
    if len(cards)!=232:
        raise ValueError("Do not replace original 232 primary phone cards")
    lookup={m["key"]:m for m in data["models"]}
    urls=[]
    for hi in (False,True):
        hub=HI if hi else EN
        save(destination,hub,hub_page(data,hi))
        urls.append(BASE+hub)
        for m in data["models"]:
            choices=[r for r in data["models"] if r["key"]!=m["key"]]
            related=sorted(choices,key=lambda x:(x["brand"]!=m["brand"],x["model"]))[:3]
            save(destination,pth(m,hi),model_page(m,related,cards,hi))
            if m["manufacturer_scope"]!="MODEL_NAMING_ALIAS_REQUIRES_REVIEW":
                urls.append(BASE+pth(m,hi))
        for category,keys in data["ranked_categories"].items():
            route=hub+"best-"+category+"/"
            save(destination,route,category_page(category,[lookup[k] for k in keys],data["models"],hi))
            urls.append(BASE+route)
    _link_from_existing_page(destination,"/phones/")
    _link_from_existing_page(destination,"/hi/phones/",hi=True)
    _link_from_existing_page(destination,"/index.html")
    ns="http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("",ns)
    sitemap=destination/"sitemap.xml"
    tree=ET.parse(sitemap)
    root=tree.getroot()
    old={u.text for u in root.findall("{"+ns+"}url/{"+ns+"}loc")}
    for u in urls:
        if u in old:
            raise ValueError("Duplicate sitemap route: "+u)
        node=ET.SubElement(root,"{"+ns+"}url")
        ET.SubElement(node,"{"+ns+"}loc").text=u
        ET.SubElement(node,"{"+ns+"}lastmod").text="2026-11-06"
    tree.write(sitemap,encoding="utf-8",xml_declaration=True)
    print(f"Under-25k pages: 25 models + 4 rankings + hub in EN/HI = 60 routes; indexable {len(urls)}, model identity holds 2.")
    return urls
