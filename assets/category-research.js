/* Progressive enhancement for source-reviewed category research.
   No merchant prices, scoring, identity promotions or API requests. */
(() => {
  "use strict";
  const source = document.getElementById("cr-payload");
  const grid = document.getElementById("cr-grid");
  if (!source || !grid) return;
  const payload = JSON.parse(source.textContent || "{}");
  const records = Array.isArray(payload.records) ? payload.records : [];
  const bySlug = new Map(records.map(record => [record.slug, record]));
  const query = document.getElementById("cr-query");
  const brand = document.getElementById("cr-brand");
  const type = document.getElementById("cr-type");
  const form = document.getElementById("cr-filters");
  const status = document.getElementById("cr-status");
  const noResults = document.getElementById("cr-no-results");
  const panel = document.getElementById("cr-comparison");
  const tableHost = document.getElementById("cr-comparison-table");
  const compareStatus = document.getElementById("cr-comparison-status");
  const clear = document.getElementById("cr-clear-compare");
  const selected = new Set();

  const fold = value => String(value || "").toLocaleLowerCase("en-IN").trim();

  function filterRecords() {
    let visible = 0;
    const phrase = fold(query.value);
    for (const card of grid.querySelectorAll("[data-model]")) {
      const matches = (!phrase || fold(card.dataset.search).includes(phrase)) &&
        (!brand.value || card.dataset.brand === brand.value) &&
        (!type.value || card.dataset.type === type.value);
      card.hidden = !matches;
      visible += Number(matches);
    }
    status.textContent = visible + " of " + records.length + " source-reviewed models shown.";
    noResults.hidden = visible > 0;
  }

  function makeCell(tag, text) {
    const cell = document.createElement(tag);
    cell.textContent = String(text);
    return cell;
  }

  function comparison() {
    tableHost.replaceChildren();
    const items = [...selected].map(id => bySlug.get(id)).filter(Boolean);
    panel.hidden = !items.length;
    if (!items.length) {
      compareStatus.textContent = "";
      return;
    }
    compareStatus.textContent = items.length +
      " selected · Source claims only. Unknown facts are not zeros or negative performance scores.";
    const table = document.createElement("table");
    table.className = "cr-compare-table";
    const head = document.createElement("thead");
    const header = document.createElement("tr");
    header.append(makeCell("th", "Documented fact"));
    for (const item of items) header.append(makeCell("th", item.model));
    head.append(header);
    table.append(head);
    const body = document.createElement("tbody");
    const labels = new Set(items.flatMap(item => item.specifications.map(field => field.label)));
    for (const label of labels) {
      const row = document.createElement("tr");
      row.append(makeCell("th", label));
      for (const item of items) {
        const match = item.specifications.find(field => field.label === label);
        const cell = makeCell("td", match ? match.value : "Not documented");
        if (match && match.source_url) {
          const link = document.createElement("a");
          link.href = match.source_url;
          link.target = "_blank";
          link.rel = "noopener noreferrer";
          link.textContent = " Source";
          cell.append(link);
        }
        row.append(cell);
      }
      body.append(row);
    }
    table.append(body);
    tableHost.append(table);
  }

  grid.addEventListener("change", event => {
    const control = event.target.closest("input[data-compare]");
    if (!control) return;
    const item = bySlug.get(control.dataset.compare);
    if (!item) {
      control.checked = false;
      return;
    }
    if (control.checked) {
      const first = bySlug.get([...selected][0]);
      if (selected.size >= 3 || (first && first.product_type !== item.product_type)) {
        control.checked = false;
        status.textContent = selected.size >= 3
          ? "Compare a maximum of three models."
          : "Select models of the same product type to compare meaningful facts.";
        return;
      }
      selected.add(item.slug);
    } else {
      selected.delete(item.slug);
    }
    comparison();
  });

  for (const control of [query, brand, type]) control.addEventListener("input", filterRecords);
  form.addEventListener("reset", () => {
    window.setTimeout(filterRecords, 0);
  });
  clear.addEventListener("click", () => {
    selected.clear();
    for (const input of grid.querySelectorAll("input[data-compare]")) input.checked = false;
    comparison();
  });

  const phrase = new URLSearchParams(window.location.search).get("q");
  if (phrase) {
    query.value = phrase.slice(0, 120);
  }
  filterRecords();
})();
