import assert from "node:assert/strict";
import { test } from "node:test";
import { freshSession, transition } from "../src/session.ts";

const send = (state, type, data = {}) => transition(state, { type, ...data });

function rejected(state, id = "tylenol500") {
  const before = structuredClone(state);
  const result = send(state, "compare-cart-item", { id });
  assert.deepEqual(result, before);
  assert.deepEqual(state, before);
}

test("cart items append to comparison in the order added while cart and existing choices stay intact", () => {
  let state = send(freshSession(), "candidate", { id: "illiyoon_cream" });
  state = send(state, "select", { id: "illiyoon_cream" });
  state = send(state, "check", {
    id: "illiyoon_cream",
    check: {
      price: 21000,
      stock: "available",
      pack: true,
      pharmacist: false,
      fields: ["overview"],
    },
  });
  state = {
    ...state,
    page: "catalog",
    cart: { bepanthol_lip: 2, tylenol500: 4 },
    quantities: { ...state.quantities, bepanthol_lip: 2, tylenol500: 3 },
    checks: {
      ...state.checks,
      bepanthol_lip: {
        price: 1,
        stock: "available",
        pack: true,
        pharmacist: true,
        fields: ["overview"],
      },
      tylenol500: {
        price: 1,
        stock: "available",
        pack: true,
        pharmacist: true,
        fields: ["overview"],
      },
    },
    tester: "illiyoon_cream",
    purchaseRequested: true,
    purchased: true,
  };
  const before = structuredClone(state);

  const afterBepanthol = send(state, "compare-cart-item", {
    id: "bepanthol_lip",
  });
  assert.deepEqual(afterBepanthol?.candidates, [
    "illiyoon_cream",
    "bepanthol_lip",
  ]);
  state = afterBepanthol;
  assert.deepEqual(state, {
    ...before,
    candidates: [...before.candidates, "bepanthol_lip"],
    quantities: { illiyoon_cream: 1, tylenol500: 3 },
    checks: {
      illiyoon_cream: before.checks.illiyoon_cream,
      tylenol500: before.checks.tylenol500,
    },
    tester: null,
    purchaseRequested: false,
    purchased: false,
  });

  const beforeSecond = structuredClone(state);
  const afterTylenol = send(state, "compare-cart-item", {
    id: "tylenol500",
  });
  assert.deepEqual(afterTylenol?.candidates, [
    "illiyoon_cream",
    "bepanthol_lip",
    "tylenol500",
  ]);
  state = afterTylenol;
  assert.deepEqual(state, {
    ...beforeSecond,
    candidates: [...beforeSecond.candidates, "tylenol500"],
    quantities: { illiyoon_cream: 1 },
    checks: { illiyoon_cream: beforeSecond.checks.illiyoon_cream },
  });
});

test("an item already being compared is not duplicated or toggled out", () => {
  let state = send(freshSession(), "candidate", { id: "tylenol500" });
  state = send(state, "select", { id: "tylenol500" });
  state = {
    ...state,
    cart: { tylenol500: 2 },
    purchaseRequested: true,
  };

  rejected(state);
});

test("the fifth comparison item is allowed and a sixth item leaves every value unchanged", () => {
  let state = freshSession();
  const firstFour = [
    "illiyoon_cream",
    "bepanthol_lip",
    "tylenol500",
    "bepanthen",
  ];
  for (const id of firstFour) state = send(state, "candidate", { id });
  state = {
    ...state,
    page: "catalog",
    cart: { festal_plus: 3, allegra120: 1 },
    purchaseRequested: true,
  };

  const fifth = send(state, "compare-cart-item", { id: "festal_plus" });
  assert.deepEqual(fifth?.candidates, [...firstFour, "festal_plus"]);
  state = fifth;
  assert.deepEqual(state.candidates, [...firstFour, "festal_plus"]);
  assert.deepEqual(state.cart, { festal_plus: 3, allegra120: 1 });
  assert.equal(state.purchaseRequested, false);

  state = { ...state, purchaseRequested: true, purchased: true };
  rejected(state, "allegra120");
});

test("a missing cart item or unknown product leaves the session unchanged", () => {
  const state = { ...freshSession(), cart: { illiyoon_cream: 1 } };
  const before = structuredClone(state);

  const absent = send(state, "compare-cart-item", { id: "tylenol500" });
  assert.deepEqual(absent, before);
  assert.deepEqual(state, before);
  const unknown = send(state, "compare-cart-item", { id: "missing" });
  assert.deepEqual(unknown, before);
  assert.deepEqual(state, before);
});
