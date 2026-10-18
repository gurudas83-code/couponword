# Phase-D Mobile Coverage Expansion — Final Local Receipt

**Date:** 2026-10-18
**Worktree:** `C:\Users\HP\Documents\projects\couponword-phase-d-coverage`
**Branch:** `phase-d-coverage`
**Base:** `e5d9dced13a6d615e466973cb7a04f9e3b6dd055` (`ranking-quality-repair`)
**Release state:** local only; no push, merge or deploy

## Scope and safety

This run used the existing official-specification extractor, evidence cache, canonical admission workflow and retailer-offer gates. It did not change ranking weights, budget grouping, identity thresholds, freshness rules, security controls or retailer link handling. Research leads were treated as leads only. No canonical ID, offer, stock state or specification was invented.

The original ranking worktree remains untouched apart from its pre-existing runtime caches and outputs. This isolated worktree contains the Phase-D source/evidence/test/report changes below. Generated caches created while running the local gate are excluded from the commit.

## Inventory before and after

Counts were calculated from the tracked files in this worktree. “Fresh in-stock” uses the existing six-hour offer rule and requires a real observation timestamp and `in_stock` state.

| Measure | Before | After | Evidence |
|---|---:|---:|---|
| India three-year research-seed variants | 126 | 126 | `data/india_three_year_coverage.json` |
| Research-seed models | 126 | 126 | same file; unresolved research rows remain separate variants |
| Mobile catalogue rows / exact variants | 40 / 40 | 40 / 40 | `coupons.json` |
| Canonical mobile IDs | 34 | 34 | `data/retailer_product_registry.json` (`products` keys) |
| Official-evidence records | 17 | 22 | `data/verified_product_evidence_cache.json` |
| Exact RAM/storage evidence records | 4 | 9 | same cache; both fields are present in `variant_signature` |
| Retailer-offer rows | 7 | 7 | `data/retailer_offers.json` |
| Fresh, timestamped, in-stock offers | 0 | 0 | existing offer store; no row has a usable observation timestamp/current six-hour validity |
| Clean tracked-store rankable variants | 0 | 0 | no fresh in-stock offer can pass the existing recommendation gate |

The seed inventory still reports 124 `needs_launch_identity_price_verification` rows and two `already_present_exact_variant` rows. This is a coverage backlog, not evidence that all 126 phones are eligible recommendations.

The previously quoted 187-seed baseline is not present in the current tracked seed file; the reproducible current denominator is 126 candidates. No rows were deleted in this run.

## Verified Product DNA batch

These five exact variants were admitted to the existing evidence cache as `candidate_ready` Product DNA. They have no canonical ID or buyable offer in this batch, so none is recommendation-eligible yet.

| Candidate | Exact physical variant | Official evidence | Observation | Offer state | Canonical admission |
|---|---|---|---|---|---|
| iQOO Neo 10 | 12 GB / 256 GB, SKU `19299` | [iQOO Neo 10 official specs](https://www.iqoo.com/in/products/param/neo10?id=64); selected SKU [official store page](https://shop.vivo.com/in/product/10325?skuId=19299) | 2026-10-18T04:12:04Z (exact heading) | Official selected page showed ₹38,999, but `Out of stock`; not a current buyable offer | Not admitted; no existing canonical mapping/SKU registry row |
| vivo V60 | 12 GB / 256 GB, SKU `19255` | selected [official store page](https://shop.vivo.com/in/product/10320?skuId=19255) | 2026-10-18T04:12:07Z (exact heading) | Official selected page showed ₹45,999, but `Out of stock`; not a current buyable offer | Not admitted; no existing canonical mapping/SKU registry row |
| OnePlus 13R | 12 GB / 256 GB, manufacturer SKU `5011111066` | [official 13R specifications](https://www.oneplus.in/13r/specs); [official SKU terms](https://www.oneplus.in/oneplus-easy-upgrades/terms-and-conditions) | 2026-10-18T04:12:01Z | ₹42,999 is explicitly stored as a listed/MRP value from the terms page. No current in-stock SKU offer was verified | Not admitted; no current offer and no canonical retailer mapping |
| OnePlus 13 | 12 GB / 256 GB | [official India specifications](https://www.oneplus.in/13/specs) | 2026-10-18T04:43:49Z (configuration text) | No current exact buyable offer verified; no price promoted | Not admitted; no current offer and no canonical retailer mapping |
| Samsung Galaxy S24 | 8 GB / 256 GB, India page `SM-S921EZKWINS` | [Samsung India official page](https://www.samsung.com/in/smartphones/galaxy-s/galaxy-s24-onyx-black-256gb-sm-s921ezkwins/) | 2026-10-18T04:44Z (official memory/storage fields) | No current exact buyable offer verified; no price promoted | Not admitted; no current offer and no canonical retailer mapping |

The shared `shop.vivo.com` storefront exposes generic platform JSON-LD (`vivo`) for the iQOO page. The record is bound to iQOO only through the exact selected heading and the separate official iQOO specification page; the generic platform brand is not used as iQOO identity evidence.

## Source-specific correction

`python/official_spec_extractor.py` now permits the existing selected-SKU capacity helper for `iQOO` only when all existing restrictions remain true: verified official page, `shop.vivo.com`, `/in/product/<digits>` path, `skuId=<digits>`, exact selected heading, exact model and exact RAM/storage. It also binds the visible `12GB+256GB` configuration on the exact OnePlus `/13/specs` route, rejecting a 13R page. The helpers still fail closed for other brands, sibling models or mismatched headings. These are source-specific extractor corrections; no scoring or eligibility rule changed.

## Gate and recommendation observations

The saved local seven-query gate receipt was inspected without rerunning broad discovery. In the representative run, the existing pipeline executed normally and returned honest results: `mobile under 10000` was `PARTIAL` with two eligible IDs (`cw-mobile-84`, `cw-mobile-79`), while supported `under 15000`, generic `under 20000` and Samsung `under 20000` rows returned three results. Timings remained discovery-bound (roughly 4–44 seconds in that receipt). The three new Product DNA records did not appear because they have no canonical identity/verified fresh in-stock offer.

For the ₹50,000 primary band, the new leads are not silently promoted:

- OnePlus 13R listed ₹42,999: Product DNA verified; current offer unavailable, so excluded.
- iQOO Neo 10 observed ₹38,999: below the existing ₹40,000 primary floor and out of stock; excluded.
- vivo V60 observed ₹45,999: in the declared price interval but out of stock; excluded.

The correct current conclusion is a verified coverage/offer gap, not a ranking defect. No lower-band phone was promoted into a primary result and no threshold was lowered.

## Duplicate, rejection and blocker accounting

- No new canonical IDs were created, so there are no duplicate or ambiguous canonical writes.
- 124 research-seed rows remain unresolved for launch identity/price verification.
- The three new exact variants are blocked at the canonical/current-offer boundary: iQOO and vivo V60 are out of stock; OnePlus 13R has only a listed price and no verified current buyable offer.
- OnePlus 13 and Samsung Galaxy S24 now have exact official Product DNA, but no current exact buyable offer or canonical retailer mapping was verified.
- Existing seven offer rows are not usable for a six-hour current recommendation because they lack a valid observation timestamp/current freshness proof.
- No CAPTCHA, private endpoint, paid API or fabricated retailer evidence was used.

## Focused validation

The Phase-D correction and its affected gates were run after the edit:

`test_phase_d_coverage.py`, manufacturer-offer admission, Product DNA, exact-variant identity, Gate-3 API, budget-band/presentation, OnePlus extractor and security tests: **32/32 PASS**.

The new tests prove both positive and negative identity behavior (iQOO 12/256 selected heading binds exactly; an 8/256 heading cannot be reused) and verify all three durable Product DNA records have HTTPS official sources, exact 12/256 signatures and resolver verification.

The focused Phase-D/security/regression subset ran **29/29 PASS**. The expanded relevant set ran **66 tests: 65 PASS, 1 FAIL**. The one failure is the pre-existing historical non-catalogue pilot assertion (`test_existing_snapshot_reaches_real_pipeline`): its output is classified `fixture_gap` with `executed=0` because the mutable historical discovery snapshot is unavailable, so the old three-result expectation cannot be reconstructed from current immutable inputs. The Phase-D correction does not alter that path. It remains visible as an existing fixture blocker; it was not weakened or skipped. The other offline catalogue lane, identity, budget, security and retailer tests passed.

Python compilation (`official_spec_extractor.py`), JavaScript syntax (`buying-guides.js`) and `git diff --check` all passed. No production or remote checks are claimed from this local run.

## Changed and excluded files

Intended source/evidence/test/report files:

- `python/official_spec_extractor.py`
- `data/verified_product_evidence_cache.json` (three exact Product DNA records; no offers or canonical IDs)
- `test_phase_d_coverage.py`
- `reports/phase_d/PHASE_D_COVERAGE_EXPANSION_FINAL.md`

Excluded generated or runtime-only files: `data/retail_price_cache.json`, `data/market_discovery_cache.json`, `data/runtime_shopping_intelligence.json`, `data/official_sitemap_cache.json` and `outputs/`. They are not release evidence and are not staged.

## Decision and next action

**Phase-D coverage expansion status: PARTIAL.** The extractor corrections are verified and five exact official Product DNA records are durable. Recommendation coverage did not increase because no new candidate has both a canonical mapping and a fresh, in-stock exact retailer offer.

The subsequent canonical-admission trace durably stored all five verified exact variants in the existing private Product DNA repository with `canonical_product_id: null`; it did not create retailer owners or buyable offers. See [PHASE_D_CANONICAL_ADMISSION_INVESTIGATION.md](PHASE_D_CANONICAL_ADMISSION_INVESTIGATION.md) for the gate-by-gate result.

**Next smallest safe action:** obtain one authorized exact in-stock Amazon, Flipkart, Croma or official-store offer for an existing Product DNA record, bind it through the canonical admission workflow with its observed timestamp, and rerun only the corresponding identity/offer/API tests. Do not add an ID or current price until that evidence is available.

No push, merge or deploy was performed.
