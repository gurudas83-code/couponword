#!/usr/bin/env python3
"""
Coupon World AI OS
Product Fit Signal Builder v1.0

Bridge:
Product Intelligence Profile -> fit_signals -> Weighted Fit Engine

Conservative rule:
If evidence is missing, return UNKNOWN. Never guess a positive match.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "python") not in sys.path:
    sys.path.insert(0, str(ROOT / "python"))

from intent_engine import parse_query
from product_intelligence_bridge import build_profile
from weighted_fit_engine import calculate_product_fit


def signal(match: float | None, reason: str, status: str = "verified") -> dict[str, Any]:
    return {
        "match": match,
        "status": status if match is not None else "unknown",
        "reason": reason,
    }


def text_blob(profile: dict[str, Any]) -> str:
    parts = [
        str(profile.get("title") or ""),
        str(profile.get("brand") or ""),
        json.dumps(profile.get("attributes", {}), ensure_ascii=False),
        " ".join(str(x) for x in profile.get("features", []) if x),
        " ".join(str(x) for x in profile.get("best_for", []) if x),
        " ".join(str(x) for x in profile.get("limitations", []) if x),
    ]
    return " ".join(parts).lower()


def numeric(pattern: str, text: str) -> float | None:
    m = re.search(pattern, text, re.I)
    if not m:
        return None
    try:
        return float(m.group(1))
    except (TypeError, ValueError):
        return None


def budget_signal(profile: dict[str, Any], intent: dict[str, Any]) -> dict[str, Any]:
    price = profile.get("price")
    budget_max = intent.get("budget_max")

    if budget_max in (None, ""):
        return signal(1.0, "No maximum budget constraint supplied", "derived")

    if price in (None, ""):
        return signal(None, "Current verified selling price is unavailable")

    try:
        price_f = float(price)
        budget_f = float(budget_max)
    except (TypeError, ValueError):
        return signal(None, "Price could not be evaluated")

    if price_f <= budget_f:
        return signal(1.0, f"Verified price {price_f:g} is within budget {budget_f:g}")

    return signal(0.0, f"Verified price {price_f:g} exceeds budget {budget_f:g}")


def battery_signal(text: str) -> dict[str, Any]:
    playback_values = [
        float(x)
        for x in re.findall(
            r"\b(\d{1,3}(?:\.\d+)?)\s*(?:h|hr|hrs|hour|hours)\b",
            text,
            re.I,
        )
    ]

    capacities = [
        float(x)
        for x in re.findall(r"\b(\d{2,5})\s*mah\b", text, re.I)
    ]

    # Earbud/product pages commonly state both single-charge playback
    # and total playback with the charging case. For shopping endurance,
    # the largest explicitly verified playback figure is the useful signal.
    playback = max(playback_values) if playback_values else None

    if playback is not None:
        if playback >= 50:
            return signal(
                1.0,
                f"Long verified playback/endurance: {playback:g} hours",
            )
        if playback >= 30:
            return signal(
                0.90,
                f"Strong verified playback/endurance: {playback:g} hours",
            )
        if playback >= 15:
            return signal(
                0.75,
                f"Moderate verified playback/endurance: {playback:g} hours",
            )
        return signal(
            0.55,
            f"Verified playback/endurance: {playback:g} hours",
        )

    # Capacity fallback is intentionally conservative.
    # Large mAh thresholds mainly apply to phones/laptops, while tiny
    # earbud/case capacities must not be converted into guessed runtime.
    if capacities:
        capacity = max(capacities)

        if capacity >= 5500:
            return signal(
                1.0,
                f"Large verified battery capacity: {capacity:g}mAh",
            )
        if capacity >= 5000:
            return signal(
                0.90,
                f"Strong verified battery capacity: {capacity:g}mAh",
            )
        if capacity >= 4500:
            return signal(
                0.75,
                f"Moderate verified battery capacity: {capacity:g}mAh",
            )
        if capacity >= 4000:
            return signal(
                0.60,
                f"Verified battery capacity: {capacity:g}mAh",
            )

    return signal(None, "No comparable battery/endurance evidence found")

def display_signal(text: str) -> dict[str, Any]:
    score = 0.0
    reasons: list[str] = []

    # This builder currently serves phone-oriented fit scoring.
    # Accept only plausible handheld display sizes so unrelated
    # measurements such as 12-inch accessories or packaging do not
    # become smartphone display evidence.
    display_sizes = [
        float(x)
        for x in re.findall(
            r"\b(\d{1,2}(?:\.\d{1,2})?)\s*(?:\\?\"|-?inch|inches?)",
            text,
            re.I,
        )
        if 4.0 <= float(x) <= 8.5
    ]

    size = max(display_sizes) if display_sizes else None

    if size is not None:
        if size >= 6.6:
            score += 0.45
        elif size >= 6.3:
            score += 0.35
        else:
            score += 0.25

        reasons.append(f"{size:g}-inch class display")

    if "amoled" in text or "oled" in text:
        score += 0.30
        reasons.append("AMOLED/OLED")

    if re.search(r"\b(?:120|144)\s*hz\b", text):
        score += 0.20
        reasons.append("high refresh rate")

    brightness = numeric(r"\b(\d{3,5})\s*(?:nit|nits)\b", text)

    if brightness is not None and brightness >= 1500:
        score += 0.10
        reasons.append("high peak brightness")

    if not reasons:
        return signal(None, "No reliable display evidence found")

    return signal(min(score, 1.0), ", ".join(reasons))


def performance_signal(text: str) -> dict[str, Any]:
    high = (
        "snapdragon 8 elite",
        "snapdragon 8s gen 4",
        "dimensity 9400",
        "dimensity 9300",
        "rtx 4060",
        "rtx 4070",
        "rtx 4080",
        "rtx 4090",
    )
    medium = (
        "snapdragon 7",
        "dimensity 8",
        "core ultra",
        "ryzen 7",
        "ryzen 5",
        "core i7",
        "core i5",
        "rtx 4050",
        "rtx 3050",
    )

    if any(x in text for x in high):
        return signal(1.0, "High-performance verified chipset/GPU class detected")
    if any(x in text for x in medium):
        return signal(0.80, "Strong mainstream verified performance hardware detected")
    if any(x in text for x in ("snapdragon", "dimensity", "ryzen", "core i", "tensor", "exynos")):
        return signal(0.65, "Recognized verified performance hardware detected")

    return signal(None, "No reliable performance evidence found")


def ram_signal(text: str) -> dict[str, Any]:
    amount = numeric(r"\b(\d{1,3})\s*gb\s*ram\b", text)
    if amount is None:
        return signal(None, "No verified RAM capacity found")

    if amount >= 16:
        return signal(1.0, f"{amount:g}GB RAM")
    if amount >= 12:
        return signal(0.95, f"{amount:g}GB RAM")
    if amount >= 8:
        return signal(0.80, f"{amount:g}GB RAM")
    if amount >= 6:
        return signal(0.65, f"{amount:g}GB RAM")
    return signal(0.45, f"{amount:g}GB RAM")


def storage_signal(text: str) -> dict[str, Any]:
    amount = numeric(r"\b(\d{2,4})\s*gb\s*(?:storage|internal storage)?", text)
    fast = any(x in text for x in ("ufs 4.0", "ssd"))

    if amount is not None:
        if amount >= 512:
            base = 1.0
        elif amount >= 256:
            base = 0.90
        elif amount >= 128:
            base = 0.75
        else:
            base = 0.55

        if fast:
            base = min(1.0, base + 0.05)

        return signal(base, f"{amount:g}GB storage" + (" with fast storage technology" if fast else ""))

    if fast:
        return signal(0.75, "Fast verified storage technology detected")

    return signal(None, "No reliable storage evidence found")


def software_support_signal(text: str) -> dict[str, Any]:
    years = [
        float(x)
        for x in re.findall(r"\b(\d+)\s+years?\s+(?:of\s+)?(?:android updates|security patches|software updates)", text, re.I)
    ]
    if not years:
        return signal(None, "No verified support-duration evidence found")

    longest = max(years)
    if longest >= 7:
        return signal(1.0, f"Long verified software/security support: up to {longest:g} years")
    if longest >= 5:
        return signal(0.90, f"Strong verified support duration: {longest:g} years")
    if longest >= 3:
        return signal(0.75, f"Moderate verified support duration: {longest:g} years")
    return signal(0.55, f"Verified support duration: {longest:g} years")


def connectivity_signal(text: str) -> dict[str, Any]:
    score = 0.0
    reasons: list[str] = []

    # Signal builders must be safe when called directly as well as
    # through text_blob(), which already returns lowercase text.
    normalized = str(text or "").lower()

    # 5G alone is strong positive connectivity evidence.
    if re.search(r"\b5g\b", normalized):
        score += 0.80
        reasons.append("5G")

    if "wi-fi 7" in normalized or "wifi 7" in normalized:
        score += 0.30
        reasons.append("Wi-Fi 7")
    elif "wi-fi 6" in normalized or "wifi 6" in normalized:
        score += 0.25
        reasons.append("Wi-Fi 6")

    bt = numeric(
        r"bluetooth(?:\s+version)?\s*(5\.\d)",
        normalized,
    )

    if bt is not None:
        score += 0.30 if bt >= 5.3 else 0.20
        reasons.append(f"Bluetooth {bt:g}")

    if not reasons:
        return signal(
            None,
            "No reliable connectivity evidence found",
        )

    return signal(min(score, 1.0), ", ".join(reasons))


def anc_signal(text: str) -> dict[str, Any]:
    explicit_anc = bool(
        re.search(
            r"\b(?:anc|active noise cancellation|active noise cancelling)\b",
            text,
            re.I,
        )
    )

    if not explicit_anc:
        return signal(
            None,
            "No explicit listening ANC evidence found",
        )

    depth_values = [
        float(x)
        for x in re.findall(
            r"\b(\d{1,2}(?:\.\d+)?)\s*db\b",
            text,
            re.I,
        )
    ]

    depth = max(depth_values) if depth_values else None

    if depth is not None:
        if depth >= 50:
            return signal(
                1.0,
                f"Deep verified ANC up to {depth:g}dB",
            )
        if depth >= 40:
            return signal(
                0.90,
                f"Strong verified ANC up to {depth:g}dB",
            )

    return signal(
        0.75,
        "Verified explicit ANC support detected",
    )

def sound_quality_signal(text: str) -> dict[str, Any]:
    score = 0.0
    reasons: list[str] = []

    if "hi-res audio wireless" in text or "hi res audio wireless" in text:
        score += 0.40
        reasons.append("Hi-Res Audio Wireless")

    if "lhdc" in text or "ldac" in text:
        score += 0.25
        reasons.append("high-resolution codec support")

    if "dual audio drivers" in text or "dual dynamic" in text:
        score += 0.25
        reasons.append("dual-driver design")
    elif re.search(r"\b\d{1,2}\s*mm\b.*driver", text):
        score += 0.15
        reasons.append("verified driver specification")

    if "nextbass" in text:
        score += 0.10
        reasons.append("bass-enhancement technology")

    if not reasons:
        return signal(None, "No conservative sound-quality evidence found")

    return signal(min(score, 1.0), ", ".join(reasons))


def call_quality_signal(text: str) -> dict[str, Any]:
    score = 0.0
    reasons: list[str] = []

    mic_count = None

    numeric_mic = re.search(
        r"\b(\d+)\s*[- ]?\s*(?:microphones?|mics?)\b",
        text,
        re.I,
    )

    reverse_numeric_mic = re.search(
        r"\b(?:microphones?|mics?)\s*[:=-]?\s*(\d+)\b",
        text,
        re.I,
    )

    if numeric_mic:
        mic_count = float(numeric_mic.group(1))
    elif reverse_numeric_mic:
        mic_count = float(reverse_numeric_mic.group(1))
    elif re.search(r"\b(?:quad|four)\s+(?:microphones?|mics?)\b", text, re.I):
        mic_count = 4.0
    elif re.search(r"\b(?:dual|two)\s+(?:microphones?|mics?)\b", text, re.I):
        mic_count = 2.0

    if mic_count is not None:
        if mic_count >= 6:
            score += 0.55
        elif mic_count >= 4:
            score += 0.45
        elif mic_count >= 2:
            score += 0.30

        reasons.append(f"{mic_count:g} microphones")

    call_noise = bool(
        re.search(
            r"\b(?:enc|environment(?:al)? noise cancellation|"
            r"ai noise cancellation(?: for)? calls?|"
            r"noise cancellation call|"
            r"call noise cancellation|"
            r"clear call|crystal clear call|"
            r"enx)\b",
            text,
            re.I,
        )
    )

    if call_noise:
        score += 0.35
        reasons.append("call-noise reduction technology")

    if not reasons:
        return signal(
            None,
            "No reliable call-quality evidence found",
        )

    return signal(min(score, 1.0), ", ".join(reasons))

def ease_of_use_signal(text: str) -> dict[str, Any]:
    # Do not infer ease-of-use from brand/OS alone.
    if any(x in text for x in ("easy to use", "simple to use", "easy ui", "simple ui")):
        return signal(0.90, "Verified usability evidence indicates simple/easy use")
    return signal(None, "Ease-of-use is not sufficiently verified")


def camera_signal(text: str) -> dict[str, Any]:
    # Megapixels alone are not enough to claim camera quality.
    if "camera specifications have not yet been added" in text:
        return signal(None, "Camera evidence is explicitly incomplete")
    if "ois" in text or "optical image stabilization" in text:
        return signal(0.75, "Verified OIS evidence found")
    return signal(None, "Camera quality is not sufficiently verified")


def generic_unknown(name: str) -> dict[str, Any]:
    return signal(None, f"No conservative v1 scoring rule/evidence for {name}")


def capacity_requirement_signal(
    requirement: str,
    text: str,
) -> dict[str, Any]:
    """
    Evaluate query-specific RAM/storage requirements.

    Examples:
        8gb_ram
        128gb_storage

    Normal shopping wording means "at least" the requested capacity.
    Missing evidence remains UNKNOWN.
    """

    ram_match = re.fullmatch(r"(\d+)gb_ram", requirement)
    if ram_match:
        required = float(ram_match.group(1))
        actual = numeric(
            r"\b(\d{1,3})\s*gb\s*ram\b",
            text,
        )

        if actual is None:
            return signal(
                None,
                f"Required {required:g}GB RAM, but verified RAM capacity is unavailable",
            )

        if actual >= required:
            return signal(
                1.0,
                f"Verified {actual:g}GB RAM satisfies requirement of at least {required:g}GB",
            )

        return signal(
            0.0,
            f"Verified {actual:g}GB RAM is below required {required:g}GB",
        )

    storage_match = re.fullmatch(r"(\d+)gb_storage", requirement)
    if storage_match:
        required = float(storage_match.group(1))
        actual = numeric(
            r"\b(\d{2,4})\s*gb\s*(?:storage|internal storage|rom)\b",
            text,
        )

        if actual is None:
            return signal(
                None,
                f"Required {required:g}GB storage, but verified storage capacity is unavailable",
            )

        if actual >= required:
            return signal(
                1.0,
                f"Verified {actual:g}GB storage satisfies requirement of at least {required:g}GB",
            )

        return signal(
            0.0,
            f"Verified {actual:g}GB storage is below required {required:g}GB",
        )

    return generic_unknown(requirement)


BUILDERS = {
    "budget": lambda p, i, t: budget_signal(p, i),
    "battery": lambda p, i, t: battery_signal(t),
    "display": lambda p, i, t: display_signal(t),
    "ease_of_use": lambda p, i, t: ease_of_use_signal(t),
    "camera": lambda p, i, t: camera_signal(t),
    "performance": lambda p, i, t: performance_signal(t),
    "ram": lambda p, i, t: ram_signal(t),
    "storage": lambda p, i, t: storage_signal(t),
    "software_support": lambda p, i, t: software_support_signal(t),
    "connectivity": lambda p, i, t: connectivity_signal(t),
    "anc": lambda p, i, t: anc_signal(t),
    "sound_quality": lambda p, i, t: sound_quality_signal(t),
    "call_quality": lambda p, i, t: call_quality_signal(t),
}


def build_fit_signals(profile: dict[str, Any], intent: dict[str, Any]) -> dict[str, dict[str, Any]]:
    text = text_blob(profile)
    weights = intent.get("priority_weights", {})
    signals: dict[str, dict[str, Any]] = {}

    if not isinstance(weights, dict):
        return signals

    for criterion in weights:
        builder = BUILDERS.get(criterion)
        if builder is None:
            signals[criterion] = generic_unknown(criterion)
        else:
            signals[criterion] = builder(profile, intent, text)

    # Bridge query-specific must-have capacities into fit_signals.
    # Weighted Fit Engine can then enforce them without knowing how
    # product evidence was extracted.
    must_have = intent.get("must_have", [])

    if isinstance(must_have, list):
        for requirement in must_have:
            requirement = str(requirement).strip().lower()

            if (
                re.fullmatch(r"\d+gb_ram", requirement)
                or re.fullmatch(r"\d+gb_storage", requirement)
            ):
                signals[requirement] = capacity_requirement_signal(
                    requirement,
                    text,
                )

    return signals


def score_product(product_id: str, query: str) -> dict[str, Any] | None:
    profile = build_profile(product_id)
    if profile is None:
        return None

    intent = parse_query(query)
    profile["fit_signals"] = build_fit_signals(profile, intent)

    assessment = calculate_product_fit(profile, intent)

    return {
        "query": query,
        "intent": intent,
        "profile": profile,
        "assessment": assessment,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Score a real Coupon World product against a shopping query"
    )
    parser.add_argument("--product-id", required=True)
    parser.add_argument("--query", required=True)
    args = parser.parse_args()

    result = score_product(args.product_id, args.query)

    if result is None:
        print("ERROR: Product not found")
        return 1

    profile = result["profile"]
    assessment = result["assessment"]

    print("=" * 72)
    print("COUPON WORLD REAL PRODUCT FIT TEST")
    print("=" * 72)
    print("QUERY:", result["query"])
    print("PRODUCT:", profile.get("title"))
    print("FIT:", f'{assessment.get("fit_percent", 0)}%')
    print("RAW FIT:", f'{assessment.get("raw_fit_percent", 0)}%')
    print("EVIDENCE COVERAGE:", f'{assessment.get("evidence_coverage_percent", 0)}%')
    print("CONFIDENCE:", str(assessment.get("recommendation_confidence", "low")).upper())
    print("ELIGIBLE:", assessment.get("eligible"))
    print()

    for criterion in assessment.get("criteria", []):
        match = criterion.get("match_score")
        match_text = "UNKNOWN" if match is None else f"{round(float(match) * 100)}%"
        print(
            f'{criterion.get("criterion"):18} '
            f'weight={criterion.get("weight"):>3} '
            f'match={match_text:>7} | '
            f'{criterion.get("reason")}'
        )

    failures = assessment.get("hard_constraint_failures", [])
    if failures:
        print()
        print("HARD CONSTRAINT FAILURES:")
        for item in failures:
            print(" -", item)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())



