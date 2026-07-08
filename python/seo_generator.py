"""
Coupon World SEO Generator v1.0
Reads data/seo-pages.json and templates/seo-template.html
Generates SEO pages inside /seo/
"""

from pathlib import Path
import json
import html

ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = ROOT / "data" / "seo-pages.json"
TEMPLATE_FILE = ROOT / "templates" / "seo-template.html"
OUTPUT_FOLDER = ROOT / "seo"

def safe_text(value):
    return html.escape(str(value or ""), quote=True)

def generate_page(template, page):
    output = template
    output = output.replace("{{TITLE}}", safe_text(page.get("title")))
    output = output.replace("{{META_DESCRIPTION}}", safe_text(page.get("metaDescription")))
    output = output.replace("{{SLUG}}", safe_text(page.get("slug")))
    output = output.replace("{{KEYWORD}}", safe_text(page.get("keyword")))
    output = output.replace("{{CATEGORY}}", safe_text(page.get("category")))
    output = output.replace("{{INTENT}}", safe_text(page.get("intent")))
    return output

def main():
    OUTPUT_FOLDER.mkdir(exist_ok=True)

    pages = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    template = TEMPLATE_FILE.read_text(encoding="utf-8")

    generated = 0

    for page in pages:
        if page.get("status") != "ready":
            continue

        slug = page.get("slug")
        if not slug:
            print("Skipped page without slug")
            continue

        html_page = generate_page(template, page)
        output_file = OUTPUT_FOLDER / f"{slug}.html"
        output_file.write_text(html_page, encoding="utf-8")

        print(f"Generated: {output_file}")
        generated += 1

    print(f"Done. Total pages generated: {generated}")

if __name__ == "__main__":
    main()
