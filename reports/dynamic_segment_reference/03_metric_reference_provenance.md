# Metric reference provenance

The adapter accepts structured `metric_records` with exact variant, source, protocol, version, observation date, verification status and `comparable_group_id`. Only approved verified statuses are eligible for a compatible reference group. Missing or incompatible records produce `NO_COMPARABLE_VERIFIED_REFERENCE`.

Reference leaders are selected independently per metric. Ties are retained in `reference_product_ids` and resolved deterministically for the singular `reference_product_id`. Each scorecard row records the candidate value, reference value, relative score, source and protocol.

Current live result: no authorized fresh offer records were available, so there is no live reference winner to report.
