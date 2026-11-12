"""Render the curated phone-guide collection; never generate offers or scores."""
import html
import json
from pathlib import Path
from urllib.parse import urlencode

from python.page_feedback import markup as feedback_markup
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://coupon-world.in'
HUB = '/guides/phone-budget-guides/'

def esc(value):
    return html.escape(str(value), quote=True)

def budget_examples(destination, guide, hindi=False):
    import re
    from python.phone_research_pages import eligible, model_title, slug_for, summary_fields
    match = re.fullmatch(r"phones-under-(\d+)", guide["slug"])
    if not match:
        return ""
    cap = int(match[1])
    catalogue = json.loads((Path(destination) / "data/mobile_research_catalogue.json").read_text(encoding="utf-8"))
    selected = []
    for card in catalogue["model_cards"]:
        ref = card.get("research_budget_reference") or {}
        price = ref.get("reference_price_inr")
        if eligible(card) and isinstance(price, (int, float)) and 0 < price < cap and ref.get("checked_at"):
            selected.append(card)
    selected.sort(key=lambda c: model_title(c).casefold())
    if not selected:
        return ""
    heading = "शोध शुरू करने के लिए मॉडल" if hindi else "Models to start researching"
    note = ("पुरानी कीमत के प्रमाण पर आधारित उदाहरण; नाम के क्रम में, प्रदर्शन रैंकिंग नहीं। आज की कीमत और सटीक RAM/स्टोरेज विक्रेता पर जाँचें।" if hindi else
            "Examples with dated budget evidence, in alphabetical order, not a performance ranking. Confirm today’s price and exact RAM/storage at the retailer. Prices do not affect performance scores.")
    parts = []
    for card in selected[:6]:
        title = model_title(card)
        path = ("/hi" if hindi else "") + "/phones/" + slug_for(card) + "/"
        facts = " · ".join(f"{esc(k)}: {esc(v)}" for k,v in summary_fields(card, 3))
        ref = card["research_budget_reference"]
        date_label = "बजट प्रमाण की जाँच" if hindi else "Budget evidence checked"
        date = esc(ref["checked_at"])
        parts.append(f'<li><h3><a href="{path}">{esc(title)}</a></h3><p>{facts}</p><p>{date_label}: {date}. '
                     + ("सीमा: वास्तविक बैटरी रनटाइम और कैमरा गुणवत्ता सिर्फ इन आँकड़ों से तय नहीं होते।" if hindi else "Trade-off to check: these specifications do not establish real battery runtime or camera quality.")
                     + '</p></li>')
    return f'<section class="budget-examples"><h2>{heading}</h2><p>{note}</p><ul>'+"".join(parts)+'</ul></section>'


def render_phone_guides(destination):
    data = json.loads((ROOT / 'data/phone-guides.json').read_text(encoding="utf-8"))
    pages = data['pages']
    if len(pages) != 20 or len({p['slug'] for p in pages}) != 20:
        raise ValueError('curated guide set must have 20 distinct topics')
    def document(title, description, path, content, schema):
        return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(title)} | Coupon World</title><meta name="description" content="{esc(description)}"><meta name="robots" content="index,follow,max-image-preview:large"><link rel="canonical" href="{BASE+path}"><link rel="alternate" hreflang="en-IN" href="{BASE+path}"><link rel="alternate" hreflang="hi-IN" href="{BASE}/hi{path}"><meta property="og:type" content="article"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{BASE+path}"><meta property="og:image" content="{BASE}/assets/coupon-world-og.svg"><meta name="twitter:card" content="summary"><meta name="twitter:title" content="{esc(title)}"><link rel="stylesheet" href="/assets/phone-guides.css?v=20261104"><link rel="stylesheet" href="/assets/page-feedback.css?v=20261112"><script async src="https://www.googletagmanager.com/gtag/js?id=G-921WL91ZGW"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag("js",new Date());gtag("config","G-921WL91ZGW");</script><script defer src="/assets/discovery-analytics.js?v=20261104"></script><script type="application/ld+json">{json.dumps(schema,ensure_ascii=False).replace('<','\\u003c')}</script></head><body><a class="skip" href="#content">Skip to content</a><header><nav aria-label="Main navigation"><a class="brand" href="/">CW <span>Coupon World<small>Find your next phone</small></span></a><a href="{HUB}">Phone guides</a><a href="/hi{path}" lang="hi">हिंदी</a><a href="/#mobileResearchSearch">Find a phone ↗</a></nav></header><main id="content">{content}{feedback_markup("buying_guide")}</main><script defer src="/assets/page-feedback.js?v=20261112"></script><footer><a href="{HUB}">All phone buying guides</a> · <a href="/guides/smartphone-buying-guide/">Standard Buying Guide</a><p>As an Amazon Associate I earn from qualifying purchases. Retailer search links do not confirm a current price, stock or delivery. We may earn commission from qualifying purchases through tagged Amazon links.</p></footer></body></html>'''
    def cards(items):
        return '<div class="guide-grid">'+''.join(f'<a class="guide-card" href="/seo/{p["slug"]}.html"><h3>{esc(p["title"])}</h3><p>{esc(p["intro"])}</p><span>Read guide →</span></a>' for p in items)+'</div>'
    for i,p in enumerate(pages):
        path=f'/seo/{p["slug"]}.html'
        query='/?'+urlencode({'q':p['query']})+'#mobileResearchSearch'
        sections=''.join(f'<section id="section-{n}"><h2>{esc(s["heading"])}</h2><p>{esc(s["text"])}</p></section>' for n,s in enumerate(p['sections'],1))
        toc='<nav class="contents" aria-label="On this page">'+''.join(f'<a href="#section-{n}">{esc(s["heading"])}</a>' for n,s in enumerate(p['sections'],1))+'</nav>'
        amazon='https://www.amazon.in/s?'+urlencode({'k':p['query'],'tag':'guru07cc-21'})
        related=[pages[(i+j)%len(pages)] for j in (1,5,11)]
        evidence_links = ''
        if 'camera' in p['slug']:
            evidence_links = '<li><a href="https://www.phonearena.com/phones/benchmarks/camera" rel="noopener noreferrer" target="_blank">PhoneArena original camera tests and methodology</a></li>'
        elif any(term in p['slug'] for term in ('battery', 'gaming', 'charging')):
            ledger = json.loads((ROOT / 'data/mobile_independent_test_evidence.json').read_text(encoding="utf-8"))
            review = ledger['models'][1]['metrics'][0]['source_url']
            evidence_links = '<li><a href="'+esc(review)+'" rel="noopener noreferrer" target="_blank">Notebookcheck Galaxy A56 review — original lab test context</a></li>'
        content=f'''<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="{HUB}">Phone guides</a> / Guide</nav><article><div class="eyebrow">THE PHONE EDIT / BUYING GUIDE</div><h1>{esc(p['title'])}</h1><p class="lead">{esc(p['intro'])}</p><p class="byline">By {esc(data['editor'])} · Updated <time datetime="{data['updated']}">{esc(data['updated'])}</time></p><aside class="note"><strong>Research, with the limits visible.</strong><p>This is an editorial buying guide based on saved research, not a hands-on review or a live-offer list. Budget references are dated. No current price, stock or performance winner is certified here.</p></aside><section class="quick-answer" aria-label="Quick answer"><h2>{esc(p["reader_question"])}</h2><p>{esc(p["quick_answer"])}</p></section>{toc}{sections}{budget_examples(destination, p)}<section class="action"><h2>Turn the guide into a shortlist</h2><p>Open the existing research tool with “{esc(p['query'])}”. Add your budget, physical RAM, storage or excluded brand. Inspect each source and any missing information, then compare up to three matching phones. No condition is silently relaxed.</p><a class="button" href="{esc(query)}">Explore matching research ↗</a><p><a href="{esc(amazon)}" rel="sponsored nofollow noopener" target="_blank">Search Amazon (affiliate link)</a> · Confirm the selected variant and current offer at the retailer.</p></section><section><h2>Sources and how to verify</h2><p>Follow the specification sources on each research card for the exact model. Independent measurements retain their original source, tested unit and conditions. A research checking date does not imply that a lab test or retailer price was measured that day.</p><ul><li><a href="/guides/smartphone-buying-guide/">Standard smartphone buying checklist</a></li><li><a href="/seo/phone-research-evidence-method.html">Coupon World evidence method and limitations</a></li><li><a href="/phones/">Curated phone specifications with original sources</a></li>{evidence_links}</ul></section></article><section class="related"><h2>Continue your research</h2>{cards(related)}</section>'''
        article={'@context':'https://schema.org','@graph':[{'@type':'Article','headline':p['title'],'description':p['intro'],'dateModified':data['updated'],'datePublished':data['updated'],'author':{'@type':'Organization','name':data['editor']},'publisher':{'@type':'Organization','name':'Coupon World'},'mainEntityOfPage':BASE+path},{'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'Home','item':BASE+'/'},{'@type':'ListItem','position':2,'name':'Phone guides','item':BASE+HUB},{'@type':'ListItem','position':3,'name':p['title'],'item':BASE+path}]}]}
        target=destination/path.lstrip('/');target.parent.mkdir(parents=True,exist_ok=True)
        description=p['intro'].split('. ')[0]+'.'
        target.write_text(document(p['title'],description,path,content,article),encoding='utf-8')
    hub=destination/HUB.lstrip('/');hub.mkdir(parents=True,exist_ok=True)
    content='<div class="eyebrow">COUPON WORLD / SMARTPHONE RESEARCH</div><h1>Make a more informed phone choice.</h1><p class="lead">20 practical guides. Start with your budget, explore a priority, or resolve a specific buying question. Every guide links back to the existing research and comparison tool.</p><p><a href="/phones/">Explore source-linked phone specifications</a> for curated documented models, or search all 232 records in the research tool.</p><aside class="note">Updated 4 November 2026. These guides explain documented features and evidence gaps; they do not claim live prices or tested winners. Prepared with AI assistance against saved research; no hands-on testing is claimed.</aside><p><a href="/seo/india-smartphone-search-demand.html">See how historical search-demand signals shape our editorial coverage →</a></p>'
    for title,items in [('Start with your budget',pages[:5]),('Choose what matters most',pages[5:11]),('Get the details right',pages[11:])]:content+=f'<section><h2>{title}</h2>{cards(items)}</section>'
    (hub/'index.html').write_text(document('Smartphone Budget and Buying Guides','Explore 20 practical India phone guides for budgets, camera, battery, gaming, memory and exact-variant comparisons.',HUB,content,{'@context':'https://schema.org','@type':'CollectionPage','name':'Coupon World phone guides','url':BASE+HUB,'mainEntity':{'@type':'ItemList','numberOfItems':len(pages),'itemListElement':[{'@type':'ListItem','position':i+1,'name':p['title'],'url':BASE+'/seo/'+p['slug']+'.html'} for i,p in enumerate(pages)]}}),encoding='utf-8')
    sitemap=destination/'sitemap.xml'
    ns='http://www.sitemaps.org/schemas/sitemap/0.9';ET.register_namespace('',ns)
    tree=ET.parse(sitemap);root=tree.getroot();existing={x.text for x in root.findall(f'{{{ns}}}url/{{{ns}}}loc')}
    for path in [HUB]+[f'/seo/{p["slug"]}.html' for p in pages]:
        if BASE+path in existing:continue
        node=ET.SubElement(root,f'{{{ns}}}url');ET.SubElement(node,f'{{{ns}}}loc').text=BASE+path;ET.SubElement(node,f'{{{ns}}}lastmod').text=data['updated']
    tree.write(sitemap,encoding='utf-8',xml_declaration=True)
