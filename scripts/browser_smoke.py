#!/usr/bin/env python3
"""End-to-end smoke test of the *generated public site*, not a mocked DOM.

Requires: pip install playwright && python -m playwright install chromium
Runs against a loopback static server with controlled offer and API responses.
"""
from __future__ import annotations

import argparse
import contextlib
import functools
import http.server
import json
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright


def run(root: Path):
    root = root.resolve()
    if not (root / "index.html").is_file():
        raise FileNotFoundError(root / "index.html")

    class SilentHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    handler = functools.partial(SilentHandler, directory=str(root))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}/"
    results = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
            try:
                for width in (390, 768, 1440):
                    page = browser.new_page(viewport={"width": width, "height": 900})
                    page_errors = []
                    page.on("pageerror", lambda error: page_errors.append(str(error)))
                    # Tracking, not the application, is excluded from deterministic QA.
                    page.route("https://www.googletagmanager.com/**", lambda route: route.abort())
                    pending_offers = []
                    page.route("**/api/recommend?*", lambda route: pending_offers.append(route))
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    # New visitors have a clear way to browse, compare and reach retailers.
                    assert page.locator("#howToShop").is_visible(), width
                    assert "Tap the phone photo" in page.locator("#howToShop").inner_text(), width
                    assert page.locator(".cw-primary-actions a").count() == 5, width
                    assert page.locator('.cw-primary-actions a[href="/phones/new-india-mobiles/"]').count() == 1, width
                    assert page.locator('.cw-primary-actions a[href="/seo/top-30-phone-research-india.html"]').count() == 1, width
                    primary_shortcuts = (10000, 15000, 20000, 25000, 30000)
                    assert page.locator(".mobile-budget-chips [data-mobile-query]").count() == 5, width
                    for cap in primary_shortcuts:
                        assert page.locator(
                            f'.mobile-budget-chips [data-mobile-query="mobile under {cap}"]'
                        ).is_visible(), (width, cap)
                    assert page.locator(".cw-budget-more").count() == 0, width
                    assert page.locator("#researchCategories").evaluate(
                        "(el) => !!(el.compareDocumentPosition(document.getElementById('mobileResearchSearch')) & Node.DOCUMENT_POSITION_FOLLOWING)"
                    ), width
                    page.wait_for_function("() => !!window.CouponWorldMobileResearch", timeout=15000)
                    # First-party chat must answer via the published local catalogues,
                    # without a paid AI API or changing the existing mobile search.
                    page.wait_for_function(
                        "() => !!window.CouponWorldAssistant && !!window.CouponWorldAssistantCore && !!window.CouponWorldQueryParser",
                        timeout=15000,
                    )
                    assistant_form = page.locator("#cwAssistantForm")
                    assert not assistant_form.is_visible(), width
                    page.locator("#cwAssistant > summary").click()
                    assert assistant_form.is_visible(), width
                    page.locator("#cwAssistantInput").fill("55 inch Xiaomi TV")
                    page.locator('#cwAssistantForm button[type="submit"]').click()
                    page.wait_for_function(
                        "() => document.querySelector('#cwAssistantMessages').innerText.includes('Xiaomi')",
                        timeout=12000,
                    )
                    page.locator("#cwAssistantMessages .cw-assistant-bot").last.locator('a[href^="https://"]').first.wait_for(timeout=12000)
                    affiliate = page.locator("#cwAssistantMessages .cw-assistant-bot").last.locator('a[href*="amazon.in"]').first
                    affiliate.wait_for(timeout=12000)
                    assert "tag=guru07cc-21" in affiliate.get_attribute("href"), width
                    assert "sponsored" in affiliate.get_attribute("rel"), width
                    label = affiliate.inner_text().lower()
                    assert "matched model listing" in label or "search amazon" in label, (width, label)
                    if "search amazon" in label:
                        assert "not an exact listing" in label, (width, label)
                    assert "research" in page.locator("#cwAssistantMessages .cw-assistant-bot").last.inner_text().lower(), width
                    assert page.evaluate("document.documentElement.scrollWidth") <= width + 8, width
                    # Wait for the real fetch->catalogue->browser filtering chain.
                    page.wait_for_function(
                        "() => window.CouponWorldMobileResearch.search('phone under 30000').length > 0",
                        timeout=20000,
                    )
                    # Top 3 must never invent 3 winners, exceed the correct
                    # ₹5k band or include price-unknown phones among ranked picks.
                    for cap in (10000, 15000, 20000, 25000, 30000):
                        top3 = page.evaluate("""cap => {
                            const t0=performance.now();
                            const matches=window.CouponWorldMobileResearch.search('top 3 mobile under '+cap);
                            const elapsed=performance.now()-t0;
                            const tier=document.querySelector('#mobileResearchResults .research-verified-top3');
                            const picks=[...document.querySelectorAll('#mobileResearchResults .research-top3-result')];
                            return {
                                elapsed, count:picks.length, matched:matches.length,
                                text:tier?.innerText||'',
                                prices:matches.map(x=>x.card.research_budget_reference?.reference_price_inr),
                                keys:matches.map(x=>x.card.model_key)
                            };
                        }""", cap)
                        assert top3['count'] <= 3, (width, cap, top3)
                        assert top3['elapsed'] < 1000, (width, cap, top3['elapsed'])
                        assert 'Research-Verified' in top3['text'], (width, cap)
                        assert 'current price' in top3['text'].lower() or 'current stock' in top3['text'].lower(), (width, cap)
                        print('TOP3_BUDGET_AUDIT', width, cap, json.dumps({
                            'ranked':top3['count'], 'strict_matches':top3['matched'],
                            'local_js_ms':round(top3['elapsed'],1)
                        }), flush=True)

                    # Corrupted saved evidence must not qualify in Top 3 or
                    # ordinary budget filters; restore the record each time.
                    gated = page.evaluate("""() => {
                        const query='phone under 15000';
                        const before=window.CouponWorldMobileResearch.search(query);
                        if(!before.length)return {error:'no dated references'};
                        const item=before[0].card, ref=item.research_budget_reference;
                        const original={...ref};
                        const tests=[
                            ['missing date',{checked_at:''}],
                            ['expired evidence',{checked_at:'not-a-date'}],
                            ['ranking weight',{ranking_weight:0.5}],
                            ['sold out',{stock_indication:'OUT_OF_STOCK'}],
                            ['no offer distinction',{live_offer:true}],
                            ['string price',{reference_price_inr:'12999'}]
                        ];
                        const result=[];
                        try {
                            for(const [name,patch] of tests){
                                Object.keys(ref).forEach(k=>delete ref[k]);
                                Object.assign(ref,original,patch);
                                const ranked=window.CouponWorldMobileResearch.search('top 3 '+query);
                                const budget=window.CouponWorldMobileResearch.search(query);
                                result.push({name,excluded:!budget.some(x=>x.card.model_key===item.model_key),
                                    excludedFromTop3:!ranked.some(x=>x.card.model_key===item.model_key)});
                            }
                        } finally {
                            Object.keys(ref).forEach(k=>delete ref[k]);
                            Object.assign(ref,original);
                        }
                        return {result};
                    }""")
                    assert 'error' not in gated, (width, gated)
                    assert all(row['excluded'] and row['excludedFromTop3'] for row in gated['result']), (width, gated)
                    # Market additions are searchable alongside the core models.
                    page.wait_for_function(
                        "() => window.CouponWorldMobileResearch.search('OPPO A6x 5G').some("
                        "item => item.card.model_key === 'oppo|a6x 5g' && item.card.market_intake === true)",
                        timeout=20000,
                    )
                    a6 = page.locator("#mobileResearchResults [data-mobile-model-card='oppo|a6x 5g']")
                    assert a6.count() == 1, width
                    assert "current price and availability with the retailer" in a6.inner_text(), width
                    assert a6.locator('a[aria-label="Search Amazon"]').count() == 1, width
                    assert a6.locator('a[aria-label="Search Flipkart"]').count() == 1, width
                    assert "Search Croma" in a6.inner_text(), width
                    assert page.evaluate(
                        "() => window.CouponWorldMobileResearch.search('Samsung Galaxy A07 5G').some("
                        "item => item.card.model_key === 'samsung|galaxy a07 5g' && item.card.market_intake === true)"
                    ), width
                    # Verify all 21 research additions actually appear after fetch.
                    page.wait_for_function(
                        "() => !!document.querySelector('#mobileResearchNew') && "
                        "!document.querySelector('#mobileResearchNew').hidden && "
                        "document.querySelector('#mobileResearchNewCount').textContent.includes('21 recently added phones')",
                        timeout=20000,
                    )
                    assert page.locator("#mobileResearchNewGrid [data-mobile-model-card]").count() == 21, width
                    assert page.locator(".hero-stats strong").all_text_contents() == ["253", "247", "20"], width
                    assert page.locator("#mobileResearchNewGrid a.research-model-name-link").count() == 21, width
                    more_phones = page.locator("#mobileResearchNewGrid details.recent-mobile-more")
                    more_phones.evaluate("details => { details.open = true; }")
                    new_cards = page.locator("#mobileResearchNewGrid [data-mobile-model-card]")
                    for card in new_cards.all():
                        image = card.locator(
                            "img[src^='/assets/phone-photos/'], "
                            "img[src^='/assets/phone-illustrations/'], "
                            "img[src^='/assets/new-mobile-art/']"
                        )
                        assert image.count() == 1, width
                        assert image.evaluate("img => img.getBoundingClientRect().height") >= 180, width
                        assert card.locator("h3").evaluate(
                            "heading => parseFloat(getComputedStyle(heading).fontSize)"
                        ) >= 20, width
                        src = image.get_attribute("src") or ""
                        text = card.text_content() or ""
                        if src.startswith("/assets/phone-photos/"):
                            assert "Model photo:" in text, width
                        elif src.startswith("/assets/phone-illustrations/"):
                            assert "AI illustration" in text, width
                    more_phones.evaluate("details => { details.open = false; }")
                    assert "Price unavailable" in page.locator("#mobileResearchNewGrid").text_content(), width
                    assert page.evaluate(
                        "() => window.CouponWorldMobileResearch.search('Samsung Galaxy F70 5G').some("
                        "item => item.card.model_key === 'samsung|galaxy f70 5g' && item.card.market_intake === true)"
                    ), width
                    page.evaluate("window.CouponWorldMobileResearch.search('phone under 30000')")
                    assert page.locator("#mobileResearchResults [data-mobile-model-card]").count() > 0, width
                    assert page.locator("#mobileResearchResults").is_visible(), width
                    research_text = page.locator("#mobileResearchResults").text_content() or ""
                    visible_text = page.locator("#mobileResearchResults").inner_text()
                    print("RESEARCH-DIAGNOSTIC", width, "DOM:", repr(research_text[:180]), "visible:", repr(visible_text[:180]), flush=True)
                    assert "Research only" in research_text, width
                    assert page.locator("#browse").is_hidden(), width
                    assert page.locator("#hot-deals").is_hidden(), width
                    assert "Browse Hot Deals" not in page.content(), width

                    # Hold the offer request while proving local results render.
                    page.locator("#heroSearch").fill("phone under 25000")
                    with page.expect_request("**/api/recommend?*"):
                        research_visible_ms = page.evaluate("""() => new Promise(resolve => {
                            const started = performance.now();
                            document.getElementById("heroSearchButton").click();
                            requestAnimationFrame(() => requestAnimationFrame(
                                () => resolve(performance.now() - started)
                            ));
                        })""")
                    print(f"Search click to next painted frame at {width}px: {research_visible_ms:.1f} ms", flush=True)
                    assert research_visible_ms < 300, (width, research_visible_ms)
                    # Both budget lanes are painted from already-loaded local
                    # research while the API request is deliberately held.
                    assert page.locator("#mobileResearchResults .research-budget-evidenced").is_visible(), width
                    assert page.locator("#mobileResearchResults .research-budget-unpriced").is_visible(), width
                    assert page.locator("#mobileResearchResults .research-budget-primary-grid [data-mobile-model-card]").count() > 0, width
                    assert page.locator("#mobileResearchResults .research-budget-related-item").count() > 0, width
                    assert "price not verified" in page.locator("#mobileResearchResults .research-budget-unpriced").inner_text().lower(), width
                    assert not page.locator("#mobileResearchResults .research-budget-unpriced .purchase-cta").count(), width
                    assert page.locator("#mobileResearchResults [data-mobile-model-card]").count() > 0, width
                    assert page.locator("#aiRecommendation").is_hidden(), width
                    pending_offers.pop().fulfill(status=503, headers={"Access-Control-Allow-Origin": "*"})
                    assert page.locator("#mobileResearchResults [data-mobile-model-card]").first.is_visible(), width
                    assert page.locator("#aiRecommendation").is_hidden(), width
                    page.unroute("**/api/recommend?*")
                    page.route("**/api/recommend?*", lambda route: route.fulfill(
                        json={"recommendations": [
                            {"title": "Unverified fixture", "current_offer_verified": False},
                            {"title": "Verified offer fixture", "current_offer_verified": True,
                             "purchase_cta_eligible": True, "retailer_offers": [{
                                 "retailer": "flipkart", "price": 14999, "availability": "in_stock",
                                 "product_url": "https://www.flipkart.com/test/p/itmfixture",
                                 "cta_eligibility": {"eligible": True},
                             }]},
                        ]},
                        headers={"Access-Control-Allow-Origin": "*"},
                    ))
                    page.locator("#heroSearchButton").click()
                    page.locator("#aiRecommendation").wait_for(state="visible", timeout=10000)
                    assert "Verified offer fixture" in page.locator("#aiRecommendation").inner_text(), width
                    assert "Unverified fixture" not in page.locator("#aiRecommendation").inner_text(), width
                    assert page.locator("#mobileResearchResults [data-mobile-model-card]").first.is_visible(), width
                    page.locator("#researchClearSearch").click()
                    assert page.locator("#aiRecommendation").is_hidden(), width
                    page.unroute("**/api/recommend?*")
                    page.route("**/api/recommend?*", lambda route: route.fulfill(
                        json={"recommendations": []}, headers={"Access-Control-Allow-Origin": "*"}
                    ))
                    # Regression: exact-model, brand exclusion and memory hard
                    # constraints are also preserved for price-unverified leads.
                    elapsed_ms = page.evaluate("""() => {
                      const started = performance.now();
                      window.CouponWorldMobileResearch.search('Samsung Galaxy F70 5G under 25000');
                      return performance.now() - started;
                    }""")
                    assert elapsed_ms < 1000, (width, elapsed_ms)
                    related_text = page.locator("#mobileResearchResults .research-budget-unpriced").inner_text()
                    assert "galaxy f70 5g" in related_text.lower(), (width, related_text[:400])
                    assert "Price not verified" in related_text, width
                    assert not page.locator("#mobileResearchResults .research-budget-primary-grid [data-mobile-model-card]").count(), (
                        width,
                        page.locator("#mobileResearchResults .research-budget-primary-grid [data-mobile-model-card]").evaluate_all(
                            "(nodes) => nodes.map(n => ({ key: n.dataset.mobileModelCard, text: n.innerText.slice(0,120) }))"
                        )
                    )
                    page.evaluate("window.CouponWorldMobileResearch.search('Samsung Galaxy F70 5G 8GB RAM under 30000')")
                    assert not page.locator("#mobileResearchResults .research-budget-related-item").count(), width
                    page.evaluate("window.CouponWorldMobileResearch.search('phone under 30000 exclude Samsung')")
                    assert not any("Samsung" in name for name in page.locator(
                        "#mobileResearchResults .research-budget-related-item>strong"
                    ).all_inner_texts()), width
                    page.evaluate("window.CouponWorldMobileResearch.search('phone under 30000')")

                    # Ordinary under-budget searches now default to strict previous-₹5k windows.
                    nearby = page.evaluate("""() => window.CouponWorldMobileResearch.search('phone under 30000 nearby band').map(x => x.card.research_budget_reference.reference_price_inr)""")
                    assert nearby and all(25000 <= price < 30000 for price in nearby), width
                    # Full-budget is an explicit opt-in exception, not the default.
                    details = page.locator("details.research-guided-search")
                    details.locator("summary").click()
                    page.locator("#researchGuidedBudget").select_option("30000")
                    page.locator("#researchGuidedScope").select_option("all")
                    page.locator("#researchGuidedApply").click()
                    assert "full budget" in page.locator("#mobileResearchQuery").input_value(), width
                    expanded = page.evaluate("""() => window.CouponWorldMobileResearch.search('phone under 30000 full budget').map(x => x.card.research_budget_reference.reference_price_inr)""")
                    assert len(expanded) > len(nearby), width
                    assert all(0 < price < 30000 for price in expanded), width
                    assert any(price < 25000 for price in expanded), width
                    ordinary = page.evaluate("() => window.CouponWorldMobileResearch.search('phone under 30000').map(x => x.card.model_key)")
                    full = page.evaluate("() => window.CouponWorldMobileResearch.search('phone under 30000 full budget').map(x => x.card.model_key)")
                    assert ordinary == page.evaluate("() => window.CouponWorldMobileResearch.search('phone under 30000 nearby band').map(x => x.card.model_key)"), width
                    assert ordinary != full, width

                    # Exercise all 40 five-thousand-rupee public budget filters using the generated catalogue.
                    # These are dated references, not live retailer prices or buy claims.
                    # Stub unrelated backend recommendations while testing chip click handlers.
                    page.route("**/api/recommend?*", lambda route: route.fulfill(
                        status=503, headers={"Access-Control-Allow-Origin": "*"}))
                    budget_audit = []
                    previous_keys = set()
                    for limit in range(5000, 200001, 5000):
                        # Only five buttons are prominent. Other bands remain
                        # fully accessible through the advanced budget selector.
                        button = page.locator(
                            f'.mobile-budget-chips [data-mobile-query="mobile under {limit}"]'
                        )
                        assert page.locator(f'#researchGuidedBudget option[value="{limit}"]').count() == 1, (width, limit)
                        if limit in primary_shortcuts:
                            assert button.count() == 1, (width, limit)
                            button.evaluate("(el) => el.click()")
                            expected_query = f"mobile under {limit}"
                        else:
                            assert button.count() == 0, (width, limit)
                            page.locator("#researchGuidedBudget").select_option(str(limit))
                            page.locator("#researchGuidedScope").select_option("band")
                            page.locator("#researchGuidedApply").evaluate("(el) => el.click()")
                            expected_query = f"phone under {limit} nearby band"
                        assert page.locator("#heroSearch").input_value() == expected_query, (width, limit)
                        if limit in primary_shortcuts:
                            # Quick buttons intentionally target local Research Top 3.
                            assert page.locator("#mobileResearchResults .research-verified-top3").count() == 1, (width, limit)
                            assert "research picks" in page.locator("#mobileResearchSearchStatus").inner_text(), (width, limit)
                            # The 40-band audit below exercises the ordinary two-lane budget query.
                            page.evaluate("(limit) => window.CouponWorldMobileResearch.search('phone under ' + limit)", limit)
                        assert "dated budget-reference matches" in page.locator("#mobileResearchSearchStatus").inner_text(), (width, limit)
                        measure = page.evaluate("""limit => {
                          const matches = window.CouponWorldMobileResearch.search('phone under ' + limit);
                          const prices = matches.map(item => Number(item.card.research_budget_reference.reference_price_inr));
                          const names = matches.map(item => [item.card.brand, item.card.model].join(' '));
                          const keys = matches.map(item => item.card.model_key);
                          const heading = document.querySelector('#mobileResearchResults .research-budget-evidenced h3')?.textContent || '';
                          const status = document.getElementById('mobileResearchSearchStatus')?.textContent || '';
                          const related = document.querySelectorAll('#mobileResearchResults .research-budget-related-item').length;
                          const rendered = document.querySelectorAll('#mobileResearchResults .research-budget-primary-grid [data-mobile-model-card]').length;
                          return {
                            limit, count: matches.length, min_reference: prices.length ? Math.min(...prices) : null,
                            max_reference: prices.length ? Math.max(...prices) : null,
                            invalid_references: prices.filter(price => !(price >= limit - 5000 && price < limit)).length,
                            keys, sample_names: names.slice(0, 5), related_unverified_preview: related,
                            rendered_cards_initial: rendered, heading, status
                          };
                        }""", limit)
                        assert measure["invalid_references"] == 0, (width, limit, measure)
                        assert len(measure["keys"]) == len(set(measure["keys"])), (width, limit, measure)
                        assert previous_keys.isdisjoint(set(measure["keys"])), (width, limit, "overlapping adjacent ₹5k budgets")
                        assert str(measure["count"]) in measure["heading"], (width, limit, measure["heading"])
                        assert "below ₹" in measure["status"], (width, limit, measure["status"])
                        assert measure["rendered_cards_initial"] <= measure["count"], (width, limit)
                        previous_keys = set(measure["keys"])
                        del measure["keys"]
                        budget_audit.append(measure)
                        print("BUDGET_FILTER_AUDIT", width, json.dumps(measure, ensure_ascii=False), flush=True)
                    # Select each guided budget and actually click the Apply action.
                    for cap in range(5000, 200001, 5000):
                        page.locator("#researchGuidedBudget").select_option(str(cap))
                        page.locator("#researchGuidedScope").select_option("band")
                        page.locator("#researchGuidedApply").evaluate("(el) => el.click()")
                        assert page.locator("#heroSearch").input_value() == f"phone under {cap} nearby band", (width, cap)
                        expected_count = next(a["count"] for a in budget_audit if a["limit"] == cap)
                        assert page.locator("#mobileResearchSearchStatus").inner_text().startswith(
                            f"{expected_count} dated budget-reference matches"
                        ), (width, cap)
                    page.unroute("**/api/recommend?*")
                    page.evaluate("window.CouponWorldMobileResearch.search('phone under 30000')")
                    # Identity-only research is never mistaken for a valid budget match.
                    page.evaluate("window.CouponWorldMobileResearch.search('Infinix 5G mobile 10k ke andar')")
                    identity_text = page.locator("#mobileResearchResults .research-identity-only").inner_text().lower()
                    assert "verification pending" in identity_text, (width, identity_text[:300])
                    assert "not budget-qualified" in identity_text, width
                    assert not page.locator("#mobileResearchResults .research-identity-only .purchase-cta").count(), width
                    page.evaluate("window.CouponWorldMobileResearch.search('exact model Smart 8 HD phone under 25000')")
                    # The exact identity may already qualify for the source-linked
                    # unpriced lane, in which case it must NOT repeat in identity-only.
                    related_names = page.locator(
                        "#mobileResearchResults .research-budget-unpriced .research-budget-related-item strong, "
                        "#mobileResearchResults .research-identity-only .research-budget-related-item strong"
                    ).all_inner_texts()
                    assert any("Smart 8 HD" in name for name in related_names), (width, related_names)
                    assert all("GT 30 Pro" not in name for name in related_names), (width, related_names)
                    assert sum("Smart 8 HD" in name for name in related_names) == 1, (width, related_names)
                    page.evaluate("window.CouponWorldMobileResearch.search('Samsung nahi chahiye phone under 8000')")
                    assert "Samsung" not in page.locator("#mobileResearchResults .research-identity-only").inner_text(), width
                    page.evaluate("window.CouponWorldMobileResearch.search('exact model Unknown Phantom 888 phone under 25000')")
                    assert not page.locator("#mobileResearchResults .research-identity-only").count(), width
                    # Exact brand exclusion must survive mixed-language searches.
                    excluded = page.evaluate("""() => window.CouponWorldMobileResearch.search(
                        'phone under 30000 exclude samsung'
                    ).map(item => String(item.card.brand).toLowerCase())""")
                    assert all(brand != 'samsung' for brand in excluded), (width, excluded)
                    # No invented recommendation when a nonsensical exact variant is requested.
                    impossible = page.evaluate("""() => window.CouponWorldMobileResearch.search(
                        'Galaxy A36 99GB RAM 9999GB storage'
                    ).length""")
                    assert impossible == 0, (width, impossible)
                    # Research results must disclose their nature rather than claim a tested winner.
                    page.evaluate("window.CouponWorldMobileResearch.search('best camera phone under 30000')")
                    response_text = page.locator("#mobileResearchResults").inner_text().lower()
                    assert "research coverage" in response_text, (width, response_text[:400])
                    assert "performance-based recommendation" in response_text, width

                    # Priority answers are evidence-limited, not synthetic benchmark rankings.
                    priority_cautions = {
                        "camera": "megapixels alone do not establish photo quality",
                        "battery": "capacity is not measured battery life",
                        "gaming": "chipset names alone do not establish sustained fps",
                        "software": "an update promise is not the remaining support period",
                        "reliability": "an ip rating does not establish drop resistance",
                    }
                    for priority, caution in priority_cautions.items():
                        count = page.evaluate("""priority => window.CouponWorldMobileResearch.search(
                            'best ' + priority + ' phone under 30000'
                        ).length""", priority)
                        assert count > 0, (width, priority, 'no research results')
                        priority_text = page.locator("#mobileResearchResults").inner_text().lower()
                        assert caution in priority_text, (width, priority, priority_text[:500])
                        assert "research coverage" in priority_text, (width, priority)
                        assert "check eligible recommendations" in priority_text, (width, priority)
                        assert "decision evidence checklist" in priority_text, (width, priority)
                        assert "source linked" in priority_text or "not source-confirmed" in priority_text, (width, priority)
                        assert "not a measured performance verdict" in priority_text, (width, priority)


                    page.evaluate("window.CouponWorldMobileResearch.search('Galaxy A36 8GB 256GB')")
                    names = page.locator("#mobileResearchResults [data-mobile-model-card]")
                    assert names.count() == 1, f"{width}: exact-variant result count {names.count()}"
                    assert "8GB RAM" in names.first.inner_text(), width
                    assert "256GB storage" in names.first.inner_text(), width
                    photo = names.first.locator("figure.research-phone-photo")
                    assert photo.locator("img").get_attribute("src") == "/assets/phone-photos/samsung-galaxy-a36-5g.jpg", width
                    assert photo.locator("figcaption a").count() == 2, width
                    assert page.request.get(url + "assets/phone-photos/samsung-galaxy-a36-5g.jpg").ok, width
                    # Existing product image opens the same-page model details,
                    # exposes all three retailer choices, and toggles closed.
                    trigger = photo.locator("button.research-photo-open")
                    assert trigger.count() == 1, width
                    assert "Galaxy A36" in trigger.get_attribute("aria-label"), width
                    assert trigger.get_attribute("aria-expanded") == "false", width
                    assert "Tap photo to see retailer choices" in photo.locator("figcaption").inner_text(), width
                    trigger.click()
                    panel = photo.locator(".research-photo-retailer-panel")
                    assert panel.is_visible(), width
                    retailer_choices = panel.locator(".retailer-search-links")
                    assert "View saved price & stock checks" in panel.inner_text(), width
                    for retailer in ("Flipkart", "Amazon", "Croma"):
                        assert retailer in retailer_choices.inner_text(), (width, retailer)
                    assert "Search Croma for this model" in retailer_choices.inner_text(), width
                    assert panel.locator(".shop-button,.purchase-cta").count() == 0, width
                    assert trigger.get_attribute("aria-expanded") == "true", width
                    assert page.url == url, width
                    panel.locator("[data-research-detail]").click()
                    detail = page.locator("#mobileResearchDetail")
                    assert detail.is_visible(), width
                    assert page.locator("#mobileResearchDetailContent details.mobile-research-model-details").get_attribute("open") is not None, width
                    assert page.url.startswith(url + "#mobileResearchDetail/"), width
                    trigger.click()
                    assert panel.count() == 0, width
                    assert trigger.get_attribute("aria-expanded") == "false", width
                    variants = page.evaluate("""() => window.CouponWorldMobileResearch.search(
                        'OnePlus 13 24GB RAM 1TB storage'
                    ).map(item => item.card.model_key)""")
                    assert variants == ["oneplus|13"], (width, variants)

                    page.evaluate("window.CouponWorldMobileResearch.search('Galaxy A36 vs Galaxy A56')")
                    assert page.locator("#mobileResearchCompare table").count() == 1, width
                    assert "no performance winner" in page.locator("#mobileResearchCompare").inner_text().lower(), width
                    saved = page.evaluate("() => JSON.parse(localStorage.getItem('cw-saved-phone-shortlist-v1'))")
                    assert len(saved) == 2, (width, saved)
                    assert page.locator("#researchSavedShortlist").is_visible(), width
                    # Reload the same origin to verify persistent selection
                    # even when all document/JS state is reconstructed.
                    page.reload(wait_until="domcontentloaded", timeout=30000)
                    page.locator("#researchSavedShortlist").wait_for(state="visible", timeout=20000)
                    assert page.locator("#mobileResearchCompare table").count() == 1, width
                    assert "2/3" in page.locator("#researchSavedShortlist").inner_text(), width
                    page.locator("[data-research-compare-clear]").click()
                    assert page.evaluate("() => localStorage.getItem('cw-saved-phone-shortlist-v1')") is None, width
                    assert page.locator("#researchSavedShortlist").is_hidden(), width

                    page.evaluate(
                        """() => {
                          window.__handedOff = null;
                          window.CouponWorldShoppingRecommend = q => { window.__handedOff = q; };
                          window.CouponWorldMobileResearch.search('camera phone under 30000 exclude Samsung');
                        }"""
                    )
                    bridge = page.locator("[data-research-verified-recommend]")
                    assert bridge.is_visible(), width
                    bridge.click()
                    handed_off = page.evaluate("window.__handedOff")
                    assert handed_off == "camera phone under 30000 exclude Samsung", (width, handed_off)

                    # Front-end research does not turn historical budgets into purchase CTAs.
                    assert page.locator("#mobileResearchResults .shop-button").count() == 0, width
                    # The evidence-rich pages must also work without submitting
                    # any JavaScript search or relying on generated hidden data.
                    page.goto(url + "phones/samsung-galaxy-a56-5g/", wait_until="domcontentloaded", timeout=30000)
                    assert page.locator("#variant-12-256").get_by_text("Manufacturer India source").is_visible(), width
                    assert page.locator("figcaption").get_by_text("CC BY-SA 4.0").is_visible(), width
                    assert "Galaxy A56 5G" in page.locator("h1").inner_text(), width
                    assert page.locator(".mobile-fact-table tbody tr").count() >= 8, width
                    assert page.locator('a:has-text("Manufacturer source")').count() >= 8, width
                    assert page.locator('link[rel="canonical"]').get_attribute("href") == (
                        "https://coupon-world.in/phones/samsung-galaxy-a56-5g/"
                    ), width
                    assert not page.locator(".shop-button").count(), width
                    document_width = page.evaluate("document.documentElement.scrollWidth")
                    assert document_width <= width + 8, (
                        f"Phone research page overflows {width}px viewport: {document_width}"
                    )
                    page.goto(url + "phones/", wait_until="domcontentloaded", timeout=30000)
                    assert page.locator(".mobile-fact-card").count() == 50, width
                    assert page.locator('a[href="/phones/samsung-galaxy-a56-5g/"]').count() >= 1, width
                    assert page.locator('a[href="/phones/apple-iphone-17/"]').count() >= 1, width
                    assert page.locator('a[href="/phones/google-pixel-10/"]').count() >= 1, width
                    page.goto(url + "phones/samsung-galaxy-f05/", wait_until="domcontentloaded", timeout=30000)
                    assert "4G LTE" in page.locator(".mobile-fact-table").inner_text(), width
                    assert "5G" not in page.locator(".mobile-fact-table").inner_text(), width
                    page.goto(url + "phones/google-pixel-10/", wait_until="domcontentloaded", timeout=30000)
                    assert page.locator(".mobile-fact-table tbody tr").count() >= 10, width
                    assert not page.locator(".shop-button").count(), width
                    # New research categories must work in the same public
                    # artifact at mobile, tablet and desktop widths.
                    for category in ("accessories", "tvs"):
                        page.goto(url + category + "/", wait_until="domcontentloaded", timeout=30000)
                        page.locator("#cr-grid .cr-card").first.wait_for(timeout=10000)
                        assert page.locator("#cr-grid .cr-card").count() == 4, (width, category)
                        page.locator("#cr-query").fill("Sony" if category == "tvs" else "Apple")
                        assert page.locator("#cr-grid .cr-card:visible").count() == 1, (width, category)
                        page.locator("#cr-query").fill("")
                        if category == "accessories":
                            candidates = page.locator('#cr-grid .cr-card[data-type="Chargers"] input[data-compare]')
                        else:
                            candidates = page.locator('#cr-grid input[data-compare]')
                        candidates.nth(0).check()
                        candidates.nth(1).check()
                        assert page.locator("#cr-comparison").is_visible(), (width, category)
                        assert page.locator("#cr-comparison-table table tbody tr").count() >= 5
                        assert page.locator(".shop-button, .purchase-cta").count() == 0
                        cr_width = page.evaluate("document.documentElement.scrollWidth")
                        assert cr_width <= width + 8, (category, width, cr_width)
                        page.goto(url + category + "/" + (
                            "samsung-ep-t2510-25w" if category == "accessories" else "sony-k-43s20-bravia-2"
                        ) + "/", wait_until="domcontentloaded", timeout=30000)
                        assert page.locator(".cr-detail-facts .cr-fact").count() >= 5
                        assert page.locator('a:has-text("Maker source")').count() >= 5
                        assert page.locator(".purchase-cta, .shop-button").count() == 0
                        cr_width = page.evaluate("document.documentElement.scrollWidth")
                        assert cr_width <= width + 8, (category, width, cr_width)
                    for new_path in ("tvs/india-20/", "accessories/earbuds-20/"):
                        page.goto(url + new_path, wait_until="domcontentloaded", timeout=30000)
                        page.locator("#cr-grid .cr-card").first.wait_for(timeout=10000)
                        assert page.locator("#cr-grid .cr-card").count() == 20, (width, new_path)
                        page.locator("#cr-grid input[data-compare]").nth(0).check()
                        page.locator("#cr-grid input[data-compare]").nth(1).check()
                        assert page.locator("#cr-comparison-table table tbody tr").count() >= 3
                        assert page.locator(".purchase-cta, .shop-button").count() == 0
                    # One indexable editorial page lists the 13 added official sources,
                    # rather than manufacturing thin product SEO pages.
                    page.goto(url + "phones/new-india-mobiles/", wait_until="domcontentloaded", timeout=30000)
                    assert page.locator(".cr-grid .cr-card").count() == 13, width
                    assert "Galaxy F70 5G" in page.locator("main").inner_text(), width
                    assert "REDMI 17C 5G" in page.locator("main").inner_text(), width
                    assert "P4s Lite" in page.locator("main").inner_text(), width
                    assert page.locator('link[rel="canonical"]').get_attribute("href") == "https://coupon-world.in/phones/new-india-mobiles/"
                    assert page.locator(".purchase-cta, .shop-button").count() == 0, width
                    assert page.evaluate("document.documentElement.scrollWidth") <= width + 8, width
                    # Title click opens a real full-detail HTML page (not a search-only hash).
                    new_model = "phones/new-india-mobiles/samsung-galaxy-f70-5g/"
                    page.goto(url + new_model, wait_until="domcontentloaded", timeout=30000)
                    assert "Samsung Galaxy F70 5G" in page.locator("h1").inner_text(), width
                    assert "Current price unavailable" in page.locator("main").inner_text(), width
                    assert page.locator("img[src='/assets/phone-illustrations/recent-india-pairs/samsung-galaxy-f70-5g.webp']").count() == 1, width
                    assert "AI-generated" in page.locator(".cr-detail figcaption").inner_text(), width
                    assert page.locator(".cr-detail-facts .cr-fact").count() >= 5, width
                    assert page.locator('meta[name="robots"]').get_attribute("content") == "noindex,follow", width
                    assert page.locator("a:has-text('Search Amazon')").count() == 1, width
                    assert page.locator("a:has-text('Search Flipkart')").count() == 1, width
                    assert page.locator("a:has-text('Search Croma')").count() == 1, width
                    assert page.evaluate("document.documentElement.scrollWidth") <= width + 8, width
                    page.goto(url + "phones/india-market-demand-q3-2026/", wait_until="domcontentloaded", timeout=30000)
                    assert page.locator(".cr-grid .cr-card").count() == 10
                    assert "NOT an official nationwide Top 10 ranking" in page.locator("main").inner_text()
                    assert "6 were missing" in page.locator("main").inner_text()
                    assert page.locator("a[href*='galaxy-a07-5g/']").count() >= 1
                    assert page.evaluate("document.documentElement.scrollWidth") <= width + 8, width
                    page.goto(url + "phones/india-market-demand-q3-2026/samsung-galaxy-a07-5g/", wait_until="domcontentloaded", timeout=30000)
                    assert "Galaxy A07 5G" in page.locator("h1").inner_text()
                    assert page.locator(".cr-detail-facts .cr-fact").count() >= 5
                    assert page.locator('meta[name="robots"]').get_attribute("content") == "noindex,follow"
                    assert not page.locator(".shop-button,.purchase-cta").count()
                    for guide in ("compare/", "hi/compare/", "phones/under-25000/", "hi/phones/under-25000/"):
                        response=page.goto(url+guide, wait_until="domcontentloaded")
                        assert response.status == 200
                        assert page.locator('h1').count() == 1
                        assert page.evaluate('document.documentElement.scrollWidth') <= width+8
                        assert not page.locator('.rank,.answer-model,.comparison-list').count()
                    for answer in ("answers/phone-for-student-under-18000/", "hi/answers/phone-for-student-under-18000/"):
                        response=page.goto(url+answer, wait_until="domcontentloaded")
                        assert response.status == 200, answer
                        assert page.locator('h1').count() == 1
                        assert "noindex" not in page.locator('meta[name="robots"]').get_attribute("content")
                    for removed in ("answers/best-apple-phone-under-7000/", "compare/apple-iphone-17-vs-apple-iphone-16/", "phones/under-25000/best-camera/"):
                        response=page.goto(url+removed, wait_until="domcontentloaded")
                        assert response.status == 404, removed
                    page.goto(url, wait_until="domcontentloaded")
                    recent_links = page.locator("#indiaPhoneSources article h3 a[href^='/phones/new-india-mobiles/']")
                    assert recent_links.count() == 13, width
                    assert len(set(recent_links.evaluate_all("links => links.map(link => link.href)"))) == 13
                    watch_link = page.locator("#indiaPhoneSources a[href='/seo/india-30-phone-price-watch.html']")
                    assert watch_link.is_visible(), width
                    hero_phone = page.locator(".hero-copy h1 img[src$='phone-in-magnifier.webp']")
                    assert hero_phone.is_visible(), width
                    hero_phone.evaluate("img => img.decode()")
                    assert hero_phone.bounding_box()["width"] <= 64, width
                    watch_link.click()
                    page.wait_for_url("**/seo/india-30-phone-price-watch.html")
                    cards = page.locator(".phone-watch-card")
                    count = cards.count()
                    assert count == 30, width
                    assert cards.locator("img").count() == count, width
                    assert cards.locator(".phone-watch-store-link").count() == count * 3, width
                    assert cards.locator(".phone-watch-status").count() == count, width
                    for store in ("Amazon", "Flipkart", "Croma"):
                        assert cards.get_by_role("link", name=f"Check price on {store} ↗", exact=True).count() > 0, width
                    if count:
                        loaded_image = cards.first.locator("img")
                        loaded_image.scroll_into_view_if_needed()
                        loaded_image.evaluate("img => img.decode()")
                        assert cards.first.locator(".phone-watch-details h2").bounding_box()["x"] > loaded_image.bounding_box()["x"], width
                    for card in cards.all() if width == 1440 else [cards.first]:
                        title = card.locator("h2 button")
                        title.click()
                        dialog = card.locator("dialog")
                        assert dialog.is_visible(), width
                        assert dialog.locator("h2").inner_text() == title.inner_text(), width
                        assert dialog.get_by_role("link", name="Battery source").count() + dialog.get_by_role("link", name="Battery and charging source").count() == 1, width
                        assert dialog.locator(".phone-watch-store-link").count() == 3, width
                        page.keyboard.press("Escape")
                        assert not dialog.is_visible(), width
                    cards.first.locator(".phone-watch-image-button").click()
                    assert cards.first.locator("dialog").is_visible(), width
                    cards.first.locator("dialog").get_by_role("button", name="Close").click()
                    assert page.evaluate("document.documentElement.scrollWidth") <= width + 8, width
                    page.locator('main a[href="/phones/upcoming-india/"]').click()
                    page.wait_for_url("**/phones/upcoming-india/")
                    assert "India launch status checked" in page.locator("main").inner_text(), width
                    assert "₹" not in page.locator("main").inner_text(), width
                    # Reproduce the full-catalogue view shown in the narrow-card bug.
                    page.goto(url + "#mobileResearchCatalogue", wait_until="domcontentloaded")
                    page.locator("#mobileResearchCatalogueGrid .mobile-research-model-card").first.wait_for(state="visible")
                    for inventory_card in page.locator("#mobileResearchCatalogueGrid .mobile-research-model-card").all()[:3]:
                        dimensions = inventory_card.evaluate("""card => {
                            const style = getComputedStyle(card);
                            const body = card.querySelector('.mobile-research-inventory-body');
                            return {
                                available: card.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight),
                                body: body.getBoundingClientRect().width
                            };
                        }""")
                        assert dimensions["body"] >= dimensions["available"] - 2, (width, dimensions)
                        assert dimensions["body"] > 180, (width, dimensions)
                    assert not page_errors, f"{width}px uncaught JS errors: {page_errors}"
                    results.append({"width": width, "search": "PASS", "full_budget_opt_in": "PASS", "exact_variant": "PASS",
                                    "comparison": "PASS", "engine_handoff": "PASS",
                                    "page_errors": len(page_errors), "budget_filters": budget_audit})
                    print(f"PASS {width}px responsive smartphone research, comparison and engine handoff")
                    page.close()
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("public"))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = {"status": "PASS", "scope": "loopback public-site Chromium QA (not real retailer availability)",
              "results": run(args.root)}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
