#!/usr/bin/env python3

from __future__ import annotations

from datetime import datetime, timezone

from price_evidence import PriceEvidence
from retailer_contract import RetailerOffer


ALLOWED_AVAILABILITY = {
    "in_stock",
    "out_of_stock",
    "unknown",
}


def _parse_timestamp(value: str) -> datetime:
    text = str(value or "").strip()

    if not text:
        raise ValueError(
            "Evidence observation time required."
        )

    dt = datetime.fromisoformat(
        text.replace("Z", "+00:00")
    )

    if dt.tzinfo is None:
        raise ValueError(
            "Evidence timestamp must include timezone."
        )

    return dt.astimezone(timezone.utc)


def validate_price_evidence(
    offer: RetailerOffer,
    evidence: PriceEvidence,
) -> tuple[bool, list[str]]:

    errors: list[str] = []

    if evidence.product_id != offer.product_id:
        errors.append(
            "canonical_product_id_mismatch"
        )

    if (
        evidence.retailer.strip().lower()
        != offer.retailer.strip().lower()
    ):
        errors.append(
            "retailer_mismatch"
        )

    if (
        evidence.retailer_product_id
        != offer.retailer_product_id
    ):
        errors.append(
            "retailer_product_id_mismatch"
        )

    if evidence.availability not in ALLOWED_AVAILABILITY:
        errors.append(
            "invalid_availability"
        )

    if not evidence.source_url.strip():
        errors.append(
            "missing_source_url"
        )

    if not evidence.source_type.strip():
        errors.append(
            "missing_source_type"
        )

    if not 0.0 <= evidence.confidence <= 1.0:
        errors.append(
            "invalid_confidence"
        )

    try:
        observed = _parse_timestamp(
            evidence.observed_at
        )

        now = datetime.now(timezone.utc)

        if observed > now:
            errors.append(
                "future_observation_time"
            )

    except (TypeError, ValueError):
        errors.append(
            "invalid_observation_time"
        )

    return (
        len(errors) == 0,
        errors,
    )


if __name__ == "__main__":

    offer = RetailerOffer(
        retailer="amazon",
        product_id="cw-test-001",
        retailer_product_id="B0TEST123",
    )

    evidence = PriceEvidence(
        product_id="cw-test-001",
        retailer="amazon",
        retailer_product_id="B0TEST123",
        price=19999,
        mrp=22999,
        availability="in_stock",
        source_url="https://example.com/evidence",
        source_type="test_verified",
        confidence=0.95,
    )

    valid, errors = validate_price_evidence(
        offer,
        evidence,
    )

    print("\nCOUPON WORLD EVIDENCE VALIDATOR")
    print("Valid  :", valid)
    print("Errors :", errors)
