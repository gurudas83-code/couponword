import json, shutil, re
from pathlib import Path
from urllib.parse import quote_plus

AFFILIATE_TAG = "guru0906-21"
JSON_FILE = Path("coupons.json")
BACKUP_FILE = Path("coupons.backup.json")

PRODUCTS = [
    ("boAt Airdopes 311 Pro TWS Earbuds", "Electronics", "boat airdopes 311 pro"),
    ("Fire-Boltt Ninja Smartwatch", "Electronics", "fire boltt ninja"),
    ("Samsung Galaxy M16 5G", "Mobiles", "samsung galaxy m16"),
    ("Milton Thermosteel Bottle", "Home", "milton thermosteel"),
    ("Philips Trimmer", "Electronics", "philips trimmer"),
]

def load_existing():
    if not JSON_FILE.exists():
        return []

    text = JSON_FILE.read_text(encoding="utf-8").strip()

    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
    except json.JSONDecodeError:
        pass

    print("WARNING: Invalid coupons.json found. Backup created and fresh file will be generated.")
    shutil.copy2(JSON_FILE, BACKUP_FILE)
    return []

def amazon_link(keyword):
    return f"https://www.amazon.in/s?k={quote_plus(keyword)}&tag={AFFILIATE_TAG}"

def normalize(text):
    return re.sub(r"\s+", " ", str(text).lower().strip())

def main():
    existing = load_existing()
    seen_titles = {normalize(d.get("title", "")) for d in existing}
    seen_links = {d.get("link", "") for d in existing}

    deals = existing[:]
    next_id = max([int(d.get("id", 0)) for d in deals if str(d.get("id", "")).isdigit()] or [0]) + 1

    for title, category, keyword in PRODUCTS:
        link = amazon_link(keyword)

        if normalize(title) in seen_titles or link in seen_links:
            continue

        deals.append({
            "id": next_id,
            "store": "Amazon IN",
            "category": category,
            "discount": "Check Price",
            "title": title,
            "code": "NO CODE NEEDED",
            "link": link,
            "expiry": "Limited Time",
            "image": "",
            "description": f"Latest Amazon India deal for {title}. Check current price on Amazon."
        })

        next_id += 1

    deals.sort(key=lambda x: int(x.get("id", 0)))

    JSON_FILE.write_text(json.dumps(deals, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Generated valid coupons.json with {len(deals)} deals.")

if __name__ == "__main__":
    main()
