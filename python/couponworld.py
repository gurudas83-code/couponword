#!/usr/bin/env python3

"""
Coupon World Control Center v1

Current command:
    python python/couponworld.py check

Purpose:
- Validate coupons.json
- Verify product/page/sitemap counts
- Verify affiliate tags
- Detect duplicate products and links
- Detect missing required fields
- Detect stale or missing generated product pages
- Detect unwanted public-facing retailer wording
- Return PASS or FAIL with proper exit code

READ-ONLY:
This script does not modify the website.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent.parent
COUPONS_FILE = ROOT / "coupons.json"
PRODUCTS_DIR = ROOT / "products"
SITEMAP_FILE = ROOT / "sitemap.xml"

CORRECT_AFFILIATE_TAG = "guru0906-21"
WRONG_AFFILIATE_TAGS = {"guru07cc-21"}

# Preserve previously published URLs when titles change.
LEGACY_PRODUCT_PATHS = {
    "17": "amazon-in-fashion-fest-17",
}

PUBLIC_FILES = [
    ROOT / "index.html",
    ROOT / "app.js",
    ROOT / "validator.html",
    ROOT / "global_coupon_website.html",
    ROOT / "templates" / "seo-template.html",
]

PUBLIC_DIRS = [
    ROOT / "products",
    ROOT / "seo",
]

UNWANTED_PUBLIC_TERMS = [
    "Amazon India",
    "Amazon IN",
    "View on Amazon",
    "Check latest price on Amazon",
    "Check price on Amazon",
    "latest Amazon deals",
]

LINK_KEYS = (
    "link",
    "url",
    "affiliate_link",
    "affiliate_url",
    "product_url",
)


def slugify(value: object, max_length: int = 70) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:max_length].rstrip("-")


def load_products() -> list[dict]:
    if not COUPONS_FILE.exists():
        raise FileNotFoundError("coupons.json not found")

    data = json.loads(COUPONS_FILE.read_text(encoding="utf-8"))

    if not isinstance(data, list):
        raise ValueError("coupons.json must contain a JSON list")

    invalid_rows = [
        index
        for index, item in enumerate(data, start=1)
        if not isinstance(item, dict)
    ]

    if invalid_rows:
        raise ValueError(
            "Non-object product rows found at positions: "
            + ", ".join(map(str, invalid_rows))
        )

    return data


def product_identity(product: dict, index: int) -> str:
    return str(
        product.get("id")
        or product.get("sl_no")
        or product.get("asin")
        or f"row-{index}"
    )


def product_link(product: dict) -> str:
    for key in LINK_KEYS:
        value = product.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return ""


def page_directory(product: dict) -> Path:
    identity = str(
        product.get("id")
        or product.get("sl_no")
        or product.get("asin")
        or ""
    )

    legacy_path = LEGACY_PRODUCT_PATHS.get(identity)

    if legacy_path:
        return PRODUCTS_DIR / legacy_path

    title_slug = slugify(product.get("title"))
    suffix = (
        product.get("asin")
        or product.get("id")
        or product.get("sl_no")
    )

    return PRODUCTS_DIR / f"{title_slug}-{slugify(suffix)}"


def sitemap_urls() -> list[str]:
    if not SITEMAP_FILE.exists():
        return []

    root = ET.parse(SITEMAP_FILE).getroot()

    return [
        node.text.strip()
        for node in root.iter()
        if node.tag.endswith("loc") and node.text
    ]


def public_files() -> list[Path]:
    found: list[Path] = []
    seen: set[Path] = set()

    for path in PUBLIC_FILES:
        if path.exists() and path.is_file():
            resolved = path.resolve()
            if resolved not in seen:
                found.append(path)
                seen.add(resolved)

    for directory in PUBLIC_DIRS:
        if not directory.exists():
            continue

        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue

            if path.suffix.lower() not in {".html", ".js", ".json"}:
                continue

            resolved = path.resolve()

            if resolved not in seen:
                found.append(path)
                seen.add(resolved)

    return found


def print_section(title: str) -> None:
    print()
    print("=" * 68)
    print(title)
    print("=" * 68)


def check_command() -> int:
    failures: list[str] = []
    warnings: list[str] = []

    print_section("COUPON WORLD CONTROL CENTER â€” CHECK")

    try:
        products = load_products()
        print("PASS: coupons.json valid")
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}")
        return 1

    identities: list[str] = []
    links: list[str] = []

    missing_titles: list[str] = []
    missing_categories: list[str] = []
    missing_links: list[str] = []

    correct_tags: list[str] = []
    wrong_tags: list[tuple[str, str]] = []
    missing_tags: list[str] = []

    expected_pages: set[str] = set()

    for index, product in enumerate(products, start=1):
        identity = product_identity(product, index)
        identities.append(identity)

        title = product.get("title")
        category = product.get("category")
        link = product_link(product)

        if not title:
            missing_titles.append(identity)

        if not category:
            missing_categories.append(identity)

        if not link:
            missing_links.append(identity)
        else:
            links.append(link)

            tag = parse_qs(
                urlparse(link).query
            ).get("tag", [None])[0]

            if tag == CORRECT_AFFILIATE_TAG:
                correct_tags.append(identity)
            elif tag:
                wrong_tags.append((identity, tag))
            else:
                missing_tags.append(identity)

        expected_pages.add(
            str(page_directory(product).relative_to(ROOT))
        )

    duplicate_ids = [
        value
        for value, count in Counter(identities).items()
        if count > 1
    ]

    duplicate_links = [
        value
        for value, count in Counter(links).items()
        if count > 1
    ]

    actual_page_dirs = {
        str(path.parent.relative_to(ROOT))
        for path in PRODUCTS_DIR.rglob("index.html")
    } if PRODUCTS_DIR.exists() else set()

    missing_page_dirs = sorted(expected_pages - actual_page_dirs)
    stale_page_dirs = sorted(actual_page_dirs - expected_pages)

    urls = sitemap_urls()

    public_findings: list[tuple[str, int, str]] = []

    for path in public_files():
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        for line_number, line in enumerate(
            text.splitlines(),
            start=1,
        ):
            lowered = line.lower()

            for term in UNWANTED_PUBLIC_TERMS:
                if term.lower() in lowered:
                    public_findings.append(
                        (
                            str(path.relative_to(ROOT)),
                            line_number,
                            term,
                        )
                    )
                    break

    print(f"Products                 : {len(products)}")
    print(f"Product pages            : {len(actual_page_dirs)}")
    print(f"Sitemap URLs             : {len(urls)}")
    print(f"Correct affiliate tags   : {len(correct_tags)}")
    print(f"Wrong affiliate tags     : {len(wrong_tags)}")
    print(f"Missing affiliate tags   : {len(missing_tags)}")
    print(f"Duplicate IDs            : {len(duplicate_ids)}")
    print(f"Duplicate links          : {len(duplicate_links)}")
    print(f"Missing titles           : {len(missing_titles)}")
    print(f"Missing categories       : {len(missing_categories)}")
    print(f"Missing links            : {len(missing_links)}")
    print(f"Missing product pages    : {len(missing_page_dirs)}")
    print(f"Stale product pages      : {len(stale_page_dirs)}")
    print(f"Public wording findings  : {len(public_findings)}")

    indexable_extra_pages = []

    for root_name in ("guides", "seo"):
        root_dir = ROOT / root_name

        if not root_dir.exists():
            continue

        for page in root_dir.rglob("*.html"):
            text = page.read_text(
                encoding="utf-8",
                errors="ignore",
            )

            if 'name="robots"' in text.lower() and "noindex" in text.lower():
                continue

            indexable_extra_pages.append(page)

    expected_sitemap_count = (
        len(products)
        + 1
        + len(indexable_extra_pages)
    )

    if len(actual_page_dirs) != len(products):
        failures.append(
            "Product page count does not match product count"
        )

    if len(urls) != expected_sitemap_count:
        failures.append(
            "Sitemap URL count mismatch: "
            f"expected {expected_sitemap_count}, found {len(urls)}"
        )

    if wrong_tags:
        failures.append("Wrong affiliate tags found")

    if missing_tags:
        failures.append("Missing affiliate tags found")

    if duplicate_ids:
        failures.append("Duplicate product IDs found")

    if duplicate_links:
        failures.append("Duplicate product links found")

    if missing_titles:
        failures.append("Products missing titles")

    if missing_categories:
        failures.append("Products missing categories")

    if missing_links:
        failures.append("Products missing links")

    if missing_page_dirs:
        failures.append("Expected product pages are missing")

    if stale_page_dirs:
        failures.append("Stale product pages found")

    if public_findings:
        failures.append(
            "Unwanted public-facing retailer wording found"
        )

    wrong_tag_files: list[str] = []

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue

        if ".git" in path.parts:
            continue

        # Do not report the checkerâ€™s own blocked-tag definitions.
        if path.resolve() == Path(__file__).resolve():
            continue

        if any(
            folder in path.parts
            for folder in (
                ".branding_backups",
                ".compliance_backups",
            )
        ):
            continue

        name_lower = path.name.lower()
        relative_lower = str(path.relative_to(ROOT)).lower()

        # Ignore historical backups/audit artifacts in repository-wide
        # affiliate-tag hygiene checks. Active site/data/code validation
        # remains unchanged.
        if (
            "_before_" in name_lower
            or ".bak" in name_lower
            or name_lower.endswith(".bak")
            or "audit_reports" in path.parts
            or name_lower == "system_core_audit.txt"
        ):
            continue

        if path.suffix.lower() not in {
            ".py",
            ".json",
            ".html",
            ".js",
            ".md",
            ".txt",
        }:
            continue

        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        for wrong_tag in WRONG_AFFILIATE_TAGS:
            if wrong_tag in text:
                wrong_tag_files.append(
                    str(path.relative_to(ROOT))
                )

    if wrong_tag_files:
        failures.append(
            "Old wrong affiliate tag still exists in repository"
        )

    if failures:
        print_section("FAILURES")

        for item in failures:
            print("FAIL:", item)

        if wrong_tags:
            print()
            print("Wrong product tags:")
            for identity, tag in wrong_tags:
                print(f"  {identity}: {tag}")

        if missing_tags:
            print()
            print("Missing product tags:")
            for identity in missing_tags:
                print(f"  {identity}")

        if missing_page_dirs:
            print()
            print("Missing pages:")
            for path in missing_page_dirs[:20]:
                print(f"  {path}")

        if stale_page_dirs:
            print()
            print("Stale pages:")
            for path in stale_page_dirs[:20]:
                print(f"  {path}")

        if public_findings:
            print()
            print("Public wording findings:")
            for file_name, line_number, term in public_findings:
                print(
                    f"  {file_name}:{line_number}: {term}"
                )

        if wrong_tag_files:
            print()
            print("Files containing old wrong tag:")
            for file_name in sorted(set(wrong_tag_files)):
                print(f"  {file_name}")

        print_section("SITE STATUS: FAIL")
        return 1

    if warnings:
        print_section("WARNINGS")
        for item in warnings:
            print("WARNING:", item)

    print_section("SITE STATUS: PASS")
    print("Safe to continue with the next controlled step.")
    return 0



def run_command(command: list[str]) -> int:
    print()
    print("$", " ".join(command))

    result = subprocess.run(
        command,
        cwd=ROOT,
    )

    return result.returncode


def validate_build_source() -> int:
    print_section("BUILD SOURCE VALIDATION")

    try:
        products = load_products()
    except (
        FileNotFoundError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(f"FAIL: {exc}")
        return 1

    identities: list[str] = []
    links: list[str] = []
    failures: list[str] = []

    for index, product in enumerate(products, start=1):
        identity = product_identity(product, index)
        identities.append(identity)

        title = product.get("title")
        category = product.get("category")
        link = product_link(product)

        if not title:
            failures.append(
                f"Product {identity} missing title"
            )

        if not category:
            failures.append(
                f"Product {identity} missing category"
            )

        if not link:
            failures.append(
                f"Product {identity} missing link"
            )
            continue

        links.append(link)

        tag = parse_qs(
            urlparse(link).query
        ).get("tag", [None])[0]

        if tag != CORRECT_AFFILIATE_TAG:
            failures.append(
                f"Product {identity} has invalid affiliate tag"
            )

    duplicate_ids = [
        value
        for value, count in Counter(identities).items()
        if count > 1
    ]

    duplicate_links = [
        value
        for value, count in Counter(links).items()
        if count > 1
    ]

    if duplicate_ids:
        failures.append(
            "Duplicate product IDs: "
            + ", ".join(duplicate_ids)
        )

    if duplicate_links:
        failures.append(
            f"Duplicate product links found: {len(duplicate_links)}"
        )

    print("Products loaded          :", len(products))
    print("Duplicate IDs            :", len(duplicate_ids))
    print("Duplicate links          :", len(duplicate_links))

    if failures:
        print()
        for failure in failures:
            print("FAIL:", failure)

        print_section("BUILD SOURCE STATUS: FAIL")
        return 1

    print_section("BUILD SOURCE STATUS: PASS")
    return 0


def build_command() -> int:
    print_section("COUPON WORLD CONTROL CENTER â€” BUILD")

    if validate_build_source() != 0:
        print("BUILD ABORTED: source validation failed")
        return 1

    print_section("STEP 1 â€” BUILD PRODUCT PAGES")

    code = run_command(
        [
            sys.executable,
            "python/build_product_pages.py",
            "--write",
            "--clean",
        ]
    )

    if code != 0:
        print("BUILD FAILED: product page generation failed")
        return code

    print_section("STEP 2 â€” BUILD SITEMAP")

    code = run_command(
        [
            sys.executable,
            "python/build_sitemap.py",
        ]
    )

    if code != 0:
        print("BUILD FAILED: sitemap generation failed")
        return code

    print_section("STEP 3 â€” POST-BUILD CHECK")

    code = check_command()

    if code != 0:
        print_section("BUILD STATUS: FAIL")
        print("Generated site failed final validation.")
        return code

    print_section("BUILD STATUS: PASS")
    print("Product pages and sitemap rebuilt successfully.")
    print("Final site validation passed.")
    return 0




def intake_products(
    input_file: str,
    output_csv: str = "data/products_import.csv",
) -> int:
    print_section("COUPON WORLD CONTROL CENTER â€” INTAKE")

    input_path = Path(input_file)
    if not input_path.is_absolute():
        input_path = ROOT / input_path

    output_path = Path(output_csv)
    if not output_path.is_absolute():
        output_path = ROOT / output_path

    if not input_path.exists():
        print(f"FAIL: Product URL file not found: {input_path}")
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    return run_command(
        [
            sys.executable,
            "python/batch_product_importer.py",
            "prepare",
            str(input_path),
            str(output_path),
        ]
    )


def import_products(csv_file: str, write: bool = False) -> int:
    print_section("COUPON WORLD CONTROL CENTER â€” IMPORT")

    csv_path = Path(csv_file)

    if not csv_path.is_absolute():
        csv_path = ROOT / csv_path

    if not csv_path.exists():
        print(f"FAIL: CSV file not found: {csv_path}")
        return 1

    command = [
        sys.executable,
        "python/batch_product_importer.py",
        "import",
        str(csv_path),
    ]

    if write:
        command.append("--write")

    return run_command(command)





def adapt_source(input_csv: str, output_csv: str) -> int:
    print_section("COUPON WORLD CONTROL CENTER â€” ADAPT")

    input_path = Path(input_csv)
    if not input_path.is_absolute():
        input_path = ROOT / input_path

    output_path = Path(output_csv)
    if not output_path.is_absolute():
        output_path = ROOT / output_path

    return run_command(
        [
            sys.executable,
            "python/product_source_adapter.py",
            str(input_path),
            str(output_path),
        ]
    )


def intelligence_report() -> int:
    print_section("COUPON WORLD CONTROL CENTER â€” REPORT")

    return run_command(
        [
            sys.executable,
            "python/site_intelligence.py",
        ]
    )



def ask_command(
    query: str,
    json_output: bool = False,
) -> int:
    """Run the existing Shopping Brain through the control center."""
    command = [
        sys.executable,
        "python/shopping_brain.py",
    ]

    if json_output:
        command.append("--json")

    command.append(query)
    return run_command(command)


def run_workflow(
    input_file: str = "",
    output_csv: str = "data/products_import.csv",
) -> int:
    print_section("COUPON WORLD MASTER WORKFLOW")

    print("Mode        : SAFE")
    print("Auto-write  : NO")
    print("Auto-push   : NO")
    print("Discovery   : External source required")

    print_section("STEP 1 â€” FOUNDATION CHECK")

    check_code = check_command()

    if check_code != 0:
        print_section("MASTER WORKFLOW STATUS: FAIL")
        print("Foundation check failed. Workflow stopped.")
        return check_code

    if input_file:
        print_section("STEP 2 â€” PRODUCT INTAKE")

        intake_code = intake_products(
            input_file,
            output_csv,
        )

        if intake_code != 0:
            print_section("MASTER WORKFLOW STATUS: FAIL")
            print("Product intake failed. Workflow stopped.")
            return intake_code

        print_section("STEP 3 â€” IMPORT PREVIEW")

        import_code = import_products(
            output_csv,
            write=False,
        )

        if import_code != 0:
            print_section("MASTER WORKFLOW STATUS: REVIEW")
            print("Import preview requires review.")
            return import_code
    else:
        print_section("STEP 2 â€” PRODUCT INTAKE")
        print("SKIPPED: No input URL file supplied.")

    print_section("STEP 4 â€” CONTROLLED BUILD")

    build_code = build_command()

    if build_code != 0:
        print_section("MASTER WORKFLOW STATUS: FAIL")
        print("Controlled build failed.")
        return build_code

    print_section("MASTER WORKFLOW STATUS: PASS")
    print("Foundation             : PASS")
    print("Product intake         :", "PREVIEWED" if input_file else "SKIPPED")
    print("Database modification  : NO")
    print("Site build             : PASS")
    print("Git commit/push        : NOT PERFORMED")
    return 0



def knowledge_command(action: str, limit: int) -> int:
    """
    Run the controlled Coupon World knowledge pipeline.

    The update action resolves a limited pending batch, extracts newly
    verified official specifications, prepares review drafts, and then
    prints pipeline status. It does not auto-approve or auto-publish.
    """

    import subprocess

    scripts = {
        "resolver": ROOT / "python" / "official_source_resolver.py",
        "extractor": ROOT / "python" / "official_spec_extractor.py",
        "vision": ROOT / "run_gemini_vision_batch_v2.py",
        "builder": ROOT / "python" / "build_product_knowledge.py",
    }

    missing = [
        str(path)
        for path in scripts.values()
        if not path.exists()
    ]

    if missing:
        print("ERROR: Missing knowledge pipeline file(s):")
        for path in missing:
            print(" -", path)
        return 1

    def run_step(label: str, command: list[str]) -> int:
        print()
        print("=" * 72)
        print(label)
        print("=" * 72)
        print("$", " ".join(command))

        result = subprocess.run(
            command,
            cwd=ROOT,
            check=False,
        )

        if result.returncode != 0:
            if allow_failure:
                print(
                    f"WARNING: {label} returned exit code "
                    f"{result.returncode}; continuing in partial-review mode."
                )
            else:
                print(
                    f"ERROR: {label} failed with exit code "
                    f"{result.returncode}"
                )

        return result.returncode

    python_executable = sys.executable

    if action == "status":
        steps = [
            (
                "OFFICIAL SOURCE RESOLVER STATUS",
                [
                    python_executable,
                    str(scripts["resolver"]),
                    "status",
                ],
            ),
            (
                "OFFICIAL SPEC EXTRACTOR STATUS",
                [
                    python_executable,
                    str(scripts["extractor"]),
                    "status",
                ],
            ),
            (
                "PRODUCT KNOWLEDGE STATUS",
                [
                    python_executable,
                    str(scripts["builder"]),
                    "status",
                ],
            ),
        ]
    else:
        safe_limit = max(1, int(limit))

        steps = [
            (
                "STEP 1/4 - RESOLVE PENDING OFFICIAL SOURCES",
                [
                    python_executable,
                    str(scripts["resolver"]),
                    "run",
                    "--pending",
                    "--limit",
                    str(safe_limit),
                ],
            ),
            (
                "STEP 2/4 - EXTRACT NEW VERIFIED SPECIFICATIONS",
                [
                    python_executable,
                    str(scripts["extractor"]),
                    "extract",
                    "--pending",
                ],
            ),
            (
                "STEP 3/4 - PREPARE KNOWLEDGE REVIEW DRAFTS",
                [
                    python_executable,
                    str(scripts["builder"]),
                    "prepare",
                ],
            ),
            (
                "STEP 4/4 - SHOW KNOWLEDGE STATUS",
                [
                    python_executable,
                    str(scripts["builder"]),
                    "status",
                ],
            ),
        ]

    for label, command in steps:
        return_code = run_step(label, command)

        if return_code != 0:
            return return_code

    print()
    print("=" * 72)
    print("KNOWLEDGE PIPELINE COMPLETE")
    print("=" * 72)

    if action == "update":
        print(
            "Review-ready drafts, if any, remain pending for "
            "human approval."
        )

    return 0



def freeze_pending_intelligence_ids(
    limit: int,
) -> list[str]:
    queue_path = ROOT / "data" / "research_queue.json"
    results_path = ROOT / "data" / "research_results.json"

    if not queue_path.exists():
        raise FileNotFoundError(
            f"Missing research queue: {queue_path}"
        )

    queue_payload = json.loads(
        queue_path.read_text(encoding="utf-8")
    )
    queue_products = queue_payload.get("products", [])

    if not isinstance(queue_products, list):
        raise ValueError(
            "research_queue.json products must be a list"
        )

    existing_ids: set[str] = set()

    if results_path.exists():
        results_payload = json.loads(
            results_path.read_text(encoding="utf-8")
        )
        result_products = results_payload.get("products", [])

        if isinstance(result_products, list):
            existing_ids = {
                str(item.get("product_id") or "").strip()
                for item in result_products
                if isinstance(item, dict)
                and str(item.get("product_id") or "").strip()
            }

    frozen_ids: list[str] = []

    for product in queue_products:
        if not isinstance(product, dict):
            continue

        product_id = str(
            product.get("product_id") or ""
        ).strip()

        if not product_id:
            continue

        if str(
            product.get("status") or "pending"
        ) != "pending":
            continue

        if product_id in existing_ids:
            continue

        frozen_ids.append(product_id)

        if len(frozen_ids) >= max(1, int(limit)):
            break

    return frozen_ids


def intelligence_command(
    product_ids: list[str],
    limit: int = 1,
) -> int:
    """
    Run the safe Universal Product Intelligence workflow.

    Flow:
    official source resolver
    -> official specification extraction
    -> universal semantic consolidation
    -> knowledge review draft preparation
    -> knowledge status

    This command does not auto-approve, auto-publish, build the public site,
    commit Git changes, or push to GitHub.
    """

    scripts = {
        "resolver": ROOT / "python" / "official_source_resolver.py",
        "extractor": ROOT / "python" / "official_spec_extractor.py",
        "vision": ROOT / "run_gemini_vision_batch_v2.py",
        "builder": ROOT / "python" / "build_product_knowledge.py",
    }

    missing = [
        str(path)
        for path in scripts.values()
        if not path.exists()
    ]

    if missing:
        print("ERROR: Missing intelligence pipeline file(s):")
        for path in missing:
            print(" -", path)
        return 1

    safe_limit = max(1, int(limit))

    selected_ids = [
        str(value).strip()
        for value in product_ids
        if str(value).strip()
    ]

    if not selected_ids:
        try:
            selected_ids = freeze_pending_intelligence_ids(
                safe_limit
            )
        except (OSError, ValueError) as error:
            print(
                "ERROR: Could not freeze pending intelligence batch:",
                error,
            )
            return 1

        if not selected_ids:
            print("No pending unresolved products available.")
            return 0

        print(
            "Frozen batch IDs:",
            ", ".join(selected_ids),
        )

    def add_product_ids(command: list[str]) -> list[str]:
        for product_id in selected_ids:
            command.extend(
                [
                    "--product-id",
                    product_id,
                ]
            )
        return command

    def run_step(
        label: str,
        command: list[str],
        allow_failure: bool = False,
    ) -> int:
        print()
        print("=" * 72)
        print(label)
        print("=" * 72)
        print("$", " ".join(command))

        result = subprocess.run(
            command,
            cwd=ROOT,
            check=False,
        )

        if result.returncode != 0:
            print(
                f"ERROR: {label} failed with exit code "
                f"{result.returncode}"
            )

        return result.returncode

    python_executable = sys.executable

    if selected_ids:
        resolver_command = add_product_ids(
            [
                python_executable,
                str(scripts["resolver"]),
                "run",
            ]
        )

        extractor_command = add_product_ids(
            [
                python_executable,
                str(scripts["extractor"]),
                "extract",
            ]
        )

        semantic_command = add_product_ids(
            [
                python_executable,
                str(scripts["extractor"]),
                "semantic",
            ]
        )

        vision_commands = [
            [
                python_executable,
                str(scripts["vision"]),
                "--product-id",
                product_id,
            ]
            for product_id in selected_ids
        ]
    else:
        resolver_command = [
            python_executable,
            str(scripts["resolver"]),
            "run",
            "--pending",
            "--limit",
            str(safe_limit),
        ]

        extractor_command = [
            python_executable,
            str(scripts["extractor"]),
            "extract",
            "--pending",
            "--limit",
            str(safe_limit),
        ]

        semantic_command = [
            python_executable,
            str(scripts["extractor"]),
            "semantic",
            "--limit",
            str(safe_limit),
        ]

        vision_commands = []

    steps: list[tuple[str, list[str], bool]] = [
        (
            "STEP 1 - RESOLVE OFFICIAL PRODUCT SOURCE",
            resolver_command,
            False,
        ),
        (
            "STEP 2 - EXTRACT OFFICIAL PRODUCT EVIDENCE",
            extractor_command,
            False,
        ),
    ]

    for index, vision_command in enumerate(vision_commands, start=1):
        steps.append(
            (
                f"STEP 3.{index} - RUN PROVENANCE-SAFE VISION",
                vision_command,
                True,
            )
        )

    if not vision_commands:
        print(
            "VISION NOTE: automatic Vision v2 currently runs when "
            "--product-id is supplied explicitly."
        )

    steps.extend(
        [
            (
                "STEP 4 - CONSOLIDATE UNIVERSAL PRODUCT FACTS",
                semantic_command,
                False,
            ),
            (
                "STEP 5 - PREPARE KNOWLEDGE REVIEW DRAFTS",
                [
                    python_executable,
                    str(scripts["builder"]),
                    "prepare",
                ],
                False,
            ),
            (
                "STEP 6 - SHOW KNOWLEDGE STATUS",
                [
                    python_executable,
                    str(scripts["builder"]),
                    "status",
                ],
                False,
            ),
        ]
    )

    print()
    print("=" * 72)
    print("COUPON WORLD UNIVERSAL INTELLIGENCE WORKFLOW")
    print("=" * 72)
    print(
        "Products    :",
        ", ".join(selected_ids)
        if selected_ids
        else f"pending batch, limit {safe_limit}",
    )
    print("Auto-publish: NO")
    print("Auto-push   : NO")
    print("Review gate : REQUIRED")

    vision_soft_failures = 0
    resolver_ineligible_ids: list[str] = []
    verified_downstream_ids: list[str] = list(selected_ids)

    for label, command, allow_failure in steps:
        if label.startswith("STEP 2"):
            try:
                results_path = ROOT / "data" / "research_results.json"

                if results_path.exists():
                    resolver_db = json.loads(
                        results_path.read_text(encoding="utf-8")
                    )
                    resolver_products = resolver_db.get("products", [])

                    resolver_index = {
                        str(item.get("product_id") or "").strip(): item
                        for item in resolver_products
                        if isinstance(item, dict)
                        and str(item.get("product_id") or "").strip()
                    }

                    verified_downstream_ids = [
                        product_id
                        for product_id in selected_ids
                        if (
                            resolver_index.get(product_id, {}).get("verified")
                            is True
                            and str(
                                resolver_index.get(product_id, {}).get("status")
                                or ""
                            ) == "candidate_verified"
                        )
                    ]

                    resolver_ineligible_ids = [
                        product_id
                        for product_id in selected_ids
                        if product_id not in verified_downstream_ids
                    ]

                    print()
                    print(
                        "Verified downstream IDs:",
                        ", ".join(verified_downstream_ids)
                        if verified_downstream_ids
                        else "NONE",
                    )

                    if resolver_ineligible_ids:
                        print(
                            "Resolver review/not-found IDs:",
                            ", ".join(resolver_ineligible_ids),
                        )

            except (OSError, ValueError, TypeError) as error:
                print(
                    "ERROR: Could not evaluate resolver eligibility:",
                    str(error)[:250],
                )
                return 1

        if (
            (label.startswith("STEP 2") or label.startswith("STEP 4"))
            and not verified_downstream_ids
        ):
            print()
            print("=" * 72)
            print(label)
            print("=" * 72)
            print("SKIP: No resolver-verified products eligible.")
            continue

        if label.startswith("STEP 3."):
            vision_product_id = ""

            if "--product-id" in command:
                try:
                    vision_product_id = command[
                        command.index("--product-id") + 1
                    ]
                except (ValueError, IndexError):
                    vision_product_id = ""

            if vision_product_id not in verified_downstream_ids:
                print()
                print("=" * 72)
                print(label)
                print("=" * 72)
                print(
                    "SKIP: Product",
                    vision_product_id or "unknown",
                    "has no verified official source.",
                )
                continue

        if (
            verified_downstream_ids
            and (
                label.startswith("STEP 2")
                or label.startswith("STEP 4")
            )
        ):
            filtered_command: list[str] = []
            index = 0

            while index < len(command):
                token = command[index]

                if (
                    token == "--product-id"
                    and index + 1 < len(command)
                ):
                    product_id = command[index + 1]

                    if product_id in verified_downstream_ids:
                        filtered_command.extend(
                            ["--product-id", product_id]
                        )

                    index += 2
                    continue

                filtered_command.append(token)
                index += 1

            command = filtered_command

        return_code = run_step(
            label,
            command,
            allow_failure=allow_failure,
        )

        if return_code != 0:
            if allow_failure:
                vision_soft_failures += 1
                continue

            print()
            print("=" * 72)
            print("INTELLIGENCE WORKFLOW STATUS: FAIL")
            print("=" * 72)
            print("Stopped safely at:", label)
            return return_code

    partial_products: list[tuple[str, int, int]] = []

    if vision_soft_failures:
        print(
            "VISION STATUS: partial provider execution; "
            f"soft_failures={vision_soft_failures}"
        )

    try:
        official_specs_path = ROOT / "data" / "official_specs.json"

        if official_specs_path.exists():
            semantic_db = json.loads(
                official_specs_path.read_text(encoding="utf-8")
            )

            semantic_products = semantic_db.get("products", [])

            if isinstance(semantic_products, list):
                for product in semantic_products:
                    if not isinstance(product, dict):
                        continue

                    product_id = str(
                        product.get("product_id") or ""
                    ).strip()

                    if selected_ids and product_id not in selected_ids:
                        continue

                    media = product.get("media_evidence", {})

                    if not isinstance(media, dict):
                        continue

                    mismatches = int(
                        media.get(
                            "vision_provenance_mismatches",
                            0,
                        )
                        or 0
                    )

                    skipped = int(
                        media.get(
                            "vision_skipped_results",
                            0,
                        )
                        or 0
                    )

                    if mismatches > 0 or skipped > 0:
                        partial_products.append(
                            (
                                product_id,
                                mismatches,
                                skipped,
                            )
                        )

    except (OSError, ValueError, TypeError) as error:
        print(
            "WARNING: Could not evaluate partial vision status:",
            str(error)[:250],
        )

    print()
    print("=" * 72)

    if (
        partial_products
        or resolver_ineligible_ids
        or vision_soft_failures
    ):
        print("INTELLIGENCE WORKFLOW STATUS: PARTIAL_REVIEW")
    else:
        print("INTELLIGENCE WORKFLOW STATUS: PASS")

    print("=" * 72)
    print("Official source       : PROCESSED")
    print("Evidence extraction   : PROCESSED")
    print("Semantic consolidation: PROCESSED")
    print("Knowledge drafts      : PREPARED/REVIEWED")

    if resolver_ineligible_ids:
        print("Resolver eligibility  : PARTIAL")
        print(
            "  Review/not-found    :",
            ", ".join(resolver_ineligible_ids),
        )

    if partial_products or vision_soft_failures:
        print("Vision evidence       : PARTIAL")
        for product_id, mismatches, skipped in partial_products:
            print(
                f"  Product {product_id}: "
                f"provenance_mismatches={mismatches}, "
                f"skipped_results={skipped}"
            )

        if vision_soft_failures:
            print(
                "  Provider soft fails :",
                vision_soft_failures,
            )

        print(
            "Action                : Retry pending vision evidence when "
            "provider quota is available"
        )
    elif verified_downstream_ids:
        print("Vision evidence       : COMPLETE/NO BLOCKER")
    else:
        print("Vision evidence       : NOT RUN - NO VERIFIED SOURCE")

    print("Auto-publish          : NO")
    print("Human review          : REQUIRED")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Coupon World Control Center"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser(
        "check",
        help="Run read-only foundation checks",
    )

    subparsers.add_parser(
        "build",
        help="Rebuild product pages and sitemap safely",
    )

    adapt_parser = subparsers.add_parser(
        "adapt",
        help="Convert an approved product feed into Coupon World CSV",
    )

    adapt_parser.add_argument(
        "input_csv",
        help="Approved source CSV",
    )

    adapt_parser.add_argument(
        "output_csv",
        help="Coupon World formatted CSV",
    )

    subparsers.add_parser(
        "report",
        help="Show product quality and next best action",
    )


    intelligence_parser = subparsers.add_parser(
        "intelligence",
        help="Run the Universal Product Intelligence workflow",
    )

    intelligence_parser.add_argument(
        "--product-id",
        action="append",
        default=[],
        help="Process a specific product ID; may be repeated",
    )

    intelligence_parser.add_argument(
        "--limit",
        type=int,
        default=1,
        help="Maximum pending products when no product ID is supplied",
    )

    knowledge_parser = subparsers.add_parser(
        "knowledge",
        help="Run or inspect the verified knowledge pipeline",
    )

    knowledge_parser.add_argument(
        "action",
        choices=("update", "status"),
        help="Update a controlled batch or show pipeline status",
    )

    knowledge_parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum pending products to resolve during update",
    )

    ask_parser = subparsers.add_parser(
        "ask",
        help="Ask the Coupon World Shopping Brain",
    )

    ask_parser.add_argument(
        "query",
        nargs="+",
        help="Shopping query",
    )

    ask_parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of formatted text",
    )

    run_parser = subparsers.add_parser(
        "run",
        help="Run the safe Coupon World master workflow",
    )

    run_parser.add_argument(
        "--input",
        default="",
        help="Optional text file containing product URLs",
    )

    run_parser.add_argument(
        "--output",
        default="data/products_import.csv",
        help="Prepared CSV output path",
    )

    intake_parser = subparsers.add_parser(
        "intake",
        help="Prepare product import CSV from URL list",
    )

    intake_parser.add_argument(
        "input_file",
        help="Text file with one product URL per line",
    )

    intake_parser.add_argument(
        "--output",
        default="data/products_import.csv",
        help="Output CSV path",
    )

    import_parser = subparsers.add_parser(
        "import",
        help="Validate or import products from CSV",
    )

    import_parser.add_argument(
        "csv_file",
        help="CSV file containing products",
    )

    import_parser.add_argument(
        "--write",
        action="store_true",
        help="Write products and rebuild the site",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "check":
        return check_command()

    if args.command == "build":
        return build_command()

    if args.command == "adapt":
        return adapt_source(
            args.input_csv,
            args.output_csv,
        )

    if args.command == "report":
        return intelligence_report()


    if args.command == "intelligence":
        return intelligence_command(
            args.product_id,
            args.limit,
        )

    if args.command == "knowledge":
        return knowledge_command(
            args.action,
            args.limit,
        )

    if args.command == "ask":
        return ask_command(
            " ".join(args.query).strip(),
            args.json,
        )

    if args.command == "run":
        return run_workflow(
            args.input,
            args.output,
        )

    if args.command == "intake":
        return intake_products(
            args.input_file,
            args.output,
        )

    if args.command == "import":
        return import_products(
            args.csv_file,
            args.write,
        )

    parser.error("Unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
