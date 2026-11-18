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
                    assert page.locator(".cw-budget-more").evaluate("(el) => !el.open"), width
                    page.locator(".cw-budget-more summary").click()
                    assert page.locator('[data-mobile-query="mobile under 50000"]').is_visible(), width
                    page.locator(".cw-budget-more summary").click()
                    assert page.locator(".cw-budget-more").evaluate("(el) => !el.open"), width
                    assert page.locator("#researchCategories").evaluate(
                        "(el) => !!(el.compareDocumentPosition(document.getElementById('mobileResearchSearch')) & Node.DOCUMENT_POSITION_FOLLOWING)"
                    ), width
                    page.wait_for_function("() => !!window.CouponWorldMobileResearch", timeout=15000)
                    # Wait for the real fetch->catalogue->browser filtering chain.
                    page.wait_for_function(
                        "() => window.CouponWorldMobileResearch.search('phone under 30000').length > 0",
                        timeout=20000,
                    )
                    # Original 232-card registry remains distinct from eight
                    # manufacturer-sourced sales-report additions.
                    page.wait_for_function(
                        "() => window.CouponWorldMobileResearch.search('OPPO A6x 5G').some("
                        "item => item.card.model_key === 'oppo|a6x 5g' && item.card.market_intake === true)",
                        timeout=20000,
                    )
                    a6 = page.locator("#mobileResearchResults [data-mobile-model-card='oppo|a6x 5g']")
                    assert a6.count() == 1, width
                    assert "India sales/shipments research addition" in a6.inner_text(), width
                    assert "Search Amazon" in a6.inner_text(), width
                    assert "Search Flipkart" in a6.inner_text(), width
                    assert "Search Croma" in a6.inner_text(), width
                    assert page.evaluate(
                        "() => window.CouponWorldMobileResearch.search('Samsung Galaxy A07 5G').some("
                        "item => item.card.model_key === 'samsung|galaxy a07 5g' && item.card.market_intake === true)"
                    ), width
                    # Verify all 19 research additions actually appear after fetch.
                    page.wait_for_function(
                        "() => !!document.querySelector('#mobileResearchNew') && "
                        "!document.querySelector('#mobileResearchNew').hidden && "
                        "document.querySelector('#mobileResearchNewCount').textContent.includes('19 additional')",
                        timeout=20000,
                    )
                    assert page.locator("#mobileResearchNewGrid [data-mobile-model-card]").count() == 19, width
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
                    assert not page.locator("#mobileResearchResults .research-budget-primary-grid [data-mobile-model-card]").count(), width
                    page.evaluate("window.CouponWorldMobileResearch.search('Samsung Galaxy F70 5G 8GB RAM under 30000')")
                    assert not page.locator("#mobileResearchResults .research-budget-related-item").count(), width
                    page.evaluate("window.CouponWorldMobileResearch.search('phone under 30000 exclude Samsung')")
                    assert not any("Samsung" in name for name in page.locator(
                        "#mobileResearchResults .research-budget-related-item>strong"
                    ).all_inner_texts()), width
                    page.evaluate("window.CouponWorldMobileResearch.search('phone under 30000')")

                    # Nearby-band narrowing must be explicit.
                    nearby = page.evaluate("""() => window.CouponWorldMobileResearch.search('phone under 30000 nearby band').map(x => x.card.research_budget_reference.reference_price_inr)""")
                    assert nearby and all(25000 <= price < 30000 for price in nearby), width
                    # The ordinary under-budget shortcut matches the full-budget search.
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
                    assert ordinary == full, width

                    # Regression: strict under-budget semantics and no hidden lower band.
                    for limit in (10000, 15000, 20000, 25000, 30000, 50000):
                        prices = page.evaluate("""limit => window.CouponWorldMobileResearch.search(
                            'phone under ' + limit
                        ).map(item => item.card.research_budget_reference.reference_price_inr)""", limit)
                        assert all(0 < price < limit for price in prices), (width, limit, prices)
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
                    # One indexable editorial page lists the 11 added official sources,
                    # rather than manufacturing thin product SEO pages.
                    page.goto(url + "phones/new-india-mobiles/", wait_until="domcontentloaded", timeout=30000)
                    assert page.locator(".cr-grid .cr-card").count() == 11, width
                    assert "Galaxy F70 5G" in page.locator("main").inner_text(), width
                    assert "REDMI 17C 5G" in page.locator("main").inner_text(), width
                    assert "P4s Lite" in page.locator("main").inner_text(), width
                    assert page.locator('link[rel="canonical"]').get_attribute("href") == "https://coupon-world.in/phones/new-india-mobiles/"
                    assert page.locator(".purchase-cta, .shop-button").count() == 0, width
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
                                    "page_errors": len(page_errors)})
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
