"""
CouponWorld Generator v4
Generates real Amazon IN affiliate deal entries for coupons.json.

Design principle: this script only writes fields it can actually
guarantee are true. It does NOT fabricate ratings, review counts,
"verified" status, or urgency claims -- those would be false claims
sitting next to a real, live affiliate link, which is a compliance
risk and against the "no fake data" rule for this project.
"""

import json
import random
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus, urlparse

AFFILIATE_TAG = "guru0906-21"
JSON_FILE = Path("coupons.json")
BACKUP_FILE = Path("coupons.backup.json")
NEW_DEALS_COUNT = 30
ALLOWED_DOMAIN = "www.amazon.in"

# (title, category, search_keyword)
PRODUCTS = [
    ("boAt Airdopes 311 Pro TWS Earbuds", "Electronics", "boat airdopes 311 pro"),
    ("Fire-Boltt Ninja Smartwatch", "Electronics", "fire boltt ninja"),
    ("Samsung Galaxy M16 5G", "Mobiles", "samsung galaxy m16"),
    ("Noise ColorFit Smartwatch", "Electronics", "noise smartwatch"),
    ("Milton Thermosteel Bottle", "Home", "milton thermosteel"),
    ("Philips Trimmer", "Electronics", "philips trimmer"),
    ("Sony Wireless Headphones", "Electronics", "sony headphones"),
    ("HP Wireless Mouse", "Electronics", "hp wireless mouse"),
    ("ASUS Gaming Laptop", "Electronics", "asus gaming laptop"),
    ("Echo Dot 5th Gen", "Electronics", "echo dot 5"),
    ("boAt Rockerz 450 Headphones", "Electronics", "boat rockerz 450"),
    ("Mi Power Bank 10000mAh", "Electronics", "mi power bank 10000"),
    ("Titan Analog Watch", "Fashion", "titan watch"),
    ("Wildcraft Backpack 35L", "Fashion", "wildcraft backpack 35l"),
    ("Redmi Note 13 5G", "Mobiles", "redmi note 13 5g"),
    ("OnePlus Nord CE", "Mobiles", "oneplus nord ce"),
    ("JBL Tune 510BT Headphones", "Electronics", "jbl tune 510bt"),
    ("Dell Inspiron Laptop", "Electronics", "dell inspiron laptop"),
    ("Apple AirPods", "Electronics", "apple airpods"),
    ("Samsung 25L Microwave Oven", "Home", "samsung 25l microwave oven"),
    ("Prestige Induction Cooktop", "Home", "prestige induction cooktop"),
    ("Bajaj Ceiling Fan", "Home", "bajaj ceiling fan"),
    ("American Tourister Trolley Bag", "Fashion", "american tourister trolley bag"),
    ("Puma Men's Running Shoes", "Fashion", "puma mens running shoes"),
    ("Levi's Men's Jeans", "Fashion", "levis mens jeans"),
    ("Lakme Makeup Kit", "Beauty", "lakme makeup kit"),
    ("Mamaearth Skincare Combo", "Beauty", "mamaearth skincare combo"),
    ("Kindle Paperwhite", "Electronics", "kindle paperwhite"),
    ("Fire TV Stick 4K", "Electronics", "fire tv stick 4k"),
    ("Kore Adjustable Dumbbells", "Fitness", "kore adjustable dumbbells"),
]


def normalize_title(title: str) -> str:
    """Collapse whitespace and lowercase, so near-duplicate titles still match."""
    return " ".join(title.lower().split())


def load_existing_coupons() -> list:
    if not JSON_FILE.exists():
        print(f"No existing {JSON_FILE} found -- starting fresh.")
        return []

    try:
        with JSON_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise SystemExit(
            f"ERROR: {JSON_FILE} is not valid JSON ({e}). "
            "Fix or restore it before running the generator."
        )

    if not isinstance(data, list):
        raise SystemExit(f"ERROR: {JSON_FILE} does not contain a JSON array at the top level.")

    return data


def build_amazon_link(keyword: str) -> str:
    encoded = quote_plus(keyword)
    link = f"https://{ALLOWED_DOMAIN}/s?k={encoded}&tag={AFFILIATE_TAG}"
    validate_link(link)
    return link


def validate_link(link: str) -> None:
    """Refuse to write a link that isn't actually pointing at amazon.in with our tag."""
    parsed = urlparse(link)
    if parsed.netloc != ALLOWED_DOMAIN:
        raise ValueError(f"Refusing to write non-Amazon link: {link}")
    if AFFILIATE_TAG not in link:
        raise ValueError(f"Refusing to write link missing affiliate tag: {link}")


def random_expiry_label() -> str:
    """
    Only two honest options: either we don't claim an expiry at all,
    or we give a real forward-looking window. No fake countdowns.
    """
    return "Limited Time"


def generate_new_coupons(existing: list) -> list:
    existing_titles = {normalize_title(c.get("title", "")) for c in existing}
    existing_links = {c.get("link", "") for c in existing}

    next_id = max((c.get("id", 0) for c in existing), default=0) + 1

    available = [p for p in PRODUCTS if normalize_title(p[0]) not in existing_titles]
    random.shuffle(available)

    if not available:
        print("No new products available -- add more entries to PRODUCTS.")
        return []

    new_coupons = []

    for title, category, keyword in available[:NEW_DEALS_COUNT]:
        try:
            link = build_amazon_link(keyword)
        except ValueError as e:
            print(f"Skipping '{title}': {e}")
            continue

        if link in existing_links:
            print(f"Skipping '{title}': link already exists.")
            continue

        coupon = {
            "id": next_id,
            "store": "Amazon IN",
            "category": category,
            "discount": "Check Deal",
            "title": title,
            "code": "NO CODE NEEDED",
            "link": link,
            "expiry": random_expiry_label(),
            "badge": None,
            # No "verified" field: we cannot actually verify live price/stock,
            # so we don't claim to have.
        }

        new_coupons.append(coupon)
        existing_links.add(link)
        next_id += 1

    return new_coupons


def save_coupons(coupons: list) -> None:
    if JSON_FILE.exists():
        shutil.copy2(JSON_FILE, BACKUP_FILE)

    tmp_file = JSON_FILE.with_suffix(".json.tmp")
    with tmp_file.open("w", encoding="utf-8") as f:
        json.dump(coupons, f, indent=2, ensure_ascii=False)

    tmp_file.replace(JSON_FILE)  # atomic on POSIX and Windows


def main():
    coupons = load_existing_coupons()
    new_coupons = generate_new_coupons(coupons)

    coupons.extend(new_coupons)
    coupons.sort(key=lambda c: c.get("id", 0))

    save_coupons(coupons)

    print("=" * 50)
    print("CouponWorld Generator v4")
    print("=" * 50)
    print(f"Added : {len(new_coupons)}")
    print(f"Total : {len(coupons)}")
    if JSON_FILE.exists() and BACKUP_FILE.exists():
        print(f"Backup: {BACKUP_FILE}")
    print("Done.")
    print("=" * 50)


if __name__ == "__main__":
    main()
