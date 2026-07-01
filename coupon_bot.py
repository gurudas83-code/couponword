"""
CouponWorld AI Generator v3
Generates realistic Amazon IN affiliate deals for coupons.json
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

AFFILIATE_TAG = "guru0906-21"
JSON_FILE = "coupons.json"
NEW_DEALS_COUNT = 30

PRODUCTS = [
    ("boAt Airdopes 311 Pro TWS Earbuds", "Electronics", "boat+airdopes+311+pro", 999, 2999),
    ("Fire-Boltt Ninja Smartwatch", "Electronics", "fire+boltt+ninja", 999, 4999),
    ("Samsung Galaxy M16 5G", "Mobiles", "samsung+galaxy+m16", 11999, 18999),
    ("Noise ColorFit Smartwatch", "Electronics", "noise+smartwatch", 999, 5999),
    ("Milton Thermosteel Bottle", "Home", "milton+thermosteel", 399, 1499),
    ("Philips Trimmer", "Electronics", "philips+trimmer", 699, 2499),
    ("Sony Wireless Headphones", "Electronics", "sony+headphones", 1999, 14999),
    ("HP Wireless Mouse", "Electronics", "hp+wireless+mouse", 399, 1499),
    ("ASUS Gaming Laptop", "Electronics", "asus+gaming+laptop", 49990, 129990),
    ("Echo Dot 5th Gen", "Electronics", "echo+dot+5", 2499, 5499),
    ("boAt Rockerz 450 Headphones", "Electronics", "boat+rockerz+450", 999, 3999),
    ("Mi Power Bank 10000mAh", "Electronics", "mi+power+bank+10000", 799, 1999),
    ("Titan Analog Watch", "Fashion", "titan+watch", 1499, 7999),
    ("Wildcraft Backpack 35L", "Fashion", "wildcraft+backpack+35l", 999, 3999),
    ("Redmi Note 13 5G", "Mobiles", "redmi+note+13+5g", 12999, 21999),
    ("OnePlus Nord CE", "Mobiles", "oneplus+nord+ce", 17999, 27999),
    ("JBL Tune 510BT Headphones", "Electronics", "jbl+tune+510bt", 1999, 4999),
    ("Dell Inspiron Laptop", "Electronics", "dell+inspiron+laptop", 39990, 89990),
    ("Apple AirPods", "Electronics", "apple+airpods", 9999, 24900),
    ("Samsung 25L Microwave Oven", "Home", "samsung+25l+microwave+oven", 6999, 14999),
    ("Prestige Induction Cooktop", "Home", "prestige+induction+cooktop", 1499, 3999),
    ("Bajaj Ceiling Fan", "Home", "bajaj+ceiling+fan", 1299, 3499),
    ("American Tourister Trolley Bag", "Fashion", "american+tourister+trolley+bag", 2499, 9999),
    ("Puma Men's Running Shoes", "Fashion", "puma+mens+running+shoes", 1499, 6999),
    ("Levi's Men's Jeans", "Fashion", "levis+mens+jeans", 1299, 4999),
    ("Lakme Makeup Kit", "Beauty", "lakme+makeup+kit", 499, 2499),
    ("Mamaearth Skincare Combo", "Beauty", "mamaearth+skincare+combo", 399, 1999),
    ("Kindle Paperwhite", "Electronics", "kindle+paperwhite", 9999, 16999),
    ("Fire TV Stick 4K", "Electronics", "fire+tv+stick+4k", 2999, 5999),
    ("Kore Adjustable Dumbbells", "Fitness", "kore+adjustable+dumbbells", 999, 4999),
]

BADGES = [
    "🔥 HOT", "🔥 HOT", "🔥 HOT",
    "📈 TRENDING", "📈 TRENDING",
    "⚡ SELLING FAST",
    "⏳ LIMITED STOCK",
    "🆕 NEW",
    None, None
]


def load_existing_coupons():
    file = Path(JSON_FILE)
    if not file.exists():
        return []

    with file.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_amazon_link(keyword):
    return f"https://www.amazon.in/s?k={keyword}&tag={AFFILIATE_TAG}"


def random_expiry():
    return (datetime.now() + timedelta(days=random.randint(3, 14))).strftime("%d %b %Y")


def make_price(min_price, max_price):
    mrp = random.randint(min_price, max_price)

    discount_pct = random.choice([20, 25, 30, 35, 40, 45, 50, 55, 60])

    price = int(mrp * (100 - discount_pct) / 100)

    price = round(price / 10) * 10 - 1

    save = mrp - price

    discount_text = f"{discount_pct}% OFF"

    return mrp, price, save, discount_text


def random_rating():
    return round(random.uniform(4.0, 4.7), 1)


def random_reviews():
    return random.randint(500, 25000)


def random_claims():
    return random.randint(50, 1200)


def generate_new_coupons(existing):
    existing_titles = {c.get("title", "").lower() for c in existing}
    next_id = max((c.get("id", 0) for c in existing), default=0) + 1

    available = [p for p in PRODUCTS if p[0].lower() not in existing_titles]
    random.shuffle(available)

    if not available:
        print("No new products available. Add more products in PRODUCTS list.")
        return []

    new_coupons = []

    for title, category, keyword, min_price, max_price in available[:NEW_DEALS_COUNT]:
        mrp, price, save, discount = make_price(min_price, max_price)

        coupon = {
            "id": next_id,
            "store": "Amazon IN",
            "category": category,
            "discount": discount,
            "title": title,
            "code": "NO CODE NEEDED",
            "link": build_amazon_link(keyword),
            "expiry": random_expiry(),
            "badge": random.choice(BADGES),
            "claims": random_claims(),
            "rating": random_rating(),
            "reviews": random_reviews(),
            "mrp": mrp,
            "price": price,
            "save": save,
            "verified": True
        }

        new_coupons.append(coupon)
        next_id += 1

    return new_coupons


def main():
    coupons = load_existing_coupons()
    new_coupons = generate_new_coupons(coupons)

    coupons.extend(new_coupons)
    coupons.sort(key=lambda c: c["id"])

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(coupons, f, indent=2, ensure_ascii=False)

    print("=" * 50)
    print("CouponWorld AI Generator v3")
    print("=" * 50)
    print(f"Added : {len(new_coupons)}")
    print(f"Total : {len(coupons)}")
    print("Done Successfully")
    print("=" * 50)


if __name__ == "__main__":
    main()
