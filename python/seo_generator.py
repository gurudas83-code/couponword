"""
Coupon World SEO Generator
Version : 1.0
Author  : Coupon World

Purpose:
Reads seo-pages.json
Uses seo-template.html
Generates SEO pages automatically
"""

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = ROOT / "data" / "seo-pages.json"
TEMPLATE_FILE = ROOT / "templates" / "seo-template.html"
OUTPUT_FOLDER = ROOT / "seo"

print("===================================")
print(" Coupon World SEO Generator")
print("===================================")

print("Data File :", DATA_FILE)
print("Template  :", TEMPLATE_FILE)
print("Output    :", OUTPUT_FOLDER)
