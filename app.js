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
    grid.innerHTML = `
      <div class="state-card">
        <strong>Unable to load deals</strong>
        <span>Please check coupons.json file path and JSON validity.</span>
      </div>
    `;
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

function getFilteredDeals() {
  const query = normalize(searchInput.value);

  let deals = allDeals.filter(deal => {
    const matchSearch = normalize(getSearchText(deal)).includes(query);
    const matchCategory =
      activeCategory === "All" ||
      normalize(deal.category) === normalize(activeCategory);

    return matchSearch && matchCategory;
  });

  const sort = sortSelect.value;

  if (sort === "az") {
    deals.sort((a, b) => String(a.title || "").localeCompare(String(b.title || "")));
  }

  if (sort === "discount") {
    deals.sort((a, b) => extractNumber(b.discount) - extractNumber(a.discount));
  }

  if (sort === "latest") {
    deals.sort((a, b) => Number(b.id || 0) - Number(a.id || 0));
  }

  return deals;
}

function extractNumber(value) {
  const match = String(value || "").match(/\d+/);
  return match ? Number(match[0]) : 0;
}

function updateStats() {
  document.getElementById("statDeals").textContent = allDeals.length;

  const categories = new Set(
    allDeals.map(d => d.category).filter(Boolean)
  );

  document.getElementById("statCategories").textContent = categories.size;
}

function buildCategoryChips() {
  const categories = ["All", ...new Set(allDeals.map(d => d.category).filter(Boolean))];

  chipsBox.innerHTML = categories.map(cat => `
    <button type="button" class="${cat === activeCategory ? "active" : ""}" data-category="${cat}">
      ${cat}
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

  if (!deal) return;

  box.innerHTML = `
    ${renderImage(deal, "spotlight-image")}
    <h2>${escapeHTML(deal.title || "Hot Deal")}</h2>
    <p>${escapeHTML(deal.discount || "Latest offer")} • ${escapeHTML(deal.category || "Deal")}</p>
    <a href="${safeLink(deal.link)}" target="_blank" rel="nofollow sponsored noopener">
      View on Store
    </a>
  `;
}

function renderDeals() {
  const deals = getFilteredDeals();

  resultsCount.textContent = `${deals.length} deal${deals.length !== 1 ? "s" : ""} found`;

  if (!deals.length) {
    grid.innerHTML = `
      <div class="state-card">
        <strong>No matching deals found</strong>
        <span>Try another search or category.</span>
      </div>
    `;
    return;
  }

  grid.className = activeView === "compact" ? "deal-grid compact-view" : "deal-grid";

  grid.innerHTML = deals.map(deal => `
    <article class="deal-card">
      <div class="deal-image-wrap">
        ${renderImage(deal, "deal-image")}
        <span class="deal-badge">${escapeHTML(deal.discount || "Deal")}</span>
      </div>

      <div class="deal-body">
        <div class="deal-meta">
          <span>${escapeHTML(deal.store || "Amazon IN")}</span>
          <span>${escapeHTML(deal.category || "Deal")}</span>
        </div>

        <h3>${escapeHTML(deal.title || "Amazon Product Deal")}</h3>

        <div class="price-row">
          ${deal.price ? `<strong>${escapeHTML(deal.price)}</strong>` : ""}
          ${deal.mrp ? `<del>${escapeHTML(deal.mrp)}</del>` : ""}
          ${deal.save ? `<small>${escapeHTML(deal.save)}</small>` : ""}
        </div>

        <div class="deal-extra">
          <span>Code: ${escapeHTML(deal.code || "NO CODE NEEDED")}</span>
          <span>${escapeHTML(deal.expiry || "Limited Time")}</span>
        </div>

        <a class="shop-btn" href="${safeLink(deal.link)}" target="_blank" rel="nofollow sponsored noopener">
          Shop Now →
        </a>
      </div>
    </article>
  `).join("");
}

function renderImage(deal, className) {
  if (deal.image) {
    return `
      <img class="${className}" src="${escapeHTML(deal.image)}" alt="${escapeHTML(deal.title || "Deal image")}" loading="lazy"
      onerror="this.outerHTML='<div class=&quot;${className} placeholder-img&quot;>🛍️</div>'">
    `;
  }

  return `<div class="${className} placeholder-img">🛍️</div>`;
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

heroSearchButton.addEventListener("click", () => {
  applySearch(heroSearch.value);
});

heroSearch.addEventListener("keydown", e => {
  if (e.key === "Enter") applySearch(heroSearch.value);
});

document.querySelectorAll("[data-search]").forEach(el => {
  el.addEventListener("click", () => {
    applySearch(el.dataset.search);
  });
});

document.querySelectorAll("[data-quick]").forEach(el => {
  el.addEventListener("click", () => {
    applySearch(el.dataset.quick);
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
