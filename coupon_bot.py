import json, datetime

tag = "guru0906-21"

new_deals = [
    {"store": "Myntra", "title": "Fashion 60% OFF", "code": "STYLE60", "discount": "60% OFF"},
    {"store": "Ajio", "title": "Shoes Flat ₹800", "code": "AJIO800", "discount": "₹800 OFF"},
]

with open('coupons.json', 'r') as f:
    coupons = json.load(f)

for deal in new_deals:
    coupons.append({
        "id": len(coupons) + 1,
        "store": deal["store"],
        "title": deal["title"],
        "code": deal["code"],
        "discount": deal["discount"],
        "expiry": "31 Dec 2026",
        "link": f"https://amazon.in?tag={tag}",
        "category": "Shopping"
    })

with open('coupons.json', 'w') as f:
    json.dump(coupons, f, indent=2)

print(f"✅ Bot added {len(new_deals)} coupons. Total: {len(coupons)}")
