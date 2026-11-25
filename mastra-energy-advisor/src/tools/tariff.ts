import { createTool } from "@mastra/core/tools";
import { z } from "zod";
import { CURRENT_TARIFF_ID, READINGS, TARIFFS } from "../data/home.ts";
import { costOnTariff } from "../energy.ts";

export const compareTariffs = createTool({
  id: "compare_tariffs",
  description:
    "Price the household's last 7 days of metered usage on a tariff. Valid ids: flat-saver (the " +
    "household's current plan) and evening-shift (cheap off-peak, expensive 16:00-20:00 peak). " +
    "Call once per tariff to compare them.",
  inputSchema: z.object({
    tariff_id: z.enum(["flat-saver", "evening-shift"]).describe("Tariff to price"),
  }),
  execute: async ({ tariff_id }) => {
    const tariff = TARIFFS[tariff_id];
    return {
      tariff: tariff.name,
      is_current_plan: tariff_id === CURRENT_TARIFF_ID,
      ...costOnTariff(READINGS, tariff),
      period: "last 7 days",
    };
  },
});
