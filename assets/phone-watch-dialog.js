"use strict";

document.addEventListener("click", (event) => {
  const trigger = event.target.closest("[data-phone-dialog]");
  if (!trigger) return;

  const dialog = document.getElementById(trigger.dataset.phoneDialog);
  const card = trigger.closest(".phone-watch-card");
  const prices = dialog.querySelector(".phone-watch-dialog-prices");
  if (!prices.hasChildNodes()) {
    const image = card.querySelector(".phone-watch-image").cloneNode(true);
    const imageButton = image.querySelector("button");
    imageButton.replaceWith(imageButton.firstElementChild);
    dialog.querySelector("h2").after(image);
    const reference = card.querySelector(".phone-watch-reference");
    if (reference) prices.append(reference.cloneNode(true));
    prices.append(card.querySelector(".phone-watch-details ul").cloneNode(true));
  }
  dialog.showModal();
});
