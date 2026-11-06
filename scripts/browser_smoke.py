#!/usr/bin/env python3
"""End-to-end smoke test of the *generated public site*, not a mocked DOM.

Requires: pip install playwright && python -m playwright install chromium
Runs against a loopback static server, so no live retailer/API credentials
are used. The backend recommendation handoff is stubbed after the public
app.js handler loads; only its correct argument routing is asserted here.
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
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_function("() => !!window.CouponWorldMobileResearch", timeout=15000)
                    # Wait for the real fetch->catalogue->browser filtering chain.
                    page.wait_for_function(
                        "() => window.CouponWorldMobileResearch.search('phone under 30000').length > 0",
                        timeout=20000,
                    )
                    assert page.locator("#mobileResearchResults [data-mobile-model-card]").count() > 0, width
                    assert page.locator("#mobileResearchResults").is_visible(), width
                    research_text = page.locator("#mobileResearchResults").text_content() or ""
                    visible_text = page.locator("#mobileResearchResults").inner_text()
                    print("RESEARCH-DIAGNOSTIC", width, "DOM:", repr(research_text[:180]), "visible:", repr(visible_text[:180]), flush=True)
                    assert "Research only" in research_text, width
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


                    page.evaluate("window.CouponWorldMobileResearch.search('Galaxy A36 8GB 256GB')")
                    names = page.locator("#mobileResearchResults [data-mobile-model-card]")
                    assert names.count() == 1, f"{width}: exact-variant result count {names.count()}"
                    assert "8GB RAM" in names.first.inner_text(), width
                    assert "256GB storage" in names.first.inner_text(), width

                    page.evaluate("window.CouponWorldMobileResearch.search('Galaxy A36 vs Galaxy A56')")
                    assert page.locator("#mobileResearchCompare table").count() == 1, width
                    assert "no performance winner" in page.locator("#mobileResearchCompare").inner_text().lower(), width

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
                    for answer_prefix in ("answers/", "hi/answers/"):
                        page.goto(url+answer_prefix+"phone-under-25000-with-amoled-ois-and-8gb-ram/", wait_until="domcontentloaded")
                        assert page.locator('.answer-model').count() == 2
                        assert 'CMF Phone 1' not in page.locator('main').inner_text()
                        assert 'POCO X7 Pro 5G' not in page.locator('main').inner_text()
                        assert page.locator('link[rel="alternate"]').count() == 2
                        assert 'noindex' not in page.locator('meta[name="robots"]').get_attribute('content')
                        assert page.locator('table tbody tr').count() >= 16
                        assert page.evaluate('document.documentElement.scrollWidth') <= width+8
                    page.goto(url+"answers/best-apple-phone-under-7000/", wait_until="domcontentloaded")
                    assert page.locator('meta[name="robots"]').get_attribute('content') == 'noindex,follow'
                    assert page.locator('.answer-model').count() == 0
                    assert 'not proof' in page.locator('.quick-answer').inner_text()
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
