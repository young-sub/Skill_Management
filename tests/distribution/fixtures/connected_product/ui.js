class AppNav extends HTMLElement {
  connectedCallback() {
    const active = this.getAttribute("active");
    this.innerHTML =
      '<nav class="site-nav" aria-label="Main navigation">' +
      '<span class="brand">Connected Product</span>' +
      '<div class="nav-links">' +
      '<a id="nav-add" href="/" ' + (active === "add" ? 'aria-current="page"' : "") + '>Add quantity</a>' +
      '<a id="nav-history" href="/history" ' + (active === "history" ? 'aria-current="page"' : "") + '>History</a>' +
      "</div></nav>";
  }
}

customElements.define("app-nav", AppNav);

const form = document.querySelector("#quantity-form");
if (form) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const status = document.querySelector("#status-message");
    const quantity = Number(document.querySelector("#quantity").value);
    status.textContent = "Saving…";
    status.dataset.state = "pending";
    try {
      const response = await fetch("/api/items", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ quantity }),
      });
      const result = await response.json();
      status.textContent = response.ok
        ? "Saved quantity " + result.quantity + " (item " + result.id + ")."
        : "Rejected: " + result.error;
      status.dataset.state = response.ok ? "success" : "error";
      if (response.ok) form.reset();
    } catch (error) {
      status.textContent = "Request failed: " + error.message;
      status.dataset.state = "error";
    }
  });
}

const historyList = document.querySelector("#history-items");
if (historyList) {
  fetch("/api/items")
    .then((response) => response.json().then((body) => ({ response, body })))
    .then(({ response, body }) => {
      if (!response.ok) throw new Error(body.error || "HTTP " + response.status);
      const state = document.querySelector("#history-state");
      if (body.items.length === 0) state.textContent = "No saved items yet.";
      else state.textContent = body.items.length + " saved items";
      for (const item of body.items) {
        const row = document.createElement("li");
        row.className = "item-row";
        row.dataset.testid = "item-row";
        row.dataset.quantity = String(item.quantity);
        const label = document.createElement("span");
        label.textContent = "Item " + item.id;
        const value = document.createElement("span");
        value.className = "item-quantity";
        value.textContent = "Quantity " + item.quantity;
        row.append(label, value);
        historyList.append(row);
      }
      historyList.dataset.loaded = "true";
    })
    .catch((error) => {
      document.querySelector("#history-state").textContent = "Could not load history: " + error.message;
      historyList.dataset.loaded = "error";
    });
}
