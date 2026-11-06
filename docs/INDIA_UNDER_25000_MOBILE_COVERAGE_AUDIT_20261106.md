# Coupon World — India mobile shortlist under ₹25,000
**Audited:** 6 November 2026 · **Repository:** gurudas83-code/couponword

## What was checked
- Primary: [Gadgets 360's 21-phone editorial picks](https://www.gadgets360.com/mobiles/best-phone-under-25000) (reference prices dated 5 November 2026).
- Four additional phones: Motorola Moto G57 Power, Lava Virat Curve 5G (both [91mobiles' tested list](https://www.91mobiles.com/reviews/best-phones-under-25000/), prices dated 12 October), plus Samsung Galaxy F70 Pro 5G and OPPO K13 5G ([Smartprix November listings](https://www.smartprix.com/mobiles/price-below_25000/)).
- Compared exact manufacturer/model identity against the untouched 232-model [primary research catalogue](../data/mobile_research_catalogue.json). Suffix, family and storage distinctions were *not* silently treated as equivalent.
- Machine-readable per-model snapshot: [data/india_under_25000_editorial_coverage_20261106.json](../data/india_under_25000_editorial_coverage_20261106.json).

## Count reconciliation
| Dataset | Models inspected | Already in original 232 cards | Missing primary research model card |
| --- | ---: | ---: | ---: |
| Gadgets 360 editorial list | 21 | 8 | 13 |
| Four additional editorial models | 4 | 2 | 2 |
| **Total** | **25** | **10** | **15** |

These **15 previously absent identities have been registered as research candidates** in the new structured data file. This does not automatically add them to the 232-card primary catalogue, authorize a retailer offer, or make them visible in the shopping recommendation route.

### Existing primary model cards
POCO X7 Pro 5G; POCO M8 Power 5G; OnePlus N6 5G; Redmi Note 15 5G; Infinix GT 30 Pro; Motorola Edge 60 Fusion; Nothing Phone (3a); Samsung Galaxy A36 5G; Samsung Galaxy F70 Pro 5G; OPPO K13 5G.

### Missing primary model cards / intake
Infinix Hot 70 Pro 5G+; Motorola Moto G Max; Infinix Note Edge; POCO M8 5G; Nothing Phone (3a) Lite; OnePlus Nord CE5; vivo T4 5G; iQOO Neo 10R; realme P3 Pro 5G; realme 14 Pro+ 5G; Tecno Pova Slim 5G; realme 15T; Samsung Galaxy A26 5G; Motorola Moto G57 Power; Lava Virat Curve 5G.

**Identity warning:** The original catalogue has an Infinix Hot 70 Pro 5G card, but the third-party reference uses “Hot 70 Pro 5G+” while the [India manufacturer's product naming](https://infinixmobiles.in/products/hot-70-pro) is simply “Hot 70 Pro”. An alias or SKU admission must be confirmed before collapsing these.

## Editorial choices for readers — not Coupon World's approved weighted rankings
- **Gaming/performance:** POCO X7 Pro 5G 8GB+256GB. [Flipkart product listing](https://www.flipkart.com/poco-x7-pro-5g-obsidian-black-256-gb/p/itm83a82908d7dbb?ov_redirect=true) displayed ₹23,999 on this research date; maker [global specs](https://www.mi.com/global/product/poco-x7-pro/specs/) list Dimensity 8400-Ultra. Exact sale, region, stock and delivery must be rechecked.
- **Camera / optical zoom:** Nothing Phone (3a), source: [Nothing India](https://in.nothing.tech/products/phone-3a), lists a 50MP OIS main and 50MP telephoto. The under-₹25k price depends on the exact merchant variant.
- **Battery/performance:** OnePlus Nord CE5, currently **missing from primary catalogue**; [OnePlus India](https://www.oneplus.in/nord-ce5) lists 7,100mAh battery and Dimensity 8350 Apex, from ₹24,999.
- **Battery overall:** POCO M8 Power 5G, present in primary catalogue; [91mobiles](https://www.91mobiles.com/reviews/best-phones-under-25000/) selects this as its October overall choice and gives a 6GB/128GB ₹22,999 indicative starting price.
- **Battery/camera value:** Motorola Moto G57 Power, missing; [Motorola India](https://www.motorola.in/smartphones-moto-g57-power-5g/p?skuId=602) lists Snapdragon 6s Gen 4 and 7,000mAh. [91mobiles](https://www.91mobiles.com/reviews/best-phones-under-25000/) Oct category choice at ₹21,999.
- **Long software support:** Samsung Galaxy A36 5G, present; [Samsung India specs](https://www.samsung.com/in/smartphones/galaxy-a/galaxy-a36-5g-awesome-black-128gb-sm-a366ezkjins/) list six OS upgrades and six years security. **Price conflict:** editorial list reports ₹24,999, whereas [Samsung direct storefront](https://www.samsung.com/in/smartphones/galaxy-a36/buy/) displayed ₹31,999 for 8GB/128GB. It cannot be treated as reliably under budget without a dated qualifying retailer offer.
- **Design/display:** Motorola Edge 60 Fusion, present; [Motorola India](https://www.motorola.in/smartphones-motorola-edge-60-fusion/p?skuId=488), but current manufacturer prices may exceed the budget.

## Guardrails
1. Original 232-card research catalogue, canonical Product DNA, recommendation engine, and official ranking weights are unchanged.
2. All third-party prices are dated **indicative budget evidence only**; they must not change performance scoring (price weight 0%). No current retailer price, stock, affiliate tracking, buy CTA or exact-variant admission is certified by this intake.
3. Never substitute “Hot 70 Pro” for “Hot 70 Pro 5G+”, “vivo T4x” for “vivo T4”, “iQOO Neo 10” for “Neo 10R”, or “POCO M8 Power” for “POCO M8”.
4. Next admission actions: India manufacturer page → exact RAM/storage/manufacturer SKU → independent performance evidence → dated Amazon/Flipkart/Croma variant-specific seller links → editorial and automated regression gates → publish to primary catalogue if compliant.
5. Actual production deploy, live storefront prices, and browser QA are **not established** by this repository-only audit.
