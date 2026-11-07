#!/usr/bin/env python3
"""Build the approved public GitHub Pages artifact."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
for import_path in (ROOT, ROOT / "python"):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))
PUBLIC_FILES = (
    "index.html", "style.css", "app.js", "mobile-research-preview.js", "coupons.json", "CNAME",
    "robots.txt", "sitemap.xml", "google54faf165096b5622.html", "buying-guides.html", "buying-guides.js",
)
PUBLIC_DATA_FILES = ("data/seo-pages.json", "data/mobile_research_preview.json")
PUBLIC_DIRECTORIES = ("assets", "seo", "guides")
PUBLIC_SOURCE_DIRECTORIES = ("assets", "products", "seo", "guides")
FORBIDDEN_NAMES = {
    "admin.html", "validator.html", "python", "reports", "outputs",
    "backups", ".git", "phase_e_current.zip",
}
SECRET_PATTERNS = (
    re.compile(r"(?:OPENAI|GEMINI|TAVILY|ANTHROPIC)_API_KEY\s*[:=]", re.I),
    re.compile(r"-----BEGIN (?:RSA|OPENSSH|EC|PRIVATE) KEY-----", re.I),
    re.compile(r"(?:private_product_id|/outputs/|/reports/|C:\\Users\\)", re.I),
)


def _copy_file(relative: str, destination: Path) -> None:
    source = ROOT / relative
    if not source.is_file():
        raise FileNotFoundError(f"required public file is missing: {relative}")
    target = destination / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _generate_product_pages(destination: Path) -> None:
    """Render product pages from current catalogue data into the artifact."""
    from python import build_product_pages as product_pages

    products = product_pages.load_products()
    pages_root = destination / "products"
    for product in products:
        relative = product_pages.page_dir(product).relative_to(product_pages.OUT)
        target = pages_root / relative
        target.mkdir(parents=True, exist_ok=True)
        (target / "index.html").write_text(
            product_pages.render(product, products),
            encoding="utf-8",
        )



def _prune_unverified_product_sitemap_entries(destination: Path) -> None:
    """Only offer-verified, indexable legacy pages belong in the live sitemap.

    This is a publication gate on the existing artifact, not a new catalogue,
    identity or recommendation engine. Preserve all old URLs for bookmarks.
    """
    ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", ns)
    sitemap = destination / "sitemap.xml"
    tree = ET.parse(sitemap)
    root = tree.getroot()
    removed = 0
    retained = 0
    for entry in list(root.findall(f"{{{ns}}}url")):
        location = entry.find(f"{{{ns}}}loc")
        url = urlsplit(str(location.text or "") if location is not None else "")
        if url.hostname != "coupon-world.in" or not url.path.startswith("/products/"):
            continue
        if not url.path.endswith("/") or url.query or url.fragment:
            raise RuntimeError(f"Invalid canonical product URL in sitemap: {url.geturl()}")
        page_path = destination / url.path.lstrip("/") / "index.html"
        if not page_path.is_file():
            raise RuntimeError(f"Sitemap refers to missing product page: {url.geturl()}")
        page = page_path.read_text(encoding="utf-8")
        meta = re.search(r'<meta[ ]+name="robots"[ ]+content="([^"]+)"', page, flags=re.I)
        if not meta:
            raise RuntimeError(f"Product page missing robots instruction: {page_path}")
        if "noindex" in meta.group(1).casefold():
            root.remove(entry)
            removed += 1
        else:
            retained += 1
    tree.write(sitemap, encoding="utf-8", xml_declaration=True)
    print(f"Legacy product sitemap gate: {retained} verified indexable; {removed} unverified omitted")


def _generate_research_catalogue(destination: Path) -> None:
    """Write a sanitized discovery index derived from existing research files."""
    from python.mobile_research_catalogue import build_public_catalogue

    target = destination / "data" / "mobile_research_catalogue.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(build_public_catalogue(ROOT), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _validate_public_content(output: Path) -> None:
    preview_path = output / "data" / "mobile_research_preview.json"
    preview = json.loads(preview_path.read_text(encoding="utf-8"))
    rows = preview.get("products")
    if preview.get("mode") != "PUBLIC_TECHNICAL_RESEARCH_PREVIEW" or not preview.get("default_enabled"):
        raise RuntimeError("public mobile research preview must remain explicitly enabled and research-only")
    if not isinstance(rows, list) or len(rows) != 10:
        raise RuntimeError("public mobile research preview must contain exactly 10 variants")
    ids = [row.get("canonical_product_id") for row in rows]
    if len(ids) != len(set(ids)) or any(not item for item in ids):
        raise RuntimeError("public mobile research preview contains duplicate or missing canonical IDs")
    for row in rows:
        commerce = row.get("commerce") or {}
        if any(commerce.get(key) not in (None, False, "") for key in ("price", "stock")):
            raise RuntimeError("research preview exposes commerce data")
        if commerce.get("purchase_cta_eligible") or commerce.get("publication_eligible"):
            raise RuntimeError("research preview exposes a commerce CTA")

    catalogue_path = output / "data" / "mobile_research_catalogue.json"
    catalogue = json.loads(catalogue_path.read_text(encoding="utf-8"))
    discovery_rows = catalogue.get("records")
    if catalogue.get("mode") != "PUBLIC_MOBILE_RESEARCH_CATALOGUE" or not isinstance(discovery_rows, list):
        raise RuntimeError("public mobile research catalogue has an invalid mode or record list")
    model_cards = catalogue.get("model_cards")
    if not isinstance(model_cards, list) or len(model_cards) != 232:
        raise RuntimeError("public mobile research catalogue must expose 232 primary model cards")
    if catalogue.get("source_counts", {}).get("visible_model_cards") != len(model_cards):
        raise RuntimeError("public model card count does not match source reconciliation")
    model_keys = [card.get("model_key") for card in model_cards]
    if any(not key for key in model_keys) or len(model_keys) != len(set(model_keys)):
        raise RuntimeError("public mobile research catalogue contains duplicate or missing model card keys")
    required_card_fields = {"brand", "model", "status", "specifications", "missing_specifications", "source_urls", "image_status"}
    for card in model_cards:
        if not required_card_fields <= set(card):
            raise RuntimeError("public model card is missing technical coverage metadata")
        photo = card.get("photo")
        if card["image_status"] == "VERIFIED_MATCH":
            if not photo or not (output / photo["url"].lstrip("/")).is_file():
                raise RuntimeError("approved model photo missing from the public artifact")
        elif card["image_status"] != "PLACEHOLDER" or photo:
            raise RuntimeError("public model card image rights are not explicitly cleared")
        for key, item in (card.get("specifications") or {}).items():
            if not isinstance(item, dict) or not str(item.get("source_url") or "").startswith("https://"):
                raise RuntimeError("public model card contains an unsupported specification source")
        if not isinstance(card.get("missing_specifications"), list):
            raise RuntimeError("public model card missing-specification list is invalid")
    keys = [row.get("record_key") for row in discovery_rows]
    if any(not key for key in keys) or len(keys) != len(set(keys)):
        raise RuntimeError("public mobile research catalogue contains duplicate or missing record keys")
    allowed_statuses = {"OFFICIAL_VERIFIED", "PARTIALLY_VERIFIED", "RESEARCH_ONLY", "NEEDS_VERIFICATION"}
    for row in discovery_rows:
        if row.get("status") not in allowed_statuses:
            raise RuntimeError("public mobile research catalogue contains an unknown evidence status")
        commerce = row.get("commerce") or {}
        if any(commerce.get(key) not in (None, False, "") for key in ("price", "stock")):
            raise RuntimeError("public mobile research catalogue exposes commerce data")
        if commerce.get("purchase_cta_eligible") or commerce.get("publication_eligible"):
            raise RuntimeError("public mobile research catalogue exposes a commerce CTA")
        if row.get("status") == "OFFICIAL_VERIFIED" and not set(("brand", "model", "ram_gb", "storage_gb")) <= set(row.get("verified_fields") or []):
            raise RuntimeError("officially verified discovery row is missing exact variant fields")
    card_record_keys = [key for card in model_cards for key in (card.get("discovery_record_keys") or [])]
    if sorted(card_record_keys) != sorted(keys):
        raise RuntimeError("public model cards do not retain each discovery record exactly once")
    preview_ids = [row.get("canonical_product_id") for row in rows]
    card_preview_ids = [key for card in model_cards for key in (card.get("frozen_variant_ids") or [])]
    if sorted(card_preview_ids) != sorted(preview_ids):
        raise RuntimeError("public model cards do not retain each frozen variant exactly once")

    coupons_path = output / "coupons.json"
    coupons = json.loads(coupons_path.read_text(encoding="utf-8"))
    if not isinstance(coupons, list):
        raise RuntimeError("public coupons.json must contain a list")
    approved_hosts = {"amazon.in", "www.amazon.in", "amzn.in", "www.amzn.in", "flipkart.com", "www.flipkart.com", "croma.com", "www.croma.com"}
    for row in coupons:
        if not isinstance(row, dict) or row.get("cta_eligible") is not True:
            continue
        try:
            from urllib.parse import urlparse

            parsed = urlparse(str(row.get("link") or ""))
            price = float(str(row.get("price") or "").replace(",", "").replace("₹", ""))
        except (TypeError, ValueError):
            raise RuntimeError("public CTA row has an invalid price or URL")
        if row.get("active") is not True or price <= 0 or str(row.get("availability") or "").casefold() not in {"in_stock", "in stock", "available", "available_now"}:
            raise RuntimeError("public CTA row is missing active, positive-price and in-stock evidence")
        if parsed.scheme != "https" or parsed.hostname not in approved_hosts:
            raise RuntimeError("public CTA row points to an unapproved retailer host")
        if row.get("identity_verified") is not True and str(row.get("catalog_status") or "").casefold() != "verified":
            raise RuntimeError("public CTA row is missing verified identity evidence")

    for path in output.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".html", ".js", ".json", ".css", ".txt", ".xml", ".svg"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                raise RuntimeError(f"sensitive content pattern found in public artifact: {path.relative_to(output)}")
        if "products" in path.relative_to(output).parts:
            # Product pages must not carry an active CTA beside an
            # unavailable price. Verified offer pages are allowed only
            # through the renderer's explicit offer decision.
            if re.search(r"price-unavailable.*?<a class=\"cta\" href=", text, re.S):
                raise RuntimeError(f"stale active CTA beside unavailable price: {path.relative_to(output)}")


def build(output: Path) -> Path:
    output = output.resolve()
    if output == ROOT or output in ROOT.parents:
        raise ValueError("public artifact output cannot replace the repository")
    source_paths = [ROOT / item for item in PUBLIC_FILES + PUBLIC_SOURCE_DIRECTORIES]
    if any(output == source or source in output.parents for source in source_paths):
        raise ValueError("public artifact output cannot overlap a source path")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    for relative in PUBLIC_FILES + PUBLIC_DATA_FILES:
        _copy_file(relative, output)
    for relative in PUBLIC_DIRECTORIES:
        source = ROOT / relative
        if not source.is_dir():
            raise FileNotFoundError(f"required public directory is missing: {relative}")
        shutil.copytree(source, output / relative)

    _generate_research_catalogue(output)

    # Product pages are generated from the same fail-closed renderer used
    # for local review. Never copy stale HTML from the source checkout.
    _generate_product_pages(output)

    from python.phone_guides import render_phone_guides
    render_phone_guides(output)

    # Publish only an editorially selected subset of the same source-linked
    # mobile research catalogue. No ranking, new engines or offers are added.
    from python.phone_research_pages import render_phone_research_pages
    render_phone_research_pages(output)

    # Hindi pages reuse exactly the same curated English guide/model sources;
    # category budget pages stay noindex until strict ranked evidence exists.
    from python.phone_hindi_pages import build as render_hindi_phone_pages
    render_hindi_phone_pages(output)

    # Extend the same evidence-first static publication path to both adjacent
    # categories. Research pages do not change core recommendation/offer gates.
    from python.category_research_pages import publish_category_research_pages
    publish_category_research_pages(output)

    # Import the 20-TV / 20-earbuds editorial workbook into dedicated research
    # routes. No newly admitted live offers or price-weighted rankings.
    from python.tv_earbuds_workbook_pages import publish_workbook_catalogue
    publish_workbook_catalogue(output)

    # Add source-supported Q3 India market-demand research from the same
    # reviewed public Pages path. The 232-phone core remains unchanged.
    from python.india_sales_priority_pages import publish_sales_priority
    publish_sales_priority(output)

    # Consolidate repeated/unsupported landing-page batches into reviewed guides.
    from python.publication_policy import apply_policy
    apply_policy(output)

    # The source sitemap still lists historical catalogue URLs. Keep those
    # pages online, but do not encourage indexing without current offer proof.
    _prune_unverified_product_sitemap_entries(output)

    from python.affiliate_links import tag_public_artifact
    tag_public_artifact(output)

    leaked = []
    for path in output.rglob("*"):
        parts = path.relative_to(output).parts
        if path.name in FORBIDDEN_NAMES or any(part in FORBIDDEN_NAMES for part in parts):
            leaked.append(str(path.relative_to(output)))
    if leaked:
        raise RuntimeError("forbidden files entered public artifact: " + ", ".join(leaked))
    _validate_public_content(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(f"public artifact ready: {build(args.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
