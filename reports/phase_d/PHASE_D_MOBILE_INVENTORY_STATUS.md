# Phase D mobile inventory status

## Why the recommendation count has not increased

The research list and the recommendation catalogue are separate stages. The
existing backend can use a phone in a recommendation only after the exact
brand/model/RAM/storage identity is verified, Product DNA or official evidence
is durable, a canonical mobile ID exists, and a matching retailer offer is
fresh, in stock and price-valid. A research row by itself does not satisfy
those gates.

The latest verified counts are:

| Stage | Current count | Meaning |
| --- | ---: | --- |
| Existing India research seed | 187 entries | Candidate inventory from `data/mobile_universe_priority_126.json`; not a verified launch census |
| Three-year coverage source | 126 entries | Existing `data/india_three_year_coverage.json` research list |
| Official evidence records | 35 | Evidence rows in the current working-tree evidence store |
| Exact-variant evidence | 22 | Rows previously classified as exact variant evidence |
| Private Product DNA | 9 | Durable verified DNA records in `data/mobile_intelligence_repository.json` |
| Canonical mobile IDs | 34 | Mobile IDs in `data/retailer_product_registry.json` |
| Fresh in-stock offers | 0 | No exact offer is within the existing six-hour freshness gate |
| New rankable variants from the latest batch | 0 | No newly admitted variant has both canonical identity and a fresh offer |

The first verified batch added four Product DNA records. The remaining seed
rows are still blocked by missing exact official evidence, identity review,
canonical admission or a fresh exact retailer offer. Their count is therefore
not allowed to increase the recommendation result merely because a name is in
the research inventory.

## Inventory status feed

`data/phase_d_mobile_inventory_status.json` is a deterministic status index
derived from the existing 187-entry research inventory. It records each
candidate's exact seed variant (when known), evidence URLs, private-DNA IDs,
canonical ID and current offer state. It is safe to load for backend/admin
coverage reporting, but it deliberately does not promote research rows to
shopping eligibility. The recommendation path remains the existing canonical
registry + official evidence + retailer-offer stores.

The status index has two summaries: global current-store counts and the join
of those stores against the 187 seed entries. This avoids confusing records
that are verified elsewhere with an exact seed match. `in_stock` rows older
than six hours are reported as stale and do not count as fresh offers.

## Correct next action

Process the remaining high-priority seed rows in small, evidence-backed
batches. For each row, verify the exact India variant on an official source,
admit Product DNA through the existing workflow, then obtain an exact current
retailer offer before expecting the canonical mobile count or search results
to increase. Do not invent prices, canonical IDs or specifications, and do not
lower any eligibility threshold to make the inventory appear larger.

No push or deployment was performed. Existing dirty evidence, price-cache and
discovery-cache files remain untouched.
