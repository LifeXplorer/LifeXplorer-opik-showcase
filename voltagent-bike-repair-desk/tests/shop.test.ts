import { describe, expect, it } from "vitest";
import { buildQuote, lookupTicket, searchParts } from "../src/shop.ts";

describe("repair desk logic", () => {
  it("finds a ticket regardless of case and whitespace", () => {
    expect(lookupTicket(" rt-2043 ")?.customer).toBe("Priya Nair");
    expect(lookupTicket("RT-0000")).toBeUndefined();
  });

  it("narrows parts to the bike type but keeps universal parts", () => {
    const skus = searchParts("tire tube", "commuter").map((p) => p.sku);
    expect(skus).toContain("TR-701");
    expect(skus).toContain("TB-700");
    expect(skus).not.toContain("TR-290");
  });

  it("adds tax to parts and labor", () => {
    // 19 chain + 41 tire + 25 chain-replace + 20 tire-swap = 105; 8% tax = 8.40
    expect(buildQuote(["CH-108", "TR-701"], ["chain-replace", "tire-swap"])).toMatchObject({
      subtotal_usd: 105,
      tax_usd: 8.4,
      total_usd: 113.4,
    });
  });

  it("refuses to quote a sold-out part or an unknown job", () => {
    expect(buildQuote(["TR-700"], [])).toEqual({ error: "TR-700 (Marathon 700x35 commuter tire) is out of stock" });
    expect(buildQuote([], ["engine-swap"])).toEqual({ error: "Unknown labor job engine-swap" });
  });
});
