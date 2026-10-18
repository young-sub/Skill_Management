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

async function layoutObservation(page) {
  return page.evaluate(() => ({
    viewport_width: window.innerWidth,
    document_width: document.documentElement.scrollWidth,
    no_horizontal_overflow: document.documentElement.scrollWidth <= window.innerWidth,
    navigation_visible: Boolean(document.querySelector("nav")?.getClientRects().length),
    main_visible: Boolean(document.querySelector("#main-content")?.getClientRects().length),
  }));
}

async function sharedUiObservation(page) {
  await page.evaluate(() => {
    if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
    document.body.setAttribute("tabindex", "-1");
    document.body.focus();
    window.scrollTo(0, 0);
  });
  await page.keyboard.press("Tab");
  return page.evaluate(() => {
    document.body.removeAttribute("tabindex");
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
    const controlSize = getComputedStyle(document.documentElement)
      .getPropertyValue("--control-size").trim();
    return {
      viewport_width: window.innerWidth,
      control_size_token: controlSize,
      control_size_px: Number.parseFloat(controlSize),
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
    entry_desktop_screenshot: path.join(reportDir, "entry-1280.png"),
    entry_mobile_screenshot: path.join(reportDir, "entry-390.png"),
    history_desktop_screenshot: path.join(reportDir, "history-1280.png"),
    history_mobile_screenshot: path.join(reportDir, "history-390.png"),
    history_mobile_after_restart_screenshot: path.join(reportDir, "history-390-after-restart.png"),
    trace: path.join(reportDir, "browser-trace.zip"),
  };
  const observations = {
    keyboard: {},
    history_before_restart: null,
    history_after_restart: null,
    responsive: {},
    shared_ui: { desktop: {}, mobile: {} },
    states: {},
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

  let releaseEmptyRead;
  const emptyReadGate = new Promise((resolve) => { releaseEmptyRead = resolve; });
  const delayedEmptyRead = async (route) => {
    const response = await route.fetch();
    await emptyReadGate;
    await route.fulfill({ response });
  };
  await page.route("**/api/items", delayedEmptyRead);
  await page.goto(baseUrl + "/history", { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => {
    const state = document.querySelector("#history-state");
    const list = document.querySelector("#history-items");
    return state?.textContent.startsWith("Loading saved items") && list?.dataset.loaded === "false";
  });
  observations.states.history_loading = await page.evaluate(() => ({
    text: document.querySelector("#history-state").textContent,
    loaded: document.querySelector("#history-items").dataset.loaded,
  }));
  releaseEmptyRead();
  const emptyItems = await quantitiesOnPage(page);
  observations.states.history_empty = await page.evaluate(() => ({
    text: document.querySelector("#history-state").textContent,
    loaded: document.querySelector("#history-items").dataset.loaded,
  }));
  observations.states.history_empty.items = emptyItems;
  await page.unroute("**/api/items", delayedEmptyRead);
  const emptyStatePassed = observations.states.history_loading.text.startsWith("Loading saved items") &&
    observations.states.history_loading.loaded === "false" &&
    observations.states.history_empty.text === "No saved items yet." &&
    observations.states.history_empty.loaded === "true" && emptyItems.length === 0;
  check("history_empty_and_loading_states", {
    loading: { text: "Loading saved items", loaded: "false" },
    empty: { text: "No saved items yet.", loaded: "true", items: [] },
  }, {
    loading: observations.states.history_loading,
    empty: observations.states.history_empty,
  }, emptyStatePassed);

  const failedHistoryRead = (route) => route.fulfill({
    status: 503,
    contentType: "application/json",
    body: JSON.stringify({ error: "Controlled history read failure" }),
  });
  await page.route("**/api/items", failedHistoryRead);
  await page.goto(baseUrl + "/history", { waitUntil: "networkidle" });
  await page.waitForFunction(() => document.querySelector("#history-items")?.dataset.loaded === "error");
  observations.states.history_error = await page.evaluate(() => ({
    text: document.querySelector("#history-state").textContent,
    loaded: document.querySelector("#history-items").dataset.loaded,
    role: document.querySelector("#history-state").getAttribute("role"),
  }));
  await page.unroute("**/api/items", failedHistoryRead);
  const historyErrorPassed = observations.states.history_error.text ===
    "Could not load history: Controlled history read failure" &&
    observations.states.history_error.loaded === "error" && observations.states.history_error.role === "status";
  check("history_read_error_state", {
    text: "Could not load history: Controlled history read failure", loaded: "error", role: "status",
  }, observations.states.history_error, historyErrorPassed);

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
  let savePending = null;
  let releaseSaveResponse;
  const saveResponseGate = new Promise((resolve) => { releaseSaveResponse = resolve; });
  const delayedSave = async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    const response = await route.fetch();
    await saveResponseGate;
    await route.fulfill({ response });
  };
  await page.route("**/api/items", delayedSave);
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
  await page.waitForFunction(() => document.querySelector("#status-message")?.dataset.state === "pending");
  savePending = await page.evaluate(() => ({
    state: document.querySelector("#status-message").dataset.state,
    text: document.querySelector("#status-message").textContent,
  }));
  releaseSaveResponse();
  await page.waitForFunction(() => document.querySelector("#status-message")?.dataset.state === "success");
  await page.unroute("**/api/items", delayedSave);
  await Promise.all(responseTasks);
  const positiveText = await page.locator("#status-message").innerText();
  observations.keyboard.saved_by_keyboard = savedByKeyboard;
  observations.states.save_pending = savePending;
  check("keyboard_submit", {
    order: expectedTabOrder, saved_by_keyboard: true, pending_state: "pending", pending_text: "Saving…",
  }, { order: tabOrder, saved_by_keyboard: savedByKeyboard, save_pending: savePending },
  keyboardNavigationPassed && savedByKeyboard && savePending.state === "pending" &&
    savePending.text.startsWith("Saving"));
  const positiveResponse = apiResponses.find((entry) =>
    entry.method === "POST" && entry.status === 201 && entry.response_body?.quantity === 2);
  const positiveMatch = Boolean(positiveResponse) && positiveText.startsWith("Saved quantity 2");
  check("positive_quantity_api_save", { status: 201, quantity: 2, state: "success" },
    { status: 201, state: "success", status_message: positiveText, api_response: positiveResponse || null }, positiveMatch);

  await page.locator("#quantity").fill("-1");
  await page.keyboard.press("Enter");
  await page.waitForFunction(() => document.querySelector("#status-message")?.dataset.state === "error");
  await Promise.all(responseTasks);
  const negativeText = await page.locator("#status-message").innerText();
  const negativeResponse = apiResponses.find((entry) =>
    entry.method === "POST" && entry.request_body === "{\"quantity\":-1}");
  const negativeMatch = Boolean(negativeResponse && negativeResponse.status === 422 &&
    negativeResponse.response_body?.error === "Quantity cannot be negative") &&
    (await page.locator("#status-message").getAttribute("data-state")) === "error" &&
    negativeText === "Rejected: Quantity cannot be negative";
  check("negative_quantity_rejected_by_domain", {
    status: 422, error: "Quantity cannot be negative", persisted: false, state: "error",
  }, { status_message: negativeText, state: "error", api_response: negativeResponse || null }, negativeMatch);

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
  await page.setViewportSize({ width: 1280, height: 900 });
  observations.shared_ui.desktop.entry = await sharedUiObservation(page);
  observations.responsive.desktop = { entry: await layoutObservation(page) };
  await page.screenshot({ path: artifacts.entry_desktop_screenshot, fullPage: true });
  await page.goto(baseUrl + "/history", { waitUntil: "networkidle" });
  observations.shared_ui.desktop.history = await sharedUiObservation(page);
  observations.responsive.desktop.history = await layoutObservation(page);
  await page.screenshot({ path: artifacts.history_desktop_screenshot, fullPage: true });

  await page.setViewportSize({ width: 390, height: 844 });
  observations.shared_ui.mobile.history = await sharedUiObservation(page);
  observations.responsive.mobile = { history: await layoutObservation(page) };
  await page.screenshot({ path: artifacts.history_mobile_screenshot, fullPage: true });
  await page.goto(baseUrl + "/", { waitUntil: "networkidle" });
  observations.shared_ui.mobile.entry = await sharedUiObservation(page);
  observations.responsive.mobile.entry = await layoutObservation(page);
  await page.screenshot({ path: artifacts.entry_mobile_screenshot, fullPage: true });

  await page.goto(baseUrl + "/history", { waitUntil: "networkidle" });
  observations.history_before_restart = await quantitiesOnPage(page);
  observations.states.history_populated = await page.evaluate(() => ({
    text: document.querySelector("#history-state").textContent,
    loaded: document.querySelector("#history-items").dataset.loaded,
  }));
  check("history_fresh_read_before_restart", [2, 0], observations.history_before_restart,
    JSON.stringify(observations.history_before_restart) === "[2,0]" &&
    observations.states.history_populated.text === "2 saved items" &&
    observations.states.history_populated.loaded === "true");

  const focusIsVisible = (focus) =>
    focus.element_id === "nav-add" && focus.focus_visible &&
    focus.outline_style === "solid" && focus.outline_width_px >= 2 &&
    focus.outline_color !== "rgba(0, 0, 0, 0)";
  const targetsMeetToken = (route) => Number.isFinite(route.control_size_px) &&
    route.control_size_px >= 44 && route.targets.length > 0 &&
    route.targets.every((target) => target.height_px >= Math.max(44, route.control_size_px));
  const routesMatch = (view, field) => {
    const { entry, history } = observations.shared_ui[view];
    return field(entry) === field(history);
  };
  const allScreens = [
    observations.shared_ui.desktop.entry, observations.shared_ui.desktop.history,
    observations.shared_ui.mobile.entry, observations.shared_ui.mobile.history,
  ];
  const allLayouts = [
    observations.responsive.desktop.entry, observations.responsive.desktop.history,
    observations.responsive.mobile.entry, observations.responsive.mobile.history,
  ];
  const focusVisibleEverywhere = allScreens.every((screen) => focusIsVisible(screen.keyboard_focus));
  const targetsMeetTokenEverywhere = allScreens.every(targetsMeetToken);
  const sharedNavigationMatches = ["desktop", "mobile"].every((view) => routesMatch(view,
    (route) => JSON.stringify(route.navigation)));
  const keyboardFocusMatches = ["desktop", "mobile"].every((view) => routesMatch(view,
    (route) => JSON.stringify(route.keyboard_focus)));
  const tokenValidOnBothRoutes = ["desktop", "mobile"].every((view) =>
    routesMatch(view, (route) => route.control_size_px) &&
    observations.shared_ui[view].entry.control_size_px >= 44);
  const allTargetsAtLeast44 = allScreens.every((screen) =>
    screen.targets.length > 0 && screen.targets.every((target) => target.height_px >= 44));
  const uiParityPassed = sharedNavigationMatches && keyboardFocusMatches &&
    focusVisibleEverywhere && targetsMeetTokenEverywhere && tokenValidOnBothRoutes && allTargetsAtLeast44;
  observations.shared_ui.acceptance = {
    shared_navigation_matches: sharedNavigationMatches,
    keyboard_focus_matches: keyboardFocusMatches,
    focus_visible_on_both_routes: focusVisibleEverywhere,
    all_targets_at_least_44px: allTargetsAtLeast44,
    token_is_valid_on_both_routes: tokenValidOnBothRoutes,
    targets_meet_token: targetsMeetTokenEverywhere,
  };
  check("shared_ui_mobile_acceptance", {
    viewport_widths: [1280, 390],
    shared_navigation_matches: true,
    keyboard_focus_matches: true,
    focus_visible_on_both_routes: true,
    all_targets_at_least_44px: true,
    token_is_valid_on_both_routes: true,
    targets_meet_token: true,
  }, observations.shared_ui.acceptance, uiParityPassed);
  await Promise.all(responseTasks);
  checksBeforeRestart = checks.length;
  process.stdout.write(JSON.stringify({
    phase: "restart_ready",
    checks: checks.slice(),
    api_responses: apiResponses.slice(),
    observations: {
      keyboard: observations.keyboard,
      states: observations.states,
      history_before_restart: observations.history_before_restart,
      responsive: observations.responsive,
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
  await page.screenshot({ path: artifacts.history_mobile_after_restart_screenshot, fullPage: true });
  observations.responsive.mobile.history_after_restart = await layoutObservation(page);
  observations.responsive.mobile.history_after_restart.list_visible = await page.evaluate(() =>
    Boolean(document.querySelector("#history-items")?.getClientRects().length));
  const mobileHistoryLayout = observations.responsive.mobile.history_after_restart;
  const responsivePassed = [...allLayouts, mobileHistoryLayout].every((layout) =>
    layout.no_horizontal_overflow && layout.navigation_visible && layout.main_visible) &&
    mobileHistoryLayout.list_visible;
  check("mobile_history_layout", {
    viewport_width: 390, no_horizontal_overflow: true, navigation_visible: true, list_visible: true,
  }, { ...mobileHistoryLayout, responsive: observations.responsive }, responsivePassed);
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
