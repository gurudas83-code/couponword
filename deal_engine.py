import csv
import json
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

AMAZON_TAG = "guru0906-21"
INPUT_FILE = "deals.csv"
OUTPUT_FILE = "coupons.json"

def clean(value):
    return re.sub(r"\s+", " ", str(value or "").strip())

def add_amazon_tag(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    query["tag"] = [AMAZON_TAG]
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))

def discount_text(price, mrp):
    try:
        price = float(price)
        mrp = float(mrp)
        if price > 0 and mrp > price:
            return f"{round((mrp - price) / mrp * 100)}% OFF"
    except:
        pass
    return "Check Price"

def main():
    deals = []
    seen = set()

    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            title = clean(row.get("title"))
            link = clean(row.get("link"))

            if not title or not link:
                continue

            if "amazon.in" in link:
                link = add_amazon_tag(link)

            if link in seen:
                continue
            seen.add(link)

            price = clean(row.get("price"))
            mrp = clean(row.get("mrp"))

            deals.append({
                "id": len(deals) + 1,
                "store": clean(row.get("store")) or "Amazon IN",
                "title": title,
                "category": clean(row.get("category")) or "Deals",
                "discount": discount_text(price, mrp),
                "price": f"₹{price}" if price else "",
                "mrp": f"₹{mrp}" if mrp else "",
                "save": "",
                "code": "NO CODE NEEDED",
                "link": link,
                "expiry": clean(row.get("expiry")) or "Limited Time",
                "image": "",
                "description": f"Latest deal for {title}. Check current price and offer on Coupon World.",
                "last_updated": datetime.now().strftime("%d %b %Y")
            })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(deals, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(deals)} deals.")

if __name__ == "__main__":
    main()
