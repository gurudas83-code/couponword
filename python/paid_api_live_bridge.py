"""Bounded, server-side QuickCommerce price observations for the existing website.

Third-party research only: NEVER feeds the authorized retailer offer store,
ranking, product admissions, or purchase eligibility. No API credentials are
ever included in HTTP responses or browser code.

Calls occur only when a shopper opens the price panel. The first exact,
in-stock, positive-price observation wins: Flipkart -> Amazon -> Croma (only
with an independently reviewed exact Croma item ID). Price is for a stated
listing configuration and Delhi test pincode, not an all-India quote.
"""
from __future__ import annotations

import json
import os
import re
import threading
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from build_multi_retailer_public import (
    build_observation_snapshot, observed_configuration, observation_url,
)
from quickcommerce_flipkart_adapter import (
    QuickCommerceFlipkartConnector, _positive_price, _tokens,
)

ROOT = Path(__file__).resolve().parents[1]
PINCODE = "110001"
# Process-local protection only. Multi-instance / restart-wide hard budgets
# require a shared, persistent counter at the provider or datastore.
_LOCK = threading.RLock()
_CACHE: dict[tuple[str, str], tuple[datetime, dict]] = {}
_SPEND: dict[str, int] = {}


@lru_cache(maxsize=1)
def catalogue() -> dict[str, dict]:
    phones = json.loads(
        (ROOT / "data" / "mobile_research_catalogue.json").read_text(encoding="utf-8-sig")
    )["model_cards"]
    extras = json.loads(
        (ROOT / "data" / "india_tv_earbuds_40_catalogue.json").read_text(encoding="utf-8-sig")
    )["records"]
    cards = phones + [dict(row, model_key=row["id"]) for row in extras]
    return {row["model_key"]: row for row in cards}


def _max_calls() -> int:
    try:
        return min(100, max(0, int(os.environ.get("CW_QUICKCOMMERCE_DAILY_CAP", "20"))))
    except ValueError:
        return 0


def _paid_fetch(client, endpoint: str, platform: str, query_value: str, now: datetime):
    """Cache provider responses by model and platform before any new billed call."""
    key = (platform, endpoint + ":" + query_value)
    day = now.date().isoformat()
    with _LOCK:
        cached = _CACHE.get(key)
        if cached and cached[0] > now:
            return cached[1], "cached"
        cap = _max_calls()
        if cap == 0 or _SPEND.get(day, 0) >= cap:
            return None, "budget_exhausted"
        # Reserve before the network operation, including failed attempts.
        _SPEND[day] = _SPEND.get(day, 0) + 1
    try:
        arguments = {"q": query_value} if endpoint == "search" else {"item_id": query_value}
        payload, observed_at = client.fetch_observation(endpoint, platform, **arguments)
        data = payload.get("data") if isinstance(payload, dict) else None
        if (not isinstance(data, dict) or payload.get("status") != "success"
                or (endpoint == "search" and data.get("platform") != platform)
                or not isinstance(data.get("products" if endpoint == "search" else "items"), list)):
            return None, "provider_error"
        result = {"payload": payload, "observed_at": observed_at or now.isoformat()}
        # Search by the same model can be reused for other RAM/storage selections.
        with _LOCK:
            _CACHE[key] = (now + timedelta(hours=6), result)
        return result, "live"
    except Exception:
        # Never return private transport errors or secrets to the browser.
        return None, "provider_error"


def _croma_id(card: dict) -> str | None:
    reviewed = (card.get("retailers") or {}).get("croma") or {}
    if reviewed.get("exact_model_link_verified") is not True:
        return None
    url = str(reviewed.get("retailer_research_url") or "")
    parts = urlsplit(url)
    matched = re.search(r"/p/(\d{5,9})/?$", parts.path)
    if (parts.scheme == "https" and parts.hostname in {"croma.com", "www.croma.com"}
            and matched):
        return matched.group(1)
    return None


def _wanted_variant(config: dict, *, ram_gb=None, storage_gb=None, color=None) -> bool:
    if ram_gb is not None and config.get("ram_gb") != ram_gb:
        return False
    if storage_gb is not None and config.get("storage_gb") != storage_gb:
        return False
    if color and _tokens(config.get("color")) != _tokens(color):
        return False
    return True


def _eligible_item(item, card, platform, *, ram_gb=None, storage_gb=None, color=None):
    if not isinstance(item, dict):
        return None
    retailer = platform.lower()
    entry = item
    if retailer == "croma" and isinstance(item.get("available"), str):
        entry = dict(item, available={"true": True, "false": False}.get(item["available"].lower()))
    if not entry.get("brand") and retailer == "croma" and _tokens(entry.get("name")).startswith(_tokens(card["brand"]) + " "):
        entry = dict(entry, brand=card["brand"])
    config = observed_configuration(entry, card, retailer)
    if not config or not _wanted_variant(config, ram_gb=ram_gb, storage_gb=storage_gb, color=color):
        return None
    if (observation_url(retailer, entry) is None
            or type(entry.get("available")) is not bool
            or entry["available"] is not True
            or entry.get("currency") != "INR"
            or _positive_price(entry.get("offer_price", entry.get("price"))) is None):
        return None
    return entry


def observe_card(card: dict, *, ram_gb=None, storage_gb=None, color=None,
                 client=None, now=None) -> dict:
    """Test-injectable, exact-model sequential provider lookup."""
    now = now or datetime.now(timezone.utc)
    if client is None and not os.environ.get("QUICKCOMMERCE_API_KEY"):
        return {"status": "not_configured", "source": "QuickCommerce API"}
    client = client or QuickCommerceFlipkartConnector(pincode=PINCODE)
    query = (card["model"] if card["model"].lower().startswith(card["brand"].lower() + " ")
             else card["brand"] + " " + card["model"])
    attempts = []
    steps = [("Flipkart", "search", query), ("Amazon", "search", query)]
    croma_id = _croma_id(card)
    if croma_id:
        steps.append(("Croma", "item", croma_id))
    for platform, endpoint, argument in steps:
        fetched, fetch_status = _paid_fetch(client, endpoint, platform, argument, now)
        attempts.append({"retailer": platform.lower(), "status": fetch_status})
        if fetch_status == "budget_exhausted":
            return {"status": "budget_exhausted", "attempts": attempts}
        if fetched is None:
            continue
        key = "products" if endpoint == "search" else "items"
        candidates = fetched["payload"]["data"][key]
        for candidate in candidates:
            entry = _eligible_item(candidate, card, platform, ram_gb=ram_gb,
                                   storage_gb=storage_gb, color=color)
            if entry is None:
                continue
            checked = fetched["observed_at"]
            row = {"endpoint": endpoint, "platform": platform, "status": "success",
                   "model_key": card["model_key"],
                   "params": {"q": query, "item_id": argument},
                   "observed_at": checked, "items": [entry]}
            snapshot = build_observation_snapshot({}, [card], [row], now=now)
            configurations = snapshot["models"].get(card["model_key"]) or []
            if configurations and configurations[0].get("offers"):
                return {"status": "ok", "source": "QuickCommerce API",
                        "source_type": "quickcommerce_third_party_research",
                        "publication_authorized": False,
                        "purchase_eligible": False,
                        "pincode": PINCODE, "model_key": card["model_key"],
                        "configuration": configurations[0],
                        "attempts": attempts}
    return {"status": "no_exact_in_stock_observation", "attempts": attempts,
            "source": "QuickCommerce API", "pincode": PINCODE}


def observe_model(model_key: str, *, ram_gb=None, storage_gb=None, color=None) -> dict:
    card = catalogue().get(model_key)
    if not card:
        return {"status": "unknown_model"}
    return observe_card(card, ram_gb=ram_gb, storage_gb=storage_gb, color=color)
