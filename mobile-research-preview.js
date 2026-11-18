    fillSelect(inventoryStorage, optionValues(rows, "storage_gb"), "All storage");
    fillSelect(inventoryStatus, ["OFFICIAL_VERIFIED", "PARTIALLY_VERIFIED", "RESEARCH_ONLY", "NEEDS_VERIFICATION"], "All evidence statuses");
    renderInventory();
  }

  function loadInventoryCatalogue() {
    if (!inventoryGrid) return;
    // Version the generated data URL so a reviewed catalogue refresh cannot
    // be hidden by a stale GitHub Pages/browser cache.
    // Import only the eight source-reviewed missing market identities.
    // They remain separate from the original 232-card registry, ratings and offers.
    var coreFetch = fetch("/data/mobile_research_catalogue.json?v=licensed-photos-20261117", { credentials: "same-origin" })
      .then(function (response) {
        if (!response.ok) throw new Error("research catalogue unavailable");
        return response.json();
      });
    var marketFetch = fetch("/data/india_sales_eight_research.json?v=20261118", { credentials: "same-origin" })
      .then(function (response) {
        if (!response.ok) throw new Error("market intake unavailable");
        return response.json();
      }).catch(function () { return null; });
    var recentFetch = fetch("/data/india_recent_manufacturer_research.json?v=20261118d", { credentials: "same-origin" })
      .then(function (response) {
        if (!response.ok) throw new Error("recent phone research unavailable");
        return response.json();
      }).catch(function () { return null; });
    Promise.all([coreFetch, marketFetch, recentFetch])
      .then(function (results) {
        var payload = results[0], intake = results[1], recent = results[2];
        inventoryLoadFailed = false;
        inventoryRows = Array.isArray(payload.records) ? payload.records : [];
        inventoryByKey = new Map(inventoryRows.map(function (row) { return [row.record_key, row]; }));
        inventoryCards = Array.isArray(payload.model_cards) ? payload.model_cards : [];
        inventorySourceCounts = payload.source_counts || {};
        marketIntakeCount = 0;
        if (intake && intake.mode === "EIGHT_SOURCE_REVIEWED_MARKET_ADDITIONS_NO_LIVE_OFFERS" &&
            intake.core_model_count_unchanged === 232 &&
            Array.isArray(intake.model_cards) && intake.model_cards.length === 8 &&
            Array.isArray(intake.records) && intake.records.length === 8) {
          var known = new Set(inventoryCards.map(function (card) { return card.model_key; }));
          var imported = intake.model_cards.every(function (card) {
            return card.market_intake === true && card.status === "RESEARCH_ONLY" &&
              card.image_status === "PLACEHOLDER" && !card.photo && !known.has(card.model_key) &&
              Array.isArray(card.verified_retailer_links) && !card.verified_retailer_links.length;
          });
          if (imported) {
            intake.records.forEach(function (row) { inventoryByKey.set(row.record_key, row); inventoryRows.push(row); });
            inventoryCards = inventoryCards.concat(intake.model_cards);
            marketIntakeCount = intake.model_cards.length;
          }
        }
        // Strictly separate manufacturer-source discovery from canonical phones
        // and exact retail SKUs. Ignore incomplete or conflicting data entirely.
        if (recent && recent.mode === "RECENT_INDIA_MANUFACTURER_MODELS_RESEARCH_ONLY" &&
            recent.core_model_count_unchanged === 232 &&
            Array.isArray(recent.model_cards) && recent.model_cards.length === 13 &&
            Array.isArray(recent.records) && recent.records.length === 13) {
          var identifiers = new Set(inventoryCards.map(function (card) { return card.model_key; }));
          var recordIds = new Set(inventoryRows.map(function (row) { return row.record_key; }));
          var safeRecent = recent.model_cards.every(function (card) {
            return card.market_intake === true && card.status === "RESEARCH_ONLY" &&
              card.image_status === "PLACEHOLDER" && !card.photo &&
              !identifiers.has(card.model_key) &&
              Array.isArray(card.discovery_record_keys) && card.discovery_record_keys.length === 1 &&
              Array.isArray(card.verified_retailer_links) && !card.verified_retailer_links.length &&
              Array.isArray(card.frozen_variant_ids) && !card.frozen_variant_ids.length &&
              card.specifications && Object.values(card.specifications).every(function (field) {
                return field && typeof field.value === "string" && field.value.trim() &&
                  field.source_url === card.manufacturer_page;
              });
          }) && recent.records.every(function (row) {
            return row.status === "RESEARCH_ONLY" && !recordIds.has(row.record_key);
          }) && new Set(recent.model_cards.map(function (card) { return card.model_key; })).size === recent.model_cards.length &&
              new Set(recent.records.map(function (row) { return row.record_key; })).size === recent.records.length;
          if (safeRecent) {
            recent.records.forEach(function (row) { inventoryByKey.set(row.record_key, row); inventoryRows.push(row); });
            inventoryCards = inventoryCards.concat(recent.model_cards);
            marketIntakeCount += recent.model_cards.length;
          }
        }
        refreshInventoryControls();
        restoreShortlist();
        renderNewNoteworthy();
        handleResearchHash();
        var initialQuery = lastSearchQuery || new URLSearchParams(window.location.search || "").get("q");
        if (initialQuery) submitResearch(initialQuery);
      })
      .catch(function () {
        inventoryLoadFailed = true;
        if (researchSearchStatus) researchSearchStatus.textContent = "Saved smartphone research is temporarily unavailable. Use the Standard Buying Guide below.";
        if (researchResults) { researchResults.hidden = false; researchResults.innerHTML = researchGuideFallback(); }