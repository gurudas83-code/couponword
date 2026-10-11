# Task 4 — price observation provenance

Proven defect: build_price_evidence did not expose an observation timestamp on its
top-level verified-price contract. Cached observations had timestamps only inside
cached_evidence; retailer seed conversion relied on PriceEvidence's default current time.

Fix: fresh observations carry verified_at; cached observations preserve original verified_at
and explicitly retain unknown current stock. Retailer seed conversion forwards the supplied
time and refuses to manufacture a seed when time is missing. Existing canonical/variant
guards, exact-ASIN binding, six-hour expiry and price-source/link contract remain active.

20 targeted tests PASS: new timestamp/failed-page cases, multi-retailer identity,
failed-price request reuse, discovery diversity (including stale/incorrect URL cache guards).
The new timestamp assertions fail against the earlier implementation, which omitted that field.

Frontend selects price and URL from the same primary offer (best_offer or first retailer offer),
otherwise core price/market source. No independently computed frontend price or rank found.
Exact variant preservation is covered by existing wrong-variant canonical-owner tests.

Limitations: no claim that all retailer adapters or live pages have been independently
certified. Unknown stock stays unknown; a verified recent price is not proof of current stock.
Final live checks and complete regression results belong to Task6. No price was fabricated,
no stale cache was refreshed by this repair, and no deployment occurred.
