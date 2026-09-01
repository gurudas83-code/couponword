#!/usr/bin/env python3

from __future__ import annotations

from datetime import datetime, timezone


DEFAULT_MAX_AGE_HOURS = 24


def parse_timestamp(value: str) -> datetime | None:
    text = str(value or "").strip()

    if not text:
        return None

    try:
        dt = datetime.fromisoformat(
            text.replace("Z", "+00:00")
        )
    except ValueError:
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def evidence_age_hours(last_checked: str) -> float | None:
    checked = parse_timestamp(last_checked)

    if checked is None:
        return None

    now = datetime.now(timezone.utc)

    age = now - checked

    return max(
        0.0,
        age.total_seconds() / 3600,
    )


def is_offer_fresh(
    offer,
    max_age_hours: float = DEFAULT_MAX_AGE_HOURS,
) -> bool:

    age = evidence_age_hours(
        getattr(offer, "last_checked", "")
    )

    if age is None:
        return False

    return age <= max_age_hours


def freshness_status(
    offer,
    max_age_hours: float = DEFAULT_MAX_AGE_HOURS,
) -> str:

    age = evidence_age_hours(
        getattr(offer, "last_checked", "")
    )

    if age is None:
        return "unknown"

    if age <= max_age_hours:
        return "fresh"

    return "stale"
