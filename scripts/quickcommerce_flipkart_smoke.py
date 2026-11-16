#!/usr/bin/env python3
"""Opt-in *one-call* QuickCommerce Flipkart smoke test: research observation only.

No site/build/offer-store writes, no affiliate links, no automatic refresh.
Do not pass secrets as CLI arguments. Place QUICKCOMMERCE_API_KEY in a private
environment variable. Only --live initiates a billed API request.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from canonical_product import CanonicalProduct
from quickcommerce_flipkart_adapter import QuickCommerceFlipkartConnector, dry_run

FIXTURE = ROOT / "tests" / "fixtures" / "quickcommerce_flipkart_a56_search.json"


def sample_product():
    return CanonicalProduct(
        product_id="cw-api-dryrun-a56",
        title="Samsung Galaxy A56 5G",
        brand="Samsung",
        model="Galaxy A56 5G",
        variant="8GB/128GB",
        category="Mobiles",
        identifiers={},
        attributes={"color": "Light Violet"},
        source_product_id="fixture",
        confidence=0.9,
    )


def run(live: bool = False):
    product = sample_product()
    if not live:
        return dry_run(FIXTURE, product)
    # Exactly one GET /v1/search call. API errors terminate without retries.
    offer = QuickCommerceFlipkartConnector().get_offer(product)
    if offer is None:
        return {
            "status": "NO_EXACT_MATCH",
            "publishable": False,
            "provider": "QuickCommerce",
            "retailer": "Flipkart",
        }
    return {
        "status": "RESEARCH_ONLY",
        "provider": "QuickCommerce",
        "retailer": "Flipkart",
        "product_id": offer.product_id,
        "retailer_product_id": offer.retailer_product_id,
        "price_observation": offer.price,
        "mrp_observation": offer.mrp,
        "availability_observation": offer.availability,
        "observed_at_utc": offer.last_checked,
        "source": offer.source,
        "publishable": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="Spend one API call. Requires private QUICKCOMMERCE_API_KEY.")
    args = parser.parse_args()
    try:
        print(json.dumps(run(live=args.live), ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as error:
        # Never print upstream HTTP errors, request headers, or secrets.
        # The provider/API key itself must remain private.
        print(json.dumps({
            "status": "RESEARCH_CALL_FAILED",
            "error_class": type(error).__name__,
            "http_status": getattr(error, "code", None) if type(error).__name__ == "HTTPError" else None,
            "publishable": False
        }))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
