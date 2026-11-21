"""Refresh the India 30-phone price watch using the existing research adapter."""

import argparse
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "python")]

from paid_api_live_bridge import PINCODE, catalogue
from quickcommerce_flipkart_adapter import QuickCommerceFlipkartConnector
from scripts.refresh_api_comparison import FIELDS
from build_multi_retailer_public import build_observation_snapshot, observation_url
from quickcommerce_flipkart_adapter import _tokens
from python.category_research_pages import doc, esc

ROUTE = "/seo/india-30-phone-price-watch.html"
SNAPSHOT_PATH = "data/india_daily_price_watch_snapshot.json"
PLATFORMS = ("Amazon", "Flipkart", "Croma")
IST = ZoneInfo("Asia/Kolkata")
DAILY_LIMIT = 60
SOURCES = {
    "Q2 India sell-through Top 5": "https://counterpointresearch.com/en/insights/top-5-smartphone-model-share-8-countries",
    "Q3 model or portfolio mention": "https://omdia.tech.informa.com/pr/2026/oct/indias-smartphone-shipments-fell-26percent-to-a-decade-low-third-quarter-level-despite-festive-season",
    "Q3 Galaxy S26 series": "https://omdia.tech.informa.com/pr/2026/oct/indias-smartphone-shipments-fell-26percent-to-a-decade-low-third-quarter-level-despite-festive-season",
    "Counterpoint India sell-through tracked model": "https://dir.counterpointresearch.com/smartphones/in",
}


def worklist():
    rows = json.loads((ROOT / "data/india_daily_price_watch.json").read_text())
    keys = {row["model_key"] for row in rows}
    cards = catalogue()
    if len(rows) != 30 or len(keys) != 30 or any(key not in cards or cards[key].get("category") for key in keys):
        raise ValueError("Expected 30 distinct catalogue smartphones")
    for row in rows:
        if row["evidence"] not in SOURCES:
            raise ValueError("Unknown market evidence")
        url = row.get("croma_url")
        if url:
            match = re.search(r"/p/(\d{5,9})$", url)
            if not match or not observation_url("croma", {"id": match[1], "deeplink": url}):
                raise ValueError("Croma needs an exact product URL")
            row["croma_id"] = match[1]
    return rows, cards


def planned_calls(rows, day):
    calls = []
    for index, row in enumerate(rows):
        platforms = list(PLATFORMS[:2])
        if row.get("croma_id"):
            platforms = list(PLATFORMS)
            platforms.pop((day.toordinal() + index) % len(PLATFORMS))
        calls.extend((row, platform) for platform in platforms)
    if len(calls) != DAILY_LIMIT:
        raise ValueError("Unexpected daily API call budget")
    return calls


def read_previous():
    try:
        with urlopen("https://coupon-world.in/" + SNAPSHOT_PATH, timeout=10) as response:
            data = json.loads(response.read(2_000_000))
        if not isinstance(data, dict) or not isinstance(data.get("stores"), dict):
            return {}
        return data
    except (URLError, TimeoutError, ValueError):
        return {}


def collect(previous, rows, cards, client, now, pause=time.sleep):
    day = now.astimezone(IST).date()
    stores = previous.get("stores", {})
    previous = dict(previous, stores={key: dict(value) for key, value in stores.items() if isinstance(value, dict)})
    if previous.get("attempted_on") == str(day):
        return previous
    previous.update(attempted_on=str(day), calls_attempted=0, run_status="completed")
    previous["stores"] = {row["model_key"]: previous["stores"].get(row["model_key"], {}) for row in rows}
    for row, platform in planned_calls(rows, day):
        key = row["model_key"]
        card = cards[key]
        brand, model = card["brand"], card["model"]
        query = model if model.lower().startswith(brand.lower() + " ") else brand + " " + model
        endpoint = "item" if platform == "Croma" else "search"
        params = {"item_id": row["croma_id"]} if endpoint == "item" else {"q": query}
        previous["calls_attempted"] += 1
        try:
            payload, checked = client.fetch_observation(endpoint, platform, **params)
            body = payload.get("data") or {}
            field = "items" if endpoint == "item" else "products"
            items = body.get(field)
            if payload.get("status") != "success" or body.get("platform", platform) != platform or not isinstance(items, list):
                raise ValueError("Unexpected provider response")
        except (URLError, TimeoutError, ValueError, OSError) as error:
            previous["stores"][key].setdefault(platform, {})["last_attempt"] = "provider_error"
            previous["run_status"] = "partial"
            if isinstance(error, HTTPError) and error.code in (401, 403, 429):
                break
            pause(1)
            continue
        if platform == "Croma":
            normalized = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                pid = str(item.get("id") or item.get("item_id") or "")
                title = str(item.get("name") or "")
                reference = row["croma_title"]
                if pid != row["croma_id"] or _tokens(title).replace(" ", "") != _tokens(reference).replace(" ", ""):
                    continue
                # Croma displays RAM, storage, then color. Use the reviewed exact
                # ID and matching title to rearrange those fields for the parser.
                match = re.fullmatch(r".+\((?:(\d+GB RAM), )?(\d+(?:GB|TB)), ([^)]+)\)", reference, re.I)
                if not match:
                    continue
                ram, storage, color = match.groups()
                quantity = ram or ""
                item = dict(item, name=f"{query} ({color}, {storage}) {quantity}",
                            quantity=quantity, brand=brand)
                normalized.append(item)
            items = normalized
        snapshots = build_observation_snapshot({}, [card], [{
            "model_key": key, "endpoint": endpoint, "platform": platform, "params": params,
            "status": "success", "observed_at": checked,
            "items": [{k: v for k, v in item.items() if k in FIELDS} for item in items if isinstance(item, dict)]
        }])
        offers = []
        for config in snapshots["models"].get(key, []):
            offers.extend(dict(offer, variant=config["variant"]) for offer in config["offers"])
        previous["stores"][key][platform] = {"checked_at": checked, "last_attempt": "checked", "offers": offers[:12]}
        pause(1)
    return previous


def amazon_search_url(name):
    return "https://www.amazon.in/s?k=" + quote_plus(name) + "&tag=guru07cc-21"


def displayable_prices(store, observed, now):
    try:
        checked = datetime.fromisoformat(observed.get("checked_at")).astimezone(IST)
    except (TypeError, ValueError):
        return None, []
    if not timedelta(0) <= now - checked <= timedelta(hours=72):
        return checked, []
    prices = []
    for offer in observed.get("offers", []):
        price = offer.get("price")
        url = observation_url(store.lower(), offer)
        if type(price) in (int, float) and price > 0 and offer.get("availability") == "in_stock" and url:
            prices.append((price, url, offer["variant"]))
    return checked, sorted(prices)


def render_store(row, store, observed, now, name="", *, lowest=False):
    q = quote_plus(name)
    search_url = {
        "Amazon": amazon_search_url(name),
        "Flipkart": "https://www.flipkart.com/search?q=" + q,
        "Croma": row.get("croma_url") or "https://www.croma.com/searchB?q=" + q,
    }[store]
    actions = f'<a class="phone-watch-store-link" rel="sponsored nofollow noopener" href="{esc(search_url)}">{esc(store)} ↗</a>'
    checked, prices = displayable_prices(store, observed, now)
    if not checked:
        details = "Exact listing" if store == "Croma" and row.get("croma_id") else "Search listing"
    else:
        label = esc(checked.strftime("%d %b, %H:%M IST"))
        if not timedelta(0) <= now - checked <= timedelta(hours=72):
            details = f"Refresh pending · {label}"
        else:
            items = []
            for index, (price, url, variant) in enumerate(prices[:3]):
                price_class = "phone-watch-price"
                label_prefix = ""
                if lowest and index == 0:
                    price_class += " phone-watch-lowest"
                    label_prefix = '<span class="phone-watch-lowest-label">Lowest observed</span> '
                items.append(
                    f'{label_prefix}<a class="{price_class}" href="{esc(url)}">₹{price:,.0f}</a> '
                    f'<span>{esc(variant)}</span>'
                )
            details = ("<br>".join(items) if items else "No exact in-stock price returned") + f"<br>{label}"
    return f'<li>{actions}<small>{details}</small></li>'


def render_image(media, output, name):
    photo = media.get("photo") or media.get("reviewed_model_photo")
    path = photo["url"] if photo else media.get("representative_illustration")
    if not path or not (output / path.lstrip("/")).is_file():
        path = "/assets/phone-illustrations/representative-smartphone.webp"
        photo = None
    caption = "AI illustration · not the actual phone"
    alt = ""
    if photo:
        alt = name + " model photograph"
        caption = (f'<a href="{esc(photo["source"])}">{esc(photo["author"])}</a> · '
                   f'<a href="{esc(photo["license_url"])}">{esc(photo["license"])}</a> · resized')
    return (f'<figure class="phone-watch-image"><img src="{esc(path)}" alt="{esc(alt)}" '
            f'loading="lazy" decoding="async"><figcaption>{caption}</figcaption></figure>')


def publish(output, snapshot_path=None):
    rows, cards = worklist()
    data = json.loads(Path(snapshot_path).read_text()) if snapshot_path else {}
    stores = data.get("stores", {})
    now = datetime.now(IST)
    media = {}
    for filename in ("mobile_research_catalogue", "india_sales_eight_research", "india_recent_manufacturer_research"):
        feed = json.loads((output / "data" / f"{filename}.json").read_text())
        media.update({card["model_key"]: card for card in feed["model_cards"]})
    body = []
    for row in rows:
        key = row["model_key"]
        card = cards[key]
        name = card["model"] if card["model"].lower().startswith(card["brand"].lower() + " ") else f'{card["brand"]} {card["model"]}'
        evidence = row["evidence"]
        source = f'<a href="{esc(SOURCES[evidence])}">{esc(evidence)}</a>'
        observations = stores.get(key, {})
        price_candidates = []
        for store in PLATFORMS:
            _, prices = displayable_prices(store, observations.get(store, {}), now)
            if prices:
                price_candidates.append((prices[0][0], store))
        cheapest_store = min(price_candidates)[1] if price_candidates else None
        badge = ('<span class="phone-watch-status has-price">Price found</span>' if cheapest_store else
                 '<span class="phone-watch-status no-price">Price not verified</span>')
        fallback = "" if cheapest_store else (
            f'<a class="phone-watch-price-cta" rel="sponsored nofollow noopener" href="{esc(amazon_search_url(name))}">'
            'Check today’s price on Amazon ↗</a>'
            '<small>Choose the matching variant and check the final price in your cart.</small>'
        )
        shop_links = "".join(
            render_store(row, store, observations.get(store, {}), now, name, lowest=store == cheapest_store)
            for store in PLATFORMS
        )
        body.append(
            '<article class="phone-watch-card">' + render_image(media.get(key, {}), output, name) +
            f'<div class="phone-watch-details">{badge}<h2>{esc(name)}</h2><p>{source}</p>{fallback}' +
            f'<ul aria-label="{esc(name)} retailer options">{shop_links}</ul></div></article>'
        )
    status = f'Latest collection attempt {esc(data["attempted_on"])} · {int(data["calls_attempted"])} API requests.' if data.get("attempted_on") else "First API collection pending."
    page = """<h1>India Top 30 Phones</h1>
    <p>Five models are from the published Q2 India sales Top 5. The others are selected from shipment reports and sell-through tracking. The selection is a price watchlist rather than a national sales ranking.</p>
    <p>Prices are dated API observations for Delhi PIN 110001. Retailer checks rotate within 60 requests per day. The lowest observed price can be for a different variant.</p>"""
    page += f'<p>{status}</p><div class="phone-watch-grid">' + "".join(body) + "</div>"
    target = output / ROUTE.lstrip("/")
    target.parent.mkdir(parents=True, exist_ok=True)
    html = doc("India Top 30 Phones", "Dated Amazon, Flipkart and Croma price observations for selected India phones.", ROUTE, page, {"@context": "https://schema.org", "@type": "WebPage"})
    target.write_text(html.replace("</head>", '<link rel="stylesheet" href="/assets/phone-watch-grid.css?v=light-price-cta-v1">\n</head>'), encoding="utf-8")
    target = output / SNAPSHOT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--collect", action="store_true")
    args = parser.parse_args()
    rows, cards = worklist()
    candidates = [read_previous()]
    for path in (args.output, ROOT / "data/india_daily_price_watch_seed.json"):
        try:
            saved = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(saved, dict) and isinstance(saved.get("stores"), dict):
                candidates.append(saved)
        except (OSError, ValueError):
            continue
    previous = max(candidates, key=lambda snapshot: snapshot.get("attempted_on", ""))
    if args.collect:
        if os.environ.get("QUICKCOMMERCE_API_KEY"):
            previous = collect(previous, rows, cards, QuickCommerceFlipkartConnector(pincode=PINCODE), datetime.now(IST))
        else:
            previous["run_status"] = "missing_provider_secret"
        print(json.dumps({key: previous.get(key) for key in ("attempted_on", "calls_attempted", "run_status")}))
    args.output.write_text(json.dumps(previous, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
