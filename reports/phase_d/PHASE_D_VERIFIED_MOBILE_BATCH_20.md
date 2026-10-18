# Phase D — Verified mobile knowledge batch 1 (20 candidates)

Observed: 2026-10-18 (UTC)

This batch uses the existing `india_three_year_coverage.json` research inventory,
`official_spec_extractor.py`, `product_evidence_store.py` and
`mobile_intelligence_repository.py`. No canonical shopping records or retailer
offers were created.

## Counts

| Measure | At `6115f02` | Current working tree | This batch delta |
|---|---:|---:|---:|
| Official-evidence records | 22 | 35 | 4 exact records added by this batch; other dirty evidence rows were preserved |
| Exact RAM/storage evidence | 9 | 22 | 4 exact model/variant admissions |
| Private Product DNA records | 5 | 9 | 4 admitted |
| Canonical shopping IDs | 34 | 34 | 0 |
| Fresh in-stock offers | 0 | 0 | 0 |

The scoped commit itself contains 26 official-evidence records (13 exact) and
9 private DNA records. The larger working-tree totals include 11 older dirty
evidence rows that remain outside this commit and were restored after commit
creation.

The working tree already contained dirty evidence rows from earlier work. They
remain uncommitted and untouched by this batch. The four new records are
`Samsung Galaxy F05 4/64`, `vivo T4x 6/128`, `vivo T5x 6/128`, and
`vivo T5 Pro 8/128`.

## Candidate result

`PRIVATE_DNA_ADMITTED` means exact official identity and RAM/storage passed the
existing extractor/evidence gates. It does not mean buyable or recommendation
eligible: all four have `canonical_product_id = null` and no current offer.

| Candidate / exact variant | Official source or bounded result | State | Reason |
|---|---|---|---|
| Samsung Galaxy F05 — 4/64 | [Samsung India product page](https://www.samsung.com/in/smartphones/galaxy-f/galaxy-f05-blue-64gb-sm-e055fdbdins/) | PRIVATE_DNA_ADMITTED | Exact Memory 4 GB and Storage 64 GB extracted; page identity 1.0 |
| vivo T4x 5G — 6/128 | [vivo India selected SKU 19292](https://shop.vivo.com/in/product/10303?skuId=19292) | PRIVATE_DNA_ADMITTED | Exact selected-SKU heading; page identity 1.0 |
| vivo T5x 5G — 6/128 | [vivo India selected SKU 19387](https://shop.vivo.com/in/product/10339?skuId=19387) | PRIVATE_DNA_ADMITTED | Exact selected-SKU heading; page identity 1.0 |
| vivo T5 Pro 5G — 8/128 | [vivo India selected SKU 19410](https://shop.vivo.com/in/product/10344?skuId=19410) | PRIVATE_DNA_ADMITTED | Exact selected-SKU heading; page identity 1.0 |
| Nothing Phone 3a — 8/128 | [Nothing India selected configuration](https://in.nothing.tech/products/phone-3a?Capacity=8%2B128GB&Colour=White) | IDENTITY_BLOCKED | Page is official and selected, but the existing extractor did not emit exact physical RAM/storage fields; no DNA write |
| Redmi 13 5G — 6/128 | [Xiaomi India specifications](https://www.mi.com/in/product/redmi-13-5g/specs/) | IDENTITY_BLOCKED | Page lists 6/8 GB RAM and 128 GB together; no selected exact variant binding |
| realme P3 5G — 6/128 | [realme India product page](https://www.realme.com/in/realme-p3-5g) | IDENTITY_BLOCKED | Page exposes expanded/default 18 GB/256 GB wording; requested physical 6/128 is not independently selected |
| realme C61 — 6/128 | [realme India store](https://buy.realme.com/in/goods/713?feedback=01) | IDENTITY_BLOCKED | Store exposes several configurations without an exact selected URL in the bounded attempt |
| OPPO A5x — 4/128 | [OPPO India specifications](https://www.oppo.com/in/smartphones/series-a/a5x/specs/) | IDENTITY_BLOCKED | Official page lists 4/64 and 4/128; exact selection is not bound |
| OPPO K13 5G — 8/128 | [OPPO India product page](https://www.oppo.com/in/smartphones/series-k/k13-5g/) | IDENTITY_BLOCKED | India page has model evidence but no exact physical RAM/storage selection |
| Motorola Edge 60 Fusion — 8/256 | [Motorola India SKU page](https://www.motorola.in/smartphones-motorola-edge-60-fusion/p?skuId=491) | EXTRACTOR_FAILURE | Exact page is dynamic; existing extractor sees JSON-LD but not the rendered selected specs |
| POCO X7 Pro — 8/256 | [Xiaomi global specifications](https://www.mi.com/global/product/poco-x7-pro/specs/) | MISSING_OFFICIAL_EVIDENCE | India-specific official source was not established; global page is not substituted |
| POCO M7 Pro — 6/128 | — | RESEARCH_ONLY | No bounded India official source established |
| Google Pixel 7a — 8/128 | — | IDENTITY_BLOCKED | Bounded official source did not expose physical RAM for exact identity |
| Lava Agni 4 — 8/256 | — | RESEARCH_ONLY | No bounded India official source established |
| Infinix GT 30 Pro — 8/256 | — | MISSING_OFFICIAL_EVIDENCE | Only a global official page was found in the bounded attempt |
| OPPO Reno12 — 8/256 | — | IDENTITY_BLOCKED | Available official pages did not bind the requested India physical variant |
| OPPO Reno14 — 8/256 | [OPPO India launch release](https://www.oppo.com/in/newsroom/press/oppo-reno14-series-launched/) | IDENTITY_BLOCKED | India launch lists 8/128, 12/256 and 12/512; requested 8/256 is not verified |
| Samsung Galaxy S25 FE — 8/128 | — | RESEARCH_ONLY | No bounded India official exact-variant page established |
| OnePlus 13s — 12/256 | — | RESEARCH_ONLY | No bounded India official exact-variant page established |

No candidate received a canonical shopping ID, current price, or retailer
button. This preserves the existing exact identity, six-hour freshness,
in-stock and security gates.

## Focused correction

The existing vivo/iQOO selected-SKU extractor was called after page-wide chrome
removal. On vivo pages the exact RAM/storage heading is inside that removed
markup, so the page remained model-verified but lost its physical variant.
`official_spec_extractor.extract_one()` now captures the selected-SKU heading
before cleanup and then continues through the same evidence pipeline. The
correction is source-specific and does not change ranking, thresholds, offers,
canonical identity, or security behavior.

## Verification

- New batch tests: 3/3 PASS.
- Existing Phase-D coverage, private-DNA, and variant-identity tests run with this batch: 12/12 PASS.
- Historical non-catalogue fixture gap remains recorded separately; it was not weakened or skipped.
- No fresh retailer offers were added; `retailer_offers.json` still has zero valid fresh in-stock rows.

## Remaining backlog

The next batch should target exact manufacturer selected-SKU pages for the
blocked Redmi/realme/OPPO/Motorola candidates. Global pages, multi-variant
specification pages, search snippets, launch prices and expanded/virtual RAM
must remain blocked until an exact India physical variant is independently
bound.
