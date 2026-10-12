# Premium source attempt — 2026-10-12

This is a bounded continuation from the previous OnePlus/S26 blocker. No old
catalogue, cache or backup was overwritten.

## OnePlus 15, exact 12GB/256GB

Official India source: `https://www.oneplus.in/oneplus-15?sku=501111657`.
The source identifies OnePlus 15, 12GB RAM + 256GB ROM, and lists ₹85,999. It
also states the product is under urgent restocking. The official page's static
HTML is fetchable, but the existing `official_spec_extractor` returns
`manual_review`/no usable specifications for this dynamic page. The existing
Amazon exact-ASIN attempt for B0FTR5NGHJ did not produce a current structured
price and availability, so the ₹84,999 discovery hint remains unverified.

The exact identity is therefore known, but the required combination of
extractor-approved official evidence plus current exact retailer price and
availability is **BLOCKED**. No canonical ID or catalogue record was created.
OnePlus 15R search results were explicitly rejected as a different model.

## Samsung Galaxy S26 Ultra, exact 12GB/256GB

Official India buying source:
`https://www.samsung.com/in/smartphones/galaxy-s26-ultra/buy/?modelCode=SM-S948BLBCINS`.
The page exposes 256GB/12GB, 512GB/12GB and 1TB/16GB choices. Samsung Newsroom
India gives the 12GB/256GB launch price as ₹1,39,999:
`https://news.samsung.com/in/samsung-india-launches-its-most-advanced-ai-phone-the-galaxy-s26-series-for-exciting-offers`.
That launch announcement is not a current retailer offer or availability proof.
The selected buying page did not yield a structured current price/stock signal to
the existing retailer evidence pipeline. Status: **BLOCKED**. No canonical ID or
recommendation evidence was created.

## Other missing premium candidates

The current research seeds include OnePlus 15R, OnePlus 15, Samsung S26 Ultra,
and other premium models, but seed presence is not verification. No other model
was admitted in this bounded run because it would require repeating broad
discovery or inventing retailer evidence. The next lawful batch should use the
same exact-SKU workflow for one candidate at a time.

## Ranking impact

No verified catalogue change occurred, so the saved before/after Top-3 is
unchanged. F36 remains third at ₹1.2L/₹1.5L because only Signature and Redmi
Note 17 Pro Max are stronger admitted peers. This is a coverage blocker, not a
proven price-floor or threshold defect. No scoring rule was changed.

Focused verification remains green: existing 162/162 suite and prior frozen
stability evidence remain valid. Production remains unsafe until a premium peer
passes exact identity, official evidence, current price and availability gates.
