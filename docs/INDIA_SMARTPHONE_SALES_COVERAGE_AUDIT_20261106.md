# India smartphone sales coverage audit — 6 November 2026

## Scope and source truth
This is a **repository coverage** audit, not an assertion of a nationally certified Top 10 list for November 2026.

- **Q3 2026 market signal:** [Omdia, 19 October 2026](https://omdia.tech.informa.com/pr/2026/oct/indias-smartphone-shipments-fell-26percent-to-a-decade-low-third-quarter-level-despite-festive-season). It names model families or series contributing to vendor shipments, but publishes **no exact ordered top-ten model sales chart**. The curated ten-model intake is in [data/india_q3_2026_sales_priority_models.json](../data/india_q3_2026_sales_priority_models.json).
- **Q2 2026 ranked model sales:** [Counterpoint, India Top 5](https://counterpointresearch.com/en/insights/top-5-smartphone-model-share-8-countries). Its rounded market shares and source-backed evidence are in [data/india_q2_2026_reported_top5_sales_models.json](../data/india_q2_2026_reported_top5_sales_models.json). **Do not describe Q2 ranks as current November or Q3 ranks.**
- **Primary research catalogue baseline:** [data/mobile_research_catalogue.json](../data/mobile_research_catalogue.json), with 232 model cards, as compared on this audit date.

## Ten Q3 2026 market-report model references
| Model | In 232-card catalogue? | Treatment |
| --- | --- | --- |
| Samsung Galaxy A07 5G | No | Manufacturer-source research intake, not ranked |
| Samsung Galaxy A17 5G | No | Manufacturer-source research intake, not ranked |
| Samsung Galaxy A27 5G | Yes | Existing primary research card |
| vivo Y11 5G | No | Manufacturer-source research intake, not ranked |
| vivo Y21 5G | No | Manufacturer-source research intake, not ranked |
| Redmi 15A 5G | No | Manufacturer-source research intake, not ranked |
| Redmi A7 | No | Manufacturer-source research intake, not ranked |
| OPPO Reno16 5G | Yes | Existing primary research card (Omdia refers to series) |
| Apple iPhone 17 | Yes | Existing primary research card |
| POCO X8 5G | Yes | Existing primary research card; global maker source needs India variant check |

**Result:** 4/10 in original primary cards, 6/10 manufacturer-linked source-reviewed intake outside the frozen 232.

## Counterpoint Q2 2026 independently ranked five
| Rank | Model | Approx. India model sales share | In 232-card catalogue? |
| ---: | --- | ---: | --- |
| 1 | OPPO A6x 5G | 4% | **No — new documented research intake** |
| 2 | Apple iPhone 17 | 3% | Yes |
| 3 | Apple iPhone 16 | 3% | Yes |
| 4 | Samsung Galaxy M17 5G | 2% | Yes |
| 5 | vivo Y31 5G | 2% | **No — new documented research intake** |

Both absent Q2-ranked models are now recorded with Indian manufacturer specifications in the new dedicated data file. These are **not** automatically admitted to the canonical registry or recommendation engine.

## QA and release boundaries
- Preserve the original 232-card catalogue and approved ranking formula. Do not assign a price weight to scoring (budget gate only).
- Sales mention is not proof of an exact RAM/storage/colour SKU, current price, stock, authorized retailer offer, or measured camera/battery/gaming performance.
- Do not add invented retailer URLs or unverified product offers. Manufacturer specifications are evidence of claimed features, not independent performance test results.
- Promote a model into performance ranking only after source and exact-variant identity admission; publish buy buttons only after separate offer-freshness gates.
- **Deployment and live-page verification:** not established by this audit. Repository source presence alone is not proof that GitHub Pages has published a corresponding route.
