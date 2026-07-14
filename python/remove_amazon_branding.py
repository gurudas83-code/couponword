#!/usr/bin/env python3

import json
import re
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(".")
BACKUP = ROOT / ".branding_backups" / datetime.now().strftime("%Y%m%d_%H%M%S")

TEXT_REPLACEMENTS = {
    "AMAZON INDIA DEALS UPDATED DAILY": "BEST ONLINE DEALS UPDATED DAILY",
    "Amazon India Deals Updated Daily": "Best Online Deals Updated Daily",
    "Amazon India deals updated daily": "Best online deals updated daily",

    "Amazon IN": "Online Store",
    "Amazon India": "Online Store",

    "Check latest price on Amazon": "Check Latest Offer",
    "Check Latest Price on Amazon": "Check Latest Offer",
    "Check price on Amazon": "Check Latest Offer",

    "View on Amazon": "View Deal",
    "View On Amazon": "View Deal",

    "Shop Now": "Get Deal",

    "Visit the Amazon IN product page": "Visit the retailer product page",
    "Visit the Amazon product page": "Visit the retailer product page",
    "on Amazon may change": "on the retailer site may change",
    "Final price on Amazon may change": "Price and availability may change",
    "jump to Amazon with one click": "visit the retailer with one click",
    "Amazon affiliate links": "retailer deal links",
    "Amazon deals": "online deals",
    "Amazon Deals": "Online Deals",
}

SKIP_JSON_KEYS = {
    "link",
    "url",
    "affiliate_link",
    "affiliate_url",
    "product_url",
    "image",
    "image_url",
}


def backup_file(path: Path) -> None:
    destination = BACKUP / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)


def clean_text(text: str) -> str:
    for old, new in TEXT_REPLACEMENTS.items():
        text = text.replace(old, new)

    text = re.sub(
        r"\bCheck latest price\s+on\s+Amazon\b",
        "Check Latest Offer",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\bView\s+on\s+Amazon\b",
        "View Deal",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\bAmazon\s+IN\b",
        "Online Store",
        text,
        flags=re.IGNORECASE,
    )

    return text


def clean_json_value(value, key=""):
    if isinstance(value, dict):
        return {
            k: clean_json_value(v, k)
            for k, v in value.items()
        }

    if isinstance(value, list):
        return [clean_json_value(item, key) for item in value]

    if isinstance(value, str):
        if key.lower() in SKIP_JSON_KEYS:
            return value
        return clean_text(value)

    return value


def process_text_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    updated = clean_text(original)

    if updated == original:
        return False

    backup_file(path)
    path.write_text(updated, encoding="utf-8")
    return True


def process_json_file(path: Path) -> bool:
    original_text = path.read_text(encoding="utf-8")
    data = json.loads(original_text)
    updated_data = clean_json_value(data)

    updated_text = json.dumps(
        updated_data,
        ensure_ascii=False,
        indent=2,
    ) + "\n"

    if updated_text == original_text:
        return False

    backup_file(path)
    path.write_text(updated_text, encoding="utf-8")
    return True


def main():
    changed = []

    text_files = [
        Path("index.html"),
        Path("app.js"),
        Path("admin.html"),
        Path("python/build_product_pages.py"),
    ]

    for path in text_files:
        if path.exists() and process_text_file(path):
            changed.append(str(path))

    json_file = Path("coupons.json")
    if json_file.exists() and process_json_file(json_file):
        changed.append(str(json_file))

    products_dir = Path("products")
    if products_dir.exists():
        for path in products_dir.rglob("*.html"):
            if process_text_file(path):
                changed.append(str(path))

    print(f"Updated files: {len(changed)}")
    for path in changed:
        print(f"  - {path}")

    print(f"\nBackup: {BACKUP}")
    print("Affiliate URLs and guru0906-21 tag were preserved.")


if __name__ == "__main__":
    main()
