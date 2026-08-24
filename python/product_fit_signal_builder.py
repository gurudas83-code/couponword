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
import ast
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
    def evidence_text(value: Any) -> str:
        if value in (None, ""):
            return ""

        # Native structured evidence:
        # use only human-readable evidence fields.
        if isinstance(value, dict):
            for key in ("text", "value", "label"):
                candidate = value.get(key)
                if candidate not in (None, ""):
                    return str(candidate)

            return ""

        # Some upstream paths currently duplicate evidence objects
        # as their Python string representation, e.g.
        #
        # "{'text': 'Battery Capacity ... 5000',
        #   'confidence': 77, ...}"
        #
        # Parse these safely and again retain ONLY the evidence text.
        if isinstance(value, str):
            stripped = value.strip()

            if (
                stripped.startswith("{")
                and stripped.endswith("}")
                and (
                    "'text'" in stripped
                    or '"text"' in stripped
                    or "'value'" in stripped
                    or '"value"' in stripped
                    or "'label'" in stripped
                    or '"label"' in stripped
                )
            ):
                try:
                    parsed = ast.literal_eval(stripped)
                except (ValueError, SyntaxError):
                    parsed = None

                if isinstance(parsed, dict):
                    for key in ("text", "value", "label"):
                        candidate = parsed.get(key)
                        if candidate not in (None, ""):
                            return str(candidate)

                    return ""

            return value

        return str(value)

    def list_text(values: Any) -> str:
        if not isinstance(values, list):
            return evidence_text(values)

        return " ".join(
            evidence_text(item)
            for item in values
            if evidence_text(item)
        )

    attributes = profile.get("attributes", {})

    if isinstance(attributes, dict):
        attribute_parts = []

        for key, value in attributes.items():
            rendered = evidence_text(value)

            if rendered:
                attribute_parts.append(
                    f"{key} {rendered}"
                )

        attributes_text = " ".join(attribute_parts)
    else:
        attributes_text = evidence_text(attributes)

    parts = [
        evidence_text(profile.get("title")),
        evidence_text(profile.get("brand")),
        evidence_text(profile.get("description")),
        attributes_text,
        list_text(profile.get("features", [])),
        list_text(profile.get("best_for", [])),
        list_text(profile.get("limitations", [])),
    ]

    return " ".join(
        part
        for part in parts
        if part
    ).lower()

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
        for x in re.findall(
            r"\b(\d{2,5})\s*mah\b",
            text,
            re.I,
        )
    ]

    # Label-first official specifications, e.g.
    # "Battery Capacity (mAh, Typical) 5000"
    capacities.extend(
        float(x)
        for x in re.findall(
            r"battery\s+capacity[^\n\r]{0,40}?(\d{3,5})\b",
            text,
            re.I,
        )
    )

    # Label-first endurance, e.g.
    # "Video Playback Time (Hours) Up to 17"
    playback_values.extend(
        float(x)
        for x in re.findall(
            r"(?:video\s+)?playback\s+time[^\n\r]{0,40}?"
            r"(?:up\s+to\s+)?(\d{1,3}(?:\.\d+)?)\b",
            text,
            re.I,
        )
    )

    candidates: list[tuple[float, str]] = []

    if playback_values:
        playback = max(playback_values)

        if playback >= 50:
            candidates.append((
                1.0,
                f"Long verified playback/endurance: {playback:g} hours",
            ))
        elif playback >= 30:
            candidates.append((
                0.90,
                f"Strong verified playback/endurance: {playback:g} hours",
            ))
        elif playback >= 15:
            candidates.append((
                0.75,
                f"Moderate verified playback/endurance: {playback:g} hours",
            ))
        else:
            candidates.append((
                0.55,
                f"Verified playback/endurance: {playback:g} hours",
            ))

    if capacities:
        capacity = max(capacities)

        if capacity >= 5500:
            candidates.append((
                1.0,
                f"Large verified battery capacity: {capacity:g}mAh",
            ))
        elif capacity >= 5000:
            candidates.append((
                0.90,
                f"Strong verified battery capacity: {capacity:g}mAh",
            ))
        elif capacity >= 4500:
            candidates.append((
                0.75,
                f"Moderate verified battery capacity: {capacity:g}mAh",
            ))
        elif capacity >= 4000:
            candidates.append((
                0.60,
                f"Verified battery capacity: {capacity:g}mAh",
            ))

    if not candidates:
        return signal(
            None,
            "No comparable battery/endurance evidence found",
        )

    best_score, best_reason = max(
        candidates,
        key=lambda item: item[0],
    )

    return signal(best_score, best_reason)

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



def laptop_display_signal(text: str) -> dict[str, Any]:
    sizes = [
        float(x)
        for x in re.findall(
            r"\b(\d{2}(?:\.\d)?)\s*(?:\\?\"|-?inch|inches?)",
            text,
            re.I,
        )
        if 10.0 <= float(x) <= 19.0
    ]

    score = 0.0
    reasons: list[str] = []

    if sizes:
        size = max(sizes)
        score += 0.35
        reasons.append(f"{size:g}-inch laptop display")

    if any(x in text for x in ("oled", "amoled")):
        score += 0.30
        reasons.append("OLED display")

    if any(x in text for x in ("ips", "ips-level", "ips level")):
        score += 0.15
        reasons.append("IPS-class panel")

    if re.search(r"\b(?:120|144|165|240)\s*hz\b", text, re.I):
        score += 0.20
        reasons.append("high refresh rate")

    if any(x in text for x in ("2.5k", "2.8k", "3k", "4k", "qhd")):
        score += 0.20
        reasons.append("high-resolution display")

    if not reasons:
        return signal(None, "No reliable laptop display evidence found")

    return signal(min(score, 1.0), ", ".join(reasons))


def laptop_battery_signal(text: str) -> dict[str, Any]:
    hours = [
        float(x)
        for x in re.findall(
            r"\b(\d{1,2}(?:\.\d+)?)\s*(?:hours?|hrs?|hr)\b",
            text,
            re.I,
        )
    ]

    if hours:
        endurance = max(hours)

        if endurance >= 12:
            return signal(
                1.0,
                f"Strong verified laptop battery endurance: {endurance:g} hours",
            )

        if endurance >= 8:
            return signal(
                0.80,
                f"Good verified laptop battery endurance: {endurance:g} hours",
            )

        if endurance >= 5:
            return signal(
                0.65,
                f"Moderate verified laptop battery endurance: {endurance:g} hours",
            )

        return signal(
            0.50,
            f"Verified laptop battery endurance: {endurance:g} hours",
        )

    wh_values = [
        float(x)
        for x in re.findall(
            r"\b(\d{2,3}(?:\.\d+)?)\s*wh\b",
            text,
            re.I,
        )
    ]

    if wh_values:
        capacity = max(wh_values)

        if capacity >= 70:
            return signal(0.90, f"Large verified laptop battery: {capacity:g}Wh")

        if capacity >= 55:
            return signal(0.75, f"Good verified laptop battery: {capacity:g}Wh")

        if capacity >= 40:
            return signal(0.60, f"Moderate verified laptop battery: {capacity:g}Wh")

    return signal(None, "No reliable laptop battery evidence found")


def portability_signal(text: str) -> dict[str, Any]:
    weights = [
        float(x)
        for x in re.findall(
            r"\b(\d(?:\.\d{1,2})?)\s*kg\b",
            text,
            re.I,
        )
        if 0.5 <= float(x) <= 5.0
    ]

    if weights:
        weight = min(weights)

        if weight <= 1.3:
            return signal(1.0, f"Highly portable verified weight: {weight:g}kg")

        if weight <= 1.6:
            return signal(0.85, f"Portable verified weight: {weight:g}kg")

        if weight <= 2.0:
            return signal(0.65, f"Moderate verified weight: {weight:g}kg")

        return signal(0.45, f"Relatively heavy verified weight: {weight:g}kg")

    if any(
        phrase in text
        for phrase in ("lightweight", "thin and light", "thin & light", "ultralight")
    ):
        return signal(0.80, "Verified lightweight/thin-and-light positioning")

    return signal(None, "No reliable portability evidence found")


def build_quality_signal(text: str) -> dict[str, Any]:
    reasons: list[str] = []
    score = 0.0

    if any(
        phrase in text
        for phrase in (
            "aluminium chassis",
            "aluminum chassis",
            "aluminium body",
            "aluminum body",
            "metal chassis",
            "metal body",
        )
    ):
        score += 0.70
        reasons.append("metal/aluminium construction")

    if any(
        phrase in text
        for phrase in (
            "mil-std",
            "mil std",
            "military grade",
            "military-grade",
        )
    ):
        score += 0.30
        reasons.append("durability-standard evidence")

    if not reasons:
        return signal(None, "No conservative laptop build-quality evidence found")

    return signal(min(score, 1.0), ", ".join(reasons))


def category_display_signal(
    profile: dict[str, Any],
    intent: dict[str, Any],
    text: str,
) -> dict[str, Any]:
    if str(intent.get("category") or "").lower() == "laptop":
        return laptop_display_signal(text)

    return display_signal(text)


def category_battery_signal(
    profile: dict[str, Any],
    intent: dict[str, Any],
    text: str,
) -> dict[str, Any]:
    if str(intent.get("category") or "").lower() == "laptop":
        return laptop_battery_signal(text)

    return battery_signal(text)


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



def graphics_signal(text: str) -> dict[str, Any]:
    normalized = str(text or "").lower()

    very_high = (
        "rtx 4090",
        "rtx 4080",
        "rtx 4070",
        "rtx 4060",
    )

    high = (
        "rtx 4050",
        "rx 7700",
        "rx 7600",
        "rx 7600s",
    )

    medium = (
        "rtx 3050",
        "rtx 2050",
        "gtx 1660",
        "gtx 1650",
        "rx 6500",
    )

    integrated = (
        "intel iris xe",
        "intel uhd",
        "intel arc integrated",
        "radeon 780m",
        "radeon 680m",
        "radeon graphics",
        "integrated graphics",
    )

    if any(x in normalized for x in very_high):
        return signal(
            1.0,
            "High-end dedicated gaming GPU verified",
        )

    if any(x in normalized for x in high):
        return signal(
            0.90,
            "Strong dedicated gaming GPU verified",
        )

    if any(x in normalized for x in medium):
        return signal(
            0.70,
            "Moderate dedicated gaming GPU verified",
        )

    if any(x in normalized for x in integrated):
        return signal(
            0.35,
            "Integrated graphics detected; limited for demanding gaming",
        )

    if any(x in normalized for x in ("nvidia geforce", "radeon rx")):
        return signal(
            0.60,
            "Dedicated graphics hardware detected",
        )

    return signal(
        None,
        "No reliable graphics/GPU evidence found",
    )


def ram_signal(text: str) -> dict[str, Any]:
    amount = numeric(r"\b(\d{1,3})\s*gb\s*ram\b", text)

    if amount is None:
        amount = numeric(
            r"\b(\d{1,3})\s*gb\s*\+\s*\d{2,4}\s*gb\b",
            text,
        )

    if amount is None:
        amount = numeric(
            r"\b(\d{1,3})\s*\+\s*\d{2,4}\s*gb\b",
            text,
        )

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
    amount = numeric(
        r"\b(\d{2,4})\s*gb\s*(?:storage|internal storage|rom|ssd)\b",
        text,
    )

    if amount is None:
        compact = re.search(
            r"\b\d{1,3}\s*(?:gb\s*)?\+\s*(\d{2,4})\s*gb\b",
            text,
            re.I,
        )
        if compact:
            amount = float(compact.group(1))
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
    normalized = str(text or "")

    # ---------------------------------------------------------
    # 1. Explicit support duration
    # ---------------------------------------------------------
    # Examples:
    #   6 years of software updates
    #   6 years of Android updates
    #   6 years of security updates
    #   6 years security patches
    years = [
        float(x)
        for x in re.findall(
            r"\b(\d+(?:\.\d+)?)\s+years?\s+"
            r"(?:of\s+)?"
            r"(?:android\s+updates?|"
            r"android\s+upgrades?|"
            r"security\s+patches?|"
            r"security\s+updates?|"
            r"software\s+updates?|"
            r"os\s+updates?)\b",
            normalized,
            re.I,
        )
    ]

    # ---------------------------------------------------------
    # 2. Explicit support-valid-until date
    # ---------------------------------------------------------
    # Manufacturer pages commonly provide support as:
    #
    #   Security Update Period (Valid until) 31 December 2031
    #
    # Convert that verified date into remaining support years.
    date_match = re.search(
        r"(?:security\s+update\s+period|"
        r"software\s+support|"
        r"support\s+period)"
        r"[^\n\r]{0,80}?"
        r"(?:valid\s+until|until|through|to)"
        r"[^\d]{0,20}"
        r"(\d{1,2})\s+"
        r"(january|february|march|april|may|june|july|"
        r"august|september|october|november|december)"
        r"\s+(\d{4})",
        normalized,
        re.I,
    )

    if date_match:
        from datetime import date

        month_numbers = {
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12,
        }

        try:
            support_end = date(
                int(date_match.group(3)),
                month_numbers[date_match.group(2).lower()],
                int(date_match.group(1)),
            )

            today = date.today()

            remaining_days = (
                support_end - today
            ).days

            if remaining_days > 0:
                remaining_years = remaining_days / 365.2425
                years.append(remaining_years)

        except (TypeError, ValueError):
            pass

    if not years:
        return signal(
            None,
            "No verified support-duration evidence found",
        )

    longest = max(years)

    if longest >= 7:
        return signal(
            1.0,
            f"Long verified software/security support: up to {longest:.1f} years",
        )

    if longest >= 5:
        return signal(
            0.90,
            f"Strong verified support duration: {longest:.1f} years",
        )

    if longest >= 3:
        return signal(
            0.75,
            f"Moderate verified support duration: {longest:.1f} years",
        )

    return signal(
        0.55,
        f"Verified support duration: {longest:.1f} years",
    )

def connectivity_signal(text: str) -> dict[str, Any]:
    score = 0.0
    reasons: list[str] = []

    normalized = str(text or "").lower()

    # ---------------------------------------------------------
    # 5G evidence with negation protection
    # ---------------------------------------------------------
    # A bare "5G" is not sufficient when the surrounding text
    # explicitly says that 5G is absent / unsupported.
    #
    # Examples that must NOT become positive evidence:
    #   "5G not supported"
    #   "does not support 5G"
    #   "no 5G"
    #   "without 5G"
    #   "4G only"
    # ---------------------------------------------------------

    has_5g_token = bool(re.search(r"\b5g\b", normalized))

    negative_5g_patterns = (
        r"\bno\s+5g\b",
        r"\bwithout\s+5g\b",
        r"\bnon[-\s]?5g\b",
        r"\b5g\s+(?:is\s+)?not\s+supported\b",
        r"\b5g\s+unsupported\b",
        r"\b5g\s+not\s+available\b",
        r"\bdoes\s+not\s+support\s+5g\b",
        r"\bdoesn't\s+support\s+5g\b",
        r"\bnot\s+support(?:ed|ing)?\s+5g\b",
        r"\b4g\s+only\b",
        r"\bonly\s+4g\b",
    )

    has_negative_5g = any(
        re.search(pattern, normalized)
        for pattern in negative_5g_patterns
    )

    if has_5g_token and not has_negative_5g:
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
        if has_negative_5g:
            return signal(
                None,
                "5G is explicitly unavailable; no other reliable connectivity evidence found",
            )

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
    """
    Conservatively score verified camera-system evidence.

    Important:
    Megapixel count alone must never be treated as proof of image quality.
    It can provide weak hardware evidence, while features such as OIS,
    telephoto capability and useful multi-camera hardware provide stronger
    support.
    """
    text = str(text or "").lower()

    if "camera specifications have not yet been added" in text:
        return signal(None, "Camera evidence is explicitly incomplete")

    score = 0.0
    reasons: list[str] = []

    # Strong camera-system evidence.
    if "ois" in text or "optical image stabilization" in text:
        score += 0.45
        reasons.append("verified optical image stabilization")

    if re.search(
        r"\btelephoto\b|\boptical\s+zoom\b|\bperiscope\b",
        text,
        re.I,
    ):
        score += 0.30
        reasons.append("verified telephoto/optical-zoom capability")

    # Useful supporting camera-system evidence.
    if re.search(
        r"\bultra[- ]?wide\b|\bultrawide\b|\bwide[- ]angle\b",
        text,
        re.I,
    ):
        score += 0.15
        reasons.append("verified ultrawide camera")

    if re.search(r"\b4k\b.{0,30}\bvideo\b|\bvideo\b.{0,30}\b4k\b", text, re.I):
        score += 0.10
        reasons.append("verified 4K video capability")

    if re.search(
        r"\b(?:dual|triple|quad)\s+(?:rear\s+)?camera\b"
        r"|\b(?:dual|triple|quad)[- ]camera\b",
        text,
        re.I,
    ):
        score += 0.10
        reasons.append("verified multi-camera system")

    # Megapixel specifications are useful hardware evidence, but they do
    # not establish real-world camera quality by themselves.
    megapixels = [
        int(value)
        for value in re.findall(r"\b(\d{1,3})\s*mp\b", text, re.I)
        if int(value) <= 250
    ]

    if megapixels:
        main_mp = max(megapixels)

        if main_mp >= 48:
            score += 0.10
            reasons.append(f"verified {main_mp}MP camera hardware")
        elif main_mp >= 12:
            score += 0.05
            reasons.append(f"verified {main_mp}MP camera hardware")

    if not reasons:
        return signal(None, "Camera quality is not sufficiently verified")

    # Hardware-only evidence must remain moderate unless meaningful
    # imaging capabilities such as OIS/telephoto are also verified.
    strong_evidence = (
        "ois" in text
        or "optical image stabilization" in text
        or bool(
            re.search(
                r"\btelephoto\b|\boptical\s+zoom\b|\bperiscope\b",
                text,
                re.I,
            )
        )
    )

    if strong_evidence:
        score = max(score, 0.70)
    else:
        score = min(score, 0.55)

    return signal(
        min(score, 1.0),
        "; ".join(reasons),
    )


def category_relevance_signal(
    profile: dict[str, Any],
    intent: dict[str, Any],
    text: str,
) -> dict[str, Any]:
    category = str(intent.get("category") or "").strip().lower()

    if not category:
        return signal(None, "Shopping category is not yet identified")

    aliases = {
        "smartphone": ("phone", "mobile", "smartphone"),
        "television": ("tv", "television", "smart tv", "led tv", "oled", "qled"),
        "mixer_grinder": ("mixer grinder", "mixer", "grinder", "mixie"),
        "air_fryer": ("air fryer",),
        "air_conditioner": ("air conditioner", "split ac", "window ac", " ac "),
        "washing_machine": ("washing machine", "washer"),
        "refrigerator": ("refrigerator", "fridge"),
        "shoes": ("shoe", "shoes", "running shoes", "walking shoes", "sneakers"),
        "chair": ("chair", "office chair", "gaming chair"),
        "camera": ("camera", "dslr", "mirrorless"),
        "gift": ("gift", "toy", "toys"),
        "vacuum_cleaner": ("vacuum cleaner", "vacuum"),
        "water_purifier": ("water purifier", "ro purifier"),
        "microwave": ("microwave", "microwave oven"),
        "monitor": ("monitor",),
        "printer": ("printer",),
        "router": ("router", "wifi router", "wi-fi router"),
        "power_bank": ("power bank", "powerbank"),
        "backpack": ("backpack", "rucksack"),
        "luggage": ("luggage", "suitcase", "trolley"),
    }

    haystack = f" {str(text or '').lower()} "
    category_aliases = aliases.get(
        category,
        (category.replace("_", " "),),
    )

    for alias in category_aliases:
        if f" {alias.strip()} " in haystack or alias.strip() in haystack:
            return signal(
                1.0,
                f"Verified product evidence matches shopping category: {category.replace('_', ' ')}",
            )

    return signal(
        None,
        f"No reliable evidence yet confirms category {category.replace('_', ' ')}",
    )


def query_relevance_signal(
    profile: dict[str, Any],
    intent: dict[str, Any],
    text: str,
) -> dict[str, Any]:
    stopwords = {
        "best", "top", "recommend", "recommended", "suggest", "show",
        "buy", "online", "india", "under", "below", "less", "than",
        "upto", "up", "to", "for", "with", "without", "and", "or",
        "the", "a", "an", "my", "me", "good", "latest", "family",
    }

    raw_keywords = intent.get("keywords", [])
    if not isinstance(raw_keywords, list):
        raw_keywords = []

    terms = []

    for item in raw_keywords:
        term = str(item or "").strip().lower()

        if (
            not term
            or term in stopwords
            or term.isdigit()
            or len(term) < 2
        ):
            continue

        if term not in terms:
            terms.append(term)

    if not terms:
        return signal(None, "No meaningful query terms available for relevance scoring")

    haystack = str(text or "").lower()

    matched = [
        term
        for term in terms
        if re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", haystack)
    ]

    if not matched:
        return signal(None, "No reliable query-term match found in product evidence")

    ratio = len(matched) / len(terms)

    if ratio >= 0.75:
        score = 1.0
    elif ratio >= 0.50:
        score = 0.85
    elif ratio >= 0.30:
        score = 0.65
    else:
        score = 0.50

    return signal(
        score,
        "Matched shopping need terms: " + ", ".join(matched[:6]),
    )


def product_identity_signal(
    profile: dict[str, Any],
    intent: dict[str, Any],
    text: str,
) -> dict[str, Any]:
    title = str(profile.get("title") or "").strip()

    if not title:
        return signal(None, "Product title is unavailable")

    tokens = re.findall(r"[A-Za-z0-9]+", title)

    if len(tokens) < 2:
        return signal(None, "Product identity is too generic")

    brand = str(profile.get("brand") or "").strip()

    has_model_marker = bool(
        re.search(r"\b[A-Za-z]*\d+[A-Za-z0-9-]*\b", title)
    )

    if brand and has_model_marker:
        return signal(1.0, "Specific branded product/model identity verified")

    if has_model_marker:
        return signal(0.90, "Specific product/model identity detected")

    if brand:
        return signal(0.85, "Specific branded product identity detected")

    return signal(0.70, "Specific product listing identity detected")



def tv_screen_size_signal(
    profile: dict[str, Any],
    intent: dict[str, Any],
    text: str,
) -> dict[str, Any]:
    requirements = intent.get("tv_requirements", {})
    required = requirements.get("screen_size_inches")

    sizes = [
        int(x)
        for x in re.findall(
            r"\b(32|40|42|43|48|50|55|58|60|65|70|75|77|83|85|86|98|100)"
            r"\s*(?:inch|inches|in|\\?\")\b",
            text,
            re.I,
        )
    ]

    if required is not None:
        if required in sizes:
            return signal(
                1.0,
                f"Verified {required}-inch screen matches requested size",
            )

        if sizes:
            return signal(
                0.0,
                f"Requested {required}-inch TV but listing shows "
                + "/".join(str(x) for x in sorted(set(sizes)))
                + "-inch",
            )

        return signal(
            None,
            f"Requested {required}-inch screen size is not verified",
        )

    if sizes:
        return signal(
            0.85,
            f"TV screen size verified: {sizes[0]} inch",
        )

    return signal(None, "TV screen size is unavailable")


def tv_panel_technology_signal(
    profile: dict[str, Any],
    intent: dict[str, Any],
    text: str,
) -> dict[str, Any]:
    requirements = intent.get("tv_requirements", {})
    required = str(
        requirements.get("panel_technology") or ""
    ).lower()

    lower = text.lower()

    detected = None

    if re.search(r"\b(?:mini[\s-]?led|miniled)\b", lower):
        detected = "mini_led"
    elif re.search(r"\boled\b", lower):
        detected = "oled"
    elif re.search(r"\bqled\b", lower):
        detected = "qled"
    elif re.search(r"\bled\b", lower):
        detected = "led"

    labels = {
        "mini_led": "Mini LED",
        "oled": "OLED",
        "qled": "QLED",
        "led": "LED",
    }

    if required:
        if detected == required:
            return signal(
                1.0,
                f"Verified {labels.get(required, required)} panel "
                "matches requested technology",
            )

        if detected:
            return signal(
                0.0,
                f"Requested {labels.get(required, required)} but "
                f"listing indicates {labels.get(detected, detected)}",
            )

        return signal(
            None,
            f"Requested {labels.get(required, required)} panel "
            "technology is not verified",
        )

    scores = {
        "oled": 0.95,
        "mini_led": 0.92,
        "qled": 0.82,
        "led": 0.60,
    }

    if detected:
        return signal(
            scores[detected],
            f"{labels[detected]} display technology detected",
        )

    return signal(None, "TV panel technology is unavailable")


def tv_refresh_rate_signal(
    profile: dict[str, Any],
    intent: dict[str, Any],
    text: str,
) -> dict[str, Any]:
    requirements = intent.get("tv_requirements", {})
    required = requirements.get("refresh_rate_hz")

    rates = [
        int(x)
        for x in re.findall(
            r"\b(50|60|90|100|120|144|165)\s*hz\b",
            text,
            re.I,
        )
    ]

    verified_rate = max(rates) if rates else None

    if required is not None:
        if verified_rate is None:
            return signal(
                None,
                f"Requested {required}Hz refresh rate is not verified",
            )

        if verified_rate >= int(required):
            return signal(
                1.0,
                f"Verified {verified_rate}Hz satisfies requested "
                f"{required}Hz refresh rate",
            )

        return signal(
            0.0,
            f"Verified {verified_rate}Hz is below requested {required}Hz",
        )

    if verified_rate is None:
        return signal(None, "TV refresh rate is unavailable")

    if verified_rate >= 120:
        return signal(
            0.95,
            f"High-refresh {verified_rate}Hz TV display verified",
        )

    if verified_rate >= 100:
        return signal(
            0.82,
            f"{verified_rate}Hz TV refresh rate verified",
        )

    return signal(
        0.55,
        f"Standard {verified_rate}Hz TV refresh rate verified",
    )


def tv_gaming_features_signal(
    profile: dict[str, Any],
    intent: dict[str, Any],
    text: str,
) -> dict[str, Any]:
    requirements = intent.get("tv_requirements", {})
    lower = text.lower()

    hdmi21 = bool(re.search(r"\bhdmi\s*2\.1\b", lower))
    vrr = bool(
        re.search(r"\b(?:vrr|variable refresh rate)\b", lower)
    )
    allm = bool(
        re.search(r"\b(?:allm|auto low latency mode)\b", lower)
    )
    four_k_120 = bool(
        re.search(
            r"\b(?:4k\s*(?:at|@)?\s*120\s*hz|4k120)\b",
            lower,
        )
    )

    required_hdmi = requirements.get("hdmi_2_1") is True
    required_vrr = requirements.get("vrr") is True
    required_allm = requirements.get("allm") is True

    missing_required = []

    if required_hdmi and not hdmi21:
        missing_required.append("HDMI 2.1")
    if required_vrr and not vrr:
        missing_required.append("VRR")
    if required_allm and not allm:
        missing_required.append("ALLM")

    if missing_required:
        return signal(
            None,
            "Required gaming feature(s) are not verified: "
            + ", ".join(missing_required),
        )

    features = []

    if hdmi21:
        features.append("HDMI 2.1")
    if vrr:
        features.append("VRR")
    if allm:
        features.append("ALLM")
    if four_k_120:
        features.append("4K120")

    if not features:
        return signal(
            None,
            "Dedicated TV gaming features are not verified",
        )

    score = min(1.0, 0.55 + 0.12 * len(features))

    if required_hdmi or required_vrr or required_allm:
        score = max(score, 0.90)

    return signal(
        score,
        "Verified gaming features: " + ", ".join(features),
    )



def tv_picture_quality_signal(text: str) -> dict[str, Any]:
    lower = text.lower()
    score = 0.0
    reasons = []

    if "oled" in lower:
        score += 0.35
        reasons.append("OLED contrast/black-level capability")
    elif re.search(r"\b(?:mini[\s-]?led|miniled)\b", lower):
        score += 0.32
        reasons.append("Mini LED contrast capability")
    elif "qled" in lower:
        score += 0.22
        reasons.append("QLED colour-volume capability")

    if "dolby vision" in lower:
        score += 0.20
        reasons.append("Dolby Vision")

    if "hdr10+" in lower:
        score += 0.15
        reasons.append("HDR10+")

    if re.search(r"\b4k\b|ultra hd|uhd", lower):
        score += 0.15
        reasons.append("4K resolution")

    if any(
        phrase in lower
        for phrase in (
            "full array local dimming",
            "local dimming",
            "fald",
            "mini led",
        )
    ):
        score += 0.15
        reasons.append("local-dimming evidence")

    if not reasons:
        return signal(None, "No reliable TV picture-quality evidence found")

    return signal(min(score, 1.0), ", ".join(reasons))


def tv_brightness_signal(text: str) -> dict[str, Any]:
    lower = text.lower()

    brightness_values = [
        int(x)
        for x in re.findall(
            r"\b(\d{3,4})\s*(?:nit|nits)\b",
            lower,
            re.I,
        )
    ]

    if brightness_values:
        peak = max(brightness_values)

        if peak >= 1200:
            return signal(1.0, f"Very strong verified brightness: {peak} nits")
        if peak >= 800:
            return signal(0.90, f"Strong verified brightness: {peak} nits")
        if peak >= 500:
            return signal(0.72, f"Good verified brightness: {peak} nits")
        if peak >= 350:
            return signal(0.58, f"Moderate verified brightness: {peak} nits")

        return signal(0.40, f"Low verified brightness: {peak} nits")

    if any(
        phrase in lower
        for phrase in (
            "high brightness",
            "bright room",
            "anti reflection",
            "anti-reflection",
            "glare free",
            "glare-free",
        )
    ):
        return signal(0.72, "Brightness/glare-handling evidence detected")

    return signal(None, "No reliable TV brightness evidence found")


def tv_motion_signal(text: str) -> dict[str, Any]:
    lower = text.lower()

    rates = [
        int(x)
        for x in re.findall(
            r"\b(60|90|100|120|144|165)\s*hz\b",
            lower,
            re.I,
        )
    ]

    score = 0.0
    reasons = []

    if rates:
        rate = max(rates)

        if rate >= 120:
            score += 0.65
            reasons.append(f"{rate}Hz refresh rate")
        elif rate >= 100:
            score += 0.55
            reasons.append(f"{rate}Hz refresh rate")
        else:
            score += 0.35
            reasons.append(f"{rate}Hz refresh rate")

    if any(
        phrase in lower
        for phrase in (
            "motionflow",
            "motion pro",
            "motion xcelerator",
            "trumotion",
            "smooth motion",
        )
    ):
        score += 0.25
        reasons.append("motion-processing feature")

    if "vrr" in lower or "variable refresh rate" in lower:
        score += 0.15
        reasons.append("VRR")

    if not reasons:
        return signal(None, "No reliable TV motion evidence found")

    return signal(min(score, 1.0), ", ".join(reasons))


def tv_smart_signal(text: str) -> dict[str, Any]:
    lower = text.lower()

    platforms = (
        "google tv",
        "android tv",
        "webos",
        "tizen",
        "fire tv",
        "vidaa",
    )

    detected = [x for x in platforms if x in lower]

    if detected:
        return signal(
            0.90,
            "Verified smart-TV platform: " + ", ".join(detected),
        )

    if "smart tv" in lower:
        return signal(0.70, "Smart TV capability verified")

    return signal(None, "Smart-TV platform/capability is not verified")


def tv_sound_signal(text: str) -> dict[str, Any]:
    lower = text.lower()
    score = 0.0
    reasons = []

    if "dolby atmos" in lower:
        score += 0.45
        reasons.append("Dolby Atmos")

    watt_values = [
        int(x)
        for x in re.findall(
            r"\b(\d{2,3})\s*w(?:att)?\b",
            lower,
            re.I,
        )
    ]

    if watt_values:
        power = max(watt_values)

        if power >= 40:
            score += 0.45
        elif power >= 20:
            score += 0.30
        else:
            score += 0.18

        reasons.append(f"{power}W audio output")

    if any(
        phrase in lower
        for phrase in (
            "acoustic surface",
            "object tracking sound",
            "ai sound",
            "woofer",
            "subwoofer",
        )
    ):
        score += 0.20
        reasons.append("enhanced TV audio feature")

    if not reasons:
        return signal(None, "No reliable TV sound evidence found")

    return signal(min(score, 1.0), ", ".join(reasons))


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
            actual = numeric(
                r"\b(\d{1,3})\s*gb\s*\+\s*\d{2,4}\s*gb\b",
                text,
            )

        if actual is None:
            actual = numeric(
                r"\b(\d{1,3})\s*\+\s*\d{2,4}\s*gb\b",
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
            r"\b(\d{2,4})\s*gb\s*(?:storage|internal storage|rom|ssd)\b",
            text,
        )

        if actual is None:
            compact = re.search(
                r"\b\d{1,3}\s*(?:gb\s*)?\+\s*(\d{2,4})\s*gb\b",
                text,
                re.I,
            )
            if compact:
                actual = float(compact.group(1))

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
    "screen_size": lambda p, i, t: tv_screen_size_signal(p, i, t),
    "picture_quality": lambda p, i, t: tv_picture_quality_signal(t),
    "brightness": lambda p, i, t: tv_brightness_signal(t),
    "motion": lambda p, i, t: tv_motion_signal(t),
    "smart_tv": lambda p, i, t: tv_smart_signal(t),
    "sound": lambda p, i, t: tv_sound_signal(t),
    "panel_technology": lambda p, i, t: tv_panel_technology_signal(p, i, t),
    "refresh_rate": lambda p, i, t: tv_refresh_rate_signal(p, i, t),
    "gaming_features": lambda p, i, t: tv_gaming_features_signal(p, i, t),
    "battery": lambda p, i, t: category_battery_signal(p, i, t),
    "display": lambda p, i, t: category_display_signal(p, i, t),
    "ease_of_use": lambda p, i, t: ease_of_use_signal(t),
    "camera": lambda p, i, t: camera_signal(t),
    "performance": lambda p, i, t: performance_signal(t),
    "graphics": lambda p, i, t: graphics_signal(t),
    "ram": lambda p, i, t: ram_signal(t),
    "storage": lambda p, i, t: storage_signal(t),
    "software_support": lambda p, i, t: software_support_signal(t),
    "connectivity": lambda p, i, t: connectivity_signal(t),
    "anc": lambda p, i, t: anc_signal(t),
    "sound_quality": lambda p, i, t: sound_quality_signal(t),
    "call_quality": lambda p, i, t: call_quality_signal(t),
    "category_relevance": lambda p, i, t: category_relevance_signal(p, i, t),
    "query_relevance": lambda p, i, t: query_relevance_signal(p, i, t),
    "product_identity": lambda p, i, t: product_identity_signal(p, i, t),
    "portability": lambda p, i, t: portability_signal(t),
    "build_quality": lambda p, i, t: build_quality_signal(t),
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



