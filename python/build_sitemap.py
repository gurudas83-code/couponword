#!/usr/bin/env python3

import json
import re
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree

ROOT = Path(__file__).resolve().parent.parent
COUPONS_FILE = ROOT / "coupons.json"
SITEMAP_FILE = ROOT / "sitemap.xml"
SITE_URL = "https://coupon-word.in"


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


def product_url(product):
    suffix = str(
        product.get("asin")
        or product.get("id")
        or product.get("sl_no")
        or "item"
    ).lower()

    slug = slugify(product.get("title"))

    return f"{SITE_URL}/products/{slug}-{suffix}/"


def add_url(urlset, location, changefreq, priority):
    url = SubElement(urlset, "url")

    loc = SubElement(url, "loc")
    loc.text = location

    freq = SubElement(url, "changefreq")
    freq.text = changefreq

    rank = SubElement(url, "priority")
    rank.text = priority


def main():
    with COUPONS_FILE.open(encoding="utf-8") as file:
        products = json.load(file)

    if not isinstance(products, list):
        raise ValueError("coupons.json must contain a JSON list")

    namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"
    urlset = Element(
        "urlset",
        {"xmlns": namespace},
    )

    add_url(
        urlset,
        f"{SITE_URL}/",
        "daily",
        "1.0",
    )

    included = 0
    skipped = 0

    for product in products:
        if product.get("active") is False:
            skipped += 1
            continue

        add_url(
            urlset,
            product_url(product),
            "weekly",
            "0.8",
        )

        included += 1

    tree = ElementTree(urlset)

    tree.write(
        SITEMAP_FILE,
        encoding="utf-8",
        xml_declaration=True,
    )

    print("SITEMAP GENERATED")
    print("Homepage included :", 1)
    print("Products included :", included)
    print("Products skipped  :", skipped)
    print("Total URLs        :", included + 1)
    print("Output file       :", SITEMAP_FILE.name)


if __name__ == "__main__":
    main()
