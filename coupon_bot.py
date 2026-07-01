"""
CouponWorld AI Generator
Generates fresh Amazon IN affiliate deals and appends them to coupons.json
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# ===========================
# CONFIG
# ===========================

AFFILIATE_TAG = "guru0906-21"
JSON_FILE = "coupons.json"
NEW_DEALS_COUNT = 30

# ===========================
# PRODUCT DATABASE (Amazon IN only)
# Format: (title, category, search_keyword)
# ===========================

PRODUCTS = [
    ("boAt Airdopes 311 Pro TWS Earbuds", "Electronics", "boat+airdopes+311+pro"),
    ("Fire-Boltt Ninja Smartwatch", "Electronics", "fire+boltt+ninja"),
    ("Samsung Galaxy M16 5G", "Mobiles", "samsung+galaxy+m16"),
    ("Noise ColorFit Smartwatch", "Electronics", "noise+smartwatch"),
    ("Milton Thermosteel Bottle", "Home", "milton+thermosteel"),
    ("Philips Trimmer", "Electronics", "philips+trimmer"),
    ("Sony Wireless Headphones", "Electronics", "sony+headphones"),
    ("HP Wireless Mouse", "Electronics", "hp+wireless+mouse"),
    ("ASUS Gaming Laptop", "Electronics", "asus+gaming+laptop"),
    ("Echo Dot 5th Gen", "Electronics", "echo+dot+5"),
    ("boAt Rockerz 450 Headphones", "Electronics", "boat+rockerz+450"),
    ("boAt Stone Bluetooth Speaker", "Electronics", "boat+stone+speaker"),
    ("Mi Power Bank 10000mAh", "Electronics", "mi+power+bank+10000"),
    ("Titan Analog Watch", "Fashion", "titan+watch"),
    ("Wildcraft Backpack 35L", "Fashion", "wildcraft+backpack+35l"),
    ("Redmi Note 13 5G", "Mobiles", "redmi+note+13+5g"),
    ("OnePlus Nord CE", "Mobiles", "oneplus+nord+ce"),
    ("Realme Buds T100", "Electronics", "realme+buds+t100"),
    ("JBL Tune 510BT Headphones", "Electronics", "jbl+tune+510bt"),
    ("Logitech Wireless Keyboard Combo", "Electronics", "logitech+wireless+keyboard+combo"),
    ("Dell Inspiron Laptop", "Electronics", "dell+inspiron+laptop"),
    ("Apple AirPods", "Electronics", "apple+airpods"),
    ("Samsung 25L Microwave Oven", "Home", "samsung+25l+microwave+oven"),
    ("Prestige Induction Cooktop", "Home", "prestige+induction+cooktop"),
    ("Bajaj Ceiling Fan", "Home", "bajaj+ceiling+fan"),
    ("Cello Water Bottle Set", "Home", "cello+water+bottle+set"),
    ("American Tourister Trolley Bag", "Fashion", "american+tourister+trolley+bag"),
    ("Puma Men's Running Shoes", "Fashion", "puma+mens+running+shoes"),
    ("Levi's Men's Jeans", "Fashion", "levis+mens+jeans"),
    ("Lakme Makeup Kit", "Beauty", "lakme+makeup+kit"),
    ("Mamaearth Skincare Combo", "Beauty", "mamaearth+skincare+combo"),
    ("Kindle Paperwhite", "Electronics", "kindle+paperwhite"),
    ("Fire TV Stick 4K", "Electronics", "fire+tv+stick+4k"),
    ("Boult Audio Bluetooth Speaker", "Electronics", "boult+audio+bluetooth+speaker"),
    ("Strauss Yoga Mat", "Fitness", "strauss+yoga+mat"),
    ("Kore Adjustable Dumbbells", "Fitness", "kore+adjustable+dumbbells"),
]

DISCOUNTS = [
    "Deal Price",
    "Lightning Deal",
    "Up to 80% OFF",
    "Up to 70% OFF",
    "Flat 50% OFF",
    "Extra 10% Coupon",
    "Extra ₹500 OFF",
    "Extra ₹1000 OFF",
    "Bank Offer",
    "Limited Time Deal",
]

# Urgency/social-proof badges shown on deal cards to boost click-through.
# Weighted so "HOT"/"TRENDING" appear more often than rarer high-urgency tags.
BADGES = [
    "🔥 HOT", "🔥 HOT", "🔥 HOT",
    "📈 TRENDING", "📈 TRENDING",
    "⚡ SELLING FAST",
    "⏳ LIMITED STOCK",
    "🆕 NEW",
    None, None, None,  # some deals get no badge, keeps it believable
]


def load_existing_coupons(path: str) -> list[dict]:
    """Load existing coupons.json, or return an empty list if it doesn't exist."""
    file = Path(path)
    if not file.exists():
        return []
    with file.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_amazon_link(keyword: str) -> str:
    """Build an Amazon IN search link with the affiliate tag applied."""
    return f"https://www.amazon.in/s?k={keyword}&tag={AFFILIATE_TAG}"


def random_expiry(min_days: int = 3, max_days: int = 14) -> str:
    """Return a near-future expiry date string, e.g. '04 Jul 2026'.

    Kept short (3-14 days) on purpose: a deal expiring soon creates urgency
    and converts better than one expiring months out.
    """
    days_ahead = random.randint(min_days, max_days)
    return (datetime.now() + timedelta(days=days_ahead)).strftime("%d %b %Y")


def random_claims_count() -> int:
    """Return a plausible 'people claimed this' social-proof number."""
    return random.randint(35, 980)


def random_rating() -> float:
    """Return a plausible Amazon-style star rating (most products skew 3.8-4.8)."""
    return round(random.uniform(3.8, 4.8), 1)


def random_price_pair() -> tuple[int, int]:
    """Return (original_price, deal_price) so the site can show a rupee savings amount.

    'Save ₹1,200' next to a price is a stronger visitor magnet than a
    percentage alone, since it's concrete and skimmable.
    """
    original = random.choice([499, 699, 999, 1299, 1499, 1999, 2499, 2999,
                               3999, 4999, 6999, 9999, 14999, 19999, 24999])
    discount_pct = random.uniform(0.20, 0.65)
    deal_price = int(original * (1 - discount_pct))
    return original, deal_price


def generate_new_coupons(existing: list[dict], count: int) -> list[dict]:
    """Generate `count` new, non-duplicate Amazon coupon entries."""
    existing_titles = {c.get("title", "").lower() for c in existing}
    next_id = max((c.get("id", 0) for c in existing), default=0) + 1

    available = [p for p in PRODUCTS if p[0].lower() not in existing_titles]
    random.shuffle(available)

    new_coupons = []
    for title, category, keyword in available[:count]:
        original_price, deal_price = random_price_pair()
        new_coupons.append({
            "id": next_id,
            "store": "Amazon IN",
            "category": category,
            "discount": random.choice(DISCOUNTS),
            "title": title,
            "code": "NO CODE NEEDED",
            "link": build_amazon_link(keyword),
            "expiry": random_expiry(),
            "badge": random.choice(BADGES),
            "claims": random_claims_count(),
            "rating": random_rating(),
            # NOTE: field names below (mrp / price / save) match what
            # index.html's renderCard() actually reads. Using different
            # names here means the price block silently won't render.
            "mrp": original_price,
            "price": deal_price,
            "save": original_price - deal_price,
        })
        next_id += 1

    return new_coupons


def main():
    coupons = load_existing_coupons(JSON_FILE)
    new_coupons = generate_new_coupons(coupons, NEW_DEALS_COUNT)

    coupons.extend(new_coupons)
    coupons.sort(key=lambda c: c["id"])

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(coupons, f, indent=2, ensure_ascii=False)

    print("=" * 50)
    print("CouponWorld AI Generator")
    print("=" * 50)
    print(f"Added : {len(new_coupons)}")
    print(f"Total : {len(coupons)}")
    print("Done Successfully")
    print("=" * 50)


if __name__ == "__main__":
    main()
