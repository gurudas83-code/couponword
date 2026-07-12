#!/usr/bin/env python3
import argparse, json, shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "coupons.json"
BACKUPS = ROOT / "backups"

def load():
    data = json.loads(DB.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("coupons.json must contain a list")
    return data

def save(data):
    tmp = DB.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(DB)

def backup():
    BACKUPS.mkdir(exist_ok=True)
    p = BACKUPS / f"coupons-before-status-update-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    shutil.copy2(DB, p)
    return p

def num(v):
    v = str(v or "").replace("₹","").replace(",","").strip()
    if not v: return ""
    n = float(v)
    return int(n) if n.is_integer() else n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("asin")
    ap.add_argument("status", choices=["available","unavailable"])
    ap.add_argument("--price", default="")
    ap.add_argument("--mrp", default="")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    data = load()
    p = next((x for x in data if str(x.get("asin","")).upper() == a.asin.upper()), None)
    if not p:
        print("ERROR: ASIN not found:", a.asin.upper())
        return 1

    proposed = dict(p)
    proposed["availability"] = a.status
    proposed["active"] = a.status == "available"
    proposed["amazon_checked_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    if a.status == "unavailable":
        for k in ("price","mrp","save","discount"):
            proposed[k] = None
    else:
        if a.price: proposed["price"] = num(a.price)
        if a.mrp: proposed["mrp"] = num(a.mrp)
        price, mrp = proposed.get("price",""), proposed.get("mrp","")
        if price != "" and mrp != "" and float(mrp) >= float(price) > 0:
            saving = float(mrp) - float(price)
            proposed["save"] = int(saving) if saving.is_integer() else round(saving,2)
            proposed["discount"] = f"{round(saving/float(mrp)*100)}% OFF" if saving > 0 else ""

    print("="*60)
    print("ASIN         :", proposed.get("asin"))
    print("Title        :", proposed.get("title"))
    print("Availability :", proposed.get("availability"))
    print("Active       :", proposed.get("active"))
    print("Price        :", proposed.get("price",""))
    print("MRP          :", proposed.get("mrp",""))
    print("Discount     :", proposed.get("discount",""))
    print("="*60)

    if not a.write:
        print("DRY RUN: coupons.json was not changed.")
        return 0

    b = backup()
    p.clear(); p.update(proposed)
    save(data)
    print("UPDATE COMPLETE")
    print("Backup created:", b.relative_to(ROOT))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
