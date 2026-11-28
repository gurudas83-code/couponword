"""Build the 50-model TV research catalogue page from the validated workbook export.

The page is intentionally a research catalogue: it exposes model/spec/source/retailer
links and AI illustrations, but never claims live stock or a live lowest price.
"""
from __future__ import annotations
import html
import json
import re
from xml.etree import ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "tv_50_catalogue.json"
OUT = ROOT / "public" / "tvs" / "india-50" / "index.html"

def esc(v): return html.escape(str(v or ""), quote=True)
def hue(i): return (i * 137.5) % 360
def visual(i):
    h = hue(i)
    return (f'<div class="tv50-visual" style="--a:hsl({h:.1f} 56% 92%);--b:hsl({(h+34)%360:.1f} 66% 78%)" '
            f'role="img" aria-label="AI-generated illustrative TV visual, not an exact product photo">'
            '<img class="tv50-image" src="/assets/tv-illustrations/tv-3d-ai.png" alt="AI-generated 3D TV illustration, not an exact product photo">'
            '<small>AI-generated image · not an exact product photo</small></div>')

def retailer_url(item, key, host, path):
    url = str(item.get(key) or '')
    if host not in url:
        from urllib.parse import quote
        q = quote(f"{item.get('brand','')} {item.get('code') or item.get('model','')}")
        return f"https://{host}/{path}{q}"
    return url

def card(item, i):
    price = f"₹{int(item['observedPrice']):,} · dated research reference" if item.get('observedPrice') else "Price not verified live"
    spec = " · ".join(x for x in [item.get('technology'), item.get('resolution'), item.get('refresh'), item.get('hdr'), item.get('os'), item.get('audio')] if x)
    links = ''.join(f'<a href="{esc(url)}" target="_blank" aria-label="Open {label} listing for {esc(item.get("model"))}" rel="noopener noreferrer nofollow"><strong>{label}</strong><span>View price / listing ↗</span></a>' for k,label,host,path in [('flipkart','Flipkart','flipkart.com','search?q='),('amazon','Amazon','amazon.in','s?k='),('croma','Croma','croma.com','search/?text=')] for url in [retailer_url(item,k,host,path)])
    return f'''<article class="tv50-card" data-search="{esc((item.get('brand','')+' '+item.get('model','')+' '+spec).lower())}" data-size="{esc(item.get('size'))}">
{visual(i)}<div class="tv50-copy"><p class="eyebrow">{esc(item.get('brand'))} · {esc(item.get('size'))}″</p><h2>{esc(item.get('model'))}</h2><p class="code">{esc(item.get('code'))}</p><p>{esc(spec or 'Specifications listed in source-backed research sheet.')}</p><p class="price">{esc(price)}</p><p class="status">{esc(item.get('status'))}</p><div class="links">{links}</div><details><summary>Source and notes</summary><p><a href="{esc(item.get('official'))}" target="_blank" rel="noopener noreferrer nofollow">Official / technical source</a></p><p>{esc(item.get('notes'))}</p></details></div></article>'''

def build(output_root=None):
    rows = json.loads(DATA.read_text(encoding='utf-8'))
    if len(rows) != 50: raise ValueError(f"Expected 50 rows, found {len(rows)}")
    cards = ''.join(card(r, i) for i,r in enumerate(rows))
    html_doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="index,follow"><title>50 TVs to research in India | Coupon World</title><meta name="description" content="50 India-market TV models with specifications, AI illustrations and Amazon, Flipkart and Croma research links."><link rel="canonical" href="https://coupon-world.in/tvs/india-50/"><style>
*{{box-sizing:border-box}}body{{margin:0;background:#f4f8fb;color:#102a43;font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}}a{{color:#075985}}.shell{{max-width:1240px;margin:auto;padding:24px}}header{{background:#071a33;color:#e0f2fe;padding:18px 24px}}header a{{color:#fff;text-decoration:none;margin-right:18px;font-weight:800}}.hero{{background:linear-gradient(135deg,#071a33,#0b5d78);color:#fff;border-radius:24px;padding:30px;margin:20px 0}}.hero h1{{font-size:clamp(30px,5vw,58px);line-height:1;margin:0 0 12px}}.hero p{{max-width:820px;color:#dbeafe}}.notice{{padding:14px 16px;border-left:5px solid #f59e0b;background:#fffbeb;color:#713f12;border-radius:12px;margin:16px 0}}.filters{{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0}}input,select{{padding:11px 13px;border:1px solid #bfd2df;border-radius:10px;background:#fff}}.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}.tv50-card{{background:#fff;border:1px solid #d7e2ea;border-radius:18px;overflow:hidden;box-shadow:0 8px 20px #0b1f3a12;display:grid;grid-template-columns:minmax(220px,.82fr) minmax(0,1.18fr)}}.tv50-visual{{min-height:220px;padding:18px 12px 10px;background:linear-gradient(145deg,var(--a),var(--b));display:flex;flex-direction:column;align-items:center;justify-content:center}}.tv50-image{{display:block;width:96%;max-height:175px;object-fit:contain;filter:drop-shadow(0 13px 15px #0b1f3a45)}}.tv50-visual small{{font-size:10px;color:#334155;margin-top:7px;text-align:center}}.tv50-copy{{padding:18px}}.eyebrow{{text-transform:uppercase;letter-spacing:.1em;font-weight:900;color:#075985;font-size:11px}}.tv50-copy h2{{margin:5px 0 0;font-size:22px;line-height:1.15}}.code{{color:#64748b;font-size:12px}}.price{{font-weight:900;color:#166534}}.status{{font-size:12px;background:#fff4cc;border-radius:8px;padding:7px;color:#92400e}}.links{{display:flex;gap:7px;flex-wrap:wrap;margin:10px 0}}.links a{{padding:8px 10px;border:1px solid #cbd5e1;border-radius:8px;background:#f8fafc;color:#0f172a;text-decoration:none;font-size:12px;display:flex;flex-direction:column;gap:1px;min-width:96px;box-shadow:0 3px 8px #0b1f3a12}}.links a:hover{{background:#fff;border-color:#0f5b78}}.links a strong{{font-size:13px;color:#0f172a;font-weight:900}}.links a span{{font-size:10px;color:#475569}}details{{font-size:12px}}@media(max-width:860px){{.grid{{grid-template-columns:1fr}}}}@media(max-width:620px){{.shell{{padding:14px}}.tv50-card{{grid-template-columns:1fr}}}}
</style></head><body><header><div class="shell"><a href="/">Coupon World</a><a href="/tvs/">Televisions</a><a href="/tvs/how-to-choose/">How to choose</a><a href="/tvs/tv-size-calculator/">3D size calculator</a></div></header><main class="shell"><section class="hero"><p class="eyebrow">TV DISCOVERY LAB · 50-MODEL RESEARCH CATALOGUE</p><h1>Compare 50 TVs before you buy.</h1><p>Model specifications, AI-generated illustrative visuals and direct Flipkart, Amazon and Croma links in one place.</p></section><div class="notice"><strong>Research disclosure:</strong> AI images are illustrative, not exact product photos. Prices and stock are not live-certified; open the retailer link to confirm today’s price and availability. Exact model/SKU status is shown on every card.</div><div class="filters"><input id="q" placeholder="Search brand, model or technology" aria-label="Search TVs"><select id="size"><option value="">All sizes</option><option>32</option><option>43</option><option>50</option><option>55</option><option>65</option><option>75</option></select><span id="count" aria-live="polite"></span></div><section class="grid" id="grid">{cards}</section></main><script>const q=document.querySelector('#q'),s=document.querySelector('#size'),cards=[...document.querySelectorAll('.tv50-card')],count=document.querySelector('#count');function run(){{const x=q.value.toLowerCase().trim(),z=s.value;let n=0;cards.forEach(c=>{{const ok=(!x||c.dataset.search.includes(x))&&(!z||c.dataset.size===z);c.hidden=!ok;if(ok)n++}});count.textContent=n+' TV models shown';}}q.addEventListener('input',run);s.addEventListener('change',run);run();</script></body></html>'''
    destination = Path(output_root) if output_root else ROOT / 'public'
    out = destination / 'tvs' / 'india-50' / 'index.html'
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(html_doc, encoding='utf-8')
    hub = destination / 'tvs' / 'index.html'
    if hub.exists():
        hub_html = hub.read_text(encoding='utf-8')
        link = '<section class="cr-guidance"><h2>50-TV research catalogue</h2><p>Compare all 50 India-market TV candidates with AI visuals and retailer research links. <a href="/tvs/india-50/">Open the 50-TV catalogue →</a></p></section>'
        if '/tvs/india-50/' not in hub_html:
            hub_html = hub_html.replace('</main>', link + '</main>', 1)
            hub.write_text(hub_html, encoding='utf-8')
    sitemap = destination / 'sitemap.xml'
    if sitemap.exists():
        ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'; ET.register_namespace('', ns)
        tree = ET.parse(sitemap); root = tree.getroot(); url = 'https://coupon-world.in/tvs/india-50/'
        if not any(n.text == url for n in root.findall(f'{{{ns}}}url/{{{ns}}}loc')):
            node = ET.SubElement(root, f'{{{ns}}}url'); ET.SubElement(node, f'{{{ns}}}loc').text = url
            tree.write(sitemap, encoding='utf-8', xml_declaration=True)
    return len(rows)

if __name__ == '__main__': print(f'Wrote 50-TV page: {build()}')

