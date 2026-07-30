#!/usr/bin/env python3

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent

REVIEW = ROOT / "data" / "knowledge_review.json"
QUEUE = ROOT / "data" / "research_queue.json"


with open(REVIEW, "r", encoding="utf-8") as f:
    review = json.load(f)

queue = []

for product in review["products"]:

    if product["review"]["approved"]:
        continue

    title = product["title"]
    brand = product["brand"]
    asin = product.get("asin", "")

    queries = []

    if asin:
        queries.append(f"{asin} official")

    if brand:
        queries.append(f"{brand} {title} official")

    queries.append(f"{title} specifications")

    queue.append(
        {
            "product_id": product["product_id"],
            "title": title,
            "brand": brand,
            "asin": asin,
            "status": "pending",
            "priority": 100 if asin else 50,
            "search_queries": queries,
        }
    )

with open(QUEUE, "w", encoding="utf-8") as f:
    json.dump(
        {
            "total_products": len(queue),
            "products": queue,
        },
        f,
        indent=2,
        ensure_ascii=False,
    )

print("=" * 60)
print("RESEARCH AGENT")
print("=" * 60)
print("Pending Products :", len(queue))
print("Output :", QUEUE)
print("=" * 60)