#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class EvidenceValue:
    value: Any = None
    source: str | None = None
    source_url: str | None = None
    confidence: str = "unknown"
    verified: bool = False


@dataclass
class MobileProductDNA:
    product_id: str
    canonical_product_id: str | None = None

    brand: EvidenceValue = field(default_factory=EvidenceValue)
    model: EvidenceValue = field(default_factory=EvidenceValue)

    ram_gb: EvidenceValue = field(default_factory=EvidenceValue)
    storage_gb: EvidenceValue = field(default_factory=EvidenceValue)

    display_size_inch: EvidenceValue = field(default_factory=EvidenceValue)
    display_type: EvidenceValue = field(default_factory=EvidenceValue)
    refresh_rate_hz: EvidenceValue = field(default_factory=EvidenceValue)

    chipset: EvidenceValue = field(default_factory=EvidenceValue)

    main_camera_mp: EvidenceValue = field(default_factory=EvidenceValue)
    ultrawide_camera_mp: EvidenceValue = field(default_factory=EvidenceValue)
    selfie_camera_mp: EvidenceValue = field(default_factory=EvidenceValue)

    battery_mah: EvidenceValue = field(default_factory=EvidenceValue)
    charging_w: EvidenceValue = field(default_factory=EvidenceValue)

    operating_system: EvidenceValue = field(default_factory=EvidenceValue)
    update_policy: EvidenceValue = field(default_factory=EvidenceValue)

    supports_5g: EvidenceValue = field(default_factory=EvidenceValue)

    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_mobile_dna(dna: MobileProductDNA) -> list[str]:
    errors: list[str] = []

    if not str(dna.product_id).strip():
        errors.append("product_id is required")

    allowed_confidence = {"unknown", "low", "medium", "high"}

    for name, item in dna.__dict__.items():
        if isinstance(item, EvidenceValue):
            if item.confidence not in allowed_confidence:
                errors.append(
                    f"{name}: invalid confidence {item.confidence!r}"
                )

            if item.verified and not item.source:
                errors.append(
                    f"{name}: verified value requires a source"
                )

    return errors


if __name__ == "__main__":
    sample = MobileProductDNA(product_id="test-mobile")

    errors = validate_mobile_dna(sample)

    print("MOBILE PRODUCT DNA CONTRACT")
    print("Validation :", "PASS" if not errors else "FAIL")
    print("Errors     :", errors)
    print("Unknown data remains unknown.")
