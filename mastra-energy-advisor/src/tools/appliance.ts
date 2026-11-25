import { createTool } from "@mastra/core/tools";
import { z } from "zod";
import { APPLIANCES, TARIFFS } from "../data/home.ts";
import { applianceDailyCost, applianceDailyKwh } from "../energy.ts";

export const estimateAppliance = createTool({
  id: "estimate_appliance",
  description:
    "Estimate the daily energy and cost of one appliance, and whether it can be moved out of the " +
    "peak window. Valid ids: heat-pump-dryer, dishwasher, ev-charger, oven, fridge-freezer.",
  inputSchema: z.object({
    appliance_id: z.enum(["heat-pump-dryer", "dishwasher", "ev-charger", "oven", "fridge-freezer"]),
    tariff_id: z.enum(["flat-saver", "evening-shift"]).describe("Tariff whose rates to apply"),
    run_at_peak: z.boolean().describe("true if it runs 16:00-20:00, false if it runs off-peak"),
  }),
  execute: async ({ appliance_id, tariff_id, run_at_peak }) => {
    const appliance = APPLIANCES[appliance_id];
    const tariff = TARIFFS[tariff_id];
    const rate = tariff.flatRate ?? (run_at_peak ? tariff.peakRate : tariff.offPeakRate) ?? 0;
    return {
      appliance: appliance.name,
      daily_kwh: applianceDailyKwh(appliance),
      rate_usd_per_kwh: rate,
      daily_cost_usd: applianceDailyCost(appliance, rate),
      shiftable_out_of_peak: appliance.shiftable,
    };
  },
});
