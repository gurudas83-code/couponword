#!/usr/bin/env python3

import html
import json
import re
from pathlib import Path
from urllib.parse import urlparse
from xml.etree.ElementTree import Element, ElementTree, SubElement


ROOT = Path(__file__).resolve().parent.parent
COUPONS_FILE = ROOT / "coupons.json"
SITEMAP_FILE = ROOT / "sitemap.xml"

SITE_URL = "https://coupon-world.in"

LEGACY_PRODUCT_PATHS = {
    "17": "amazon-in-fashion-fest-17",
}


def clean(value):
    if value is None:
        return ""

    return " ".join(str(value).strip().split())


def slugify(value, max_length=70):
    value = clean(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-") or "product"

    if len(value) > max_length:
        value = value[:max_length].rstrip("-")

    return value


def product_identity(product):
    return str(
        product.get("id")
        or product.get("sl_no")
        or product.get("asin")
        or ""
    )


def product_path(product):
    identity = product_identity(product)

    legacy_path = LEGACY_PRODUCT_PATHS.get(identity)

    if legacy_path:
        return legacy_path

    suffix = str(
        product.get("asin")
        or product.get("id")
        or product.get("sl_no")
        or "item"
    ).lower()

    slug = slugify(product.get("title"))

    return f"{slug}-{slugify(suffix)}"


def product_url(product):
    return (
        f"{SITE_URL}/products/"
        f"{product_path(product)}/"
    )


def canonical_url(page):
    text = page.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    if re.search(
        r'<meta[^>]+name=["\']robots["\'][^>]+'
        r'content=["\'][^"\']*noindex',
        text,
        flags=re.I,
    ):
        return ""

    match = re.search(
        r'<link[^>]+rel=["\']canonical["\'][^>]+'
        r'href=["\']([^"\']+)["\']',
        text,
        flags=re.I,
    )

    if not match:
        match = re.search(
            r'<link[^>]+href=["\']([^"\']+)["\'][^>]+'
            r'rel=["\']canonical["\']',
            text,
            flags=re.I,
        )

    if not match:
        raise ValueError(
            f"Indexable page has no canonical URL: {page}"
        )

    url = html.unescape(match.group(1)).strip()
    parsed = urlparse(url)

    if parsed.scheme != "https":
        raise ValueError(
            f"Canonical must use HTTPS: {page} -> {url}"
        )

    if parsed.netloc != "coupon-world.in":
        raise ValueError(
            f"Unexpected canonical host: {page} -> {url}"
        )

    return url


def extra_page_urls():
    pages = []

    guides_dir = ROOT / "guides"

    if guides_dir.exists():
        pages.extend(
            sorted(
                guides_dir.rglob("index.html")
            )
        )

    seo_dir = ROOT / "seo"

    if seo_dir.exists():
        pages.extend(
            sorted(
                seo_dir.glob("*.html")
            )
        )

    urls = []

    for page in pages:
        url = canonical_url(page)

        if url:
            urls.append(url)

    return urls


def add_url(urlset, location, changefreq, priority):
    url = SubElement(urlset, "url")

    loc = SubElement(url, "loc")
    loc.text = location

    freq = SubElement(url, "changefreq")
    freq.text = changefreq

    rank = SubElement(url, "priority")
    rank.text = priority


def main():
    with COUPONS_FILE.open(
        encoding="utf-8"
    ) as file:
        products = json.load(file)

    if not isinstance(products, list):
        raise ValueError(
            "coupons.json must contain a JSON list"
        )

    namespace = (
        "http://www.sitemaps.org/schemas/sitemap/0.9"
    )

    urlset = Element(
        "urlset",
        {"xmlns": namespace},
    )

    seen = set()

    def add_unique(
        location,
        changefreq,
        priority,
    ):
        if location in seen:
            raise ValueError(
                f"Duplicate sitemap URL: {location}"
            )

        seen.add(location)

        add_url(
            urlset,
            location,
            changefreq,
            priority,
        )

    add_unique(
        f"{SITE_URL}/",
        "daily",
        "1.0",
    )

    included_products = 0
    skipped_products = 0

    for product in products:
        if product.get("active") is False:
            skipped_products += 1
            continue

        add_unique(
            product_url(product),
            "weekly",
            "0.8",
        )

        included_products += 1

    extras = extra_page_urls()

    for url in extras:
        add_unique(
            url,
            "monthly",
            "0.7",
        )

    tree = ElementTree(urlset)

    tree.write(
        SITEMAP_FILE,
        encoding="utf-8",
        xml_declaration=True,
    )

    print("SITEMAP GENERATED")
    print("Homepage included :", 1)
    print("Products included :", included_products)
    print("Products skipped  :", skipped_products)
    print("Extra pages       :", len(extras))
    print("Total URLs        :", len(seen))
    print("Output file       :", SITEMAP_FILE.name)


if __name__ == "__main__":
    main()
