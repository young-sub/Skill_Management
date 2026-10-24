import assert from "node:assert/strict";
import { test } from "node:test";
import { freshSession, purchaseStatus, reviewedField, transition } from "../src/session.ts";

const send = (state, type, data = {}) => transition(state, { type, ...data });
function reviewedProduct(id, pharmacist) {
  let state = send(freshSession(), "candidate", { id });
  state = send(state, "select", { id });
  return send(state, "check", {
    id,
    check: {
      price: 21000,
      stock: "available",
      pack: true,
      pharmacist,
      fields: ["overview"],
    },
  });
}

test("medicine explanations stay hidden until pharmacist review", () => {
  const state = reviewedProduct("tylenol500", false);
  assert.equal(reviewedField(state, "tylenol500", "overview"), false);
});

test("medicine remains blocked from purchase until pharmacist review", () => {
  const state = reviewedProduct("tylenol500", false);
  assert.equal(purchaseStatus(state).ready, false);
  assert.equal(send(state, "purchase-request").purchaseRequested, false);
});

test("a completed pharmacist review reveals medicine information and allows the prepared purchase", () => {
  const state = reviewedProduct("tylenol500", true);
  assert.equal(reviewedField(state, "tylenol500", "overview"), true);
  assert.equal(purchaseStatus(state).ready, true);
  assert.equal(send(state, "purchase-request").purchaseRequested, true);
});

test("cosmetic information and purchase remain available without pharmacist review", () => {
  const state = reviewedProduct("illiyoon_cream", false);
  assert.equal(reviewedField(state, "illiyoon_cream", "overview"), true);
  assert.equal(purchaseStatus(state).ready, true);
});