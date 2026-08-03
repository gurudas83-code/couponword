import json
from datetime import datetime, timezone
from pathlib import Path
import shutil

path = Path("data/knowledge_review.json")

if not path.exists():
    raise SystemExit("ERROR: data/knowledge_review.json not found")

backup = path.with_name(
    f"knowledge_review_before_logitech_approval_{datetime.now():%Y%m%d_%H%M%S}.json"
)
shutil.copy2(path, backup)

payload = json.load(open(path, encoding="utf-8"))

products = payload.get("products", [])

draft = next(
    (
        item
        for item in products
        if str(item.get("product_id")) == "56"
    ),
    None,
)

if draft is None:
    raise SystemExit("ERROR: Product 56 draft not found")

draft["features"] = [
    "Wireless keyboard and mouse combo",
    "Minimalist space-saving design",
    "Spill-resistant keyboard",
    "High-definition optical tracking mouse",
    "Long battery life"
]

draft["best_for"] = [
    "Everyday office work",
    "Home computer use",
    "Students and general typing",
    "Users who prefer a compact wireless keyboard and mouse combo"
]

draft["limitations"] = [
    "Current price is not verified",
    "Detailed technical specifications are limited on the extracted official page",
    "Suitability for gaming or specialist use has not been verified"
]

draft["status"] = "approved"

draft["review"] = {
    "approved": True,
    "reviewed_by": "Guru Das",
    "reviewed_on": datetime.now(timezone.utc).isoformat(),
    "notes": (
        "Approved using verified Logitech official product page evidence. "
        "Only supported factual claims have been included."
    ),
}

draft["confidence"] = {
    "score": 82,
    "level": "high",
    "reason": (
        "Official Logitech product page, canonical URL, product identity, "
        "brand and key product features were verified."
    ),
}

path.write_text(
    json.dumps(payload, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("PASS: Logitech MK240 knowledge draft approved")
print("Backup:", backup)
print("Updated:", path)
