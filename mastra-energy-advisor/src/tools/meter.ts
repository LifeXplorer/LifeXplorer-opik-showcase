import { createTool } from "@mastra/core/tools";
import { z } from "zod";
import { READINGS } from "../data/home.ts";
import { summarizeReadings } from "../energy.ts";

export const readMeter = createTool({
  id: "read_meter",
  description:
    "Read the household smart meter for the last N days (1-7). Returns total kWh, the kWh used in " +
    "the 16:00-20:00 peak window versus all other hours, and the average per day.",
  inputSchema: z.object({
    days: z.number().int().min(1).max(7).describe("How many most-recent days to include"),
  }),
  execute: async ({ days }) => summarizeReadings(READINGS.slice(-days)),
});
