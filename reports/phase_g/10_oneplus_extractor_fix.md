# OnePlus 15 extractor correction — 2026-10-12

## Root cause

The OnePlus India `/15` page is a client-rendered SPA. Its stable server HTML
contains the model title and manufacturer metadata, but not JSON-LD, tables,
definition lists, embedded state, or the existing manufacturer-specific spec
containers. The generic extractor therefore produced zero specifications and a
low/unstable identity score even though the official page identified OnePlus 15.

## Minimal correction

`extract_oneplus_15_meta_specs` now reads only the official `oneplus.in` exact
`/15` path. It requires the page metadata to contain `OnePlus 15` and explicitly
rejects `OnePlus 15R`. It extracts six manufacturer metadata facts into the
existing specification dictionary with source `oneplus_official_meta`:
Snapdragon 8 Elite Gen 5, 165Hz, 7300mAh, triple 50MP camera, 4K 120FPS Dolby
Vision and OxygenOS 16. It never creates RAM/storage fields. The existing exact
listing identity gate remains responsible for 12GB/256GB, and the existing
retailer price gate remains responsible for price and availability.

The identity fallback is equally narrow: verified `oneplus.in/15` only, with
positive OnePlus 15 metadata and an explicit 15R exclusion. No other brand,
path, model or generic page receives this behavior.

## Verification

Focused tests: 14/14 PASS, including OnePlus fixture/source restriction,
variant identity, canonical output, retailer identity and price timestamp guards.
Full suite: **165/165 PASS**, 49 unittest modules, zero failures/errors/skips.
Live extractor check: HTTP 200, `candidate_ready`, identity score 1.0, six
metadata specifications and four page features.

## Admission status

OnePlus 15 exact 12/256 is still **BLOCKED for recommendation admission**. The
official page lists ₹85,999 but says urgent restocking; the exact Amazon ASIN
B0FTR5NGHJ did not yield a current structured in-stock offer. The metadata fix
solves specification extraction only; it does not turn a listed or search-card
price into a current offer. No catalogue or canonical record was added.

Samsung S26 Ultra remains blocked for the same separate reason: official variant
and launch/listed price evidence exist, but current exact retailer price and
availability did not pass the existing pipeline. No ranking rerun was necessary
because no verified premium candidate was admitted.
