from typing import Any

from resolver_engine import compare_identity, parse_identity


AUTO_REUSE = "AUTO_REUSE"
NEEDS_EVIDENCE = "NEEDS_EVIDENCE"
HARD_REJECT = "HARD_REJECT"


def _token_set(values: list[str]) -> set[str]:
    return {str(value).strip().lower() for value in values if str(value).strip()}


def _result(
    status: str,
    reason: str,
    *,
    resolver: Any,
    expected: Any,
    candidate: Any,
) -> dict[str, Any]:
    return {
        "status": status,
        "reason": reason,
        "resolver_decision": resolver.decision,
        "resolver_score": resolver.score,
        "expected": {
            "brand": expected.brand,
            "model_tokens": expected.model_tokens,
            "numeric_tokens": expected.numeric_tokens,
            "network_tokens": expected.network_tokens,
            "variant_tokens": expected.variant_tokens,
            "ram_tokens": expected.ram_tokens,
            "storage_tokens": expected.storage_tokens,
        },
        "candidate": {
            "brand": candidate.brand,
            "model_tokens": candidate.model_tokens,
            "numeric_tokens": candidate.numeric_tokens,
            "network_tokens": candidate.network_tokens,
            "variant_tokens": candidate.variant_tokens,
            "ram_tokens": candidate.ram_tokens,
            "storage_tokens": candidate.storage_tokens,
        },
    }


def classify_mobile_identity_reuse(
    expected_text: Any,
    candidate_title: Any,
    candidate_url: Any = "",
    expected_brand: Any = "",
) -> dict[str, Any]:
    """
    Conservative gate for reusing an existing canonical mobile identity.

    Base resolver remains authoritative for brand/model/imposter checks.
    This layer adds exact mobile-variant safety for RAM, storage,
    variant/sibling semantics and network-generation ambiguity.

    Missing evidence is not treated as contradictory evidence.
    """

    resolver = compare_identity(
        expected_text=expected_text,
        candidate_title=candidate_title,
        candidate_url=candidate_url,
        expected_brand=expected_brand,
    )

    expected = parse_identity(
        expected_text,
        brand_hint=expected_brand,
    )

    candidate = parse_identity(candidate_title)

    if resolver.decision == "reject":
        return _result(
            HARD_REJECT,
            "base resolver rejected brand/model/product identity",
            resolver=resolver,
            expected=expected,
            candidate=candidate,
        )

    expected_ram = _token_set(expected.ram_tokens)
    candidate_ram = _token_set(candidate.ram_tokens)

    expected_storage = _token_set(expected.storage_tokens)
    candidate_storage = _token_set(candidate.storage_tokens)

    expected_variant = _token_set(expected.variant_tokens)
    candidate_variant = _token_set(candidate.variant_tokens)

    expected_network = _token_set(expected.network_tokens)
    candidate_network = _token_set(candidate.network_tokens)

    if expected_ram and candidate_ram and not expected_ram.issubset(candidate_ram):
        return _result(
            HARD_REJECT,
            "explicit RAM conflict",
            resolver=resolver,
            expected=expected,
            candidate=candidate,
        )

    if (
        expected_storage
        and candidate_storage
        and not expected_storage.issubset(candidate_storage)
    ):
        return _result(
            HARD_REJECT,
            "explicit storage conflict",
            resolver=resolver,
            expected=expected,
            candidate=candidate,
        )

    if expected_variant and candidate_variant:
        if not expected_variant.issubset(candidate_variant):
            return _result(
                HARD_REJECT,
                "explicit sibling/variant conflict",
                resolver=resolver,
                expected=expected,
                candidate=candidate,
            )

    if candidate_variant and not expected_variant:
        return _result(
            HARD_REJECT,
            "candidate contains additional sibling/variant identity",
            resolver=resolver,
            expected=expected,
            candidate=candidate,
        )

    if expected_network and candidate_network:
        if not expected_network.issubset(candidate_network):
            return _result(
                HARD_REJECT,
                "explicit network-generation conflict",
                resolver=resolver,
                expected=expected,
                candidate=candidate,
            )

    missing_evidence = []

    if expected_ram and not candidate_ram:
        missing_evidence.append("RAM")

    if expected_storage and not candidate_storage:
        missing_evidence.append("storage")

    if expected_variant and not candidate_variant:
        missing_evidence.append("variant")

    if expected_network != candidate_network:
        missing_evidence.append("network generation")

    if missing_evidence:
        return _result(
            NEEDS_EVIDENCE,
            "missing or asymmetric evidence: " + ", ".join(missing_evidence),
            resolver=resolver,
            expected=expected,
            candidate=candidate,
        )

    return _result(
        AUTO_REUSE,
        "brand/model identity passed and all explicit mobile variant constraints matched",
        resolver=resolver,
        expected=expected,
        candidate=candidate,
    )
