(function () {
  "use strict";
  // A saved quote is useful only while its original check remains recent.
  // No network, paid lookup, rewritten timestamps, or price-based quality score.
  function refreshWatchAge() {
    document.querySelectorAll("[data-watch-price-checked]").forEach(function (card) {
      var checked = Date.parse(card.getAttribute("data-watch-price-checked"));
      var age = Date.now() - checked;
      if (!Number.isFinite(checked) || age < 0 || age > 36 * 60 * 60 * 1000) {
        card.querySelector("[data-watch-amount]").textContent = "Check current price";
        card.querySelector("[data-watch-status]").textContent = "Saved check · recheck stock";
        card.classList.add("cw-watch-stale");
      }
    });
  }
  refreshWatchAge();
  document.addEventListener("visibilitychange", refreshWatchAge);
  window.setInterval(refreshWatchAge, 60000);
}());
