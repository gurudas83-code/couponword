# Phase-D Canonical Admission Investigation

**Worktree:** `C:\Users\HP\Documents\projects\couponword-phase-d-coverage`
**Base under review:** `ad283e32c47520444e927a2a5d38826db476bf7c`
**Scope:** five verified exact variants; no ranking, discovery or security redesign

## Admission contract found in the existing code

The repository has three deliberately separate states:

| State | Existing gate | Fresh `in_stock` offer required? | Source |
|---|---|---:|---|
| A. Verified Product DNA | Successful official fetch, resolver verification, usable evidence, exact variant signature. Private DNA persistence validates the record and allows `canonical_product_id = null` | **No** | `python/product_evidence_store.py:476-539`; `python/mobile_intelligence_repository.py:91-131`; `python/mobile_product_dna.py:49-78` |
| B. Currently buyable offer | Exact canonical product/brand/model/variant, approved retailer URL, positive price, `in_stock`, valid timestamp within the six-hour cache window; selected-vivo SKU must match the retailer ID | **Yes** | `python/retailer_offer_store.py:69-185` |
| C. Priced shopping recommendation | Candidate must resolve to an exact durable catalogue owner before model deduplication/ranking, then pass verified current price/offer and the existing eligibility/scoring gates | **Yes** | `python/shopping_intelligence_pipeline.py:1484-1568`, `1793-1815`, `2846-2955`; `python/retailer_product_registry.py:138-224` |

The Amazon promotion utility is a separate, strict catalogue-owner workflow. It requires a numeric `coupons.json` source row, category `Mobiles`, exact Amazon ASIN, no existing ASIN owner, and a live exact Amazon identity check before writing `cw-mobile-<source_id>` (`python/promote_mobile_canonical.py:245-409`). It does **not** require a fresh offer, but it cannot run without a real catalogue row and exact ASIN. Inventing either would violate the existing gate.

## Five-variant trace

All five records now pass `find_verified_evidence()` with an exact physical signature and have a durable private Product DNA record. None has a matching `coupons.json` catalogue row, canonical registry owner, or fresh offer row.

| Variant | Official evidence | Private Product DNA | Existing catalogue/registry match | Fresh offer | Result |
|---|---|---|---|---|---|
| iQOO Neo 10 12/256, SKU 19299 | `https://shop.vivo.com/in/product/10325?skuId=19299` plus official iQOO specs | `dna-iqoo-neo-10-12gb-256gb` | None | None; official page observed out of stock | **DNA ADMITTED; SHOPPING BLOCKED** |
| vivo V60 12/256, SKU 19255 | `https://shop.vivo.com/in/product/10320?skuId=19255` | `dna-vivo-v60-12gb-256gb` | None | None; official page observed out of stock | **DNA ADMITTED; SHOPPING BLOCKED** |
| OnePlus 13R 12/256, manufacturer SKU 5011111066 | `https://www.oneplus.in/13r/specs` and official SKU terms | `dna-oneplus-13r-12gb-256gb` | None | None; ₹42,999 is listed/MRP only | **DNA ADMITTED; SHOPPING BLOCKED** |
| OnePlus 13 12/256 | `https://www.oneplus.in/13/specs` | `dna-oneplus-13-12gb-256gb` | None | None; no exact current offer verified | **DNA ADMITTED; SHOPPING BLOCKED** |
| Samsung Galaxy S24 8/256 | `https://www.samsung.com/in/smartphones/galaxy-s/galaxy-s24-onyx-black-256gb-sm-s921ezkwins/` | `dna-samsung-galaxy-s24-8gb-256gb` | None | None; no exact current offer verified | **DNA ADMITTED; SHOPPING BLOCKED** |

The private IDs above are deterministic Product DNA storage keys, not canonical catalogue IDs, Amazon ASINs or retailer IDs. Every record has `canonical_product_id: null`, so the recommendation pipeline cannot mistake it for a buyable product.

## Root cause

There is no defect where a fresh offer is incorrectly required for Product DNA. The existing private repository explicitly supports verified DNA without a canonical owner or price. The actual blocking dependency is downstream:

1. `promote_mobile_canonical.py` cannot create a `cw-mobile-*` owner without a numeric `coupons.json` row and a verified exact ASIN.
2. `retailer_product_registry.find_catalogued_mobile_id()` refuses an unregistered or variant-ambiguous ASIN.
3. `catalogued_recommendation_candidates()` drops candidates without that exact owner before ranking.
4. `find_fresh_verified_offer()` requires the exact owner plus an in-stock, timestamped, six-hour-valid offer.

This is a verified external-data/catalogue-mapping gap, not a scoring or eligibility defect. No threshold or price rule was relaxed.

## Before/after result

| Measure | Before | After this investigation |
|---|---:|---:|
| Official evidence records | 17 | 22 |
| Exact verified variants | 4 | 9 |
| Durable private Product DNA records for this batch | 0 | 5 |
| Canonical mobile IDs | 34 | 34 |
| Fresh buyable retailer offers | 0 | 0 |
| Current-price eligible recommendations from this batch | 0 | 0 |

## Validation

- Evidence lookup and exact variant checks: 5/5 pass.
- Durable private DNA reload after a clean process boundary: 5/5 records load with exact brand/model/RAM/storage and `canonical_product_id = null`.
- `test_phase_d_coverage.py` now covers the five durable records and the negative OnePlus 13R parser guard.
- Existing focused suite remains green except the documented historical non-catalogue `FIXTURE_GAP`; no fresh offer, price, retailer button or ranking result was fabricated.

## Decision

No schema or product-policy change is required. Product DNA admission is now independent of retailer stock through the existing `mobile_intelligence_repository`. Canonical shopping admission remains correctly blocked until an authorized exact retailer identifier/ASIN and a fresh exact in-stock offer are available.

**Next owner action:** provide or authorize one exact retailer listing for any of the five variants. Then run the existing canonical promotion workflow, register the exact retailer ID, add the six-hour offer observation, and rerun only the affected eligibility/API tests.
