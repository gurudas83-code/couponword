(function () {
  "use strict";
  var panel = document.querySelector("[data-page-feedback]");
  if (!panel) return;
  var kind = panel.getAttribute("data-feedback-kind") || "page";
  var status = panel.querySelector("[data-feedback-status]");
  var reasons = panel.querySelector("[data-feedback-reasons]");
  function send(name, params) {
    try { if (typeof window.gtag === "function") window.gtag("event", name, params); } catch (_) { /* Never block reading. */ }
  }
  panel.addEventListener("click", function (event) {
    var value = event.target.closest && event.target.closest("[data-feedback-value]");
    if (value) {
      var feedback = value.getAttribute("data-feedback-value") || "unknown";
      send("page_feedback", { feedback_value: feedback, page_kind: kind });
      if (reasons) reasons.hidden = feedback !== "needs_work";
      if (status) status.textContent = feedback === "helpful" ? "Thanks — we’ll keep improving this research." : "Thanks — tell us what would make this page more useful.";
      return;
    }
    var reason = event.target.closest && event.target.closest("[data-feedback-reason]");
    if (reason) {
      send("page_feedback_reason", { feedback_reason: reason.getAttribute("data-feedback-reason") || "unknown", page_kind: kind });
      if (status) status.textContent = "Thanks — your improvement signal was recorded.";
    }
  });
})();
