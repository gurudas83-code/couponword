#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "coupons.json"
BACKUP_DIR = ROOT / ".import_backups"
CORRECT_TAG = "guru0906-21"

REQUIRED_FIELDS = ("title", "category", "link")


def load_existing() -> list[dict]:
    data = json.loads(DB.read_text(encoding="utf-8"))

    if not isinstance(data, list):
        raise ValueError("coupons.json must contain a list")

    return data


def clean(value: object) -> str:
    return str(value or "").strip()


def parse_int(value: object) -> int | None:
    value = clean(value)

    if not value:
        return None

    number = float(value)

    if number < 0:
        raise ValueError("numeric values cannot be negative")

    return int(number)


def get_tag(url: str) -> str | None:
    return parse_qs(urlparse(url).query).get("tag", [None])[0]


def normalize_row(row: dict[str, str]) -> dict:
    product = {
        "title": clean(row.get("title")),
        "category": clean(row.get("category")),
        "link": clean(row.get("link")),
        "store": clean(row.get("store")) or "Online Store",
        "discount": clean(row.get("discount")) or "Check Deal",
        "code": clean(row.get("code")) or "No code",
        "expiry": clean(row.get("expiry")),
    }

    optional_text = (
        "badge",
        "priceText",
        "linkType",
        "asin",
        "image",
        "description",
    )

    for key in optional_text:
        value = clean(row.get(key))

        if value:
            product[key] = value

    for key in ("price", "mrp", "save"):
        value = parse_int(row.get(key))

        if value is not None:
            product[key] = value

    return product


def read_csv(csv_path: Path) -> list[tuple[int, dict]]:
    rows: list[tuple[int, dict]] = []

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)

        if not reader.fieldnames:
            raise ValueError("CSV header missing")

        for number, raw in enumerate(reader, start=2):
            rows.append((number, normalize_row(raw)))

    return rows


def validate_rows(
    existing: list[dict],
    rows: list[tuple[int, dict]],
) -> tuple[list[str], list[tuple[int, dict]]]:
    errors: list[str] = []
    accepted: list[tuple[int, dict]] = []

    existing_links = {
        clean(item.get("link"))
        for item in existing
        if clean(item.get("link"))
    }

    existing_asins = {
        clean(item.get("asin")).upper()
        for item in existing
        if clean(item.get("asin"))
    }

    seen_links: set[str] = set()
    seen_asins: set[str] = set()

    for line_number, product in rows:
        line_errors = 0

        for field in REQUIRED_FIELDS:
            if not product.get(field):
                errors.append(
                    f"Line {line_number}: missing required field '{field}'"
                )
                line_errors += 1

        link = product.get("link", "")
        asin = clean(product.get("asin")).upper()

        if link:
            tag = get_tag(link)

            if tag != CORRECT_TAG:
                errors.append(
                    f"Line {line_number}: affiliate tag must be {CORRECT_TAG}"
                )
                line_errors += 1

            if link in existing_links:
                errors.append(
                    f"Line {line_number}: duplicate link already in database"
                )
                line_errors += 1

            if link in seen_links:
                errors.append(
                    f"Line {line_number}: duplicate link inside CSV"
                )
                line_errors += 1

            seen_links.add(link)

        if asin:
            if asin in existing_asins:
                errors.append(
                    f"Line {line_number}: duplicate ASIN already in database"
                )
                line_errors += 1

            if asin in seen_asins:
                errors.append(
                    f"Line {line_number}: duplicate ASIN inside CSV"
                )
                line_errors += 1

            seen_asins.add(asin)

        if line_errors == 0:
            accepted.append((line_number, product))

    return errors, accepted


def next_id(existing: list[dict]) -> int:
    ids = [
        int(item.get("id"))
        for item in existing
        if str(item.get("id", "")).isdigit()
    ]

    return max(ids, default=0) + 1


def write_atomic(products: list[dict]) -> None:
    temp = DB.with_suffix(".json.tmp")

    temp.write_text(
        json.dumps(products, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    temp.replace(DB)


def run_build() -> int:
    result = subprocess.run(
        [
            sys.executable,
            "python/couponworld.py",
            "build",
        ],
        cwd=ROOT,
    )

    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Coupon World product importer"
    )

    parser.add_argument("csv_file")

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preview", action="store_true")
    mode.add_argument("--write", action="store_true")

    args = parser.parse_args()

    csv_path = Path(args.csv_file)

    if not csv_path.exists():
        print(f"CSV file not found: {csv_path}")
        return 1

    try:
        existing = load_existing()
        rows = read_csv(csv_path)
        errors, accepted = validate_rows(existing, rows)
    except (ValueError, json.JSONDecodeError, OSError) as exc:
        print(f"IMPORT FAILED: {exc}")
        return 1

    print("=" * 68)
    print("COUPON WORLD PRODUCT IMPORTER")
    print("=" * 68)
    print("Existing products :", len(existing))
    print("CSV rows          :", len(rows))
    print("Accepted rows     :", len(accepted))
    print("Validation errors :", len(errors))

    if errors:
        print()
        print("ERRORS")
        print("-" * 68)

        for error in errors:
            print("FAIL:", error)

        print()
        print("IMPORT STATUS: REJECTED")
        return 1

    first_id = next_id(existing)

    prepared: list[dict] = []

    print()
    print("PRODUCTS TO IMPORT")
    print("-" * 68)

    for offset, (line_number, product) in enumerate(accepted):
        item = dict(product)
        item["id"] = first_id + offset
        prepared.append(item)

        print(
            f"CSV line {line_number} -> ID {item['id']} | "
            f"{item['title']} | {item['category']}"
        )

    if args.preview:
        print()
        print("IMPORT STATUS: PREVIEW PASS")
        print("No files were modified.")
        return 0

    if not prepared:
        print()
        print("IMPORT STATUS: NOTHING TO IMPORT")
        return 0

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"coupons_{stamp}.json"

    shutil.copy2(DB, backup_file)

    print()
    print(f"Backup created: {backup_file.relative_to(ROOT)}")

    updated = existing + prepared

    try:
        write_atomic(updated)

        print(f"Database updated: {len(existing)} -> {len(updated)}")
        print()
        print("Running controlled site build...")

        build_code = run_build()

        if build_code != 0:
            raise RuntimeError(
                "Controlled build failed after database update"
            )

    except Exception as exc:
        shutil.copy2(backup_file, DB)

        print()
        print(f"IMPORT FAILED: {exc}")
        print("Original coupons.json restored.")
        return 1

    print()
    print("=" * 68)
    print("IMPORT STATUS: PASS")
    print("=" * 68)
    print("Products imported :", len(prepared))
    print("Products total    :", len(updated))
    print("Backup            :", backup_file.relative_to(ROOT))
    print("Site build        : PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
