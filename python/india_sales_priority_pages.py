#!/usr/bin/env python3
"""Publish manufacturer-linked Indian Q3 2026 shipment-signal research.

The Omdia report names device families supporting shipments, NOT a unit-
ranked list of India's ten best-selling models. Missing identities become
a research intake, never canonical variant/price/ranking admissions.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET
from python.category_research_pages import SITE, esc, doc, schema

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "india_q3_2026_sales_priority_models.json"
CATALOGUE = ROOT / "data" / "mobile_research_catalogue.json"
ROUTE = "/phones/india-market-demand-q3-2026/"
REPORT_HOST = "omdia.tech.informa.com"
OFFICIAL_HOSTS = {
 "Samsung":"samsung.com", "vivo":"vivo.com", "Redmi":"mi.com",
 "OPPO":"oppo.com", "Apple":"apple.com", "POCO":"mi.com"
}

def _identity(model):
    return (str(model.get("brand") or "").lower(), str(model.get("model") or "").lower())

def validate():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    catalogue = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    cards = catalogue["model_cards"]
    card_ids = {str(c["model_key"]).lower() for c in cards}
    if len(cards) != 232:
        raise ValueError("Original research catalogue changed: refuse promotion")
    if data.get("mode") != "RESEARCH_PRIORITY_SHIPMENT_DRIVERS_NO_MODEL_SALES_RANK":
        raise ValueError("Unapproved market-signal mode")
    if data.get("source_period") != "2026-Q3" or data.get("original_primary_catalogue_model_count") != 232:
        raise ValueError("Incorrect source period or core catalogue denominator")
    report = urlsplit(data.get("sales_evidence_url", ""))
    if report.scheme != "https" or report.hostname != REPORT_HOST:
        raise ValueError("Missing original Omdia market source")
    rows = data.get("models")
    if not isinstance(rows, list) or len(rows) != 10:
        raise ValueError("Exactly 10 editorial reference model rows required")
    seen=set()
    existing=missing=0
    for row in rows:
        key=str(row.get("repository_model_key") or "")
        expected="|".join(_identity(row))
        if key != expected or key in seen:
            raise ValueError("Duplicate or mismatched model identity: " + key)
        seen.add(key)
        exists = key in card_ids
        status = "EXISTING_232_MODEL" if exists else "NEW_SOURCE_REVIEWED_INTAKE_ONLY"
        if row.get("repository_snapshot_status") != status:
            raise ValueError("Mismatch vs original source catalogue: " + key)
        existing+=int(exists);missing+=int(not exists)
        official = urlsplit(row.get("official_spec_url") or "")
        host=OFFICIAL_HOSTS.get(row["brand"])
        if official.scheme!="https" or not host or not (official.hostname==host or
           (official.hostname or "").endswith("."+host)):
            raise ValueError("Non-manufacturer source for " + key)
        specs=row.get("specs")
        if not isinstance(specs,list) or len(specs)<5:
            raise ValueError("No meaningful official specifications for " + key)
        if any(not x.get("label") or not x.get("value") or x.get("source_url")!=row["official_spec_url"] for x in specs):
            raise ValueError("Invalid source provenance for " + key)
        if row.get("merchant_offer_eligible") is not False or row.get("price_inr") is not None or row.get("stock") is not None or row.get("performance_score") is not None:
            raise ValueError("Sales reference promoted to commerce/performance")
        if not row.get("notes"):
            raise ValueError("Regional/family scope not disclosed")
    if existing!=4 or missing!=6:
        raise ValueError(f"Reconciliation changed: {existing} already present, {missing} new")
    return data

def slug(model):
    return re.sub(r"[^a-z0-9]+","-",model["repository_model_key"].replace("|","-")).strip("-")

def model_route(row):
    return ROUTE+slug(row)+"/"

def _detail(row):
    title=row["brand"]+" "+row["model"]
    route=model_route(row)
    facts="".join('<div class="cr-fact"><dt>'+esc(f["label"])+
      '</dt><dd>'+esc(f["value"])+
      ' <a href="'+esc(f["source_url"])+'" rel="noopener noreferrer" target="_blank">Manufacturer source</a></dd></div>'
      for f in row["specs"])
    status="Already present in core phone catalogue" if row["repository_snapshot_status"]=="EXISTING_232_MODEL" else "New manufacturer-reviewed research candidate"
    body=f'''<p class="cr-crumb"><a href="/">Home</a> / <a href="/phones/">Phones</a> /
<a href="{ROUTE}">India Q3 2026 market research</a> / {esc(title)}</p>
<article class="cr-detail"><p class="cr-eyebrow">Model-level market research · {esc(status)}</p>
<h1>{esc(title)}</h1>
<p class="cr-lead">Cited by industry analysis as part of a model or series contributing to Q3 2026 India shipments. This is NOT a ranked bestseller position or verified exact RAM/storage sale.</p>
<h2>Manufacturer-sourced technical facts</h2><dl class="cr-detail-facts">{facts}</dl>
<p><a href="{esc(row["official_spec_url"])}" target="_blank" rel="noopener noreferrer">View original maker specifications</a></p>
<h2>Important model and sales limitations</h2><p>{esc(row["notes"])}</p>
<ul><li>Market research names a model family or series, not the exact colour, RAM/storage or variant sales rank</li>
<li>No authorized live price, retailer stock, commission, purchase link or performance score has been added</li>
<li>Manufacturer claims are not independent measurements of battery life, camera quality or gaming</li>
<li>Confirm exact Indian SKU and retailer terms before buying</li></ul>
<p>Sales source: <a href="{esc(row["source_report_url"])}" target="_blank" rel="noopener noreferrer">Omdia India Q3 2026 report</a></p>
<p><a href="{ROUTE}">Return to market coverage audit</a> · <a href="/phones/">Browse phone specifications</a></p>
</article>'''
    content=doc(title+" India model research",
      "India model-level manufacturer facts and Q3 2026 shipment-signal research for "+title+". No ranked sales figures or live prices.",
      route,body,schema(title,route,"phones"))
    # Non-indexable until certified editorial status/variant review. The
    # substantive category hub stays indexable with the original market source.
    return content.replace('name="robots" content="index,follow"',
      'name="robots" content="noindex,follow"',1)

def _hub(data):
    rows=data["models"]
    items=[]
    for row in rows:
        state="Already in the 232-model catalogue" if row["repository_snapshot_status"]=="EXISTING_232_MODEL" else "New verified-source research intake"
        summary="".join('<div class="cr-fact"><dt>'+esc(f["label"])+
             '</dt><dd>'+esc(f["value"])+'</dd></div>' for f in row["specs"][:3])
        items.append('<article class="cr-card"><div class="cr-card-head"><span class="cr-tag">'+
            esc(row["brand"])+'</span><span class="cr-check">'+esc(state)+'</span></div><h3>'+
            '<a href="'+model_route(row)+'">'+esc(row["brand"]+" "+row["model"])+
            '</a></h3><p class="cr-muted">Industry report: '+esc(row["market_report_name"])+
            '</p><dl class="cr-facts">'+summary+
            '</dl><p>'+esc(row["notes"])+'</p><div class="cr-card-foot">'+
            '<a href="'+model_route(row)+'">Inspect research</a> · '+
            '<a href="'+esc(row["official_spec_url"])+
            '" target="_blank" rel="noopener noreferrer">Maker source</a></div></article>')
    body=f'''<p class="cr-crumb"><a href="/">Home</a> / <a href="/phones/">Phones</a> / India market coverage</p>
<section class="cr-hero"><p class="cr-eyebrow">2026 Q3 · India smartphone shipment signals</p>
<h1>10 important models in India's 2026 sales reports</h1>
<p>{esc(data["ranking_disclosure"])}</p>
<p><strong>Repository audit:</strong> 4 already included in our existing 232-model research catalogue, 6 were missing and have now been recorded with official India manufacturer research as new intake candidates.</p>
<p>This is NOT an official nationwide Top 10 ranking by phone units, not a shopping recommendation, and not evidence of live retailer stock or prices.</p>
<p>Primary source: <a href="{esc(data["sales_evidence_url"])}" target="_blank" rel="noopener noreferrer">Omdia, 19 October 2026</a>.</p></section>
<section><h2>The ten model-level research references</h2>
<p>Listed by manufacturer group, not sales position. Models cited as families/series are identified explicitly.</p>
<div class="cr-grid">{''.join(items)}</div></section>
<section class="cr-guidance"><h2>Why six are not yet certified recommendations</h2>
<p>The existing approved phone ranking requires verified exact India variant identity, a documented performance formula and fresh authorized retailer offers. The newly researched models remain separate from the frozen original 232-card registry until those gates are met. No price is used as a performance scoring signal.</p>
<p>See the existing <a href="/phones/">phone specification library</a> and <a href="/guides/phone-budget-guides/">budget research guides</a>.</p></section>'''
    return doc("India sales-report model coverage, Q3 2026",
        "Research-backed coverage check for ten smartphone model families named by Omdia for India Q3 2026 shipments; not a unit-ranked Top 10.",
        ROUTE,body,schema("India smartphone market coverage Q3 2026",ROUTE,"phones"))

def publish_sales_priority(destination):
    data=validate()
    out=destination/ROUTE.lstrip("/")
    out.mkdir(parents=True,exist_ok=True)
    (out/"index.html").write_text(_hub(data),encoding="utf-8")
    for row in data["models"]:
        p=out/slug(row)
        p.mkdir(parents=True,exist_ok=True)
        (p/"index.html").write_text(_detail(row),encoding="utf-8")
    ns="http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("",ns)
    path=destination/"sitemap.xml"
    tree=ET.parse(path);root=tree.getroot()
    url=SITE+ROUTE
    if url in {str(el.text) for el in root.findall(f"{{{ns}}}url/{{{ns}}}loc")}:
        raise ValueError("Duplicate market research sitemap entry")
    el=ET.SubElement(root,f"{{{ns}}}url")
    ET.SubElement(el,f"{{{ns}}}loc").text=url
    tree.write(path,encoding="utf-8",xml_declaration=True)
    print("India Q3 2026 market coverage: 10 model research pages, 6 new intake models")
    return url
