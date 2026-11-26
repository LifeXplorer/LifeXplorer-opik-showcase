import { describe, expect, it } from "vitest";

import { checkGlossary, checkLength, checkPlaceholders, decide, runChecks, similarity } from "../src/qa.js";

const glossary = [{ source: "tide window", target: "Gezeitenfenster" }];

describe("qa checks", () => {
  it("flags a dropped placeholder and an invented one", () => {
    const r = checkPlaceholders("Hi {name}, you have {count} items", "Hallo {name}, du hast {total} Dinge");
    expect(r.ok).toBe(false);
    expect(r.missing).toEqual(["{count}"]);
    expect(r.extra).toEqual(["{total}"]);
  });

  it("requires the mandated glossary target only when the source term appears", () => {
    expect(checkGlossary("Next tide window", "Nächste Flutzeit", glossary).ok).toBe(false);
    expect(checkGlossary("Next tide window", "Nächstes Gezeitenfenster", glossary).ok).toBe(true);
    expect(checkGlossary("Hello", "Hallo", glossary).ok).toBe(true);
  });

  it("rejects translations much longer than the source", () => {
    expect(checkLength("Save", "Speichern und fortfahren").ok).toBe(false);
    expect(checkLength("Save your changes", "Änderungen speichern").ok).toBe(true);
  });

  it("scores word overlap and ignores placeholders", () => {
    expect(similarity("Your catch was saved {name}", "Your catch was saved {other}")).toBe(1);
    expect(similarity("Reel in your lines", "Quantum banana")).toBe(0);
  });

  it("sends anything suspicious to review with a reason per failed check", () => {
    const checks = runChecks("Open {time}", "Öffnet", "Opens", glossary);
    const v = decide(checks);
    expect(v.verdict).toBe("review");
    expect(v.reasons.join()).toContain("placeholders");
  });

  it("passes a clean round trip", () => {
    const checks = runChecks("Next tide window at {time}", "Nächstes Gezeitenfenster um {time}", "Next tide window at {time}", glossary);
    expect(decide(checks)).toEqual({ verdict: "pass", reasons: [] });
  });
});
