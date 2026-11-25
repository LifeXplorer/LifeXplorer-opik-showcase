import { describe, expect, it } from "vitest";
import { buildSystemPrompt, findExhibits, loadCollection } from "../src/collection.js";

const collection = loadCollection();

describe("findExhibits", () => {
  it("ranks the exhibit whose keywords match the message", () => {
    const hits = findExhibits("How many birds does the cuckoo have?", collection.exhibits);
    expect(hits[0]?.id).toBe("tinker-room-cuckoo");
  });

  it("returns nothing when no keyword matches", () => {
    expect(findExhibits("Do you sell postcards?", collection.exhibits)).toEqual([]);
  });

  it("respects the limit and prefers more keyword hits", () => {
    const hits = findExhibits("wheelchair stairs tower bell lunch cafe", collection.exhibits, 1);
    expect(hits).toHaveLength(1);
    expect(hits[0]?.id).toBe("tower-bellframe");
  });
});

describe("buildSystemPrompt", () => {
  it("includes the matched exhibit and the museum facts", () => {
    const prompt = buildSystemPrompt(collection, findExhibits("orrery", collection.exhibits));
    expect(prompt).toContain("The Marlow Orrery");
    expect(prompt).toContain("Closed Mondays");
  });

  it("says so when nothing matched", () => {
    expect(buildSystemPrompt(collection, [])).toContain("no specific exhibit matched");
  });
});
