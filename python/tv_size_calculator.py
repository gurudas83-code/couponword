#!/usr/bin/env python3
"""Publish the interactive TV-size calculator and responsive room preview."""
from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from python.category_research_pages import SITE, esc, doc, schema


ROUTE = "/tvs/tv-size-calculator/"


STYLE = r"""<style>
.tvcalc{max-width:1120px;margin:0 auto}.tvcalc-grid{display:grid;grid-template-columns:minmax(280px,390px) 1fr;gap:22px;align-items:start}.tvcalc-card{background:#fff;border:1px solid #dbe3ef;border-radius:20px;padding:20px;box-shadow:0 8px 24px #102a4312}.tvcalc-fields{display:grid;grid-template-columns:1fr 1fr;gap:12px}.tvcalc-fields label{font-weight:700;font-size:14px}.tvcalc-fields input,.tvcalc-fields select{width:100%;box-sizing:border-box;margin-top:6px;padding:11px;border:1px solid #cbd5e1;border-radius:10px;font:inherit}.tvcalc-result{margin-top:16px;padding:16px;border-radius:14px;background:#eef6ff;border:1px solid #bfdbfe}.tvcalc-result strong{font-size:30px;color:#075985}.tvcalc-note{font-size:13px;color:#475569}.room{--tv-w:44%;--tv-h:40%;position:relative;min-height:390px;overflow:hidden;border-radius:18px;background:linear-gradient(160deg,#e0f2fe,#f8fafc 50%,#cbd5e1);perspective:900px}.room:before{content:"";position:absolute;inset:0 0 35%;background:linear-gradient(135deg,#f8fafc,#dbeafe);transform:skewY(-8deg);transform-origin:bottom}.room:after{content:"";position:absolute;left:-8%;right:-8%;bottom:-28%;height:55%;background:linear-gradient(160deg,#cbd5e1,#94a3b8);transform:rotateX(58deg);transform-origin:top}.wall-window{position:absolute;right:8%;top:12%;width:17%;height:22%;border:8px solid #fff;background:linear-gradient(135deg,#7dd3fc,#2563eb);box-shadow:0 8px 22px #0f172a22;z-index:2}.tv-frame{position:absolute;z-index:4;left:50%;top:30%;transform:translateX(-50%);width:var(--tv-w);height:var(--tv-h);background:#111827;border:7px solid #111827;border-radius:8px;box-shadow:0 15px 18px #0f172a55}.tv-screen{position:absolute;inset:3px;background:radial-gradient(circle at 72% 30%,#bae6fd,transparent 25%),linear-gradient(135deg,#0f172a,#0369a1 48%,#22d3ee);border-radius:3px}.tv-screen:after{content:"Coupon World";position:absolute;left:12%;top:40%;font-size:clamp(10px,1.5vw,18px);font-weight:800;color:#e0f2fe}.tv-stand{position:absolute;z-index:4;left:50%;top:calc(30% + var(--tv-h) + 6px);transform:translateX(-50%);width:18%;height:8px;background:#334155;border-radius:50%}.sofa{position:absolute;z-index:5;left:29%;bottom:13%;width:42%;height:17%;background:#64748b;border-radius:22px 22px 8px 8px;box-shadow:0 12px 12px #0f172a2c}.sofa:before{content:"";position:absolute;left:8%;right:8%;top:-25%;height:44%;background:#94a3b8;border-radius:20px}.room-label{position:absolute;z-index:6;left:14px;bottom:14px;background:#ffffffd9;padding:8px 12px;border-radius:10px;font-size:13px;font-weight:700}
@media(max-width:760px){.tvcalc-grid{grid-template-columns:1fr}.room{min-height:300px}.tvcalc-fields{grid-template-columns:1fr 1fr}}
</style>"""


SCRIPT = r"""<script>
(() => {
  const $ = (id) => document.getElementById(id);
  const sizes = [32, 43, 50, 55, 65, 75, 85, 98];
  const calc = () => {
    const distance = Math.max(2, Number($('distance').value) || 8);
    const wallW = Math.max(3, Number($('wallW').value) || 10);
    const wallH = Math.max(3, Number($('wallH').value) || 8);
    const distanceIn = distance * 12;
    // Comfortable mixed-use heuristic: 30–40° diagonal viewing envelope.
    let target = distanceIn * 0.62;
    const maxDiagByWallW = ((wallW * 12 - 12) / 0.8716);
    const maxDiagByWallH = ((wallH * 12 - 16) / 0.4903);
    target = Math.min(target, maxDiagByWallW, maxDiagByWallH);
    let size = sizes.reduce((best, candidate) => Math.abs(candidate-target) < Math.abs(best-target) ? candidate : best, sizes[0]);
    size = Math.min(size, Math.max(...sizes.filter(x => x <= target), 32));
    const diagonal = size;
    const width = diagonal * 0.8716;
    const height = diagonal * 0.4903;
    $('recommended').textContent = `${size}-inch`;
    $('details').textContent = `Approx. screen ${width.toFixed(1)}″ wide × ${height.toFixed(1)}″ high; target envelope ${Math.round(target)}″. Keep at least 6″ side and 8″ top clearance.`;
    $('room').style.setProperty('--tv-w', `${Math.min(76, Math.max(26, width / (wallW*12) * 100))}%`);
    $('room').style.setProperty('--tv-h', `${Math.min(54, Math.max(22, height / (wallH*12) * 100))}%`);
    $('roomLabel').textContent = `${size}″ TV • ${distance} ft viewing distance`;
  };
  ['distance','wallW','wallH','roomHeight','roomWidth'].forEach(id => $(id)?.addEventListener('input', calc));
  calc();
})();
</script>"""


def publish(destination: Path):
    route_dir = destination / "tvs" / "tv-size-calculator"
    route_dir.mkdir(parents=True, exist_ok=True)
    body = f'''<article class="tvcalc"><p class="eyebrow">TV buying tool · India</p>
<h1>What TV size is right for your room?</h1>
<p>Enter your viewing distance and TV-wall dimensions. The calculator recommends a common 16:9 TV size and shows a responsive room preview so you can judge the scale before buying.</p>
{STYLE}<div class="tvcalc-grid"><section class="tvcalc-card"><h2>Your room</h2><div class="tvcalc-fields">
<label>Viewing distance (ft)<input id="distance" type="number" min="2" max="40" step="0.5" value="8"></label>
<label>TV wall width (ft)<input id="wallW" type="number" min="3" max="30" step="0.5" value="10"></label>
<label>TV wall height (ft)<input id="wallH" type="number" min="3" max="20" step="0.5" value="8"></label>
<label>Room width (ft)<input id="roomWidth" type="number" min="5" max="40" step="0.5" value="12"></label>
<label>Room height (ft)<input id="roomHeight" type="number" min="7" max="20" step="0.5" value="10"></label>
</div><div class="tvcalc-result"><span>Recommended size</span><br><strong id="recommended">55-inch</strong><p id="details">Calculating…</p></div>
<p class="tvcalc-note">Model: mixed-use comfort target ≈ 0.62 × viewing distance in inches, capped by wall clearance and snapped down to a common TV size. This is a planning estimate, not a medical or installation guarantee.</p></section>
<section class="tvcalc-card"><h2>Room preview</h2><div id="room" class="room" role="img" aria-label="Illustrative room preview with a TV whose size changes with your inputs"><div class="wall-window"></div><div class="tv-frame"><div class="tv-screen"></div></div><div class="tv-stand"></div><div class="sofa"></div><div id="roomLabel" class="room-label">55″ TV • 8 ft viewing distance</div></div><p class="tvcalc-note">Illustrative 3D-style preview; verify the exact TV’s outer dimensions, stand width, VESA pattern and wall strength before installation.</p></section></div>
<section><h2>How to use this result</h2><ul><li>Measure from your normal eye position to the screen plane, not to the wall behind the TV.</li><li>Check the exact model’s width, height, stand footprint and VESA mount before purchase.</li><li>For gaming or cinema, you may prefer the larger end of the suggested range; for mixed family viewing, the snapped recommendation is a safer starting point.</li></ul></section></article>'''
    html = doc("TV Size Calculator for Your Room", "Calculate a comfortable TV size from viewing distance and room dimensions, with an interactive room preview.", ROUTE, body, schema("TV Size Calculator", ROUTE, "tvs"))
    (route_dir / "index.html").write_text(html.replace("</body>", SCRIPT + "</body>"), encoding="utf-8")
    hub = destination / "tvs" / "index.html"
    if hub.exists():
        hub_html = hub.read_text(encoding="utf-8")
        link = '<section class="cr-guidance"><h2>TV size calculator</h2><p>Measure your viewing distance and TV wall, then use the <a href="' + ROUTE + '">interactive TV size calculator</a> with a responsive room preview.</p></section>'
        if "TV size calculator</h2>" not in hub_html:
            hub.write_text(hub_html.replace("</main>", link + "</main>", 1), encoding="utf-8")
    ns="http://www.sitemaps.org/schemas/sitemap/0.9"
    sitemap=destination/"sitemap.xml"; tree=ET.parse(sitemap); root=tree.getroot()
    url=SITE+ROUTE; existing={str(e.text) for e in root.findall(f"{{{ns}}}url/{{{ns}}}loc")}
    if url not in existing:
        node=ET.SubElement(root,f"{{{ns}}}url"); ET.SubElement(node,f"{{{ns}}}loc").text=url
        tree.write(sitemap, encoding="utf-8", xml_declaration=True)
    print("Published TV size calculator", url)
    return [url]
