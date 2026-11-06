"""Static answers to recovered shopper questions; never a recommendation engine.

Historical semantic groups and the existing intent parser define requirements.
Only an editorially reviewed, distinct answer with sufficient source evidence
can enter the sitemap. Missing-evidence answers remain available but noindex.
No current offers, scores, demand-volume estimates or market-absence claims.
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from xml.etree import ElementTree as ET

from python.intent_engine import parse_query
from python.affiliate_links import amazon_link
from python.phone_research_pages import accepted_specs, eligible, model_title, slug_for, specification_label, specification_value

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://coupon-world.in"
EN, HI = "/answers/", "/hi/answers/"
REVIEWED = "2026-11-06"
HISTORY = ROOT / "data/mobile_historical_query_groups_20261014.csv"
MAKER_HOSTS = {"samsung.com", "news.samsung.com", "apple.com", "support.apple.com", "oneplus.in", "oneplus.com", "mi.com", "po.co", "vivo.com", "vivonewsroom.in", "motorola.in", "motorola.com", "support.motorola.com", "nothing.tech", "in.nothing.tech", "realme.com", "oppo.com", "iqoo.com", "google.com", "store.google.com", "support.google.com", "lava.in", "lavamobiles.com", "infinixmobility.com", "tecno-mobile.com"}

# These are recovered questions, not invented keyword-volume claims.
MEMORY_QUERIES = [
    "mobile under 10000", "mobile under 15000", "mobile under 30000", "mobile under 30 k", "mobile under 30k",
    "5G mobile under 30000", "best camera phone under 15000", "best camera phone under 20000",
    "best camera phone under 30000", "best camera phone under 40000", "Samsung camera phone under 25000",
    "Samsung phone with good camera and battery", "phone under 25000 with AMOLED OIS and 8GB RAM",
    "camera and battery phone under 25000", "phone with clean software", "phone with long updates under 40000",
    "best battery phone under 30000", "best battery phone under 35000", "best battery phone under 50000",
    "12GB 512GB Samsung under 10000", "12GB 256GB phone under 10000",
    "camera phone under 30000 8GB RAM 256GB storage exclude Samsung",
    "phone under 20000 with 8GB RAM 128GB storage AMOLED good camera",
    "Samsung M36 vs Nothing Phone 3a", "Galaxy A36 vs Galaxy A56", "Galaxy A36 8GB 256GB",
    "phone with durable build under 25000", "phone under 30000 upgrade budget 5000",
    "is the second phone battery better", "Samsung A vs OnePlus",
    "phone under 35000", "phone under 40000", "phone under 60000", "phone under 70000",
    "phone under 80000", "phone under 90000", "phone under 100000",
]

# Individually reviewed, distinct shopper decisions. Successful filtering alone
# never turns a generated benchmark permutation into an indexable SEO page.
INDEX_REVIEW_QUERIES = {
    "Samsung phone under 25000", "Samsung nahi chahiye phone under 20000",
    "Redmi nahi chahiye 20k ke andar", "120Hz AMOLED phone under 25000",
    "phone for student under 18000", "phone for office use under 20000",
    "phone under 25000 with AMOLED OIS and 8GB RAM", "5G mobile under 30000",
    "phone with long updates under 40000", "gaming phone under 30000",
    "best battery phone under 35000", "Galaxy A36 vs Galaxy A56",
}

EDITORIAL_TITLES = {
 'samsung phone under 25000':('Samsung phones under ₹25,000: documented options','₹25,000 से कम Samsung फोन: दस्तावेज़ित विकल्प'),
 'samsung nahi chahiye phone under 20000':('Phones under ₹20,000 excluding Samsung','Samsung को छोड़कर ₹20,000 से कम के फोन'),
 'redmi nahi chahiye 20k ke andar':('Phones under ₹20,000 excluding Redmi','Redmi को छोड़कर ₹20,000 से कम के फोन'),
 '120hz amoled phone under 25000':('120 Hz AMOLED phones under ₹25,000','₹25,000 से कम के 120 Hz AMOLED फोन'),
 'phone for student under 18000':('Phones for students under ₹18,000: study-first checks','विद्यार्थियों के लिए ₹18,000 से कम के फोन'),
 'phone for office use under 20000':('Phones for office use under ₹20,000','कार्यालय उपयोग के लिए ₹20,000 से कम के फोन'),
 'phone under 25000 with amoled ois and 8gb ram':('Phones under ₹25,000 with AMOLED, OIS and 8GB RAM','₹25,000 से कम में AMOLED, OIS और 8GB RAM वाले फोन'),
 '5g mobile under 30000':('5G phones under ₹30,000: regional and variant checks','₹30,000 से कम के 5G फोन: सटीक भारतीय वेरिएंट'),
 'phone with long updates under 40000':('Phone update support under ₹40,000: promises and remaining years','₹40,000 से कम फोन में अपडेट समर्थन की जाँच'),
 'gaming phone under 30000':('Gaming phones under ₹30,000: hardware and test evidence','₹30,000 से कम के गेमिंग फोन: हार्डवेयर और परीक्षण'),
 'best battery phone under 35000':('Battery-focused phones under ₹35,000: evidence and trade-offs','₹35,000 से कम में बैटरी प्राथमिकता वाले फोन'),
 'galaxy a36 vs galaxy a56':('Samsung Galaxy A36 5G vs Galaxy A56 5G: sourced comparison','Samsung Galaxy A36 5G बनाम Galaxy A56 5G: स्रोत आधारित तुलना'),
}

# Editorial advice is deliberately topic-specific. Manufacturer specifications
# describe hardware; they are not substitutes for controlled comparative tests.
ADVICE = {
 "camera": (
  "For photographs, check main-camera stabilization, moving subjects, low-light samples and skin tones. For video, inspect supported resolution, stabilization and microphone behaviour on the exact regional model. An OIS label is useful hardware evidence, not proof that one phone takes the best photographs.",
  "तस्वीरों के लिए मुख्य कैमरे का स्थिरीकरण, चलती वस्तु, कम रोशनी और त्वचा के रंग वाले नमूने देखें। वीडियो में रिजोल्यूशन, स्थिरीकरण और माइक्रोफोन का परिणाम जाँचें। OIS एक हार्डवेयर सुविधा है; इससे सर्वश्रेष्ठ तस्वीर का विजेता तय नहीं होता।"),
 "battery": (
  "For time away from a charger, compare measured runtime under a similar workload, screen brightness and network. Capacity is a useful screening fact, but a larger mAh number does not guarantee longer use. For example, vivo's India T4x page lists 6500 mAh with an LCD display; that fact does not establish an AMOLED screen or a runtime win.",
  "चार्जर से दूर उपयोग के लिए समान काम, स्क्रीन ब्राइटनेस और नेटवर्क पर मापा रनटाइम देखें। बड़ी mAh क्षमता लंबे उपयोग की गारंटी नहीं है। vivo के भारतीय T4x पेज पर 6500 mAh और LCD दर्ज है; इससे AMOLED या सबसे लंबी बैटरी लाइफ सिद्ध नहीं होती।"),
 "gaming": (
  "Choose the game, graphics preset and target frame rate first. Then look for a sustained session on the same phone, software version and settings, including heat and battery drain. A fast chipset or 120 Hz panel does not establish 120 FPS support in BGMI. Manufacturer demonstrations and independent measurements must remain separately labelled.",
  "पहले गेम, ग्राफिक्स सेटिंग और लक्षित फ्रेम रेट तय करें। फिर उसी फोन और सॉफ्टवेयर पर लंबे सत्र में FPS, तापमान और बैटरी खपत देखें। तेज चिपसेट या 120 Hz स्क्रीन से BGMI में 120 FPS का समर्थन सिद्ध नहीं होता। निर्माता के प्रदर्शन और स्वतंत्र परीक्षण अलग रखें।"),
 "display": (
  "Keep display technology, refresh rate and outdoor readability separate. AMOLED describes the panel type; Hz describes refresh capability. Peak brightness, automatic sustained brightness and typical brightness are different measurements. A large diagonal also needs an in-hand check of width and weight, particularly for one-handed use.",
  "स्क्रीन का प्रकार, रिफ्रेश रेट और धूप में पढ़ने की क्षमता अलग बातें हैं। AMOLED पैनल का प्रकार है और Hz रिफ्रेश क्षमता बताता है। पीक, सामान्य और ऑटो ब्राइटनेस को एक मान न मानें। एक हाथ से उपयोग के लिए स्क्रीन के विकर्ण के साथ चौड़ाई और वजन भी जाँचें।"),
 "memory": (
  "Physical RAM and internal storage are different requirements. An 8/128 question means 8 GB physical RAM and 128 GB internal storage; RAM expansion is not a replacement. A dated price observation for 8/128 must never admit 8/256 or 12/256 under the same budget. Check the selected SKU, expandable storage and usable space before purchase.",
  "भौतिक RAM और अंदरूनी स्टोरेज अलग जरूरतें हैं। 8/128 का अर्थ 8 GB भौतिक RAM और 128 GB स्टोरेज है; वर्चुअल RAM इसका विकल्प नहीं है। 8/128 की पुरानी कीमत से 8/256 या 12/256 को उसी बजट में शामिल नहीं किया जा सकता। खरीद से पहले चुना SKU और वास्तविक खाली जगह जाँचें।"),
 "software": (
  "Separate operating-system upgrades from security updates and count support from the manufacturer's stated start or end date. Samsung's India A36 documentation specifies six OS generations and six years of security updates; it does not mean six years remain from every purchase date. A 'clean UI' preference needs a current software walkthrough, app-removal check and notification experience, not a chipset score.",
  "OS अपग्रेड और सुरक्षा अपडेट अलग गिनें तथा निर्माता की घोषित शुरुआत या अंतिम तिथि देखें। Samsung के भारतीय A36 दस्तावेज में छह OS पीढ़ियाँ और छह वर्ष सुरक्षा अपडेट हैं; हर खरीद की तारीख से छह वर्ष शेष होने का अर्थ नहीं है। साफ UI के लिए वर्तमान सॉफ्टवेयर, ऐप हटाने और सूचनाओं का अनुभव देखें।"),
 "parents": (
  "For a parent, try the actual calling, contact search, text size, speaker audibility and grip before paying. Android offers separate font-size and display-size controls, but not every app follows every setting. A large screen can improve readability while making a phone harder to hold. Prioritize the person's own comfort, charging routine and nearby service access.",
  "माता-पिता के लिए कॉल, संपर्क खोजना, अक्षरों का आकार, स्पीकर और पकड़ खुद जाँचें। Android में फ़ॉन्ट और डिस्प्ले आकार की अलग सेटिंग हैं; सभी ऐप हर सेटिंग का पालन नहीं करते। बड़ी स्क्रीन पढ़ने में उपयोगी हो सकती है लेकिन पकड़ कठिन भी हो सकती है। उपयोगकर्ता की सुविधा, चार्जिंग आदत और सेवा केंद्र देखें।"),
 "student": (
  "For study, list the required learning apps, video calls, document scans and offline files. Confirm storage for those files, physical RAM for multitasking and a charging plan for the school or college day. A gaming preference should be considered after these essentials. Check repair cost and update support rather than treating extra virtual RAM as a study benefit.",
  "पढ़ाई के लिए जरूरी ऐप, वीडियो कॉल, दस्तावेज स्कैन और ऑफलाइन फाइलों की सूची बनाएं। उनके लिए स्टोरेज, मल्टीटास्किंग की भौतिक RAM और दिनभर की चार्जिंग व्यवस्था देखें। गेमिंग को इन आवश्यकताओं के बाद रखें। अतिरिक्त वर्चुअल RAM के बजाय मरम्मत खर्च और अपडेट समर्थन जाँचें।"),
 "office": (
  "For office use, verify your work-profile or company-device policy, required authentication apps, call quality and document handling. Security support and repair turnaround can matter more than peak gaming speed. Test the keyboard, conferencing app and network where you work; a specification sheet cannot certify call quality or weak-signal reliability at your location.",
  "कार्यालय के लिए कंपनी की डिवाइस नीति, work profile, जरूरी प्रमाणन ऐप, कॉल और दस्तावेज उपयोग जाँचें। सुरक्षा अपडेट और मरम्मत का समय पीक गेमिंग गति से अधिक महत्वपूर्ण हो सकते हैं। अपने कार्यस्थल पर कीबोर्ड, मीटिंग ऐप और नेटवर्क जाँचें; स्पेसिफिकेशन से स्थानीय कॉल गुणवत्ता सिद्ध नहीं होती।"),
 "build": (
  "Treat an IP rating as a defined ingress-protection claim under stated conditions, not a drop-proof or long-term-reliability certificate. Materials, grip, repairability and warranty exclusions need separate checks. Do not turn a manufacturer's durability demonstration into an independent ownership failure rate.",
  "IP रेटिंग को बताई परिस्थितियों में धूल-पानी सुरक्षा का दावा समझें; यह गिरने से सुरक्षा या दीर्घकालिक विश्वसनीयता का प्रमाणपत्र नहीं है। सामग्री, पकड़, मरम्मत और वारंटी अपवाद अलग जाँचें। निर्माता के प्रदर्शन को वास्तविक उपयोग की विफलता दर न मानें।"),
 "charging": (
  "The maximum advertised wattage is not the charging speed throughout a full cycle. Check the supported charging protocol, included adapter and cable, then compare measured 0–50% or 0–100% times under the same conditions. A third-party charger may use a different rate even when its wattage label is higher.",
  "अधिकतम घोषित वॉट पूरे चार्जिंग चक्र की स्थिर गति नहीं है। समर्थित प्रोटोकॉल, बॉक्स के चार्जर और केबल देखें, फिर समान परिस्थितियों में 0–50% या 0–100% का मापा समय मिलाएँ। अधिक वॉट वाला दूसरा चार्जर भी अलग गति दे सकता है।"),
 "connectivity": (
  "A 5G label does not guarantee coverage or speed at your address. Verify the exact India model, supported bands, operator compatibility and SIM behaviour. Keep 4G and 5G phones with similar names separate. Do not infer network capability from a related model or a retailer search headline.",
  "5G लिखे होने से आपके पते पर कवरेज या गति की गारंटी नहीं होती। सटीक भारतीय मॉडल, बैंड, ऑपरेटर और SIM व्यवहार जाँचें। मिलते-जुलते नाम वाले 4G और 5G फोन अलग रखें। दूसरे मॉडल या खोज शीर्षक से नेटवर्क क्षमता न मानें।"),
 "budget": (
  "Use the amount as a strict spending constraint, then choose camera, battery, gaming or software as your priority. Below a cap includes cheaper documented variants. Keep bank-card, exchange and membership conditions separate from an unconditional payable price. A saved reference is useful for research but does not establish today's stock, delivery or cheapest retailer.",
  "राशि को खर्च की सीमा मानें और कैमरा, बैटरी, गेमिंग या सॉफ्टवेयर की प्राथमिकता चुनें। सीमा के नीचे सस्ते दस्तावेज़ित वेरिएंट भी आते हैं। बैंक कार्ड, एक्सचेंज और सदस्यता की शर्तें सामान्य भुगतान राशि से अलग रखें। पुराना मूल्य-संदर्भ आज का स्टॉक, डिलीवरी या सबसे सस्ता विक्रेता सिद्ध नहीं करता।"),
 "comparison": (
  "Name both exact models and memory variants before comparing. Keep the reference phone separate from alternatives that pass the requested budget; the reference itself need not be affordable. Compare model-specific manufacturer fields side by side. Camera points, battery tests and FPS from incompatible protocols cannot be combined into a defensible overall winner.",
  "तुलना से पहले दोनों सटीक मॉडल और RAM/स्टोरेज बताएं। मूल फोन को बजट में आने वाले विकल्पों से अलग रखें; मूल फोन का बजट में होना जरूरी नहीं है। निर्माता के मॉडल-विशिष्ट तथ्य मिलाएँ। अलग परीक्षण पद्धति के कैमरा, बैटरी और FPS को जोड़कर समग्र विजेता तय नहीं किया जा सकता।"),
}

SOURCE_NOTES = [
 ("Samsung India A36 — memory, OIS and update policy", "https://www.samsung.com/in/smartphones/galaxy-a/galaxy-a36-5g-awesome-black-256gb-sm-a366ezkkins/"),
 ("vivo India T4x — LCD, memory and typical battery", "https://www.vivo.com/in/products/param/t4x-5g"),
 ("Nothing India Phone (3a) — camera and regional model", "https://in.nothing.tech/products/phone-3a"),
 ("Xiaomi FAQ — POCO X7 Pro India/global battery distinction", "https://www.mi.com/pk/support/faq/details/KA-522489/"),
 ("Android accessibility — font and display size", "https://support.google.com/accessibility/android/answer/11183305?hl=en-IN"),
]

def esc(value):
    return html.escape(str(value if value is not None else ""), quote=True)

def norm(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()

def brand_key(value):
    key=norm(value)
    return {'xiaomi redmi':'redmi','google pixel':'google'}.get(key,key)

def tokens(value):
    return sorted({x.strip() for x in str(value or "").split(",") if x.strip()})

def number(value):
    return int(float(value)) if value not in (None, "") else None

def maker_url(value):
    u = urlsplit(str(value or ""))
    host = (u.hostname or "").removeprefix("www.")
    return u.scheme == "https" and any(host == h or host.endswith("."+h) for h in MAKER_HOSTS)

def historical_groups():
    with HISTORY.open(encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    if len(rows) != 334 or sum(int(r["Query Count"]) for r in rows) != 1000:
        raise ValueError("Historical coverage source must retain 334 groups / 1000 wordings")
    return [dict(id=r["Protected Group ID"], query=r["Example Query"], action=r["Intent Action"],
                 lower=number(r["Budget Min"]), cap=number(r["Budget Max"]), brands=tokens(r["Brand Filter"]),
                 must=tokens(r["Must Have"]), preferred=tokens(r["Preferred"]), avoid=tokens(r["Avoid"]),
                 target=r["Target Model"], persona=r["Persona"], qualifier=r["Extra Qualifier"],
                 query_ids=tokens(r["Query IDs"]), source="historical-canonical-20261014", reviewed=False)
            for r in rows]

def parsed_group(q, identifier):
    p = parse_query(q)
    group = dict(id=identifier, query=q, action="comparison" if p.get("compare") else "recommendation",
                lower=p.get("budget_min"), cap=p.get("budget_max"), brands=p.get("brands") or [],
                must=p.get("must_have") or [], preferred=p.get("preferred") or [], avoid=p.get("avoid") or [],
                target=p.get("exact_model") or "", persona=p.get("user_profile") or "", qualifier="",
                query_ids=[identifier], source="recovered-mobile-question", reviewed=True)
    # Editorial interpretation of recovered literal questions. This does not
    # modify the runtime parser, recommendation engine or scoring policy.
    if re.search(r"amoled",q,re.I) and not re.search(r"amoled\s+prefer|prefer\w*\s+amoled",q,re.I):
        group['must']=sorted(set(group['must']+['amoled_display']))
        group['preferred']=[x for x in group['preferred'] if x!='amoled_display']
    if re.search(r'\bois\b',q,re.I) and not re.search(r'prefer\w*\s+ois|ois\s+prefer',q,re.I):
        group['must']=sorted(set(group['must']+['ois']))
        group['preferred']=[x for x in group['preferred'] if x!='ois']
    if norm(q)=='galaxy a36 8gb 256gb':group['target']='galaxy a36 5g'
    pair_questions={
        'samsung m36 vs nothing phone 3a':['samsung|galaxy m36 5g','nothing|phone 3a'],
        'galaxy a36 vs galaxy a56':['samsung|galaxy a36 5g','samsung|galaxy a56 5g'],
    }
    group['pair']=pair_questions.get(norm(q),[])
    return group

def signature(g):
    fields = {k:g[k] for k in ("action", "lower", "cap", "brands", "must", "preferred", "avoid", "target", "persona", "qualifier")}
    fields['pair']=g.get('pair',[])
    for k in ("brands", "must", "preferred", "avoid"):
        fields[k] = sorted(norm(x) for x in fields[k])
    return json.dumps(fields, sort_keys=True)

def load_groups():
    groups = historical_groups()
    rows = json.loads((ROOT/"data/mobile_query_benchmark_phase3.json").read_text())
    rows += [{"id":"S"+r["id"], "q":r["query"]} for r in json.loads((ROOT/"data/mobile_search_benchmark.json").read_text())]
    rows += [{"id":f"MEM{i:03}", "q":q} for i,q in enumerate(MEMORY_QUERIES,1)]
    by_signature = {signature(g):g for g in groups}
    for r in rows:
        g = parsed_group(r["q"], r["id"])
        key = signature(g)
        if key in by_signature:
            existing = by_signature[key]
            existing.setdefault("aliases",[]).append(g["query"])
            existing["query_ids"] += g["query_ids"]
            existing["reviewed"] = True
        else:
            groups.append(g)
            by_signature[key]=g
    for g in groups:
        g["slug"] = re.sub(r"[^a-z0-9]+", "-", g["query"].lower()).strip("-")[:100] or g["id"].lower()
    seen = set()
    for g in groups:
        if g["slug"] in seen:
            g["slug"] += "-"+g["id"].lower()
        seen.add(g["slug"])
    return groups

def spec(card, *keys):
    for key in keys:
        item=(card.get("specifications") or {}).get(key)
        if item and maker_url(item.get("source_url")):
            return item.get("value")
    return None

def documented(card):
    return len([(k,v) for k,v in accepted_specs(card) if maker_url(v.get("source_url"))]) >= 8

def supported(card, ref, feature):
    f = feature.lower().replace("good_", "").replace("strong_", "")
    m=re.fullmatch(r"(\d+)gb_(ram|storage)", f)
    if m:
        return ref.get("ram_gb" if m[2]=="ram" else "storage_gb")==int(m[1])
    m=re.fullmatch(r"(\d+)mah_battery", f)
    if m:
        v=spec(card,"battery_mah_typical")
        return isinstance(v,(int,float)) and v >= int(m[1])
    if f=="ois":
        return str(spec(card,"ois")).casefold() in {"yes","true","supported"}
    if f in {"amoled_display","oled_display"}:
        return "oled" in str(spec(card,"display_type","display_type_description")).lower()
    m=re.fullmatch(r"(\d+)hz_display",f)
    if m:
        v=spec(card,"display_refresh_max_hz")
        return isinstance(v,(int,float)) and v>=int(m[1])
    if f=="5g":
        return "5g" in str(spec(card,"network_support")).lower()
    if f.startswith("brand_"):
        return brand_key(card["brand"])==brand_key(f[6:])
    # A subjective preference is never admitted as a hard proven capability.
    return False

def topic(g):
    t=norm(g["query"]+" "+" ".join(g["preferred"]+g["must"]))
    if "compar" in g["action"] or " vs " in " "+t+" ": return "comparison"
    if g["persona"] in {"parent","parents"} or re.search(r"father|mother|parents|simple phone",t): return "parents"
    if re.search(r"student|college",t):return "student"
    if re.search(r"office",t):return "office"
    if re.search(r"battery more important|battery pe compromise|battery priority",t):return "battery"
    if re.search(r'gaming nahi|gaming nahin|not gaming',t) and 'camera' in t:return 'camera'
    if re.search(r"gaming|game|processor|bgmi",t):return "gaming"
    if re.search(r"camera|photograph|ois",t):return "camera"
    if re.search(r"battery|mah",t):return "battery"
    if re.search(r"charging",t):return "charging"
    if re.search(r"software|updates|clean ui",t):return "software"
    if re.search(r"durab|build|reliab",t):return "build"
    if re.search(r"ram|storage|8 128|12 256",t):return "memory"
    if re.search(r"display|amoled|compact|screen",t):return "display"
    if "5g" in t:return "connectivity"
    return "budget"

def hardware_key(card):
    # The existing source records use both labels for this exact POCO model.
    # Xiaomi's regional FAQ explicitly distinguishes its India battery.
    if card.get('model_key') in {'poco|x7 pro','poco|x7 pro 5g'}:
        return 'poco|x7pro'
    return (card.get('research_budget_reference') or {}).get('hardware_group_key')

def regional_records(cards):
    """Prefer an existing reviewed record for the same evidenced hardware/SKU.

    Never combine fields between records. If regional fields conflict and no
    reviewed representative exists, withhold that hardware family entirely.
    """
    families={}
    independent=[]
    for card in cards:
        ref=card.get('research_budget_reference') or {}
        key=hardware_key(card)
        if key:families.setdefault(key,[]).append(card)
        else:independent.append(card)
    for family in families.values():
        approved=[c for c in family if eligible(c)]
        if approved:
            independent.extend(approved)
            continue
        conflict=any(len({str(spec(c,key)) for c in family if spec(c,key) is not None})>1 for key in ('battery_mah_typical','display_resolution','display_inches'))
        if not conflict:independent.extend(family)
    return independent

def candidates(g, cards):
    out=[]
    avoid={brand_key(x.removeprefix("brand_")) for x in g["avoid"] if x.startswith("brand_")}
    soft_brands={brand_key(x[6:]) for x in g["preferred"] if x.startswith("brand_")}
    allowed={brand_key(x) for x in g["brands"]}-avoid-soft_brands
    for c in regional_records(cards):
        if not documented(c):continue
        if brand_key(c["brand"]) in avoid:continue
        if allowed and brand_key(c["brand"]) not in allowed:continue
        ref=c.get("research_budget_reference") or {}
        if re.search(r"OUT.OF.STOCK|UNAVAILABLE|SOLD.OUT|DISCONTINUED", str(ref.get('stock_indication','')),re.I):continue
        if g.get('pair') and c['model_key'] not in g['pair']:continue
        if g["cap"] is not None:
            price=ref.get("reference_price_inr")
            if not isinstance(price,(int,float)) or not ref.get("checked_at") or ref.get("live_offer") is not False or ref.get("ranking_weight")!=0:continue
            if not price < g["cap"] or (g["lower"] is not None and price<g["lower"]):continue
        if not all(supported(c,ref,f) for f in g["must"]):
            if g['cap'] is not None:continue
            # A no-budget exact-variant question may use an already frozen
            # manufacturer-verified variant. Clear the unrelated price record;
            # NEVER transfer the 8/128 price to the frozen 8/256 variant.
            variants=[v for v in c.get('_frozen_variants',[]) if all(supported(c,v,f) for f in g['must'])]
            if not variants:continue
            c=dict(c)
            c['research_budget_reference']={**variants[0], 'variant_basis':'FROZEN_VERIFIED_NO_PRICE'}
        if g["target"]:
            equal=norm(c["model"])==norm(g["target"]) or norm(model_title(c))==norm(g["target"])
            if g["action"]=="compare_against_model":
                if equal:continue
            elif not equal:continue
        out.append(c)
    # Source/research examples only, alphabetically grouped. No performance sort.
    unique={}
    for c in sorted(out,key=lambda c:model_title(c).casefold()):
        ref=c.get('research_budget_reference') or {}
        hardware=hardware_key(c) or norm(model_title(c))
        unique.setdefault((hardware,ref.get('ram_gb'),ref.get('storage_gb')),c)
    return list(unique.values())

def needs_clarification(g):
    q=g["query"].lower()
    return (g["action"]=="comparison" and not g.get("target") and not g.get('pair')) or "second phone" in q or "upgrade budget" in q

def description(g, rows, hi=False):
    if needs_clarification(g):
        return ("तुलना का सही जवाब देने के लिए दोनों सटीक मॉडल, RAM/स्टोरेज और प्राथमिकता जरूरी हैं। केवल सीरीज़ या ‘दूसरा फोन’ से निष्पक्ष विजेता तय नहीं हो सकता।" if hi else "A defensible comparison needs both exact models, memory variants and your priority. A series name or 'the second phone' is insufficient to identify a winner.")
    if g["action"]=="named_model_price_deal":
        return ("इस शोध रिकॉर्ड से आज की कीमत या सबसे सस्ता विक्रेता प्रमाणित नहीं है। नीचे निर्माता के तथ्य और स्वतंत्र विक्रेता खोज हैं; सटीक वेरिएंट, शर्तें और अंतिम कीमत वहाँ जाँचें।" if hi else "This research record does not certify today's price or a cheapest seller. The sourced facts and independent retailer searches below help check the exact variant, conditions and final payable price.")
    if g['action'] in {'named_model_camera_review','named_model_gaming_review','named_model_buy_decision'}:
        return ('इस रिकॉर्ड में निर्माता के तथ्य उपलब्ध हो सकते हैं, लेकिन नियंत्रित कैमरा/गेमिंग श्रेष्ठता या आज इसे खरीदने का निष्कर्ष प्रमाणित नहीं है। नीचे सही मॉडल के तथ्य और बाकी जाँच देखें।' if hi else 'Manufacturer facts may be documented, but this record does not certify controlled camera/gaming superiority or that buying this model today is the right decision. The exact model facts and remaining checks are shown below.')
    if g.get('pair'):
        return ('दोनों नामित मॉडल के उपलब्ध तथ्य नीचे दिए हैं। अधूरी जानकारी स्पष्ट रखी गई है; समान स्वतंत्र परीक्षण के बिना विजेता नहीं चुना गया है।' if hi else 'Available manufacturer facts for the two named models are shown below. Missing evidence remains explicit; no winner is selected without comparable independent tests.')
    if re.search(r'compact|clean ui|clean software|latest|good reviews', g['query'], re.I):
        return ('इस प्रश्न की कॉम्पैक्ट आकार, साफ सॉफ्टवेयर, नवीनतम मॉडल या अच्छे अनुभव वाली विशेष पसंद को इस रिकॉर्ड से प्रमाणित नहीं किया गया है। नीचे केवल बजट और अनिवार्य हार्डवेयर की जाँच है; इसे उस पसंद का प्रमाणित जवाब न मानें।' if hi else 'The requested compact handling, clean-software experience, latest-model status or review quality is not established by this record. The examples below only pass the budget and mandatory hardware checks; they do not certify that subjective preference.')
    if not rows:
        return ("इस सवाल की सभी अनिवार्य शर्तों के लिए हमारे दस्तावेज़ित रिकॉर्ड में पर्याप्त मेल नहीं मिला। इसका अर्थ भारत में ऐसा फोन नहीं बिकता, यह नहीं है। कोई सस्ता या दूसरे वेरिएंट का फोन चुपचाप विकल्प नहीं बनाया गया है।" if hi else "Our documented records do not establish a sufficient match for all mandatory conditions in this question. This is not proof that no such phone is sold in India. The budget, brand and exact-memory conditions have not been silently relaxed.")
    names=", ".join(model_title(c) for c in rows[:3])
    prefix=('इस रिकॉर्ड से सर्वश्रेष्ठ प्रदर्शन वाला फोन प्रमाणित नहीं है। ' if hi else 'A best-performing phone is not established by this record. ') if re.search(r'best|achha|acha|mast|important|priority',g['query'],re.I) else ''
    return prefix+(f"{names} जैसे {len(rows)} दस्तावेज़ित शोध विकल्प नीचे की अनिवार्य शर्तों के दायरे में हैं। यह प्रदर्शन रैंकिंग या आज उपलब्ध ऑफर की सूची नहीं है। प्राथमिकता की मापी श्रेष्ठता अलग से प्रमाणित करनी होगी।" if hi else f"Documented research examples include {names}; {len(rows)} records satisfy the mandatory evidence filters below. These are not performance-ranked winners or verified current offers. Priority preferences still require the stated checks.")

def constraints(g,hi):
    def readable(value):
        names={
            'amoled_display':('AMOLED display','AMOLED स्क्रीन'),
            'ois':('Optical image stabilization (OIS)','ऑप्टिकल इमेज स्थिरीकरण (OIS)'),
            'good_camera':('Camera quality preference','कैमरा गुणवत्ता की पसंद'),
            'good_battery':('Battery-life preference','बैटरी चलने की पसंद'),
            'strong_gaming_performance':('Gaming performance preference','गेमिंग प्रदर्शन की पसंद'),
            'clean_ui':('Clean software experience','साफ सॉफ्टवेयर अनुभव'),
            'easy_to_use':('Ease of use','उपयोग में आसानी'),
            'large_display':('Large display preference','बड़ी स्क्रीन की पसंद'),
            'compact_phone':('Compact handling preference','छोटे आकार और पकड़ की पसंद'),
        }
        if value in names:return names[value][int(hi)]
        m=re.fullmatch(r'(\d+)gb_(ram|storage)',value)
        if m:return f'{m[1]}GB '+(('भौतिक RAM' if hi else 'physical RAM') if m[2]=='ram' else ('अंदरूनी स्टोरेज' if hi else 'internal storage'))
        if value.startswith('brand_'):return value[6:].title()
        return value.replace('_',' ').replace('|',' / ')
    fields=[]
    if g["cap"] is not None:fields.append(("सख्त ऊपरी सीमा" if hi else "Strict budget cap",f'Below INR {g["cap"]:,}'))
    if g["lower"] is not None:fields.append(("न्यूनतम सीमा" if hi else "Inclusive lower bound",f'INR {g["lower"]:,}'))
    for key,en,hn in [("brands","Brand scope (subject to preferences/exclusions)","ब्रांड दायरा"),("must","Mandatory requirements","अनिवार्य शर्तें"),("preferred","Preferences; not proven superiority","पसंद; श्रेष्ठता प्रमाणित नहीं"),("avoid","Excluded requirements","बहिष्कृत शर्तें"),("target","Reference model","मूल मॉडल"),("persona","Use case","उपयोग"),("qualifier","Additional question","अतिरिक्त जरूरत")]:
        value=g[key]
        if value:fields.append((hn if hi else en, ", ".join(readable(x) for x in value) if isinstance(value,list) else readable(value)))
    if g.get('pair'):fields.append(('तुलना के मॉडल' if hi else 'Explicit comparison models',', '.join(readable(x) for x in g['pair'])))
    return '<dl>'+''.join(f'<dt>{esc(k)}</dt><dd>{esc(v)}</dd>' for k,v in fields)+'</dl>'

def model_card(card,hi=False):
    ref=card.get("research_budget_reference") or {}
    fields=[(k,v) for k,v in accepted_specs(card) if maker_url(v.get("source_url"))]
    order={k:i for i,k in enumerate(("chipset","display_type","display_inches","display_refresh_max_hz","rear_main_mp","ois","battery_mah_typical","wired_charging_max_w","os_upgrade_generations","security_support_years","network_support","ip_rating"))}
    fields.sort(key=lambda kv:order.get(kv[0],100))
    cells=''.join(f'<tr><th scope="row">{esc(specification_label(k,v))}</th><td>{esc(specification_value(k,v))}</td><td><a href="{esc(v["source_url"])}" rel="noopener noreferrer" target="_blank">{"निर्माता स्रोत" if hi else "Manufacturer source"}</a></td></tr>' for k,v in fields[:10])
    memory=(f'{ref["ram_gb"]}GB RAM / {ref["storage_gb"]}GB storage' if ref.get("ram_gb") and ref.get("storage_gb") else ("वेरिएंट का बजट प्रमाण उपलब्ध नहीं" if hi else "No exact-memory budget reference"))
    links=[]
    for item in card.get("retailer_search_links") or []:
        url=amazon_link(str(item.get("url") or ""))
        if urlsplit(url).hostname not in {"www.amazon.in","www.flipkart.com","www.croma.com"}:continue
        label=("Browse Croma category" if item["retailer"]=="Croma" else "Search "+item["retailer"])
        links.append(f'<a href="{esc(url)}" rel="sponsored nofollow noopener noreferrer" target="_blank">{esc(label)}</a>')
    dates=sorted({str(v.get("checked_at") or v.get("checked_date") or "") for _,v in fields if v.get("checked_at") or v.get("checked_date")})
    dates_text=", ".join(dates) or str(card.get("research_checked_at") or "Not recorded")
    ref_link=(f'<a href="{esc(amazon_link(ref["source_url"]))}" rel="sponsored nofollow noopener noreferrer" target="_blank">Dated retailer evidence (not a current offer)</a>' if str(ref.get('source_url','')).startswith('https://') else '')
    return (f'<article class="answer-model"><h3>{esc(model_title(card))}</h3><p>{esc(memory)}</p>'
            f'<p>{"बजट प्रमाण जाँच" if hi else "Budget evidence checked"}: {esc(ref.get("checked_at") or "Not available")}. '
            f'{"स्पेक रिकॉर्ड जाँच" if hi else "Saved specification checks"}: {esc(dates_text)}. {ref_link}</p>'
            '<div class="table-wrap"><table><caption>Manufacturer-linked model facts; exact India SKU still requires confirmation</caption><thead><tr><th>Field</th><th>Value</th><th>Evidence</th></tr></thead><tbody>'+cells+'</tbody></table></div>'
            '<p class="retail">'+" · ".join(links)+'</p><p>'
            + ("ये खोज/ब्राउज़ लिंक हैं, सटीक ऑफर नहीं। Croma सामान्य श्रेणी खोल सकता है। कीमत, मेमोरी, स्टॉक और डिलीवरी विक्रेता पर जाँचें।" if hi else "Search/browse destinations, not verified exact offers. Croma may open a general category. Confirm memory, price, stock and delivery at the retailer.")+'</p></article>')

def route(g,hi=False):
    return (HI if hi else EN)+g["slug"]+"/"

def save(dest,path,text):
    target=dest/path.lstrip('/')/'index.html'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(text,encoding="utf-8")

def document(title,body,path,hi,indexed,canonical=None):
    other=path.removeprefix('/hi') if hi else '/hi'+path
    canon=SITE+(canonical or path)
    robots="index,follow,max-image-preview:large" if indexed else "noindex,follow"
    schema={"@context":"https://schema.org","@type":"WebPage","name":title,"url":canon,"inLanguage":"hi-IN" if hi else "en-IN","dateModified":REVIEWED}
    return f'''<!doctype html><html lang="{"hi-IN" if hi else "en-IN"}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} | Coupon World</title><meta name="description" content="{esc(title)} — sourced facts, exact requirements, dated budget evidence and the limits of what can be concluded."><meta name="robots" content="{robots}"><link rel="canonical" href="{esc(canon)}"><link rel="alternate" hreflang="{"hi-IN" if hi else "en-IN"}" href="{esc(SITE+path)}"><link rel="alternate" hreflang="{"en-IN" if hi else "hi-IN"}" href="{esc(SITE+other)}"><link rel="stylesheet" href="/assets/phone-guides.css"><link rel="stylesheet" href="/assets/query-answers.css"><script type="application/ld+json">{json.dumps(schema,ensure_ascii=False).replace('<','\\u003c')}</script></head><body><a class="skip" href="#main">{"मुख्य सामग्री" if hi else "Skip to content"}</a><header><nav aria-label="Main navigation"><a href="/">Coupon World</a><a href="{HI if hi else EN}">{"मोबाइल सवाल" if hi else "Phone questions"}</a><a href="{other}">{"English" if hi else "हिंदी"}</a><a href="/#mobileResearchSearch">Find a phone</a></nav></header><main id="main"><p class="eyebrow">COUPON WORLD / SOURCE-LINKED ANSWERS</p>{body}</main><footer><p><a href="/guides/about-coupon-world/">About our research and corrections</a> · <a href="/seo/phone-research-evidence-method.html">Evidence method</a></p><p>Prepared with AI assistance from saved manufacturer-source research. No hands-on testing or current offer is certified. As an Amazon Associate I earn from qualifying purchases.</p></footer></body></html>'''

def publish_answers(destination):
    dest=Path(destination)
    cards=json.loads((dest/'data/mobile_research_catalogue.json').read_text())["model_cards"]
    frozen={p['canonical_product_id']:p for p in json.loads((dest/'data/mobile_research_preview.json').read_text())['products']}
    for card in cards:
        card['_frozen_variants']=[{'ram_gb':frozen[k]['ram_gb'],'storage_gb':frozen[k]['storage_gb']} for k in card.get('frozen_variant_ids',[]) if k in frozen]
    groups=load_groups()
    ledger=[]
    seen_evidence=set()
    for g in groups:
        rows=[] if needs_clarification(g) else candidates(g,cards)
        curated=[c for c in rows if eligible(c)]
        # Only manually recovered/reviewed intent topics with substantial
        # manufacturer evidence can be indexed. Historical permutations alone
        # are NOT an editorial publication approval.
        reviewed=any(norm(q) in {norm(g['query']),*(norm(q) for q in g.get('aliases',[]))} for q in INDEX_REVIEW_QUERIES)
        indexed=reviewed and len(curated)>=2 and not needs_clarification(g) and not g["qualifier"] and not g["action"].startswith("named_model")
        evidence_key=(topic(g),tuple(c['model_key'] for c in rows[:6]),tuple(g['must']),tuple(g['avoid']),g['persona'])
        if evidence_key in seen_evidence:indexed=False
        if indexed:seen_evidence.add(evidence_key)
        # Existing budget / ranked-category pages already own these intents.
        cap=g["cap"]
        simple=not any(g[k] for k in ('brands','must','preferred','avoid','target','persona','qualifier'))
        existing=f'/seo/phones-under-{cap}.html' if simple and cap in {10000,15000,20000,30000,50000} else None
        if simple and cap==25000:existing='/phones/under-25000/'
        if norm(g['query']) in {'best camera phone under 25000','gaming phone 25k tak','best phone 25000 tak'}:
            existing='/phones/under-25000/'+('best-camera/' if 'camera' in g['query'] else 'best-gaming/' if 'gaming' in g['query'] else '')
        if norm(g['query']) in {'samsung','oneplus','motorola phone'}:existing='/phones/'
        if existing:indexed=False
        for hi in (False,True):
            title=("मोबाइल सवाल: "+g['query']) if hi else g['query'][0].upper()+g['query'][1:]+" — evidence answer"
            if g['query'].lower() in EDITORIAL_TITLES:title=EDITORIAL_TITLES[g['query'].lower()][int(hi)]
            answer=description(g,rows,hi)
            body=f'<h1>{esc(title)}</h1><p class="byline">Coupon World editorial research · Answer reviewed {REVIEWED}</p><section class="quick-answer"><h2>{"सीधा जवाब" if hi else "Direct answer"}</h2><p>{esc(answer)}</p></section>'
            body+=f'<section><h2>{"इस सवाल की शर्तें" if hi else "What this answer does and does not require"}</h2>'+constraints(g,hi)+'</section>'
            if g['action']=='compare_against_model':
                targets=[c for c in cards if norm(c['model'])==norm(g['target']) and documented(c)]
                body+='<section><h2>Reference phone (not certified within this budget)</h2>'+(''.join(model_card(c,hi) for c in targets[:1]) or '<p>The reference model lacks sufficient manufacturer-linked fields in this record. No comparison winner is asserted.</p>')+'</section>'
            body+=f'<section><h2>{"चुनाव का व्यावहारिक तरीका" if hi else "How to make this particular decision"}</h2><p>{esc(ADVICE[topic(g)][int(hi)])}</p></section>'
            if rows:
                body+=f'<section><h2>{"दस्तावेज़ित विकल्प और सीमाएँ" if hi else "Documented examples and their limits"}</h2><p>{len(rows)} records; displaying {min(len(rows),6)}, alphabetically. Preference satisfaction and performance superiority are not certified.</p>'+''.join(model_card(c,hi) for c in rows[:6])+'</section>'
                if g.get('pair'):
                    missing=set(g['pair'])-{c['model_key'] for c in rows}
                    if missing:body+='<p>Comparison model without sufficient source fields: '+esc(', '.join(sorted(missing)))+'. No substitute model has been selected.</p>'
            else:
                body+='<section><h2>What is missing before a recommendation is defensible</h2><p>We need a manufacturer-linked exact model, a dated price reference for the requested memory configuration, and evidence for every mandatory feature. A zero-result research snapshot is not a nationwide availability finding.</p></section>'
            body+='<section><h2>'+('खरीद से पहले अंतिम जाँच' if hi else 'Before paying')+'</h2><p>'+esc(ADVICE['budget'][int(hi)])+'</p><p>'+('मूल्य का प्रदर्शन स्कोर में भार 0% है। स्पेसिफिकेशन, स्वतंत्र परीक्षण और विक्रेता के ऑफर अलग प्रमाण हैं।' if hi else 'Price has 0% weight in performance scoring. Manufacturer specifications, independent tests and retailer offers answer different questions.')+'</p></section>'
            body+='<section><h2>Source context reviewed for this guide</h2><p>These background source checks do not refresh every saved specification or price date in the model tables.</p><ul>'+''.join(f'<li><a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)}</a></li>' for label,url in SOURCE_NOTES)+'</ul></section>'
            if existing:
                body+=f'<p><a href="{("/hi" if hi else "")+existing}">Read the established budget guide</a></p>'
            if not indexed:
                body+='<p class="note">Research limitations remain: some evidence is incomplete, or a dedicated buying guide already covers this decision. Use the original sources and check the exact variant before choosing.</p>'
            save(dest,route(g,hi),document(title,body,route(g,hi),hi,indexed))
        ledger.append(dict(group_id=g['id'],question=g['query'],aliases=g.get('aliases',[]),query_ids=g['query_ids'],route=route(g),hindi_route=route(g,True),indexable=indexed,matched_model_keys=[c['model_key'] for c in rows],mandatory=g['must'],preferred=g['preferred'],price_weight=0,live_offer=False,status='INDEXABLE_RESEARCH_ANSWER' if indexed else 'NOINDEX_EVIDENCE_OR_DUPLICATE_HOLD',existing_intent_page=existing))
    # The public directory is a curated navigation aid, not a keyword dump.
    for hi in (False,True):
        links=''.join(f'<li><a href="{x["hindi_route"] if hi else x["route"]}">{esc(x["question"])}</a></li>' for x in ledger if x['indexable'])
        title='मोबाइल खरीदने के सवाल और स्रोत-आधारित जवाब' if hi else 'Phone buying questions, answered with evidence'
        body=f'<h1>{title}</h1><p>Start with a concrete buying question. These answers keep mandatory conditions, preferences, dated references and unknowns visible. They do not claim live prices, a tested best phone or measured search volume.</p><p>Reviewed {REVIEWED} · <a href="/phones/">Source-linked models</a> · <a href="/compare/">Model comparisons</a></p><ul>{links}</ul><p><a href="{HI if hi else EN}coverage/">Question coverage and evidence gaps</a></p>'
        save(dest,HI if hi else EN,document(title,body,HI if hi else EN,hi,True))
        table=''.join(f'<tr><td><a href="{x["hindi_route"] if hi else x["route"]}">{esc(x["question"])}</a></td><td>{len(x["matched_model_keys"])}</td><td>{"Reviewed research answer" if x["indexable"] else "Evidence gap or existing guide"}</td></tr>' for x in ledger)
        body='<h1>Question coverage and evidence gaps</h1><p>The recovered historical file contains 334 groups representing 1,000 wordings. Additional benchmark and remembered questions are reconciled by semantic requirements. The separate synthetic regression corpus and advertising keyword permutations are not evidence of search demand or automatic page-publication targets.</p><div class="table-wrap"><table><thead><tr><th>Question</th><th>Documented matches</th><th>Index status</th></tr></thead><tbody>'+table+'</tbody></table></div>'
        path=(HI if hi else EN)+'coverage/'
        save(dest,path,document('Question coverage',body,path,hi,False))
    ns='http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('',ns)
    tree=ET.parse(dest/'sitemap.xml');root=tree.getroot()
    urls={n.text for n in root.iter('{'+ns+'}loc')}
    paths=[EN,HI]+[x[k] for x in ledger if x['indexable'] for k in ('route','hindi_route')]
    for path in paths:
        if SITE+path in urls:raise ValueError('Duplicate answer sitemap URL')
        node=ET.SubElement(root,'{'+ns+'}url');ET.SubElement(node,'{'+ns+'}loc').text=SITE+path
        ET.SubElement(node,'{'+ns+'}lastmod').text=REVIEWED
    tree.write(dest/'sitemap.xml',encoding='utf-8',xml_declaration=True)
    report={'reviewed_on':REVIEWED,'historical_groups':334,'historical_wordings':1000,'answer_groups':len(ledger),'indexable_groups':sum(x['indexable'] for x in ledger),'noindex_groups':sum(not x['indexable'] for x in ledger),'ranking_price_weight':0,'live_offers_admitted':0,'answers':ledger}
    (dest/'data/mobile_query_answer_coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    homepage=dest/'index.html';text=homepage.read_text();text=text.replace('</main>','<section class="container"><h2><a href="/answers/">Phone buying questions, answered with evidence</a></h2><p>Exact requirements, documented alternatives and clearly explained evidence gaps.</p></section></main>');homepage.write_text(text)
    print(f'Question answers: {len(ledger)} EN/HI groups; {report["indexable_groups"]} indexable, {report["noindex_groups"]} held noindex')
    return report
