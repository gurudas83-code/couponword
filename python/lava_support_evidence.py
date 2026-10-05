"""Bounded, model-bound Lava secondary support evidence for deep extraction."""
import re
from datetime import datetime, timezone
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from product_evidence_store import variant_signature_from_text, variant_signature_from_specifications

SUPPORT_URL = "https://www.lavamobiles.com/software-update-center"

def add_lava_support_evidence(output, identity, product_html, fetch_page, observed_at):
    # Never add policy evidence to an unverified product or ambiguous variant.
    if output.get("resolver_verified") is not True or output.get("review", {}).get("status") != "candidate_ready":
        return False
    model = str(identity.get("model") or "").strip().casefold()
    if model not in {"bold n2", "bold n2 lite", "virat v1"} or str(identity.get("brand", "")).casefold() != "lava":
        return False
    product_url = urlparse(output.get("official_url") or "")
    if product_url.hostname not in {"lavamobiles.com", "www.lavamobiles.com"} or product_url.path.rstrip("/") != "/smartphones/" + model.replace(" ", "-"):
        return False
    requested = variant_signature_from_text(identity.get("original_title"), identity.get("title"))
    actual = variant_signature_from_specifications(output.get("specifications"))
    if set(requested) != {"ram_gb", "storage_gb"} or requested != actual:
        return False
    product_soup = BeautifulSoup(product_html, "html.parser")
    if not any(a.get("href") in {"/software-update-center", SUPPORT_URL} for a in product_soup.find_all("a")):
        return False
    html, error, status = fetch_page(SUPPORT_URL)
    if error or status != 200 or not html:
        return False
    soup = BeautifulSoup(html, "html.parser")
    policy = next((p.get_text(" ", strip=True) for p in soup.find_all("p")
                   if re.search(r"quarterly security updates\s+for\s+two years\s+after the launch of a model", p.get_text(" ", strip=True), re.I)), "")
    rows = [row for row in soup.select(".product-model-container")
            if row.find("h2") and row.find("h2").get_text(" ", strip=True).casefold() == model]
    if not policy or len(rows) != 1:
        return False
    row = rows[0]
    tab = row.find_parent(class_="tab-content")
    if tab is None or "end-of-life" in tab.get_text(" ", strip=True).casefold():
        return False
    fields = {col.find("span").get_text(" ", strip=True): col.find("h4").get_text(" ", strip=True)
              for col in row.select(".col") if col.find("span") and col.find("h4")}
    launch = fields.get("Launch Date", "")
    match = re.fullmatch(r"([A-Za-z]{3})[-'](\d{2})", launch)
    if not match:
        return False
    try:
        month = datetime.strptime(match[1], "%b").month
        now = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        # Month precision: stop using the policy at the first possible expiry.
        expiry = datetime(2000 + int(match[2]) + 2, month, 1, tzinfo=timezone.utc)
        if now.tzinfo is None or now >= expiry:
            return False
    except ValueError:
        return False
    output["specifications"]["software_security_support"] = {
        "label": "Software security support", "value": "2 years of security updates from model launch; quarterly cadence",
        "source": "official_model_support_policy", "source_url": SUPPORT_URL,
        "observed_at": observed_at, "identity_match": {"model": model, "variant": requested, "status": "exact_model_row_and_verified_product_variant"},
        "launch_month": launch, "policy_text": policy,
    }
    return True
