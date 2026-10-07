const fs = require("node:fs");
const path = require("node:path");
const readline = require("node:readline");
const { chromium } = require("playwright");

const baseUrl = process.argv[2];
const reportDir = path.resolve(process.argv[3]);
const checks = [];
const apiResponses = [];
const responseTasks = [];
let checksBeforeRestart = 0;

function check(id, expected, observed, passed) {
  checks.push({ id, expected, observed, passed: Boolean(passed) });
}

async function quantitiesOnPage(page) {
  await page.waitForFunction(() => {
    const list = document.querySelector("#history-items");
    return list && list.dataset.loaded !== "false";
  }, null, { timeout: 10000 });
  return page.locator(".item-row").evaluateAll((rows) =>
    rows.map((row) => Number(row.dataset.quantity))
  );
}

async function sharedUiObservation(page) {
  await page.evaluate(() => {
    if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
    window.scrollTo(0, 0);
  });
  await page.keyboard.press("Tab");
  return page.evaluate(() => {
    const nav = document.querySelector(".site-nav");
    const active = document.activeElement;
    const navStyle = getComputedStyle(nav);
    const focusStyle = getComputedStyle(active);
    const selectors = [".nav-links a", "#quantity", "#save-quantity"];
    const targets = selectors.flatMap((selector) =>
      Array.from(document.querySelectorAll(selector)).map((element) => ({
        selector,
        id: element.id || null,
        height_px: Math.round(element.getBoundingClientRect().height * 100) / 100,
      }))
    );
    return {
      viewport_width: window.innerWidth,
      control_size_token: getComputedStyle(document.documentElement)
        .getPropertyValue("--control-size").trim(),
      navigation: {
        padding: navStyle.padding,
        background_color: navStyle.backgroundColor,
      },
      keyboard_focus: {
        element_id: active.id || null,
        focus_visible: active.matches(":focus-visible"),
        outline_style: focusStyle.outlineStyle,
        outline_width_px: Number.parseFloat(focusStyle.outlineWidth),
        outline_color: focusStyle.outlineColor,
        outline_offset_px: Number.parseFloat(focusStyle.outlineOffset),
      },
      targets,
    };
  });
}

async function main() {
  fs.mkdirSync(reportDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();
  const artifacts = {
    entry_screenshot: path.join(reportDir, "entry-390.png"),
    history_screenshot: path.join(reportDir, "history-390.png"),
    trace: path.join(reportDir, "browser-trace.zip"),
  };
  const observations = {
    keyboard: {},
    history_before_restart: null,
    history_after_restart: null,
    responsive: {},
    shared_ui: {},
  };
  await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
  page.on("response", (response) => {
    if (!new URL(response.url()).pathname.startsWith("/api/")) return;
    responseTasks.push((async () => {
      const body = await response.json().catch(() => null);
      apiResponses.push({
        method: response.request().method(),
        url: response.url(),
        request_body: response.request().postData(),
        status: response.status(),
        response_body: body,
      });
    })());
  });

  await page.goto(baseUrl + "/", { waitUntil: "networkidle" });
  const semantics = await page.evaluate(() => ({
    language: document.documentElement.lang,
    heading: document.querySelector("h1")?.textContent.trim(),
    quantity_label_count: document.querySelector("#quantity").labels.length,
    navigation_label: document.querySelector("nav")?.getAttribute("aria-label"),
    status_role: document.querySelector("#status-message")?.getAttribute("role"),
  }));
  check("accessible_entry_controls", {
    language: "en", heading: "Add a quantity", quantity_label_count: 1,
    navigation_label: "Main navigation", status_role: "status",
  }, semantics,
  semantics.language === "en" && semantics.heading === "Add a quantity" &&
    semantics.quantity_label_count === 1 && semantics.navigation_label === "Main navigation" &&
    semantics.status_role === "status");

  const tabOrder = [];
  for (let index = 0; index < 4; index += 1) {
    await page.keyboard.press("Tab");
    tabOrder.push(await page.evaluate(() => document.activeElement.id || document.activeElement.tagName));
  }
  observations.keyboard.tab_order = tabOrder;
  const expectedTabOrder = ["nav-add", "nav-history", "quantity", "save-quantity"];
  const keyboardNavigationPassed = JSON.stringify(tabOrder) === JSON.stringify(expectedTabOrder);
  let savedByKeyboard = false;
  if (tabOrder[2] === "quantity" && tabOrder[3] === "save-quantity") {
    await page.keyboard.press("Shift+Tab");
    const quantityFocused = await page.evaluate(() => document.activeElement.id === "quantity");
    await page.keyboard.type("2");
    await page.keyboard.press("Tab");
    const submitFocused = await page.evaluate(() => document.activeElement.id === "save-quantity");
    if (quantityFocused && submitFocused) {
      await page.keyboard.press("Enter");
      savedByKeyboard = true;
    }
  } else {
    await page.locator("#quantity").fill("2");
    await page.locator("#save-quantity").click();
  }
  await page.waitForFunction(() => document.querySelector("#status-message")?.dataset.state === "success");
  await Promise.all(responseTasks);
  const positiveText = await page.locator("#status-message").innerText();
  observations.keyboard.saved_by_keyboard = savedByKeyboard;
  check("keyboard_submit", { order: expectedTabOrder, saved_by_keyboard: true },
    { order: tabOrder, saved_by_keyboard: savedByKeyboard },
    keyboardNavigationPassed && savedByKeyboard);
  const positiveResponse = apiResponses.find((entry) =>
    entry.method === "POST" && entry.status === 201 && entry.response_body?.quantity === 2);
  const positiveMatch = Boolean(positiveResponse);
  check("positive_quantity_api_save", { status: 201, quantity: 2 },
    { status_message: positiveText, api_response: positiveResponse || null }, positiveMatch);

  await page.locator("#quantity").fill("-1");
  await page.keyboard.press("Enter");
  await page.waitForFunction(() => document.querySelector("#status-message")?.dataset.state === "error");
  await Promise.all(responseTasks);
  const negativeText = await page.locator("#status-message").innerText();
  const negativeResponse = apiResponses.find((entry) =>
    entry.method === "POST" && entry.request_body === "{\"quantity\":-1}");
  const negativeMatch = Boolean(negativeResponse && negativeResponse.status === 422 &&
    negativeResponse.response_body?.error === "Quantity cannot be negative");
  check("negative_quantity_rejected_by_domain", {
    status: 422, error: "Quantity cannot be negative", persisted: false,
  }, { status_message: negativeText, api_response: negativeResponse || null }, negativeMatch);

  await page.locator("#quantity").fill("0");
  await page.keyboard.press("Enter");
  await page.waitForFunction(() => document.querySelector("#status-message")?.dataset.state === "success");
  await Promise.all(responseTasks);
  const zeroText = await page.locator("#status-message").innerText();
  const zeroResponse = apiResponses.find((entry) =>
    entry.method === "POST" && entry.request_body === "{\"quantity\":0}");
  const zeroMatch = Boolean(zeroResponse && zeroResponse.status === 201 &&
    zeroResponse.response_body?.quantity === 0);
  check("zero_quantity_api_save", { status: 201, quantity: 0 },
    { status_message: zeroText, api_response: zeroResponse || null }, zeroMatch);

  await page.goto(baseUrl + "/", { waitUntil: "networkidle" });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(150);
  observations.shared_ui.entry = await sharedUiObservation(page);
  await page.screenshot({ path: artifacts.entry_screenshot, fullPage: true });
  await page.goto(baseUrl + "/history", { waitUntil: "networkidle" });
  observations.history_before_restart = await quantitiesOnPage(page);
  check("history_fresh_read_before_restart", [2, 0], observations.history_before_restart,
    JSON.stringify(observations.history_before_restart) === "[2,0]");
  observations.shared_ui.history = await sharedUiObservation(page);
  const entryUi = observations.shared_ui.entry;
  const historyUi = observations.shared_ui.history;
  const focusIsVisible = (focus) =>
    focus.element_id === "nav-add" && focus.focus_visible &&
    focus.outline_style === "solid" && focus.outline_width_px >= 2 &&
    focus.outline_color !== "rgba(0, 0, 0, 0)";
  const targetsMeetMinimum = (route) =>
    route.viewport_width === 390 && route.targets.length > 0 &&
    route.targets.every((target) => target.height_px >= 44);
  const uiParityPassed =
    entryUi.control_size_token === "44px" && historyUi.control_size_token === "44px" &&
    entryUi.navigation.padding === historyUi.navigation.padding &&
    entryUi.navigation.background_color === historyUi.navigation.background_color &&
    JSON.stringify(entryUi.keyboard_focus) === JSON.stringify(historyUi.keyboard_focus) &&
    focusIsVisible(entryUi.keyboard_focus) && focusIsVisible(historyUi.keyboard_focus) &&
    targetsMeetMinimum(entryUi) && targetsMeetMinimum(historyUi);
  observations.shared_ui.acceptance = {
    shared_navigation_matches: entryUi.navigation.padding === historyUi.navigation.padding &&
      entryUi.navigation.background_color === historyUi.navigation.background_color,
    keyboard_focus_matches: JSON.stringify(entryUi.keyboard_focus) ===
      JSON.stringify(historyUi.keyboard_focus),
    focus_visible_on_both_routes: focusIsVisible(entryUi.keyboard_focus) &&
      focusIsVisible(historyUi.keyboard_focus),
    all_targets_at_least_44px: targetsMeetMinimum(entryUi) && targetsMeetMinimum(historyUi),
    token_is_44px_on_both_routes:
      entryUi.control_size_token === "44px" && historyUi.control_size_token === "44px",
  };
  check("shared_ui_mobile_acceptance", {
    viewport_width: 390,
    shared_navigation_matches: true,
    keyboard_focus_matches: true,
    focus_visible_on_both_routes: true,
    all_targets_at_least_44px: true,
    token_is_44px_on_both_routes: true,
  }, observations.shared_ui.acceptance, uiParityPassed);
  await page.screenshot({ path: artifacts.history_screenshot, fullPage: true });
  await Promise.all(responseTasks);
  checksBeforeRestart = checks.length;
  process.stdout.write(JSON.stringify({
    phase: "restart_ready",
    checks: checks.slice(),
    api_responses: apiResponses.slice(),
    observations: {
      keyboard: observations.keyboard,
      history_before_restart: observations.history_before_restart,
      shared_ui: observations.shared_ui,
    },
    browser: {
      node_version: process.version,
      playwright_version: require("playwright/package.json").version,
      chromium_executable: chromium.executablePath(),
    },
    artifacts,
  }) + "\n");

  const input = readline.createInterface({ input: process.stdin });
  const restartSignal = await new Promise((resolve) => {
    input.once("line", resolve);
    input.once("close", () => resolve(""));
  });
  input.close();
  if (restartSignal.trim() !== "RESTARTED") throw new Error("Runner did not confirm service restart");
  await page.reload({ waitUntil: "networkidle" });
  observations.history_after_restart = await quantitiesOnPage(page);
  check("history_fresh_read_after_service_restart", [2, 0], observations.history_after_restart,
    JSON.stringify(observations.history_after_restart) === "[2,0]");
  await page.screenshot({ path: artifacts.history_screenshot, fullPage: true });
  observations.responsive = await page.evaluate(() => ({
    viewport_width: window.innerWidth,
    document_width: document.documentElement.scrollWidth,
    no_horizontal_overflow: document.documentElement.scrollWidth <= window.innerWidth,
    navigation_visible: Boolean(document.querySelector("nav")?.getClientRects().length),
    list_visible: Boolean(document.querySelector("#history-items")?.getClientRects().length),
  }));
  const responsivePassed = observations.responsive.no_horizontal_overflow &&
    observations.responsive.navigation_visible && observations.responsive.list_visible;
  check("mobile_history_layout", {
    viewport_width: 390, no_horizontal_overflow: true, navigation_visible: true, list_visible: true,
  },
    observations.responsive, responsivePassed);
  await Promise.all(responseTasks);
  await context.tracing.stop({ path: artifacts.trace });
  await browser.close();
  process.stdout.write(JSON.stringify({
    phase: "complete",
    checks: checks.slice(checksBeforeRestart),
    api_responses: apiResponses,
    observations,
    browser: {
      node_version: process.version,
      playwright_version: require("playwright/package.json").version,
      chromium_executable: chromium.executablePath(),
    },
    artifacts,
  }) + "\n");
}

main().catch(async (error) => {
  process.stdout.write(JSON.stringify({
    phase: "error",
    error: { name: error.name, message: error.message, stack: error.stack },
    checks,
    api_responses: apiResponses,
  }) + "\n");
  process.exitCode = 1;
});
