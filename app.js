// Keep the data URL stable so CDN/browser caches follow the deployed artifact
// instead of forcing a new request on every page load.
const DEALS_FILE = "/coupons.json";
const DEAL_MAX_AGE_MS = 6 * 60 * 60 * 1000;
const APPROVED_RETAILER_HOSTS = new Set([
  "amazon.in", "www.amazon.in", "amzn.in", "www.amzn.in",
  "flipkart.com", "www.flipkart.com", "croma.com", "www.croma.com"
]);
const RECOMMENDATION_TIMEOUT_MS = 15000;

// Keep the published site on the approved Render API while making the
// existing frontend route testable against the local backend.  The override
// is intentionally limited to loopback hosts and does not rewrite unrelated
// production requests.
const API_BASE_URL = ["127.0.0.1", "localhost"].includes(
  window.location.hostname
)
  ? "http://127.0.0.1:8000"
  : "https://couponword.onrender.com";

let allDeals = [];
let activeCategory = "All";
let activeView = "grid";
let recommendationRequestId = 0;
let recommendationController = null;

const grid = document.getElementById("dealsGrid");
const searchInput = document.getElementById("searchInput");
const heroSearch = document.getElementById("heroSearch");
const heroSearchButton = document.getElementById("heroSearchButton");
const sortSelect = document.getElementById("sortSelect");
const chipsBox = document.getElementById("categoryChips");
const resultsCount = document.getElementById("resultsCount");
const mobileNavToggle = document.querySelector(".mobile-nav-toggle");
const mobileNav = document.getElementById("mobileNav");

if (mobileNavToggle && mobileNav) {
  mobileNavToggle.addEventListener("click", () => {
    const open = mobileNav.hidden;
    mobileNav.hidden = !open;
    mobileNavToggle.setAttribute("aria-expanded", String(open));
  });
  mobileNav.querySelectorAll("a").forEach(link => {
    link.addEventListener("click", () => {
      mobileNav.hidden = true;
      mobileNavToggle.setAttribute("aria-expanded", "false");
    });
  });
}

async function loadDeals() {
  try {
    const res = await fetch(DEALS_FILE);
    if (!res.ok) throw new Error("coupons.json not found");

    const rawDeals = await res.json();
    if (!Array.isArray(rawDeals)) throw new Error("Invalid public deal data");
    allDeals = rawDeals.filter(isCurrentVerifiedDeal);

    updateStats();
    buildCategoryChips();
    renderFeaturedDeal();
    renderDeals();
  } catch (err) {
    grid.innerHTML = `<div class="state-card"><strong>Verified offers are currently unavailable.</strong><span>Explore <a href="#mobileResearchPreview">verified smartphone research</a> instead.</span></div>`;
    resultsCount.textContent = "No deals loaded";
  }
}

function numericPrice(value) {
  const match = String(value ?? "").replace(/,/g, "").match(/\d+(?:\.\d+)?/);
  return match ? Number(match[0]) : 0;
}

function isRecentDeal(deal) {
  const stamp = deal.last_checked || deal.verified_at || deal.checked_at;
  const checkedAt = Date.parse(String(stamp || ""));
  return Number.isFinite(checkedAt) && Date.now() - checkedAt >= 0 && Date.now() - checkedAt <= DEAL_MAX_AGE_MS;
}

function hasExplicitStock(deal) {
  return ["in_stock", "in stock", "available", "available_now"].includes(
    normalize(deal.availability)
  );
}

function hasApprovedRetailerLink(deal) {
  try {
    const parsed = new URL(String(deal.link || ""), window.location.href);
    return parsed.protocol === "https:" && APPROVED_RETAILER_HOSTS.has(parsed.hostname.toLowerCase());
  } catch (error) {
    return false;
  }
}

function isCurrentVerifiedDeal(deal) {
  if (!deal || typeof deal !== "object") return false;
  const identityVerified = deal.identity_verified === true ||
    normalize(deal.catalog_status) === "verified" ||
    normalize(deal.identity_decision) === "verified";
  return deal.active === true &&
    deal.cta_eligible === true &&
    identityVerified &&
    numericPrice(deal.price) > 0 &&
    hasExplicitStock(deal) &&
    isRecentDeal(deal) &&
    hasApprovedRetailerLink(deal);
}

function normalize(text) {
  return String(text || "").toLowerCase().trim();
}

function getSearchText(deal) {
  return [
    deal.title,
    deal.store,
    deal.category,
    deal.discount,
    deal.code,
    deal.price,
    deal.mrp,
    deal.save,
    deal.expiry
  ].join(" ");
}

function extractNumber(value) {
  const match = String(value || "").match(/\d+/);
  return match ? Number(match[0]) : 0;
}

function getFilteredDeals() {
  const query = normalize(searchInput.value);

  let deals = allDeals.filter(deal => {
    const matchSearch = normalize(getSearchText(deal)).includes(query);
    const matchCategory =
      activeCategory === "All" ||
      normalize(deal.category) === normalize(activeCategory);

    return matchSearch && matchCategory;
  });

  if (sortSelect.value === "latest") {
    deals.sort((a, b) => Number(b.id || 0) - Number(a.id || 0));
  }

  if (sortSelect.value === "discount") {
    deals.sort((a, b) => extractNumber(b.discount) - extractNumber(a.discount));
  }

  if (sortSelect.value === "az") {
    deals.sort((a, b) => String(a.title || "").localeCompare(String(b.title || "")));
  }

  return deals;
}

function updateStats() {
  document.getElementById("statDeals").textContent = allDeals.length;

  const categories = new Set(allDeals.map(d => d.category).filter(Boolean));
  document.getElementById("statCategories").textContent = categories.size;
}

function buildCategoryChips() {
  const categories = ["All", ...new Set(allDeals.map(d => d.category).filter(Boolean))];

  chipsBox.innerHTML = categories.map(cat => `
    <button type="button" class="chip ${cat === activeCategory ? "active" : ""}" data-category="${escapeHTML(cat)}">
      ${escapeHTML(cat)}
    </button>
  `).join("");

  chipsBox.querySelectorAll("button").forEach(btn => {
    btn.addEventListener("click", () => {
      activeCategory = btn.dataset.category;
      buildCategoryChips();
      renderDeals();
    });
  });
}

function renderFeaturedDeal() {
  const box = document.getElementById("featuredDeal");
  const deal = allDeals[0];

  if (!deal) {
    box.innerHTML = `
      <div class="spotlight-image placeholder-big" aria-hidden="true">📱</div>
      <h2>Verified offers are currently unavailable.</h2>
      <p>Explore verified smartphone research while fresh retailer checks are unavailable.</p>
      <a href="#mobileResearchPreview">Explore smartphone research</a>
    `;
    return;
  }

  box.innerHTML = `
    ${renderImage(deal, "spotlight-image")}
    <h2>${escapeHTML(deal.title || "Hot Deal")}</h2>
    <p>${escapeHTML(deal.discount || "Latest offer")} • ${escapeHTML(deal.category || "Deal")}</p>
    ${deal.cta_eligible === true
      ? `<a href="${escapeHTML(safeLink(deal.link))}" target="_blank" rel="nofollow sponsored noopener">View Deal</a>`
      : `<span class="shop-button disabled">Offer verification unavailable</span>`}
  `;
}

function renderDeals() {
  const deals = getFilteredDeals();

  resultsCount.textContent = `${deals.length} deal${deals.length !== 1 ? "s" : ""} found`;

  if (!deals.length) {
    grid.innerHTML = `<div class="state-card"><strong>Verified offers are currently unavailable.</strong><span>Explore <a href="#mobileResearchPreview">verified smartphone research</a> instead.</span></div>`;
    return;
  }

  grid.className = activeView === "compact" ? "deal-grid compact" : "deal-grid";

  grid.innerHTML = deals.map(deal => `
    <article class="deal-card">
      ${renderImage(deal, "deal-image")}

      <div class="deal-meta">
        <span class="store">${escapeHTML(deal.store || "Online Store")}</span>
        <span class="category-pill">${escapeHTML(deal.category || "Deal")}</span>
      </div>

      <h3 class="deal-title">${escapeHTML(deal.title || "Amazon Product Deal")}</h3>

      <div class="discount">${escapeHTML(deal.discount || "Deal Price")}</div>

      <div class="price-row">
        ${deal.price ? `<span class="price">${escapeHTML(deal.price)}</span>` : ""}
        ${deal.mrp ? `<span class="mrp">${escapeHTML(deal.mrp)}</span>` : ""}
        ${deal.save ? `<span class="save">${escapeHTML(deal.save)}</span>` : ""}
      </div>

      <p class="description">${escapeHTML(deal.description || "Check the latest price, availability and offer on the retailer site before buying.")}</p>

      <div class="code-row">
        <span>${escapeHTML(deal.code || "NO CODE NEEDED")}</span>
        <span>${escapeHTML(deal.expiry || "Limited Time")}</span>
      </div>

      ${deal.cta_eligible === true
        ? `<a class="shop-button" href="${escapeHTML(safeLink(deal.link))}" target="_blank" rel="nofollow sponsored noopener">Get Deal →</a>`
        : `<span class="shop-button disabled">Offer verification unavailable</span>`}

      <div class="card-note">Price and availability may change on the retailer site</div>
    </article>
  `).join("");
}

function categoryPlaceholder(category) {
  const key = String(category || "").toLowerCase().trim();

  const placeholders = {
    "mobiles": "mobiles.svg",
    "mobile": "mobiles.svg",
    "smartphones": "mobiles.svg",
    "cell phones & accessories": "mobiles.svg",
    "electronics": "electronics.svg",
    "laptops": "laptops.svg",
    "computers": "laptops.svg",
    "audio": "audio.svg",
    "headphones": "audio.svg",
    "speakers": "audio.svg",
    "fashion": "fashion.svg",
    "clothing": "fashion.svg",
    "footwear": "fashion.svg",
    "home": "home-kitchen.svg",
    "home & kitchen": "home-kitchen.svg",
    "home improvement": "home-kitchen.svg",
    "beauty": "beauty.svg",
    "health & personal care": "beauty.svg",
    "grocery": "grocery.svg",
    "appliances": "appliances.svg"
  };

  return `assets/images/categories/${placeholders[key] || "default.svg"}`;
}

function renderImage(deal, className) {
  const fallbackImage = categoryPlaceholder(deal.category);
  const displayImage = deal.image || fallbackImage;

  return `
    <div class="${className}">
      <img
        src="${escapeHTML(displayImage)}"
        alt="${escapeHTML(deal.title || "Deal image")}"
        loading="lazy"
        decoding="async"
        onerror="this.onerror=null;this.src='${escapeHTML(fallbackImage)}'">
    </div>
  `;
}

function applySearch(value) {
  searchInput.value = value || "";
  document.getElementById("browse").scrollIntoView({ behavior: "smooth" });
  renderDeals();
}

function safeLink(link) {
  const raw = String(link || "").trim();
  if (!raw) {
    return "#";
  }

  try {
    const parsed = new URL(raw, window.location.href);
    if (!["http:", "https:"].includes(parsed.protocol)) {
      return "#";
    }
    if (window.location.protocol === "https:" && parsed.protocol === "http:") {
      return "#";
    }
    return parsed.href;
  } catch (error) {
    return "#";
  }
}

function trackAnalyticsEvent(eventName, params = {}) {
  try {
    if (typeof window.gtag === "function") {
      window.gtag("event", eventName, params);
    }
  } catch (error) {
    console.warn("Coupon World analytics event failed:", eventName, error);
  }
}

function analyticsSearchTerm(value) {
  return String(value || "")
    .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, "[email]")
    .replace(/(?:\+?91[\s-]?)?[6-9]\d{9}/g, "[phone]")
    .trim()
    .slice(0, 100);
}

function retailerFromLink(link) {
  try {
    return new URL(link.href, window.location.href).hostname
      .replace(/^www\./, "")
      .slice(0, 100);
  } catch (error) {
    return "unknown";
  }
}

document.addEventListener("click", event => {
  const link = event.target.closest('a[rel~="sponsored"]');

  if (!link || link.dataset.aiRetailerClick === "1") {
    return;
  }

  const card = link.closest(".deal-card, #featuredDeal");
  const title = card
    ? card.querySelector(".deal-title, h2, h3")?.textContent
    : "";

  trackAnalyticsEvent("affiliate_click", {
    retailer: retailerFromLink(link),
    link_placement: link.closest("#featuredDeal")
      ? "featured_deal"
      : "deal_card",
    product_title: String(title || "").trim().slice(0, 100)
  });
});

function escapeHTML(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

searchInput.addEventListener("input", renderDeals);
sortSelect.addEventListener("change", renderDeals);

heroSearchButton.addEventListener("click", () => {
  const query = heroSearch.value;
  applySearch(query);
  loadShoppingRecommendation(query);
});

heroSearch.addEventListener("keydown", e => {
  if (e.key === "Enter") {
    const query = heroSearch.value;
    applySearch(query);
    loadShoppingRecommendation(query);
  }
});

document.querySelectorAll("[data-search]").forEach(el => {
  el.addEventListener("click", () => applySearch(el.dataset.search));
});

document.querySelectorAll("[data-quick]").forEach(el => {
  el.addEventListener("click", () => applySearch(el.dataset.quick));
});

// Mobile budget shortcuts use the same recommendation endpoint as the hero
// search. They do not alter ranking or eligibility; they only provide a clear
// customer-facing way to submit the existing query contract.
document.querySelectorAll("[data-mobile-query]").forEach(el => {
  el.addEventListener("click", () => {
    const query = String(el.dataset.mobileQuery || "").trim();
    if (!query) return;
    heroSearch.value = query;
    loadShoppingRecommendation(query);
  });
});

document.querySelectorAll("[data-view]").forEach(btn => {
  btn.addEventListener("click", () => {
    activeView = btn.dataset.view;

    document.querySelectorAll("[data-view]").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");

    renderDeals();
  });
});

loadDeals();
// Hide unverified discount labels from all product cards.
function removeUnverifiedDiscounts() {
  const discountPattern = /^\s*\d+(?:\.\d+)?\s*%\s*OFF\s*$/i;

  document
    .querySelectorAll(
      ".discount, .discount-badge, .discount-text, .product-discount, .deal-discount, [data-discount]"
    )
    .forEach((element) => element.remove());

  document.querySelectorAll("body *").forEach((element) => {
    const hasChildElements = element.children.length > 0;
    const text = element.textContent?.trim() || "";

    if (!hasChildElements && discountPattern.test(text)) {
      element.remove();
    }
  });
}

document.addEventListener("DOMContentLoaded", removeUnverifiedDiscounts);

// Also run after dynamically rendered products.
setTimeout(removeUnverifiedDiscounts, 300);

function renderResearchComparison(comparison) {
  const models = Array.isArray(comparison?.models) ? comparison.models : [];
  if (models.length < 2) return "";
  const modelCards = models.map(model => {
    const specs = model.specifications && typeof model.specifications === "object"
      ? model.specifications
      : {};
    const chipset = specs.chipset?.value || "Not available";
    const battery = specs.battery_mah_typical?.value != null
      ? `${specs.battery_mah_typical.value} mAh`
      : "Not available";
    const mainCamera = specs.rear_main_mp?.value != null
      ? `${specs.rear_main_mp.value} MP main camera`
      : "Not available";
    const ultrawide = specs.rear_ultrawide_mp?.value != null
      ? `${specs.rear_ultrawide_mp.value} MP ultrawide`
      : "Not available";
    const variants = Array.isArray(model.variants)
      ? model.variants.map(variant =>
        `${escapeHTML(variant.ram_gb)}GB/${escapeHTML(variant.storage_gb)}GB (${escapeHTML(variant.canonical_product_id)})`
      ).join(", ")
      : "Not available";
    const batteryEvidence = model.battery_evidence || {};
    const cameraEvidence = model.camera_evidence || {};
    const cameraTypes = Array.isArray(cameraEvidence.observation_types)
      ? cameraEvidence.observation_types.join(", ").replaceAll("_", " ")
      : "No accepted observation";
    const official = safeLink(model.official_source);
    return `<article class="research-comparison-card">
      <div class="research-comparison-card-top">
        <h4>${escapeHTML(model.brand || "")} ${escapeHTML(model.model || "")}</h4>
        <span class="research-status">${escapeHTML(model.manufacturer_spec_status || "VERIFIED")}</span>
      </div>
      <p><strong>Verified India variants:</strong> ${variants}</p>
      <dl class="research-comparison-specs">
        <div><dt>Processor</dt><dd>${escapeHTML(chipset)}</dd></div>
        <div><dt>Battery</dt><dd>${escapeHTML(battery)}</dd></div>
        <div><dt>Camera hardware</dt><dd>${escapeHTML(mainCamera)} · ${escapeHTML(ultrawide)}</dd></div>
      </dl>
      <p><strong>Battery evidence:</strong> ${escapeHTML(batteryEvidence.status || "Unavailable")} <span class="research-scope">(${escapeHTML(batteryEvidence.applicability || "model context")})</span></p>
      <p><strong>Camera evidence:</strong> ${escapeHTML(cameraEvidence.status || "Unavailable")} · ${escapeHTML(cameraTypes)} <span class="research-scope">(qualitative/model context)</span></p>
      ${official !== "#" ? `<a class="mobile-research-link" href="${escapeHTML(official)}" target="_blank" rel="noopener">Official source ↗</a>` : ""}
    </article>`;
  }).join("");
  return `<section class="research-comparison-result" aria-label="Evidence-backed smartphone comparison">
    <h3>Evidence-backed A36 vs A56 comparison</h3>
    <p>Research reference only. This comparison uses verified India specifications and labelled model-level battery/camera evidence. It contains no price, offer, ranking or purchase claim.</p>
    <div class="research-comparison-grid">${modelCards}</div>
    <a class="btn btn-ghost" href="#mobileResearchPreview">View all 10 verified smartphone variants</a>
  </section>`;
}

function isResearchComparisonQuery(query) {
  const normalized = normalize(query);
  return (normalized.includes("compare") || normalized.includes(" vs ")) &&
    normalized.includes("a36") && normalized.includes("a56") &&
    normalized.includes("galaxy");
}

function comparisonFromPreviewPayload(payload, query) {
  const products = Array.isArray(payload?.products) ? payload.products : [];
  const models = ["Galaxy A36 5G", "Galaxy A56 5G"].map(model => {
    const rows = products.filter(row => row.brand === "Samsung" && row.model === model);
    if (!rows.length) return null;
    const base = rows[0];
    return {
      brand: base.brand,
      model: base.model,
      manufacturer_spec_status: base.manufacturer_spec_status,
      official_source: base.official_source,
      specifications: base.specifications || {},
      battery_evidence: base.battery_evidence || {},
      camera_evidence: base.camera_evidence || {},
      variants: rows.map(row => ({
        canonical_product_id: row.canonical_product_id,
        ram_gb: row.ram_gb,
        storage_gb: row.storage_gb
      }))
    };
  }).filter(Boolean);
  return models.length === 2 ? {
    status: "RESEARCH_REFERENCE_ONLY",
    query,
    models,
    source_dataset: "P13.1O_PUBLIC_TECHNICAL_RESEARCH_PREVIEW",
    commerce: {
      price: null,
      stock: null,
      purchase_cta_eligible: false,
      publication_eligible: false
    }
  } : null;
}

async function loadResearchComparisonFallback(query, signal) {
  if (!isResearchComparisonQuery(query)) return null;
  try {
    const response = await fetch("/data/mobile_research_preview.json", {
      credentials: "omit",
      signal
    });
    if (!response.ok) return null;
    return comparisonFromPreviewPayload(await response.json(), query);
  } catch (error) {
    return null;
  }
}

function renderOfferUnavailable() {
  return `<section class="ai-detail-block ai-unknowns" aria-label="Verified offer status">
    <h3>Verified offers are currently unavailable</h3>
    <p>No current in-stock retailer offer passed the existing price, identity and freshness gates for this shopping query.</p>
    <a class="btn btn-ghost" href="#mobileResearchPreview">Explore verified smartphone research</a>
  </section>`;
}

async function loadShoppingRecommendation(query) {
  const card = document.getElementById("shoppingBrainCard");
  const section = document.getElementById("aiRecommendation");

  if (!card) {
    console.error("shoppingBrainCard element not found");
    return;
  }

  const cleanQuery = String(query || "").trim();
  const analyticsQuery = analyticsSearchTerm(cleanQuery);

  if (!cleanQuery) {
    recommendationRequestId += 1;
    if (recommendationController) {
      recommendationController.abort();
      recommendationController = null;
    }
    card.innerHTML = `
      <h3>Ask Coupon World</h3>
      <p>Search for a product above to get personalized AI recommendations.</p>
    `;
    return;
  }

  trackAnalyticsEvent("ai_search_submit", {
    search_term: analyticsQuery
  });

  if (recommendationController) recommendationController.abort();
  const requestId = ++recommendationRequestId;
  const controller = new AbortController();
  recommendationController = controller;
  const timeoutHandle = window.setTimeout(
    () => controller.abort(),
    RECOMMENDATION_TIMEOUT_MS
  );

  card.innerHTML = `
    <h3>Finding the best matches...</h3>
    <p>Coupon World AI is checking products, prices and fit for your request.</p>
  `;

  if (section) {
    section.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  try {
    const endpoint =
      API_BASE_URL +
      "/api/recommend?q=" +
      encodeURIComponent(cleanQuery);

    const response = await fetch(endpoint, { signal: controller.signal });

    if (!response.ok) {
      throw new Error(`Shopping API returned HTTP ${response.status}`);
    }

    const data = await response.json();

    if (requestId !== recommendationRequestId) return;

    console.log("Shopping Brain live response:", data);

    const recommendations = Array.isArray(data.recommendations)
      ? data.recommendations
      : [];

    // The backend keeps the legacy ranked pool for API compatibility and
    // exposes an auditable presentation split for generic under-budget
    // searches. Primary and value sections never relax the hard eligibility
    // or evidence gates.
    const recommendationSections = data.recommendation_sections &&
      typeof data.recommendation_sections === "object"
      ? data.recommendation_sections
      : {};
    const budgetBandMode = recommendationSections.mode === "budget_band";
    const primaryRecommendations = Array.isArray(data.primary_recommendations)
      ? data.primary_recommendations
      : recommendations;
    const valueRecommendations = Array.isArray(data.value_recommendations)
      ? data.value_recommendations
      : [];

    const exactModelQuery =
      Boolean(data.exact_model_scope) &&
      data.exact_model_scope.active === true;

    const recommendationPass =
      String(data.result_status || "").toUpperCase() === "PASS";

    const rawTotalSeconds =
      data.timings && data.timings.total_seconds;

    const totalSeconds =
      rawTotalSeconds != null &&
      rawTotalSeconds !== "" &&
      Number.isFinite(Number(rawTotalSeconds))
        ? Number(rawTotalSeconds)
        : null;

    const resultAnalytics = {
      search_term: analyticsQuery,
      result_status: String(data.result_status || ""),
      response_status: String(data.status || ""),
      recommendation_count: recommendations.length,
      exact_model_query: exactModelQuery ? 1 : 0,
      exact_model_success:
        exactModelQuery && recommendationPass &&
        recommendations.length > 0 ? 1 : 0,
      recommendation_pass: recommendationPass ? 1 : 0,
      zero_result: recommendations.length === 0 ? 1 : 0
    };

    if (Number.isFinite(totalSeconds)) {
      resultAnalytics.total_seconds = totalSeconds;
      resultAnalytics.api_latency_ms = Math.round(totalSeconds * 1000);
    }

    trackAnalyticsEvent("ai_search_result", resultAnalytics);

    if (recommendations.length > 0) {
      const topRecommendation = recommendations[0] || {};
      const topOffers = Array.isArray(topRecommendation.retailer_offers)
        ? topRecommendation.retailer_offers
        : [];

      const topBestOffer =
        topRecommendation.best_offer &&
        typeof topRecommendation.best_offer === "object"
          ? topRecommendation.best_offer
          : null;

      const topOffer = topBestOffer || topOffers[0] || {};
      const rawTopFit = topRecommendation.fit_percent;
      const topFit =
        rawTopFit != null &&
        rawTopFit !== "" &&
        Number.isFinite(Number(rawTopFit))
          ? Number(rawTopFit)
          : null;

      const viewAnalytics = {
        search_term: analyticsQuery,
        recommendation_count: recommendations.length,
        top_product_id: String(
          topOffer.product_id ||
          topRecommendation.product_id ||
          ""
        ),
        top_rank: Number(topRecommendation.rank || 1)
      };

      if (Number.isFinite(topFit)) {
        viewAnalytics.top_fit_percent = topFit;
      }

      trackAnalyticsEvent("recommendation_view", viewAnalytics);
    }

    if (recommendations.length === 0) {
      trackAnalyticsEvent("zero_result", {
        search_term: analyticsQuery,
        result_status: String(data.result_status || ""),
        exact_model_query: exactModelQuery ? 1 : 0
      });

      if (data.research_comparison && data.request_route === "research_comparison") {
        card.innerHTML = renderResearchComparison(data.research_comparison);
      } else if (isResearchComparisonQuery(cleanQuery)) {
        const fallbackComparison = await loadResearchComparisonFallback(cleanQuery, controller.signal);
        if (fallbackComparison) {
          card.innerHTML = renderResearchComparison(fallbackComparison);
          return;
        }
        card.innerHTML = `<h3>Verified smartphone research is temporarily unavailable</h3><p>Please try the comparison again.</p>`;
      } else if (String(data.market_data_status || "").toUpperCase() === "CURRENT_OFFERS_UNAVAILABLE") {
        card.innerHTML = renderOfferUnavailable();
      } else {
        card.innerHTML = `
          <h3>No strong match found</h3>
          <p>Try changing the budget, RAM, storage, brand or other requirements.</p>
        `;
      }
      return;
    }

    const renderRecommendation = (p) => {
      const title = escapeHTML(p.title || "Recommended Product");
      const brand = escapeHTML(p.brand || "Not available");
      const fitNumber =
        p.fit_percent != null &&
        p.fit_percent !== "" &&
        Number.isFinite(Number(p.fit_percent))
          ? Math.max(0, Math.min(100, Number(p.fit_percent)))
          : null;

      const fitDisplay =
        fitNumber != null ? `${fitNumber}%` : "Not available";

      const evidenceNumber =
        p.evidence_coverage_percent != null &&
        p.evidence_coverage_percent !== "" &&
        Number.isFinite(Number(p.evidence_coverage_percent))
          ? Math.max(0, Math.min(100, Number(p.evidence_coverage_percent)))
          : null;

      const evidenceDisplay =
        evidenceNumber != null ? `${evidenceNumber}%` : "Not available";

      const confidence = escapeHTML(p.confidence || "unknown");
      const capabilityDisplay = p.quality_score != null && Number.isFinite(Number(p.quality_score))
        ? `${Math.max(0, Math.min(100, Number(p.quality_score)))}/100`
        : "Not available";

      const scoreTrace = p.score_trace && typeof p.score_trace === "object"
        ? p.score_trace
        : {};
      const traceCriteria = Array.isArray(scoreTrace.criteria)
        ? scoreTrace.criteria
        : [];
      const scoreTraceRows = traceCriteria.map((criterion) => {
        const match = criterion.match_score == null
          ? "UNKNOWN"
          : `${Math.round(Number(criterion.match_score) * 100)}%`;
        const points = criterion.match_score == null
          ? "0"
          : `${criterion.weighted_points ?? 0} / ${criterion.weight ?? 0}`;
        return `<tr>
          <td>${escapeHTML(criterion.criterion || "criterion")}</td>
          <td>${escapeHTML(String(criterion.weight ?? ""))}</td>
          <td>${escapeHTML(match)}</td>
          <td>${escapeHTML(points)}</td>
          <td>${escapeHTML(criterion.evidence_status || "unknown")}</td>
          <td>${criterion.source_url ? `<a href="${escapeHTML(safeLink(criterion.source_url))}" target="_blank" rel="noopener">source</a>` : "UNKNOWN"}</td>
          <td>${escapeHTML(criterion.observed_at || "UNKNOWN")}</td>
          <td>${escapeHTML(criterion.reason || "No reliable evidence available")}</td>
        </tr>`;
      }).join("");
      const scoreTraceHTML = traceCriteria.length
        ? `<details class="ai-score-trace">
            <summary>Why this Fit Score?</summary>
            <p><strong>Raw Fit:</strong> ${escapeHTML(String(p.raw_fit_percent ?? "Not available"))}% · <strong>Evidence Coverage:</strong> ${escapeHTML(String(p.evidence_coverage_percent ?? "Not available"))}% · <strong>Policy:</strong> ${escapeHTML(scoreTrace.policy_version || "Not available")}</p>
            <p><strong>Eligibility:</strong> ${scoreTrace.eligibility && scoreTrace.eligibility.eligible ? "eligible" : "not eligible"}</p>
            <table><thead><tr><th>Criterion</th><th>Weight</th><th>Match</th><th>Points / max</th><th>Evidence</th><th>Source</th><th>Observed</th><th>Reason</th></tr></thead><tbody>${scoreTraceRows}</tbody></table>
          </details>`
        : "";

      const offers = Array.isArray(p.retailer_offers)
        ? p.retailer_offers.filter(offer =>
            offer &&
            offer.cta_eligibility &&
            offer.cta_eligibility.eligible === true &&
            (!Object.prototype.hasOwnProperty.call(p, "current_offer_verified") || p.current_offer_verified === true)
          )
        : [];
      const hasExplicitOfferContract = Object.prototype.hasOwnProperty.call(
        p,
        "current_offer_verified"
      );
      const currentOfferVerified = hasExplicitOfferContract &&
        p.current_offer_verified === true;

      // Respect the backend comparison contract:
      // best_offer exists only when enough trustworthy comparable
      // retailer offers are available. A single verified offer is
      // still useful, but must not be presented as "best".
      const bestOffer =
        p.best_offer &&
        typeof p.best_offer === "object" &&
        p.best_offer.cta_eligibility &&
        p.best_offer.cta_eligibility.eligible === true &&
        (!hasExplicitOfferContract || currentOfferVerified)
          ? p.best_offer
          : null;
      const purchaseCtaEligible = hasExplicitOfferContract
        ? p.purchase_cta_eligible === true && currentOfferVerified
        : Boolean(bestOffer || offers.length > 0);

      const primaryOffer = bestOffer || offers[0] || {};
      const priceEvidence =
        p.provenance && p.provenance.price_evidence
          ? p.provenance.price_evidence
          : {};
      const exactVariant = p.identity_evidence && p.identity_evidence.variant || {};

      const variant = primaryOffer.variant
        ? escapeHTML(primaryOffer.variant)
        : exactVariant.ram_gb && exactVariant.storage_gb
          ? `${escapeHTML(exactVariant.ram_gb)}GB/${escapeHTML(exactVariant.storage_gb)}GB`
          : "Not available";

      const retailer = primaryOffer.retailer
        ? escapeHTML(primaryOffer.retailer)
        : "Not available";

      const retailerHeading = currentOfferVerified && bestOffer
        ? "Best verified retailer"
        : currentOfferVerified && offers.length > 0
          ? "Verified retailer"
          : hasExplicitOfferContract
            ? "Retailer information"
            : "Retailer";

      const lastChecked = primaryOffer.last_checked
        ? escapeHTML(primaryOffer.last_checked)
        : priceEvidence.verified_at ? escapeHTML(priceEvidence.verified_at) : "Not available";

      const retailerAvailability = String(
        primaryOffer.availability || ""
      ).trim().toLowerCase();

      let priceStatusRaw;

      if (p.price_status) {
        priceStatusRaw = p.price_status;
      } else if (offers.length > 0) {
        if (
          primaryOffer.price != null &&
          primaryOffer.price !== ""
        ) {
          priceStatusRaw =
            retailerAvailability &&
            retailerAvailability !== "unknown"
              ? `price available ? ${retailerAvailability.replaceAll("_", " ")}`
              : "price available ? availability not verified";
        } else {
          priceStatusRaw = "price unavailable";
        }
      } else {
        priceStatusRaw = priceEvidence.status || "CURRENT_OFFER_UNAVAILABLE";
      }

      const priceStatus = escapeHTML(
        String(priceStatusRaw).replaceAll("_", " ")
      );

      const priceStatusHeading =
        offers.length > 0
          ? "Retailer offer status"
          : "Price status";

      const imageUrl = safeLink(p.image_url);

      const selectedPrice =
        primaryOffer.price != null &&
        primaryOffer.price !== ""
          ? primaryOffer.price
          : purchaseCtaEligible ? p.price : null;

      const price =
        purchaseCtaEligible &&
        selectedPrice != null &&
        selectedPrice !== ""
          ? `\u20B9${escapeHTML(selectedPrice)}`
          : "Current price unavailable";
      // The former "Check latest price" label was intentionally replaced:
      // unverified historical values must never look current or purchase-ready.

      // retailer_offers and best_offer are sanitized by the backend.
      // Prefer that exact retailer URL so displayed retailer, price
      // and CTA all refer to the same offer.
      const informationalLink = escapeHTML(safeLink(
        primaryOffer.product_url ||
        priceEvidence.source_url ||
        p.market_source ||
        p.official_source ||
        p.link
      ));
      const productLink = purchaseCtaEligible
        ? escapeHTML(safeLink(primaryOffer.product_url))
        : informationalLink;

      const offerCtaLabel = bestOffer
        ? "View Best Verified Offer \u2192"
        : offers.length > 0
          ? "Check Verified Retailer \u2192"
          : "Check Price \u2192";

      // Keep the requested retailer choices visible without inventing links
      // or prices. A button is active only for an exact sanitized offer.
      const retailerButtonsHTML = [
        { key: "amazon", label: "Amazon" },
        { key: "flipkart", label: "Flipkart" },
        { key: "croma", label: "Croma" }
      ].map(({ key, label }) => {
        const offer = offers.find(item =>
          String(item.retailer || "").trim().toLowerCase() === key &&
          String(item.availability || "").trim().toLowerCase() === "in_stock" &&
          safeLink(item.product_url) !== "#"
        );
        if (!offer) {
          return `<span class="retailer-choice retailer-choice-disabled" aria-disabled="true">${label}<small>Not verified</small></span>`;
        }
        const offerPrice = offer.price != null && offer.price !== ""
          ? ` · ₹${escapeHTML(offer.price)}`
          : "";
        return `<a class="retailer-choice" href="${escapeHTML(safeLink(offer.product_url))}" target="_blank" rel="nofollow sponsored noopener" data-ai-retailer-click="1" data-ai-rank="${escapeHTML(p.rank || "")}" data-ai-product-id="${escapeHTML(offer.product_id || p.product_id || "")}" data-ai-retailer="${label}">${label}${offerPrice}</a>`;
      }).join("");

      const why = Array.isArray(p.why_it_fits)
        ? p.why_it_fits
        : [];

      const whyHTML = why.length
        ? `
          <div class="ai-detail-block ai-positive">
            <div class="ai-detail-title">Why it fits</div>
            <ul class="ai-reasons">
              ${why.map(item => `<li>${escapeHTML(item)}</li>`).join("")}
            </ul>
          </div>
        `
        : "";

      const tradeoffs = Array.isArray(p.tradeoffs)
        ? p.tradeoffs
        : [];

      const tradeoffsHTML = tradeoffs.length
        ? `
          <div class="ai-detail-block ai-tradeoffs">
            <div class="ai-detail-title">Trade-offs</div>
            <ul>
              ${tradeoffs.map(item => `<li>${escapeHTML(item)}</li>`).join("")}
            </ul>
          </div>
        `
        : "";

      const unknowns = Array.isArray(p.unknown)
        ? p.unknown
        : [];

      const unknownsHTML = unknowns.length
        ? `
          <div class="ai-detail-block ai-unknowns">
            <div class="ai-detail-title">Missing / uncertain evidence</div>
            <ul>
              ${unknowns.map(item => `<li>${escapeHTML(item)}</li>`).join("")}
            </ul>
          </div>
        `
        : "";

      return `
        <article class="ai-result-card">
          <div class="ai-result-rank">#${escapeHTML(p.rank || "")}</div>

          ${
            imageUrl !== "#"
              ? `
                <div class="ai-result-image-wrap">
                  <img
                    class="ai-result-image"
                    src="${escapeHTML(imageUrl)}"
                    alt="${title}"
                    loading="lazy"
                  />
                </div>
              `
              : ""
          }

          <h3>${title}</h3>

          <div class="ai-meta-grid">
            <div class="ai-meta-chip">
              <span>Brand</span>
              <strong>${brand}</strong>
            </div>
            <div class="ai-meta-chip">
              <span>Variant</span>
              <strong>${variant}</strong>
            </div>
            <div class="ai-meta-chip">
              <span>${retailerHeading}</span>
              <strong>${retailer}</strong>
            </div>
            <div class="ai-meta-chip">
              <span>${priceStatusHeading}</span>
              <strong>${priceStatus}</strong>
            </div>
          </div>

          <div class="ai-metrics">
            <div class="ai-meter">
              <div class="ai-meter-row">
                <span>Requirement Match</span>
                <strong>${fitDisplay}</strong>
              </div>
              ${
                fitNumber != null
                  ? `
                    <div class="ai-meter-track">
                      <span class="ai-meter-fill" style="width:${fitNumber}%"></span>
                    </div>
                  `
                  : ""
              }
            </div>

            <div class="ai-meter">
              <div class="ai-meter-row">
                <span>Evidence Coverage</span>
                <strong>${evidenceDisplay}</strong>
              </div>
              ${
                evidenceNumber != null
                  ? `
                    <div class="ai-meter-track">
                      <span class="ai-meter-fill" style="width:${evidenceNumber}%"></span>
                    </div>
                  `
                  : ""
              }
            </div>
          </div>

          ${scoreTraceHTML}

          <p><strong>AI Confidence:</strong> ${confidence}</p>
          <p><strong>Capability match:</strong> ${capabilityDisplay} <small>(known specifications; missing evidence is listed below)</small></p>
          <p><strong>Price:</strong> ${price}</p>
          <p class="ai-last-checked"><strong>Last checked:</strong> ${lastChecked}</p>

          ${whyHTML}
          ${tradeoffsHTML}
          ${unknownsHTML}

          <div class="retailer-choice-group" aria-label="Verified retailer choices">
            ${retailerButtonsHTML}
          </div>
          <p class="retailer-availability-note">
            Amazon, Flipkart and Croma links activate only when this exact variant has a fresh verified in-stock offer.
          </p>

          ${
            productLink !== "#" && purchaseCtaEligible
              ? `
                <a
                  class="shop-button"
                  href="${productLink}"
                  target="_blank"
                  rel="nofollow sponsored noopener"
                  data-ai-retailer-click="1"
                  data-ai-rank="${escapeHTML(p.rank || "")}"
                  data-ai-product-id="${escapeHTML(
                    primaryOffer.product_id || p.product_id || ""
                  )}"
                  data-ai-retailer="${retailer}"
                >
                  ${offerCtaLabel}
                </a>
              `
              : productLink !== "#"
                ? `
                <a
                  class="card-note"
                  href="${productLink}"
                  target="_blank"
                  rel="noopener"
                >
                  View product information →
                </a>
                `
              : `
                <p class="card-note">
                  Retailer link is currently unavailable.
                </p>
              `
          }
        </article>
      `;
    };

    const primaryCards = primaryRecommendations
      .map(renderRecommendation)
      .join("");
    const valueCards = valueRecommendations
      .map(renderRecommendation)
      .join("");

    card.innerHTML = `
      ${budgetBandMode
        ? `<section class="ai-recommendation-section ai-primary-section">
            <h2>${escapeHTML(recommendationSections.primary_title || "Top verified phones")}</h2>
            <p class="ai-section-note">Capability ranking is unchanged; this section keeps primary picks close to your declared budget.</p>
            <div class="ai-section-card-grid">
              ${primaryCards || `<p class="card-note">${escapeHTML(recommendationSections.no_primary_message || "No currently verified phones found in the primary range.")}</p>`}
            </div>
          </section>`
        : `<div class="ai-section-card-grid">${primaryCards}</div>`}
      ${budgetBandMode && valueCards
        ? `<section class="ai-recommendation-section ai-value-section">
            <h2>${escapeHTML(recommendationSections.value_title || "Best Value Alternatives")}</h2>
            <p class="ai-section-note">These verified phones are below the primary band and are shown separately as value alternatives.</p>
            <div class="ai-section-card-grid">${valueCards}</div>
          </section>`
        : ""}
    `;

    const categoryResults = data.category_results && typeof data.category_results === "object"
      ? data.category_results
      : {};
    const unavailableCategories = ["camera", "battery", "gaming", "performance"].filter(name =>
      categoryResults[name] &&
      categoryResults[name].status === "CATEGORY_EVIDENCE_UNAVAILABLE"
    );
    if (unavailableCategories.length) {
      card.insertAdjacentHTML("beforeend", `
        <p class="card-note">
          Specialist sections unavailable: ${escapeHTML(unavailableCategories.join(", "))}. No unsupported category winners were added.
        </p>
      `);
    }

    const dynamicReference = data.dynamic_reference &&
      typeof data.dynamic_reference === "object"
      ? data.dynamic_reference
      : null;
    if (dynamicReference) {
      const requestedSnapshot = dynamicReference.requested_snapshot &&
        typeof dynamicReference.requested_snapshot === "object"
        ? dynamicReference.requested_snapshot
        : {};
      const referenceRows = Array.isArray(requestedSnapshot.metrics)
        ? requestedSnapshot.metrics.filter(metric => metric && metric.sample_size > 0)
        : [];
      const referenceStatus = String(dynamicReference.reference_status || "LIVE_ELIGIBLE_POOL_EMPTY");
      const statusLabel = referenceStatus === "LIVE_VERIFIED_BUYABLE"
        ? "Live verified reference"
        : referenceStatus === "RESEARCH_REFERENCE_ONLY"
          ? "Research reference only"
        : `Live reference unavailable (${referenceStatus})`;
      const rowsHTML = referenceRows.map(metric => `
        <tr>
          <td>${escapeHTML(metric.metric_name || "metric")}</td>
          <td>${escapeHTML(metric.reference_product_id || "UNAVAILABLE")}</td>
          <td>${escapeHTML(String(metric.metric_reference_value ?? "UNAVAILABLE"))} ${escapeHTML(metric.metric_unit || "")}</td>
          <td>${escapeHTML(String(metric.sample_size ?? 0))}</td>
        </tr>
      `).join("");
      card.insertAdjacentHTML("beforeend", `
        <section class="ai-detail-block ai-dynamic-reference" aria-label="Dynamic benchmark reference">
          <div class="ai-detail-title">Budget benchmark reference</div>
          <p><strong>${escapeHTML(statusLabel)}</strong> · Budget ₹${escapeHTML(String(dynamicReference.requested_budget_inr ?? "Not available"))} · Version ${escapeHTML(String(dynamicReference.benchmark_version || "Not available"))}</p>
          ${referenceRows.length
            ? `<table><thead><tr><th>Metric</th><th>Reference</th><th>Value</th><th>Sample</th></tr></thead><tbody>${rowsHTML}</tbody></table>`
            : `<p class="card-note">No comparable verified metric reference is available for the current live eligible pool. Research-only values are not shown as buyable recommendations.</p>`}
        </section>
      `);
    }

    if (
      !budgetBandMode &&
      !exactModelQuery &&
      String(data.intent && data.intent.category || "").toLowerCase() === "smartphone" &&
      recommendations.length < 3
    ) {
      const nearby = Array.isArray(data.closest_matches)
        ? data.closest_matches.filter(p =>
            p && p.why_not_recommended ===
              "Below the minimum verified Fit threshold"
          ).slice(0, 3 - recommendations.length)
        : [];

      card.insertAdjacentHTML("beforeend", `
        <section class="ai-detail-block ai-unknowns" aria-label="Other researched phones">
          <h3>Only ${recommendations.length} phone${recommendations.length === 1 ? "" : "s"} met the recommendation standard</h3>
          <p>${nearby.length
            ? "Other phones with official product evidence are shown separately because their Fit is below 50%. They are not recommendations."
            : "No additional phones passed the identity, evidence and Fit checks."}</p>
          ${nearby.length ? `<ul>${nearby.map(p => `
            <li>${escapeHTML(p.title || "Phone")} —
              ${p.price == null ? "Price unverified" : `₹${escapeHTML(p.price)}`},
              Fit ${escapeHTML(p.fit_percent || 0)}%
            </li>
          `).join("")}</ul>` : ""}
        </section>
      `);
    }

    card
      .querySelectorAll('a[data-ai-retailer-click="1"]')
      .forEach(link => {
        link.addEventListener("click", () => {
          trackAnalyticsEvent("retailer_click", {
            search_term: analyticsQuery,
            product_id: link.dataset.aiProductId || "",
            retailer: link.dataset.aiRetailer || "",
            recommendation_rank: Number(link.dataset.aiRank || 0)
          });
        });
      });

  } catch (error) {
    if (requestId !== recommendationRequestId) return;
    console.error("Unable to load Shopping Brain response:", error);

    trackAnalyticsEvent("ai_search_error", {
      search_term: analyticsQuery,
      error_type: String(error && error.name || "Error").slice(0, 40)
    });

    const fallbackComparison = await loadResearchComparisonFallback(cleanQuery);
    if (fallbackComparison) {
      card.innerHTML = renderResearchComparison(fallbackComparison);
      return;
    }
    const timedOut = error && error.name === "AbortError";
    const message = timedOut
      ? "The recommendation service took too long to respond."
      : error && /^Shopping API returned HTTP 4/.test(error.message || "")
        ? "Please check the search and try again."
        : error && /^Shopping API returned HTTP 5/.test(error.message || "")
          ? "The recommendation service is temporarily unavailable."
          : "We could not reach the recommendation service.";
    card.innerHTML = `
      <h3>Recommendation temporarily unavailable</h3>
      <p>${escapeHTML(message)}</p>
      <button type="button" class="btn btn-ghost" data-retry-recommendation>Try again</button>
    `;
    card.querySelector("[data-retry-recommendation]")?.addEventListener("click", () => {
      loadShoppingRecommendation(cleanQuery);
    });
  } finally {
    window.clearTimeout(timeoutHandle);
    if (recommendationController === controller) recommendationController = null;
  }
}

loadShoppingRecommendation("");
