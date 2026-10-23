"""Issue 13 mapping/destination precondition; CTA semantics remain Issue 12-owned."""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlparse


MAPPING_VALID = "MAPPING_VALID"
AFFILIATE_DESTINATION_VALID = "AFFILIATE_DESTINATION_VALID"
DESTINATION_UNVERIFIED = "DESTINATION_UNVERIFIED"

HOSTS = {
    "amazon": ("amazon.in",),
    "flipkart": ("flipkart.com",),
    "croma": ("croma.com",),
}


def _host_allowed(retailer: str, hostname: str) -> bool:
    return any(hostname == allowed or hostname.endswith("." + allowed) for allowed in HOSTS.get(retailer, ()))


def _id_in_listing_url(retailer: str, listing_id: str, url: str) -> bool:
    parsed = urlparse(url)
    path_and_query = (parsed.path + "?" + parsed.query).casefold()
    token = listing_id.casefold()
    if retailer == "flipkart":
        return token in path_and_query or token in " ".join(parse_qs(parsed.query).get("pid", [] )).casefold()
    return token in path_and_query


def validate_mapping_destination(
    offer: dict[str, Any] | None,
    *,
    expected_retailer: str,
    expected_retailer_product_id: str,
) -> dict[str, Any]:
    """Validate mapping/destination identity only; never asserts price or stock."""
    if not isinstance(offer, dict):
        return {"valid": False, "status": DESTINATION_UNVERIFIED, "reason": "missing_mapping"}
    retailer = str(offer.get("retailer") or "").strip().lower()
    listing_id = str(offer.get("retailer_product_id") or "").strip()
    expected_id = str(expected_retailer_product_id or "").strip()
    url = str(offer.get("product_url") or "").strip()
    affiliate = str(offer.get("affiliate_url") or "").strip()
    if retailer != str(expected_retailer or "").strip().lower() or not listing_id or listing_id.casefold() != expected_id.casefold():
        return {"valid": False, "status": DESTINATION_UNVERIFIED, "reason": "retailer_or_listing_id_mismatch"}
    parsed = urlparse(url)
    if parsed.scheme != "https" or not _host_allowed(retailer, (parsed.hostname or "").lower()):
        return {"valid": False, "status": DESTINATION_UNVERIFIED, "reason": "unapproved_listing_host"}
    if "redirect" in parsed.path.casefold() or "url=" in parsed.query.casefold() or not _id_in_listing_url(retailer, listing_id, url):
        return {"valid": False, "status": DESTINATION_UNVERIFIED, "reason": "listing_id_not_bound_to_destination"}
    if affiliate:
        affiliate_parsed = urlparse(affiliate)
        if affiliate_parsed.scheme != "https" or not _host_allowed(retailer, (affiliate_parsed.hostname or "").lower()) or not _id_in_listing_url(retailer, listing_id, affiliate):
            return {"valid": False, "status": DESTINATION_UNVERIFIED, "reason": "affiliate_destination_mismatch"}
    return {"valid": True, "status": AFFILIATE_DESTINATION_VALID if affiliate else MAPPING_VALID, "reason": "retailer_listing_id_bound_to_destination"}
