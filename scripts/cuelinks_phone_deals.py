"""Render dated phone deals from the publisher API into the public build."""
from datetime import date, datetime
from html import escape
import json
import os
import re
from urllib.error import URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


def render_phone_deals():
    key = os.environ.get("CUELINKS_API_KEY")
    today = datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()
    offers = {}
    if key:
        for term in ("smartphone", "mobile phone"):
            query = urlencode({"q": term, "valid_on": today, "per_page": 25})
            request = Request("https://developers.cuelinks.com/pub_api/v3/offers?" + query, headers={
                "Authorization": "Token " + key,
                "Accept": "application/json",
                "User-Agent": "CouponWorld-Cuelinks/1.0",
            })
            try:
                with urlopen(request, timeout=12) as response:
                    rows = json.load(response).get("data", [])
            except (URLError, TimeoutError, ValueError, AttributeError):
                print("Cuelinks phone offers unavailable for one search.")
                continue
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict) or not isinstance(row.get("id"), int):
                    continue
                title = str(row.get("title") or "").strip()
                description = str(row.get("description") or "").strip()
                terms = str(row.get("terms") or "").strip()
                scope = title + " " + description
                if not re.search(r"\b(?:smartphones?|mobile phones?|handsets?)\b", scope, re.I):
                    continue
                if re.search(r"\b(?:recharges?|phone cases?|screen protectors?)\b", title, re.I):
                    continue
                start, end = str(row.get("start_date") or ""), str(row.get("end_date") or "")
                try:
                    valid_today = date.fromisoformat(start) <= date.fromisoformat(today) <= date.fromisoformat(end)
                except ValueError:
                    continue
                if row.get("status") != "live" or not title or not valid_today:
                    continue
                url = str(row.get("tracking_url") or "")
                try:
                    parsed = urlsplit(url)
                    host = parsed.hostname or ""
                except ValueError:
                    continue
                if (parsed.scheme != "https" or parsed.username is not None or
                        not (host in {"linksredirect.com", "clnk.in"} or host.endswith(".clnk.in"))):
                    continue
                merchant = str(row.get("campaign_name") or "").strip()
                code = str(row.get("coupon_code") or "").strip()
                offers[row["id"]] = (title, merchant, code, description, terms, date.fromisoformat(end).isoformat(), url)

    cards = []
    for title, merchant, code, description, terms, end, url in list(offers.values())[:6]:
        cards.append(
            f'<article class="mobile-research-result-card" data-phone-deal-expiry="{escape(end)}">'
            f'<h3>{escape(title)}</h3><p>{escape(merchant)} · Ends {escape(end)} (IST)</p>'
            + (f'<p>Coupon code <strong>{escape(code)}</strong></p>' if code else '')
            + (f'<p>{escape(description)}</p>' if description and description != title else '')
            + (f'<details><summary>Offer terms</summary><p>{escape(terms)}</p></details>' if terms else '')
            + f'<p><a href="{escape(url)}" rel="sponsored nofollow noopener">View deal ↗</a></p></article>'
        )
    print(f"Cuelinks phone deals published: {len(cards)}")
    return (
        '<section id="phoneDeals" class="container mobile-research-new-section" aria-labelledby="phoneDealsTitle">'
        '<div class="section-panel"><h2 id="phoneDealsTitle">Phone Deals &amp; Coupon Codes</h2>'
        '<p>Check the eligible model, payment method and final discount at checkout. Coupon World may earn a commission from qualifying purchases.</p>'
        '<div class="mobile-research-results">' + "".join(cards) + '</div>'
        '<p id="phoneDealsEmpty"' + (' hidden' if cards else '') + '>No verified phone coupon is listed right now.</p>'
        '</div></section>'
        '<script>(()=>{const section=document.getElementById("phoneDeals");'
        'const day=new Intl.DateTimeFormat("en-CA",{timeZone:"Asia/Kolkata",year:"numeric",month:"2-digit",day:"2-digit"});'
        'const parts=Object.fromEntries(day.formatToParts(new Date()).map(p=>[p.type,p.value]));'
        'const today=parts.year+"-"+parts.month+"-"+parts.day;'
        'section.querySelectorAll("[data-phone-deal-expiry]").forEach(card=>{'
        'if(card.dataset.phoneDealExpiry<today)card.remove();});'
        'document.getElementById("phoneDealsEmpty").hidden=!!section.querySelector("article");})();</script>'
    )
