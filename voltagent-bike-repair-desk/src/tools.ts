// The three tools the front-desk agent can call. Each one is a thin wrapper
// over a pure function in shop.ts.
import { createTool } from "@voltagent/core";
import { z } from "zod";
import { LABOR, buildQuote, lookupTicket, searchParts } from "./shop.ts";

export const repairStatus = createTool({
  name: "repair_status",
  description: "Look up a repair ticket by id (like RT-2043) and report its status and pickup estimate.",
  parameters: z.object({ ticket_id: z.string().describe("Ticket id, e.g. RT-2043") }),
  execute: async ({ ticket_id }) => lookupTicket(ticket_id) ?? { error: `No ticket ${ticket_id}` },
});

export const findParts = createTool({
  name: "find_parts",
  description: "Search the parts shelf by keyword, optionally for one bike type. Returns price and units in stock.",
  parameters: z.object({
    query: z.string().describe("Keywords such as 'chain' or 'commuter tire'"),
    bike_type: z.enum(["road", "mtb", "commuter"]).optional().describe("Narrow to parts that fit this bike type"),
  }),
  execute: async ({ query, bike_type }) => ({ parts: searchParts(query, bike_type) }),
});

export const quoteRepair = createTool({
  name: "quote_repair",
  description: `Price a repair from part SKUs and labor jobs (${Object.keys(LABOR).join(", ")}). Adds sales tax.`,
  parameters: z.object({
    part_skus: z.array(z.string()).describe("SKUs from find_parts"),
    labor_jobs: z.array(z.string()).describe("Labor job names"),
  }),
  execute: async ({ part_skus, labor_jobs }) => buildQuote(part_skus, labor_jobs),
});
