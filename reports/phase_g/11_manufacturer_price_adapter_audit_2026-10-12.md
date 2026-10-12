# Phase-G manufacturer price adapter audit — 2026-10-12

## Change

`6eef4cd` extends the existing `retail_price_evidence` adapter with narrow
first-party URL admission: OnePlus `/15` and `/oneplus-15` product paths and
Samsung India smartphone `/buy` paths. It also records JSON-LD `InStock` or
`OutOfStock` only when the structured offer states it. Generic manufacturer,
support, news, and search pages remain rejected; missing price remains unknown.

## Bounded live checks

| Candidate | Exact evidence result | Decision |
|---|---|---|
| OnePlus 15, 12/256, `501111657` | HTTP 200, no structured current price, availability unknown; official page shows urgent restocking | Specs retained, offer pending; not admitted |
| Samsung Galaxy S26 Ultra, selected India buy page | HTTP 200, JSON-LD contains multiple variant prices (₹154,999 and ₹174,999), aggregate availability `InStock`; exact selected SKU price is ambiguous | Specs/listed evidence retained, offer pending; not admitted |

The Samsung newsroom ₹139,999 figure remains historical/listed launch pricing,
not a current exact offer. Search-card prices remain hints and were not used.

## Ranking impact

No fully verified candidate was admitted, so ranking rules and saved traces are
unchanged:

- ₹50k: Redmi Note 17 Pro Max ₹49,998; Samsung Galaxy F36 5G ₹22,370; Samsung Galaxy A56 5G ₹32,999.
- ₹1.2L: Motorola Signature ₹59,990; Redmi Note 17 Pro Max ₹49,998; Samsung Galaxy F36 5G ₹22,370.
- ₹1.5L: Motorola Signature ₹59,990; Redmi Note 17 Pro Max ₹49,998; Samsung Galaxy F36 5G ₹22,370.

F36 remains third because the verified premium peer pool still contains only
the admitted Signature and Redmi candidates; this is a coverage bottleneck,
with scoring calibration secondary. No threshold or identity/price guard was
changed.

## Tests and readiness

- Focused adapter, OnePlus extractor, and price timestamp tests: **9/9 PASS**.
- Full discovery run: **168 tests discovered; 166 pass, 2 environment errors**
  (missing optional `google.genai`; missing semantic result fixture). These are
  pre-existing environment/fixture issues, unrelated to this scoped change.
- No premium model was safely admitted. External retailer exact-SKU price and
  availability remain the blocker. **Not ready for production premium release.**
