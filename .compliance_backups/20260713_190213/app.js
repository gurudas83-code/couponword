const DEALS_FILE = "/coupons.json?v=" + Date.now();

let allDeals = [];
let activeCategory = "All";
let activeView = "grid";

const grid = document.getElementById("dealsGrid");
const searchInput = document.getElementById("searchInput");
const heroSearch = document.getElementById("heroSearch");
const heroSearchButton = document.getElementById("heroSearchButton");
const sortSelect = document.getElementById("sortSelect");
const chipsBox = document.getElementById("categoryChips");
const resultsCount = document.getElementById("resultsCount");

async function loadDeals() {
  try {
    const res = await fetch(DEALS_FILE);
    if (!res.ok) throw new Error("coupons.json not found");

    allDeals = await res.json();

    updateStats();
    buildCategoryChips();
    renderFeaturedDeal();
    renderDeals();
  } catch (err) {
    grid.innerHTML = `<div class="state-card"><strong>Unable to load deals</strong><span>Check coupons.json file.</span></div>`;
    resultsCount.textContent = "No deals loaded";
  }
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

  deals.sort((a, b) => {
    const aUnavailable = a.active === false ? 1 : 0;
    const bUnavailable = b.active === false ? 1 : 0;
    return aUnavailable - bUnavailable;
  });

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
  const deal = allDeals.find(item => item.active !== false) || allDeals[0];

  if (!deal) return;

  box.innerHTML = `
    ${renderImage(deal, "spotlight-image")}
    <h2>${escapeHTML(deal.title || "Hot Deal")}</h2>
    <p>${escapeHTML(deal.discount || "Latest offer")} • ${escapeHTML(deal.category || "Deal")}</p>
    <a href="${safeLink(deal.link)}" target="_blank" rel="nofollow sponsored noopener">View on Amazon</a>
  `;
}

function productSlug(value, maxLength = 70) {
  let slug = normalize(value)
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");

  if (!slug) {
    slug = "product";
  }

  if (slug.length > maxLength) {
    slug = slug.slice(0, maxLength).replace(/-+$/g, "");
  }

  return slug;
}

function getProductPageLink(deal) {
  const suffix = String(
    deal.asin || deal.id || deal.sl_no || "item"
  ).toLowerCase();

  return `products/${productSlug(deal.title) + "-" + suffix}/`;
}

function renderDeals() {
  const deals = getFilteredDeals();

  resultsCount.textContent = `${deals.length} deal${deals.length !== 1 ? "s" : ""} found`;

  if (!deals.length) {
    grid.innerHTML = `<div class="state-card"><strong>No matching deals found</strong><span>Try another keyword or category.</span></div>`;
    return;
  }

  grid.className = activeView === "compact" ? "deal-grid compact" : "deal-grid";

  grid.innerHTML = deals.map(deal => {
    const unavailable = deal.active === false ||
      normalize(deal.availability) === "unavailable";
    const productPage = getProductPageLink(deal);

    return `
    <article class="deal-card ${unavailable ? "deal-card-unavailable" : ""}">
      <a class="product-media-link" href="${productPage}" aria-label="View ${escapeHTML(deal.title || "product")} details">
        ${renderImage(deal, "deal-image")}
      </a>

      <div class="deal-meta">
        <span class="store">${escapeHTML(deal.store || "Amazon IN")}</span>
        <span class="category-pill">${escapeHTML(deal.category || "Deal")}</span>
      </div>

      <h3 class="deal-title">
        <a href="${productPage}">
          ${escapeHTML(deal.title || "Amazon Product Deal")}
        </a>
      </h3>

      <div class="discount">
        ${unavailable
          ? "Currently unavailable"
          : escapeHTML(deal.discount || "Check latest price on Amazon")}
      </div>

      <div class="price-row">
        ${deal.price ? `<span class="price">${escapeHTML(deal.price)}</span>` : ""}
        ${deal.mrp ? `<span class="mrp">${escapeHTML(deal.mrp)}</span>` : ""}
        ${deal.save ? `<span class="save">${escapeHTML(deal.save)}</span>` : ""}
      </div>

      <p class="description">${escapeHTML(deal.description || "Check latest price and offer on Amazon before buying.")}</p>

      <div class="code-row">
        <span>${escapeHTML(deal.code || "NO CODE NEEDED")}</span>
        <span>${escapeHTML(deal.expiry || "Limited Time")}</span>
      </div>

      <div class="card-actions">
        <a class="details-button" href="${productPage}">
          View Details
        </a>

        ${unavailable
          ? `<span class="shop-button shop-button-disabled" aria-disabled="true">
               Currently Unavailable
             </span>`
          : `<a class="shop-button" href="${safeLink(deal.link)}"
                target="_blank"
                rel="nofollow sponsored noopener">
               Shop Now →
             </a>`
        }
      </div>

      <div class="card-note">
        ${unavailable
          ? "Product currently unavailable on Amazon"
          : "Affiliate link • Final price on Amazon may change"}
      </div>
    </article>
    `;
  }).join("");
}

function getCategoryPlaceholder(deal) {
  const category = normalize(deal.category);
  const title = normalize(deal.title);

  if (
    category.includes("security camera") ||
    title.includes("camera") ||
    title.includes("cctv")
  ) {
    return "📹";
  }

  if (
    title.includes("earbud") ||
    title.includes("headphone") ||
    title.includes("buds") ||
    title.includes("tws")
  ) {
    return "🎧";
  }

  if (
    category.includes("mobile") ||
    title.includes("iphone") ||
    title.includes("smartphone")
  ) {
    return "📱";
  }

  if (
    category.includes("home") ||
    category.includes("kitchen")
  ) {
    return "🏠";
  }

  if (
    category.includes("beauty") ||
    category.includes("personal care")
  ) {
    return "✨";
  }

  if (
    category.includes("fashion") ||
    category.includes("footwear") ||
    title.includes("shoe")
  ) {
    return "👟";
  }

  if (
    category.includes("toy") ||
    title.includes("kids")
  ) {
    return "🧸";
  }

  if (
    category.includes("electronics")
  ) {
    return "⚡";
  }

  return "🛍️";
}

function renderImage(deal, className) {
  const placeholderIcon = getCategoryPlaceholder(deal);

  if (deal.image) {
    return `
      <div class="${className}">
        <img
          src="${escapeHTML(deal.image)}"
          alt="${escapeHTML(deal.title || "Deal image")}"
          loading="lazy"
          onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
        >
        <div class="placeholder image-fallback" style="display:none">
          ${placeholderIcon}
          <small>${escapeHTML(deal.category || "Coupon World")}</small>
        </div>
      </div>
    `;
  }

  return `
    <div class="${className}">
      <div class="placeholder">
        ${placeholderIcon}
        <small>${escapeHTML(deal.category || "Coupon World")}</small>
      </div>
    </div>
  `;
}

function applySearch(value) {
  searchInput.value = value || "";
  document.getElementById("browse").scrollIntoView({ behavior: "smooth" });
  renderDeals();
}

function safeLink(link) {
  return link || "#";
}

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

heroSearchButton.addEventListener("click", () => applySearch(heroSearch.value));
heroSearch.addEventListener("keydown", e => {
  if (e.key === "Enter") applySearch(heroSearch.value);
});

document.querySelectorAll("[data-search]").forEach(el => {
  el.addEventListener("click", () => applySearch(el.dataset.search));
});

document.querySelectorAll("[data-quick]").forEach(el => {
  el.addEventListener("click", () => applySearch(el.dataset.quick));
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
