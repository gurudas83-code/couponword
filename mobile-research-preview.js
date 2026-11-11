(function () {
  "use strict";

  // This is a public, read-only research comparison. Live shopping remains on
  // the existing /api/recommend path and never consumes this dataset.
  var section = document.getElementById("mobileResearchPreview");
  var grid = document.getElementById("mobileResearchGrid");
  if (!section || !grid) return;

  var searchSection = document.getElementById("mobileResearchSearch");
  var researchQuery = document.getElementById("mobileResearchQuery");
  var researchSearchButton = document.getElementById("mobileResearchSearchButton");
  var researchResults = document.getElementById("mobileResearchResults");
  var researchResultsMore = document.getElementById("mobileResearchResultsMore");
  var researchSearchStatus = document.getElementById("mobileResearchSearchStatus");
  var researchNewSection = document.getElementById("mobileResearchNew");
  var researchNewGrid = document.getElementById("mobileResearchNewGrid");
  var detailSection = document.getElementById("mobileResearchDetail");
  var detailContent = document.getElementById("mobileResearchDetailContent");
  var detailTitle = document.getElementById("mobileResearchDetailTitle");

  var catalogueGrid = document.getElementById("catalogueDiscoveryGrid");
  var catalogueCount = document.getElementById("catalogueDiscoveryCount");
  var catalogueMore = document.getElementById("catalogueDiscoveryMore");
  var inventoryGrid = document.getElementById("mobileResearchCatalogueGrid");
  var inventoryCount = document.getElementById("mobileResearchCatalogueCount");
  var inventoryMore = document.getElementById("mobileResearchCatalogueMore");
  var inventoryQuery = document.getElementById("mobileResearchCatalogueQuery");
  var inventoryBrand = document.getElementById("mobileResearchCatalogueBrand");
  var inventoryRam = document.getElementById("mobileResearchCatalogueRam");
  var inventoryStorage = document.getElementById("mobileResearchCatalogueStorage");
  var inventoryStatus = document.getElementById("mobileResearchCatalogueStatus");
  var catalogueRows = [];
  var catalogueExpanded = false;
  var inventoryRows = [];
  var inventoryByKey = new Map();
  var verifiedById = new Map();
  var inventoryCards = [];
  var inventoryLoadFailed = false;
  var inventorySourceCounts = {};
  var verifiedRows = [];
  var CATALOGUE_INITIAL_LIMIT = 18;
  var INVENTORY_PAGE_SIZE = 18;
  var MAX_SEARCH_RESULTS = 6;
  var inventoryExpanded = false;
  var searchExpanded = false;
  var lastSearchQuery = "";
  var lastSearchMatches = [];
  var guidedControls = ["researchGuidedBudget", "researchGuidedPriority", "researchGuidedRam", "researchGuidedStorage", "researchGuidedExclude"].map(function (id) { return document.getElementById(id); });
  var guidedScope = document.getElementById("researchGuidedScope");
  var appliedFilters = document.getElementById("researchAppliedFilters");
  var clearSearchButton = document.getElementById("researchClearSearch");
  var guidedApply = document.getElementById("researchGuidedApply");
  var guidedStatus = document.getElementById("researchGuidedStatus");
  var comparisonSelection = [];
  var comparePanel = document.getElementById("mobileResearchCompare");
  var TECHNICAL_FIELD_LABELS = {
    chipset: "Chipset",
    gpu: "GPU",
    display_type: "Display technology",
    display_inches: "Display size",
    display_resolution: "Display resolution",
    display_size_description: "Display size",
    display_resolution_description: "Display resolution",
    display_refresh_max_hz: "Refresh rate",
    display_refresh_description: "Refresh rate",
    display_type_description: "Display technology",
    rear_main_mp: "Main camera",
    rear_ultrawide_mp: "Ultrawide camera",
    rear_telephoto_mp: "Telephoto camera",
    front_mp: "Front camera",
    ois: "OIS",
    battery_mah_typical: "Battery capacity",
    wired_charging_max_w: "Wired charging",
    launch_android: "Launch Android",
    os_upgrade_generations: "OS updates",
    security_support_years: "Security updates",
    ip_rating: "IP rating",
    network_support: "5G/network support",
    rear_camera_system: "Rear camera system",
    front_camera_system: "Front camera system",
    battery_capacity_description: "Battery capacity",
    charging_description: "Charging support",
    battery_and_charging: "Battery and charging",
    operating_system: "Operating system",
    security_update_policy: "Security update policy",
    durability: "Durability"
  };

  // Keep the research catalogue out of the idle homepage. It is revealed by an
  // explicit search, comparison link, or Browse All action.
  section.hidden = true;
  var catalogueSection = document.getElementById("mobileResearchCatalogue");
  if (catalogueSection) catalogueSection.hidden = true;

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function link(url, label) {
    if (!/^https:\/\//i.test(String(url || ""))) return "";
    var amazon = /^https:\/\/(?:www\.)?amazon\.in(?:[/?#]|$)/i.test(String(url));
    if (amazon) { var parsed = new URL(url); parsed.searchParams.set("tag", "guru07cc-21"); url = parsed.href; }
    return '<a class="mobile-research-link" href="' + escapeHtml(url) + '" target="_blank" rel="' + (amazon ? 'sponsored nofollow noopener noreferrer' : 'noopener noreferrer') + '">' + escapeHtml(label) + " ↗</a>";
  }

  function optionValues(rows, key) {
    var values = {};
    (rows || []).forEach(function (row) {
      if (row && row[key] != null && row[key] !== "") values[String(row[key])] = true;
    });
    return Object.keys(values).sort(function (a, b) { return Number(a) - Number(b) || a.localeCompare(b); });
  }

  function fillSelect(select, values, label) {
    if (!select) return;
    select.innerHTML = '<option value="">' + escapeHtml(label) + '</option>' + values.map(function (value) {
      return '<option value="' + escapeHtml(value) + '">' + escapeHtml(value) + '</option>';
    }).join("");
  }

  function inventoryVariantStatus(row) {
    if (row && row.status) return String(row.status);
    if (row && String(row.manufacturer_spec_status || "").toUpperCase() === "VERIFIED") return "OFFICIAL_VERIFIED";
    return "RESEARCH_ONLY";
  }

  function inventoryRowsForCard(card) {
    var discovery = (card.discovery_record_keys || []).map(function (key) {
      return inventoryByKey.get(key);
    }).filter(Boolean);
    var frozen = (card.frozen_variant_ids || []).map(function (id) {
      return verifiedById.get(id);
    }).filter(Boolean);
    var rows = discovery.concat(frozen);
    (card.verified_india_variants || []).forEach(function (variant) {
      if (rows.some(function (row) { return row.ram_gb === variant.ram_gb && row.storage_gb === variant.storage_gb; })) return;
      rows.push({
        ram_gb: variant.ram_gb, storage_gb: variant.storage_gb,
        status: "PARTIALLY_VERIFIED",
        variant_text: variant.ram_gb + "GB RAM / " + variant.storage_gb + "GB storage",
        source_urls: [variant.source_url]
      });
    });
    return rows;
  }

  function inventoryAllVariantRows() {
    return inventoryCards.reduce(function (all, card) { return all.concat(inventoryRowsForCard(card)); }, []);
  }

  function inventoryMatches(card) {
    var query = String(inventoryQuery && inventoryQuery.value || "").trim().toLowerCase();
    var brand = String(inventoryBrand && inventoryBrand.value || "");
    var ram = String(inventoryRam && inventoryRam.value || "");
    var storage = String(inventoryStorage && inventoryStorage.value || "");
    var status = String(inventoryStatus && inventoryStatus.value || "");
    var rows = inventoryRowsForCard(card);
    var haystack = (String(card.brand || "") + " " + String(card.model || "") + " " + rows.map(function (row) {
      return row.variant_text || ((row.ram_gb || "") + "GB " + (row.storage_gb || "") + "GB");
    }).join(" ")).toLowerCase();
    return (!query || haystack.indexOf(query) >= 0) &&
      (!brand || String(card.brand || "") === brand) &&
      rows.some(function (row) { return (!ram || String(row.ram_gb || "") === ram) && (!storage || String(row.storage_gb || "") === storage); }) &&
      (!status || rows.some(function (row) { return inventoryVariantStatus(row) === status; }));
  }

  function researchPhoneImage(card) {
    var photo = card.image_status === "VERIFIED_MATCH" && card.photo;
    if (photo) {
      return '<figure class="research-phone-photo"><img src="' + escapeHtml(photo.url) +
        '" width="' + escapeHtml(photo.width) + '" height="' + escapeHtml(photo.height) +
        '" loading="lazy" decoding="async" alt="' + escapeHtml(displayPhoneName(card)) +
        '"><figcaption>Model photo: <a href="' + escapeHtml(photo.source) + '">' +
        (photo.title ? escapeHtml(photo.title) + " by " : "") + escapeHtml(photo.author) + '</a> · <a href="' + escapeHtml(photo.license_url) +
        '">' + escapeHtml(photo.license) + '</a> · resized</figcaption></figure>';
    }
    return '<div class="research-phone-visual" aria-hidden="true"><img src="/assets/phone-study.svg" width="600" height="540" alt="" loading="lazy"><span>' + escapeHtml(card.brand) + ' / PHONE RESEARCH</span></div><p class="research-illustration-label">Illustration · not a product photo</p>';
  }

  function renderInventoryCard(card) {
    var rows = inventoryRowsForCard(card);
    var discoveryRows = rows.filter(function (row) { return !row.canonical_product_id; });
    var frozenRows = rows.filter(function (row) { return !!row.canonical_product_id; });
    var statuses = Array.from(new Set(rows.map(inventoryVariantStatus)));
    var statusLabel = card.status || (statuses.length === 1 ? statuses[0] : "MIXED_EVIDENCE");
    var variantItems = rows.map(function (row) {
      var ram = row.ram_gb != null ? row.ram_gb + "GB RAM" : "RAM not specified";
      var storage = row.storage_gb != null ? row.storage_gb + "GB storage" : "storage not specified";
      if (row.canonical_product_id) return '<li><strong>Verified India variant</strong> · ' + escapeHtml(ram + " · " + storage) + ' · ' + escapeHtml(row.canonical_product_id) + '</li>';
      return '<li>Research variant · ' + escapeHtml(row.variant_text || (ram + " · " + storage)) + ' · ' + escapeHtml(inventoryVariantStatus(row)) + '</li>';
    }).join("");
    var fieldSet = {};
    discoveryRows.forEach(function (row) { (row.verified_fields || []).forEach(function (field) { fieldSet[String(field).replace(/_/g, " ")] = true; }); });
    var fields = Object.keys(fieldSet).join(", ") || "No exact fields verified in discovery record";
    var specSet = {};
    Object.keys(card.specifications || {}).forEach(function (key) {
      var item = card.specifications[key] || {};
      var label = String(specificationLabel(key, item)).replace(/_/g, " ");
      var value = specValue(key, item);
      if (value != null && value !== "") specSet[label + "|" + String(value)] = true;
    });
    frozenRows.forEach(function (row) {
      Object.keys(row.specifications || {}).forEach(function (key) {
        var item = row.specifications[key] || {};
        var label = String(specificationLabel(key, item)).replace(/_/g, " ");
        var value = specValue(key, item);
        if (value != null && value !== "") specSet[label + "|" + String(value)] = true;
      });
    });
    var frozenSpecs = Object.keys(specSet).map(function (entry) {
      var separator = entry.indexOf("|");
      return '<li><span>' + escapeHtml(entry.slice(0, separator)) + '</span><strong>' + escapeHtml(entry.slice(separator + 1)) + '</strong></li>';
    }).join("");
    var knownLabels = {};
    Object.keys(specSet).forEach(function (entry) {
      var separator = entry.indexOf("|");
      if (separator > 0) knownLabels[entry.slice(0, separator).toLowerCase()] = true;
    });
    var missingSpecs = [];
    (card.missing_specifications || []).forEach(function (key) {
      var label = TECHNICAL_FIELD_LABELS[key] || String(key).replace(/_/g, " ");
      if (!knownLabels[String(label).toLowerCase()] && missingSpecs.indexOf(label) < 0) missingSpecs.push(label);
    });
    var pending = missingSpecs.length ? '<p class="mobile-research-pending"><strong>Verification pending:</strong> ' + escapeHtml(missingSpecs.join(", ")) + '</p>' : '';
    var details = frozenSpecs ? '<p class="mobile-research-known"><strong>Source-backed specifications:</strong></p><ul class="mobile-research-model-specs">' + frozenSpecs + '</ul>' + pending : '<p>Source-backed technical specifications are not yet available for this model.</p>' + pending;
    var sourceUrls = [];
    discoveryRows.forEach(function (row) { (row.source_urls || []).forEach(function (url) { if (sourceUrls.indexOf(url) < 0) sourceUrls.push(url); }); });
    (card.source_urls || []).forEach(function (url) { if (sourceUrls.indexOf(url) < 0) sourceUrls.push(url); });
    frozenRows.forEach(function (row) { if (row.official_source && sourceUrls.indexOf(row.official_source) < 0) sourceUrls.push(row.official_source); });
    var sources = sourceUrls.slice(0, 3).map(function (url, index) { return link(url, index ? "Source" : "Official/source evidence"); }).join("");
    var counts = (discoveryRows.length ? discoveryRows.length + " research record" + (discoveryRows.length === 1 ? "" : "s") : "No discovery record") +
      (frozenRows.length ? " · " + frozenRows.length + " frozen exact variant" + (frozenRows.length === 1 ? "" : "s") : "");
    var launch = card.india_launch_date ? '<p class="mobile-research-launch"><strong>Verified India launch:</strong> ' + escapeHtml(card.india_launch_date) + '</p>' : '';
    return '<article class="mobile-research-inventory-card mobile-research-model-card" data-mobile-model-card="' + escapeHtml(card.model_key) + '">' +
      '<div class="mobile-research-inventory-body">' +
      '<div class="mobile-research-card-top"><span class="research-status inventory-status-' + escapeHtml(statusLabel.toLowerCase()) + '">' + escapeHtml(statusLabel) + '</span></div>' +
      researchPhoneImage(card) + '<h3>' + escapeHtml(displayPhoneName(card)) + '</h3>' + launch +
      '<p class="mobile-research-variant">' + escapeHtml(counts || "Model research reference") + '</p>' +
      '<ul class="mobile-research-variant-list">' + (variantItems || "<li>Variant details are not specified in the source universe.</li>") + '</ul>' +
      '<p class="mobile-research-inventory-fields"><strong>Verified fields:</strong> ' + escapeHtml(fields) + '</p>' +
      '<details class="mobile-research-model-details"><summary>View specifications / details</summary>' + details + '</details>' +
      '<p class="mobile-research-inventory-reason">Model card groups source-backed discovery records and frozen exact variants. It does not certify availability or purchase eligibility.</p>' +
      '<div class="mobile-research-sources">' + sources + '</div>' + retailerResearchLinks(card) +
      '<p class="mobile-research-gate">Research only · no price · no stock · no purchase action</p>' +
      '</div></article>';
  }

  function renderInventory() {
    if (!inventoryGrid) return;
    var filtered = inventoryCards.filter(inventoryMatches);
    var matchingVariants = filtered.reduce(function (count, card) { return count + inventoryRowsForCard(card).length; }, 0);
    var isUnfiltered = !(inventoryQuery && inventoryQuery.value) && !(inventoryBrand && inventoryBrand.value) && !(inventoryRam && inventoryRam.value) && !(inventoryStorage && inventoryStorage.value) && !(inventoryStatus && inventoryStatus.value);
    if (inventoryCount) {
      inventoryCount.textContent = isUnfiltered && inventorySourceCounts.visible_model_cards ?
        inventorySourceCounts.visible_model_cards + " catalogue entries · " + (inventorySourceCounts.deduplicated_discovery_records || inventoryRows.length) + " research records · " + (inventorySourceCounts.frozen_verified_variants || verifiedRows.length) + " frozen exact variants" :
        filtered.length + " catalogue entries · " + matchingVariants + " matching research/frozen variants";
    }
    var visible = inventoryExpanded ? filtered : filtered.slice(0, INVENTORY_PAGE_SIZE);
    inventoryGrid.innerHTML = visible.length ? visible.map(renderInventoryCard).join("") : "<p>No smartphone models match these filters.</p>";
    if (inventoryMore) {
      inventoryMore.hidden = filtered.length <= INVENTORY_PAGE_SIZE;
      inventoryMore.textContent = inventoryExpanded ? "Show fewer research models" : "Load more research models";
    }
  }

  function refreshInventoryControls() {
    var rows = inventoryAllVariantRows();
    fillSelect(inventoryBrand, Array.from(new Set(inventoryCards.map(function (card) { return card.brand; }))).sort(), "All brands");
    fillSelect(inventoryRam, optionValues(rows, "ram_gb"), "All RAM");
    fillSelect(inventoryStorage, optionValues(rows, "storage_gb"), "All storage");
    fillSelect(inventoryStatus, ["OFFICIAL_VERIFIED", "PARTIALLY_VERIFIED", "RESEARCH_ONLY", "NEEDS_VERIFICATION"], "All evidence statuses");
    renderInventory();
  }

  function loadInventoryCatalogue() {
    if (!inventoryGrid) return;
    // Version the generated data URL so a reviewed catalogue refresh cannot
    // be hidden by a stale GitHub Pages/browser cache.
    fetch("/data/mobile_research_catalogue.json?v=p1-20261107", { credentials: "same-origin" })
      .then(function (response) {
        if (!response.ok) throw new Error("research catalogue unavailable");
        return response.json();
      })
      .then(function (payload) {
        inventoryLoadFailed = false;
        inventoryRows = Array.isArray(payload.records) ? payload.records : [];
        inventoryByKey = new Map(inventoryRows.map(function (row) { return [row.record_key, row]; }));
        inventoryCards = Array.isArray(payload.model_cards) ? payload.model_cards : [];
        inventorySourceCounts = payload.source_counts || {};
        refreshInventoryControls();
        renderNewNoteworthy();
        handleResearchHash();
        var initialQuery = lastSearchQuery || new URLSearchParams(window.location.search || "").get("q");
        if (initialQuery) submitResearch(initialQuery);
      })
      .catch(function () {
        inventoryLoadFailed = true;
        if (researchSearchStatus) researchSearchStatus.textContent = "Saved smartphone research is temporarily unavailable. Use the Standard Buying Guide below.";
        if (researchResults) { researchResults.hidden = false; researchResults.innerHTML = researchGuideFallback(); }
        if (inventoryCount) inventoryCount.textContent = "Research catalogue unavailable";
        inventoryGrid.innerHTML = "<p>Existing research records are currently unavailable.</p>" + researchGuideFallback();
      });
  }

  function specValue(key, item) {
    var value = item && item.value;
    if (key === "display_inches") return value + " in";
    if (key === "display_refresh_max_hz") return value + " Hz";
    if (["rear_main_mp", "rear_ultrawide_mp", "front_mp"].indexOf(key) >= 0) return value + " MP";
    if (key === "battery_mah_typical") return value + " mAh";
    if (key === "wired_charging_max_w") return value + " W";
    if (key === "os_upgrade_generations") return value + " Android generations";
    if (key === "security_support_years") return value + " years";
    return value;
  }

  function metricNames(metrics) {
    return (metrics || []).map(function (metric) {
      return String(metric).replace(/_/g, " ");
    }).join(", ") || "No accepted measurement";
  }

  function catalogueStatus(row) {
    var identityVerified = row && (row.identity_verified === true || String(row.catalog_status || "").toLowerCase() === "verified");
    return identityVerified ? "Identity verified · no current offer" : "Historical / unverified reference";
  }

  function safeCatalogueRows(rows) {
    return (Array.isArray(rows) ? rows : []).filter(function (row) {
      var keys = Object.keys(row || {});
      return row && typeof row === "object" && row.id != null && String(row.title || "").trim() &&
        !keys.some(function (key) { return /private|secret|credential|output|report/i.test(String(key)); });
    }).map(function (row) {
      return {
        id: String(row.id),
        title: String(row.title || "").trim().slice(0, 180),
        brand: String(row.brand || "").trim().slice(0, 80),
        category: String(row.category || "Catalogue").trim().slice(0, 80),
        status: catalogueStatus(row)
      };
    });
  }

  function renderCatalogueRow(row) {
    return '<article class="catalogue-reference-card">' +
      '<div class="catalogue-reference-top"><span class="research-id">Catalogue #' + escapeHtml(row.id) + '</span><span class="catalogue-status">' + escapeHtml(row.status) + '</span></div>' +
      '<h3>' + escapeHtml(row.title) + '</h3>' +
      '<p><strong>' + escapeHtml(row.brand || "Brand not stated") + '</strong> · ' + escapeHtml(row.category) + '</p>' +
      '<p class="catalogue-reference-note">Reference listing only. Exact identity, price, stock and purchase eligibility are not asserted.</p>' +
      '</article>';
  }

  function renderCatalogueRows() {
    if (!catalogueGrid) return;
    var visible = catalogueExpanded ? catalogueRows : catalogueRows.slice(0, CATALOGUE_INITIAL_LIMIT);
    catalogueGrid.innerHTML = visible.length ? visible.map(renderCatalogueRow).join("") : "<p>Catalogue references are currently unavailable.</p>";
    if (catalogueMore) {
      catalogueMore.hidden = catalogueRows.length <= CATALOGUE_INITIAL_LIMIT;
      catalogueMore.textContent = catalogueExpanded ? "Show fewer catalogue references" : "Show all catalogue references";
    }
  }

  function renderProduct(product) {
    var specs = product.specifications || {};
    var specHtml = Object.keys(specs).map(function (key) {
      var item = specs[key] || {};
      return '<li><span>' + escapeHtml(specificationLabel(key, item)) + '</span><strong>' + escapeHtml(specValue(key, item)) + '</strong></li>';
    }).join("");
    var battery = product.battery_evidence || {};
    var camera = product.camera_evidence || {};
    var cameraScope = (camera.scope || []).join(", ").replace(/_/g, " ");
    return '<article class="mobile-research-card">' +
      '<div class="mobile-research-card-top"><span class="research-id">' + escapeHtml(product.canonical_product_id) + '</span><span class="research-status">' + escapeHtml(product.manufacturer_spec_status || "UNAVAILABLE") + '</span></div>' +
      '<h3>' + escapeHtml(product.brand + " " + product.model) + '</h3>' +
      '<p class="mobile-research-variant">India · ' + escapeHtml(product.ram_gb) + 'GB RAM · ' + escapeHtml(product.storage_gb) + 'GB storage</p>' +
      '<ul class="mobile-research-specs">' + specHtml + '</ul>' +
      '<p class="mobile-research-lane"><strong>Technical lane:</strong> ' + escapeHtml(product.technical_lane) + '</p>' +
      '<div class="mobile-research-evidence"><p><strong>Battery:</strong> ' + escapeHtml(battery.status || "Unavailable") + ' · ' + escapeHtml(metricNames(battery.metrics)) + ' <span class="research-scope">(' + escapeHtml(battery.applicability || "scope not stated") + ')</span></p>' +
      '<p><strong>Camera:</strong> ' + escapeHtml(camera.status || "Unavailable") + ' · ' + escapeHtml((camera.observation_types || []).join(", ").replace(/_/g, " ") || "No accepted observation") + ' <span class="research-scope">(' + escapeHtml(cameraScope || "scope not stated") + ')</span></p></div>' +
      '<div class="mobile-research-sources">' + link(product.official_source, "Official source") + (battery.source_urls && battery.source_urls[0] ? link(battery.source_urls[0], "Battery source") : "") + (camera.source_urls && camera.source_urls[0] ? link(camera.source_urls[0], "Camera source") : "") + '</div>' +
      '<p class="mobile-research-gate">No live offer · no price · no purchase action</p>' +
      '</article>';
  }

  function normalizeResearch(value) {
    return String(value == null ? "" : value).toLowerCase()
      .replace(/[’']/g, "")
      .replace(/[^a-z0-9\u0900-\u097f]+/g, " ")
      .replace(/\s+/g, " ").trim();
  }


  function researchConstraints(query) {
    var text = String(query || "").toLowerCase().replace(/[०-९]/g, function (d) { return String("०१२३४५६७८९".indexOf(d)); }).replace(/,/g, "");
    text = text.replace(/सैमसंग/g, "samsung").replace(/आईफोन/g, "iphone").replace(/रेडमी/g, "redmi").replace(/वनप्लस/g, "oneplus");
    var amount = "([0-9]+(?:\\.[0-9]+)?)\\s*(k|thousand|hazar|hazaar|हजार|हज़ार|lakh|lac|लाख)?";
    function value(n, unit) { return Number(n) * (/^(k|thousand|hazar|hazaar|हजार|हज़ार)$/.test(unit || "") ? 1000 : /^(lakh|lac|लाख)$/.test(unit || "") ? 100000 : 1); }
    var nearbyBudget = /\bnearby\s+(?:band|budget)\b/i.test(text);
    text = text.replace(/\bnearby\s+(?:band|budget)\b/gi, " ");
    var fullBudget = /\bfull\s+budget\b|पूरे\s*बजट/i.test(text);
    text = text.replace(/\bfull\s+budget\b|पूरे\s*बजट/gi, " ");
    var budget = null, lower = null, inclusive = false;
    var between = text.match(new RegExp("(?:between|from)\\s*(?:rs\\.?|inr|₹)?\\s*" + amount + "\\s*(?:and|to|-)\\s*(?:rs\\.?|inr|₹)?\\s*" + amount));
    if (between) { lower = value(between[1], between[2] || between[4]); budget = value(between[3], between[4]); inclusive = true; text = text.replace(between[0], " "); }
    else {
      var prefix = text.match(new RegExp("(?:under|below|within|upto|up to|budget(?: of)?)\\s*(?:rs\\.?|inr|₹)?\\s*" + amount));
      var suffix = text.match(new RegExp("(?:rs\\.?|inr|₹)?\\s*" + amount + "\\s*(?:rupees|रुपये|रुपए)?\\s*(?:ke\\s*)?(?:andar|se kam|के\\s*अंदर|के\\s*नीचे|से\\s*कम|तक)"));
      var currency = text.match(new RegExp("(?:₹|rs\\.?|inr)\\s*" + amount));
      var m = prefix || suffix || currency;
      if (m) { budget = value(m[1], m[2]); inclusive = /within|upto|up to|तक/.test(m[0]); text = text.replace(m[0], " "); }
    }
    // Under-budget searches include every documented cheaper candidate.
    // Only an explicit nearby-band choice or range adds a lower bound.
    if (budget != null && lower == null) {
      lower = nearbyBudget && !fullBudget ? Math.max(0, budget - (budget <= 30000 ? 5000 : 10000)) : 0;
    }
    var ram = null, storage = null;
    text = text.replace(/\b(\d{1,2})\s*\/\s*(\d{2,4})\b/g, function (_, r, t) { ram = Number(r); storage = Number(t); return " "; });
    text = text.replace(/\b(\d+(?:\.\d+)?)\s*(gb|tb)\s*(?:(?:physical|internal)\s+)?(ram|storage|rom)?\b/g, function (_, n, unit, type) {
      var size = Number(n) * (unit === "tb" ? 1024 : 1);
      if (type === "ram" || (!type && size <= 24)) ram = size; else storage = size;
      return " ";
    });
    var minimumBattery = null, minimumRefresh = null;
    text = text.replace(/\b(\d{3,5})\s*mah\b/g, function (_, n) { minimumBattery = Number(n); return " battery "; });
    text = text.replace(/\b(\d{2,3})\s*hz\b/g, function (_, n) { minimumRefresh = Number(n); return " display "; });
    var need5g = /\b5g\b/.test(text); text = text.replace(/\b5g\b/g, " ");
    var needOis = /\bois\b/.test(text); text = text.replace(/\bois\b/g, " camera ");
    return { text: normalizeResearch(text), budget: budget, lower: lower, inclusive: inclusive, ram: ram, storage: storage, minimumBattery: minimumBattery, minimumRefresh: minimumRefresh, need5g: need5g, needOis: needOis };
  }


  function researchRowsFor(card, c) {
    var rows;
    if (c.budget != null) {
      var ref = card.research_budget_reference;
      if (!ref || ref.live_offer !== false || !(ref.reference_price_inr > 0)) return [];
      if (c.inclusive ? ref.reference_price_inr > c.budget : ref.reference_price_inr >= c.budget) return [];
      if (c.lower != null && ref.reference_price_inr < c.lower) return [];
      rows = [{ ram_gb: ref.ram_gb, storage_gb: ref.storage_gb, variant_text: (ref.ram_gb == null ? "RAM not officially specified" : ref.ram_gb + "GB RAM") + " / " + ref.storage_gb + "GB storage", research_reference: true }];
    } else {
      rows = inventoryRowsForCard(card);
    }
    return rows.filter(function (row) { return (c.ram == null || Number(row.ram_gb) === c.ram) && (c.storage == null || Number(row.storage_gb) === c.storage); });
  }

  function excludedBrand(query) {
    var beforeMarker = String(query || "").match(/\b([a-z][a-z0-9/&-]*)\s+(?:ko\s+)?(?:chhodkar|chhod|छोड़कर|छोड़|हटाकर|के\s+बिना|बिना)\b/i);
    if (beforeMarker) return normalizeResearch(beforeMarker[1]);
    var match = String(query || "").match(/(?:exclude|excluding|without|except|no|chhodkar|chhod|छोड़कर|छोड़|हटाकर|के बिना)\s+([a-z][a-z0-9/& -]{1,30})/i);
    if (!match) return "";
    return normalizeResearch(match[1]).split(" ")[0];
  }

  function researchFeatureKeys(query) {
    var text = normalizeResearch(query);
    var keys = [];
    var groups = [
      [/camera|कैमरा/, ["rear_main_mp", "rear_camera_system", "front_camera_system", "ois"]],
      [/battery|बैटरी/, ["battery_mah_typical", "battery_capacity_description", "battery_and_charging", "wired_charging_max_w"]],
      [/gaming|game|गेमिंग/, ["gpu", "chipset"]],
      [/software|android|update|support|सॉफ्टवेयर/, ["operating_system", "launch_android", "os_upgrade_generations", "security_update_policy", "security_support_years"]],
      [/display|screen|डिस्प्ले/, ["display_type", "display_inches", "display_resolution", "display_refresh_max_hz"]],
      [/build|reliability|durability/, ["ip_rating", "durability"]]
    ];
    groups.forEach(function (group) { if (group[0].test(text)) keys = keys.concat(group[1]); });
    return Array.from(new Set(keys));
  }

  function researchSpecKeys(card, rows) {
    var keys = Object.keys(card.specifications || {});
    (rows || []).forEach(function (row) { keys = keys.concat(Object.keys(row.specifications || {})); });
    return keys;
  }


  function findResearchMatches(query) {
    var c = researchConstraints(query), text = c.text;
    var excluded = excludedBrand(text), featureKeys = researchFeatureKeys(text);
    var stop = /^(best|good|phone|phones|mobile|mobiles|smartphone|smartphones|under|below|within|price|in|the|and|with|ram|storage|camera|battery|gaming|game|software|support|display|screen|build|reliability|durability|android|update|updates|ko|ke|ka|ki|bina|chhodkar|chhod|mujhe|mujhko|chahiye|batao|dikhao|achha|acha|accha|wala|wali|mein|me|se|kam|tak|rs|inr|rupees|minimum|least|at|above|over|more|than|का|की|के|में|मुझे|चाहिए|बताओ|दिखाओ|अच्छा|अच्छे|वाला|वाले|फोन|मोबाइल|कैमरा|बैटरी|गेमिंग|डिस्प्ले|छोड़कर|छोड़|हटाकर|बिना|exclude|excluding|without|except|no)$/;
    var tokens = text.split(" ").filter(function (token) { return token && !stop.test(token) && token !== excluded; });
    var aliases = { "सैमसंग": "samsung", "आईफोन": "iphone", "रेडमी": "redmi", "पोको": "poco", "वनप्लस": "oneplus" };
    tokens = tokens.map(function (token) { return aliases[token] || token; });
    if (!tokens.length && !featureKeys.length && !excluded && c.budget == null && c.ram == null && c.storage == null && !c.need5g) return [];
    var matches = [];
    // A full model name with a memory constraint must not select a sibling.
    var exactCard = (c.ram != null || c.storage != null) && inventoryCards.find(function (card) {
      return normalizeResearch(displayPhoneName(card).replace(/\b5g\b/ig, "")) === text;
    });
    (exactCard ? [exactCard] : inventoryCards).forEach(function (card) {
      if (excluded && normalizeResearch(card.brand).indexOf(excluded) >= 0) return;
      var rows = researchRowsFor(card, c);
      if (!rows.length) return;
      var specs = card.specifications || {};
      function spec(key) { return specs[key] && specs[key].value; }
      if (c.minimumBattery != null && !(Number(spec("battery_mah_typical")) >= c.minimumBattery)) return;
      if (c.minimumRefresh != null && !(Number(spec("display_refresh_max_hz")) >= c.minimumRefresh)) return;
      if (c.needOis && !/^(yes|true|supported)$/i.test(String(spec("ois") || ""))) return;
      if (c.need5g && !/5g/i.test(String(spec("network_support") || "") + " " + card.model)) return;
      if (tokens.length) {
        var hayTokens = normalizeResearch(card.brand + " " + card.model).split(" ");
        if (!tokens.every(function (token) { return hayTokens.indexOf(token) >= 0; })) return;
      }
      if (featureKeys.length) {
        var keys = researchSpecKeys(card, rows);
        if (!featureKeys.some(function (key) { return keys.indexOf(key) >= 0; })) return;
      }
      matches.push({card: card, rows: rows});
    });
    return sortResearchMatches(matches, query);
  }



  function displayPhoneName(card) {
    var brand = String(card.brand || "");
    if (brand.toLowerCase() === "samsung") brand = "Samsung";
    if (normalizeResearch(brand) === "xiaomi redmi") brand = "Redmi";
    var model = String(card.model || "");
    if (normalizeResearch(model).indexOf(normalizeResearch(brand) + " ") === 0) return model;
    return brand + " " + model;
  }

  function researchGroupKey(card) {
    // Display grouping only. No source row, price or variant is transferred.
    var name = normalizeResearch(displayPhoneName(card))
      .replace(/\s+(?:mobile\s+)?(?:moonlight|sapphire|frost|thunder|light|bahama|violet|velvet)(?:\s+(?:silver|black|blue))?$/, "")
      .replace(/\s+smartphone$/, "")
      .replace(/\s+\d+\s*gb(?:\s+ram)?/g, "").trim();
    // These spelling aliases share the manufacturer's exact specification URL.
    var aliases = {"vivo t5x": "vivo t5x 5g", "oppo k13 turbo": "oppo k13 turbo 5g"};
    return aliases[name] || name;
  }

  function groupResearchMatches(matches) {
    var seen = {}, result = [];
    matches.forEach(function (item) {
      var key = researchGroupKey(item.card);
      if (seen[key]) { seen[key].group_size += 1; return; }
      var copy = {card: item.card, rows: item.rows, group_size: 1};
      seen[key] = copy; result.push(copy);
    });
    return result;
  }

  function specificationLabel(key, item) {
    var value = String(item && item.value || "");
    if (key === "chipset" && /ghz/i.test(value) && !/snapdragon|exynos|dimensity|bionic|tensor|mediatek|unisoc/i.test(value)) return "CPU clock (chipset name unconfirmed)";
    if (/display_type/.test(key) && /colou?r depth|16m/i.test(value)) return "Display colour depth";
    return item.label || TECHNICAL_FIELD_LABELS[key] || key.replace(/_/g, " ");
  }

  function compactSpecRows(card, query) {
    var specs = card.specifications || {};
    var groups = [
      ["chipset"], ["display_type", "display_type_description"], ["display_refresh_max_hz", "display_refresh_description"],
      ["rear_main_mp", "rear_camera_system"], ["ois"], ["battery_mah_typical", "battery_capacity_description", "battery_and_charging"],
      ["wired_charging_max_w", "charging_description"], ["security_support_years", "security_update_policy", "operating_system"],
      ["display_resolution", "display_resolution_description"], ["gpu"], ["ip_rating", "durability"]
    ];
    var priorities = researchFeatureKeys(query), keys = [];
    groups.forEach(function (group) { var key = group.find(function (k) { return specs[k] && specs[k].value !== "" && specs[k].value != null; }); if (key) keys.push(key); });
    keys.sort(function (a, b) { return (priorities.indexOf(a) < 0 ? 100 : priorities.indexOf(a)) - (priorities.indexOf(b) < 0 ? 100 : priorities.indexOf(b)); });
    return keys.slice(0, 6).map(function (key) { return {key:key, label:specificationLabel(key, specs[key]), value:specValue(key, specs[key])}; });
  }

  function documentedContext(card, query) {
    var specs = card.specifications || {};
    var text = normalizeResearch(query), fact = "Compare these documented specifications with your everyday needs.";
    var caution = "Current price, exact listing and delivery need retailer confirmation.";
    if (/camera|कैमरा/.test(text)) {
      var ois = specs.ois && String(specs.ois.value);
      fact = /^(yes|true|supported)$/i.test(ois || "") ? "Optical image stabilization (OIS) is listed in the source." : "Optical image stabilization is not confirmed in this record.";
      caution = "Megapixels alone do not establish photo quality. Check camera samples and independent tests.";
    } else if (/battery|बैटरी/.test(text)) {
      var battery = specs.battery_mah_typical;
      fact = battery ? "Listed battery capacity: " + specValue("battery_mah_typical", battery) + "." : "Battery capacity needs confirmation from the source.";
      caution = "Capacity is not measured battery life. Usage, signal and charging tests also matter.";
    } else if (/gaming|game|गेमिंग/.test(text)) {
      fact = "Processor and GPU specifications are shown where documented.";
      caution = "Chipset names alone do not establish sustained FPS, heating or gaming endurance.";
    } else if (/build|reliability|durability/.test(text)) {
      fact = specs.ip_rating ? "Documented ingress-protection rating: " + specs.ip_rating.value + "." : "An ingress-protection rating is not confirmed in this record.";
      caution = "An IP rating does not establish drop resistance or long-term reliability. Check warranty conditions and repair support.";
    } else if (/software|support|update|android/.test(text)) {
      fact = "Check the documented operating system and update policy below.";
      caution = "An update promise is not the remaining support period. Confirm launch and support-end dates.";
    }
    return '<div class="research-context"><p><strong>What to consider</strong> ' + escapeHtml(fact) + '</p><p><strong>Before choosing</strong> ' + escapeHtml(caution) + '</p></div>';
  }

  function retailerResearchLinks(card) {
    return '<div class="mobile-research-sources retailer-search-links">' + (card.retailer_search_links || []).map(function (item) { return link(item.url, "Search " + item.retailer + " for this model"); }).join(" ") + '</div>';
  }

  function independentTestContext(card) {
    var tests = card.independent_tests || [];
    if (!tests.length) return "";
    return '<details class="research-independent-tests"><summary>Independent lab tests (' + tests.length + ')</summary><p>' + escapeHtml(card.independent_test_limitation) + '</p>' + tests.map(function (test) {
      return '<div class="research-lab-measurement"><p><strong>' + escapeHtml(test.label) + ': ' + escapeHtml(test.value) + ' ' + escapeHtml(test.unit) + '</strong></p><p>Tested: ' + escapeHtml(test.tested_unit) + '</p><p>' + escapeHtml(test.protocol) + ' · Version: ' + escapeHtml(test.test_version || 'not reported') + ' · ' + escapeHtml(test.conditions) + '</p><p>' + link(test.source_url, test.source_name + ' test source') + ' · Source checked: ' + escapeHtml(test.checked_at) + ' · Measurement date: ' + escapeHtml(test.observed_at || 'not separately reported') + '</p></div>';
    }).join('') + '<p>Source-specific measurements; excluded from Best 3 scoring. Missing tests on other phones do not mean worse performance.</p></details>';
  }

  function renderResearchResultCard(card, rows, groupSize) {
    var variants = Array.from(new Set(rows.map(function (row) { return (row.ram_gb != null ? row.ram_gb + "GB RAM" : "RAM not specified") + " · " + (row.storage_gb != null ? row.storage_gb + "GB storage" : "storage not specified"); })));
    var facts = compactSpecRows(card, lastSearchQuery);
    var specs = facts.map(function (item) { var value = String(item.value); return '<li><span>' + escapeHtml(item.label) + '</span><strong title="' + escapeHtml(value) + '">' + escapeHtml(value.length > 160 ? value.slice(0, 157) + "…" : value) + '</strong></li>'; }).join("");
    var sourceItem = Object.values(card.specifications || {}).find(function (item) { return /^https:\/\//.test(item.source_url || ""); });
    var status = card.status === "OFFICIAL_VERIFIED" ? "Manufacturer evidence" : card.status === "PARTIALLY_VERIFIED" ? "Partial specifications" : "Needs verification";
    var selected = comparisonSelection.some(function (item) { return researchGroupKey(item.card) === researchGroupKey(card); });
    var launch = card.india_launch_date ? '<p class="mobile-research-launch">India launch: ' + escapeHtml(card.india_launch_date) + '</p>' : '';
    return '<article class="mobile-research-inventory-card mobile-research-result-card" data-mobile-model-card="' + escapeHtml(card.model_key) + '"><div class="mobile-research-inventory-body">' +
      '<div class="mobile-research-card-top"><span class="research-status">' + escapeHtml(status) + '</span><span class="research-status">Research only</span></div>' +
      researchPhoneImage(card) + '<h3>' + escapeHtml(displayPhoneName(card)) + '</h3>' + launch + '<p class="mobile-research-variant">Matching documented variant' + (variants.length > 1 ? "s" : "") + ': ' + escapeHtml(variants.join("; ")) + '</p>' +
      (groupSize > 1 ? '<p class="research-group-note">' + groupSize + ' matching catalogue entries grouped. Specifications below belong to the displayed record.</p>' : '') +
      (specs ? '<ul class="mobile-research-model-specs">' + specs + '</ul>' : '<p>Technical specifications are pending verification.</p>') + documentedContext(card, lastSearchQuery) + independentTestContext(card) +
      '<p class="research-source-note">' + (sourceItem ? link(sourceItem.source_url, "Specification source") : 'Specification source pending') + ' · Specification research snapshot: ' + escapeHtml(card.research_checked_at || sourceItem && (sourceItem.checked_at || sourceItem.checked_date) || 'date unavailable') + ' (not a live check)</p>' + (card.research_budget_reference ? '<p class="research-source-note">Budget filter uses a dated retailer observation: ' + escapeHtml(String(card.research_budget_reference.checked_at || 'date unavailable').match(/\d{4}-\d{2}-\d{2}/)?.[0] || String(card.research_budget_reference.checked_at || 'date unavailable')) + '. Current price and stock not verified.</p>' : '') +
      '<div class="research-card-actions"><button type="button" class="btn btn-ghost mobile-research-detail-button" data-research-detail="' + escapeHtml(card.model_key) + '">All specifications</button>' +
      '<button type="button" class="btn btn-ghost" data-research-compare="' + escapeHtml(card.model_key) + '" aria-pressed="' + selected + '">' + (selected ? 'Remove comparison' : 'Compare') + '</button></div>' + retailerResearchLinks(card) +
      '<p class="mobile-research-gate">Model-targeted retailer searches only, not exact-SKU purchase links. Confirm RAM/storage, current price, stock and delivery on retailer sites.</p></div></article>';
  }

  function renderSelectedComparison() {
    if (!comparePanel) return;
    comparePanel.hidden = comparisonSelection.length === 0;
    if (!comparisonSelection.length) { comparePanel.innerHTML = ""; return; }
    var fields = [ ["Processor", ["chipset"]], ["Display", ["display_type", "display_type_description"]], ["Refresh rate", ["display_refresh_max_hz", "display_refresh_description"]], ["Main camera", ["rear_main_mp", "rear_camera_system"]], ["Optical stabilization", ["ois"]], ["Battery", ["battery_mah_typical", "battery_capacity_description", "battery_and_charging"]], ["Charging", ["wired_charging_max_w", "charging_description"]], ["Software / updates", ["security_support_years", "security_update_policy", "operating_system"]] ];
    function value(card, keys) { var key = keys.find(function (key) { return card.specifications && card.specifications[key]; }); if (!key) return "Not confirmed"; var item = card.specifications[key]; return (key === "chipset" && /ghz/i.test(String(item.value)) ? specificationLabel(key, item) + ": " : "") + specValue(key, item); }
    comparePanel.innerHTML = '<div class="research-comparison-heading"><h3>Compare your shortlist (' + comparisonSelection.length + '/3)</h3><button type="button" class="btn btn-ghost" data-research-compare-clear>Clear comparison</button></div><p>Model specifications side by side; no performance winner is asserted. Unknown fields remain explicit.</p><div class="research-table-scroll" role="region" aria-label="Phone specification comparison" tabindex="0"><table class="research-spec-table"><caption>Documented specifications for the selected records</caption><thead><tr><th scope="col">Specification</th>' + comparisonSelection.map(function (item) { return '<th scope="col">' + escapeHtml(displayPhoneName(item.card)) + '<br><small>' + escapeHtml(item.rows.filter(function (row) { return row.ram_gb != null || row.storage_gb != null; }).map(function (row) { return (row.ram_gb != null ? row.ram_gb + 'GB' : 'RAM not stated') + ' / ' + (row.storage_gb != null ? row.storage_gb + 'GB' : 'storage not stated'); }).join('; ') || 'Memory not confirmed') + '</small></th>'; }).join('') + '</tr></thead><tbody>' + fields.map(function (field) { return '<tr><th scope="row">' + field[0] + '</th>' + comparisonSelection.map(function (item) { return '<td>' + escapeHtml(value(item.card, field[1])) + '</td>'; }).join('') + '</tr>'; }).join('') + '</tbody></table></div><p>Use All specifications for each phone\'s original source and remaining gaps.</p>';
  }

  function sortResearchMatches(matches, query) {
    var text = normalizeResearch(query);
    var priorityKeys = researchFeatureKeys(query);
    function relevantEvidenceCount(card) {
      return priorityKeys.filter(function (key) { return Object.prototype.hasOwnProperty.call(card.specifications || {}, key); }).length;
    }
    return matches.slice().sort(function (a, b) {
      var aExact = normalizeResearch(a.card.brand + " " + a.card.model) === text ? 1 : 0;
      var bExact = normalizeResearch(b.card.brand + " " + b.card.model) === text ? 1 : 0;
      if (aExact !== bExact) return bExact - aExact;
      // Prioritize documented evidence for the requested topic; never infer a performance winner.
      var aRelevant = relevantEvidenceCount(a.card), bRelevant = relevantEvidenceCount(b.card);
      if (aRelevant !== bRelevant) return bRelevant - aRelevant;
      var aEvidence = Object.keys(a.card.specifications || {}).length;
      var bEvidence = Object.keys(b.card.specifications || {}).length;
      return bEvidence - aEvidence || String(a.card.model).localeCompare(String(b.card.model));
    });
  }



  function showAppliedConditions(query) {
    var c = researchConstraints(query), labels = [];
    if (query) {
      [["Camera", /camera|कैमरा/], ["Battery", /battery|बैटरी/], ["Gaming", /gaming|game|गेमिंग/], ["Display", /display|screen|डिस्प्ले/], ["Software support", /software|support|update|android/], ["Build / reliability", /build|reliability|durability/]].forEach(function (item) { if (item[1].test(c.text)) labels.push("Priority: " + item[0]); });
      if (c.budget != null) labels.push("Reference range: ₹" + Number(c.lower).toLocaleString("en-IN") + " to " + (c.inclusive ? "₹" : "below ₹") + Number(c.budget).toLocaleString("en-IN"));
      if (c.ram != null) labels.push("Exact physical RAM: " + c.ram + "GB");
      if (c.storage != null) labels.push("Exact storage: " + c.storage + "GB");
      var excluded = excludedBrand(c.text); if (excluded) labels.push("Exclude: " + excluded);
      if (c.need5g) labels.push("5G required");
      if (c.needOis) labels.push("OIS required");
      if (c.minimumBattery != null) labels.push("Battery capacity ≥ " + c.minimumBattery + "mAh");
      if (c.minimumRefresh != null) labels.push("Refresh rate ≥ " + c.minimumRefresh + "Hz");
    }
    if (appliedFilters) { appliedFilters.hidden = labels.length === 0; appliedFilters.innerHTML = labels.map(function (label) { return '<span class="research-condition">' + escapeHtml(label) + '</span>'; }).join(''); }
    if (clearSearchButton) clearSearchButton.hidden = !query;
  }

  function researchGuideFallback() {
    return '<p class="standard-guide-fallback"><a class="btn btn-ghost" href="/guides/smartphone-buying-guide/">Standard Buying Guide</a></p>';
  }

  function emptyResearchResult(query) {
    var c = researchConstraints(query);
    var message = "No documented match in our saved research for this request.";
    if (c.lower != null && c.budget != null && c.lower > c.budget) message = "The lower budget is higher than the upper budget. Please correct the range.";
    else if (c.ram != null || c.storage != null) message += " We cannot confirm the requested exact memory variant with all these conditions.";
    else if (c.budget != null) message += " No matching record passes this price band and the other conditions. Missing references and recorded out-of-stock entries are excluded.";
    return '<div class="mobile-research-empty"><p>' + escapeHtml(message) + '</p><p>This is a research coverage gap, not proof that no suitable phone exists. No constraint has been relaxed.</p><a href="#mobileResearchCatalogue">Browse the full research catalogue</a>' + researchGuideFallback() + '</div>';
  }

  function verifiedRecommendationBridge(query, isComparison) {
    var c = researchConstraints(query);
    if (isComparison || c.budget == null) return "";
    return '<div class="research-context research-verified-recommendations">' +
      '<p><strong>Need a performance-based recommendation?</strong> This list is ordered by research coverage, not proven camera, gaming or battery performance. Check the existing recommendation engine separately; it will show results only when its evidence and eligibility rules pass.</p>' +
      '<button type="button" class="btn btn-ghost" data-research-verified-recommend>Check eligible recommendations</button></div>';
  }

  function searchResearch(query) {
    var nextQuery = String(query || "").trim();
    var queryChanged = nextQuery !== lastSearchQuery;
    if (queryChanged) {
      searchExpanded = false;
      if (typeof window.CouponWorldCancelShoppingRecommendation === "function") {
        window.CouponWorldCancelShoppingRecommendation();
      }
    }
    lastSearchQuery = nextQuery;
    showAppliedConditions(lastSearchQuery);
    if (researchQuery && researchQuery.value !== nextQuery) researchQuery.value = nextQuery;
    if (!lastSearchQuery) {
      if (researchResults) { researchResults.hidden = true; researchResults.innerHTML = ""; }
      if (researchResultsMore) researchResultsMore.hidden = true;
      if (researchSearchStatus) researchSearchStatus.textContent = "";
      return [];
    }
    revealSearch();
    if (!inventoryCards.length) { if (researchSearchStatus) researchSearchStatus.textContent = inventoryLoadFailed ? "Saved smartphone research is temporarily unavailable." : "Loading smartphone research…"; if (researchResults) { researchResults.hidden = false; researchResults.innerHTML = researchGuideFallback(); } return []; }
    var parts = lastSearchQuery.replace(/^compare\s+/i, "").split(/\s+(?:vs\.?|versus|और|compare)\s+/i);
    if (/^compare\s/i.test(lastSearchQuery) && parts.length === 1) parts = parts[0].split(/\s+and\s+/i);
    var comparison = parts.length > 1;
    var missingComparison = false;
    var matches;
    if (comparison) {
      matches = [];
      parts.slice(0, 4).forEach(function (part) {
        var group = findResearchMatches(part);
        if (!group.length) missingComparison = true;
        group.slice(0, 1).forEach(function (item) { if (!matches.some(function (existing) { return existing.card.model_key === item.card.model_key; })) matches.push(item); });
      });
    } else {
      matches = findResearchMatches(lastSearchQuery);
    }
    var c = researchConstraints(lastSearchQuery);
    matches = groupResearchMatches(matches);
    lastSearchMatches = matches;
    var visible = searchExpanded ? matches : matches.slice(0, MAX_SEARCH_RESULTS);
    if (comparison && queryChanged) { comparisonSelection = matches.slice(0, 3); renderSelectedComparison(); }
    if (researchResults) {
      researchResults.hidden = false;
      researchResults.innerHTML = verifiedRecommendationBridge(lastSearchQuery, comparison) + (comparison ? '<p class="mobile-research-gate">Specification comparison; no performance winner is asserted.' + (missingComparison ? ' At least one requested model or memory variant could not be matched.' : '') + '</p>' : '') + (visible.length ? visible.map(function (item) { return renderResearchResultCard(item.card, item.rows, item.group_size); }).join("") : emptyResearchResult(lastSearchQuery));
    }
    if (researchSearchStatus) researchSearchStatus.textContent = matches.length + " matching research model" + (matches.length === 1 ? "" : "s") + " · showing " + visible.length + (c.budget != null ? " · requested range ₹" + Number(c.lower).toLocaleString("en-IN") + " to " + (c.inclusive ? "₹" : "below ₹") + Number(c.budget).toLocaleString("en-IN") + " · dated references; current price and delivery unverified" : "") + (/best|अच्छा|अच्छे/i.test(lastSearchQuery) ? " · evidence coverage order, not a performance ranking" : "");
    if (researchResultsMore) { researchResultsMore.hidden = matches.length <= MAX_SEARCH_RESULTS; researchResultsMore.textContent = searchExpanded ? "Show fewer results" : "Load more research results"; }
    return matches;
  }

  function submitResearch(query) {
    searchResearch(query);
    if (inventoryCards.length && researchConstraints(query).budget != null &&
        !/\b(?:compare|vs\.?|versus)\b|और/i.test(String(query || "")) &&
        typeof window.CouponWorldShoppingRecommend === "function") {
      window.CouponWorldShoppingRecommend(query, {background: true});
    }
  }

  function revealSearch() {
    if (searchSection) searchSection.hidden = false;
  }

  function revealPreview() {
    section.hidden = false;
    section.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function revealCatalogue() {
    if (catalogueSection) catalogueSection.hidden = false;
    if (catalogueSection) catalogueSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function showDetail(modelKey) {
    var card = inventoryCards.find(function (item) { return item.model_key === modelKey; });
    if (!card || !detailSection || !detailContent) return;
    detailSection.hidden = false;
    if (detailTitle) detailTitle.textContent = displayPhoneName(card);
    detailContent.innerHTML = renderInventoryCard(card) + '<p class="mobile-research-gate">Research detail only · no current offer, price or purchase action.</p>';
    detailSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function handleResearchHash() {
    var hash = String(window.location.hash || "");
    if (hash === "#mobileResearchPreview") revealPreview();
    if (hash === "#mobileResearchCatalogue") revealCatalogue();
    if (hash.indexOf("#mobileResearchDetail/") === 0) showDetail(decodeURIComponent(hash.slice("#mobileResearchDetail/".length)));
  }

  function renderNewNoteworthy() {
    if (!researchNewSection || !researchNewGrid) return;
    var now = Date.now();
    var recent = inventoryCards.filter(function (card) {
      var date = card.india_launch_date || card.launch_date_india || card.launch_date;
      var time = Date.parse(String(date || ""));
      return card.status === "OFFICIAL_VERIFIED" && Number.isFinite(time) && now - time >= 0 && now - time <= 365 * 24 * 60 * 60 * 1000 && (card.source_urls || []).length;
    }).sort(function (a, b) { return Date.parse(b.india_launch_date || b.launch_date_india || b.launch_date) - Date.parse(a.india_launch_date || a.launch_date_india || a.launch_date); }).slice(0, 6);
    researchNewSection.hidden = recent.length === 0;
    researchNewGrid.innerHTML = recent.map(function (card) { return renderResearchResultCard(card, inventoryRowsForCard(card)); }).join("");
  }

  fetch("/data/mobile_research_preview.json", { credentials: "omit" })
    .then(function (response) {
      if (!response.ok) throw new Error("research preview unavailable");
      return response.json();
    })
    .then(function (payload) {
      var products = Array.isArray(payload.products) ? payload.products : [];
      verifiedRows = products;
      verifiedById = new Map(products.map(function (row) { return [row.canonical_product_id, row]; }));
      grid.innerHTML = products.length ? products.map(renderProduct).join("") : "<p>Verified mobile research is currently unavailable.</p>";
      refreshInventoryControls();
      renderNewNoteworthy();
      handleResearchHash();
    })
    .catch(function () {
      grid.innerHTML = "<p>Verified mobile research is currently unavailable.</p>";
    });

  if (catalogueGrid) {
    fetch("/coupons.json", { credentials: "omit" })
      .then(function (response) {
        if (!response.ok) throw new Error("catalogue unavailable");
        return response.json();
      })
      .then(function (rows) {
        catalogueRows = safeCatalogueRows(rows);
        if (catalogueCount) catalogueCount.textContent = catalogueRows.length + " catalogue references";
        renderCatalogueRows();
      })
      .catch(function () {
        if (catalogueCount) catalogueCount.textContent = "No catalogue references available";
        catalogueGrid.innerHTML = "<p>Catalogue references are currently unavailable.</p>";
      });
    if (catalogueMore) {
      catalogueMore.addEventListener("click", function () {
        catalogueExpanded = !catalogueExpanded;
        renderCatalogueRows();
      });
    }
  }

  [inventoryQuery, inventoryBrand, inventoryRam, inventoryStorage, inventoryStatus].forEach(function (control) {
    if (control) control.addEventListener("input", function () { inventoryExpanded = false; renderInventory(); });
    if (control && control.tagName === "SELECT") control.addEventListener("change", function () { inventoryExpanded = false; renderInventory(); });
  });
  if (inventoryMore) inventoryMore.addEventListener("click", function () { inventoryExpanded = !inventoryExpanded; renderInventory(); });

  if (guidedApply) guidedApply.addEventListener("click", function () {
    var values = guidedControls.map(function (control) { return String(control && control.value || ""); });
    if (!values.some(Boolean)) { if (guidedStatus) guidedStatus.textContent = "Choose a budget, priority, exact memory or brand exclusion to start."; return; }
    var query = (values[1] ? values[1] + " " : "") + "phone";
    if (values[0]) query += " under " + values[0] + (guidedScope && guidedScope.value === "band" ? " nearby band" : " full budget");
    if (values[2]) query += " " + values[2] + "GB physical RAM";
    if (values[3]) query += " " + values[3] + "GB storage";
    if (values[4]) query += " exclude " + values[4];
    if (guidedStatus) guidedStatus.textContent = "Search built from your selected conditions.";
    var hero = document.getElementById("heroSearch"); if (hero) hero.value = query;
    submitResearch(query);
  });
  if (clearSearchButton) clearSearchButton.addEventListener("click", function () {
    guidedControls.forEach(function (control) { if (control) control.value = ""; });
    if (guidedScope) guidedScope.value = "all";
    if (guidedStatus) guidedStatus.textContent = "";
    var hero = document.getElementById("heroSearch"); if (hero) hero.value = "";
    searchResearch("");
  });
  if (researchSearchButton) researchSearchButton.addEventListener("click", function () { submitResearch(researchQuery && researchQuery.value); });
  if (researchQuery) researchQuery.addEventListener("keydown", function (event) { if (event.key === "Enter") submitResearch(researchQuery.value); });
  document.querySelectorAll("[data-mobile-research-query]").forEach(function (button) {
    button.addEventListener("click", function () { var requested = button.getAttribute("data-mobile-research-query") || "";
      var current = researchQuery && researchQuery.value || "";
      if (current && researchConstraints(current).budget != null && researchConstraints(requested).budget == null) {
        var constraintsOnly = current.replace(/camera|battery|gaming|game|software|support|display|screen|कैमरा|बैटरी|गेमिंग/gi, " ");
        requested = requested + " " + constraintsOnly;
      }
      if (researchQuery) researchQuery.value = requested;
      submitResearch(requested); });
  });
  if (researchResultsMore) researchResultsMore.addEventListener("click", function () { searchExpanded = !searchExpanded; searchResearch(lastSearchQuery); });
  document.addEventListener("click", function (event) {
    if (event.target.closest("[data-research-verified-recommend]")) {
      if (typeof window.CouponWorldShoppingRecommend === "function" && lastSearchQuery) {
        window.CouponWorldShoppingRecommend(lastSearchQuery);
      } else if (researchSearchStatus) {
        researchSearchStatus.textContent = "Recommendation service is unavailable. Research results remain accessible.";
      }
      return;
    }
    var compareButton = event.target.closest("[data-research-compare]");
    if (compareButton) {
      var candidate = lastSearchMatches.find(function (item) { return item.card.model_key === compareButton.getAttribute("data-research-compare"); });
      if (!candidate) {
        var sourceCard = inventoryCards.find(function (card) { return card.model_key === compareButton.getAttribute("data-research-compare"); });
        if (sourceCard) candidate = {card: sourceCard, rows: inventoryRowsForCard(sourceCard)};
      }
      if (candidate) {
        var existing = comparisonSelection.findIndex(function (item) { return researchGroupKey(item.card) === researchGroupKey(candidate.card); });
        if (existing >= 0) comparisonSelection.splice(existing, 1);
        else if (comparisonSelection.length < 3) comparisonSelection.push(candidate);
        else { if (researchSearchStatus) researchSearchStatus.textContent = "Compare up to 3 phones. Remove one before adding another."; return; }
        renderSelectedComparison(); searchResearch(lastSearchQuery);
        if (comparisonSelection.length >= 2 && comparePanel) comparePanel.scrollIntoView({behavior: "smooth", block: "start"});
      }
    }
    if (event.target.closest("[data-research-compare-clear]")) { comparisonSelection = []; renderSelectedComparison(); searchResearch(lastSearchQuery); }
    var detail = event.target.closest("[data-research-detail]");
    if (detail) {
      event.preventDefault();
      window.location.hash = "mobileResearchDetail/" + encodeURIComponent(detail.getAttribute("data-research-detail"));
      showDetail(detail.getAttribute("data-research-detail"));
    }
    var linkTarget = event.target.closest('a[href="#mobileResearchPreview"], a[href="#mobileResearchCatalogue"]');
    if (linkTarget) {
      if (linkTarget.getAttribute("href") === "#mobileResearchPreview") revealPreview();
      if (linkTarget.getAttribute("href") === "#mobileResearchCatalogue") revealCatalogue();
    }
  });
  window.addEventListener("hashchange", handleResearchHash);
  window.CouponWorldMobileResearch = {
    isResearchQuery: function (value) {
      return researchConstraints(value).budget != null || /(?:phone|mobile|smartphone|galaxy|samsung|iphone|pixel|redmi|oneplus|nothing|realme|vivo|oppo|xiaomi|motorola|poco|iqoo|lava|tecno|infinix|camera|battery|gaming|display|software|build|reliability|durability|android|ram|storage|फोन|मोबाइल|कैमरा|बैटरी|गेमिंग|सैमसंग|अच्छा)/i.test(String(value || ""));
    },
    search: searchResearch,
    submit: submitResearch,
    clear: function () { if (researchQuery) researchQuery.value = ""; searchResearch(""); },
    revealPreview: revealPreview,
    revealCatalogue: revealCatalogue
  };
  loadInventoryCatalogue();
}());
