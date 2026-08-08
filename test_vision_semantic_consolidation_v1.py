#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, "python")

import official_spec_extractor as ose

PRODUCT_ID = "11"

data = json.load(
    open("data/official_specs.json", encoding="utf-8")
)

product = next(
    x for x in data["products"]
    if str(x.get("product_id")) == PRODUCT_ID
)

test = copy.deepcopy(product)

combined = {
    "provider": "gemini",
    "results": [],
}

for path in sorted(
    Path("data/vision_results").glob(
        f"product_{PRODUCT_ID}_media_*.json"
    )
):
    payload = json.loads(
        path.read_text(encoding="utf-8")
    )
    combined["results"].extend(
        payload.get("results", [])
    )

test = ose.import_vision_result_payload(
    test,
    combined,
)

test = ose.validate_vision_claims(test)

media = test.get("media_evidence", {})

claims = []

for item in media.get("vision_evidence_queue", []):
    evidence_id = str(item.get("evidence_id") or "")

    for claim in item.get("claims", []):
        if claim.get("evidence_status") != "review_ready":
            continue

        row = dict(claim)
        row["evidence_id"] = evidence_id
        claims.append(row)


def norm(value):
    text = str(value or "").lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def canonical_key(claim):
    ctype = norm(claim.get("claim_type"))
    text = norm(claim.get("english_text"))
    value = norm(claim.get("value"))
    unit = norm(claim.get("unit"))

    # Strong cross-image canonical groups.
    if (
        "55" in value
        and unit == "db"
        and "noise" in text
    ):
        return "noise_cancellation.max_reduction"

    if (
        value == "58"
        and unit in {"hour", "hours", "hr", "hrs"}
        and (
            "battery" in ctype
            or "playback" in text
        )
    ):
        return "battery.total_playback"

    if (
        "11+6" in value.replace(" ", "")
        and unit == "mm"
    ):
        return "audio.driver_configuration"

    if (
        "ip55" in value
        or "ip55" in text
    ):
        return "durability.ip_rating"

    if (
        "bluetooth version" in text
        and value == "5.4"
    ):
        return "bluetooth.version"

    if "bluetooth codec" in text:
        return "bluetooth.codecs"

    if "effective bluetooth distance" in text:
        return "bluetooth.effective_distance"

    if ctype == "color_variant":
        return "product.color_variants"

    if ctype in {
        "microphone_count",
        "audio_hardware",
    } and (
        "microphone" in text
        or "mic" in text
    ):
        # Keep microphone count evidence together.
        return "audio.microphone_count"

    if ctype == "ai_translation":
        return "ai.live_translation_languages"

    if ctype == "latency":
        return "gaming.low_latency"

    if ctype == "battery_capacity":
        return "battery.capacity"

    if ctype == "charging_time":
        return "battery.charging_time"

    if ctype in {
        "hardware_interface",
    } and "type-c" in text:
        return "charging.port"

    if ctype == "multi_device_connectivity":
        return "connectivity.multi_device"

    if ctype == "audio_codec":
        return "audio.hires_codec_support"

    if ctype == "smart_features":
        return "ai.assistant"

    if ctype == "audio_technology":
        return "audio.nextbass_algorithm"

    if ctype == "audio_enhancement":
        return "audio.low_frequency_enhancement"

    if ctype == "noise_cancellation_modes":
        return "noise_cancellation.modes"

    if ctype == "microphone_type":
        return "audio.microphone_architecture"

    if ctype == "noise_cancellation":
        return "noise_cancellation.adaptive"

    if ctype == "tweeter_magnet":
        return "audio.tweeter_magnet"

    if ctype == "diaphragm_purity":
        return "audio.diaphragm_purity"

    if ctype == "product_identity":
        return "product.identity"

    return f"other.{ctype or 'unknown'}"


groups = defaultdict(list)

for claim in claims:
    groups[canonical_key(claim)].append(claim)

print("REVIEW READY CLAIMS:", len(claims))
print("CANONICAL GROUPS:", len(groups))
print()

for key in sorted(groups):
    rows = groups[key]

    print("=" * 100)
    print("CANONICAL:", key)
    print("EVIDENCE COUNT:", len(rows))

    for row in rows:
        print(
            "-",
            row.get("evidence_id"),
            "|",
            row.get("english_text"),
            "|",
            row.get("value"),
            row.get("unit"),
            "| CONF:",
            row.get("confidence"),
        )

print()
print("DRY RUN COMPLETE")
