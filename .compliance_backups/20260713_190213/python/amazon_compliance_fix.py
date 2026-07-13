#!/usr/bin/env python3

import argparse
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP_DIRS = {
    ".git",
    ".github",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".compliance_backups",
}

TEXT_EXTENSIONS = {
    ".html",
    ".htm",
    ".js",
    ".json",
    ".py",
    ".css",
    ".md",
    ".txt",
    ".xml",
    ".yml",
    ".yaml",
}

REPLACEMENTS = {
    "Amazon|IN": "Online Retailer",
    "Amazon | IN": "Online Retailer",
    "Amazon IN": "Online Retailer",
    "Amazon India Deals Updated Daily": "Today's Best Deals Updated Daily",
    "AMAZON INDIA DEALS UPDATED DAILY": "TODAY'S BEST DEALS UPDATED DAILY",
    "Amazon India Deals": "Today's Best Deals",
    "Amazon deals updated daily": "Deals updated daily",

    "Check latest price on Amazon": "Check Latest Price",
    "Check Latest Price on Amazon": "Check Latest Price",
    "Check price on Amazon": "Check Latest Price",
    "Check Price on Amazon": "Check Latest Price",

    "View on Amazon": "View Deal",
    "View On Amazon": "View Deal",
    "Shop on Amazon": "Shop Now",
    "Shop On Amazon": "Shop Now",
    "Buy on Amazon": "View Deal",
    "Buy Now on Amazon": "View Deal",

    "Visit the Amazon IN product page": "Visit the retailer's product page",
    "Visit the Amazon product page": "Visit the retailer's product page",
    "Visit Amazon for the latest price": "Visit the retailer for the latest price",

    "Final price and availability are confirmed on Amazon.":
        "Final price and availability are shown on the retailer's product page.",

    "Affiliate link. Final price and availability are confirmed on Amazon.":
        "Affiliate link. Final price and availability are shown on the retailer's product page.",

    "Affiliate link. Final price, availability and delivery are determined by Amazon.":
        "Affiliate link. Final price, availability and delivery are determined by the retailer.",

    "Final price on Amazon may change":
        "Final price and availability may change on the retailer's product page",

    "Final price and availability on Amazon may change":
        "Final price and availability may change on the retailer's product page",

    "Available on Amazon": "Available from the retailer",
    "Sold on Amazon": "Available from the retailer",
}


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def iter_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if should_skip(path.relative_to(ROOT)):
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        yield path


def read_text(path: Path):
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def apply_replacements(text: str):
    updated = text
    changes = []

    for old, new in REPLACEMENTS.items():
        count = updated.count(old)
        if count:
            updated = updated.replace(old, new)
            changes.append((old, new, count))

    return updated, changes


def backup_file(path: Path, backup_root: Path):
    relative = path.relative_to(ROOT)
    destination = backup_root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)


def run_build():
    build_script = ROOT / "python" / "build_site.py"

    if not build_script.exists():
        print("\nBuild skipped: python/build_site.py not found.")
        return

    print("\nRunning site build...")
    result = subprocess.run(
        ["python", str(build_script)],
        cwd=ROOT,
        check=False,
    )

    if result.returncode != 0:
        raise SystemExit(
            f"\nERROR: build_site.py failed with exit code {result.returncode}"
        )

    print("Site build completed successfully.")


def remaining_mentions():
    results = []

    for path in iter_files():
        text = read_text(path)
        if text is None:
            continue

        for line_number, line in enumerate(text.splitlines(), start=1):
            lowered = line.lower()

            if "amazon" not in lowered:
                continue

            # Affiliate destinations and approved tracking tags are not changed.
            safe_link_terms = (
                "amazon.in",
                "amzn.to",
                "amazon-adsystem",
                "guru0906-21",
                "?tag=",
                "&tag=",
            )

            if any(term in lowered for term in safe_link_terms):
                continue

            results.append(
                (
                    str(path.relative_to(ROOT)),
                    line_number,
                    line.strip()[:220],
                )
            )

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Remove prominent Amazon branding without changing affiliate links."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Apply changes. Without this option, only a dry run is performed.",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Run python/build_site.py after applying changes.",
    )
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = ROOT / ".compliance_backups" / timestamp

    changed_files = 0
    total_replacements = 0

    print("=" * 72)
    print("COUPON WORLD — AMAZON TRADEMARK WORDING CLEANUP")
    print("=" * 72)
    print("Mode:", "WRITE" if args.write else "DRY RUN")
    print("Affiliate tag guru0906-21 will not be changed.")
    print("Amazon destination URLs will not be changed.\n")

    for path in iter_files():
        original = read_text(path)
        if original is None:
            continue

        updated, changes = apply_replacements(original)

        if not changes:
            continue

        relative = path.relative_to(ROOT)
        changed_files += 1

        print(f"[CHANGE] {relative}")

        for old, new, count in changes:
            total_replacements += count
            print(f"  {count} × {old!r}")
            print(f"      -> {new!r}")

        if args.write:
            backup_file(path, backup_root)
            path.write_text(updated, encoding="utf-8")

    print("\n" + "=" * 72)
    print(f"Files affected     : {changed_files}")
    print(f"Text replacements  : {total_replacements}")

    if not args.write:
        print("\nNothing was changed.")
        print("Run again using --write to apply the cleanup.")
        return

    print(f"Backup directory   : {backup_root.relative_to(ROOT)}")

    if args.build:
        run_build()

    leftovers = remaining_mentions()

    print("\n" + "=" * 72)
    print("REMAINING NON-URL AMAZON MENTIONS")
    print("=" * 72)

    if not leftovers:
        print("PASS: No remaining visible Amazon wording detected.")
    else:
        for filename, line_number, line in leftovers:
            print(f"{filename}:{line_number}: {line}")

        print(
            "\nReview these remaining mentions manually. "
            "Affiliate destination URLs were intentionally preserved."
        )


if __name__ == "__main__":
    main()
