#!/usr/bin/env python3
"""
Coupon World AI OS
Intent Engine v2.0
"""

from __future__ import annotations
import re
from dataclasses import dataclass, asdict, field


@dataclass
class ShoppingIntent:
    intent: str = "recommendation"
    category: str | None = None
    budget_min: int | None = None
    budget_max: int | None = None
    features: list[str] = field(default_factory=list)
    brands: list[str] = field(default_factory=list)
    compare: bool = False
    keywords: list[str] = field(default_factory=list)

    user_profile: str | None = None
    use_case: list[str] = field(default_factory=list)
    hard_constraints: list[str] = field(default_factory=list)
    must_have: list[str] = field(default_factory=list)
    preferred: list[str] = field(default_factory=list)
    avoid: list[str] = field(default_factory=list)
    priority_weights: dict[str, int] = field(default_factory=dict)


def normalize(text: str) -> str:
    text = str(text or "").lower()
    text = text.replace("₹", " ").replace("â‚¹", " ").replace(",", "")
    text = re.sub(r"[^\w\s.+/\-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def detect_category(text: str) -> str | None:
    """
    Detect the shopper's primary product category.

    Keep stable canonical category names downstream while accepting
    common Indian-shopping wording and product aliases.
    """
    mapping = [
        # Personal electronics
        (("smartphone", "mobile phone", "mobile", "phone"), "smartphone"),
        (("earbuds", "earbud", "tws"), "earbuds"),
        (("laptop", "notebook"), "laptop"),
        (("smartwatch", "smart watch"), "smartwatch"),
        (("tablet", "ipad"), "tablet"),
        (("headphone", "headphones", "headset"), "headphones"),
        (("bluetooth speaker", "portable speaker", "speaker"), "speaker"),

        # TV / entertainment
        (("smart tv", "television", "led tv", "oled tv", "qled tv", "tv"), "television"),
        (("soundbar", "sound bar"), "soundbar"),
        (("projector",), "projector"),

        # Kitchen appliances
        (("mixer grinder", "mixie"), "mixer_grinder"),
        (("air fryer",), "air_fryer"),
        (("microwave oven", "microwave"), "microwave"),
        (("induction cooktop", "induction stove", "induction"), "induction_cooktop"),
        (("electric kettle", "kettle"), "electric_kettle"),
        (("toaster",), "toaster"),
        (("juicer",), "juicer"),
        (("water purifier", "ro purifier", "water filter"), "water_purifier"),

        # Major appliances
        (("refrigerator", "fridge"), "refrigerator"),
        (("washing machine", "washer"), "washing_machine"),
        (("air conditioner", "split ac", "window ac", " ac "), "air_conditioner"),
        (("room heater", "heater"), "room_heater"),
        (("ceiling fan", "table fan", "pedestal fan", "fan"), "fan"),
        (("vacuum cleaner", "vacuum"), "vacuum_cleaner"),

        # Computing / accessories
        (("monitor",), "monitor"),
        (("keyboard",), "keyboard"),
        (("mouse",), "mouse"),
        (("printer",), "printer"),
        (("router", "wifi router", "wi-fi router"), "router"),
        (("power bank", "powerbank"), "power_bank"),

        # Photography
        (("dslr", "mirrorless camera", "digital camera", "camera"), "camera"),

        # Fashion / footwear
        (("running shoes", "walking shoes", "sports shoes", "sneakers", "shoes", "shoe"), "shoes"),
        (("sandals", "slippers", "flip flops"), "footwear"),
        (("t shirt", "t-shirt", "shirt"), "shirt"),
        (("jeans",), "jeans"),
        (("trousers", "pants"), "trousers"),
        (("dress", "kurti", "saree"), "womens_clothing"),
        (("jacket",), "jacket"),

        # Home / furniture
        (("office chair", "gaming chair", "chair"), "chair"),
        (("mattress",), "mattress"),
        (("sofa",), "sofa"),
        (("study table", "computer table", "desk"), "table"),

        # Personal care / beauty
        (("trimmer",), "trimmer"),
        (("electric shaver", "shaver"), "shaver"),
        (("hair dryer", "hairdryer"), "hair_dryer"),
        (("straightener",), "hair_straightener"),
        (("perfume", "fragrance"), "perfume"),
        (("sunscreen",), "sunscreen"),

        # Bags / travel
        (("backpack", "rucksack"), "backpack"),
        (("suitcase", "trolley bag", "luggage"), "luggage"),

        # Broad shopping intents
        (("toy", "toys"), "toys"),
        (("gift", "gifting"), "gift"),
    ]

    padded_text = f" {text} "

    for aliases, category in mapping:
        for alias in aliases:
            if alias.startswith(" ") or alias.endswith(" "):
                if alias in padded_text:
                    return category
            elif re.search(
                r"(?<!\\w)" + re.escape(alias) + r"(?!\\w)",
                text,
            ):
                return category

    return None

def detect_budget(text: str) -> tuple[int | None, int | None]:
    """
    Parse common Indian shopping-budget expressions while preserving
    the existing min/max contract.

    Examples:
      under 20000
      under 20k
      20k ke andar
      20 hazar tak
      between 15k and 20k
      15k-20k
      above 30k
      30k se upar
    """

    def amount(value: str, unit: str | None = None) -> int:
        number = float(value)

        unit = str(unit or "").lower().strip()

        if unit in {"k", "thousand", "hazar", "hazaar"}:
            number *= 1000

        return int(number)

    amount_pattern = (
        r"(\d+(?:\.\d+)?)\s*"
        r"(k|thousand|hazar|hazaar)?"
    )

    # ------------------------------------------------------------
    # Maximum budget
    # ------------------------------------------------------------
    m = re.search(
        rf"(?:under|below|less than|upto|up to|max|maximum)\s*"
        rf"{amount_pattern}",
        text,
    )
    if m:
        return None, amount(m.group(1), m.group(2))

    # Common Hinglish forms:
    #   20k ke andar
    #   20k ke under
    #   20 hazar tak
    #   20000 tak
    m = re.search(
        rf"\b{amount_pattern}\s*"
        rf"(?:ke\s+)?(?:andar|under|below|tak)\b",
        text,
    )
    if m:
        return None, amount(m.group(1), m.group(2))

    # ------------------------------------------------------------
    # Budget range
    # ------------------------------------------------------------
    m = re.search(
        rf"(?:between|from)\s*"
        rf"{amount_pattern}\s*"
        rf"(?:and|to|-)\s*"
        rf"{amount_pattern}",
        text,
    )
    if m:
        a = amount(m.group(1), m.group(2))
        b = amount(m.group(3), m.group(4))
        return min(a, b), max(a, b)

    # Compact range:
    #   15k-20k
    #   15000 to 20000
    m = re.search(
        rf"\b{amount_pattern}\s*"
        rf"(?:-|to)\s*"
        rf"{amount_pattern}\b",
        text,
    )
    if m:
        a = amount(m.group(1), m.group(2))
        b = amount(m.group(3), m.group(4))
        return min(a, b), max(a, b)

    # ------------------------------------------------------------
    # Minimum budget
    # ------------------------------------------------------------
    m = re.search(
        rf"(?:above|over|more than|min|minimum)\s*"
        rf"{amount_pattern}",
        text,
    )
    if m:
        return amount(m.group(1), m.group(2)), None

    # Hinglish:
    #   30k se upar
    #   30k se above
    m = re.search(
        rf"\b{amount_pattern}\s*se\s*"
        rf"(?:upar|above|over)\b",
        text,
    )
    if m:
        return amount(m.group(1), m.group(2)), None

    return None, None


def detect_features(text: str) -> list[str]:
    patterns = [
        ("snapdragon 8 elite", "Snapdragon 8 Elite"),
        ("snapdragon 8s gen 4", "Snapdragon 8s Gen 4"),
        ("snapdragon", "Snapdragon"),
        ("dimensity", "Dimensity"),
        ("lpddr5x", "LPDDR5X"),
        ("ufs 4.0", "UFS 4.0"),
        ("wifi 7", "Wi-Fi 7"),
        ("bluetooth 5.4", "Bluetooth 5.4"),
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
        ("battery", "Battery"),
        ("camera", "Camera"),
        ("large display", "Large Display"),
        ("large screen", "Large Display"),
        ("lightweight", "Lightweight"),
    ]
    found = []
    for pattern, label in patterns:
        if pattern in text and label not in found:
            found.append(label)
    return found


def detect_brands(text: str) -> list[str]:
    brands = [
        "apple", "samsung", "oneplus", "xiaomi", "redmi", "realme",
        "vivo", "oppo", "boat", "noise", "sony", "jbl", "hp",
        "dell", "lenovo", "asus", "acer", "motorola", "nothing",
    ]
    return [brand.title() for brand in brands if brand in text]


def detect_intent(text: str) -> tuple[str, bool]:
    if " vs " in f" {text} " or "compare" in text:
        return "comparison", True
    if any(x in text for x in ("best", "top", "recommend", "suggest")):
        return "recommendation", False
    if detect_features(text):
        return "feature_search", False
    if detect_brands(text):
        return "brand_search", False
    return "recommendation", False


def detect_user_profile(text: str) -> str | None:
    profiles = [
        (("father", "dad", "papa", "mother", "mom", "mummy", "parents", "parent"), "parent"),
        (("senior citizen", "elderly", "grandfather", "grandmother"), "senior"),
        (("student", "college", "school"), "student"),
        (("child", "kid", "kids", "children"), "child"),
        (("office", "professional", "work"), "professional"),
        (("travel", "traveller", "traveler"), "traveller"),
        (("gamer",), "gamer"),
    ]
    for aliases, profile in profiles:
        if any(alias in text for alias in aliases):
            return profile

    if (
        "gaming" in text
        and not any(
            phrase in text
            for phrase in ("occasional gaming", "light gaming", "casual gaming")
        )
    ):
        return "gamer"

    return None


def detect_use_cases(text: str) -> list[str]:
    rules = [
        (("ps5", "playstation 5", "xbox", "console gaming"), "tv_gaming"),
        (("cricket", "sports", "football", "match"), "sports_viewing"),
        (("movies", "movie", "cinema", "netflix", "ott"), "movie_viewing"),
        (("bright room", "sunny room", "daylight room"), "bright_room"),
        (("dark room", "night viewing", "home theatre", "home theater"), "dark_room"),
        (("coding", "programming", "developer"), "coding"),
        (("occasional gaming", "light gaming", "casual gaming"), "light_gaming"),
        (("gaming", "game"), "gaming"),
        (("office", "professional", "work"), "office_work"),
        (("student", "study", "college", "school"), "study"),
        (("camera", "photography", "photo"), "photography"),
        (("father", "mother", "parent", "papa", "dad", "mom"), "parent_use"),
        (("senior", "elderly"), "senior_use"),
    ]
    found = []
    for aliases, label in rules:
        if any(alias in text for alias in aliases) and label not in found:
            found.append(label)

    if "light_gaming" in found and "gaming" in found:
        found.remove("gaming")
    return found



def detect_tv_requirements(text: str) -> dict[str, object]:
    result: dict[str, object] = {}

    size_match = re.search(
        r"\b(32|40|42|43|48|50|55|58|60|65|70|75|77|83|85|86|98|100)\s*(?:inch|inches|in|\\?\")\b",
        text,
        re.I,
    )
    if size_match:
        result["screen_size_inches"] = int(size_match.group(1))

    if re.search(r"\boled\b", text, re.I):
        result["panel_technology"] = "oled"
    elif re.search(r"\b(?:mini[\s-]?led|miniled)\b", text, re.I):
        result["panel_technology"] = "mini_led"
    elif re.search(r"\bqled\b", text, re.I):
        result["panel_technology"] = "qled"

    refresh_match = re.search(
        r"\b(60|90|100|120|144|165)\s*hz\b",
        text,
        re.I,
    )
    if refresh_match:
        result["refresh_rate_hz"] = int(refresh_match.group(1))

    if re.search(r"\bhdmi\s*2\.1\b", text, re.I):
        result["hdmi_2_1"] = True

    if re.search(r"\b(?:vrr|variable refresh rate)\b", text, re.I):
        result["vrr"] = True

    if re.search(r"\b(?:allm|auto low latency mode)\b", text, re.I):
        result["allm"] = True

    if re.search(r"\b(?:dolby vision)\b", text, re.I):
        result["dolby_vision"] = True

    if re.search(r"\b(?:hdr10\+)\b", text, re.I):
        result["hdr10_plus"] = True

    return result


def detect_requirements(
    text: str,
    category: str | None,
    user_profile: str | None,
    use_cases: list[str],
) -> tuple[list[str], list[str], list[str], list[str]]:
    hard_constraints: list[str] = []
    must_have: list[str] = []
    preferred: list[str] = []
    avoid: list[str] = []

    def add(items: list[str], value: str) -> None:
        if value not in items:
            items.append(value)

    # ------------------------------------------------------------
    # Brand semantics
    # ------------------------------------------------------------
    detected_brands = [
        brand.lower()
        for brand in detect_brands(text)
    ]

    for brand in detected_brands:
        marker = f"brand_{brand}"

        hard_brand_patterns = (
            rf"\bonly\s+{re.escape(brand)}\b",
            rf"\b{re.escape(brand)}\s+only\b",
            rf"\b{re.escape(brand)}\s+hi\s+chahiye\b",
            rf"\b{re.escape(brand)}\s+hi\b",
        )

        avoid_brand_patterns = (
            rf"\bno\s+{re.escape(brand)}\b",
            rf"\bwithout\s+{re.escape(brand)}\b",
            rf"\b{re.escape(brand)}\s+nahi\b",
            rf"\b{re.escape(brand)}\s+nahi\s+chahiye\b",
            rf"\bdont\s+want\s+{re.escape(brand)}\b",
            rf"\bdon't\s+want\s+{re.escape(brand)}\b",
        )

        preferred_brand_patterns = (
            rf"\bprefer(?:red|ably)?\s+{re.escape(brand)}\b",
            rf"\b{re.escape(brand)}\s+preferred\b",
            rf"\bprefer\s+{re.escape(brand)}\b",
        )

        if any(re.search(pattern, text) for pattern in avoid_brand_patterns):
            add(avoid, marker)
            continue

        if any(re.search(pattern, text) for pattern in hard_brand_patterns):
            add(must_have, marker)
            continue

        if any(re.search(pattern, text) for pattern in preferred_brand_patterns):
            add(preferred, marker)

    # Multi-brand alternatives:
    #   Samsung or OnePlus
    #   Samsung ya OnePlus
    if len(detected_brands) >= 2 and re.search(r"\b(?:or|ya)\b", text):
        for brand in detected_brands:
            marker = f"brand_{brand}"
            if marker not in avoid and marker not in must_have:
                add(preferred, marker)

    if re.search(r"(under|below|less than|upto|up to|max|maximum)\s*\d{3,7}", text):
        add(hard_constraints, "budget_max")

    for phrases, value in [
        (("good battery", "long battery", "battery life"), "good_battery"),
        (
            (
                "good call quality",
                "clear call",
                "clear calls",
                "call quality",
                "calling quality",
                "good mic",
                "good microphone",
            ),
            "good_call_quality",
        ),
        (("large display", "large screen", "big display", "big screen"), "large_display"),
        (("easy to use", "simple to use", "simple phone", "easy ui"), "easy_to_use"),
        (("good camera", "best camera"), "good_camera"),
        (("good performance", "fast performance", "powerful"), "good_performance"),
        (("lightweight", "portable"), "portable"),
        (("anc", "noise cancellation"), "anc"),
        (("5g",), "5g"),
        (("ssd",), "ssd"),
    ]:
        if any(p in text for p in phrases):
            add(preferred, value)

    if user_profile in {"parent", "senior"}:
        for value in ("good_battery", "large_display", "easy_to_use", "good_call_quality"):
            add(preferred, value)

    if user_profile == "student":
        for value in ("good_battery", "value_for_money"):
            add(preferred, value)

    if "coding" in use_cases:
        for value in ("good_performance", "comfortable_keyboard", "ssd"):
            add(preferred, value)

    if "light_gaming" in use_cases:
        add(preferred, "moderate_gaming_performance")

    if "gaming" in use_cases:
        add(preferred, "strong_gaming_performance")

    if any(p in text for p in ("no gaming", "gaming not required", "dont need gaming", "don't need gaming")):
        add(avoid, "gaming_focused")

    if "must" in text or "required" in text or "at least" in text or "minimum" in text:
        for item in list(preferred):
            if item in {"5g", "ssd", "good_battery", "large_display", "good_camera"}:
                preferred.remove(item)
                add(must_have, item)

    # Explicit feature wording means the feature is required,
    # not merely preferred.
    if category == "earbuds":
        explicit_anc_patterns = (
            r"\bwith\s+anc\b",
            r"\bmust\s+(?:have\s+)?anc\b",
            r"\banc\s+(?:is\s+)?required\b",
            r"\bneed\s+anc\b",
            r"\bwith\s+(?:active\s+)?noise\s+cancellation\b",
        )

        if any(re.search(pattern, text) for pattern in explicit_anc_patterns):
            add(must_have, "anc")
            if "anc" in preferred:
                preferred.remove("anc")

    if category == "smartphone" and "5g" in text:
        add(must_have, "5g")
        if "5g" in preferred:
            preferred.remove("5g")

    # Explicit RAM/storage capacities are product requirements.
    # Keep them in the existing must_have contract so discovery,
    # fit scoring and downstream engines can consume them without
    # introducing a parallel intent schema.
    if category in {"smartphone", "laptop", "tablet"}:
        # Compact memory notation commonly used by shoppers:
        #   8/128
        #   8+128
        #   12/256
        compact_variant_match = re.search(
            r"\b(2|3|4|6|8|12|16|18|24|32|64)\s*(?:/|\+)\s*"
            r"(32|64|128|256|512|1024)\b",
            text,
        )

        if compact_variant_match:
            add(
                must_have,
                f"{compact_variant_match.group(1)}gb_ram",
            )
            add(
                must_have,
                f"{compact_variant_match.group(2)}gb_storage",
            )

        ram_match = re.search(
            r"\b(2|3|4|6|8|12|16|18|24|32|64)\s*gb\s*(?:of\s*)?ram\b",
            text,
        )
        if ram_match:
            add(must_have, f"{ram_match.group(1)}gb_ram")

        storage_match = re.search(
            r"\b(32|64|128|256|512|1024)\s*gb\s*"
            r"(?:storage|internal\s+storage|rom|ssd)\b",
            text,
        )
        if storage_match:
            add(must_have, f"{storage_match.group(1)}gb_storage")

        # Smartphone shoppers commonly write memory variants in compact
        # form, e.g. "8GB RAM 128GB". In that pattern the second bare
        # capacity is storage even when "storage" or "ROM" is omitted.
        if category == "smartphone" and not storage_match:
            compact_memory_match = re.search(
                r"\b(?:2|3|4|6|8|12|16|18|24|32|64)\s*gb\s*"
                r"(?:of\s*)?ram\b"
                r".{0,20}?"
                r"\b(32|64|128|256|512|1024)\s*gb\b",
                text,
            )

            if compact_memory_match:
                add(
                    must_have,
                    f"{compact_memory_match.group(1)}gb_storage",
                )

        tb_storage_match = re.search(
            r"\b(1|2|4)\s*tb\s*"
            r"(?:storage|internal\s+storage|ssd|rom)\b",
            text,
        )
        if tb_storage_match:
            add(
                must_have,
                f"{int(tb_storage_match.group(1)) * 1024}gb_storage",
            )

    return hard_constraints, must_have, preferred, avoid


def normalize_weights(weights: dict[str, int]) -> dict[str, int]:
    weights = {k: max(0, int(v)) for k, v in weights.items()}
    total = sum(weights.values()) or 1
    result = {}
    running = 0
    items = list(weights.items())

    for i, (key, value) in enumerate(items):
        if i == len(items) - 1:
            score = 100 - running
        else:
            score = round(value * 100 / total)
            running += score
        result[key] = max(0, score)

    drift = 100 - sum(result.values())
    if drift:
        key = max(result, key=result.get)
        result[key] += drift
    return result


def build_priority_weights(
    category: str | None,
    user_profile: str | None,
    use_cases: list[str],
    must_have: list[str],
    preferred: list[str],
    hard_constraints_for_weights: list[str] | None = None,
    text: str = "",
) -> dict[str, int]:
    hard_constraints_for_weights = hard_constraints_for_weights or []

    if category == "smartphone":
        weights = {
            "budget": 20, "battery": 15, "display": 15, "ease_of_use": 10,
            "camera": 10, "performance": 10, "software_support": 10,
            "connectivity": 10,
        }
    elif category == "laptop":
        weights = {
            "budget": 20, "performance": 20, "ram": 15, "storage": 10,
            "battery": 10, "display": 10, "portability": 10, "build_quality": 5,
        }
    elif category == "television":
        weights = {
            "budget": 15,
            "screen_size": 15,
            "picture_quality": 18,
            "panel_technology": 12,
            "refresh_rate": 8,
            "gaming_features": 7,
            "brightness": 7,
            "motion": 6,
            "smart_tv": 5,
            "sound": 4,
            "product_identity": 3,
        }

    elif category == "earbuds":
        weights = {
            "budget": 20, "sound_quality": 20, "battery": 15,
            "call_quality": 15, "anc": 15, "comfort": 10, "connectivity": 5,
        }
    else:
        # Universal fallback for categories that do not yet have a
        # dedicated deep-scoring profile.
        #
        # Rank only from evidence we can conservatively verify:
        # product/category relevance, query relevance and specific
        # product identity. Never invent quality/performance claims.
        if "budget_max" in hard_constraints_for_weights:
            weights = {
                "budget": 25,
                "category_relevance": 35,
                "query_relevance": 30,
                "product_identity": 10,
            }
        else:
            weights = {
                "category_relevance": 45,
                "query_relevance": 40,
                "product_identity": 15,
            }

    if user_profile in {"parent", "senior"} and category == "smartphone":
        weights = {
            "budget": 20, "battery": 25, "display": 20, "ease_of_use": 20,
            "camera": 5, "performance": 5, "software_support": 5,
            "connectivity": 0,
        }

    if user_profile == "student":
        weights["budget"] = max(weights.get("budget", 0), 25)
        if "battery" in weights:
            weights["battery"] = max(weights["battery"], 15)

    if category == "television":
        if "tv_gaming" in use_cases:
            weights = {
                "budget": 12,
                "screen_size": 10,
                "picture_quality": 12,
                "panel_technology": 8,
                "refresh_rate": 18,
                "gaming_features": 22,
                "brightness": 4,
                "motion": 8,
                "smart_tv": 2,
                "sound": 2,
                "product_identity": 2,
            }

        elif "sports_viewing" in use_cases and "bright_room" in use_cases:
            weights = {
                "budget": 12,
                "screen_size": 16,
                "picture_quality": 12,
                "panel_technology": 8,
                "refresh_rate": 10,
                "gaming_features": 2,
                "brightness": 18,
                "motion": 14,
                "smart_tv": 3,
                "sound": 3,
                "product_identity": 2,
            }

        elif "movie_viewing" in use_cases and "dark_room" in use_cases:
            weights = {
                "budget": 12,
                "screen_size": 12,
                "picture_quality": 24,
                "panel_technology": 20,
                "refresh_rate": 5,
                "gaming_features": 2,
                "brightness": 3,
                "motion": 5,
                "smart_tv": 5,
                "sound": 8,
                "product_identity": 4,
            }

    if category == "laptop" and "coding" in use_cases:
        weights = {
            "budget": 20, "performance": 25, "ram": 20, "storage": 15,
            "battery": 10, "display": 5, "portability": 5, "build_quality": 0,
        }

    if category == "laptop" and "gaming" in use_cases:
        weights = {
            "budget": 15,
            "graphics": 25,
            "performance": 20,
            "ram": 12,
            "storage": 8,
            "display": 12,
            "battery": 3,
            "portability": 0,
            "build_quality": 5,
        }

    nudges = {
        "good_battery": "battery",
        "good_call_quality": "call_quality",
        "large_display": "display",
        "easy_to_use": "ease_of_use",
        "good_camera": "camera",
        "good_performance": "performance",
        "portable": "portability",
        "anc": "anc",
        "ssd": "storage",
    }

    combined = set(must_have + preferred)

    # ------------------------------------------------------------
    # Explicit smartphone memory/network query
    # ------------------------------------------------------------
    # When the shopper explicitly asks for RAM/storage capacity,
    # those requirements must become first-class ranking dimensions.
    #
    # Example:
    #   phone under 20000 with 8GB RAM and 128GB storage and 5G
    #
    # Generic secondary qualities such as camera/software remain
    # useful, but they must not dominate the shopper's stated needs.
    # ------------------------------------------------------------
    if category == "smartphone":
        has_ram_requirement = any(
            re.fullmatch(r"\d+gb_ram", str(req or "").lower())
            for req in must_have
        )

        has_storage_requirement = any(
            re.fullmatch(r"\d+gb_storage", str(req or "").lower())
            for req in must_have
        )

        if has_ram_requirement or has_storage_requirement:
            weights = {
                "budget": 25,
                "ram": 20 if has_ram_requirement else 5,
                "storage": 20 if has_storage_requirement else 5,
                "connectivity": 15 if "5g" in combined else 8,
                "battery": 7,
                "display": 5,
                "performance": 3,
                "camera": 2,
                "ease_of_use": 1,
                "software_support": 2,
            }

    # Explicit requirements should materially influence ranking,
    # while category defaults remain secondary decision factors.
    for req, dimension in nudges.items():
        if req in combined and dimension in weights:
            weights[dimension] += 10

    # ------------------------------------------------------------
    # Natural-language priority emphasis
    # ------------------------------------------------------------
    # These phrases affect ranking strength, not eligibility.
    # Examples:
    #   camera sabse important
    #   battery priority
    #   gaming most important
    #   performance zyada important
    #
    # Stronger mandatory language is handled separately by the
    # requirement layer; this section only changes ranking emphasis.
    priority_aliases = {
        "camera": ("camera",),
        "battery": ("battery",),
        "display": ("display", "screen"),
        "performance": ("performance", "speed", "processor"),
        "sound_quality": ("sound", "audio"),
        "call_quality": ("call quality", "calling", "mic", "microphone"),
        "anc": ("anc", "noise cancellation"),
        "comfort": ("comfort", "comfortable"),
        "picture_quality": ("picture quality", "picture"),
        "brightness": ("brightness", "bright"),
        "refresh_rate": ("refresh rate", "hz"),
        "gaming_features": ("gaming", "game"),
        "graphics": ("graphics", "gpu", "gaming"),
        "portability": ("portable", "lightweight"),
    }

    strong_priority_patterns = (
        "sabse important",
        "most important",
        "top priority",
        "highest priority",
        "main priority",
        "first priority",
        "priority no 1",
        "priority number 1",
        "zyada important",
        "more important",
    )

    normal_priority_patterns = (
        "priority",
        "important",
        "important hai",
        "prefer",
        "preference",
    )

    for dimension, aliases in priority_aliases.items():
        if dimension not in weights:
            continue

        strong_match = False
        normal_match = False

        for alias in aliases:
            alias_re = re.escape(alias)

            if any(
                re.search(
                    rf"\b{alias_re}\b.{{0,30}}\b{re.escape(pattern)}\b"
                    rf"|\b{re.escape(pattern)}\b.{{0,30}}\b{alias_re}\b",
                    text,
                )
                for pattern in strong_priority_patterns
            ):
                strong_match = True
                break

            if any(
                re.search(
                    rf"\b{alias_re}\b.{{0,20}}\b{re.escape(pattern)}\b"
                    rf"|\b{re.escape(pattern)}\b.{{0,20}}\b{alias_re}\b",
                    text,
                )
                for pattern in normal_priority_patterns
            ):
                normal_match = True

        if strong_match:
            weights[dimension] += 25
        elif normal_match:
            weights[dimension] += 12

    # Gaming wording usually represents a composite priority rather
    # than only one dimension.
    if any(
        phrase in text
        for phrase in (
            "gaming priority",
            "gaming important",
            "gaming sabse important",
            "gaming most important",
        )
    ):
        if "performance" in weights:
            weights["performance"] += 15
        if "graphics" in weights:
            weights["graphics"] += 18
        if "display" in weights:
            weights["display"] += 8
        if "refresh_rate" in weights:
            weights["refresh_rate"] += 10
        if "gaming_features" in weights:
            weights["gaming_features"] += 15

    # ------------------------------------------------------------
    # Relative-priority language
    # ------------------------------------------------------------
    # Examples:
    #   camera achha but battery more important
    #   performance important but battery zyada important
    #   display achha ho but camera priority
    #
    # The dimension appearing after "but/lekin" with stronger wording
    # receives the larger boost.
    relative_aliases = {
        "camera": ("camera",),
        "battery": ("battery",),
        "display": ("display", "screen"),
        "performance": ("performance", "processor", "speed"),
        "sound_quality": ("sound", "audio"),
        "call_quality": ("call quality", "calling", "mic", "microphone"),
        "anc": ("anc", "noise cancellation"),
        "comfort": ("comfort", "comfortable"),
        "picture_quality": ("picture quality", "picture"),
        "brightness": ("brightness", "bright"),
        "refresh_rate": ("refresh rate", "hz"),
        "gaming_features": ("gaming", "game"),
        "graphics": ("graphics", "gpu"),
        "portability": ("portable", "lightweight"),
    }

    relative_markers = (
        "more important",
        "zyada important",
        "higher priority",
        "top priority",
        "priority",
        "sabse important",
        "most important",
    )

    for dimension, aliases in relative_aliases.items():
        if dimension not in weights:
            continue

        for alias in aliases:
            alias_re = re.escape(alias)

            if re.search(
                rf"(?:but|lekin|however).{{0,35}}\b{alias_re}\b"
                rf".{{0,25}}(?:"
                + "|".join(re.escape(x) for x in relative_markers)
                + r")",
                text,
            ):
                weights[dimension] += 18
                break

            if re.search(
                rf"\b{alias_re}\b.{{0,25}}(?:"
                + "|".join(re.escape(x) for x in relative_markers)
                + r").{0,35}(?:but|lekin|however)",
                text,
            ):
                weights[dimension] += 10
                break

    # ------------------------------------------------------------
    # No-compromise / non-negotiable language
    # ------------------------------------------------------------
    no_compromise_aliases = {
        "battery": ("battery",),
        "camera": ("camera",),
        "performance": ("performance", "processor", "speed"),
        "display": ("display", "screen"),
        "picture_quality": ("picture quality", "picture"),
        "sound_quality": ("sound", "audio"),
        "call_quality": ("call quality", "calling"),
        "anc": ("anc", "noise cancellation"),
        "graphics": ("graphics", "gpu"),
    }

    no_compromise_patterns = (
        "no compromise",
        "compromise nahi",
        "compromise nahi chahiye",
        "must be good",
        "must be strong",
        "bilkul compromise nahi",
        "non negotiable",
        "non-negotiable",
    )

    for dimension, aliases in no_compromise_aliases.items():
        if dimension not in weights:
            continue

        matched = False

        for alias in aliases:
            alias_re = re.escape(alias)

            for phrase in no_compromise_patterns:
                phrase_re = re.escape(phrase)

                if (
                    re.search(
                        rf"\b{alias_re}\b.{{0,30}}\b{phrase_re}\b",
                        text,
                    )
                    or re.search(
                        rf"\b{phrase_re}\b.{{0,30}}\b{alias_re}\b",
                        text,
                    )
                ):
                    weights[dimension] += 25
                    matched = True
                    break

            if matched:
                break

    # ------------------------------------------------------------
    # Secondary supportive wording
    # ------------------------------------------------------------
    # "gaming important but battery bhi strong" should keep gaming
    # primary while still giving battery meaningful weight.
    supportive_aliases = {
        "battery": ("battery",),
        "camera": ("camera",),
        "display": ("display", "screen"),
        "performance": ("performance", "processor"),
        "sound_quality": ("sound", "audio"),
        "portability": ("portable", "lightweight"),
    }

    for dimension, aliases in supportive_aliases.items():
        if dimension not in weights:
            continue

        if any(
            re.search(
                rf"\b{re.escape(alias)}\b.{{0,20}}\b(?:bhi|also|too)\b"
                rf"|\b(?:bhi|also|too)\b.{{0,20}}\b{re.escape(alias)}\b",
                text,
            )
            for alias in aliases
        ):
            weights[dimension] += 8

    # Hard budget constraints are always important.
    if "budget_max" in hard_constraints_for_weights:
        weights["budget"] = max(weights.get("budget", 0), 25)

    return normalize_weights(weights)


def parse_query(query: str) -> dict:
    text = normalize(query)
    intent, compare = detect_intent(text)
    budget_min, budget_max = detect_budget(text)
    category = detect_category(text)
    user_profile = detect_user_profile(text)
    use_cases = detect_use_cases(text)

    hard_constraints, must_have, preferred, avoid = detect_requirements(
        text, category, user_profile, use_cases
    )

    parsed = asdict(
        ShoppingIntent(
            intent=intent,
            category=category,
            budget_min=budget_min,
            budget_max=budget_max,
            features=detect_features(text),
            brands=detect_brands(text),
            compare=compare,
            keywords=text.split(),
            user_profile=user_profile,
            use_case=use_cases,
            hard_constraints=hard_constraints,
            must_have=must_have,
            preferred=preferred,
            avoid=avoid,
            priority_weights=build_priority_weights(
                category,
                user_profile,
                use_cases,
                must_have,
                preferred,
                hard_constraints,
                text,
            ),
        )
    )

    # TV-specific structured requirements live alongside the stable
    # common ShoppingIntent contract. This keeps other category engines
    # backward-compatible while giving the specialist TV engine precise
    # inputs for size, panel technology and gaming/display requirements.
    parsed["tv_requirements"] = (
        detect_tv_requirements(text)
        if category == "television"
        else {}
    )

    return parsed


if __name__ == "__main__":
    tests = [
        "Best gaming laptop under 70000",
        "Phone under 25000 for my father with good battery and large display",
        "Best earbuds under 3000 with ANC",
        "Laptop for coding and occasional gaming under 60000",
        "Mobile for student with good camera and battery under 20000",
    ]
    for query in tests:
        print("=" * 80)
        print("QUERY:", query)
        print(parse_query(query))
