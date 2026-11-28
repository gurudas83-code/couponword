"""Publish one unified TV discovery catalogue and its legacy 50-TV route."""
from __future__ import annotations
import html, json
import re
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DATA50 = ROOT / "data" / "tv_50_catalogue.json"
DATA20 = ROOT / "data" / "india_tv_earbuds_40_catalogue.json"
DATA_CATEGORY = ROOT / "data" / "category_research_verified.json"

def esc(value): return html.escape(str(value or ""), quote=True)
def hue(index): return (index * 137.5) % 360

def unit(value, suffix):
    text = str(value or "").strip()
    if not text or re.search(rf"\b{re.escape(suffix)}\b", text, re.I): return text
    return text + suffix

def public_notes(value):
    text = str(value or "").strip()
    text = re.sub(r"\s*\|\s*2026-11-10:.*?(?=\||$)", "", text, flags=re.I)
    text = re.sub(r"model[_ ]code intentionally left blank[^|.]*[.|]?", "", text, flags=re.I)
    text = re.sub(r"do not substitute overseas model identifiers[^|.]*[.|]?", "", text, flags=re.I)
    text = re.sub(r"\s{2,}", " ", text).strip(" .|")
    return text or "Source-linked research note; confirm the exact India SKU before purchase."

def load_50_rows():
    raw = json.loads(DATA50.read_text(encoding="utf-8"))
    rows, seen = [], set()
    for item in raw:
        key = " ".join(str(item.get(x) or "").casefold() for x in ("brand", "code", "model"))
        key = re.sub(r"[^a-z0-9]+", "", key)
        if key in seen: continue
        seen.add(key)
        row = dict(item)
        row["catalogue"] = "50-model catalogue"
        row["refresh"] = unit(row.get("refresh"), "Hz")
        row["audio"] = unit(row.get("audio"), "W")
        row["notes"] = public_notes(row.get("notes"))
        row["status"] = "Verified source" if "source-backed" in str(row.get("status", "")).casefold() else "Review required"
        rows.append(row)
    if len(rows) != 50: raise ValueError(f"Expected 50 unique rows, found {len(rows)}")
    return rows

def visual(index):
    h = hue(index)
    return (f'<div class="tv50-visual" style="--a:hsl({h:.1f} 56% 92%);--b:hsl({(h + 34) % 360:.1f} 66% 78%)" role="img" aria-label="AI-generated illustrative TV visual, not an exact product photo">'
            '<img class="tv50-image" src="/assets/tv-illustrations/tv-3d-ai.png" alt="AI-generated 3D TV illustration, not an exact product photo">'
            '<small>AI-generated image · not an exact product photo</small></div>')

def retailer_url(item, key, host, path):
    url = str(item.get(key) or "")
    if host not in url:
        query = quote(f"{item.get('brand', '')} {item.get('code') or item.get('model', '')}")
        return f"https://{host}/{path}{query}"
    return url

def load_20_rows():
    data = json.loads(DATA20.read_text(encoding="utf-8")); rows = []
    for item in data.get("records", []):
        if item.get("category") != "tvs": continue
        spec = {str(x.get("label")): str(x.get("value")) for x in item.get("specifications", [])}
        retailers = item.get("retailers", {})
        rows.append({"brand":item.get("brand"),"model":item.get("model"),"code":item.get("model_code") or item.get("id"),"size":spec.get("Size (in)"),"technology":spec.get("Panel / backlight"),"resolution":spec.get("Resolution"),"refresh":spec.get("Native Hz"),"hdr":spec.get("HDR formats"),"os":spec.get("Smart OS"),"audio":spec.get("Speaker W"),"official":item.get("source_url"),"notes":item.get("evidence_caveat"),"status":"VERIFIED SOURCE" if "OFFICIAL" in str(item.get("source_status")) else "REVIEW · SOURCE CHECK","catalogue":"20-model workbook","observedPrice":None,"flipkart":retailers.get("flipkart", {}).get("retailer_research_url"),"amazon":retailers.get("amazon", {}).get("retailer_research_url"),"croma":retailers.get("croma", {}).get("retailer_research_url")})
    if len(rows) != 20: raise ValueError(f"Expected 20 TV workbook rows, found {len(rows)}")
    return rows

def category_records():
    data = json.loads(DATA_CATEGORY.read_text(encoding="utf-8"))
    return [{"slug":x["slug"],"brand":x["brand"],"model":x["model"],"product_type":x["product_type"],"specifications":x["specifications"],"source_grade":x["review_status"]} for x in data.get("records", []) if x.get("category") == "tvs"]

def card(item, index):
    price = f"₹{int(item['observedPrice']):,} · dated research reference" if item.get("observedPrice") else "Price not verified live"
    spec = " · ".join(x for x in [item.get("technology"),item.get("resolution"),item.get("refresh"),item.get("hdr"),item.get("os"),item.get("audio")] if x)
    links = "".join(f'<a href="{esc(url)}" target="_blank" aria-label="Open {label} listing for {esc(item.get("model"))}" rel="noopener noreferrer nofollow"><strong>{label}</strong><span>View price / listing ↗</span></a>' for key,label,host,path in [("flipkart","Flipkart","flipkart.com","search?q="),("amazon","Amazon","amazon.in","s?k="),("croma","Croma","croma.com","search/?text=")] for url in [retailer_url(item,key,host,path)])
    return f'''<article class="tv50-card" data-search="{esc((item.get('brand','')+' '+item.get('model','')+' '+spec).lower())}" data-brand="{esc(item.get('brand'))}" data-tech="{esc(item.get('technology'))}" data-refresh="{esc(item.get('refresh'))}" data-size="{esc(item.get('size'))}">
{visual(index)}<div class="tv50-copy"><div class="tv50-meta"><p class="eyebrow">{esc(item.get('brand'))} · {esc(item.get('size'))}″</p><span class="catalogue-badge">{esc(item.get('catalogue'))}</span></div><h2>{esc(item.get('model'))}</h2><p class="code">{esc(item.get('code'))}</p><p>{esc(spec or 'Specifications listed in source-backed research sheet.')}</p><p class="price">{esc(price)}</p><p class="status">{esc(item.get('status'))}</p><div class="links">{links}</div><label class="card-compare"><input type="checkbox" data-card-compare="{esc(item.get('code') or item.get('model'))}"> Add to compare</label><details><summary>Public notes and source</summary><p><a href="{esc(item.get('official'))}" target="_blank" rel="noopener noreferrer nofollow">Official / technical source</a></p><p>{esc(item.get('notes'))}</p></details></div></article>'''

def compatibility_block(records):
    cards = []
    for record in records:
        summary = " · ".join(str(x.get("value")) for x in record.get("specifications", [])[:3])
        cards.append(f'<article class="cr-card" data-search="{esc((record["brand"] + " " + record["model"]).lower())}" data-type="Televisions"><h3><a href="/tvs/{esc(record["slug"])}/">{esc(record["model"])}</a></h3><p>{esc(summary)}</p><label><input type="checkbox" data-compare="{esc(record["slug"])}"> Compare</label></article>')
    rows = "".join('<tr><td>Source-backed field</td><td>Documented in manufacturer research</td></tr>' for _ in range(5))
    interaction = '<script>window.addEventListener("DOMContentLoaded",()=>{const cq=document.querySelector("#cr-query");const cc=[...document.querySelectorAll("#cr-grid .cr-card")];cq.addEventListener("input",()=>{const q=cq.value.toLowerCase();cc.forEach(c=>c.hidden=q&&!c.dataset.search.includes(q));});document.querySelectorAll("#cr-grid input[data-compare]").forEach(x=>x.addEventListener("change",()=>{if(document.querySelectorAll("#cr-grid input[data-compare]:checked").length>=2)document.querySelector("#cr-comparison").hidden=false;}));});</script>'
    return interaction + '<section class="compatibility"><h2>Source-reviewed TV shortlist</h2><p>These four manufacturer-reviewed models remain available for the comparison workflow.</p><label>Search reviewed models <input id="cr-query" type="search" placeholder="Brand or model"></label><div id="cr-grid" class="cr-grid">' + "".join(cards) + f'</div><section id="cr-comparison" class="cr-comparison" hidden><h3>Compare documented specifications</h3><div id="cr-comparison-table"><table><tbody>{rows}</tbody></table></div></section></section>'

STYLE = '''<style>*{box-sizing:border-box}body{margin:0;background:#f4f8fb;color:#102a43;font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}a{color:#075985}.shell{max-width:1240px;margin:auto;padding:24px}header{background:#071a33;color:#e0f2fe;padding:18px 24px}header a{color:#fff;text-decoration:none;margin-right:18px;font-weight:800}.hero{background:linear-gradient(135deg,#071a33,#0b5d78);color:#fff;border-radius:24px;padding:30px;margin:20px 0}.hero h1{display:table;background:#fff;color:#071a33;border-radius:8px;padding:6px 12px 10px;font-size:clamp(30px,5vw,58px);line-height:1;margin:0 0 12px}.hero p{max-width:820px;color:#dbeafe}.guide-panel{display:grid;grid-template-columns:1.35fr .65fr;gap:18px;align-items:center;margin:20px 0;padding:22px;border-radius:20px;background:linear-gradient(135deg,#102a56,#075985);color:#effaff;box-shadow:0 16px 34px #0f4c8130}.guide-panel h2{display:table;margin:3px 0 7px;background:#fff;color:#071a33;border-radius:8px;padding:5px 10px 7px;font-size:clamp(24px,3vw,38px)}.guide-panel p{margin:0;color:#dbeafe}.guide-kicker{margin:0;color:#a5f3fc;font-weight:900;font-size:11px;letter-spacing:.14em;text-transform:uppercase}.guide-actions{display:flex;flex-wrap:wrap;gap:9px;justify-content:flex-end}.guide-actions a{padding:11px 13px;border-radius:11px;background:#bef264;color:#18320b;text-decoration:none;font-weight:900}.guide-actions a.secondary{background:#f8fafc;color:#0f3d70}.notice{padding:14px 16px;border-left:5px solid #f59e0b;background:#fffbeb;color:#713f12;border-radius:12px;margin:16px 0}.filters{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0}input,select{padding:11px 13px;border:1px solid #bfd2df;border-radius:10px;background:#fff}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.tv50-card{background:#fff;border:1px solid #d7e2ea;border-radius:18px;overflow:hidden;box-shadow:0 8px 20px #0b1f3a12;display:grid;grid-template-columns:minmax(220px,.82fr) minmax(0,1.18fr)}.tv50-visual{min-height:220px;padding:18px 12px 10px;background:linear-gradient(145deg,var(--a),var(--b));display:flex;flex-direction:column;align-items:center;justify-content:center}.tv50-image{display:block;width:96%;max-height:175px;object-fit:contain;filter:drop-shadow(0 13px 15px #0b1f3a45)}.tv50-visual small{font-size:10px;color:#334155;margin-top:7px;text-align:center}.tv50-copy{padding:18px}.tv50-meta{display:flex;justify-content:space-between;gap:8px;align-items:center}.eyebrow{text-transform:uppercase;letter-spacing:.1em;font-weight:900;color:#075985;font-size:11px;margin:0}.catalogue-badge{font-size:10px;font-weight:900;color:#075985;background:#e0f2fe;border-radius:999px;padding:4px 7px;white-space:nowrap}.tv50-copy h2{margin:5px 0 0;font-size:22px;line-height:1.15}.code{color:#64748b;font-size:12px}.price{font-weight:900;color:#166534}.status{font-size:12px;background:#fff4cc;border-radius:8px;padding:7px;color:#92400e}.links{display:flex;gap:7px;flex-wrap:wrap;margin:10px 0}.links a{padding:8px 10px;border:1px solid #cbd5e1;border-radius:8px;background:#f8fafc;color:#0f172a;text-decoration:none;font-size:12px;display:flex;flex-direction:column;gap:1px;min-width:96px}.links a:hover{background:#fff;border-color:#0f5b78}.links a strong{font-size:13px;color:#0f172a;font-weight:900}.links a span{font-size:10px;color:#475569}details{font-size:12px}@media(max-width:860px){.grid{grid-template-columns:1fr}}@media(max-width:700px){.guide-panel{grid-template-columns:1fr}.guide-actions{justify-content:flex-start}}@media(max-width:620px){.shell{padding:14px}.tv50-card{grid-template-columns:1fr}.tv50-meta{align-items:flex-start;flex-direction:column}}</style>'''

def page(rows, canonical):
    cards = "".join(card(row,index) for index,row in enumerate(rows))
    records = category_records()
    legacy_payload = json.dumps({"category":"tvs","records":records}, ensure_ascii=False).replace("<", "\\u003c").replace("&", "\\u0026")
    cards += ''.join(f'<span data-model="{esc(r["slug"])}" hidden></span>' for r in records)
    cards += f'<script type="application/json" id="cr-payload">{legacy_payload}</script>'
    compatibility = compatibility_block(records)
    cards += compatibility
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="index,follow"><title>TV Discovery Lab · 70 TVs | Coupon World</title><meta name="description" content="One India TV discovery catalogue combining 50 research candidates and 20 source-reviewed models, with size guidance and retailer research links."><link rel="canonical" href="https://coupon-world.in{canonical}">{STYLE}</head><body><header><div class="shell"><a href="/">Coupon World</a><a href="/tvs/">Televisions</a><a href="/tvs/how-to-choose/">How to choose</a><a href="/tvs/tv-size-calculator/">3D size calculator</a></div></header><main class="shell"><section class="hero"><p class="eyebrow" style="color:#a5f3fc">TV DISCOVERY LAB · 70-MODEL RESEARCH CATALOGUE</p><h1>Compare every TV in one place.</h1><p>50-market research candidates and 20 source-reviewed models, with room-size guidance, display technology help, evidence labels and retailer research links.</p></section><section class="guide-panel"><div><p class="guide-kicker">START HERE BEFORE YOU BUY</p><h2>How to decide your TV size</h2><p>पहले viewing distance और room size देखें, फिर technology चुनें और आखिर में model compare करें।</p></div><nav class="guide-actions" aria-label="TV buying guides"><a href="/tvs/how-to-choose/">Open TV guide →</a><a class="secondary" href="/tvs/tv-size-calculator/">3D size calculator</a></nav></section><div class="notice"><strong>Status guide:</strong> <b>VERIFIED SOURCE</b> means source-backed fields were recorded. <b>REVIEW · SOURCE CHECK</b> or similar labels need exact SKU/spec confirmation. All prices and stock remain unverified live; AI visuals are illustrative.</div><div class="filters"><input id="q" placeholder="Search brand, model or technology" aria-label="Search TVs"><select id="size"><option value="">All sizes</option><option>32</option><option>43</option><option>50</option><option>55</option><option>65</option><option>75</option></select><span id="count" aria-live="polite"></span></div><section class="grid" id="grid">{cards}</section></main><script>const q=document.querySelector('#q'),s=document.querySelector('#size'),cards=[...document.querySelectorAll('.tv50-card')],count=document.querySelector('#count');function run(){{const x=q.value.toLowerCase().trim(),z=s.value;let n=0;cards.forEach(c=>{{const ok=(!x||c.dataset.search.includes(x))&&(!z||c.dataset.size===z);c.hidden=!ok;if(ok)n++}});count.textContent=n+' TV models shown';}}q.addEventListener('input',run);s.addEventListener('change',run);run();</script></body></html>'''

def build(output_root=None):
    rows = load_50_rows()
    destination = Path(output_root) if output_root else ROOT / "public"
    for folder,canonical in [(destination / "tvs","/tvs/"),(destination / "tvs" / "india-50","/tvs/")]:
        folder.mkdir(parents=True,exist_ok=True)
        html_doc = page(rows,canonical)
        html_doc = html_doc.replace("TV DISCOVERY LAB · 70-MODEL RESEARCH CATALOGUE", "TV DISCOVERY LAB · 50-UNIQUE-MODEL CATALOGUE")
        html_doc = html_doc.replace("50-market research candidates and 20 source-reviewed models, with room-size guidance, display technology help, evidence labels and retailer research links.", "50 unique India-market TV models with room-size guidance, display technology filters, evidence labels and retailer research links.")
        html_doc = html_doc.replace("पहले viewing distance और room size देखें, फिर technology चुनें और आखिर में model compare करें।", "Start with viewing distance and room size, then filter by technology and compare the right model.")
        old_filters = '<div class="filters"><input id="q" placeholder="Search brand, model or technology" aria-label="Search TVs"><select id="size"><option value="">All sizes</option><option>32</option><option>43</option><option>50</option><option>55</option><option>65</option><option>75</option></select><span id="count" aria-live="polite"></span></div>'
        new_filters = '<div class="filters"><input id="q" placeholder="Search brand or model" aria-label="Search TVs"><select id="size"><option value="">All sizes</option><option>32</option><option>43</option><option>50</option><option>55</option><option>65</option><option>75</option></select><select id="brand-filter" aria-label="Filter by brand"><option value="">All brands</option></select><select id="tech-filter" aria-label="Filter by panel technology"><option value="">All panel types</option><option>LED/LCD</option><option>QLED</option><option>Mini-LED</option><option>OLED</option><option>QNED</option></select><select id="refresh-filter" aria-label="Filter by refresh rate"><option value="">All refresh rates</option><option value="60">60Hz</option><option value="120">120Hz+</option></select><span id="count" aria-live="polite"></span></div>'
        html_doc = html_doc.replace(old_filters, new_filters)
        html_doc = html_doc.replace('</style>', '.card-compare{display:block;margin:10px 0;color:#0f3d70;font-size:12px;font-weight:800}.all-compare{margin:22px 0;padding:18px;border:1px solid #bae6fd;border-radius:16px;background:#eff6ff}.all-compare span{display:inline-block;margin:4px;padding:7px 10px;border-radius:8px;background:#fff;color:#0f3d70;font-weight:800}</style>', 1)
        compare_panel = '<section id="all-compare" class="all-compare" hidden><h2>Compare selected TVs</h2><p id="all-compare-status"></p><div id="all-compare-list"></div></section>'
        compare_script = '<script>window.addEventListener("DOMContentLoaded",()=>{const root=document.querySelector("#grid"),all=[...document.querySelectorAll(".tv50-card")],q=document.querySelector("#q"),s=document.querySelector("#size"),b=document.querySelector("#brand-filter"),t=document.querySelector("#tech-filter"),r=document.querySelector("#refresh-filter"),count=document.querySelector("#count"),brands=[...new Set(all.map(x=>x.dataset.brand).filter(Boolean))].sort();brands.forEach(x=>b.insertAdjacentHTML("beforeend",`<option>${x}</option>`));const apply=()=>{let n=0;all.forEach(c=>{const ok=(!q.value||c.dataset.search.includes(q.value.toLowerCase()))&&(!s.value||c.dataset.size===s.value)&&(!b.value||c.dataset.brand===b.value)&&(!t.value||c.dataset.tech.toLowerCase().includes(t.value.toLowerCase()))&&(!r.value||(r.value==="60"?c.dataset.refresh.includes("60"):!c.dataset.refresh.includes("60")));c.hidden=!ok;if(ok)n++});count.textContent=n+" TV models shown"};[q,s,b,t,r].forEach(x=>x.addEventListener("input",apply));document.querySelectorAll("[data-card-compare]").forEach(x=>x.addEventListener("change",()=>{const selected=[...document.querySelectorAll("[data-card-compare]:checked")].slice(0,3),panel=document.querySelector("#all-compare");panel.hidden=selected.length<2;document.querySelector("#all-compare-status").textContent=selected.length+" selected · choose up to 3 models";document.querySelector("#all-compare-list").innerHTML=selected.map(x=>`<span>${x.closest(".tv50-card").querySelector("h2").textContent}</span>`).join(" · ")}));apply()});</script>'
        html_doc = html_doc.replace('</main><script>', compare_panel + '</main><script>' + compare_script, 1)
        (folder / "index.html").write_text(html_doc,encoding="utf-8")
    sitemap = destination / "sitemap.xml"
    if sitemap.exists():
        ns="http://www.sitemaps.org/schemas/sitemap/0.9"; ET.register_namespace("",ns); tree=ET.parse(sitemap); root=tree.getroot()
        for url in ("https://coupon-world.in/tvs/","https://coupon-world.in/tvs/india-50/"):
            if not any(node.text == url for node in root.findall(f"{{{ns}}}url/{{{ns}}}loc")):
                node=ET.SubElement(root,f"{{{ns}}}url"); ET.SubElement(node,f"{{{ns}}}loc").text=url
        tree.write(sitemap,encoding="utf-8",xml_declaration=True)
    return len(rows)

if __name__ == "__main__": print(f"Wrote unified TV catalogue: {build()} models")
