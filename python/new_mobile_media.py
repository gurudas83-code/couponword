"""Original, model-labelled phone illustrations for unlicensed product-photo gaps.

This artwork is not a photograph or a manufacturer render. Never scrape or
embed merchant images without documented commercial reuse permission.
"""
from __future__ import annotations

import hashlib
import re
from html import escape
from pathlib import Path

ASSET_PREFIX = "/assets/new-mobile-art/"
COLORS = ("#2146ad", "#076776", "#a13b70", "#6948a8", "#8b5a27", "#326a48")
RIGHTS_NOTE = "Original generic device illustration; NOT a photo of the named model."


def slug(key: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-")
    if not value or len(value) > 100:
        raise ValueError("Invalid research model identity")
    return value


def url(key: str) -> str:
    return ASSET_PREFIX + slug(key) + ".svg"


def publish_art(destination: Path, cards: list[dict]) -> int:
    target = destination / ASSET_PREFIX.lstrip("/")
    target.mkdir(parents=True, exist_ok=True)
    names = set()
    for card in cards:
        key = str(card["model_key"])
        name = (str(card["brand"]) + " " + str(card["model"])).strip()
        file_name = slug(key) + ".svg"
        if file_name in names:
            raise ValueError("Duplicate artwork identity " + key)
        names.add(file_name)
        shade = COLORS[int(hashlib.sha256(key.encode()).hexdigest()[:8], 16) % len(COLORS)]
        # No copied UI, logos, trade dress, official camera-layout or model photograph.
        # A neutral, two-sided silhouette is designed from scratch.
        title = escape(name)
        subtitle = escape("ILLUSTRATION  •  NOT AN ACTUAL PRODUCT PHOTO")
        content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 540 430"
role="img" aria-labelledby="title desc">
<title id="title">{title} — generic phone illustration</title>
<desc id="desc">Original generic smartphone vector art, not a photograph or verified depiction of the exact model.</desc>
<rect width="540" height="430" rx="28" fill="#edf1f7"/>
<circle cx="452" cy="93" r="85" fill="{shade}" fill-opacity=".12"/>
<rect x="143" y="42" width="162" height="296" rx="26" fill="#1d2637"/>
<rect x="151" y="50" width="146" height="280" rx="21" fill="#e6ecf6"/>
<rect x="159" y="72" width="130" height="231" rx="12" fill="{shade}" fill-opacity=".92"/>
<rect x="202" y="58" width="45" height="5" rx="2" fill="#2d364a"/>
<rect x="263" y="73" width="118" height="250" rx="21" fill="#2d364a" stroke="#e8eef5" stroke-width="5"/>
<rect x="274" y="85" width="96" height="226" rx="15" fill="{shade}" fill-opacity=".72"/>
<circle cx="296" cy="112" r="14" fill="#e8eef5" fill-opacity=".9"/>
<circle cx="296" cy="145" r="14" fill="#e8eef5" fill-opacity=".9"/>
<rect x="24" y="351" width="492" height="2" fill="#ccd6e5"/>
<text x="270" y="376" font-family="sans-serif" font-size="21" font-weight="700" text-anchor="middle" fill="#202b42">{title}</text>
<text x="270" y="400" font-family="sans-serif" font-size="12" text-anchor="middle" fill="#536176">{subtitle}</text>
</svg>'''
        (target / file_name).write_text(content, encoding="utf-8")
    return len(names)
