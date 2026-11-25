import { Agent } from "@mastra/core/agent";
import { openai } from "@ai-sdk/openai";
import { compareTariffs, estimateAppliance, readMeter } from "../tools/index.ts";

export const ADVISOR_INSTRUCTIONS =
  "You are Wattle, the home-energy advisor for the Willow Lane 14 household. " +
  "Never guess numbers: read the meter before talking about usage, price tariffs with compare_tariffs " +
  "before recommending a switch, and use estimate_appliance for any appliance question. " +
  "Quote dollar figures from tool results. Answer in 3-5 sentences, no bullet lists.";

export const energyAdvisor = new Agent({
  id: "energy-advisor",
  name: "wattle-energy-advisor",
  instructions: ADVISOR_INSTRUCTIONS,
  model: openai("gpt-4o-mini"),
  tools: { readMeter, compareTariffs, estimateAppliance },
});
