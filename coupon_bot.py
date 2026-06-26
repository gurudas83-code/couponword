import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# ===========================
# CONFIG
# ===========================

AFFILIATE_TAG = "guru0906-21"
JSON_FILE = "coupons.json"

# ===========================
# PRODUCT DATABASE
# ===========================

PRODUCTS = {

    "Amazon IN": [
        ("boAt Airdopes 311 Pro TWS Earbuds", "Electronics", "boat+airdopes+311+pro"),
        ("Fire-Boltt Ninja Smartwatch", "Electronics", "fire+boltt+ninja"),
        ("Samsung Galaxy M16 5G", "Mobiles", "samsung+galaxy+m16"),
        ("Noise ColorFit Smartwatch", "Electronics", "noise+smartwatch"),
        ("Milton Thermosteel Bottle", "Home", "milton+thermosteel"),
        ("Philips Trimmer", "Electronics", "philips+trimmer"),
        ("Sony Wireless Headphones", "Electronics", "sony+headphones"),
        ("HP Wireless Mouse", "Electronics", "hp+wireless+mouse"),
        ("ASUS Gaming Laptop", "Electronics", "asus+gaming+laptop"),
        ("Echo Dot 5th Gen", "Electronics", "echo+dot+5")
    ],

    "Flipkart": [
        ("Realme Narzo Smartphone", "Mobiles"),
        ("Puma Running Shoes", "Fashion"),
        ("LG Smart TV", "Electronics"),
        ("Levi's Jeans", "Fashion"),
        ("Campus Shoes", "Fashion")
    ],

    "Myntra": [
        ("Nike Running Shoes", "Fashion"),
        ("Levi's Slim Fit Jeans", "Fashion"),
        ("Roadster Shirt", "Fashion"),
        ("Adidas Hoodie", "Fashion"),
        ("HRX Sports Shoes", "Fashion")
    ],

    "Ajio": [
        ("US Polo T-Shirt", "Fashion"),
        ("Flying Machine Jeans", "Fashion"),
        ("Puma Sneakers", "Fashion")
    ],

    "Nykaa": [
        ("Lakme Foundation", "Beauty"),
        ("Mamaearth Face Wash", "Beauty"),
        ("Maybelline Lipstick", "Beauty"),
        ("Minimalist Serum", "Beauty")
    ],

    "Boat": [
        ("boAt Rockerz 450", "Electronics"),
        ("boAt Stone Speaker", "Electronics"),
        ("boAt Bassheads Earphones", "Electronics")
    ],

    "Croma": [
        ("Samsung Refrigerator", "Electronics"),
        ("Apple iPad", "Electronics"),
        ("Dell Laptop", "Electronics")
    ],

    "TataCliq": [
        ("Titan Watch", "Fashion"),
        ("Fastrack Smartwatch", "Fashion"),
        ("Casio Watch", "Fashion")
    ],

    "Snapdeal": [
        ("Kitchen Storage Set", "Home"),
        ("Wall Clock", "Home"),
        ("LED Bulb Pack", "Home")
    ],

    "Meesho": [
        ("Women's Kurti", "Fashion"),
        ("Bedsheet Set", "Home"),
        ("Kitchen Organizer", "Home")
    ]
}

# ===========================
# DISCOUNT TYPES
# ===========================

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
    "Limited Time Deal"
]

# ===========================
# LOAD EXISTING JSON
# ===========================

if Path(JSON_FILE).exists():
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        coupons = json.load(f)
else:
    coupons = []

existing_titles = {
    c.get("title", "").lower()
    for c in coupons
}

last_id = max([c.get("id", 0) for c in coupons], default=0)

NEW_COUPONS = []

# ===========================
# GENERATE
# ===========================

while len(NEW_COUPONS) < 30:

    store = random.choice(list(PRODUCTS.keys()))
    product = random.choice(PRODUCTS[store])

    title = product[0]
    category = product[1]

    if title.lower() in existing_titles:
        continue

    existing_titles.add(title.lower())

    last_id += 1

    expiry = (
        datetime.now() +
        timedelta(days=random.randint(7,45))
    ).strftime("%d %b %Y")

    if store == "Amazon IN":

        keyword = product[2]

        link = (
            f"https://www.amazon.in/s?k={keyword}"
            f"&tag={AFFILIATE_TAG}"
        )

    else:

        domain = store.lower()

        if domain == "tatacliq":
            domain = "tatacliq"

        if domain == "boat":
            domain = "boat-lifestyle"

        link = f"https://www.{domain}.com"

    NEW_COUPONS.append({

        "id": last_id,

        "store": store,

        "category": category,

        "discount": random.choice(DISCOUNTS),

        "title": title,

        "code": "NO CODE NEEDED",

        "link": link,

        "expiry": expiry

    })

# ===========================
# SAVE
# ===========================

coupons.extend(NEW_COUPONS)

coupons.sort(key=lambda x: x["id"])

with open(JSON_FILE, "w", encoding="utf-8") as f:

    json.dump(
        coupons,
        f,
        indent=2,
        ensure_ascii=False
    )

print("="*50)
print("CouponWorld AI Generator")
print("="*50)
print(f"Added : {len(NEW_COUPONS)}")
print(f"Total : {len(coupons)}")
print("Done Successfully")
print("="*50)
