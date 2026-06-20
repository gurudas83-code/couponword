import json, random
from datetime import datetime, timedelta

tag = "guru0906-21"

# 30 coupon का data
stores = ["Amazon IN", "Flipkart", "Myntra", "Ajio", "Nykaa", "Boat", "Croma", "TataCliq", "Snapdeal", "Meesho"]
titles = ["Mega Sale", "Fashion Fest", "Tech Deal", "Beauty Offer", "Winter Sale", "Flash Deal", "Big Discount", "Loot Offer", "Special Offer", "Limited Deal"]
discounts = ["70% OFF", "60% OFF", "50% OFF", "40% OFF", "₹2000 OFF", "₹1000 OFF", "₹500 OFF", "Buy 1 Get 1", "Flat 45% OFF", "Up to 80% OFF"]
codes = ["MEGA", "STYLE", "TECH", "BEAUTY", "WINTER", "FLASH", "DEAL", "LOOT", "SAVE", "GRAB"]

# पुरानी file पढ़ो
with open('coupons.json', 'r') as f:
    coupons = json.load(f)

last_id = coupons[-1]["id"] if coupons else 0
new_deals = []

# 30 नए coupon बनाओ
for i in range(30):
    last_id += 1
    store = random.choice(stores)
    new_deals.append({
        "id": last_id,
        "store": store,
        "title": f"{store} {random.choice(titles)}",
        "code": random.choice(codes) + str(random.randint(10,99)),
        "discount": random.choice(discounts),
        "expiry": (datetime.now() + timedelta(days=random.randint(7,60))).strftime("%d %b %Y"),
        "link": f"https://{store.lower().replace(' ','')}.in?tag={tag}",
        "category": random.choice(["Shopping", "Fashion", "Tech", "Beauty", "Food"])
    })

# JSON में जोड़ दो
coupons.extend(new_deals)

with open('coupons.json', 'w') as f:
    json.dump(coupons, f, indent=2)

print(f"✅ Bot added {len(new_deals)} coupons. Total: {len(coupons)}")
