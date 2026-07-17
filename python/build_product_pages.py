#!/usr/bin/env python3
"""
Coupon World AI OS
Static Product Page Generator v0.1

Creates:
    products/<slug>-<asin>/index.html

Rules:
- Uses only existing coupons.json fields
- Does not invent price, discount, rating, reviews, stock, or urgency
- Unavailable products receive noindex,follow
- Dry-run by default; use --write to generate
"""

import argparse
import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "coupons.json"
OUT = ROOT / "products"

# Preserve already-published product URLs when titles change.
LEGACY_PRODUCT_PATHS = {
    "17": "amazon-in-fashion-fest-17",
}
SITE = "https://coupon-world.in"


def clean(value):
    return "" if value is None else " ".join(str(value).strip().split())


def slugify(value, max_length=70):
    value = clean(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-") or "product"

    if len(value) > max_length:
        value = value[:max_length].rstrip("-")

    return value


def load_products():
    data = json.loads(DB.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("coupons.json must contain a list")
    return [p for p in data if isinstance(p, dict)]


def page_dir(product):
    identity = str(
        product.get("id")
        or product.get("sl_no")
        or product.get("asin")
        or ""
    )

    legacy_path = LEGACY_PRODUCT_PATHS.get(identity)

    if legacy_path:
        return OUT / legacy_path

    asin = clean(product.get("asin")).lower()
    suffix = asin or str(product.get("id") or product.get("sl_no") or "item")
    return OUT / f"{slugify(product.get('title'))}-{suffix}"


def page_url(product):
    rel = page_dir(product).relative_to(ROOT).as_posix()
    return f"{SITE}/{rel}/"


def excerpt(text, limit=160):
    text = clean(text)
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"




PRODUCT_FAMILIES = {
    "earbuds": (
        "earbud",
        "earbuds",
        "tws",
        "buds air",
        "airpods",
    ),
    "headphones": (
        "headphone",
        "headphones",
        "headset",
        "rockerz",
    ),
    "smartphones": (
        "iphone",
        "smartphone",
        "galaxy m",
        "redmi note",
        "redmi 13",
        "nord ce",
        "5g phone",
        "mobile phone",
    ),
    "phone-accessories": (
        "phone case",
        "mobile case",
        "screen protector",
        "charger",
        "charging cable",
        "power bank",
    ),
    "tablet-accessories": (
        "keyboard case",
        "folio cover",
        "tablet case",
        "tab a",
    ),
    "smartwatches": (
        "smartwatch",
        "smart watch",
    ),
    "telescope-accessories": (
        "telescope cover",
        "telescope case",
        "telescope bag",
    ),
    "telescopes": (
        "newtonian reflector",
        "reflector telescope",
        "telescope 235x",
        "76700 telescope",
    ),
    "projectors": (
        "projector",
        "planetarium",
        "nebula lamp",
    ),
    "storage-media": (
        "micro sd",
        "microsd",
        "memory card",
        "sd card",
    ),
    "musical-keyboards": (
        "musical keyboard",
        "mini keyboard",
        "37 keys",
        "61 keys",
        "electronic keyboard",
    ),
    "computer-keyboards": (
        "wireless usb keyboard",
        "keyboard and mouse combo",
        "computer keyboard",
        "gaming keyboard",
    ),
    "stationery": (
        "stationery",
        "notebook",
        "gel pen",
        "pens",
    ),
    "tshirts": (
        "t-shirt",
        "t shirt",
        "tee",
    ),
    "shoes": (
        "sneaker",
        "sneakers",
        "running shoe",
        "shoes",
        "footwear",
    ),
    "bottles": (
        "bottle",
        "thermosteel",
        "water bottle",
    ),
    "storage-organizers": (
        "storage organizer",
        "storage organisers",
        "storage basket",
        "storage baskets",
        "organizer",
        "organiser",
    ),
    "appliance-stands": (
        "appliance roller",
        "washing machine stand",
        "refrigerator stand",
        "moving base",
        "mobile dolly",
    ),
    "tools": (
        "electric drill",
        "angle grinder",
        "grinding wheel",
        "cutting blade",
        "tool kit",
    ),
    "supplements": (
        "tablets",
        "supplement",
        "cal mag",
        "nutrilite",
        "vitamin",
    ),
    "contact-lens-care": (
        "contact lens solution",
        "lens solution",
    ),
    "dumbbells": (
        "dumbbell",
        "dumbbells",
        "weights",
    ),
    "fitness-equipment": (
        "pull up bar",
        "resistance band",
        "fitness equipment",
        "exercise equipment",
    ),
    "backpacks": (
        "backpack",
        "rucksack",
    ),
    "trolley-bags": (
        "trolley bag",
        "luggage",
        "suitcase",
    ),
    "watches": (
        "analog watch",
        "wrist watch",
    ),
    "skincare": (
        "skincare",
        "skin care",
        "face wash",
        "moisturizer",
        "serum",
    ),
    "makeup": (
        "makeup",
        "lipstick",
        "foundation",
        "mascara",
    ),
    "microwave-ovens": (
        "microwave oven",
        "microwave",
    ),
    "induction-cooktops": (
        "induction cooktop",
        "induction stove",
    ),
    "ceiling-fans": (
        "ceiling fan",
    ),
    "trimmers": (
        "trimmer",
        "grooming kit",
    ),
    "computer-mice": (
        "wireless mouse",
        "computer mouse",
    ),
    "speakers": (
        "bluetooth speaker",
        "speaker",
        "echo dot",
    ),
    "cameras": (
        "camera",
        "cctv",
        "security camera",
        "baby monitor",
    ),
}


def searchable_text(product):
    return " ".join(
        [
            clean(product.get("title")),
            clean(product.get("category")),
        ]
    ).lower()


def detect_family(product):
    text = searchable_text(product)

    best_family = ""
    best_score = 0

    for family, phrases in PRODUCT_FAMILIES.items():
        score = 0

        for phrase in phrases:
            phrase = phrase.lower()

            if phrase in text:
                score += len(phrase.split()) * 10
                score += len(phrase)

        if score > best_score:
            best_family = family
            best_score = score

    return best_family


def related(product, products, limit=4):
    current_id = str(
        product.get("id")
        or product.get("sl_no")
        or product.get("asin")
        or ""
    )

    family = detect_family(product)

    if not family:
        return []

    candidates = []

    for candidate in products:
        candidate_id = str(
            candidate.get("id")
            or candidate.get("sl_no")
            or candidate.get("asin")
            or ""
        )

        if candidate_id == current_id:
            continue

        if candidate.get("active") is False:
            continue

        if detect_family(candidate) != family:
            continue

        candidates.append(candidate)

    return candidates[:limit]


def render(product, products):
    title = clean(product.get("title")) or "Amazon Product"
    brand = clean(product.get("brand"))
    category = clean(product.get("category")) or "Deals"
    description = clean(product.get("description")) or (
        f"{title} is listed on Coupon World. Check latest details on Amazon."
    )
    asin = clean(product.get("asin")).upper()
    image = clean(product.get("image"))
    link = clean(product.get("link"))
    active = product.get("active") is not False
    availability = clean(product.get("availability")) or (
        "available" if active else "unavailable"
    )

    canonical = page_url(product)
    robots = "index,follow" if active else "noindex,follow"
    meta = excerpt(description)

    schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": title,
        "description": description,
        "category": category,
        "sku": asin,
        "url": canonical,
    }
    if brand:
        schema["brand"] = {"@type": "Brand", "name": brand}
    if image:
        schema["image"] = image

    media = (
        f'<img src="{html.escape(image)}" alt="{html.escape(title)}">'
        if image else
        f'<div class="placeholder">🛍️<small>{html.escape(category)}</small></div>'
    )

    cta = (
        f'<a class="cta" href="{html.escape(link)}" target="_blank" '
        'rel="nofollow sponsored noopener">Check on Amazon →</a>'
        if active and link else
        '<span class="cta disabled">Currently unavailable</span>'
    )

    cards = []
    for item in related(product, products):
        href = "../../" + page_dir(item).relative_to(ROOT).as_posix() + "/"
        cards.append(
            f'<a class="related" href="{href}">'
            f'<strong>{html.escape(clean(item.get("title")))}</strong>'
            f'<span>{html.escape(clean(item.get("brand")) or clean(item.get("category")))}</span>'
            '</a>'
        )


    guide_html = ""

    family = detect_family(product)

    if family in {
        "earbuds",
        "headphones",
        "speakers",
    }:
        guide_html = (
            '<section>'
            '<h2>Wireless audio buying guide</h2>'
            '<p>Compare earbuds, headphones and Bluetooth speakers '
            'before choosing the format that fits your needs.</p>'
            '<p><a href="../../guides/wireless-audio-buying-guide/">'
            'Read the wireless audio buying guide'
            '</a></p>'
            '</section>'
        )

    elif family == "smartphones":
        guide_html = (
            '<section>'
            '<h2>Smartphone buying guide</h2>'
            '<p>Review storage, memory, display, battery, camera and '
            'connectivity information before choosing a phone.</p>'
            '<p><a href="../../guides/smartphone-buying-guide/">'
            'Read the smartphone buying guide'
            '</a></p>'
            '</section>'
        )

    elif family == "smartwatches":
        guide_html = (
            '<section>'
            '<h2>Smartwatch buying guide</h2>'
            '<p>Check phone compatibility, calling features, display, '
            'battery information and water resistance before choosing.</p>'
            '<p><a href="../../guides/smartwatch-buying-guide/">'
            'Read the smartwatch buying guide'
            '</a></p>'
            '</section>'
        )

    related_html = ""
    if cards:
        related_html = (
            '<section><h2>Related products</h2>'
            '<div class="grid">' + "".join(cards) + '</div></section>'
        )

    return f"""<!doctype html>
<html lang="en">
<head>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-921WL91ZGW"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){{dataLayer.push(arguments);}}
gtag('js', new Date());
gtag('config', 'G-921WL91ZGW');
</script>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} | Coupon World</title>
<meta name="description" content="{html.escape(meta)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{html.escape(canonical)}">
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
<style>
body{{margin:0;font-family:Arial,sans-serif;background:#f7f8fc;color:#17191f}}
.wrap{{width:min(1050px,calc(100% - 32px));margin:auto}}
header{{background:#111827;color:#fff;padding:18px 0}}
header a{{color:#fff;text-decoration:none;font-weight:800}}
.crumbs{{padding:24px 0 12px;color:#68707d}}
.hero{{display:grid;grid-template-columns:minmax(260px,420px) 1fr;gap:30px;background:#fff;border:1px solid #e5e7eb;border-radius:20px;padding:28px}}
.media{{min-height:320px;display:grid;place-items:center;background:#f1f3f7;border-radius:16px;overflow:hidden}}
.media img{{width:100%;height:100%;object-fit:contain}}
.placeholder{{display:flex;flex-direction:column;align-items:center;gap:10px;font-size:72px}}
.placeholder small{{font-size:14px;color:#68707d}}
.badge{{display:inline-block;padding:6px 10px;background:#fff1e8;color:#b54717;border-radius:999px;font-weight:700}}
h1{{font-size:clamp(30px,5vw,50px);line-height:1.08;margin:16px 0}}
.meta{{display:flex;flex-wrap:wrap;gap:12px;color:#68707d}}
.status{{font-size:21px;font-weight:800;margin:22px 0}}
.cta{{display:inline-flex;padding:14px 22px;border-radius:12px;background:#ff6b2c;color:#fff;text-decoration:none;font-weight:800}}
.cta.disabled{{background:#cfd4dc;color:#667085}}
section{{margin:28px 0;background:#fff;border:1px solid #e5e7eb;border-radius:18px;padding:25px}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}
.related{{border:1px solid #e5e7eb;border-radius:14px;padding:16px;color:#17191f;text-decoration:none;display:grid;gap:8px}}
.related span{{color:#68707d;font-size:14px}}
.note{{color:#68707d;font-size:13px;margin-top:14px}}
footer{{padding:28px 0 40px;color:#68707d;font-size:14px}}
@media(max-width:760px){{.hero{{grid-template-columns:1fr;padding:18px}}.grid{{grid-template-columns:1fr 1fr}}}}
</style>
</head>
<body>
<header><div class="wrap"><a href="../../">Coupon World</a></div></header>
<main class="wrap">
<div class="crumbs"><a href="../../">Home</a> › {html.escape(category)} › {html.escape(title)}</div>
<article class="hero">
<div class="media">{media}</div>
<div>
<span class="badge">{html.escape(category)}</span>
<h1>{html.escape(title)}</h1>
<div class="meta">
{f'<span>Brand: {html.escape(brand)}</span>' if brand else ''}
{f'<span>ASIN: {html.escape(asin)}</span>' if asin else ''}
<span>Status: {html.escape(availability)}</span>
</div>
<div class="status">{'Check Latest Offer' if active else 'Currently unavailable'}</div>
{cta}
<div class="note">Price and availability are confirmed on the retailer site.</div>
</div>
</article>
<section><h2>About this product</h2><p>{html.escape(description)}</p></section>
{guide_html}
{related_html}
</main>
<footer><div class="wrap">Coupon World may earn a commission from qualifying purchases.</div><p class="affiliate-disclosure">As an Amazon Associate I earn from qualifying purchases.</p>
</footer>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    products = load_products()
    selected = products[:args.limit] if args.limit else products

    print("=" * 64)
    print("COUPON WORLD PRODUCT PAGE GENERATOR")
    print("=" * 64)
    print("Products found :", len(products))
    print("Pages planned  :", len(selected))
    print("Write mode     :", "YES" if args.write else "NO")

    for product in selected[:10]:
        print("PAGE |", product.get("id") or product.get("sl_no"), "|", page_dir(product).relative_to(ROOT))

    if len(selected) > 10:
        print("...and", len(selected) - 10, "more")

    if not args.write:
        print("\nDRY RUN: no pages generated.")
        return 0

    if args.clean and OUT.exists():
        shutil.rmtree(OUT)

    for product in selected:
        folder = page_dir(product)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "index.html").write_text(render(product, products), encoding="utf-8")

    print("\nGENERATION COMPLETE")
    print("Pages generated:", len(selected))
    print("Output folder  :", OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
