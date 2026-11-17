#!/usr/bin/env python3

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from evidence_freshness import freshness_status
from multi_retailer_engine import compare_offers
from retailer_contract import RetailerOffer


ROOT = Path(__file__).resolve().parent.parent
PILOT_FILE = ROOT / "data" / "pilot_canonical_products.json"
OUTPUT_FILE = ROOT / "data" / "multi_retailer_public.json"


def to_offer(value) -> RetailerOffer:
    if isinstance(value, RetailerOffer):
        return value

    if isinstance(value, dict):
        return RetailerOffer(**value)

    raise TypeError(
        f"Unsupported offer type: {type(value).__name__}"
    )


def clean_public_product_url(url: str) -> str:
    """Return a direct retailer URL without affiliate tracking parameters."""
    url = str(url or "").strip()

    if not url:
        return ""

    try:
        parts = urlsplit(url)
    except ValueError:
        return url

    hostname = (parts.hostname or "").lower()

    if hostname == "amazon.in" or hostname.endswith(".amazon.in"):
        affiliate_keys = {
            "tag",
            "ascsubtag",
            "linkcode",
            "camp",
            "creative",
            "creativeasin",
        }

        query = [
            (key, value)
            for key, value in parse_qsl(
                parts.query,
                keep_blank_values=True,
            )
            if key.lower() not in affiliate_keys
        ]

        return urlunsplit(
            (
                parts.scheme,
                parts.netloc,
                parts.path,
                urlencode(query, doseq=True),
                parts.fragment,
            )
        )

    return url


def public_offer(value) -> dict:
    offer = to_offer(value)

    return {
        "retailer": offer.retailer,
        "retailer_product_id": offer.retailer_product_id,
        "price": offer.price,
        "mrp": offer.mrp,
        "currency": offer.currency,
        "availability": offer.availability,
        "freshness": freshness_status(offer),
        "product_url": clean_public_product_url(
            offer.product_url
        ),
        "affiliate_url": "",
        "last_checked": offer.last_checked,
        "source": offer.source,
        "confidence": offer.confidence,
    }


def observed_configuration(item, card, retailer):
    """Parse explicitly stated listing configuration; never infer physical RAM."""
    from quickcommerce_flipkart_adapter import _tokens
    title = str(item.get("name") or item.get("title") or "")
    quantity = str(item.get("quantity") or "")
    if re.search(r"renewed|refurbished|pre.?owned|open.?box|virtual|extended ram", title + " " + quantity, re.I):
        return None
    brand, model = _tokens(card["brand"]), _tokens(card["model"])
    if _tokens(item.get("brand", "")) != brand:
        return None
    if card.get("category") in {"tvs", "earbuds", "accessories"}:
        code = str(card.get("model_code") or "").strip()
        code_match = bool(code and re.search(r"(?<![a-z0-9])" + re.escape(code) + r"(?![a-z0-9])",
                                            title + " " + quantity, re.I))
        reviewed = (card.get("retailers") or {}).get(retailer) or {}
        pid = str(item.get("id") or item.get("retailer_product_id") or "")
        reviewed_url = str(reviewed.get("retailer_research_url") or "")
        linked = reviewed.get("exact_model_link_verified") is True and pid and pid in reviewed_url
        if not code_match and not linked:
            return None
        if card.get("category") == "tvs":
            if not code_match:
                return None
            return {"ram_gb": None, "storage_gb": None, "color": "Not applicable",
                    "variant": "Model " + code, "model_code": code}
        name = _tokens(title)
        expected = _tokens(card["model"])
        if name.startswith(brand + " "):
            name = name[len(brand) + 1:]
        if not name.startswith(expected + " ") and name != expected:
            return None
        if re.match(r"\s*(?:pro|plus|max|lite|ultra)\b", name[len(expected):]):
            return None
        color_match = re.search(r"\s-\s([a-zA-Z ]+)$", title)
        color = color_match.group(1).strip() if color_match else quantity.split(",")[0].strip()
        if not color or re.search(r"wireless|bluetooth|earbud", color, re.I):
            color = "Unspecified SKU " + pid
        return {"ram_gb": None, "storage_gb": None, "color": color,
                "variant": card["model"] + " · " + color, "model_code": code}
    memory = re.search(r"\([^()]*\b\d+\s*(?:GB|TB)\b[^()]*\)", title, re.I)
    if not memory:
        return None
    prefix = _tokens(title[:memory.start()])
    if prefix.startswith(brand + " "):
        prefix = prefix[len(brand) + 1:]
    if model.startswith(brand + " "):
        model = model[len(brand) + 1:]
    model = re.sub(r"\s+\d+\s*(?:gb|tb)$", "", model)
    prefix = re.sub(r" (?:ai smartphone|smartphone|mobile|mobile phone)$", "", prefix)
    # Optional 5G is allowed only when the catalogue itself documents it.
    network = (card.get("specifications") or {}).get("network_support") or {}
    documented_5g = "5g" in _tokens(network.get("value") if isinstance(network, dict) else network)
    if prefix != model and not (documented_5g and prefix == model + " 5g"):
        return None
    ram_matches = re.findall(r"\b(\d{1,3})\s*GB\s*RAM\b", title + " " + quantity, re.I)
    if len(set(ram_matches)) != 1 or re.search(r"\+|virtual|expand", quantity, re.I):
        return None
    ram = int(ram_matches[0])
    group = memory.group()[1:-1]
    capacities = re.findall(r"\b(\d{1,4})\s*(GB|TB)\b(?!\s*RAM)", group, re.I)
    values = {int(n) * (1024 if u.upper() == "TB" else 1) for n, u in capacities}
    if len(values) != 1:
        return None
    storage = values.pop()
    color = re.split(r",|\b\d+\s*(?:GB|TB)\b", group, maxsplit=1, flags=re.I)[0].strip()
    if not color or not ram or not storage:
        return None
    specified_storage = re.search(r"\s+(\d+)\s*(GB|TB)$", card["model"], re.I)
    if specified_storage and storage != int(specified_storage.group(1)) * (1024 if specified_storage.group(2).upper() == "TB" else 1):
        return None
    return {"ram_gb": ram, "storage_gb": storage, "color": color,
            "variant": f"{ram}GB/{storage}GB · {color}"}


def observation_url(retailer, item):
    """Only HTTPS exact retailer IDs; no redirectors, credentials or tracking."""
    pid = str(item.get("id") or item.get("retailer_product_id") or "")
    url = str(item.get("deeplink") or item.get("product_url") or "")
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.username or parts.password or parts.port not in {None, 443}:
        return None
    if retailer == "flipkart":
        if parts.hostname not in {"flipkart.com", "www.flipkart.com"} or not re.fullmatch(r"[A-Z0-9]{12,24}", pid):
            return None
        if "/p/" not in parts.path or dict(parse_qsl(parts.query)).get("pid") != pid:
            return None
        return f"https://www.flipkart.com/-/p/-?pid={pid}"
    if retailer == "amazon":
        if parts.hostname not in {"amazon.in", "www.amazon.in"} or not re.fullmatch(r"[A-Z0-9]{10}", pid):
            return None
        if not re.search(r"/(?:dp|gp/product)/" + re.escape(pid) + r"(?:/|$)", parts.path):
            return None
        return f"https://www.amazon.in/dp/{pid}"
    return None


def build_observation_snapshot(audit, cards, diagnostics=(), *, now=None):
    """Adapt paid API observations to the existing comparison engine.

    This is an attributed observation display, not the authorized-offer store.
    No canonical admissions, quality scores, affiliate links or product images.
    """
    from evidence_freshness import parse_timestamp
    from quickcommerce_flipkart_adapter import _positive_price, _tokens
    now = now or datetime.now(timezone.utc)
    card_map = {card["model_key"]: card for card in cards}
    inputs = []
    for row in audit.get("records", []):
        card = card_map.get(row.get("audit_id"))
        if card is None:
            continue
        for candidate in row.get("candidates", []):
            item = dict(candidate, brand=card["brand"])
            item["available"] = {"in_stock": True, "out_of_stock": False}.get(candidate.get("availability_observation"))
            item["price"] = candidate.get("price_observation")
            inputs.append((card, item, "flipkart", row.get("observed_at_utc"), row.get("pincode")))
    for row in diagnostics:
        if row.get("endpoint") != "search" or row.get("status") != "success":
            continue
        query = _tokens((row.get("params") or {}).get("q", ""))
        for card in cards:
            expected = _tokens(card["brand"] + " " + card["model"])
            code = _tokens(card.get("model_code", ""))
            matched_query = expected == query or row.get("model_key") == card["model_key"]
            if not matched_query and not (code and code in query and _tokens(card["brand"]) in query):
                continue
            for item in row.get("items", []):
                inputs.append((card, item, row["platform"].lower(), row.get("observed_at"), "110001"))
    groups = defaultdict(dict)
    histories = defaultdict(dict)
    rejected = 0
    for card, item, retailer, checked, pincode in inputs:
        try:
            config = observed_configuration(item, card, retailer)
            url = observation_url(retailer, item)
            timestamp = parse_timestamp(str(checked or ""))
            price = _positive_price(item.get("offer_price", item.get("price")))
            available = item.get("available")
            if (config is None or url is None or timestamp is None or timestamp > now
                    or type(available) is not bool or item.get("currency") != "INR"
                    or not re.fullmatch(r"[1-9]\d{5}", str(pincode or ""))
                    or (available and price is None)):
                rejected += 1
                continue
            identity = (card["model_key"], config["ram_gb"] or 0, config["storage_gb"] or 0, _tokens(config["color"]), str(pincode))
            offer = RetailerOffer(retailer=retailer, product_id=card["model_key"],
                retailer_product_id=str(item.get("id") or item.get("retailer_product_id")),
                brand=card["brand"], model=card["model"], variant=config["variant"],
                title=str(item.get("name") or item.get("title")),
                price=price if available else None, availability="in_stock" if available else "out_of_stock",
                product_url=url, source="quickcommerce_third_party_research", last_checked=checked,
                metadata={"evidence_observed_at": checked, "pincode": pincode,
                          "observation_display_only": True, "publication_authorized": False})
            history_key = (identity, retailer, offer.retailer_product_id)
            histories[history_key][checked] = {"observed_at": checked, "price": offer.price,
                                              "availability": offer.availability}
            previous = groups[identity].get(retailer)
            # One row per retailer/configuration, latest source observation wins.
            # Never compare multiple colors or multiple listings in one store as stores.
            if previous is None or checked > previous[0].last_checked:
                groups[identity][retailer] = (offer, config)
        except (TypeError, ValueError, KeyError):
            rejected += 1
    models = defaultdict(list)
    for identity, values in sorted(groups.items()):
        offers = [pair[0] for pair in values.values()]
        config = next(iter(values.values()))[1]
        result = compare_offers(offers)
        lowest = result["best_offer"]
        models[identity[0]].append({**config, "pincode": identity[4],
            "offers": [{"retailer": o.retailer, "retailer_product_id": o.retailer_product_id,
                        "title": o.title, "price": o.price, "currency": "INR",
                        "availability": o.availability, "observed_at": o.last_checked,
                        "product_url": o.product_url,
                        "history": [point for _, point in sorted(histories[(identity, o.retailer, o.retailer_product_id)].items())][-90:]} for o in offers],
            "lowest_observed_retailer": lowest["retailer"] if lowest else None,
            "comparison_scope": "same listed model, RAM, storage, color and pincode; checked stores only",
            "purchase_eligible": False})
    return {"schema_version": 1, "mode": "ATTRIBUTED_API_PRICE_OBSERVATIONS",
            "source": "QuickCommerce API", "source_type": "quickcommerce_third_party_research",
            "generated_at": now.isoformat(), "freshness_hours": 6,
            "disclosure": "API-observed listed prices and stock, not checkout confirmation. Bank/exchange offers and delivery charges are excluded. India firmware, warranty and seller condition require retailer confirmation. Prices do not affect quality ranking.",
            "counts": {"models": len(models), "configurations": sum(map(len, models.values())),
                       "retailer_rows": sum(len(c["offers"]) for v in models.values() for c in v),
                       "rejected_rows": rejected},
            "models": dict(models)}


def main():
    from stored_offer_comparison import load_product_offers
    pilot = json.loads(
        PILOT_FILE.read_text(encoding="utf-8-sig")
    )

    products = []

    for product in pilot.get("products", []):
        product_id = product["product_id"]

        offers = load_product_offers(product_id)
        result = compare_offers(offers)

        matched_offers = [
            public_offer(item)
            for item in result["identity_matched_offers"]
        ]

        best_offer = result.get("best_offer")

        products.append(
            {
                "product_id": product_id,
                "title": product["title"],
                "brand": product["brand"],
                "model": product["model"],
                "variant": product.get("variant", ""),
                "attributes": product.get("attributes", {}),
                "status": result["status"],
                "identity_matched_offer_count":
                    result["identity_matched_offer_count"],
                "comparable_offer_count":
                    result["comparable_offer_count"],
                "best_offer":
                    public_offer(best_offer)
                    if best_offer
                    else None,
                "price_gap": result["price_gap"],
                "offers": matched_offers,
            }
        )

    payload = {
        "version": 1,
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "products": products,
    }

    OUTPUT_FILE.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 72)
    print("MULTI-RETAILER PUBLIC DATA BUILT")
    print("=" * 72)
    print("Products :", len(products))
    print(
        "Generated:",
        payload["generated_at"],
    )
    print("Output   :", OUTPUT_FILE)

    for product in products:
        print()
        print(product["product_id"])
        print(
            "Offers     :",
            product["identity_matched_offer_count"],
        )
        print(
            "Comparable :",
            product["comparable_offer_count"],
        )

        best = product["best_offer"]

        if best:
            print(
                "Best       :",
                best["retailer"],
                best["price"],
            )
        else:
            print("Best       : None")


if __name__ == "__main__":
    main()
