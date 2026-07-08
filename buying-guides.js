async function loadBuyingGuides() {
  const container = document.getElementById("guideContainer");

  try {
    const response = await fetch("/data/seo-pages.json?v=" + Date.now());
    const pages = await response.json();

    const readyPages = pages
      .filter(page => page.status === "ready")
      .sort((a, b) => (a.priority || 999) - (b.priority || 999));

    if (!readyPages.length) {
      container.innerHTML = "<p>No buying guides found.</p>";
      return;
    }

    container.innerHTML = readyPages.map(page => `
      <article class="deal-card">
        <div class="deal-meta">
          <span class="store">${escapeHTML(page.intent || "Guide")}</span>
          <span class="category-pill">${escapeHTML(page.category || "Shopping")}</span>
        </div>

        <h3 class="deal-title">${escapeHTML(page.title)}</h3>

        <p class="description">
          ${escapeHTML(page.metaDescription || "Read this Coupon World buying guide before shopping online.")}
        </p>

        <div class="code-row">
          <span>Keyword</span>
          <span>${escapeHTML(page.keyword || "")}</span>
        </div>

        <a class="shop-button" href="/seo/${escapeHTML(page.slug)}.html">
          Read Guide →
        </a>
      </article>
    `).join("");

  } catch (error) {
    container.innerHTML = `
      <div class="state-card">
        <strong>Unable to load buying guides</strong>
        <span>Please check data/seo-pages.json</span>
      </div>
    `;
  }
}

function escapeHTML(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

loadBuyingGuides();
