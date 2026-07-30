import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

KNOWLEDGE_FILE = ROOT / "data" / "product_knowledge.json"


def load_product_knowledge():
    if not KNOWLEDGE_FILE.exists():
        return {}

    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    knowledge = {}

    for product in data.get("products", []):
        knowledge[product["title"]] = product

    return knowledge


if __name__ == "__main__":
    db = load_product_knowledge()
    print(f"Knowledge Loaded : {len(db)}")