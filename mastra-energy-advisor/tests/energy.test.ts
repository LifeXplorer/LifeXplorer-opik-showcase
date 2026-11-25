import { describe, expect, it } from "vitest";
import { READINGS, TARIFFS, APPLIANCES } from "../src/data/home.ts";
import { applianceDailyCost, applianceDailyKwh, costOnTariff, summarizeReadings } from "../src/energy.ts";

describe("energy maths", () => {
  it("summarizes a week of readings", () => {
    const s = summarizeReadings(READINGS);
    expect(s.days).toBe(7);
    expect(s.total_kwh).toBe(114.5);
    expect(s.peak_kwh).toBe(41);
    expect(s.peak_share_pct).toBe(35.8);
  });

  it("prices flat and time-of-use tariffs", () => {
    expect(costOnTariff(READINGS, TARIFFS["flat-saver"]).total_usd).toBe(34.14);
    expect(costOnTariff(READINGS, TARIFFS["evening-shift"]).total_usd).toBe(32.95);
  });

  it("estimates appliance energy and cost", () => {
    const ev = APPLIANCES["ev-charger"];
    expect(applianceDailyKwh(ev)).toBe(10.5);
    expect(applianceDailyCost(ev, 0.17)).toBe(1.79);
  });

  it("handles an empty reading list", () => {
    expect(summarizeReadings([]).avg_daily_kwh).toBe(0);
  });
});
