import { describe, expect, it } from "vitest";
import { loadPlantFile, planFor, plantingCalendar, shiftWeeks } from "../src/lib/garden";

describe("planting calendar", () => {
  it("shifts dates by whole weeks around the last frost", () => {
    expect(shiftWeeks("2026-05-04", -8)).toBe("2026-03-09");
    expect(shiftWeeks("2026-05-04", 1)).toBe("2026-05-11");
  });

  it("computes sow, plant-out and harvest dates for tomatoes", () => {
    expect(planFor("Tomato")).toMatchObject({
      found: true,
      plant: "tomato",
      sowIndoors: "2026-03-09",
      plantOut: "2026-05-11",
      firstHarvest: "2026-07-30",
    });
  });

  it("accepts a plural and leaves sowIndoors empty for direct-sown crops", () => {
    expect(planFor("peas")).toMatchObject({ found: true, plant: "peas", sowIndoors: null });
    expect(planFor("tomatoes")).toMatchObject({ found: false });
  });

  it("lists the known plants when the crop is unknown", () => {
    const result = planFor("dragonfruit");
    expect(result.found).toBe(false);
    if (!result.found) expect(result.knownPlants).toEqual(loadPlantFile().plants.map((p) => p.name));
  });

  it("exposes the lookup as an AI SDK tool", async () => {
    const out = await plantingCalendar.execute!({ plant: "kale" }, { toolCallId: "t1", messages: [] } as never);
    expect(out).toMatchObject({ found: true, plant: "kale" });
  });
});
