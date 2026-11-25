import { describe, expect, it } from "vitest";
import { compareTariffs, estimateAppliance, readMeter } from "../src/tools/index.ts";
import { buildObservability } from "../src/observability.ts";

// Mastra tools are plain async functions underneath; no agent or model is needed to test them.
const run = (tool: any, input: unknown) => tool.execute(input, {});

describe("tools", () => {
  it("read_meter returns only the requested window", async () => {
    const r = await run(readMeter, { days: 2 });
    expect(r.days).toBe(2);
    expect(r.total_kwh).toBe(34.1);
  });

  it("compare_tariffs flags the current plan", async () => {
    const flat = await run(compareTariffs, { tariff_id: "flat-saver" });
    const tou = await run(compareTariffs, { tariff_id: "evening-shift" });
    expect(flat.is_current_plan).toBe(true);
    expect(tou.total_usd).toBeLessThan(flat.total_usd);
  });

  it("estimate_appliance uses the peak or off-peak rate", async () => {
    const peak = await run(estimateAppliance, { appliance_id: "ev-charger", tariff_id: "evening-shift", run_at_peak: true });
    const off = await run(estimateAppliance, { appliance_id: "ev-charger", tariff_id: "evening-shift", run_at_peak: false });
    expect(peak.daily_cost_usd).toBe(4.3);
    expect(off.daily_cost_usd).toBe(1.79);
  });
});

describe("Opik tracing switch", () => {
  it("builds no exporter when OPIK_TRACK_DISABLE=true, and tools still run", async () => {
    process.env.OPIK_TRACK_DISABLE = "true";
    expect(buildObservability()).toBeUndefined();
    expect((await run(readMeter, { days: 1 })).days).toBe(1);
  });
});
