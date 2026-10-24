import assert from "node:assert/strict";
import { test } from "node:test";
import { catalog } from "../src/catalog.ts";
import {
  freshSession,
  transition,
} from "../src/session.ts";

const send = (state, type, data = {}) => transition(state, { type, ...data });
function selected(ids, quantities = {}) {
  let state = { ...freshSession(), page: "purchase" };
  for (const id of ids) {
    state = send(state, "candidate", { id });
    state = send(state, "select", { id });
    if ((quantities[id] ?? 1) !== 1)
      state = send(state, "quantity", { id, quantity: quantities[id] });
  }
  return state;
}
function withProduct(id, overrides, run) {
  const original = catalog.products[id];
  catalog.products[id] = { ...original, ...overrides };
  try {
    return run();
  } finally {
    catalog.products[id] = original;
  }
}

test("selected quantities merge into the cart without changing the purchase selection", () => {
  let state = selected(["illiyoon_cream"], { illiyoon_cream: 2 });
  state = { ...state, cart: { illiyoon_cream: 3 } };

  const next = send(state, "add-selected-to-cart");

  assert.deepEqual(next?.cart ?? {}, { illiyoon_cream: 5 });
  assert.deepEqual(next?.candidates ?? [], state.candidates);
  assert.deepEqual(next?.quantities ?? {}, state.quantities);
  assert.equal(next?.page, "purchase");
});

test("the batch is rejected unchanged if one merged quantity would exceed 99", () => {
  const state = {
    ...selected(["illiyoon_cream", "bepanthol_lip"], {
      illiyoon_cream: 2,
      bepanthol_lip: 1,
    }),
    cart: { illiyoon_cream: 98 },
  };
  assert.deepEqual(send(state, "add-selected-to-cart"), state);
  assert.deepEqual(state.cart, { illiyoon_cream: 98 });
});

test("an unclassified selection prevents every item in the batch from being added", () =>
  withProduct("illiyoon_cream", { kind: "unclassified" }, () => {
    let state = selected(["illiyoon_cream", "bepanthol_lip"]);
    state = send(state, "check", {
      id: "illiyoon_cream",
      check: {
        price: 12000,
        stock: "available",
        pack: true,
        pharmacist: true,
        fields: [],
      },
    });
    assert.deepEqual(send(state, "add-selected-to-cart"), state);
    assert.deepEqual(state.cart, {});
  }));

test("a catalog item marked out of stock prevents a partial add", () =>
  withProduct("illiyoon_cream", { inStock: false }, () => {
    const state = selected(["illiyoon_cream", "bepanthol_lip"]);
    assert.deepEqual(send(state, "add-selected-to-cart"), state);
    assert.deepEqual(state.cart, {});
  }));

test("a pharmacist-required product is blocked until its review is recorded", () => {
  const waiting = selected(["tylenol500"]);
  assert.deepEqual(send(waiting, "add-selected-to-cart"), waiting);

  const reviewed = send(waiting, "check", {
    id: "tylenol500",
    check: {
      price: 21000,
      stock: "available",
      pack: true,
      pharmacist: true,
      fields: [],
    },
  });
  assert.deepEqual(send(reviewed, "add-selected-to-cart")?.cart ?? {}, {
    tylenol500: 1,
  });
});

test("an unavailable staff stock check rejects the whole batch", () => {
  let state = selected(["illiyoon_cream", "bepanthol_lip"]);
  state = send(state, "check", {
    id: "illiyoon_cream",
    check: {
      price: 12000,
      stock: "unavailable",
      pack: true,
      pharmacist: false,
      fields: [],
    },
  });
  assert.deepEqual(send(state, "add-selected-to-cart"), state);
  assert.deepEqual(state.cart, {});
});