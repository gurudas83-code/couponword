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
from urllib.parse import quote_plus, urlsplit
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
UPCOMING_ROUTE = "/phones/upcoming-india/"
PRICE_MAX_AGE = timedelta(hours=36)
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
        if row["evidence"] not in SOURCES and not (row["evidence"] == "India product page" and row.get("source", "").startswith("https://")):
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
    if not timedelta(0) <= now - checked <= PRICE_MAX_AGE:
        return checked, []
    prices = []
    for offer in observed.get("offers", []):
        price = offer.get("price")
        url = observation_url(store.lower(), offer)
        if type(price) in (int, float) and price > 0 and offer.get("availability") == "in_stock" and url:
            prices.append((price, url, offer["variant"]))
    return checked, sorted(prices)


def render_store(row, store, observed, now, name="", *, lowest=False, listed_price=None, reviewed_on=""):
    q = quote_plus(name)
    search_url = {
        "Amazon": amazon_search_url(name),
        "Flipkart": "https://www.flipkart.com/search?q=" + q,
        "Croma": row.get("croma_url") or "https://www.croma.com/searchB?q=" + q,
    }[store]
    checked, prices = displayable_prices(store, observed, now)
    classes = "phone-watch-store-link"
    label = store
    if not prices and not listed_price:
        classes += " phone-watch-price-cta"
        label = f"Check price on {store}"
    if not prices and listed_price:
        search_url = listed_price.get("listing", listed_price["source"])
    actions = (f'<a class="{classes}" rel="sponsored nofollow noopener" '
               f'href="{esc(search_url)}">{esc(label)} ↗</a>')
    if not prices and listed_price:
        amount = listed_price["price"]
        source = esc(listed_price["source"])
        variant = esc(listed_price["variant"])
        return (f'<li>{actions}<small class="phone-watch-croma-reference">'
                f'<a href="{source}">₹{amount:,} listed by Croma</a> · {variant}<br>'
                f'Reviewed {esc(reviewed_on)} · check stock for your PIN</small></li>')
    if not checked:
        details = "Open product listing" if store == "Croma" and row.get("croma_id") else f"Search on {store}"
    else:
        label = esc(checked.strftime("%d %b, %H:%M IST"))
        if not timedelta(0) <= now - checked <= PRICE_MAX_AGE:
            details = f"Refresh pending · last checked {label}"
        else:
            items = []
            for index, (price, url, variant) in enumerate(prices[:3]):
                price_class = "phone-watch-price"
                label_prefix = ""
                if lowest and index == 0:
                    price_class += " phone-watch-lowest"
                    label_prefix = '<span class="phone-watch-lowest-label">Lowest price found</span> '
                items.append(
                    f'{label_prefix}<a class="{price_class}" href="{esc(url)}">₹{price:,.0f}</a> '
                    f'<span>{esc(variant)}</span>'
                )
            details = ("<br>".join(items) if items else "No matching in-stock offer found") + f"<br>{label}"
    return f'<li>{actions}<small>{details}</small></li>'


def render_image(media, output, name, dialog_id):
    photo = media.get("photo") or media.get("reviewed_model_photo")
    path = photo["url"] if photo else media.get("representative_illustration")
    if not path or not (output / path.lstrip("/")).is_file():
        path = "/assets/phone-illustrations/representative-smartphone.webp"
        photo = None
    caption = "AI-generated illustration"
    alt = ""
    if photo:
        alt = name + " model photograph"
        caption = (f'<a href="{esc(photo["source"])}">{esc(photo["author"])}</a> · '
                   f'<a href="{esc(photo["license_url"])}">{esc(photo["license"])}</a> · resized')
    return (
        f'<figure class="phone-watch-image"><button type="button" class="phone-watch-image-button" '
        f'data-phone-dialog="{dialog_id}" aria-haspopup="dialog" aria-label="View {esc(name)} specifications">'
        f'<img src="{esc(path)}" alt="{esc(alt)}" loading="lazy" decoding="async"></button>'
        f'<figcaption>{caption}</figcaption></figure>'
    )


def render_research(research, review_date, has_api_price):
    if not research:
        return ""
    specs = " · ".join(esc(value) for value in research["specs"])
    details = (f'<p class="phone-watch-specs">{specs} · '
               f'<a href="{esc(research["spec_source"])}">Official specs</a></p>')
    if has_api_price:
        return details
    listing = esc(research["listing"])
    reference = research.get("reference")
    if reference:
        amount = reference["amount"]
        variant = esc(reference["variant"])
        store = esc(reference["store"])
        details += (f'<p class="phone-watch-reference">Store price reference · '
                    f'<a href="{listing}" rel="nofollow noopener">{store} ₹{amount:,}</a> · {variant}<br>'
                    f'Source reviewed {esc(review_date)}. Check current price and stock with the store.</p>')
    else:
        details += f'<p><a href="{listing}" rel="nofollow noopener">View product listing</a></p>'
    return details


SPEC_FIELDS = (
    ("india_variant_description", "India RAM / storage options", ""),
    ("chipset", "Processor", ""),
    ("display_type_description", "Display", ""),
    ("display_type", "Display", ""),
    ("display_size_description", "Display size", ""),
    ("display_inches", "Display size", " inches"),
    ("display_resolution_description", "Display resolution", ""),
    ("display_refresh_description", "Refresh rate", ""),
    ("display_refresh_max_hz", "Refresh rate", " Hz"),
    ("battery_mah_typical", "Battery", " mAh"),
    ("battery_capacity_description", "Battery", ""),
    ("charging_description", "Charging", ""),
    ("wired_charging_max_w", "Charging", " W"),
    ("rear_camera_system", "Rear camera", ""),
    ("rear_main_mp", "Main camera", " MP"),
    ("rear_ultrawide_mp", "Ultrawide camera", " MP"),
    ("front_camera_system", "Front camera", ""),
    ("front_mp", "Front camera", " MP"),
    ("launch_android", "Android version at launch", ""),
    ("os_upgrade_generations", "OS upgrades", " generations"),
    ("security_support_years", "Security support", " years"),
    ("security_update_policy", "Security update policy", ""),
    ("network_support", "Network", ""),
)


def render_spec_dialog(dialog_id, name, card, reviewed):
    fields = {label: (value, reviewed["source"]) for label, value in reviewed.get("fields", {}).items()}
    catalogue_specs = card["specifications"]
    for key, label, unit in SPEC_FIELDS:
        entry = catalogue_specs.get(key, {})
        if not entry.get("source_url") or not entry.get("value") or label in fields:
            continue
        if label in ("Battery", "Charging") and "Battery and charging" in fields:
            continue
        if label == "Battery" and str(entry["value"]).isdigit():
            unit = " mAh"
        fields[label] = (str(entry["value"]) + unit, entry["source_url"])
    specs = "".join(
        f'<div><dt>{esc(label)}</dt><dd>{esc(value)} '
        f'<a href="{esc(source)}" aria-label="{esc(label)} source">{esc(urlsplit(source).netloc.removeprefix("www."))}</a></dd></div>'
        for label, (value, source) in fields.items()
    )
    return (
        f'<dialog id="{dialog_id}" class="phone-watch-dialog" aria-labelledby="{dialog_id}-title">'
        '<form method="dialog"><button type="submit" autofocus>Close</button></form>'
        f'<h2 id="{dialog_id}-title">{esc(name)}</h2>'
        '<h3>Phone specifications</h3><dl>' + specs + '</dl>'
        '<h3>Prices by retailer and variant</h3>'
        '<p>Match RAM, storage and colour before comparing offers. '
        'Store references may require a PIN or a fresh stock check.</p>'
        '<div class="phone-watch-dialog-prices"></div></dialog>'
    )


def publish(output, snapshot_path=None):
    rows, cards = worklist()
    data = json.loads(Path(snapshot_path).read_text()) if snapshot_path else {}
    stores = {row["model_key"]: data.get("stores", {}).get(row["model_key"], {}) for row in rows}
    data = {**data, "stores": stores}
    now = datetime.now(IST)
    research = json.loads((ROOT / "data/india_phone_watch_research.json").read_text())
    spec_reviews = json.loads((ROOT / "data/india_phone_watch_specs.json").read_text())
    media = {}
    for filename in ("mobile_research_catalogue", "india_sales_eight_research", "india_recent_manufacturer_research"):
        feed = json.loads((output / "data" / f"{filename}.json").read_text())
        media.update({card["model_key"]: card for card in feed["model_cards"]})
    body = []
    in_stock_count = 0
    reference_count = 0
    for index, row in enumerate(rows, 1):
        key = row["model_key"]
        card = cards[key]
        dialog_id = f"phone-specs-{index}"
        name = card["model"] if card["model"].lower().startswith(card["brand"].lower() + " ") else f'{card["brand"]} {card["model"]}'
        evidence = row["evidence"]
        source_label = {
            "Q2 India sell-through Top 5": "Counterpoint · India top 5, Q2 2026",
            "Q3 model or portfolio mention": "Omdia · India shipments, Q3 2026",
            "Q3 Galaxy S26 series": "Omdia · India shipments, Q3 2026",
            "Counterpoint India sell-through tracked model": "Counterpoint · India smartphone tracker",
            "India product page": "Manufacturer’s India product page",
        }[evidence]
        source = f'<a href="{esc(row.get("source") or SOURCES[evidence])}">{esc(source_label)}</a>'
        observations = stores.get(key, {})
        price_candidates = []
        for store in PLATFORMS:
            _, prices = displayable_prices(store, observations.get(store, {}), now)
            if prices:
                price_candidates.append((prices[0][0], store))
        cheapest_store = min(price_candidates)[1] if price_candidates else None
        in_stock_count += bool(price_candidates)
        model_research = research["models"].get(key, {})
        croma_reference = research["croma_listed_prices"].get(key)
        if price_candidates:
            badge = '<span class="phone-watch-status has-price">Price and stock checked</span>'
        else:
            has_reference = bool(model_research.get("reference") or croma_reference)
            reference_count += has_reference
            label = "Store price reference" if has_reference else "Check price and stock"
            badge = f'<span class="phone-watch-status no-price">{label}</span>'
        model_details = render_research(model_research, research["reviewed_on"], bool(price_candidates))
        shop_links = "".join(
            render_store(
                row, store, observations.get(store, {}), now, name,
                lowest=store == cheapest_store,
                listed_price=croma_reference if store == "Croma" else None,
                reviewed_on=research["croma_reviewed_on"],
            )
            for store in PLATFORMS
        )
        body.append(
            '<article class="phone-watch-card">' + render_image(media.get(key, {}), output, name, dialog_id) +
            f'<div class="phone-watch-details">{badge}<h2><button type="button" data-phone-dialog="{dialog_id}" aria-haspopup="dialog">{esc(name)}</button></h2><p>{source}</p>'
            f'{model_details}<ul aria-label="{esc(name)} retailer options">{shop_links}</ul></div>' +
            render_spec_dialog(dialog_id, name, card, spec_reviews.get(key, {})) + '</article>'
        )
    check_count = len(body) - in_stock_count - reference_count
    updated_at = esc(now.strftime("%d %b %Y, %H:%M IST"))
    page = (
        '<h1>India Top 30 Phones · Price Watch</h1>'
        '<p>Compare prices for 30 phones in India and check offers on Amazon, Flipkart and Croma. '
        'Coupon World selects these models using India market reports and manufacturer product pages.</p>'
        f'<p><strong>All {len(body)} phones are listed below.</strong> At the {updated_at} page update, '
        f'{in_stock_count} had a retailer price with stock confirmed within the previous 36 hours for Delhi PIN 110001. '
        f'{reference_count} had a store price reference with stock to be confirmed, and {check_count} had '
        'retailer links to check the price.</p>'
        '<p>Prices vary by storage, colour, seller and delivery PIN. Confirm your variant, '
        'availability and total price at checkout.</p>'
    )
    page += f'<p><a href="{UPCOMING_ROUTE}">Upcoming phones and India launch checks</a></p>'
    page += '<div class="phone-watch-grid">' + "".join(body) + "</div>"
    target = output / ROUTE.lstrip("/")
    target.parent.mkdir(parents=True, exist_ok=True)
    html = doc("India Top 30 Phones · Price Watch", "Dated Amazon, Flipkart and Croma price observations for selected India phones.", ROUTE, page, {"@context": "https://schema.org", "@type": "WebPage"})
    target.write_text(html.replace("</head>", '<link rel="stylesheet" href="/assets/phone-watch-grid.css?v=spec-dialog-v1"><script defer src="/assets/phone-watch-dialog.js"></script>\n</head>'), encoding="utf-8")
    target = output / SNAPSHOT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8")

    reviewed = json.loads((ROOT / "data/india_phone_launch_review.json").read_text())
    if {row["model_key"] for row in reviewed} & {row["model_key"] for row in rows}:
        raise ValueError("Launch review exclusions cannot appear in the price watch")
    entries = "".join(
        f'<li><strong>{esc(row["name"])}</strong><br>{esc(row["note"])} '
        f'<a href="{esc(row["source"])}">Official source</a></li>'
        for row in reviewed
    )
    launch_page = (
        '<h1>Upcoming Phones in India</h1>'
        '<p>We list a phone as upcoming when its manufacturer confirms a future India release. '
        'Retailer prices are published after the India launch and a matching in-stock listing is verified.</p>'
        '<p>No confirmed upcoming models have been added to this watch yet.</p>'
        '<h2>India launch status checked</h2>'
        '<p>These models already launched in 2026 and have been removed from the price watch selection.</p>'
        f'<ul>{entries}</ul><p><a href="{ROUTE}">See the India Top 30 phone price watch</a></p>'
    )
    target = output / UPCOMING_ROUTE.lstrip("/") / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(doc("Upcoming Phones in India", "Manufacturer-confirmed India launch checks and price publication rules.",
                          UPCOMING_ROUTE, launch_page, {"@context": "https://schema.org", "@type": "WebPage"}), encoding="utf-8")


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
