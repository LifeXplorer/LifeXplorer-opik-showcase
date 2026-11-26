import { Agent } from "@voltagent/core";
import { findParts, quoteRepair, repairStatus } from "./tools.ts";

export const MODEL = "openai/gpt-4o-mini";

export const frontDesk = new Agent({
  name: "cog-and-crank-front-desk",
  // VoltAgent's model router resolves this id to the AI SDK's OpenAI provider.
  model: MODEL,
  instructions:
    "You are the front-desk assistant at Cog & Crank Cycle Works, a neighborhood bike shop. " +
    "Never guess: use repair_status for ticket questions, find_parts for parts and stock, and " +
    "quote_repair to price anything. Only quote parts that are in stock; if one is sold out, say " +
    "so and offer the closest in-stock alternative. Add one labor job to every quote for each piece of work requested. State totals exactly as the tool returns them. " +
    "Be friendly and brief: 2-4 sentences.",
  // Deterministic answers keep the demo's quotes comparable between runs.
  temperature: 0,
  tools: [repairStatus, findParts, quoteRepair],
});
