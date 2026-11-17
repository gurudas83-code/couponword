# Coupon World: API मिलने के बाद रुका काम, सुधार और वास्तविक स्थिति

तारीख: 17 नवम्बर 2026. Repository baseline: 27cb2a6d08bac7e0f8fe23d5c649a65323d86bad.
Implementation: PR #113. यह रिपोर्ट public-feature release और पूरी market coverage में अंतर रखती है।

## 1. कौन-सा बेहतर काम बीच में रुका था?

पुरानी बातचीत में लक्ष्य था: जरूरत समझना → exact model/variant → manufacturer evidence → budget eligibility → मौजूदा quality ranking → तीन retailer विकल्प और price comparison.

| पुराना काम | क्यों रुका | अब क्या किया |
| --- | --- | --- |
| Multi-retailer price/stock comparison | ताजा retailer API/offer evidence नहीं था; links प्रायः searches थे | Paid QuickCommerce responses से अलग, attributed observation display जोड़ा; पुराना comparison engine reuse किया |
| Current price और dated reference को अलग रखना | HTML/search hints को current offer समझने का खतरा | Original observation timestamp, source, pincode, stock और six-hour freshness अलग दिखती है |
| Exact variant linking | Model-level catalogue और canonical RAM/storage/color identities अलग थे | प्रत्येक listing configuration अलग; missing RAM को unknown; ऐसी entries को cross-store comparison से बाहर रखा |
| Budget-aware shopping help | Fresh price का अभाव, budget और quality score में भ्रम | Selected listed configuration के लिए optional entered price cap; quality ranking में price का 0% नियम सुरक्षित |
| Genuine price history | पुराना trustworthy chronological dataset नहीं था | उपलब्ध वास्तविक checks ही दिखते हैं; कोई काल्पनिक महीनों/वर्षों की chart history नहीं |
| TV/earbuds विस्तार | पुराने matcher को mobile RAM या title में model code चाहिए था | TV code को quantity में भी पढ़ना; reviewed exact IDs reuse करना; earbuds के exact model prefix और Pro/Plus variants अलग रखना |
| API automation | Keys/source/freshness/credit boundaries स्पष्ट नहीं थीं | Private server-side transport, bounded batches, no retry loops, checkpoint artifacts; default paid search cap zero |
| Evidence-based Best 3 | Manufacturer specs को independent lab performance समझने का जोखिम | पुराने Intent/Product DNA/Weighted Fit और purchase gates सुरक्षित; कोई नया ranker या fake performance score नहीं |

प्रमाण के लिए repository के पहले से मौजूद reports/reuse_first_integration_audit_20261113.md,
reports/full_system_competitor_reuse_audit_20261113.md और reports/ranking_quality/RANKING_BUDGET_TRUST_FINAL.md पढ़े गए।
जुलाई–नवम्बर की recovered बातचीत भी यही क्रम और no-duplicate-engine निर्देश दिखाती है। पुराने counts को आज के counts बनाकर इस्तेमाल नहीं किया गया।

## 2. Competitors में क्या उपयोगी है?

| Platform | अपनी public pages पर दिखने वाली सुविधा | Coupon World में उपयोगी अपनाव |
| --- | --- | --- |
| Smartprix | Variant selection, store prices, price history, alerts, comparison और structured specs | सही configuration चुनकर checked-store comparison; source/time और सीमाएँ स्पष्ट रखना |
| MySmartPrice | Search, multi-phone comparison, price discovery, editorial/testing content | Existing shortlist और manufacturer-linked specs के साथ price panel; fake hands-on review नहीं |
| 91mobiles | Requirement-based finder, specifications, benchmarks और expert reviews | Existing intent/filter flow सुरक्षित; independently measured evidence होने पर ही performance verdict |
| Buyhatke | Price tracking/history, alerts और store comparison | असली checks से history शुरू; alert service के लिए अलग persistent refresh/delivery व्यवस्था चाहिए |

यह feature observation है, competitor traffic/conversion का measured benchmark नहीं। उनकी private API contracts, image licenses या operating costs सार्वजनिक evidence से पूरी तरह सत्यापित नहीं हुए।

Smartprix की terms product images को owners की courtesy/license से दिखाने की बात कहती हैं। उसका उदाहरण हमें उनकी photos copy करने का अधिकार नहीं देता। Photo rights का प्रश्न price/stock observations के पूरे काम को बंद करने का कारण भी नहीं होना चाहिए।

Sources reviewed:

- https://www.smartprix.com/mobiles/samsung-galaxy-a56-ppd184axqm2x
- https://www.smartprix.com/about/terms-of-services
- https://www.smartprix.com/about/editorial-guidelines
- https://www.mysmartprice.com/compare-mobile/
- https://www.91mobiles.com/phonefinder.php
- https://www.buyhatke.com/about

## 3. API का वास्तविक उपयोग और जाँच

| Evidence run | Scope | Outcome |
| --- | --- | --- |
| 44125900899 | पुराना एक-call Flipkart smoke | API connection काम करता था; पूरी catalogue verification नहीं |
| 44131040109 | 232 mobile + 20 TV + 20 earbuds Flipkart searches | 272 calls complete; पुराना strict matcher 106 model candidates तक पहुँचा |
| 44136510667 | छोटा Amazon/Flipkart schema diagnostic | 14 searches मिले; Flipkart item endpoint पर HTTP error आया और batch रुक गया; errors छिपाए या retry नहीं किए |
| 44137680179 | 232 Amazon mobile searches + 40 TV/earbud models के दो-store searches | 312 calls complete, zero recorded errors |
| 44140236781 | पहले से reviewed 9 exact Croma TV IDs | 9 item checks सफल; unknown IDs guess नहीं किए |

QuickCommerce की अपनी documentation Amazon/Flipkart search और Croma item lookup का distinction बताती है। उसकी comparison guide mapping → item lookup → checked-store comparison का उपयोग बताती है। यह third-party API है; इसे official Flipkart affiliate feed का नाम नहीं दिया गया।

- https://quickcommerceapi.com/docs
- https://quickcommerceapi.com/terms
- https://quickcommerceapi.com/blog/compare-phone-price-croma-reliance-digital-amazon-flipkart

सभी इस release के observations pincode 110001 और inherited Delhi coordinates से हैं। यह पूरे भारत की stock/delivery guarantee नहीं। Bank/exchange offers तथा delivery charges listed-price comparison में शामिल नहीं हैं।

## 4. Final observation snapshot की coverage

| Category | Catalogue entries | Observations वाली entries | अभी unmatched |
| --- | ---: | ---: | ---: |
| Mobiles | 232 | 123 | 109 |
| TVs | 20 | 16 | 4 |
| Earbuds | 20 | 15 | 5 |
| Total | 272 | 154 | 118 |

- 800 listed configurations; 887 retailer rows: Amazon 153, Flipkart 725, Croma 9.
- 85 configurations में एक से अधिक checked stores हैं।
- Snapshot generation पर 69 configurations में कम-से-कम दो fresh, in-stock stores थे; केवल इन पर lowest observed among checked stores label संभव था।
- 20 retailer/configuration rows में एक से अधिक genuine recorded checks हैं।
- ये catalogue entries और listing configurations हैं, 154 newly verified canonical products नहीं।
- Missing RAM वाली listing में RAM not stated लिखा जाता है। अलग retailer SKUs को इस unknown dimension पर comparable नहीं माना जाता।
- Unmatched का मतलब out of stock नहीं: no search hit, नाम mismatch, ambiguous memory, missing code या insufficient identity evidence कारण हो सकते हैं।
- Quality/specification evidence, India firmware और warranty को API price response से verified नहीं बनाया गया।

## 5. क्या वास्तव में बदला?

1. मोबाइल search/detail cards में Check API price & availability button.
2. TV/earbud hub और detail pages पर वही component.
3. Listed configuration selector; model, RAM/storage/color अलग रखने का नियम.
4. Store, listed amount, stock observation, pincode, source, checked time और retailer destination.
5. Optional price-cap check: केवल चुनी configuration की रकम; recommendation/quality rank नहीं.
6. दो distinct stores और समान configuration/location की condition; एक store या दो colours को comparison नहीं गिना जाता.
7. Stale/future/missing timestamps पर fresh stock/lowest label नहीं; पुराना source time replay पर नया नहीं बनता.
8. Out-of-stock row पर payable price नहीं; unknown data को zero नहीं बनाया जाता.
9. Croma के string true/false का explicit parser: false को truthy बनाकर in stock नहीं दिखाया जाता.
10. Genuine check history; no invented price forecasts or all-time lows.
11. API key frontend में नहीं; public snapshot में images/gallery/keys/provider billing data नहीं.
12. JSON price data user action पर lazy load; पहले page load में उसकी fetch नहीं.
13. Existing Amazon tag/disclosure pipeline सुरक्षित; नए tagged destinations पर sponsored link metadata.

Reuse:

- python/quickcommerce_flipkart_adapter.py: existing private transport.
- python/build_multi_retailer_public.py: observation-to-public adapter.
- python/multi_retailer_engine.py: existing checked-store comparison; scoring code नहीं बदला.
- mobile-research-preview.js: existing cards/filter/detail path; केवल price control जुड़ा.
- python/tv_earbuds_workbook_pages.py: existing category publisher.
- scripts/build_public_pages.py: existing allowlisted artifact; एक data file जोड़ी.

## 6. शेष कमियाँ और उनके कारण

| Priority | Gap | क्यों बाकी है | अगला evidence/action |
| --- | --- | --- | --- |
| P0 | 118 entries पर admitted observations नहीं | Search coverage और exact identity/configuration gaps | Existing resolver/registry से exact retailer mappings; returned evidence की जाँच |
| P0 | Complete three-store coverage नहीं | Croma keyword search नहीं देता; exact IDs चाहिए | Reviewed product URLs से IDs; source-confirmed variant mapping |
| P0 | All-India availability नहीं | अभी एक location पर checks | Private backend से visitor pincode के लिए bounded, cached lookup |
| P0 | Paid recurring freshness schedule अभी चालू नहीं | हर refresh credits खर्च करता है; default में unlimited paid polling नहीं होना चाहिए | Priority models, explicit credit cap और permitted refresh cadence तय करके activate करना |
| P1 | Quality ranking के लिए broad independent tests नहीं | Manufacturer specifications real-world test नहीं हैं | Existing evidence ledger में comparable protocol/India variant वाले tests जोड़ना |
| P1 | Photos में gaps | Existing 58 photo references हैं; 174 mobile cards में photo नहीं; new image references licensed नहीं मानी गईं | Exact-model visuals + documented reusable license/permission |
| P1 | Long price history और price-drop alerts नहीं | आज collected checks से सालभर का dataset नहीं बनता | Persistent dated collection; user alert preferences और delivery service |
| P1 | Complete canonical commerce admission नहीं | API listed identity, manufacturer identity और fresh purchasable evidence अलग हैं | Existing live-offer gate की requirements पूरी करना; उसे bypass नहीं करना |
| P2 | Search traffic/AI visibility की actual measurement | SEO build पास होना Google indexing/traffic का प्रमाण नहीं | GSC indexing/query reports और observed clicks; no fake indexing claims |
| P2 | Render shopping API parity | इस release में static Pages observations बदलीं; shopping backend untouched | Separate health/revision and live query evidence before claiming API deployment parity |

इन gaps को code से data invent करके बंद नहीं किया गया। वर्तमान search API responses complete manufacturer specification sheets या comparable lab measurements नहीं देते; specs के लिए पुराने official-source modules ही सही रास्ता हैं।

## 7. Product direction और market position

अगला मजबूत product: जरूरत खोजें → source-linked specs पढ़ें → configuration चुनें → checked-store price/stock और genuine history देखें → retailer पर अंतिम जाँच करें।

हमारी उपयोगी दिशा transparent evidence और exact configuration है। अभी पूरे market में competitors से आगे होने का प्रमाण नहीं है: coverage, first-hand reviews, long history और distribution में gap है। केवल photos या pages की संख्या बढ़ाकर यह gap नहीं भरता।

पहले existing top-30 priorities की exact-store mapping और refresh coverage मजबूत करना बेहतर है। Core ranking formula, price का 0% quality weight और useful SEO pages सुरक्षित रहते हैं। Mass thin SEO generation या another shopping brain इस release का हिस्सा नहीं है।

## 8. Validation और release evidence

- 43 focused local tests pass: original adapters, wrong models/Pro variants, RAM/storage/color separation, unknown RAM, numeric/type errors, stock states, Croma IDs/false string, source times/history, URL safety and ranking/publication contracts.
- Windows temporary-directory permissions blocked one legacy route test locally; it runs unchanged in Linux CI. It was not disabled.
- Existing five CI gates plus new price UI Chromium journey required before merge.
- Browser journey covers 390px and 1440px: lazy load, model search, configuration selection, budget cap, TV page, no new images, no document overflow, stale fallback.
- Existing recommendation weights/thresholds, quality scorer, canonical catalogue and authorized-offer store unchanged.
- Canonicals/robots/indexability policies and retired thin pages remain under existing SEO checks.
- PR: https://github.com/gurudas83-code/couponword/pull/113

Release conclusion: useful API-backed comparison display is now implementable and tested. Complete market coverage, perpetual freshness and independently benchmarked Best 3 are separate evidence/operations tasks, and are not falsely certified by this release.
