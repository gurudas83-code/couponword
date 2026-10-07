"""Render only reviewed, exact-variant mobile facts; never inferred offers."""
import html
import json
from urllib.parse import urlsplit
from product_evidence_store import (
    BUNDLED_EVIDENCE_PATH, extraction_is_cacheable, find_verified_evidence,
)
from retailer_product_registry import find_catalogued_mobile_id


def render_mobile_evidence(product, bundle_path=BUNDLED_EVIDENCE_PATH):
    if str(product.get("category", "")).casefold() != "mobiles":
        return ""
    title = str(product.get("title") or "")
    asin = str(product.get("asin") or "")
    brand = str(product.get("brand") or "")
    if not find_catalogued_mobile_id(retailer_product_id=asin,
                                    candidate_title=title, candidate_brand=brand):
        return ""
    try:
        bundle = json.loads(bundle_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return ""
    record = find_verified_evidence(asin=asin, brand=brand, title=title,
                                    store_data=bundle)
    if not record or not extraction_is_cacheable(record)[0]:
        return ""
    keys = ("ram", "storage", "internal_memory", "processor", "display", "size",
            "rear_camera", "primary_camera_rear_camera", "operating_system",
            "battery_and_charging", "type", "charger", "video_playback",
            "youtube_playback_time", "software_security_support", "warranty")
    rows = []
    for key in keys:
        fact = (record.get("specifications") or {}).get(key)
        if not isinstance(fact, dict) or not str(fact.get("value") or "").strip():
            continue
        url = str(fact.get("source_url") or record.get("official_url") or "")
        observed = str(fact.get("observed_at") or record.get("saved_at") or "")
        if urlsplit(url).scheme != "https" or not urlsplit(url).hostname or not observed:
            continue
        label = str(fact.get("label") or key.replace("_", " ").title())
        detail = html.escape(str(fact["value"]))
        conditions = str(fact.get("test_conditions") or "")
        if conditions:
            detail += "<br><small>" + html.escape(conditions) + "</small>"
        detail += ('<br><small><a href="' + html.escape(url, quote=True)
                   + '" rel="noopener noreferrer">Source</a> · Recorded '
                   + html.escape(observed[:10]) + '</small>')
        rows.append('<tr><th>' + html.escape(label) + '</th><td>' + detail + '</td></tr>')
    if not rows:
        return ""
    return ('<section class="verified-mobile-facts"><h2>Verified phone details</h2>'
            '<p>Facts for this physical RAM/storage variant. Manufacturer battery claims '
            'depend on test conditions; missing facts remain unverified.</p>'
            '<div class="spec-table-wrap"><table class="spec-table"><tbody>'
            + ''.join(rows) + '</tbody></table></div></section>')
