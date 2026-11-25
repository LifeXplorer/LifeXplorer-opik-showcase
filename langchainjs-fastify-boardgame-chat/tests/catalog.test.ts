import { describe, expect, it } from "vitest";
import { loadCatalog, mentionedGames, parseWishes, shortlist } from "../src/catalog.js";

describe("parseWishes", () => {
  it("reads party size, time, difficulty and mood from free text", () => {
    const w = parseWishes("We're four people, never played, want something quick and cooperative");
    expect(w.players).toBe(4);
    expect(w.weight).toBe("light");
    expect(w.maxMinutes).toBe(45);
    expect(w.tags).toEqual(expect.arrayContaining(["cooperative", "quick"]));
  });

  it("prefers an explicit minute budget", () => {
    expect(parseWishes("we have 90 minutes, six of us").maxMinutes).toBe(90);
  });
});

describe("shortlist", () => {
  const catalog = loadCatalog();

  it("only offers games that seat the party", () => {
    const picks = shortlist(catalog, { players: 7, tags: [] });
    expect(picks.length).toBeGreaterThan(0);
    for (const g of picks) expect(g.minPlayers <= 7 && 7 <= g.maxPlayers).toBe(true);
  });

  it("ranks matching moods first and caps the list", () => {
    const picks = shortlist(catalog, { players: 4, tags: ["bluffing"], maxMinutes: 60 });
    expect(picks).toHaveLength(4);
    expect(picks[0]?.tags).toContain("bluffing");
  });

  it("returns nothing when no game fits the party", () => {
    expect(shortlist(catalog, { players: 12, tags: [] })).toEqual([]);
  });
});

describe("mentionedGames", () => {
  it("finds games by name, ignoring case and the ampersand", () => {
    const names = mentionedGames(loadCatalog(), "how long does fox & LANTERN take, or moth and flame?").map((g) => g.name);
    expect(names).toEqual(expect.arrayContaining(["Fox & Lantern", "Moth & Flame"]));
  });
});
