# Premium recommendation quality audit — 2026-10-11

## Finding

The Samsung Galaxy F36 5G appears third at ₹1.2 lakh and ₹1.5 lakh because the
current verified candidate pool contains only two materially stronger premium/value
peers: Motorola Signature and Redmi Note 17 Pro Max. F36 is not being promoted by a
price bonus. It survives the strict budget and evidence gates and has a 62 fit score:
17h verified video playback (battery 0.5667), AMOLED/high-refresh display (0.5),
OIS/4K/multi-camera/50MP evidence (0.75), 5.2-year support (0.9), and 5G (0.8);
performance and ease-of-use are unknown. Its exact current price is ₹22,370.

Signature scores 68 (₹59,990; 12/256 exact; 28h video/57h music official claims,
Snapdragon 8 Gen 5, 165Hz, camera evidence; support/connectivity unknown). Redmi
scores 61 (₹49,998; exact listing; 75% battery, 95% display, 70% camera, 80%
connectivity; performance/support unknown). The same evidence snapshot returns the
same three in both ₹1.2L and ₹1.5L runs.

## Cause separation

1. **Missing premium coverage — primary cause.** The 30-candidate pools contain only
one reviewed high-end identity (Signature) and no admitted OnePlus 15 or Galaxy S26
Ultra record. Research seeds are not verified catalogue entries.
2. **Retrieval — secondary cause.** The bounded pool reaches 30 and the evidenced-tail
recall fix is active. It cannot retrieve a candidate whose exact identity/retailer
evidence has not been admitted. No early-stop omission was found in these traces.
3. **Scoring calibration — secondary, bounded.** F36's physical/evidence score is
defensible for its known facts, but the engine has no verified premium peer to outrank
it. The capability/evidence split is now explicit; adding a price floor would be an
unjustified scoring change. No scoring threshold was lowered.

## Source checks

- OnePlus 15 official India page: `https://www.oneplus.in/oneplus-15?sku=501111657`.
  Existing extractor fetched the page but rejected the expected identity and extracted
  no specs. Search returned B0FTR5NGHJ (15, 12/256, ₹84,999 hint) plus two 15R rows;
  none is a verified offer. Search-card price is deliberately excluded.
- Samsung Galaxy S26 Ultra official India buying page:
  `https://www.samsung.com/in/smartphones/galaxy-s26-ultra/buy/?modelCode=SM-S948BZDBINS`.
  The page exposes 12/256, 12/512 and 16/1TB choices, but no exact selected-SKU
  current price/availability was extracted. No retailer offer was admitted.

Raw checks: `outputs/phase-g-oneplus15.json` and
`outputs/phase-g-premium-source-check.json` if the latter is available. No canonical
ID, spec or current price was invented.

## Before/after

No safe premium source was admitted and no ranking rule changed after the saved
`phase-g-api.json` run. Therefore the exact Top-3 and verified prices are unchanged:

- ₹50k: Redmi Note 17 Pro Max ₹49,998; Samsung F36 ₹22,370; Samsung A56 ₹32,999.
- ₹1.2L: Motorola Signature ₹59,990; Redmi Note 17 Pro Max ₹49,998; Samsung F36 ₹22,370.
- ₹1.5L: Motorola Signature ₹59,990; Redmi Note 17 Pro Max ₹49,998; Samsung F36 ₹22,370.

All are strict pipeline prices with source/timestamp in their payloads; retailer
availability may remain unknown. Repeating ₹1.5L with unchanged evidence preserved
count and order. No artificial “premium minimum” was introduced.

## Release decision

The six prior commits plus the current local fixes are reviewable, and the final local
suite is 162/162 PASS. Staging can use this branch only as an explicitly incomplete
candidate. Production is **not safe**: premium coverage is incomplete, OnePlus/S26
exact price evidence is unresolved, live Render SHA/browser smoke is unverified, and
the API's `market_quality` remains `NOT_VERIFIED`. Keep Phase-G INCOMPLETE.
