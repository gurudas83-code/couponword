#!/usr/bin/env python3
"""
Coupon World AI OS
Intent Engine v1.0

Converts shopping queries into structured intent.
"""

from __future__ import annotations

import re

from dataclasses import dataclass, asdict


@dataclass
class ShoppingIntent:
    intent: str = "recommendation"
    category: str | None = None
    budget_min: int | None = None
    budget_max: int | None = None
    features: list[str] | None = None
    brands: list[str] | None = None
    compare: bool = False
    keywords: list[str] | None = None


def normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("₹", " ")
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def detect_category(text: str):

    categories = {
        "phone": "smartphone",
        "mobile": "smartphone",
        "smartphone": "smartphone",
        "earbuds": "earbuds",
        "earbud": "earbuds",
        "laptop": "laptop",
        "smartwatch": "smartwatch",
        "watch": "smartwatch",
        "tablet": "tablet",
    }

    for key, value in categories.items():
        if key in text:
            return value

    return None

def detect_budget(text: str):

    m = re.search(r"(under|below|less than)\s+(\d+)", text)
    if m:
        return None, int(m.group(2))

    m = re.search(r"between\s+(\d+)\s+and\s+(\d+)", text)
    if m:
        return int(m.group(1)), int(m.group(2))

    return None, None

def detect_features(text: str) -> list[str]:
    feature_patterns = [
        ("a19 pro", "A19 Pro"),
        ("a19", "A19"),
        ("snapdragon 8 elite", "Snapdragon 8 Elite"),
        ("snapdragon 8s gen 4", "Snapdragon 8s Gen 4"),
        ("snapdragon", "Snapdragon"),
        ("dimensity 9400", "Dimensity 9400"),
        ("dimensity", "Dimensity"),
        ("tensor g5", "Tensor G5"),
        ("tensor", "Tensor"),
        ("exynos 2500", "Exynos 2500"),
        ("exynos", "Exynos"),
        ("lpddr5x", "LPDDR5X"),
        ("lpddr5", "LPDDR5"),
        ("ufs 4.0", "UFS 4.0"),
        ("ufs 3.1", "UFS 3.1"),
        ("wi fi 7", "Wi-Fi 7"),
        ("wifi 7", "Wi-Fi 7"),
        ("wi fi 6", "Wi-Fi 6"),
        ("wifi 6", "Wi-Fi 6"),
        ("bluetooth 5.4", "Bluetooth 5.4"),
        ("bluetooth 5.3", "Bluetooth 5.3"),
        ("usb c", "USB-C"),
        ("qi2", "Qi2"),
        ("wireless charging", "Wireless Charging"),
        ("fast charging", "Fast Charging"),
        ("amoled", "AMOLED"),
        ("oled", "OLED"),
        ("ip68", "IP68"),
        ("anc", "ANC"),
        ("enc", "ENC"),
        ("5g", "5G"),
        ("gaming", "Gaming"),
        ("ssd", "SSD"),
        ("rgb", "RGB"),
    ]

    found: list[str] = []

    for pattern, label in feature_patterns:
        if pattern in text and label not in found:
            found.append(label)

    return found
def detect_brands(text: str) -> list[str]:
    brands = [
        "apple",
        "samsung",
        "oneplus",
        "xiaomi",
        "redmi",
        "realme",
        "vivo",
        "oppo",
        "boat",
        "noise",
        "sony",
        "jbl",
        "hp",
        "dell",
        "lenovo",
        "asus",
    ]

    found = []

    for brand in brands:
        if brand in text:
            found.append(brand.title())

    return found

def detect_intent(text: str) -> tuple[str, bool]:
    if " vs " in text or "compare" in text:
        return "comparison", True

    if any(word in text for word in ["best", "top", "recommend"]):
        return "recommendation", False

    if detect_features(text):
        return "feature_search", False

    if detect_brands(text):
        return "brand_search", False

    return "recommendation", False

def parse_query(query: str) -> dict:
    text = normalize(query)
    intent, compare = detect_intent(text)
    budget_min, budget_max = detect_budget(text)

    result = ShoppingIntent(
        intent=intent,
        category=detect_category(text),
        budget_min=budget_min,
        budget_max=budget_max,
        features=detect_features(text),
        brands=detect_brands(text),
        compare=compare,
        keywords=text.split(),
    )

    return asdict(result)



if __name__ == "__main__":
    result = parse_query("Best Noise earbuds under 2000 with ANC")
    print(result)
   