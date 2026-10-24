import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { ProductCatalogFinder } from "./ProductCatalogFinder";

const attributes = (markup: string) => Object.fromEntries(
  Array.from(markup.matchAll(/([a-zA-Z_:][-a-zA-Z0-9_:.]*)="([^"]*)"/g), match => [match[1], match[2]]),
);

const rowFor = (html: string, visibleName: string) =>
  Array.from(html.matchAll(/<tr\b[^>]*>([\s\S]*?)<\/tr>/g), match => match[1]).find(row => row.includes(visibleName));

describe("product catalog selection", () => {
  it("lets the product name activate its checkbox while keeping added products disabled", () => {
    const client = new QueryClient({ defaultOptions: { queries: { staleTime: Number.POSITIVE_INFINITY } } });
    client.setQueryData(["product-catalog", "", "", null], {
      items: [
        { id: "selectable", kind: "cosmetic", nameKo: "Selectable item", alreadyAdded: false },
        { id: "added", kind: "cosmetic", nameKo: "Already added", alreadyAdded: true },
      ],
      nextCursor: null,
    });
    const html = renderToStaticMarkup(createElement(
      QueryClientProvider,
      { client },
      createElement(ProductCatalogFinder, { categories: [], onClose: () => {}, onApplied: () => {} }),
    ));

    const selectableRow = rowFor(html, "Selectable item");
    expect(selectableRow).toBeDefined();
    const selectableInputTag = selectableRow!.match(/<input\b[^>]*>/)?.[0];
    expect(selectableInputTag).toBeDefined();
    const selectableInput = attributes(selectableInputTag!);
    expect(selectableInput.type).toBe("checkbox");
    expect(selectableInput).not.toHaveProperty("disabled");

    const nameLabel = Array.from(selectableRow!.matchAll(/<label\b[^>]*>[\s\S]*?<\/label>/g), match => match[0])
      .find(label => label.includes("Selectable item"));
    expect(nameLabel).toBeDefined();
    const labelOpenTag = nameLabel!.match(/^<label\b[^>]*>/)?.[0] ?? "";
    const labelAttributes = attributes(labelOpenTag);
    const associatedByFor = Boolean(selectableInput.id && labelAttributes.htmlFor === selectableInput.id)
      || Boolean(selectableInput.id && labelAttributes.for === selectableInput.id);
    const associatedByNesting = nameLabel!.includes(selectableInputTag!);
    expect(associatedByFor || associatedByNesting).toBe(true);

    const addedRow = rowFor(html, "Already added");
    expect(addedRow).toBeDefined();
    const addedInputTag = addedRow!.match(/<input\b[^>]*>/)?.[0];
    expect(addedInputTag).toBeDefined();
    expect(attributes(addedInputTag!).type).toBe("checkbox");
    expect(attributes(addedInputTag!)).toHaveProperty("disabled");
    client.clear();
  });
});
