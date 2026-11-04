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
                    # The normal upper-budget shortcut remains a nearby band.
                    nearby = page.evaluate("""() => window.CouponWorldMobileResearch.search('phone under 30000').map(x => x.card.research_budget_reference.reference_price_inr)""")
                    assert nearby and all(25000 <= price < 30000 for price in nearby), width
                    # Full-budget search is a deliberate visitor choice, never a silent fallback.
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
