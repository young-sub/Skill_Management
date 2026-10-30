import assert from "node:assert/strict";
import { test } from "node:test";
import { freshSession, purchaseStatus, reviewedField, transition } from "../src/session.ts";

const send = (state, type, data = {}) => transition(state, { type, ...data });

function preparedPurchase(id, pharmacist = false) {
  let state = send(freshSession(), "candidate", { id });
  state = send(state, "select", { id });
  return send(state, "check", {
    id,
    check: {
      price: 3500,
      stock: "available",
      pack: true,
      pharmacist,
      fields: ["overview"],
    },
  });
}

test("medicine overview stays hidden before pharmacist confirmation", () => {
  const state = preparedPurchase("tylenol500");

  assert.equal(reviewedField(state, "tylenol500", "overview"), false);
});

test("purchase request stays blocked before pharmacist confirmation", () => {
  const state = preparedPurchase("tylenol500");

  assert.equal(purchaseStatus(state).ready, false);
  assert.equal(send(state, "purchase-request").purchaseRequested, false);
});

test("pharmacist confirmation allows medicine overview and purchase when ordinary conditions are met", () => {
  const state = preparedPurchase("tylenol500", true);

  assert.equal(reviewedField(state, "tylenol500", "overview"), true);
  assert.equal(purchaseStatus(state).ready, true);
  assert.equal(send(state, "purchase-request").purchaseRequested, true);
});

test("nearby cosmetic stays viewable and purchasable without pharmacist confirmation", () => {
  const state = preparedPurchase("illiyoon_cream");

  assert.equal(reviewedField(state, "illiyoon_cream", "overview"), true);
  assert.equal(purchaseStatus(state).ready, true);
  assert.equal(send(state, "purchase-request").purchaseRequested, true);
});

test("another medicine remains gated as well", () => {
  const state = preparedPurchase("bepanthen");

  assert.equal(reviewedField(state, "bepanthen", "overview"), false);
  assert.equal(purchaseStatus(state).ready, false);
  assert.equal(send(state, "purchase-request").purchaseRequested, false);
});
