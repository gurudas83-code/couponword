# Coupon-World India mobile coverage closure

Generated from the existing repository on 18 October 2026. This report
separates research discovery, verified Product DNA and current shopping offers.
It does not treat a research row as a recommendation or invent a market
denominator.

## A. Current master inventory

The source files represent different scopes:

| Source | Rows | Meaning |
| --- | ---: | --- |
| `data/india_three_year_coverage.json` candidates | 126 | The tracked three-year research queue |
| `data/mobile_universe_priority_126.json` | 187 | Extended priority discovery, including 62 rows without an exact physical variant |
| Saved manufacturer launch inventory | 25 | Launch evidence rows; 18 model names were not present in the 187-entry priority file |
| Generated master models | 207 | Deduplicated union of the three existing sources |
| Generated exact physical variants | 128 | Rows with explicit RAM and storage in the source records |

The 207-model union is the current discoverable inventory, not a complete
Indian-market census. `denominator_status` therefore remains
`COVERAGE_DENOMINATOR_UNVERIFIED`.

The complete model/variant list, grouped with launch evidence and provenance,
is in [mobile_universe_2023_2026.json](../../data/mobile_universe_2023_2026.json).

## B. Backend comparison

The generated gap manifest compares every master variant with the existing
canonical registry, official evidence cache, private Product DNA repository and
retailer offer store:

| State | Rows |
| --- | ---: |
| Existing canonical mapping | 2 |
| Existing private Product DNA | 2 |
| Official evidence only | 7 |
| Research only | 197 |
| Total manifest rows | 208 |

The registry contains 34 mobile canonical IDs globally, but only two can be
joined to a source-backed exact variant in this manifest without inventing a
mapping. The other registry IDs remain counted globally and are not silently
assigned to a model.

## C. Before/after coverage

This run added no Product DNA or shopping records. It created reproducible
coverage manifests and a resumable reconciliation checkpoint from existing
data:

| Metric | Current value | Verified meaning |
| --- | ---: | --- |
| Discovered unique models | 207 | Existing-source union |
| Discovered exact variants | 128 | Explicit RAM/storage rows |
| Existing backend models in the manifest | 11 | Evidence/DNA/canonical joins only |
| Missing models identified | 196 | No durable exact backend join |
| Official evidence records | 35 | Current working-tree evidence store |
| Exact-variant evidence | 22 | Existing exact-evidence count |
| Private Product DNA | 9 | Existing durable private repository |
| Canonical mobile IDs | 34 | Existing mobile registry IDs |
| Fresh in-stock offers | 0 | Six-hour exact-offer gate |
| Current-price eligible additions | 0 | No new canonical + fresh-offer pair |
| New Product DNA admissions | 0 | No new source verification was fabricated |

The first verified Phase-D batch remains the only new admission batch in this
worktree: four Product DNA records were added earlier. The current run did not
overwrite them or the owner's dirty evidence/cache files.

## D. Actual admission state

The gap manifest records each exact variant, existing IDs, evidence record IDs,
and the required next action. No unverified model was admitted. Product DNA and
buyable offers remain separate states; a fresh offer is required before a
priced recommendation or retailer button can be enabled.

## E. Blocker recovery

The main shared blocker is evidence and identity coverage, not a ranking
change:

- `MISSING_OFFICIAL_EVIDENCE`: 197 research-only rows need bounded official
  source verification.
- `EXACT_VARIANT_IDENTITY_GAP`: model-level evidence exists but the physical
  RAM/storage selection is not established for that seed variant.
- `CANONICAL_MAPPING_GAP`: Product DNA or a source-backed exact row exists, but
  no trusted canonical owner mapping is present.
- `OFFER_COVERAGE_BLOCKED`: current offers are absent or stale; no old price is
  promoted to current.

The existing extractor correction for selected manufacturer capacities remains
in place. No new extractor, ranker or retailer bypass was introduced here.

## F. Price segments

The research manifests carry source budget buckets where they already exist.
No current price band is asserted for a model without a fresh exact offer.
The existing ₹50,000 policy is unchanged: ₹40,000–₹50,000 is primary, lower
prices are value, and prices above budget are rejected.

## G. Source evidence

Source URLs and observation metadata are preserved in the existing launch and
official evidence stores and referenced by the generated manifests. Secondary
directory rows are discovery inputs only. Unknown manufacturer fields remain
unknown; no launch year, SKU, price or availability was inferred.

## H. Tests and execution

The single resumable coordinator was run for the complete existing queue:

```text
py python/run_mobile_coverage.py --market IN --start-year 2023 --end-year 2026 --resume --until-exhausted
```

Result: manifest cursor exhausted (`208/208` rows reconciled), with 197
research-only blockers. The focused inventory/evidence tests remain 8/8 PASS;
the earlier Phase-D focused suite was 34/34 PASS before this manifest-only run.
No live retailer calls were made and no historical fixture result was changed.

## I. Repository integration

Files created by this scoped run:

- `python/run_mobile_coverage.py`
- `data/mobile_universe_2023_2026.json`
- `data/mobile_coverage_gap_2023_2026.json`
- `data/mobile_coverage_progress.json`
- this report

Existing dirty files were preserved: `data/retail_price_cache.json`,
`data/verified_product_evidence_cache.json`,
`data/market_discovery_cache.json` and `outputs/`.

## J. Unresolved market gaps

The remaining queue is recorded in
[mobile_coverage_gap_2023_2026.json](../../data/mobile_coverage_gap_2023_2026.json).
It must be processed in small, permitted official-source batches. Rows with
missing exact evidence stay pending; rows with Product DNA but no canonical ID
stay knowledge-only; rows with no fresh offer stay out of current shopping
recommendations.

## K. One-command resume

The same deterministic command can rebuild the manifests and preserve the
exhausted cursor:

```text
py python/run_mobile_coverage.py --market IN --start-year 2023 --end-year 2026 --resume --until-exhausted
```

This coordinator deliberately reconciles existing sources and does not claim
that inaccessible official or retailer pages were verified. A future evidence
batch should use the existing official extractor and admission workflow, then
rerun this command to update the gap state.

## Final acceptance status

**Coverage status: INCOMPLETE.** The repository now has a complete
source-backed gap queue for the currently discoverable union, but the actual
Indian-market denominator, most official exact evidence and all fresh offers
remain unverified. This is an honest data-coverage blocker, not permission to
lower identity or price gates.
